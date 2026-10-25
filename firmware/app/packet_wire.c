#include "packet_wire.h"

#include <string.h>

#include "packet_kat.h"

static uint8_t *put_u16(uint8_t *p, uint16_t v)
{
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
    return p + 2;
}

static uint8_t *put_u32(uint8_t *p, uint32_t v)
{
    for (int i = 0; i < 4; i++) {
        p[i] = (uint8_t)(v >> (8 * i));
    }
    return p + 4;
}

static uint8_t *put_u64(uint8_t *p, uint64_t v)
{
    for (int i = 0; i < 8; i++) {
        p[i] = (uint8_t)(v >> (8 * i));
    }
    return p + 8;
}

uint16_t pkt_crc16_ccitt_false(const uint8_t *buf, size_t len)
{
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= (uint16_t)buf[i] << 8;
        for (int bit = 0; bit < 8; bit++) {
            crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021) : (uint16_t)(crc << 1);
        }
    }
    return crc;
}

size_t pkt_encode(const pkt_t *p, uint8_t *out, size_t cap)
{
    if (p->sample_count == 0 || p->sample_count > PKT_MAX_SAMPLES) {
        return 0;
    }
    size_t size = PKT_HEADER_SIZE + 4u * p->sample_count + PKT_CRC_SIZE;
    if (cap < size) {
        return 0;
    }
    uint8_t *w = out;
    *w++ = PKT_SYNC0;
    *w++ = PKT_SYNC1;
    *w++ = PKT_VERSION;
    *w++ = p->channel_id;
    w = put_u32(w, p->session_id);
    w = put_u32(w, p->seq);
    w = put_u32(w, p->first_sample_index);
    w = put_u64(w, p->t_anchor_us);
    w = put_u64(w, p->t_first_us);
    w = put_u32(w, p->fs_nominal_mhz);
    w = put_u16(w, p->sample_count);
    w = put_u16(w, p->status);
    for (uint16_t i = 0; i < p->sample_count; i++) {
        w = put_u32(w, (uint32_t)p->data[i]);
    }
    /* CRC covers bytes 2 .. 39 + 4N: everything after SYNC. */
    put_u16(w, pkt_crc16_ccitt_false(out + 2, size - 2 - PKT_CRC_SIZE));
    return size;
}

uint64_t pkt_t_first_us(uint64_t t_anchor_us, uint16_t n, uint32_t fs_nominal_mhz)
{
    if (fs_nominal_mhz == 0 || n == 0) {
        return t_anchor_us;
    }
    /* (n - 1) * 1e6 us / (fs_mhz / 1000) = (n - 1) * 1e9 / fs_mhz */
    uint64_t offset = ((uint64_t)(n - 1) * 1000000000ull + fs_nominal_mhz / 2) / fs_nominal_mhz;
    return offset > t_anchor_us ? 0 : t_anchor_us - offset;
}

/* NUL-padded ASCII field of 32 bytes; false if text is longer than 31 bytes or
 * not ASCII. */
static bool text_field(const char *text, uint8_t field[PKT_DEVICE_INFO_TEXT_BYTES])
{
    size_t n = 0;
    for (; text[n] != '\0'; n++) {
        if (n == PKT_DEVICE_INFO_TEXT_BYTES - 1 || (uint8_t)text[n] >= 0x80) {
            return false;
        }
    }
    memset(field, 0, PKT_DEVICE_INFO_TEXT_BYTES);
    memcpy(field, text, n);
    return true;
}

bool pkt_device_info_data(const uint8_t elf_sha256[32], const char *app_version,
                          const char *idf_version, int32_t out[PKT_DEVICE_INFO_COUNT])
{
    uint8_t raw[3 * PKT_DEVICE_INFO_TEXT_BYTES];
    memcpy(raw, elf_sha256, 32);
    if (!text_field(app_version, raw + 32) || !text_field(idf_version, raw + 64)) {
        return false;
    }
    out[0] = PKT_DEVICE_INFO_LAYOUT;
    for (size_t k = 0; k < sizeof(raw) / 4; k++) {
        const uint8_t *b = raw + 4 * k;
        uint32_t word = (uint32_t)b[0] << 24 | (uint32_t)b[1] << 16 | (uint32_t)b[2] << 8 | b[3];
        /* Same bit pattern; int32_t is two's complement. */
        memcpy(&out[1 + k], &word, sizeof(word));
    }
    return true;
}

uint16_t pkt_afe_config_data(uint8_t afe, uint8_t source, bool configured, uint32_t generation,
                             const uint32_t *regs, uint16_t n,
                             int32_t out[PKT_MAX_SAMPLES])
{
    bool with_regs = source == PKT_AFE_SOURCE_CHIP && configured;
    if (!with_regs) {
        n = 0;
    }
    if (n > PKT_AFE_MAX_REGS) {
        return 0;
    }
    const uint32_t head[5] = {PKT_AFE_CONFIG_LAYOUT, afe, source, configured ? 1u : 0u,
                              generation};
    memcpy(out, head, sizeof(head)); /* same bit patterns in int32 */
    if (n > 0) {
        memcpy(&out[5], regs, n * sizeof(uint32_t));
    }
    return (uint16_t)(5u + n);
}

void pkt_command_ack_data(uint8_t cmd_id, uint16_t cmd_seq, uint8_t result,
                          uint32_t generation, int32_t out[PKT_COMMAND_ACK_COUNT])
{
    const uint32_t words[PKT_COMMAND_ACK_COUNT] = {PKT_COMMAND_ACK_LAYOUT, cmd_id, cmd_seq,
                                                   result, generation};
    memcpy(out, words, sizeof(words));
}

static bool encodes_to(const pkt_t *p, const uint8_t *expected, size_t size)
{
    uint8_t buf[PKT_MAX_SIZE];
    return pkt_encode(p, buf, sizeof(buf)) == size && memcmp(buf, expected, size) == 0;
}

bool pkt_self_test(void)
{
    const char *crc_input = KAT_CRC_INPUT;
    if (pkt_crc16_ccitt_false((const uint8_t *)crc_input, strlen(crc_input)) != KAT_CRC_EXPECTED) {
        return false;
    }
    if (KAT_VERSION != PKT_VERSION
        || pkt_t_first_us(KAT_T_ANCHOR_US, 2, KAT_FS_NOMINAL_MHZ) != KAT_T_FIRST_US) {
        return false;
    }
    const pkt_t ecg = {
        .channel_id = KAT_CHANNEL_ID,
        .session_id = KAT_SESSION_ID,
        .seq = KAT_SEQ,
        .first_sample_index = KAT_FIRST_SAMPLE_INDEX,
        .t_anchor_us = KAT_T_ANCHOR_US,
        .t_first_us = KAT_T_FIRST_US,
        .fs_nominal_mhz = KAT_FS_NOMINAL_MHZ,
        .sample_count = 2,
        .status = KAT_STATUS,
        .data = {KAT_DATA_0, KAT_DATA_1},
    };
    if (!encodes_to(&ecg, KAT_PACKET, sizeof(KAT_PACKET))) {
        return false;
    }
    pkt_t info = {
        .channel_id = PKT_CH_DEVICE_INFO,
        .session_id = KAT_INFO_SESSION_ID,
        .t_anchor_us = KAT_INFO_T_US,
        .t_first_us = KAT_INFO_T_US,
        .sample_count = PKT_DEVICE_INFO_COUNT,
    };
    return pkt_device_info_data(KAT_INFO_SHA256, KAT_INFO_APP_VERSION, KAT_INFO_IDF_VERSION,
                                info.data)
           && encodes_to(&info, KAT_INFO_PACKET, sizeof(KAT_INFO_PACKET));
}
