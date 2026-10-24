/*
 * Stand-in for a sensor FIFO while no MAX30001/MAX30101/BMI270 is connected. An
 * esp_timer callback "samples" at a fixed period into a FIFO of `depth`
 * samples (frames for the IMU); the reader latches how many samples are
 * waiting, takes T_ANCHOR_US right after (schema section 5), then reads
 * exactly that many. A full FIFO keeps its contents and loses new samples
 * (MAX3010x FIFO_ROLLOVER_EN = 0, BMI270 fifo_stop_on_full = 1). DATA is a
 * deterministic function of the cumulative sample index, so a receiver can
 * check every sample. Nothing here is a physiological signal.
 */
#pragma once

#include <stdint.h>

#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define FAKE_AFE_MAX_DEPTH 256u
#define FAKE_AFE_MAX_SLOTS 6u

typedef struct {
    const char *name;
    uint8_t n_slots;
    uint8_t channel_ids[FAKE_AFE_MAX_SLOTS];
    uint32_t fs_nominal_mhz;
    uint32_t period_us; /* real period of the fake source */
    uint16_t batch;     /* notify the reader once this many samples wait */
    uint16_t depth;     /* FIFO capacity in samples, batch .. FAKE_AFE_MAX_DEPTH */
} fake_afe_config_t;

typedef struct {
    uint64_t first_index;   /* cumulative index of the first latched sample */
    uint16_t count;         /* N latched samples, 0 .. depth */
    uint32_t lost_after;    /* samples dropped after the last one (FIFO full); a
                             * real BMI270 does not report this: answer key only */
    uint64_t t_anchor_us;   /* esp_timer right after the latch */
} fake_afe_batch_t;

typedef struct fake_afe fake_afe_t;

/* Start the fake source; the reader task gets xTaskNotifyGive per batch. */
esp_err_t fake_afe_start(const fake_afe_config_t *cfg, TaskHandle_t reader, fake_afe_t **out);

/* Latch the waiting samples and take the anchor time. */
fake_afe_batch_t fake_afe_latch(fake_afe_t *afe);

/* DATA value of a slot at a cumulative sample index. */
int32_t fake_afe_sample(const fake_afe_t *afe, uint8_t slot, uint64_t index);

const fake_afe_config_t *fake_afe_config(const fake_afe_t *afe);
