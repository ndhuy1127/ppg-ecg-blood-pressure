#include "packet_v01.h"

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
