/*
 * Timing decisions of the MAX30001 reader loop (firmware/app/main.c,
 * BOARD_ECG_REAL; decided 2026-10-25). Every ECG_CHECK_US, and as soon as no
 * sample came for ECG_DEAD_US, the chip is checked (INFO and configuration read
 * back); a failed check or a silent chip puts the loop down, and it tries to
 * start the chip again every ECG_RESTART_US until that works. While up, the FIFO
 * is read on an INTB edge, while INTB is still low, when no sample came for
 * ECG_STALL_US (inside the 62.5 ms the FIFO holds at 512 sps), and right before
 * a SYNCH, so that a mapping restart does not throw away the samples still in the
 * FIFO. Plain C with no ESP-IDF dependency, so the same code can be compiled on a
 * PC.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#define ECG_CHECK_US 1000000LL
#define ECG_STALL_US 40000LL /* inside the FIFO: 32 samples = 62.5 ms at 512 sps */
#define ECG_DEAD_US 2000000LL
#define ECG_RESTART_US 100000LL

typedef struct {
    bool down;              /* the chip failed: no reads until it starts again */
    int64_t last_samples_us; /* read time of the last packet sent (or of the start) */
    int64_t next_check_us;
    int64_t next_start_us;
} ecg_loop_t;

/* The chip has just been started at `now`. */
void ecg_loop_init(ecg_loop_t *l, int64_t now);

/* While down: whether to try a start now (every ECG_RESTART_US). */
bool ecg_loop_start_due(ecg_loop_t *l, int64_t now);

/* A start worked at `now`: up again, the clocks start over. */
void ecg_loop_up(ecg_loop_t *l, int64_t now);

/* While up: whether to check the chip now; *dead tells that no sample came for
 * ECG_DEAD_US (then the chip counts as failed whatever the check says). */
bool ecg_loop_check_due(ecg_loop_t *l, int64_t now, bool *dead);

/* The check failed or the chip is silent: down, first start at `now`. */
void ecg_loop_down(ecg_loop_t *l, int64_t now);

/* While up: whether to read the FIFO this round. `synch_due`: a mapping restart
 * (SYNCH) follows this round, so the FIFO is read first. */
bool ecg_loop_read_due(const ecg_loop_t *l, int64_t now, bool woke, bool intb_low,
                       bool synch_due);

/* A packet was sent from a read at `t_read`. */
void ecg_loop_samples(ecg_loop_t *l, int64_t t_read);
