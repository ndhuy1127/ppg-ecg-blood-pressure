/*
 * When to start and read the MAX30101 die temperature, and the index and STATUS
 * of its 0xB1 packets (Packet Schema V0.2 section 11). Plain C with no ESP-IDF
 * dependency, so the same code can be compiled on a PC.
 *
 * - Tick k is at t0 + k * DIE_TEMP_PERIOD_US on esp_timer; t0 stays across chip
 *   resets. FIRST_SAMPLE_INDEX = k, so every gap has a known length: no bit 5.
 * - A conversion starts at the first call within DIE_TEMP_START_LATE_US of a
 *   tick; a tick reached later gets no value (no error bit). Never two at once.
 * - The result must be read out by tick + DIE_TEMP_DEADLINE_US (the caller
 *   passes the readout time), else it is dropped. So every anchor lies in
 *   [tick, tick + DIE_TEMP_DEADLINE_US], which the logger checks (section 11.2).
 * - A failed start or read, a missed deadline, or a chip reset (die_temp_abort,
 *   called before every reset or reconfiguration: after RESET, TEMP_EN = 0 and
 *   the temperature registers read 0, which would look like a result) sets
 *   bit 3 on the next packet.
 * - Bit 4 is never set (the AFE latency does not apply). T_ANCHOR_US =
 *   T_FIRST_US is the caller's esp_timer right after the readout.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#define DIE_TEMP_PERIOD_US 1000000
#define DIE_TEMP_START_LATE_US 50000
#define DIE_TEMP_DEADLINE_US 100000
#define DIE_TEMP_FS_MHZ 1000u

typedef enum {
    DIE_TEMP_WAIT,  /* nothing to do now */
    DIE_TEMP_START, /* write TEMP_EN, then call die_temp_started */
    DIE_TEMP_POLL,  /* read the result, then call die_temp_polled */
} die_temp_action_t;

typedef enum {
    DIE_TEMP_READ_OK,
    DIE_TEMP_READ_BUSY, /* TEMP_EN still set */
    DIE_TEMP_READ_ERROR,
} die_temp_read_t;

typedef struct {
    int64_t t0_us;
    uint32_t next_tick;  /* first tick no conversion was started for */
    uint32_t tick;       /* tick of the conversion being started or running */
    bool converting;
    int64_t deadline_us; /* tick + DIE_TEMP_DEADLINE_US */
    uint16_t pending;    /* STATUS of the next packet */
} die_temp_t;

typedef struct {
    bool send;
    uint32_t index;      /* FIRST_SAMPLE_INDEX = tick */
    uint16_t status;
} die_temp_packet_t;

/* `t0_us`: when the chip first started measuring in this session. */
void die_temp_init(die_temp_t *t, int64_t t0_us);

die_temp_action_t die_temp_next(die_temp_t *t, int64_t now_us);

/* After DIE_TEMP_START: whether writing TEMP_EN succeeded. */
void die_temp_started(die_temp_t *t, bool ok);

/* After DIE_TEMP_POLL: the read result and `readout_us`, the esp_timer right
 * after the readout (the packet's anchor); a packet to send if it is in time. */
die_temp_packet_t die_temp_polled(die_temp_t *t, die_temp_read_t result,
                                  int64_t readout_us);

/* The chip is reset, being configured again, or unusable: drop any conversion. */
void die_temp_abort(die_temp_t *t);
