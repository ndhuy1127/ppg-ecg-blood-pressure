#include "ecg_rate.h"

void ecg_rate_init(ecg_rate_t *r)
{
    r->started = false;
    r->k0 = 0;
    r->t0_us = 0;
    r->windows = 0;
    r->faults = 0;
    r->last_ppm = 0.0;
}

void ecg_rate_reset(ecg_rate_t *r)
{
    r->started = false;
}

bool ecg_rate_packet(ecg_rate_t *r, uint32_t k, int64_t t_us, uint32_t fs_nominal_mhz,
                     uint32_t tol_ppm, int64_t window_us)
{
    if (!r->started) {
        r->started = true;
        r->k0 = k;
        r->t0_us = t_us;
        return false;
    }
    int64_t elapsed = t_us - r->t0_us;
    if (elapsed < window_us && elapsed > 0) {
        return false;
    }
    uint32_t steps = k - r->k0; /* modulo 2^32, as on the wire */
    bool fault;
    if (elapsed <= 0 || steps == 0) {
        fault = true;
        r->last_ppm = 0.0;
    } else {
        /* Frequency deviation: measured rate / nominal rate - 1, in ppm (positive
         * when the chip samples faster than nominal). */
        double nominal_us = (double)steps * 1e9 / (double)fs_nominal_mhz;
        r->last_ppm = (nominal_us / (double)elapsed - 1.0) * 1e6;
        fault = r->last_ppm > (double)tol_ppm || r->last_ppm < -(double)tol_ppm;
    }
    r->windows++;
    r->faults += fault ? 1u : 0u;
    r->k0 = k;
    r->t0_us = t_us;
    return fault;
}
