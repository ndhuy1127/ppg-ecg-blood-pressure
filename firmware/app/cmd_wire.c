#include "cmd_wire.h"

#include <string.h>

#include "packet_wire.h"

void cmd_parser_init(cmd_parser_t *p)
{
    p->n = 0;
    p->dropped = 0;
}

/* Size of the frame starting at buf[0] once its LEN is known, else 0. */
static size_t frame_size(const cmd_parser_t *p)
{
    return p->n >= CMD_HEADER_SIZE ? CMD_HEADER_SIZE + p->buf[6] + 2u : 0u;
}

static bool frame_valid(const cmd_parser_t *p)
{
    size_t body = CMD_HEADER_SIZE + p->buf[6];
    uint16_t crc = (uint16_t)(p->buf[body] | (p->buf[body + 1] << 8));
    return p->buf[2] == CMD_VERSION && pkt_crc16_ccitt_false(&p->buf[2], body - 2u) == crc;
}

/* Drop the first `k` buffered bytes, then everything up to the next SYNC0. */
static void shift(cmd_parser_t *p, size_t k)
{
    while (k < p->n && p->buf[k] != CMD_SYNC0) {
        k++;
    }
    memmove(p->buf, &p->buf[k], p->n - k);
    p->n -= k;
}

/* Settle the buffer after a new byte: emit complete valid frames, drop bad
 * starts; leave a possible frame prefix in place. */
static void settle(cmd_parser_t *p, void (*on_frame)(void *ctx, const cmd_frame_t *frame),
                   void *ctx)
{
    while (p->n > 0) {
        bool bad = (p->n >= 2 && p->buf[1] != CMD_SYNC1)
                   || (p->n >= CMD_HEADER_SIZE && p->buf[6] > CMD_MAX_PARAMS);
        size_t size = bad ? 0u : frame_size(p);
        if (!bad && (size == 0u || p->n < size)) {
            return; /* a prefix: wait for more bytes */
        }
        if (!bad && frame_valid(p)) {
            cmd_frame_t f = {
                .id = p->buf[3],
                .seq = (uint16_t)(p->buf[4] | (p->buf[5] << 8)),
                .len = p->buf[6],
            };
            memcpy(f.params, &p->buf[CMD_HEADER_SIZE], f.len);
            shift(p, size);
            on_frame(ctx, &f);
            continue;
        }
        if (p->n >= CMD_HEADER_SIZE) {
            p->dropped++; /* CRC, version or LEN */
        }
        shift(p, 1u); /* search again from the byte after this SYNC0 */
    }
}

void cmd_parser_feed(cmd_parser_t *p, const uint8_t *data, size_t n,
                     void (*on_frame)(void *ctx, const cmd_frame_t *frame), void *ctx)
{
    for (size_t i = 0; i < n; i++) {
        if (p->n == 0 && data[i] != CMD_SYNC0) {
            continue;
        }
        p->buf[p->n++] = data[i];
        settle(p, on_frame, ctx);
    }
}

size_t cmd_encode(uint8_t id, uint16_t seq, const uint8_t *params, uint8_t len, uint8_t *out,
                  size_t cap)
{
    size_t size = CMD_HEADER_SIZE + len + 2u;
    if (len > CMD_MAX_PARAMS || cap < size) {
        return 0;
    }
    out[0] = CMD_SYNC0;
    out[1] = CMD_SYNC1;
    out[2] = CMD_VERSION;
    out[3] = id;
    out[4] = (uint8_t)seq;
    out[5] = (uint8_t)(seq >> 8);
    out[6] = len;
    if (len > 0) {
        memcpy(&out[CMD_HEADER_SIZE], params, len);
    }
    uint16_t crc = pkt_crc16_ccitt_false(&out[2], CMD_HEADER_SIZE - 2u + len);
    out[CMD_HEADER_SIZE + len] = (uint8_t)crc;
    out[CMD_HEADER_SIZE + len + 1u] = (uint8_t)(crc >> 8);
    return size;
}
