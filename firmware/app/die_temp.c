#include "die_temp.h"

#include "packet_wire.h"

void die_temp_init(die_temp_t *t, int64_t t0_us)
{
    *t = (die_temp_t){.t0_us = t0_us};
}

static void give_up(die_temp_t *t)
{
    t->converting = false;
    t->next_tick = t->tick + 1u;
    t->pending |= PKT_STATUS_AFE_ERROR;
}

die_temp_action_t die_temp_next(die_temp_t *t, int64_t now_us)
{
    if (t->converting) {
        if (now_us <= t->deadline_us) {
            return DIE_TEMP_POLL;
        }
        give_up(t); /* too late: a result read now is not used either */
    }
    int64_t since = now_us - t->t0_us;
    if (since < 0 || since < (int64_t)t->next_tick * DIE_TEMP_PERIOD_US) {
        return DIE_TEMP_WAIT;
    }
    uint32_t tick = (uint32_t)(since / DIE_TEMP_PERIOD_US); /* the newest tick reached */
    int64_t tick_us = t->t0_us + (int64_t)tick * DIE_TEMP_PERIOD_US;
    if (now_us - tick_us > DIE_TEMP_START_LATE_US) {
        t->next_tick = tick + 1u; /* too late for this tick: no value, no error */
        return DIE_TEMP_WAIT;
    }
    t->tick = tick;
    t->deadline_us = tick_us + DIE_TEMP_DEADLINE_US;
    return DIE_TEMP_START;
}

void die_temp_started(die_temp_t *t, bool ok)
{
    if (!ok) {
        give_up(t);
        return;
    }
    t->converting = true;
}

die_temp_packet_t die_temp_polled(die_temp_t *t, die_temp_read_t result,
                                  int64_t readout_us)
{
    die_temp_packet_t p = {0};
    if (!t->converting || result == DIE_TEMP_READ_BUSY) {
        return p;
    }
    if (result != DIE_TEMP_READ_OK || readout_us > t->deadline_us) {
        give_up(t); /* a result read out after the deadline is not used either */
        return p;
    }
    p.send = true;
    p.index = t->tick;
    p.status = t->pending;
    t->pending = 0;
    t->converting = false;
    t->next_tick = t->tick + 1u;
    return p;
}

void die_temp_abort(die_temp_t *t)
{
    if (t->converting) {
        t->converting = false;
        t->next_tick = t->tick + 1u;
    }
    t->pending |= PKT_STATUS_AFE_ERROR;
}
