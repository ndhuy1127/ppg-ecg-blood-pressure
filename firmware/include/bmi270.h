/*
 * BMI270 IMU over SPI (datasheet BST-BMI270-DS000-08, rev 1.6, March 2026): the
 * start sequence with the microcode upload, the V1 configuration of Packet
 * Schema V0.2 section 3, the FIFO latch and the headerless frame read. Plain C
 * with no ESP-IDF dependency (the bus is a callback), so the same code runs on a
 * PC against a simulated chip. Not run on a chip yet.
 *
 * SPI (section 6.4): byte 0 is the register address with bit 7 = 1 to read; a
 * read returns one dummy byte before the data; addresses auto-increment except
 * at FIFO_DATA. The chip comes up in I2C mode and switches to SPI 200 us after a
 * rising edge of CSB (section 6.3), again after every soft reset.
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Register map (section 5.2). */
#define BMI270_CHIP_ID 0x00u
#define BMI270_ERR_REG 0x02u
#define BMI270_EVENT 0x1Bu
#define BMI270_INTERNAL_STATUS 0x21u
#define BMI270_FIFO_LENGTH_0 0x24u
#define BMI270_FIFO_DATA 0x26u
#define BMI270_ACC_CONF 0x40u
#define BMI270_ACC_RANGE 0x41u
#define BMI270_GYR_CONF 0x42u
#define BMI270_GYR_RANGE 0x43u
#define BMI270_FIFO_DOWNS 0x45u
#define BMI270_FIFO_WTM_0 0x46u
#define BMI270_FIFO_WTM_1 0x47u
#define BMI270_FIFO_CONFIG_0 0x48u
#define BMI270_FIFO_CONFIG_1 0x49u
#define BMI270_INT1_IO_CTRL 0x53u
#define BMI270_INT_LATCH 0x55u
#define BMI270_INT_MAP_DATA 0x58u
#define BMI270_INIT_CTRL 0x59u
#define BMI270_INIT_ADDR_0 0x5Bu
#define BMI270_INIT_DATA 0x5Eu
#define BMI270_PWR_CONF 0x7Cu
#define BMI270_PWR_CTRL 0x7Du
#define BMI270_CMD 0x7Eu

#define BMI270_CHIP_ID_VALUE 0x24u
#define BMI270_READ 0x80u
#define BMI270_ERR_FATAL (1u << 0)
#define BMI270_EVENT_POR (1u << 0)     /* power-up or soft reset; cleared on read */
#define BMI270_EVENT_ERROR 0x1Cu       /* error_code: ACC_CONF / GYR_CONF rejected */
#define BMI270_STATUS_MESSAGE 0x0Fu
#define BMI270_STATUS_INIT_OK 0x01u
#define BMI270_CMD_FIFO_FLUSH 0xB0u
#define BMI270_CMD_SOFTRESET 0xB6u

#define BMI270_CONFIG_SIZE 8192u
#define BMI270_INIT_CHUNK 256u      /* bytes per INIT_DATA burst (footnote 4) */
#define BMI270_FIFO_SIZE 2048u      /* bytes (section 4.7) */
#define BMI270_FRAME_SIZE 12u       /* headerless: gyr X, Y, Z then acc X, Y, Z */
#define BMI270_MAX_FRAME 21u        /* largest frame of any mode: 1 + 8 + 6 + 6 */
#define BMI270_MAX_FRAMES (BMI270_FIFO_SIZE / BMI270_FRAME_SIZE) /* 170 */
#define BMI270_AXES 6u              /* acc X, Y, Z, gyr X, Y, Z: 0xA1 .. 0xA6 */

typedef enum {
    BMI270_OK = 0,
    BMI270_ERR_BUS,      /* an SPI callback failed */
    BMI270_ERR_CHIP_ID,  /* CHIP_ID is not 0x24 */
    BMI270_ERR_INIT,     /* INTERNAL_STATUS never said init_ok */
    BMI270_ERR_READBACK, /* a configuration register reads back differently, or
                          * EVENT.error_code rejects ACC_CONF / GYR_CONF */
    BMI270_ERR_STATE,    /* a reset since the start, a fatal error, or no longer
                          * initialized */
} bmi270_err_t;

typedef struct {
    void *ctx;
    /* One SPI transaction, CSB low throughout: send tx[0..n), receive rx[0..n). */
    int (*xfer)(void *ctx, const uint8_t *tx, uint8_t *rx, size_t n);
    void (*delay_us)(void *ctx, uint32_t us); /* at least `us` */
} bmi270_bus_t;

typedef struct {
    uint8_t acc_conf, acc_range, gyr_conf, gyr_range;
    uint8_t fifo_downs, fifo_wtm[2], fifo_config[2];
    uint8_t int1_io_ctrl, int_latch, int_map_data;
    uint8_t pwr_conf, pwr_ctrl;
} bmi270_regs_t;

typedef struct {
    uint16_t length; /* FIFO_LENGTH, bytes */
    uint16_t frames; /* whole frames in it */
    bool full;       /* no room left for one more frame of any size (section 5) */
} bmi270_latch_t;

typedef struct {
    uint16_t count;
    int16_t value[BMI270_MAX_FRAMES][BMI270_AXES]; /* acc X, Y, Z, gyr X, Y, Z */
} bmi270_frames_t;

/* The V1 configuration (Packet Schema V0.2 section 3, register values decided
 * 2026-10-25): 100 Hz, +-4 g, +-500 dps, filters in performance mode, filtered
 * headerless FIFO of both sensors, stop on full, watermark 10 frames on INT1. */
void bmi270_v1_regs(bmi270_regs_t *regs);

/* The 14 register words of a 0xD2 packet (Packet Schema V0.2 section 12),
 * address << 24 | value, in the order of section 3. Returns 14. */
#define BMI270_CONFIG_WORDS 14u
unsigned bmi270_config_words(const bmi270_regs_t *regs, uint32_t out[BMI270_CONFIG_WORDS]);

bmi270_err_t bmi270_write(const bmi270_bus_t *bus, uint8_t reg, const uint8_t *data, size_t n);
bmi270_err_t bmi270_read(const bmi270_bus_t *bus, uint8_t reg, uint8_t *data, size_t n);

/* Soft reset, microcode upload (`config`, BMI270_CONFIG_SIZE bytes), INTERNAL_STATUS
 * check, configuration and read-back, sensors on, FIFO flushed once they run. */
bmi270_err_t bmi270_start(const bmi270_bus_t *bus, const bmi270_regs_t *regs,
                          const uint8_t *config);

/* CHIP_ID, no reset since the start (EVENT.por_detected, cleared by the start),
 * no fatal error, still initialized, and the configuration still holds: a
 * power-on reset would leave the chip uninitialized and silent. */
bmi270_err_t bmi270_check(const bmi270_bus_t *bus, const bmi270_regs_t *regs);

/* Read FIFO_LENGTH: the caller takes T_ANCHOR_US right after (section 3). The
 * headerless FIFO holds whole 12-byte frames and the counter moves by whole
 * frames (4.7.1, 5.2.36), so a length that is not a multiple of 12 or above
 * 2040 (a floating MISO reads 0x3FFF) is BMI270_ERR_STATE, never frames. */
bmi270_err_t bmi270_latch(const bmi270_bus_t *bus, bmi270_latch_t *latch);

/* CMD fifo_flush (5.2.86): after a read that failed part way, frames kept from
 * before a loss must not join frames written after it in the next read. */
bmi270_err_t bmi270_flush(const bmi270_bus_t *bus);

/* Read exactly `frames` frames (1 .. BMI270_MAX_FRAMES) in one burst. */
bmi270_err_t bmi270_read_frames(const bmi270_bus_t *bus, uint16_t frames,
                                bmi270_frames_t *out);
