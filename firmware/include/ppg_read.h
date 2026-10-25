/*
 * What to do with one MAX30101 FIFO look (Packet Schema V0.1 sections 5.1, 8,
 * 9; V0.2 sections 5 and 7.6): whether to read, the packets' shared index and
 * STATUS, and whether the chip must be configured again. Plain C with no
 * ESP-IDF dependency, so the same code can be compiled on a PC.
 *
 * - Read once at least `batch` samples wait (8 in V1), or whatever waits when
 *   reading on a timer (batch 1), always every sample present at the latch.
 * - A full FIFO (32 samples, FIFO_ROLLOVER_EN = 0): the samples are valid, the
 *   gap lies after the newest one; bit 0 on this read, the next read re-anchors
 *   by time with bit 5 (V0.2 sections 5 and 7.6, as for the IMU, via
 *   imu_plan_read). OVF_COUNTER is not used for the index: samples lost between
 *   the latch and the first pop are not in the latched value.
 * - ALC_OVF sets bit 6 on the next packet sent, even across reads with no packet.
 * - Any failure sends nothing; the next packet re-anchors (bits 3 and 5).
 * - The chip is configured again (max30101_start, retried by the caller) and
 *   nothing is sent until that succeeds after: PWR_RDY (a brownout reset the
 *   registers and FIFO); a failed Status 1 read (it may have cleared PWR_RDY);
 *   a failed sample read (part of the FIFO is popped; bit 0 is kept if it was
 *   full). Flags of a Status 1 that was read count even if the pointer read
 *   then fails; a failed pointer read alone needs no reconfiguration.
 * All slots of one read share FIRST_SAMPLE_INDEX, T_ANCHOR_US and STATUS.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "imu_plan.h"
#include "max30101.h"

typedef struct {
    imu_index_t index;
    uint16_t pending;       /* STATUS bits seen while no packet was sent */
    bool needs_reconfigure; /* until max30101_start succeeds again */
} ppg_read_t;

typedef struct {
    bool send;        /* `chunk` gives the packets of every slot */
    imu_chunk_t chunk;
    bool reconfigure; /* run max30101_start; nothing is sent until it succeeds */
} ppg_read_plan_t;

void ppg_read_init(ppg_read_t *r);

/* max30101_start succeeded after a reconfiguration request. */
void ppg_read_reconfigured(ppg_read_t *r);

/* Samples to read after this latch: all waiting ones once at least `batch`
 * wait or the FIFO is full; 0 otherwise. */
uint16_t ppg_read_count(const max30101_latch_t *latch, uint16_t batch);

/* `latch` as filled by max30101_latch (status_ok, pointers_ok); `count` is what
 * was read (0 if the caller did not read) and `samples_ok` whether that read
 * succeeded; `anchor_us` was taken right after the latch. */
ppg_read_plan_t ppg_read_plan(ppg_read_t *r, const max30101_latch_t *latch, uint16_t count,
                              bool samples_ok, uint64_t anchor_us, uint32_t fs_nominal_mhz,
                              uint16_t base_status);
