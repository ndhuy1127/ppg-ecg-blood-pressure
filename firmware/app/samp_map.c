#include "samp_map.h"

void samp_map_init(samp_map_t *m, uint32_t fs_nominal_mhz, uint64_t tolerance_ns,
                   int64_t holdoff_us, int64_t min_gap_us)
{
    *m = (samp_map_t){
        .state = SAMP_ERROR,
        /* 1e9 ns / (fs_mhz / 1000 Hz) = 1e12 / fs_mhz, rounded. */
        .period_ns = fs_nominal_mhz ? (1000000000000ull + fs_nominal_mhz / 2) / fs_nominal_mhz : 0,
        .tolerance_ns = tolerance_ns,
        .holdoff_us = holdoff_us,
        .min_gap_us = min_gap_us,
    };
}

void samp_map_restart(samp_map_t *m, int64_t now_us)
{
    if (m->started) {
        m->remapped = true;
        m->remap_us = now_us;
        m->remaps++;
    }
    m->started = true;
    m->state = SAMP_UNMAPPED;
    m->next_k = 0;
    m->last_e = 0;
}

bool samp_map_restart_due(const samp_map_t *m, int64_t now_us)
{
    return m->started && m->state == SAMP_ERROR
           && now_us - m->error_since_us >= m->holdoff_us
           && (!m->remapped || now_us - m->remap_us >= m->min_gap_us);
}

void samp_map_error(samp_map_t *m, samp_result_t cause, int64_t now_us)
{
    if (m->state != SAMP_ERROR) {
        m->results[cause]++;
        m->error_since_us = now_us;
    }
    m->state = SAMP_ERROR;
}

static samp_result_t check(const samp_map_t *m, uint32_t k_first, uint16_t n,
                           samp_lookup_fn lookup, void *ctx, int64_t deadline_us,
                           int64_t *last_t)
{
    if (m->state == SAMP_ERROR) {
        return SAMP_IN_ERROR;
    }
    if (n == 0 || k_first != m->next_k) {
        return SAMP_INDEX;
    }
    uint32_t e_last = k_first + n - 1u;
    /* The first packet of an epoch starts at edge 0; later ones at the edge of
     * the previous packet's last sample, so that no interval goes unchecked. */
    uint32_t e = m->state == SAMP_UNMAPPED ? 0 : m->last_e;
    int64_t t;
    if (!lookup(ctx, e, &t)) {
        return SAMP_EDGE_MISSING;
    }
    while (e != e_last) {
        int64_t next;
        if (!lookup(ctx, ++e, &next)) {
            return SAMP_EDGE_MISSING;
        }
        int64_t interval_ns = (next - t) * 1000;
        if (interval_ns < (int64_t)(m->period_ns - m->tolerance_ns)) {
            return SAMP_SHORT;
        }
        if (interval_ns > (int64_t)(m->period_ns + m->tolerance_ns)) {
            return SAMP_LONG;
        }
        t = next;
    }
    if (t > deadline_us) {
        return SAMP_LATE;
    }
    *last_t = t;
    return SAMP_OK;
}

samp_result_t samp_map_packet(samp_map_t *m, uint32_t k_first, uint16_t n,
                              samp_lookup_fn lookup, void *ctx, int64_t deadline_us,
                              int64_t now_us, int64_t *anchor_us)
{
    int64_t last_t = 0;
    samp_result_t r = check(m, k_first, n, lookup, ctx, deadline_us, &last_t);
    if (r != SAMP_OK) {
        samp_map_error(m, r, now_us);
        m->packets_fifo++;
        return r;
    }
    m->state = SAMP_MAPPED;
    m->last_e = k_first + n - 1u;
    m->next_k = k_first + n;
    m->packets_samp++;
    *anchor_us = last_t;
    return SAMP_OK;
}
