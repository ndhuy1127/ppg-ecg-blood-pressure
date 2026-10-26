#include "imu_plan.h"

#include "packet_wire.h"

void imu_index_init(imu_index_t *s, int64_t index_start)
{
    *s = (imu_index_t){.last_sent = index_start - 1};
}

int64_t imu_reanchor_index(int64_t last_prev, int64_t ref_last, int64_t ref_anchor_us,
                           int64_t next_anchor_us, uint32_t fs_nominal_mhz,
                           uint32_t next_count)
{
    int64_t elapsed = next_anchor_us - ref_anchor_us;
    if (elapsed <= 0 || fs_nominal_mhz == 0) {
        return last_prev + 1;
    }
    /* q = round_half_up(elapsed * fs / 1e9), split so that no product overflows. */
    uint64_t whole = (uint64_t)elapsed / 1000000000u;
    uint64_t rest = (uint64_t)elapsed % 1000000000u;
    int64_t q = (int64_t)(whole * fs_nominal_mhz + (rest * fs_nominal_mhz + 500000000u) / 1000000000u);
    int64_t first = ref_last + q - ((int64_t)next_count - 1);
    return first > last_prev + 1 ? first : last_prev + 1;
}

void imu_index_read_failed(imu_index_t *s)
{
    s->reanchor = true;
    s->pending |= PKT_STATUS_AFE_ERROR;
}

size_t imu_plan_read(imu_index_t *s, uint32_t frames, uint64_t anchor_us, bool full,
                     uint32_t fs_nominal_mhz, uint16_t base_status, imu_chunk_t *out,
                     size_t cap)
{
    size_t n = (frames + PKT_MAX_SAMPLES - 1) / PKT_MAX_SAMPLES;
    if (frames == 0 || n > cap) {
        return 0;
    }
    int64_t first = s->last_sent + 1;
    uint16_t head = s->pending;
    if (s->reanchor) {
        /* A full read's anchor is late, so it cannot place its own frames. */
        if (s->have_ref && !full) {
            first = imu_reanchor_index(s->last_sent, s->ref_last, s->ref_anchor_us,
                                       (int64_t)anchor_us, fs_nominal_mhz, frames);
        }
        head |= PKT_STATUS_INDEX_REANCHORED;
    }
    uint16_t all = base_status | (full ? PKT_STATUS_AFE_FIFO_OVERFLOW : 0);
    for (size_t k = 0; k < n; k++) {
        uint32_t start = (uint32_t)k * PKT_MAX_SAMPLES;
        uint32_t count = frames - start < PKT_MAX_SAMPLES ? frames - start : PKT_MAX_SAMPLES;
        bool newest = start + count == frames;
        out[k] = (imu_chunk_t){
            .first_index = (uint32_t)(first + start),
            .count = (uint16_t)count,
            .offset = (uint16_t)start,
            .t_first_us = pkt_t_first_us(anchor_us, (uint16_t)(frames - start), fs_nominal_mhz),
            .status = (uint16_t)(all | (k == 0 ? head : 0) | (newest ? 0 : PKT_STATUS_BACKLOG_CHUNK)),
        };
    }
    s->last_sent = first + frames - 1;
    s->reanchor = full;
    s->pending = 0;
    if (!full) {
        s->have_ref = true;
        s->ref_last = s->last_sent;
        s->ref_anchor_us = (int64_t)anchor_us;
    }
    return n;
}
