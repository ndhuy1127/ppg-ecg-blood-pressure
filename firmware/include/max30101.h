/*
 * MAX30101 PPG driver core (datasheet 19-8453 Rev 2). Plain C with no ESP-IDF
 * dependency: the board passes I2C and delay callbacks, so the same code runs
 * on the ESP32-S3 and in host tests against a simulated chip.
 *
 * I2C address 0x57 (7 bit). Register reads and writes auto-increment the
 * address, except FIFO_DATA (0x07), whose reads pop the FIFO (p. 15-17).
 *
 * Configuration of the V1-module (configs/hardware/custom_board_proposal.md A.3,
 * decided 2026-10-24..25): multi-LED mode with SLOT1 green, SLOT2 red, SLOT3 IR,
 * 200 sps, no sample averaging, FIFO does not roll over when full, ADC range
 * 16 384 nA, LED pulse width 411 us (18 bit; 215 us is the other candidate,
 * chosen at bring-up), PPG_RDY and ALC_OVF interrupts. LED currents are set per
 * subject (calibrated at the first session, protocol v0.2 section 6.1); the
 * defaults below are only a bring-up starting point.
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define MAX30101_I2C_ADDR 0x57u

/* Registers (p. 11-12). */
#define MAX30101_INT_STATUS1 0x00u
#define MAX30101_INT_STATUS2 0x01u
#define MAX30101_INT_ENABLE1 0x02u
#define MAX30101_INT_ENABLE2 0x03u
#define MAX30101_FIFO_WR_PTR 0x04u
#define MAX30101_OVF_COUNTER 0x05u
#define MAX30101_FIFO_RD_PTR 0x06u
#define MAX30101_FIFO_DATA 0x07u
#define MAX30101_FIFO_CONFIG 0x08u
#define MAX30101_MODE_CONFIG 0x09u
#define MAX30101_SPO2_CONFIG 0x0Au
#define MAX30101_LED1_PA 0x0Cu /* red */
#define MAX30101_LED2_PA 0x0Du /* IR */
#define MAX30101_LED3_PA 0x0Eu /* green */
#define MAX30101_LED4_PA 0x0Fu /* green, driven with LED3 in a SLOTx = 011 slot */
#define MAX30101_MULTI_LED1 0x11u
#define MAX30101_MULTI_LED2 0x12u
#define MAX30101_TEMP_INT 0x1Fu
#define MAX30101_TEMP_FRAC 0x20u
#define MAX30101_TEMP_CONFIG 0x21u
#define MAX30101_REV_ID 0xFEu
#define MAX30101_PART_ID 0xFFu

#define MAX30101_PART_ID_VALUE 0x15u

/* Interrupt Status 1 bits (p. 13). */
#define MAX30101_INT_A_FULL (1u << 7)
#define MAX30101_INT_PPG_RDY (1u << 6)
#define MAX30101_INT_ALC_OVF (1u << 5)
#define MAX30101_INT_PWR_RDY (1u << 0)

#define MAX30101_MODE_RESET (1u << 6)
#define MAX30101_MODE_MULTI_LED 0x07u
#define MAX30101_TEMP_EN (1u << 0)

#define MAX30101_FIFO_DEPTH 32u
#define MAX30101_SLOTS 3u /* green, red, IR in the V1 configuration */

typedef enum {
    MAX30101_OK = 0,
    MAX30101_ERR_BUS,      /* an I2C callback failed */
    MAX30101_ERR_PART_ID,  /* PART_ID is not 0x15 */
    MAX30101_ERR_RESET,    /* the RESET bit did not clear in time */
    MAX30101_ERR_READBACK, /* a configuration register reads back differently */
    MAX30101_ERR_BUSY,     /* a temperature conversion is still running */
} max30101_err_t;

typedef struct {
    void *ctx;
    /* Write `n` bytes starting at register `reg` (auto-increment); 0 = ok. */
    int (*write)(void *ctx, uint8_t reg, const uint8_t *data, size_t n);
    /* Read `n` bytes starting at `reg` (FIFO_DATA does not advance); 0 = ok. */
    int (*read)(void *ctx, uint8_t reg, uint8_t *data, size_t n);
    void (*delay_ms)(void *ctx, uint32_t ms);
} max30101_bus_t;

typedef struct {
    uint8_t fifo_config;
    uint8_t spo2_config;
    uint8_t led_pa[4];     /* LED1 red, LED2 IR, LED3 green, LED4 green */
    uint8_t multi_led[2];  /* 0x11 (SLOT2|SLOT1), 0x12 (SLOT4|SLOT3) */
    uint8_t int_enable[2]; /* 0x02, 0x03 */
} max30101_regs_t;

/* One look at the FIFO (Packet Schema V0.1 section 5.1): Interrupt Status 1 is
 * read first (it clears PPG_RDY), then FIFO_WR_PTR, OVF_COUNTER, FIFO_RD_PTR in
 * one burst; T_ANCHOR_US is taken right after that burst. */
typedef struct {
    bool status_ok;   /* Interrupt Status 1 was read (and so cleared) */
    bool pointers_ok; /* the pointer burst was read */
    uint8_t status1;  /* Interrupt Status 1 */
    uint8_t overflow; /* OVF_COUNTER: samples lost while full (saturates at 31) */
    uint16_t waiting; /* (WR - RD) mod 32, or 32 when WR = RD and OVF_COUNTER > 0 */
    bool full;        /* 32 samples waiting: newer samples are being lost */
} max30101_latch_t;

/* 18-bit ADC counts of `count` samples, left-justified in each 3-byte slot
 * value (p. 15-16), slots in SLOT1..3 order (green, red, IR). */
typedef struct {
    uint16_t count;
    uint32_t value[MAX30101_FIFO_DEPTH][MAX30101_SLOTS];
} max30101_samples_t;

/* Decided V1 configuration; `pulse_width_us` 411 or 215. */
void max30101_v1_regs(max30101_regs_t *regs, unsigned pulse_width_us);

/* Set the LED current codes in steps of 0.2 mA (0x00-0xFF, p. 21). `green` is
 * the code of each green sink: a SLOTx = 011 slot drives LED3 and LED4 together
 * (p. 22), so the total green current is twice the code's value. */
void max30101_set_currents(max30101_regs_t *regs, uint8_t green, uint8_t red, uint8_t ir);

int max30101_write_reg(const max30101_bus_t *bus, uint8_t reg, uint8_t value);
int max30101_read_reg(const max30101_bus_t *bus, uint8_t reg, uint8_t *value);

/* RESET, check PART_ID, write and read back `regs`, clear the FIFO pointers and
 * enter multi-LED mode last (conversions start). `rev_id` (optional) gets REV_ID. */
max30101_err_t max30101_start(const max30101_bus_t *bus, const max30101_regs_t *regs,
                              uint8_t *rev_id);

/* Read Interrupt Status 1 then the three FIFO pointers (one burst). With the
 * pointers alone an exactly full FIFO with no loss yet (WR = RD, OVF_COUNTER =
 * 0) looks empty; it shows as full one sample later, with OVF_COUNTER = 1. */
max30101_err_t max30101_latch(const max30101_bus_t *bus, max30101_latch_t *latch);

/* Read `count` samples (1 .. 32) from FIFO_DATA in one burst. */
max30101_err_t max30101_read_samples(const max30101_bus_t *bus, uint16_t count,
                                     max30101_samples_t *out);

/* Die temperature (p. 23): start one conversion; then read it in 1/16 degC
 * once TEMP_EN has cleared (MAX30101_ERR_BUSY while it runs). */
max30101_err_t max30101_temp_start(const max30101_bus_t *bus);
max30101_err_t max30101_temp_read(const max30101_bus_t *bus, int32_t *sixteenths);
