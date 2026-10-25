/*
 * MAX30101 PPG driver core; see max30101.h. Page numbers refer to the datasheet
 * (19-8453 Rev 2).
 */
#include "max30101.h"

#include <string.h>

/* Waits that the datasheet does not specify; engineering choices. */
#define RESET_POLL_MS 1u
#define RESET_POLLS 20u

/* Register bits that read back as written (unused bits masked, p. 11-12). */
#define MASK_MULTI_LED 0x77u
#define MASK_INT_ENABLE1 0xE0u
#define MASK_INT_ENABLE2 0x02u
#define MASK_MODE 0xC7u

void max30101_v1_regs(max30101_regs_t *regs, unsigned pulse_width_us)
{
    memset(regs, 0, sizeof(*regs));
    /* FIFO Configuration (p. 18): SMP_AVE 000 (no averaging), FIFO_ROLLOVER_EN
     * 0 (a full FIFO keeps its samples, Packet Schema V0.1 section 9),
     * FIFO_A_FULL 0xF (17 unread; its interrupt stays disabled). */
    regs->fifo_config = 0x0Fu;
    /* SpO2 Configuration (p. 19-20): SPO2_ADC_RGE 11 (16 384 nA), SPO2_SR 010
     * (200 sps), LED_PW 11 (411 us, 18 bit) or 10 (215 us, 17 bit). */
    regs->spo2_config = (uint8_t)((3u << 5) | (2u << 2) | (pulse_width_us == 215u ? 2u : 3u));
    /* LED Pulse Amplitude (p. 21): red and IR 0x24 = 7.2 mA; green 0x12 = 3.6 mA
     * in each of its two sinks, 7.2 mA in all (p. 22). A starting point only. */
    max30101_set_currents(regs, 0x12u, 0x24u, 0x24u);
    /* Multi-LED Mode Control (p. 22): SLOT1 011 green, SLOT2 001 red,
     * SLOT3 010 IR, SLOT4 000 off. */
    regs->multi_led[0] = (uint8_t)((1u << 4) | 3u);
    regs->multi_led[1] = 2u;
    /* Interrupt Enable (p. 14): PPG_RDY and ALC_OVF; no A_FULL, no DIE_TEMP_RDY
     * (the temperature is polled). */
    regs->int_enable[0] = MAX30101_INT_PPG_RDY | MAX30101_INT_ALC_OVF;
    regs->int_enable[1] = 0u;
}

void max30101_set_currents(max30101_regs_t *regs, uint8_t green, uint8_t red, uint8_t ir)
{
    regs->led_pa[0] = red;   /* LED1 */
    regs->led_pa[1] = ir;    /* LED2 */
    regs->led_pa[2] = green; /* LED3 */
    regs->led_pa[3] = green; /* LED4: the slot 011 drives LED3 and LED4 (p. 22) */
}

int max30101_write_reg(const max30101_bus_t *bus, uint8_t reg, uint8_t value)
{
    return bus->write(bus->ctx, reg, &value, 1);
}

int max30101_read_reg(const max30101_bus_t *bus, uint8_t reg, uint8_t *value)
{
    return bus->read(bus->ctx, reg, value, 1);
}

static bool same(const uint8_t *a, const uint8_t *b, size_t n, uint8_t mask)
{
    for (size_t i = 0; i < n; i++) {
        if ((a[i] ^ b[i]) & mask) {
            return false;
        }
    }
    return true;
}

max30101_err_t max30101_start(const max30101_bus_t *bus, const max30101_regs_t *regs,
                              uint8_t *rev_id)
{
    uint8_t value = 0;
    /* RESET clears itself once every register is back at its POR state (p. 19). */
    if (max30101_write_reg(bus, MAX30101_MODE_CONFIG, MAX30101_MODE_RESET)) {
        return MAX30101_ERR_BUS;
    }
    for (unsigned i = 0;; i++) {
        bus->delay_ms(bus->ctx, RESET_POLL_MS);
        if (max30101_read_reg(bus, MAX30101_MODE_CONFIG, &value)) {
            return MAX30101_ERR_BUS;
        }
        if (!(value & MAX30101_MODE_RESET)) {
            break;
        }
        if (i + 1 >= RESET_POLLS) {
            return MAX30101_ERR_RESET;
        }
    }
    if (max30101_read_reg(bus, MAX30101_PART_ID, &value)) {
        return MAX30101_ERR_BUS;
    }
    if (value != MAX30101_PART_ID_VALUE) {
        return MAX30101_ERR_PART_ID;
    }
    if (rev_id && max30101_read_reg(bus, MAX30101_REV_ID, rev_id)) {
        return MAX30101_ERR_BUS;
    }
    uint8_t status[2];
    if (bus->read(bus->ctx, MAX30101_INT_STATUS1, status, 2)) { /* clears PWR_RDY */
        return MAX30101_ERR_BUS;
    }
    const struct {
        uint8_t reg;
        const uint8_t *data;
        size_t n;
        uint8_t mask;
    } blocks[] = {
        {MAX30101_FIFO_CONFIG, &regs->fifo_config, 1, 0xFFu},
        {MAX30101_SPO2_CONFIG, &regs->spo2_config, 1, 0xFFu},
        {MAX30101_LED1_PA, regs->led_pa, 4, 0xFFu},
        {MAX30101_MULTI_LED1, regs->multi_led, 2, MASK_MULTI_LED},
        {MAX30101_INT_ENABLE1, &regs->int_enable[0], 1, MASK_INT_ENABLE1},
        {MAX30101_INT_ENABLE2, &regs->int_enable[1], 1, MASK_INT_ENABLE2},
    };
    for (size_t i = 0; i < sizeof(blocks) / sizeof(blocks[0]); i++) {
        if (bus->write(bus->ctx, blocks[i].reg, blocks[i].data, blocks[i].n)) {
            return MAX30101_ERR_BUS;
        }
    }
    for (size_t i = 0; i < sizeof(blocks) / sizeof(blocks[0]); i++) {
        uint8_t back[4];
        if (bus->read(bus->ctx, blocks[i].reg, back, blocks[i].n)) {
            return MAX30101_ERR_BUS;
        }
        if (!same(back, blocks[i].data, blocks[i].n, blocks[i].mask)) {
            return MAX30101_ERR_READBACK;
        }
    }
    /* Empty FIFO in a known state before the mode starts conversions (p. 15-16). */
    const uint8_t zero[3] = {0, 0, 0};
    if (bus->write(bus->ctx, MAX30101_FIFO_WR_PTR, zero, sizeof(zero))
        || max30101_write_reg(bus, MAX30101_MODE_CONFIG, MAX30101_MODE_MULTI_LED)
        || max30101_read_reg(bus, MAX30101_MODE_CONFIG, &value)) {
        return MAX30101_ERR_BUS;
    }
    return (value & MASK_MODE) == MAX30101_MODE_MULTI_LED ? MAX30101_OK : MAX30101_ERR_READBACK;
}

max30101_err_t max30101_latch(const max30101_bus_t *bus, max30101_latch_t *latch)
{
    uint8_t ptr[3];
    *latch = (max30101_latch_t){0};
    latch->status_ok = max30101_read_reg(bus, MAX30101_INT_STATUS1, &latch->status1) == 0;
    if (!latch->status_ok) {
        return MAX30101_ERR_BUS;
    }
    /* Status 1 is cleared now: its flags count even if the pointers fail. */
    latch->pointers_ok = bus->read(bus->ctx, MAX30101_FIFO_WR_PTR, ptr, sizeof(ptr)) == 0;
    if (!latch->pointers_ok) {
        return MAX30101_ERR_BUS;
    }
    uint8_t wr = ptr[0] & 0x1Fu, rd = ptr[2] & 0x1Fu;
    latch->overflow = ptr[1] & 0x1Fu;
    latch->waiting = (uint16_t)((wr + 32u - rd) & 0x1Fu);
    if (latch->waiting == 0 && latch->overflow > 0) {
        latch->waiting = MAX30101_FIFO_DEPTH; /* WR = RD and samples lost: full */
    }
    latch->full = latch->waiting == MAX30101_FIFO_DEPTH;
    return MAX30101_OK;
}

max30101_err_t max30101_read_samples(const max30101_bus_t *bus, uint16_t count,
                                     max30101_samples_t *out)
{
    uint8_t raw[MAX30101_FIFO_DEPTH * MAX30101_SLOTS * 3];
    out->count = 0;
    if (count == 0 || count > MAX30101_FIFO_DEPTH) {
        return MAX30101_OK;
    }
    if (bus->read(bus->ctx, MAX30101_FIFO_DATA, raw, (size_t)count * MAX30101_SLOTS * 3)) {
        return MAX30101_ERR_BUS;
    }
    for (uint16_t s = 0; s < count; s++) {
        for (unsigned k = 0; k < MAX30101_SLOTS; k++) {
            const uint8_t *b = &raw[(s * MAX30101_SLOTS + k) * 3];
            out->value[s][k] = (((uint32_t)b[0] << 16) | ((uint32_t)b[1] << 8) | b[2]) & 0x3FFFFu;
        }
    }
    out->count = count;
    return MAX30101_OK;
}

max30101_err_t max30101_temp_start(const max30101_bus_t *bus)
{
    return max30101_write_reg(bus, MAX30101_TEMP_CONFIG, MAX30101_TEMP_EN)
               ? MAX30101_ERR_BUS
               : MAX30101_OK;
}

max30101_err_t max30101_temp_read(const max30101_bus_t *bus, int32_t *sixteenths)
{
    uint8_t config, t[2];
    if (max30101_read_reg(bus, MAX30101_TEMP_CONFIG, &config)) {
        return MAX30101_ERR_BUS;
    }
    if (config & MAX30101_TEMP_EN) {
        return MAX30101_ERR_BUSY; /* TEMP_EN clears itself when done (p. 23) */
    }
    if (bus->read(bus->ctx, MAX30101_TEMP_INT, t, sizeof(t))) {
        return MAX30101_ERR_BUS;
    }
    /* TINT two's complement in 1 degC, TFRAC 0..15 in 1/16 degC, always added. */
    int32_t whole = t[0] >= 128u ? (int32_t)t[0] - 256 : (int32_t)t[0];
    *sixteenths = whole * 16 + (int32_t)(t[1] & 0x0Fu);
    return MAX30101_OK;
}
