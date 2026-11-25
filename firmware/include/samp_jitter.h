/*
 * Interval statistics of the captured SAMP edges: a bench check of the
 * MAX30001 sample clock while PLLINT keeps firing (bring-up report 9.9). Every
 * interval between two captured edges is compared with the nominal period in
 * capture ticks (80 MHz: 12.5 ns); so are the sums of the last 16 and the last
 * 256 intervals, which show a phase excursion too slow to stand out in one
 * interval. Integer only, so the capture callback calls samp_jitter_add.
 *
 * An interval farther than half a period from nominal (a missed or an extra
 * edge) counts as a gap and starts a new series; samp_jitter_break does the
 * same before a restart (SYNCH). Header only, built on the host by
 * tests/test_firmware_samp_jitter.py.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#define SAMP_JITTER_BINS 7  /* |dev| <= 0.125, 0.5, 1, 5, 20, 100 us, more */
#define SAMP_JITTER_RING 256u
#define SAMP_JITTER_SPAN_SHORT 16u

typedef struct {
    uint32_t n;          /* intervals counted */
    uint32_t gaps;       /* intervals more than half a period off nominal */
    int32_t min_dev;     /* ticks; valid when n > 0 */
    int32_t max_dev;
    int64_t sum_dev;
    uint64_t sum_sq;
    uint32_t bins[SAMP_JITTER_BINS];
    /* Sums of the last 16 [0] and 256 [1] intervals minus 16 or 256 nominal
     * periods, ticks; valid when span_n[i] > 0. */
    uint32_t span_n[2];
    int32_t span_min[2];
    int32_t span_max[2];
} samp_jitter_stats_t;

typedef struct {
    uint32_t nominal;                      /* ticks per nominal period; 0 = off */
    uint32_t limit[SAMP_JITTER_BINS - 1];  /* upper |dev| of each bin, ticks */
    uint32_t prev;
    bool have_prev;
    uint32_t run;                          /* intervals in the current series */
    uint32_t pos;
    int32_t ring[SAMP_JITTER_RING];
    int32_t sum[2];
    samp_jitter_stats_t stats;
} samp_jitter_t;

/* nominal: ticks per sample period; ticks_per_s: capture timer resolution. */
static inline void samp_jitter_init(samp_jitter_t *j, uint32_t nominal, uint32_t ticks_per_s)
{
    static const uint32_t ns[SAMP_JITTER_BINS - 1] = {125, 500, 1000, 5000, 20000, 100000};
    *j = (samp_jitter_t){.nominal = nominal};
    for (int i = 0; i < SAMP_JITTER_BINS - 1; i++) {
        j->limit[i] = (uint32_t)(((uint64_t)ns[i] * ticks_per_s + 500000000u) / 1000000000u);
    }
}

static inline void samp_jitter_break(samp_jitter_t *j)
{
    j->have_prev = false;
    j->run = 0;
}

__attribute__((always_inline)) static inline void samp_jitter_span(samp_jitter_stats_t *s, int i, int32_t v)
{
    if (s->span_n[i] == 0 || v < s->span_min[i]) {
        s->span_min[i] = v;
    }
    if (s->span_n[i] == 0 || v > s->span_max[i]) {
        s->span_max[i] = v;
    }
    s->span_n[i]++;
}

/* One captured edge (capture timer value; a wrap of the counter is harmless). */
static inline void samp_jitter_add(samp_jitter_t *j, uint32_t ticks)
{
    if (j->nominal == 0) {
        return;
    }
    bool had = j->have_prev;
    uint32_t prev = j->prev;
    j->prev = ticks;
    j->have_prev = true;
    if (!had) {
        return;
    }
    samp_jitter_stats_t *s = &j->stats;
    int32_t dev = (int32_t)(ticks - prev - j->nominal);
    uint32_t mag = dev < 0 ? (uint32_t)(-(int64_t)dev) : (uint32_t)dev;
    if (mag > j->nominal / 2u) {
        s->gaps++;
        j->run = 0;
        return;
    }
    if (s->n == 0 || dev < s->min_dev) {
        s->min_dev = dev;
    }
    if (s->n == 0 || dev > s->max_dev) {
        s->max_dev = dev;
    }
    s->n++;
    s->sum_dev += dev;
    s->sum_sq += (uint64_t)((int64_t)dev * dev);
    int b = 0;
    while (b < SAMP_JITTER_BINS - 1 && mag > j->limit[b]) {
        b++;
    }
    s->bins[b]++;
    if (j->run == 0) {
        j->sum[0] = j->sum[1] = 0;
    }
    /* Sliding sums over the ring: leaving values exist once the run is long. */
    j->sum[0] += dev;
    j->sum[1] += dev;
    if (j->run >= SAMP_JITTER_SPAN_SHORT) {
        j->sum[0] -= j->ring[(j->pos - SAMP_JITTER_SPAN_SHORT) % SAMP_JITTER_RING];
    }
    if (j->run >= SAMP_JITTER_RING) {
        j->sum[1] -= j->ring[j->pos % SAMP_JITTER_RING];
    }
    j->ring[j->pos % SAMP_JITTER_RING] = dev;
    j->pos++;
    j->run++;
    if (j->run >= SAMP_JITTER_SPAN_SHORT) {
        samp_jitter_span(s, 0, j->sum[0]);
    }
    if (j->run >= SAMP_JITTER_RING) {
        samp_jitter_span(s, 1, j->sum[1]);
    }
}
