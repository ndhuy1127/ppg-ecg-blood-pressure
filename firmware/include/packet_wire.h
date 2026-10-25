/*
 * Packet Schema V0.2 encoder (configs/hardware/Packet_Schema_V0.2.md; the byte
 * layout is that of V0.1, configs/hardware/Packet_Schema_V0.1.md sections 6, 7,
 * 9, 10). Plain C with no ESP-IDF dependency, so the same code can be compiled
 * on a PC. Every packet is sent with VERSION 0x02 (V0.2 section 1).
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define PKT_VERSION 0x02u
#define PKT_SYNC0 0xA5u
#define PKT_SYNC1 0x5Au
#define PKT_HEADER_SIZE 40u
#define PKT_CRC_SIZE 2u
/* Schema section 12, step 5: at most 32 samples per packet. */
#define PKT_MAX_SAMPLES 32u
#define PKT_MAX_SIZE (PKT_HEADER_SIZE + 4u * PKT_MAX_SAMPLES + PKT_CRC_SIZE)

/* CHANNEL_ID, V0.1 section 7 and V0.2 sections 2, 6 and 11. */
#define PKT_CH_ECG 0xE1u
#define PKT_CH_PPG_SLOT1 0xF1u
#define PKT_CH_PPG_SLOT2 0xF2u
#define PKT_CH_PPG_SLOT3 0xF3u
#define PKT_CH_PPG_SLOT4 0xF4u
#define PKT_CH_EVENT 0xC1u
#define PKT_CH_ACC_X 0xA1u
#define PKT_CH_ACC_Y 0xA2u
#define PKT_CH_ACC_Z 0xA3u
#define PKT_CH_GYR_X 0xA4u
#define PKT_CH_GYR_Y 0xA5u
#define PKT_CH_GYR_Z 0xA6u
#define PKT_CH_DEVICE_INFO 0xD1u
#define PKT_CH_DIE_TEMP 0xB1u

/* STATUS bits, V0.1 section 9 and V0.2 sections 4 and 7; bits 9..15 are
 * reserved and sent as 0. Bit 8 is for ECG only. */
#define PKT_STATUS_AFE_FIFO_OVERFLOW (1u << 0)
#define PKT_STATUS_MCU_BUFFER_OVERFLOW (1u << 1)
#define PKT_STATUS_ECG_LEAD_OFF (1u << 2)
#define PKT_STATUS_AFE_ERROR (1u << 3)
#define PKT_STATUS_LATENCY_UNMEASURED (1u << 4)
#define PKT_STATUS_INDEX_REANCHORED (1u << 5)
#define PKT_STATUS_PPG_ALC_OVERFLOW (1u << 6)
#define PKT_STATUS_BACKLOG_CHUNK (1u << 7)
#define PKT_STATUS_ANCHOR_SAMP (1u << 8)

/* Event codes carried in DATA[0] of a 0xC1 packet, schema section 10. */
#define PKT_EVENT_T0 1
#define PKT_EVENT_CUFF_END 2
#define PKT_EVENT_SYNC_PULSE 3
#define PKT_EVENT_OPERATOR_MARK 4

/* Device info payload 0xD1, V0.2 section 6: layout 1, 25 words. */
#define PKT_DEVICE_INFO_LAYOUT 1
#define PKT_DEVICE_INFO_COUNT 25u
#define PKT_DEVICE_INFO_TEXT_BYTES 32u

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
 * Write SYNC, VERSION, the header fields, DATA and CRC16 (little-endian) into
 * out. Returns the packet size, or 0 when sample_count is 0 or above
 * PKT_MAX_SAMPLES, or cap is too small. A packet is never partly written.
 */
size_t pkt_encode(const pkt_t *p, uint8_t *out, size_t cap);

/*
 * Firmware estimate T_FIRST_US = T_ANCHOR_US - (N - 1) * 1e6 / fs, rounded to
 * the nearest microsecond (schema section 5.3). Returns t_anchor_us when
 * fs_nominal_mhz or n is 0, and 0 if the offset exceeds t_anchor_us.
 */
uint64_t pkt_t_first_us(uint64_t t_anchor_us, uint16_t n, uint32_t fs_nominal_mhz);

/*
 * DATA of a device info packet (V0.2 section 6): out[0] = layout 1, out[1..8]
 * the ELF SHA-256, out[9..16] app_version, out[17..24] idf_version. Each word
 * joins 4 bytes big-endian and keeps the bit pattern (a word >= 2^31 is
 * negative). The texts are NUL-terminated and NUL-padded ASCII of at most 31
 * characters; returns false, leaving out untouched, if one is longer or not
 * ASCII.
 */
bool pkt_device_info_data(const uint8_t elf_sha256[32], const char *app_version,
                          const char *idf_version, int32_t out[PKT_DEVICE_INFO_COUNT]);

/*
 * Boot self-test against packet_kat.h: CRC, T_FIRST_US, an ECG packet with
 * STATUS bit 8 and a device info packet, byte for byte. The firmware sends
 * nothing when it fails.
 */
bool pkt_self_test(void);
