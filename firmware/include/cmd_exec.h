/*
 * What to do with one command frame (Packet Schema V0.2 section 13): answer at
 * once, ask the PPG reader to apply new LED currents, or mark an event
 * (MARK_EVENT). Remembers the latest request, in the order received, that was
 * carried out, so a retry with the same bytes gets the same answer without
 * touching the chip or marking a second event, and a CMD_SEQ reused with other
 * bytes is refused. An LED change that finishes after a later request was
 * already remembered does not displace it (each decision takes a ticket in
 * arrival order). BUSY means "not done" and is not remembered. Plain C with no
 * ESP-IDF dependency, so the same code can be compiled on a PC.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "cmd_wire.h"

/* LED code ceiling per code (section 13, decided 2026-10-29): 0x7F = 25.4 mA per
 * sink, the ceiling for the whole study. It may be lowered after bring-up and
 * raised only by a dated amendment of the spec; the PC limit
 * (software/data_io/command_wire.py LED_CODE_MAX) changes with it. */
#define CMD_LED_CODE_MAX 0x7Fu
#define CMD_SET_PPG_LED_LEN 7u /* SESSION_ID (uint32), green, red, IR */
#define CMD_MARK_EVENT_LEN 1u  /* event code: 2 (CUFF_END) or 4 (OPERATOR_MARK) */

typedef enum {
    CMD_PPG_NONE,  /* fake PPG, or the chip was given up */
    CMD_PPG_BUSY,  /* awaiting reconfiguration */
    CMD_PPG_READY,
} cmd_ppg_state_t;

typedef struct {
    bool have_last;
    cmd_frame_t last;
    uint8_t result;
    uint32_t generation;
    uint32_t last_ticket; /* arrival order of `last` */
    uint32_t tickets;     /* decisions made so far */
} cmd_exec_t;

typedef struct {
    bool apply_led; /* ask the PPG reader; then call cmd_exec_done with its answer */
    uint8_t green, red, ir;
    /* Send an event packet 0xC1 with event_code, timed when the frame was
     * received; then call cmd_exec_done with OK, or BUSY if it could not be
     * queued. */
    bool mark_event;
    uint8_t event_code;
    uint8_t result;      /* when neither: the answer */
    uint32_t generation; /* when neither */
    bool repeat;         /* the answer of an earlier identical request */
    uint32_t ticket;     /* arrival order of this decision; give it to cmd_exec_done */
} cmd_action_t;

void cmd_exec_init(cmd_exec_t *e);

cmd_action_t cmd_exec_decide(cmd_exec_t *e, const cmd_frame_t *f, uint32_t session_id,
                             cmd_ppg_state_t ppg);

/* The answer to `f` (decided with `ticket`) was sent: remember it, unless it is
 * BUSY, REQUEST_REUSED or a repeat, or a request received later is remembered
 * already (an LED change that finished after it). */
void cmd_exec_done(cmd_exec_t *e, const cmd_frame_t *f, uint8_t result, uint32_t generation,
                   uint32_t ticket);
