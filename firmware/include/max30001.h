/*
 * MAX30001 ECG driver core (datasheet 19-7590, Analog Devices). Plain C with no
 * ESP-IDF dependency: the board passes SPI and delay callbacks, so the same code
 * runs on the ESP32-S3 and in host tests against a simulated chip.
 *
 * SPI (datasheet p. 36-37): one 32-clock frame per register access, command
 * byte = address << 1 | R/W (1 = read) then 24 data bits, MSB first, mode 0.
 * ECG FIFO words (p. 64-65): 18-bit two's complement voltage in D[23:6], ETAG in
 * D[5:3], PTAG in D[2:0]. The FIFO is read in burst mode (0x20) in one CS frame
 * until the EOF tag, so the read ends on the last sample available.
 *
 * Configuration of the V1-module (configs/hardware/custom_board_proposal.md A.2,
 * decided 2026-10-23..25): 512 sps (FMSTR 00), gain 20 V/V, DLPF 40.96 Hz,
 * DHPF off, DC lead-off 10 nA / VMID +- 400 mV, automatic fast recovery, no
 * internal lead bias, BioZ/PACE/R-to-R off, INTB = ECG FIFO threshold (EFIT 15,
 * 16 samples), INT2B = SAMP every sample (self-clearing), both CMOS outputs.
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Registers (p. 38-40). */
#define MAX30001_STATUS 0x01u
#define MAX30001_EN_INT 0x02u
#define MAX30001_EN_INT2 0x03u
#define MAX30001_MNGR_INT 0x04u
#define MAX30001_MNGR_DYN 0x05u
#define MAX30001_SW_RST 0x08u
#define MAX30001_SYNCH 0x09u
#define MAX30001_FIFO_RST 0x0Au
#define MAX30001_INFO 0x0Fu
#define MAX30001_CNFG_GEN 0x10u
#define MAX30001_CNFG_CAL 0x12u
#define MAX30001_CNFG_EMUX 0x14u
#define MAX30001_CNFG_ECG 0x15u
#define MAX30001_ECG_FIFO_BURST 0x20u
#define MAX30001_ECG_FIFO 0x21u

/* STATUS bits (p. 41-42). */
#define MAX30001_ST_EINT (1u << 23)
#define MAX30001_ST_EOVF (1u << 22)
#define MAX30001_ST_FSTINT (1u << 21)
#define MAX30001_ST_DCLOFFINT (1u << 20)
#define MAX30001_ST_SAMP (1u << 9)
#define MAX30001_ST_PLLINT (1u << 8)
#define MAX30001_ST_LDOFF_MASK 0x00000Fu

/* EN_INT2 bit that routes SAMP to INT2B (p. 43). */
#define MAX30001_EN_SAMP (1u << 9)

/* ECG FIFO data tags, ETAG = D[5:3] (p. 65, Table 48). */
enum {
    MAX30001_ETAG_VALID = 0,
    MAX30001_ETAG_FAST = 1,
    MAX30001_ETAG_VALID_EOF = 2,
    MAX30001_ETAG_FAST_EOF = 3,
    MAX30001_ETAG_EMPTY = 6,
    MAX30001_ETAG_OVERFLOW = 7,
};

#define MAX30001_FIFO_DEPTH 32u

typedef enum {
    MAX30001_OK = 0,
    MAX30001_ERR_BUS,      /* the SPI callback failed */
    MAX30001_ERR_INFO,     /* INFO does not have the MAX30001 pattern */
    MAX30001_ERR_READBACK, /* a configuration register reads back differently */
    MAX30001_ERR_PLL,      /* the PLL did not lock in time */
} max30001_err_t;

typedef struct {
    void *ctx;
    /* Drive CSB: active = true pulls it low. */
    void (*cs)(void *ctx, bool active);
    /* Full-duplex transfer of n bytes inside the current CS frame; 0 = ok. */
    int (*xfer)(void *ctx, const uint8_t *tx, uint8_t *rx, size_t n);
    void (*delay_ms)(void *ctx, uint32_t ms);
} max30001_bus_t;

/* Register words written at start, in this order, and checked by reading back
 * the bits the datasheet defines (don't-care bits are masked). */
typedef struct {
    uint32_t cnfg_gen;
    uint32_t cnfg_cal;
    uint32_t cnfg_emux;
    uint32_t cnfg_ecg;
    uint32_t mngr_int;
    uint32_t mngr_dyn;
    uint32_t en_int;
    uint32_t en_int2;
} max30001_regs_t;

typedef struct {
    uint16_t n;                 /* FIFO words read, EOF/empty/overflow word included */
    uint16_t samples;           /* time steps: tags 000, 001, 010, 011 */
    /* Raw 24-bit word of each time step: the packet DATA keeps ETAG/PTAG
     * (Packet Schema V0.1 section 8). */
    uint32_t word[MAX30001_FIFO_DEPTH];
    int32_t value[MAX30001_FIFO_DEPTH]; /* ADC counts of the time steps, -131072..131071 */
    uint8_t etag[MAX30001_FIFO_DEPTH];  /* tag of each time step */
    bool eof;                   /* the read ended on an EOF tag */
    bool empty;                 /* the read ended on an empty word (110) */
    bool overflow;              /* an overflow word (111) was read: data corrupted */
    bool bad_tag;               /* an unused tag (10x) was read: stop, as corrupted */
    uint16_t fast;              /* time steps taken in fast recovery (voltage invalid) */
} max30001_fifo_t;

/* Decided V1-module configuration (see the file comment). */
void max30001_v1_regs(max30001_regs_t *regs);

/* The 8 register words of a 0xD2 packet (Packet Schema V0.2 section 12),
 * address << 24 | 24-bit value: CNFG_GEN, CNFG_CAL, CNFG_EMUX, CNFG_ECG,
 * MNGR_INT, MNGR_DYN, EN_INT, EN_INT2. Returns 8. */
#define MAX30001_CONFIG_WORDS 8u
unsigned max30001_config_words(const max30001_regs_t *regs,
                               uint32_t out[MAX30001_CONFIG_WORDS]);

/* The same configuration with the internal calibration source on both inputs
 * (bipolar 0.5 mV square wave at 1 Hz, inputs disconnected, p. 50-51): a
 * bring-up self test without a person or a signal generator. */
void max30001_cal_regs(const max30001_regs_t *base, max30001_regs_t *regs);

int max30001_write(const max30001_bus_t *bus, uint8_t reg, uint32_t value);
int max30001_read(const max30001_bus_t *bus, uint8_t reg, uint32_t *value);

/* SW_RST, check INFO, write and read back every register of `regs`, then wait
 * up to `pll_timeout_ms` for the PLL to lock (PLLINT clear on two successive
 * STATUS reads). Conversions run after this but the record starts with
 * max30001_restart. `info` (optional) gets the INFO word. */
/* While running: INFO still says MAX30001 and every register written at start
 * reads back the same on its defined bits. A reset (brownout) leaves the
 * registers at their defaults and the ECG silent with INTB high, so only this
 * check notices it. Reads only; the FIFO is not touched. */
max30001_err_t max30001_check(const max30001_bus_t *bus, const max30001_regs_t *regs);

max30001_err_t max30001_start(const max30001_bus_t *bus, const max30001_regs_t *regs,
                              uint32_t pll_timeout_ms, uint32_t *info);

/* Start a new record (datasheet SYNCH, p. 46) so that the first SAMP edge
 * after it belongs to the first FIFO sample (Packet Schema V0.2 section 7.2):
 * mask SAMP on INT2B, call `between` (the caller clears its edge ring and
 * restarts its mapping), send SYNCH, unmask SAMP. `regs` gives EN_INT2. */
max30001_err_t max30001_restart(const max30001_bus_t *bus, const max30001_regs_t *regs,
                                void (*between)(void *arg), void *arg);

/* Read the ECG FIFO in one burst frame up to the EOF tag (or an empty or
 * overflow word, or 32 words). Never reads past the EOF word (p. 64). */
max30001_err_t max30001_read_fifo(const max30001_bus_t *bus, max30001_fifo_t *out);

/* Split a FIFO word into its sign-extended 18-bit value and ETAG. */
void max30001_parse_word(uint32_t word, int32_t *value, uint8_t *etag);

/* Commands that need DIN = 0 (p. 46). */
int max30001_command(const max30001_bus_t *bus, uint8_t reg);
