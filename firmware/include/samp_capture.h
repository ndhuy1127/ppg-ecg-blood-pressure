/*
 * MCPWM capture of the MAX30001 SAMP pulse (INT2B on GPIO47, Packet Schema V0.2
 * section 7.1). NOT RUN ON A CHIP YET (2026-10-24): it builds, and it is used
 * only with BOARD_SAMP_CAPTURE=1; the default firmware takes its edges from the
 * fake ECG source. Check at bring-up: edge polarity and pulse width on the
 * scope, a GPIO loop-back on a bare DevKitC, the clock transfer error in the
 * UART0 log.
 *
 * The capture channel latches the MCPWM capture timer (80 MHz APB) at the edge
 * in hardware; the callback only pushes that value into the edge ring. A
 * second channel, without a GPIO, is caught by software between two esp_timer
 * reads (a bracketed pair, kept only if the reads are less than 2 us apart)
 * every 100 ms, with up to four tries in a period (2026-11-23: on the bench
 * most first tries were too wide, likely a flash cache miss). A capture value is turned into esp_timer us from the latest
 * pair with the nominal ratio (both clocks come from the same crystal), and
 * only while that pair is younger than 1 s, far inside the +-26.8 s that the
 * signed tick difference can tell apart. The gap between that prediction and
 * the next pair is logged as the transfer error, budget below 5 us.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "samp_jitter.h"

typedef struct {
    uint32_t pairs;          /* bracketed pairs kept */
    uint32_t pairs_rejected; /* reads 2 us or more apart, or no software catch */
    int64_t max_error_ns;    /* largest |predicted - measured| between pairs */
    uint32_t stale;          /* conversions refused: no pair younger than 1 s */
} samp_capture_stats_t;

/* Start the capture on gpio (rising or falling edge) and the clock pairs. */
esp_err_t samp_capture_start(int gpio, bool rising_edge);

/* Give `task` a notification (vTaskNotifyGiveFromISR) after every `every`
 * captured edges; task NULL stops it. Used by the SAMP bench mode
 * (BOARD_ECG_SAMP_BENCH), whose reader wakes on SAMP edges instead of INTB. */
void samp_capture_notify(TaskHandle_t task, uint32_t every);

/* Count the edges for samp_capture_notify from zero again (at a mapping start,
 * so the reads follow edges every, 2 * every, ... of the new epoch). */
void samp_capture_notify_restart(void);

/* Interval statistics of the captured edges (samp_jitter.h), off until
 * samp_capture_jitter_init (after samp_capture_start) gives the nominal sample
 * rate in millihertz. samp_capture_jitter_break before a restart (SYNCH) keeps
 * the interval across it out. samp_capture_jitter copies the statistics and
 * gives the capture timer resolution. */
void samp_capture_jitter_init(uint32_t fs_mhz);
void samp_capture_jitter_break(void);
samp_jitter_stats_t samp_capture_jitter(uint32_t *ticks_per_s);

/* samp_convert_fn of samp_edges.h. */
bool samp_capture_to_us(int64_t raw, int64_t *t_us);

samp_capture_stats_t samp_capture_stats(void);
