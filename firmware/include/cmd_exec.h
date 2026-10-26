/*
 * What to do with one command frame (Packet Schema V0.2 section 13): answer at
 * once, or ask the PPG reader to apply new LED currents. Remembers the last
 * request that was carried out, so a retry with the same bytes gets the same
 * answer without touching the chip, and a CMD_SEQ reused with other bytes is
 * refused. BUSY means "not done" and is not remembered. Plain C with no ESP-IDF
 * dependency, so the same code can be compiled on a PC.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "cmd_wire.h"

/* LED code limit per code (section 13, provisional): 0x7F = 25.4 mA per sink. */
#define CMD_LED_CODE_MAX 0x7Fu
#define CMD_SET_PPG_LED_LEN 7u /* SESSION_ID (uint32), green, red, IR */

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
} cmd_exec_t;

typedef struct {
    bool apply_led; /* ask the PPG reader; then call cmd_exec_done with its answer */
    uint8_t green, red, ir;
    uint8_t result;      /* when !apply_led: the answer */
    uint32_t generation; /* when !apply_led */
    bool repeat;         /* the answer of an earlier identical request */
} cmd_action_t;

void cmd_exec_init(cmd_exec_t *e);

cmd_action_t cmd_exec_decide(cmd_exec_t *e, const cmd_frame_t *f, uint32_t session_id,
                             cmd_ppg_state_t ppg);

/* The answer to `f` was sent: remember it (not BUSY, REQUEST_REUSED or a repeat). */
void cmd_exec_done(cmd_exec_t *e, const cmd_frame_t *f, uint8_t result, uint32_t generation);
