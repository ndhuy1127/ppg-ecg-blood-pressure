#include "stim_plan.h"

void stim_plan_init(stim_plan_t *s, uint32_t seed)
{
    s->state = seed != 0u ? seed : 0x9E3779B9u; /* xorshift32 must not start at 0 */
}

uint32_t stim_next_interval_us(stim_plan_t *s)
{
    /* Marsaglia xorshift32; the modulo bias over 2^32 is below 1e-6. */
    uint32_t x = s->state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    s->state = x;
    return STIM_PERIOD_US + x % STIM_JITTER_US;
}
