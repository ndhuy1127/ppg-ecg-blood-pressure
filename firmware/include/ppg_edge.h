/*
 * PPG_RDY edge times for the bench diagnostic of the MAX30101 sample clock
 * (BOARD_PPG_EDGE_ANCHOR, bring-up report 12.4): the INT interrupt stores the
 * MCU time of every falling edge (one per sample while the reader clears the
 * flag in time). For each FIFO read the reader looks up the last edge at or
 * before its read time: that edge belongs to the newest sample read, so the
 * packet can be anchored on the sample clock itself instead of the read time,
 * and read time minus edge time is the read latency.
 *
 * The edges counted since the previous read must equal the samples read; a
 * mismatch (an edge lost because the flag was still set, or an edge of a
 * sample not read yet) makes the edge anchor doubtful, so it is counted and
 * the read time is kept for that packet. An edge between the time taken just
 * before the FIFO pointer read and the read time may belong to a sample that
 * the pointers did or did not include: that read keeps the read time and the
 * count restarts (review 2026-11-26). The caller disables every other source
 * on the INT pin (ALC_OVF) and breaks on a full FIFO. Header only, built on
 * the host by tests/test_firmware_ppg_edge.py.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#define PPG_EDGE_RING 64u

typedef struct {
    uint64_t t_us[PPG_EDGE_RING];
    uint32_t count; /* edges stored since start; the newest is t_us[(count - 1) % RING] */
} ppg_edge_ring_t;

typedef struct {
    uint32_t reads;     /* FIFO reads with samples */
    uint32_t anchored;  /* reads anchored on an edge */
    uint32_t mismatch;  /* edges since the previous read != samples read */
    uint32_t no_edge;   /* no edge at or before the read time in the ring */
    uint32_t ambiguous; /* an edge during the pointer read */
    int64_t lat_min_us; /* read time - edge time, anchored reads only */
    int64_t lat_max_us;
    int64_t lat_sum_us;
} ppg_edge_stats_t;

typedef struct {
    uint32_t prev_edges; /* edges at or before the previous read */
    bool have_prev;      /* false after start or a chip reset: no mismatch check */
    ppg_edge_stats_t stats;
} ppg_edge_t;

static inline void ppg_edge_push(ppg_edge_ring_t *r, uint64_t t_us)
{
    r->t_us[r->count % PPG_EDGE_RING] = t_us;
    r->count++;
}

static inline void ppg_edge_init(ppg_edge_t *e)
{
    *e = (ppg_edge_t){0};
}

/* A chip reset or a reconfiguration empties the FIFO: the next read has no
 * reference for the edge count. */
static inline void ppg_edge_break(ppg_edge_t *e)
{
    e->have_prev = false;
}

static inline void ppg_edge_stats_reset(ppg_edge_t *e)
{
    e->stats = (ppg_edge_stats_t){0};
}

/*
 * One FIFO read of `samples` samples: `t_pre_us` taken just before the FIFO
 * pointer read, `t_read_us` just after it (the anchor of the research build),
 * with a copy of the ring taken after both. Returns the anchor to use: the
 * newest edge before t_pre_us when the edge count matches, else t_read_us.
 * `*from_edge` says which.
 */
static inline uint64_t ppg_edge_anchor(ppg_edge_t *e, const ppg_edge_ring_t *ring,
                                       uint16_t samples, uint64_t t_pre_us,
                                       uint64_t t_read_us, bool *from_edge)
{
    *from_edge = false;
    /* Edges stored after the read time (the ISR ran while we copied) are not ours. */
    uint32_t n = ring->count;
    uint32_t oldest = n > PPG_EDGE_RING ? n - PPG_EDGE_RING : 0u;
    while (n > oldest && ring->t_us[(n - 1u) % PPG_EDGE_RING] > t_read_us) {
        n--;
    }
    ppg_edge_stats_t *s = &e->stats;
    if (samples == 0) {
        return t_read_us;
    }
    s->reads++;
    if (n > oldest && ring->t_us[(n - 1u) % PPG_EDGE_RING] > t_pre_us) {
        s->ambiguous++;
        e->have_prev = false; /* the count of this read is unknown */
        return t_read_us;
    }
    bool checked = e->have_prev;
    bool match = !checked || n - e->prev_edges == samples;
    e->prev_edges = n;
    e->have_prev = true;
    if (n == oldest) {
        s->no_edge++;
        return t_read_us;
    }
    if (!match) {
        s->mismatch++;
        return t_read_us;
    }
    if (!checked) {
        return t_read_us; /* first read after a break: count not verified */
    }
    uint64_t edge = ring->t_us[(n - 1u) % PPG_EDGE_RING];
    int64_t lat = (int64_t)(t_read_us - edge);
    if (s->anchored == 0 || lat < s->lat_min_us) {
        s->lat_min_us = lat;
    }
    if (s->anchored == 0 || lat > s->lat_max_us) {
        s->lat_max_us = lat;
    }
    s->lat_sum_us += lat;
    s->anchored++;
    *from_edge = true;
    return edge;
}
