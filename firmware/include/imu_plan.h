/*
 * Sample index, STATUS and packet split of BMI270 FIFO reads (Packet Schema
 * V0.2 sections 3-5). Plain C with no ESP-IDF dependency, so the same code can
 * be compiled on a PC. The six axes of one read share every value planned here.
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct {
    bool have_ref;         /* a reliable read (not full, not failed) exists */
    int64_t ref_last;      /* last sample index of the last reliable read */
    int64_t ref_anchor_us; /* and its anchor */
    int64_t last_sent;     /* last sample index given out (index_start - 1 first) */
    bool reanchor;         /* the previous read was full or failed */
    uint16_t pending;      /* STATUS for the first packet of the next read */
} imu_index_t;

typedef struct {
    uint32_t first_index; /* FIRST_SAMPLE_INDEX, modulo 2^32 */
    uint16_t count;       /* SAMPLE_COUNT, 1 .. PKT_MAX_SAMPLES */
    uint16_t offset;      /* first frame of this packet within the read */
    uint64_t t_first_us;
    uint16_t status;
} imu_chunk_t;

/* Packets of one read: ceil(170 / 32) for a full 2 KB FIFO of 12-byte frames. */
#define IMU_MAX_CHUNKS 6u

void imu_index_init(imu_index_t *s, int64_t index_start);

/*
 * FIRST_next = max(last_prev + 1, I_ref + q - (M_next - 1)) with
 * q = round_half_up((A_next - A_ref) / T), T = 1e9 / fs_nominal_mhz us (section
 * 5); last_prev + 1 when A_next - A_ref <= 0 or fs is 0. Signed 64-bit; the
 * caller takes it modulo 2^32. Exact for any elapsed time below about 2e18 us.
 */
int64_t imu_reanchor_index(int64_t last_prev, int64_t ref_last, int64_t ref_anchor_us,
                           int64_t next_anchor_us, uint32_t fs_nominal_mhz,
                           uint32_t next_count);

/*
 * A read that failed or returned too few bytes (section 3, step 3): nothing is
 * sent from it; the next read sets bit 3 on its first packet and re-anchors.
 */
void imu_index_read_failed(imu_index_t *s);

/*
 * Plan one read of `frames` frames latched with anchor A (anchor_us); `full`
 * when the latched length leaves no room for one more frame. Writes one chunk
 * per packet of at most 32 frames (section 4: same anchor, T_FIRST_US of the
 * chunk at s = A - round_half_up((M - 1 - s) T), bit 7 on all but the newest).
 * Every chunk gets base_status, and bit 0 if full (section 5). The first chunk
 * of a read after a full or failed read re-anchors: bit 5 (and bit 3 after a
 * failed read), index by imu_reanchor_index from the last reliable read, or
 * last_sent + 1 without one or when this read is full as well. Returns the
 * number of chunks; 0, with the state unchanged, if frames is 0 or the chunks
 * do not fit in cap.
 */
size_t imu_plan_read(imu_index_t *s, uint32_t frames, uint64_t anchor_us, bool full,
                     uint32_t fs_nominal_mhz, uint16_t base_status, imu_chunk_t *out,
                     size_t cap);
