#include "cmd_exec.h"

#include <string.h>

#include "packet_wire.h"

void cmd_exec_init(cmd_exec_t *e)
{
    memset(e, 0, sizeof(*e));
}

static bool same_request(const cmd_frame_t *a, const cmd_frame_t *b)
{
    return a->id == b->id && a->len == b->len && memcmp(a->params, b->params, a->len) == 0;
}

static cmd_action_t answer(uint8_t result)
{
    return (cmd_action_t){.result = result};
}

static cmd_action_t decide(const cmd_exec_t *e, const cmd_frame_t *f, uint32_t session_id,
                           cmd_ppg_state_t ppg)
{
    if (e->have_last && f->seq == e->last.seq) {
        if (!same_request(f, &e->last)) {
            return answer(CMD_RESULT_REQUEST_REUSED);
        }
        cmd_action_t a = answer(e->result);
        a.generation = e->generation;
        a.repeat = true;
        return a;
    }
    if (f->id == CMD_ID_PING) {
        return answer(f->len == 0 ? CMD_RESULT_OK : CMD_RESULT_BAD_LENGTH);
    }
    if (f->id == CMD_ID_MARK_EVENT) {
        /* Only the operator's codes: t0 (1) stays the SW1 button, 3 the sync
         * stimulus the MCU makes itself. Independent of the PPG chip. */
        if (f->len != CMD_MARK_EVENT_LEN) {
            return answer(CMD_RESULT_BAD_LENGTH);
        }
        uint8_t code = f->params[0];
        if (code != PKT_EVENT_CUFF_END && code != PKT_EVENT_OPERATOR_MARK) {
            return answer(CMD_RESULT_OUT_OF_RANGE);
        }
        return (cmd_action_t){.mark_event = true, .event_code = code};
    }
    if (f->id != CMD_ID_SET_PPG_LED) {
        return answer(CMD_RESULT_UNKNOWN);
    }
    if (f->len != CMD_SET_PPG_LED_LEN) {
        return answer(CMD_RESULT_BAD_LENGTH);
    }
    uint32_t target = (uint32_t)f->params[0] | (uint32_t)f->params[1] << 8
                      | (uint32_t)f->params[2] << 16 | (uint32_t)f->params[3] << 24;
    if (target != session_id) {
        return answer(CMD_RESULT_WRONG_SESSION);
    }
    for (unsigned k = 4; k < CMD_SET_PPG_LED_LEN; k++) {
        if (f->params[k] > CMD_LED_CODE_MAX) {
            return answer(CMD_RESULT_OUT_OF_RANGE);
        }
    }
    if (ppg == CMD_PPG_NONE) {
        return answer(CMD_RESULT_NO_CHIP);
    }
    if (ppg == CMD_PPG_BUSY) {
        return answer(CMD_RESULT_BUSY);
    }
    return (cmd_action_t){.apply_led = true, .green = f->params[4], .red = f->params[5],
                          .ir = f->params[6]};
}

cmd_action_t cmd_exec_decide(cmd_exec_t *e, const cmd_frame_t *f, uint32_t session_id,
                             cmd_ppg_state_t ppg)
{
    cmd_action_t a = decide(e, f, session_id, ppg);
    a.ticket = ++e->tickets; /* 2^32 commands never come in one boot */
    return a;
}

void cmd_exec_done(cmd_exec_t *e, const cmd_frame_t *f, uint8_t result, uint32_t generation,
                   uint32_t ticket)
{
    if (result == CMD_RESULT_BUSY || result == CMD_RESULT_REQUEST_REUSED) {
        /* BUSY: not done, a later attempt uses a new CMD_SEQ. REQUEST_REUSED:
         * the remembered request stays, so its own retries still get its answer. */
        return;
    }
    if (e->have_last && ticket < e->last_ticket) {
        /* An LED change that finished after a request received later: keep the
         * later one, so that its retry (a MARK_EVENT, say) still gets its answer
         * instead of being carried out a second time. The PC has given up on
         * the LED change by then and never resends its bytes. */
        return;
    }
    e->have_last = true;
    e->last = *f;
    e->result = result;
    e->generation = generation;
    e->last_ticket = ticket;
}
