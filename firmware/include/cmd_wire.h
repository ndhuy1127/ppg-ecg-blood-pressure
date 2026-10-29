/*
 * Command frames PC -> device (Packet Schema V0.2 section 13): SYNC 0xA5 0x5B,
 * CMD_VERSION 1, CMD_ID, CMD_SEQ (uint16), LEN (0 .. 16), LEN parameter bytes,
 * CRC-16/CCITT-FALSE over CMD_VERSION .. the last parameter; little-endian. A
 * frame with a wrong CRC, version or length is dropped without an answer and the
 * search for SYNC goes on from the byte after its first SYNC byte. Plain C with
 * no ESP-IDF dependency, so the same code can be compiled on a PC.
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define CMD_SYNC0 0xA5u
#define CMD_SYNC1 0x5Bu
#define CMD_VERSION 0x01u
#define CMD_MAX_PARAMS 16u
#define CMD_HEADER_SIZE 7u /* SYNC, version, id, seq, len */
#define CMD_MAX_FRAME (CMD_HEADER_SIZE + CMD_MAX_PARAMS + 2u)

#define CMD_ID_PING 0x01u
#define CMD_ID_SET_PPG_LED 0x02u
#define CMD_ID_MARK_EVENT 0x03u /* amendment 2026-10-29 */

/* DATA[3] of the 0xD3 acknowledgement. */
#define CMD_RESULT_OK 0
#define CMD_RESULT_UNKNOWN 1
#define CMD_RESULT_BAD_LENGTH 2
#define CMD_RESULT_NO_CHIP 3
#define CMD_RESULT_BUSY 4 /* not done: chip busy, or the event queue full (MARK_EVENT) */
#define CMD_RESULT_CHIP_ERROR 5
#define CMD_RESULT_REQUEST_REUSED 6
#define CMD_RESULT_WRONG_SESSION 7
/* A parameter out of range: an LED code above the ceiling (SET_PPG_LED), an
 * event code other than 2 or 4 (MARK_EVENT). */
#define CMD_RESULT_OUT_OF_RANGE 8

typedef struct {
    uint8_t id;
    uint16_t seq;
    uint8_t len;
    uint8_t params[CMD_MAX_PARAMS];
} cmd_frame_t;

typedef struct {
    uint8_t buf[CMD_MAX_FRAME];
    size_t n;
    uint32_t dropped; /* frames dropped (CRC, version, length) */
} cmd_parser_t;

void cmd_parser_init(cmd_parser_t *p);

/* Feed bytes as they arrive (any split); calls `on_frame` for each valid frame. */
void cmd_parser_feed(cmd_parser_t *p, const uint8_t *data, size_t n,
                     void (*on_frame)(void *ctx, const cmd_frame_t *frame), void *ctx);

/* Build a frame (for tests and tools); returns its size, 0 if len > 16 or cap
 * is too small. */
size_t cmd_encode(uint8_t id, uint16_t seq, const uint8_t *params, uint8_t len, uint8_t *out,
                  size_t cap);
