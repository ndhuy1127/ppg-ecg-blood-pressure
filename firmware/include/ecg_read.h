/*
 * What to do with one MAX30001 ECG FIFO read: which packet to send (if any),
 * its index and STATUS, and whether to reset the FIFO and break the SAMP
 * mapping (Packet Schema V0.1 sections 5.2, 8, 9; V0.2 sections 5 and 7). Plain
 * C with no ESP-IDF dependency, so the same code can be compiled on a PC.
 *
 * - SPI failure: nothing is sent; the next packet re-anchors (bits 3 and 5).
 * - Overflow word or EOVF: the record is corrupted (datasheet p. 41, 64-65), so
 *   the whole drain is dropped, the FIFO is reset (FIFO_RST) and the next
 *   packet re-anchors by time with bits 0 and 5 (V0.1 section 9).
 * - Unused tag (10x): dropped as a read failure (bits 3 and 5), FIFO reset.
 * - A drain without EOF (32 words) holds valid samples, but its FIFO-read
 *   anchor has no bound: it is sent as a full read (bit 0) and the next packet
 *   re-anchors (bit 5), as for a full IMU FIFO (V0.2 section 5).
 * - DCLOFFINT (bit 2) and PLLINT (bit 3) are latched until a STATUS read; they
 *   are kept until the next packet that is sent, even across empty reads.
 * - The index follows imu_plan_read. A time re-anchor or a PLL unlock breaks
 *   the SAMP mapping, since k may no longer count the edges one to one.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "imu_plan.h"
#include "max30001.h"
#include "samp_map.h"

typedef struct {
    imu_index_t index;
    uint16_t pending; /* STATUS bits seen while no packet was sent */
} ecg_read_t;

typedef struct {
    bool send;          /* `chunk` is a packet to send */
    imu_chunk_t chunk;
    bool fifo_reset;    /* send FIFO_RST now */
    bool mapping_error; /* put the SAMP mapping in the error state with `cause` */
    samp_result_t cause;
} ecg_read_plan_t;

/* New epoch with index 0; `restarted` puts bit 5 on its first packet (after a
 * SYNCH that followed earlier data, not at boot) and keeps the STATUS bits not
 * sent yet (overflow, lead-off, AFE error) for it. */
void ecg_read_init(ecg_read_t *r, bool restarted);

/* `bus_ok`: the FIFO and STATUS reads both succeeded; `status_reg` is STATUS. */
ecg_read_plan_t ecg_read_plan(ecg_read_t *r, const max30001_fifo_t *f, bool bus_ok,
                              uint32_t status_reg, uint64_t t_read_us,
                              uint32_t fs_nominal_mhz, uint16_t base_status);
