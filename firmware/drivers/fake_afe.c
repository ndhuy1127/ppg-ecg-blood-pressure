#include "fake_afe.h"

#include <stdbool.h>
#include <stdlib.h>

#include "esp_timer.h"
#include "packet_wire.h"

struct fake_afe {
    fake_afe_config_t cfg;
    TaskHandle_t reader;
    esp_timer_handle_t timer;
    portMUX_TYPE lock;
    uint64_t fifo_first; /* cumulative index of the oldest sample in the FIFO */
    uint16_t fill;
    uint32_t lost;       /* samples dropped while the FIFO was full */
};

static void on_sample(void *arg)
{
    fake_afe_t *afe = arg;
    bool notify = false;
    portENTER_CRITICAL(&afe->lock);
    /* Like MAX3010x with FIFO_ROLLOVER_EN = 0 or BMI270 with stop_on_full: a
     * full FIFO keeps its contents and new samples are lost, so the gap lies
     * after the last stored sample. */
    if (afe->fill < afe->cfg.depth) {
        afe->fill++;
        /* Notify once, when the threshold is crossed: a later notification
         * could wake the reader right after a latch and yield a tiny batch. */
        notify = afe->fill == afe->cfg.batch;
    } else {
        afe->lost++;
    }
    portEXIT_CRITICAL(&afe->lock);
    if (notify) {
        xTaskNotifyGive(afe->reader);
    }
}

esp_err_t fake_afe_start(const fake_afe_config_t *cfg, TaskHandle_t reader, fake_afe_t **out)
{
    if (cfg->n_slots == 0 || cfg->n_slots > FAKE_AFE_MAX_SLOTS || cfg->batch == 0
        || cfg->batch > cfg->depth || cfg->depth > FAKE_AFE_MAX_DEPTH || cfg->period_us == 0) {
        return ESP_ERR_INVALID_ARG;
    }
    fake_afe_t *afe = calloc(1, sizeof(*afe));
    if (afe == NULL) {
        return ESP_ERR_NO_MEM;
    }
    afe->cfg = *cfg;
    afe->reader = reader;
    portMUX_INITIALIZE(&afe->lock);
    const esp_timer_create_args_t args = {
        .callback = on_sample,
        .arg = afe,
        .name = cfg->name,
    };
    esp_err_t err = esp_timer_create(&args, &afe->timer);
    if (err == ESP_OK) {
        err = esp_timer_start_periodic(afe->timer, cfg->period_us);
    }
    if (err != ESP_OK) {
        free(afe);
        return err;
    }
    *out = afe;
    return ESP_OK;
}

fake_afe_batch_t fake_afe_latch(fake_afe_t *afe)
{
    fake_afe_batch_t b;
    portENTER_CRITICAL(&afe->lock);
    b.first_index = afe->fifo_first;
    b.count = afe->fill;
    b.lost_after = afe->lost;
    afe->fifo_first += afe->fill + afe->lost;
    afe->fill = 0;
    afe->lost = 0;
    portEXIT_CRITICAL(&afe->lock);
    /* Every latched sample was created before this instant. */
    b.t_anchor_us = (uint64_t)esp_timer_get_time();
    return b;
}

int32_t fake_afe_sample(const fake_afe_t *afe, uint8_t slot, uint64_t index)
{
    uint8_t channel = afe->cfg.channel_ids[0];
    if (channel >= PKT_CH_ACC_X && channel <= PKT_CH_GYR_Z) {
        /* BMI270 word: int16, sign-extended (V0.2 section 2). Steps of 257 per
         * sample and 8191 per axis reach both ends, -32768 and 32767. */
        return (int32_t)((index * 257u + slot * 8191u) % 65536u) - 32768;
    }
    if (channel == PKT_CH_ECG) {
        /* MAX30001 FIFO word (schema section 8): 18-bit two's-complement sample
         * in bits 23..6, ETAG = PTAG = 0. Sawtooth -1024 .. 1023. */
        int32_t value = (int32_t)(index % 2048u) - 1024;
        return (int32_t)(((uint32_t)value & 0x3FFFFu) << 6);
    }
    /* MAX3010x: 18-bit unsigned count; each slot has its own offset, at most
     * 4096 + 32768 * 4 < 2^18 for slot 4. */
    return (int32_t)(index % 4096u + 32768u * (slot + 1u));
}

const fake_afe_config_t *fake_afe_config(const fake_afe_t *afe)
{
    return &afe->cfg;
}
