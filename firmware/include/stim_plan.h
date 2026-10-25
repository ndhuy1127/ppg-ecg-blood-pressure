/*
 * Schedule of the 10-minute sync stimulus (hardware/test_reports/
 * sync_10min_test_plan.md, sections 3-4; decided 2026-10-25): a rising edge on
 * GPIO6 every STIM_PERIOD_US plus a uniform offset in [0, STIM_JITTER_US), so
 * that the edges cover one ECG sample period (1953.125 us at 512 sps) evenly
 * instead of locking to a phase. The seed is the SESSION_ID, which every packet
 * carries, so each boot gives a new sequence that can be regenerated. Plain C
 * with no ESP-IDF dependency, so the same code can be compiled on a PC.
 */
#pragma once

#include <stdint.h>

#define STIM_PERIOD_US 1000000u
#define STIM_JITTER_US 1953u   /* one ECG sample period, rounded down */
#define STIM_WIDTH_US 50000u   /* pulse width */
#define STIM_FIRST_US 2000000u /* first edge this long after the start */

typedef struct {
    uint32_t state; /* xorshift32, never 0 */
} stim_plan_t;

void stim_plan_init(stim_plan_t *s, uint32_t seed);

/* Time from one scheduled rising edge to the next: STIM_PERIOD_US plus an
 * offset in [0, STIM_JITTER_US). */
uint32_t stim_next_interval_us(stim_plan_t *s);
