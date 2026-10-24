/*
 * SAMP pulse to ECG sample mapping and the anchor of each ECG packet (Packet
 * Schema V0.2 sections 7.2-7.3). Plain C with no ESP-IDF dependency, so the same
 * code can be compiled on a PC. The edge ring and the capture live with the
 * caller, which passes a lookup function.
 *
 * Edge numbers e restart at 0 with every mapping start (SYNCH), and so does the
 * ECG sample index k of the acquisition, with c = 0: edge e belongs to sample
 * k = e. A packet of N samples from k_first may take its last sample's edge as
 * T_ANCHOR_US (STATUS bit 8) only if every edge from the previous packet's last
 * edge (edge 0 for the first packet of an epoch) to edge k_first + N - 1 is
 * present and every interval between consecutive edges is within the nominal
 * period +- the tolerance. Otherwise the mapping goes to the error state and
 * every later packet uses the FIFO-read anchor until the mapping restarts,
 * which samp_map_restart_due allows `holdoff_us` after the error and at most
 * once per `min_gap_us` (decided 2026-10-24: 1 s and 10 s).
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    SAMP_UNMAPPED, /* epoch started, no packet checked yet */
    SAMP_MAPPED,
    SAMP_ERROR,    /* FIFO-read anchors until the mapping restarts */
} samp_state_t;

typedef enum {
    SAMP_OK = 0,
    SAMP_IN_ERROR,     /* already in the error state */
    SAMP_INDEX,        /* the packet does not continue the previous one */
    SAMP_EDGE_MISSING, /* an edge of the span never came or left the ring */
    SAMP_SHORT,        /* an interval below T - tolerance: an extra edge */
    SAMP_LONG,         /* above T + tolerance: a missed or overwritten edge */
    SAMP_OVERFLOW,     /* the ECG FIFO overflowed (ETAG 111) */
    SAMP_LATE,         /* the last sample's edge came after the bounded wait */
    SAMP_RESULTS,
} samp_result_t;

typedef struct {
    samp_state_t state;
    uint64_t period_ns;    /* nominal sample period, 1 953 125 ns at 512 sps */
    uint64_t tolerance_ns; /* allowed deviation of one edge interval */
    int64_t holdoff_us;    /* time in the error state before a restart */
    int64_t min_gap_us;    /* least time between two restarts after an error */
    uint32_t next_k;       /* FIRST_SAMPLE_INDEX the next packet must have */
    uint32_t last_e;       /* edge of the last sample of the last packet */
    int64_t error_since_us;
    bool started;          /* the first restart (at boot) happened */
    bool remapped;         /* a restart after an error happened */
    int64_t remap_us;      /* time of the last restart after an error */
    /* Counters for the UART0 log (section 7.7). */
    uint32_t packets_samp;
    uint32_t packets_fifo;
    uint32_t remaps;
    uint32_t results[SAMP_RESULTS]; /* cause of each entry into the error state */
} samp_map_t;

/* Returns true and the edge time (esp_timer us) if edge e is in the ring. */
typedef bool (*samp_lookup_fn)(void *ctx, uint32_t e, int64_t *t_us);

/* Nominal rate in millihertz (FS_NOMINAL_MHZ), the interval tolerance and the
 * restart policy. The state starts in the error state: nothing is mapped before
 * the first samp_map_restart. */
void samp_map_init(samp_map_t *m, uint32_t fs_nominal_mhz, uint64_t tolerance_ns,
                   int64_t holdoff_us, int64_t min_gap_us);

/* A new mapping epoch at SYNCH: edge 0 belongs to sample 0. The caller has
 * stopped the conversions and clears its ring at the same time. */
void samp_map_restart(samp_map_t *m, int64_t now_us);

/* True when the restart policy allows a restart now (error state only). */
bool samp_map_restart_due(const samp_map_t *m, int64_t now_us);

/* Enter the error state for a cause the caller found (SAMP_OVERFLOW). */
void samp_map_error(samp_map_t *m, samp_result_t cause, int64_t now_us);

/*
 * Check one ECG packet of n >= 1 samples from k_first. The edge of its last
 * sample must lie at or before deadline_us (the FIFO read time plus the bounded
 * wait of section 7.3, two sample periods). On SAMP_OK, *anchor_us is that edge
 * time and the packet sets STATUS bit 8; otherwise *anchor_us is untouched, the
 * state is SAMP_ERROR and the caller sends the FIFO-read anchor without bit 8.
 */
samp_result_t samp_map_packet(samp_map_t *m, uint32_t k_first, uint16_t n,
                              samp_lookup_fn lookup, void *ctx, int64_t deadline_us,
                              int64_t now_us, int64_t *anchor_us);
