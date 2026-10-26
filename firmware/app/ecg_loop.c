#include "ecg_loop.h"

void ecg_loop_init(ecg_loop_t *l, int64_t now)
{
    l->down = false;
    ecg_loop_up(l, now);
    l->next_start_us = 0;
}

bool ecg_loop_start_due(ecg_loop_t *l, int64_t now)
{
    if (!l->down || now < l->next_start_us) {
        return false;
    }
    l->next_start_us = now + ECG_RESTART_US;
    return true;
}

void ecg_loop_up(ecg_loop_t *l, int64_t now)
{
    l->down = false;
    l->last_samples_us = now;
    l->next_check_us = now + ECG_CHECK_US;
}

bool ecg_loop_check_due(ecg_loop_t *l, int64_t now, bool *dead)
{
    *dead = !l->down && now - l->last_samples_us > ECG_DEAD_US;
    if (l->down || (now < l->next_check_us && !*dead)) {
        return false;
    }
    l->next_check_us = now + ECG_CHECK_US;
    return true;
}

void ecg_loop_down(ecg_loop_t *l, int64_t now)
{
    l->down = true;
    l->next_start_us = now;
}

bool ecg_loop_read_due(const ecg_loop_t *l, int64_t now, bool woke, bool intb_low,
                       bool synch_due)
{
    return !l->down && (woke || intb_low || synch_due
                        || now - l->last_samples_us > ECG_STALL_US);
}

void ecg_loop_samples(ecg_loop_t *l, int64_t t_read)
{
    l->last_samples_us = t_read;
}
