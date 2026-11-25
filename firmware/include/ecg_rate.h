/*
 * ECG sample-rate check against the MCU clock (decided 2026-11-21,
 * hardware/test_reports/sync_10min_test_plan.md section 11.3). It replaces the
 * PLLINT flag on a MAX30001 board where PLLINT never clears: over each window
 * of at least `window_us` of reliable FIFO-read anchors, the samples counted
 * from the sample index must match the elapsed esp_timer time within
 * `tol_ppm` of the nominal rate. Pure C, no ESP-IDF: tested on the host.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    bool started;
    uint32_t k0;    /* last sample index (modulo 2^32) at the window start */
    int64_t t0_us;  /* its anchor */
    uint32_t windows, faults;
    double last_ppm; /* rate deviation of the last complete window, ppm (+ = fast) */
} ecg_rate_t;

void ecg_rate_init(ecg_rate_t *r);

/* Forget the current window (a re-anchored index, a full FIFO read, a chip
 * restart): the next reliable packet starts a new one. Counters are kept. */
void ecg_rate_reset(ecg_rate_t *r);

/* One reliable packet: last sample index `k` (modulo 2^32) with anchor `t_us`.
 * When the window has reached `window_us`, compares the rate and starts a new
 * window at this packet; returns true when the rate was off by more than
 * `tol_ppm` (or time did not advance). */
bool ecg_rate_packet(ecg_rate_t *r, uint32_t k, int64_t t_us, uint32_t fs_nominal_mhz,
                     uint32_t tol_ppm, int64_t window_us);
