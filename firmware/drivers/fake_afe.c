#include "fake_afe.h"

#include <stdbool.h>
#include <stdlib.h>

#include "esp_timer.h"
#include "freertos/semphr.h"
#include "packet_wire.h"

struct fake_afe {
    fake_afe_config_t cfg;
    TaskHandle_t reader;
    esp_timer_handle_t timer;
    esp_timer_handle_t drain;   /* one-shot: runs after every earlier callback */
    SemaphoreHandle_t drained;
    portMUX_TYPE lock;
    uint64_t fifo_first; /* index of the oldest sample in the FIFO */
    uint16_t fill;
    uint32_t lost;       /* samples dropped while the FIFO was full */
    uint64_t made;       /* samples converted since the (re)start */
    int64_t start_us;    /* origin of the alarms: sample k is due at start + (k + 1) T */
    bool running;        /* false from fake_afe_stop to fake_afe_resume */
};

static void on_sample(void *arg)
{
    fake_afe_t *afe = arg;
    bool notify = false;
    portENTER_CRITICAL(&afe->lock);
    /* A callback dispatched before fake_afe_stop but run after it does nothing.
     * fake_afe_stop also waits until it has returned (drain). */
    if (!afe->running) {
        portEXIT_CRITICAL(&afe->lock);
        return;
    }
    uint64_t index = afe->made++;
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
    if (afe->cfg.on_sample != NULL) {
        /* The alarm time of this sample: callbacks run late, the alarms do not.
         * Called inside the lock, so nothing of an epoch passes fake_afe_stop. */
        afe->cfg.on_sample(index, afe->start_us + (int64_t)(index + 1) * afe->cfg.period_us);
    }
    portEXIT_CRITICAL(&afe->lock);
    if (notify) {
        xTaskNotifyGive(afe->reader);
    }
}

static void on_drain(void *arg)
{
    fake_afe_t *afe = arg;
    xSemaphoreGive(afe->drained);
}

static esp_err_t start_timer(fake_afe_t *afe)
{
    /* Armed inside the lock, between two clock reads, so that start_us is the
     * time esp_timer_start_periodic took within a microsecond or two. */
    portENTER_CRITICAL(&afe->lock);
    afe->fifo_first = 0;
    afe->fill = 0;
    afe->lost = 0;
    afe->made = 0;
    int64_t t0 = esp_timer_get_time();
    esp_err_t err = esp_timer_start_periodic(afe->timer, afe->cfg.period_us);
    int64_t t1 = esp_timer_get_time();
    afe->start_us = t0 + (t1 - t0) / 2;
    afe->running = err == ESP_OK;
    portEXIT_CRITICAL(&afe->lock);
    return err;
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
    afe->drained = xSemaphoreCreateBinary();
    const esp_timer_create_args_t args = {
        .callback = on_sample,
        .arg = afe,
        .name = cfg->name,
    };
    const esp_timer_create_args_t drain_args = {
        .callback = on_drain,
        .arg = afe,
        .name = "fake_afe_drain",
    };
    esp_err_t err = afe->drained == NULL ? ESP_ERR_NO_MEM : esp_timer_create(&args, &afe->timer);
    if (err == ESP_OK) {
        err = esp_timer_create(&drain_args, &afe->drain);
    }
    if (err == ESP_OK) {
        err = start_timer(afe);
    }
    if (err != ESP_OK) {
        free(afe); /* start failures are fatal (ESP_ERROR_CHECK in the caller) */
        return err;
    }
    *out = afe;
    return ESP_OK;
}

void fake_afe_stop(fake_afe_t *afe)
{
    portENTER_CRITICAL(&afe->lock);
    afe->running = false;
    portEXIT_CRITICAL(&afe->lock);
    esp_timer_stop(afe->timer);
    /* esp_timer_stop does not wait for a callback already dispatched. The
     * esp_timer task runs callbacks one at a time, so once the one-shot drain
     * callback has run, every earlier callback has returned. */
    esp_timer_start_once(afe->drain, 0);
    xSemaphoreTake(afe->drained, portMAX_DELAY);
}

esp_err_t fake_afe_resume(fake_afe_t *afe)
{
    return start_timer(afe);
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
