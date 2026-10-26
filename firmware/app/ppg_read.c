#include "ppg_read.h"

#include "packet_wire.h"

void ppg_read_init(ppg_read_t *r)
{
    imu_index_init(&r->index, 0);
    r->pending = 0;
    r->needs_reconfigure = false;
}

void ppg_read_reconfigured(ppg_read_t *r)
{
    r->needs_reconfigure = false;
}

uint16_t ppg_read_count(const max30101_latch_t *latch, uint16_t batch)
{
    return latch->waiting >= batch || latch->full ? latch->waiting : 0u;
}

ppg_read_plan_t ppg_read_plan(ppg_read_t *r, const max30101_latch_t *latch, uint16_t count,
                              bool samples_ok, uint64_t anchor_us, uint32_t fs_nominal_mhz,
                              uint16_t base_status)
{
    ppg_read_plan_t plan = {0};
    if (r->needs_reconfigure) {
        plan.reconfigure = true;
        return plan;
    }
    if (latch->status_ok && (latch->status1 & MAX30101_INT_ALC_OVF)) {
        r->pending |= PKT_STATUS_PPG_ALC_OVERFLOW;
    }
    /* A failed Status 1 read may have cleared PWR_RDY; a failed sample read has
     * popped part of the FIFO. Either way only a reset gives a known state. */
    bool samples_failed = count > 0 && !samples_ok;
    bool reset = !latch->status_ok || (latch->status1 & MAX30101_INT_PWR_RDY)
                 || samples_failed;
    if (reset || !latch->pointers_ok) {
        imu_index_read_failed(&r->index);
        if (samples_failed && latch->full) {
            r->pending |= PKT_STATUS_AFE_FIFO_OVERFLOW; /* samples were lost */
        }
        r->needs_reconfigure = reset;
        plan.reconfigure = reset;
        return plan;
    }
    if (count == 0) {
        return plan;
    }
    r->index.pending |= r->pending;
    if (imu_plan_read(&r->index, count, anchor_us, latch->full, fs_nominal_mhz, base_status,
                      &plan.chunk, 1) != 1) {
        return plan;
    }
    r->pending = 0;
    plan.send = true;
    return plan;
}
