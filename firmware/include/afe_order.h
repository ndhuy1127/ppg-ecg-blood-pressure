/*
 * Which AFE states the control task sends as 0xD2, and which carry STATUS bit 1
 * (Packet Schema V0.2 section 12; fixed 2026-10-25). States come from three
 * places: the AFE queue (every transition, in publication order), the latest-state
 * table when a transition never reached that queue, and the 10 s periodic repeat.
 * Per AFE: never a state older than the newest one put to the TX queue; the same
 * state again only as a repeat or to carry bit 1; a repeat waits while the latest
 * state is still in the AFE queue. Bit 1 when an earlier 0xD2 of the AFE was
 * dropped before a SEQ, or when a transition up to this state never reached the
 * AFE queue; such a loss stays latched until a 0xD2 carries it. Orders count each
 * AFE's states from 1 and are 64 bit, so they never wrap. Plain C with no ESP-IDF
 * dependency, so the same code can be compiled on a PC.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#define AFE_ORDER_AFES 3u

typedef struct {
    uint64_t sent[AFE_ORDER_AFES]; /* newest state put to the TX queue, taken or not */
    uint64_t lost[AFE_ORDER_AFES]; /* newest transition not queued nor yet flagged; 0: none */
    uint32_t tx_lost;              /* bit (afe - 1): a 0xD2 was dropped before a SEQ */
} afe_order_t;

void afe_order_init(afe_order_t *o);

/* Transitions of `afe` (1..3) up to `order` never reached the AFE queue. */
void afe_order_lost(afe_order_t *o, uint8_t afe, uint64_t order);

/* Whether `afe` has a lost transition that no 0xD2 has carried yet. */
bool afe_order_pending(const afe_order_t *o, uint8_t afe);

/* Whether to send state `order` of `afe` (`repeat`: the periodic repeat of its
 * latest state); *bit1 tells whether it carries STATUS bit 1. After sending,
 * call afe_order_sent. */
bool afe_order_decide(const afe_order_t *o, uint8_t afe, uint64_t order, bool repeat,
                      bool *bit1);

/* The 0xD2 of state `order` was put to the TX queue; `queued`: the queue took it. */
void afe_order_sent(afe_order_t *o, uint8_t afe, uint64_t order, bool queued);
