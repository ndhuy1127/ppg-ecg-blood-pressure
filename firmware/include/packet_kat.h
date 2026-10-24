/*
 * Known answers for the packet encoder, copied from
 * tests/fixtures/packet_v3_expected.json ("crc16_ccitt_false" and
 * "example_packet"). tests/test_firmware_packet_kat.py checks that these values
 * match the fixture and the logger codec (software/data_io/packet_wire.py);
 * the firmware checks its own encoder against them at boot.
 */
#pragma once

#include <stdint.h>

#define KAT_CRC_INPUT "123456789"
#define KAT_CRC_EXPECTED 0x29B1

#define KAT_VERSION 1
#define KAT_CHANNEL_ID 0xE1
#define KAT_SESSION_ID 1
#define KAT_SEQ 2
#define KAT_FIRST_SAMPLE_INDEX 32
#define KAT_T_ANCHOR_US 1063500
#define KAT_T_FIRST_US 1061547
#define KAT_FS_NOMINAL_MHZ 512000
#define KAT_STATUS 0x0011
#define KAT_DATA_0 1193024
#define KAT_DATA_1 65472

static const uint8_t KAT_PACKET[] = {
    0xa5, 0x5a, 0x01, 0xe1, 0x01, 0x00, 0x00, 0x00, 0x02, 0x00,
    0x00, 0x00, 0x20, 0x00, 0x00, 0x00, 0x4c, 0x3a, 0x10, 0x00,
    0x00, 0x00, 0x00, 0x00, 0xab, 0x32, 0x10, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0xd0, 0x07, 0x00, 0x02, 0x00, 0x11, 0x00,
    0x40, 0x34, 0x12, 0x00, 0xc0, 0xff, 0x00, 0x00, 0x43, 0xfd,
};
