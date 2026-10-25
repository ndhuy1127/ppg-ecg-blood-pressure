/*
 * MAX30001 ECG driver core; see max30001.h. Page numbers refer to the
 * datasheet (19-7590).
 */
#include "max30001.h"

#include <string.h>

/* Bits each register defines; the others are don't-care (p. 38-53). */
#define MASK_CNFG_GEN 0xFEFFFFu
#define MASK_CNFG_CAL 0x707FFFu
#define MASK_CNFG_EMUX 0xBF0000u
#define MASK_CNFG_ECG 0xC37000u
#define MASK_MNGR_INT 0xFF007Fu
#define MASK_MNGR_DYN 0xFFFFFFu
#define MASK_EN_INT 0xFFFF03u

/* Waits that the datasheet does not specify; engineering choices. */
#define RESET_SETTLE_MS 10u
#define PLL_POLL_MS 5u

static uint8_t command_byte(uint8_t reg, bool read)
{
    return (uint8_t)((reg << 1) | (read ? 1u : 0u));
}

void max30001_v1_regs(max30001_regs_t *regs)
{
    /* CNFG_GEN (p. 47-49): FMSTR 00 (32 768 Hz), EN_ECG, DC lead-off on ECGP/N
     * (EN_DCLOFF 01) with 10 nA (IMAG 010), pull-up on ECGP (IPOL 0), threshold
     * VMID +- 400 mV (VTH 01); resistive bias off (EN_RBIAS 00), RBIASV left
     * at its default 01. */
    regs->cnfg_gen = (1u << 19) | (1u << 12) | (2u << 8) | (1u << 6) | (1u << 2);
    /* CNFG_CAL (p. 50): calibration source off, FCAL and FIFTY at defaults. */
    regs->cnfg_cal = (4u << 12) | (1u << 11);
    /* CNFG_EMUX (p. 51): both inputs connected (the default isolates them),
     * non-inverted, no calibration input. */
    regs->cnfg_emux = 0u;
    /* CNFG_ECG (p. 52-53): 512 sps (ECG_RATE 00), gain 20 V/V (00), DHPF off,
     * DLPF 01 = 40.96 Hz at 512 sps (Table 33). */
    regs->cnfg_ecg = (1u << 12);
    /* MNGR_INT (p. 44): EFIT 15 (16 unread samples), BFIT default, SAMP every
     * sample (SAMP_IT 00), self-clearing SAMP (CLR_SAMP 1). */
    regs->mngr_int = (15u << 19) | (3u << 16) | (1u << 2);
    /* MNGR_DYN (p. 45): automatic fast recovery (FAST 10) at the default
     * threshold 0x3F; BioZ thresholds at their defaults. */
    regs->mngr_dyn = (2u << 22) | (0x3Fu << 16) | 0xFFFFu;
    /* EN_INT / EN_INT2 (p. 43): INTB = EINT, INT2B = SAMP, both CMOS (01). */
    regs->en_int = (1u << 23) | 1u;
    regs->en_int2 = MAX30001_EN_SAMP | 1u;
}

void max30001_cal_regs(const max30001_regs_t *base, max30001_regs_t *regs)
{
    *regs = *base;
    /* No lead-off current while the inputs are disconnected. */
    regs->cnfg_gen &= ~((3u << 12) | (7u << 8));
    /* EN_VCAL, bipolar (VMODE 1), 0.5 mV (VMAG 1), 1 Hz (FCAL 100), 50 %. */
    regs->cnfg_cal = (1u << 22) | (1u << 21) | (1u << 20) | (4u << 12) | (1u << 11);
    /* Both inputs open; ECGP <- VCALP (10), ECGN <- VCALN (11); keep ECG_POL. */
    regs->cnfg_emux = (base->cnfg_emux & (1u << 23)) | (1u << 21) | (1u << 20)
                      | (2u << 18) | (3u << 16);
}

int max30001_write(const max30001_bus_t *bus, uint8_t reg, uint32_t value)
{
    uint8_t tx[4] = {command_byte(reg, false), (uint8_t)(value >> 16),
                     (uint8_t)(value >> 8), (uint8_t)value};
    uint8_t rx[4];
    bus->cs(bus->ctx, true);
    int err = bus->xfer(bus->ctx, tx, rx, sizeof(tx));
    bus->cs(bus->ctx, false);
    return err;
}

int max30001_read(const max30001_bus_t *bus, uint8_t reg, uint32_t *value)
{
    uint8_t tx[4] = {command_byte(reg, true), 0, 0, 0};
    uint8_t rx[4] = {0};
    bus->cs(bus->ctx, true);
    int err = bus->xfer(bus->ctx, tx, rx, sizeof(tx));
    bus->cs(bus->ctx, false);
    *value = ((uint32_t)rx[1] << 16) | ((uint32_t)rx[2] << 8) | rx[3];
    return err;
}

int max30001_command(const max30001_bus_t *bus, uint8_t reg)
{
    return max30001_write(bus, reg, 0u);
}

static bool info_ok(uint32_t info)
{
    /* INFO (p. 47): D[23:20] = 0101, D[13:12] = 01. */
    return ((info >> 20) & 0xFu) == 0x5u && ((info >> 12) & 0x3u) == 0x1u;
}

max30001_err_t max30001_start(const max30001_bus_t *bus, const max30001_regs_t *regs,
                              uint32_t pll_timeout_ms, uint32_t *info)
{
    const struct {
        uint8_t reg;
        uint32_t value;
        uint32_t mask;
    } writes[] = {
        {MAX30001_CNFG_GEN, regs->cnfg_gen, MASK_CNFG_GEN},
        {MAX30001_CNFG_CAL, regs->cnfg_cal, MASK_CNFG_CAL},
        {MAX30001_CNFG_EMUX, regs->cnfg_emux, MASK_CNFG_EMUX},
        {MAX30001_CNFG_ECG, regs->cnfg_ecg, MASK_CNFG_ECG},
        {MAX30001_MNGR_INT, regs->mngr_int, MASK_MNGR_INT},
        {MAX30001_MNGR_DYN, regs->mngr_dyn, MASK_MNGR_DYN},
        {MAX30001_EN_INT, regs->en_int, MASK_EN_INT},
        {MAX30001_EN_INT2, regs->en_int2, MASK_EN_INT},
    };
    uint32_t value = 0;
    if (max30001_command(bus, MAX30001_SW_RST)) {
        return MAX30001_ERR_BUS;
    }
    bus->delay_ms(bus->ctx, RESET_SETTLE_MS);
    /* The first command after a reset does not read back valid data (p. 47). */
    if (max30001_read(bus, MAX30001_INFO, &value) || max30001_read(bus, MAX30001_INFO, &value)) {
        return MAX30001_ERR_BUS;
    }
    if (info) {
        *info = value;
    }
    if (!info_ok(value)) {
        return MAX30001_ERR_INFO;
    }
    for (size_t i = 0; i < sizeof(writes) / sizeof(writes[0]); i++) {
        if (max30001_write(bus, writes[i].reg, writes[i].value)) {
            return MAX30001_ERR_BUS;
        }
    }
    for (size_t i = 0; i < sizeof(writes) / sizeof(writes[0]); i++) {
        if (max30001_read(bus, writes[i].reg, &value)) {
            return MAX30001_ERR_BUS;
        }
        if ((value ^ writes[i].value) & writes[i].mask) {
            return MAX30001_ERR_READBACK;
        }
    }
    /* PLLINT is latched until a STATUS read (p. 42): two clear reads in a row
     * mean the PLL is locked now, not only that an old flag was cleared. */
    unsigned clear = 0;
    for (uint32_t waited = 0;; waited += PLL_POLL_MS) {
        if (max30001_read(bus, MAX30001_STATUS, &value)) {
            return MAX30001_ERR_BUS;
        }
        clear = (value & MAX30001_ST_PLLINT) ? 0u : clear + 1u;
        if (clear >= 2u) {
            return MAX30001_OK;
        }
        if (waited >= pll_timeout_ms) {
            return MAX30001_ERR_PLL;
        }
        bus->delay_ms(bus->ctx, PLL_POLL_MS);
    }
}

max30001_err_t max30001_restart(const max30001_bus_t *bus, const max30001_regs_t *regs,
                                void (*between)(void *arg), void *arg)
{
    if (max30001_write(bus, MAX30001_EN_INT2, regs->en_int2 & ~MAX30001_EN_SAMP)) {
        return MAX30001_ERR_BUS;
    }
    if (between) {
        between(arg);
    }
    if (max30001_command(bus, MAX30001_SYNCH)
        || max30001_write(bus, MAX30001_EN_INT2, regs->en_int2)) {
        return MAX30001_ERR_BUS;
    }
    return MAX30001_OK;
}

void max30001_parse_word(uint32_t word, int32_t *value, uint8_t *etag)
{
    int32_t raw = (int32_t)((word >> 6) & 0x3FFFFu);
    *value = raw >= 0x20000 ? raw - 0x40000 : raw;
    *etag = (uint8_t)((word >> 3) & 7u);
}

max30001_err_t max30001_read_fifo(const max30001_bus_t *bus, max30001_fifo_t *out)
{
    memset(out, 0, sizeof(*out));
    uint8_t cmd = command_byte(MAX30001_ECG_FIFO_BURST, true);
    uint8_t ignored;
    const uint8_t zeros[3] = {0, 0, 0};
    bus->cs(bus->ctx, true);
    int err = bus->xfer(bus->ctx, &cmd, &ignored, 1);
    while (!err && out->n < MAX30001_FIFO_DEPTH) {
        uint8_t rx[3];
        err = bus->xfer(bus->ctx, zeros, rx, sizeof(rx));
        if (err) {
            break;
        }
        uint32_t word = ((uint32_t)rx[0] << 16) | ((uint32_t)rx[1] << 8) | rx[2];
        int32_t value;
        uint8_t tag;
        max30001_parse_word(word, &value, &tag);
        out->n++;
        if (tag == MAX30001_ETAG_EMPTY) {
            out->empty = true;
            break;
        }
        if (tag == MAX30001_ETAG_OVERFLOW) {
            out->overflow = true;
            break;
        }
        if (tag > MAX30001_ETAG_FAST_EOF) {
            out->bad_tag = true;
            break;
        }
        out->word[out->samples] = word;
        out->value[out->samples] = value;
        out->etag[out->samples] = tag;
        out->samples++;
        if (tag == MAX30001_ETAG_FAST || tag == MAX30001_ETAG_FAST_EOF) {
            out->fast++;
        }
        if (tag == MAX30001_ETAG_VALID_EOF || tag == MAX30001_ETAG_FAST_EOF) {
            out->eof = true;
            break;
        }
    }
    bus->cs(bus->ctx, false);
    return err ? MAX30001_ERR_BUS : MAX30001_OK;
}
