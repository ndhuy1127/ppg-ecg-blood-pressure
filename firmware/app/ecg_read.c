#include "ecg_read.h"

#include "packet_wire.h"

void ecg_read_init(ecg_read_t *r, bool restarted)
{
    /* Flags not sent yet survive a restart (they describe data before it). */
    uint16_t carry = restarted ? (uint16_t)(r->pending | r->index.pending) : 0u;
    imu_index_init(&r->index, 0);
    r->pending = restarted ? (uint16_t)(carry | PKT_STATUS_INDEX_REANCHORED) : 0u;
}

ecg_read_plan_t ecg_read_plan(ecg_read_t *r, const max30001_fifo_t *f, bool bus_ok,
                              uint32_t status_reg, uint64_t t_read_us,
                              uint32_t fs_nominal_mhz, uint16_t base_status)
{
    ecg_read_plan_t plan = {.cause = SAMP_AFE};
    if (!bus_ok) {
        imu_index_read_failed(&r->index);
        plan.mapping_error = true;
        return plan;
    }
    if (status_reg & MAX30001_ST_DCLOFFINT) {
        r->pending |= PKT_STATUS_ECG_LEAD_OFF;
    }
    if (status_reg & MAX30001_ST_PLLINT) {
        r->pending |= PKT_STATUS_AFE_ERROR;
        plan.mapping_error = true;
    }
    bool overflow = f->overflow || (status_reg & MAX30001_ST_EOVF);
    if (overflow) {
        r->index.reanchor = true;
        r->pending |= PKT_STATUS_AFE_FIFO_OVERFLOW;
        plan.fifo_reset = true;
        plan.mapping_error = true;
        plan.cause = SAMP_OVERFLOW;
    }
    if (f->bad_tag) {
        imu_index_read_failed(&r->index);
        plan.fifo_reset = true;
        plan.mapping_error = true;
    }
    if (overflow || f->bad_tag) {
        return plan;
    }
    if (f->samples == 0) {
        return plan;
    }
    bool reanchor = r->index.reanchor;
    r->index.pending |= r->pending;
    if (imu_plan_read(&r->index, f->samples, t_read_us, !f->eof, fs_nominal_mhz,
                      base_status, &plan.chunk, 1) != 1) {
        return plan;
    }
    r->pending = 0;
    plan.send = true;
    if (reanchor) {
        plan.mapping_error = true;
        plan.cause = SAMP_INDEX;
    }
    return plan;
}
