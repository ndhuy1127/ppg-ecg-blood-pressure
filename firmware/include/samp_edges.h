/*
 * Ring of captured SAMP edges (Packet Schema V0.2 section 7.1). The capture
 * callback (or the fake ECG source) pushes the raw latched value; edge numbers
 * e count from 0 after every samp_edges_clear. Each slot keeps its e, so a
 * lookup of an edge that has not come yet or was overwritten by edge e + 64
 * fails. A converter turns the raw value into esp_timer microseconds when it is
 * read, not in the callback.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#define SAMP_RING_LEN 64u /* 125 ms at 512 sps, more than the ECG FIFO holds */

/* Raw latched value to esp_timer us; false if it cannot be converted yet. */
typedef bool (*samp_convert_fn)(int64_t raw, int64_t *t_us);

/* NULL: raw values are already esp_timer us (the fake source). */
void samp_edges_set_converter(samp_convert_fn convert);

/* Empty the ring and restart edge numbering at 0 (mapping start, SYNCH). Call
 * it once before the first push: the zeroed ring would claim edge 0. */
void samp_edges_clear(void);

/* Store the next edge; safe from an ISR and from a task, in IRAM. */
void samp_edges_push(int64_t raw);

/* samp_lookup_fn of samp_map.h; ctx is unused. */
bool samp_edges_lookup(void *ctx, uint32_t e, int64_t *t_us);

/* Wait, polling every tick, until edge e is in the ring or esp_timer passes
 * deadline_us; returns whether it came. An edge may come during the last tick
 * after the deadline: samp_map_packet rejects it by its own time. */
bool samp_edges_wait(uint32_t e, int64_t deadline_us);
