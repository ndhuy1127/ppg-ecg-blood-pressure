/*
 * Packet Schema V0.1 encoder (configs/hardware/Packet_Schema_V0.1.md, sections
 * 6, 7, 9, 10). Plain C with no ESP-IDF dependency, so the same code can be
 * compiled on a PC.
 */
#pragma once

#include <stddef.h>
#include <stdint.h>

#define PKT_VERSION 0x01u
#define PKT_SYNC0 0xA5u
#define PKT_SYNC1 0x5Au
#define PKT_HEADER_SIZE 40u
#define PKT_CRC_SIZE 2u
/* Schema section 12, step 5: at most 32 samples per FIFO read. */
#define PKT_MAX_SAMPLES 32u
#define PKT_MAX_SIZE (PKT_HEADER_SIZE + 4u * PKT_MAX_SAMPLES + PKT_CRC_SIZE)

/* CHANNEL_ID, schema section 7. */
#define PKT_CH_ECG 0xE1u
#define PKT_CH_PPG_SLOT1 0xF1u
#define PKT_CH_PPG_SLOT2 0xF2u
#define PKT_CH_PPG_SLOT3 0xF3u
#define PKT_CH_PPG_SLOT4 0xF4u
#define PKT_CH_EVENT 0xC1u

/* STATUS bits, schema section 9; bits 7..15 are reserved and sent as 0. */
#define PKT_STATUS_AFE_FIFO_OVERFLOW (1u << 0)
#define PKT_STATUS_MCU_BUFFER_OVERFLOW (1u << 1)
#define PKT_STATUS_ECG_LEAD_OFF (1u << 2)
#define PKT_STATUS_AFE_ERROR (1u << 3)
#define PKT_STATUS_LATENCY_UNMEASURED (1u << 4)
#define PKT_STATUS_INDEX_REANCHORED (1u << 5)
#define PKT_STATUS_PPG_ALC_OVERFLOW (1u << 6)

/* Event codes carried in DATA[0] of a 0xC1 packet, schema section 10. */
#define PKT_EVENT_T0 1
#define PKT_EVENT_CUFF_END 2
#define PKT_EVENT_SYNC_PULSE 3
#define PKT_EVENT_OPERATOR_MARK 4

typedef struct {
    uint8_t channel_id;
    uint32_t session_id;
    uint32_t seq;
    uint32_t first_sample_index;
    uint64_t t_anchor_us;
    uint64_t t_first_us;
    uint32_t fs_nominal_mhz; /* millihertz: 512000 = 512 Hz */
    uint16_t sample_count;
    uint16_t status;
    int32_t data[PKT_MAX_SAMPLES];
} pkt_t;

/* CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, no reflection, xorout 0. */
uint16_t pkt_crc16_ccitt_false(const uint8_t *buf, size_t len);

/*
 * Write SYNC, VERSION 0x01, the header fields, DATA and CRC16 (little-endian)
 * into out. Returns the packet size, or 0 when sample_count is 0 or above
 * PKT_MAX_SAMPLES, or cap is too small. A packet is never partly written.
 */
size_t pkt_encode(const pkt_t *p, uint8_t *out, size_t cap);

/*
 * Firmware estimate T_FIRST_US = T_ANCHOR_US - (N - 1) * 1e6 / fs, rounded to
 * the nearest microsecond (schema section 5.3). Returns t_anchor_us when
 * fs_nominal_mhz or n is 0, and 0 if the offset exceeds t_anchor_us.
 */
uint64_t pkt_t_first_us(uint64_t t_anchor_us, uint16_t n, uint32_t fs_nominal_mhz);
