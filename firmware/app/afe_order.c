#include "afe_order.h"

#include <string.h>

void afe_order_init(afe_order_t *o)
{
    memset(o, 0, sizeof(*o));
}

void afe_order_lost(afe_order_t *o, uint8_t afe, uint64_t order)
{
    if (order > o->lost[afe - 1u]) {
        o->lost[afe - 1u] = order;
    }
}

bool afe_order_pending(const afe_order_t *o, uint8_t afe)
{
    return o->lost[afe - 1u] != 0;
}

bool afe_order_decide(const afe_order_t *o, uint8_t afe, uint64_t order, bool repeat,
                      bool *bit1)
{
    unsigned i = afe - 1u;
    *bit1 = (o->tx_lost >> i & 1u) != 0 || (o->lost[i] != 0 && order >= o->lost[i]);
    if (repeat) {
        /* Newer than the last sent: still in the AFE queue, it goes out from there. */
        return order == o->sent[i];
    }
    return order > o->sent[i] || (order == o->sent[i] && *bit1);
}

void afe_order_sent(afe_order_t *o, uint8_t afe, uint64_t order, bool queued)
{
    unsigned i = afe - 1u;
    if (order > o->sent[i]) {
        o->sent[i] = order;
    }
    if (order >= o->lost[i]) {
        o->lost[i] = 0; /* carried now, or by the next 0xD2 through tx_lost */
    }
    if (queued) {
        o->tx_lost &= ~(1u << i);
    } else {
        o->tx_lost |= 1u << i;
    }
}
