/*
 * BMI270 driver core; see bmi270.h. Page and section numbers refer to
 * BST-BMI270-DS000-08 (rev 1.6).
 */
#include "bmi270.h"

#include <string.h>

/* One transaction: address, dummy byte (reads), then data. */
#define XFER_MAX (2u + BMI270_MAX_FRAMES * BMI270_FRAME_SIZE)
/* Idle time after an access (section 6.4, Table 19): 2 us after a read, 450 us
 * after a write in suspend or low-power mode. Every write waits 450 us: the
 * driver writes only while starting, where the mode is not always normal. */
#define IDLE_READ_US 2u
#define IDLE_WRITE_US 450u
#define SPI_SWITCH_US 1000u  /* SPI 200 us after a CSB rising edge (section 6.3) */
#define RESET_WAIT_US 2000u  /* registers after 450 us, as after power-on (4.4, 4.17) */
#define INIT_WAIT_US 20000u  /* INTERNAL_STATUS says init_ok within 20 ms (4.4) */
#define INIT_POLLS 10        /* then every 1 ms */
#define START_UP_US 80000u   /* gyroscope 45 ms suspend to normal (p. 19), margin */

static uint8_t s_tx[XFER_MAX];
static uint8_t s_rx[XFER_MAX];

void bmi270_v1_regs(bmi270_regs_t *r)
{
    /* ACC_CONF (5.2.41): acc_filter_perf 1 (performance), acc_bwp 010 (normal),
     * acc_odr 1000 (100 Hz) -> 0xA8. ACC_RANGE (5.2.42): 01 = +-4 g. */
    r->acc_conf = 0xA8u;
    r->acc_range = 0x01u;
    /* GYR_CONF (5.2.43): gyr_filter_perf 1, gyr_noise_perf 1 (performance),
     * gyr_bwp 10 (normal), gyr_odr 1000 (100 Hz) -> 0xE8. GYR_RANGE (5.2.44):
     * 010 = +-500 dps (65.6 LSB/dps), ois_range 0 -> 0x02. */
    r->gyr_conf = 0xE8u;
    r->gyr_range = 0x02u;
    /* FIFO_DOWNS (5.2.46): filtered acc (b7) and gyr (b3), no downsampling. */
    r->fifo_downs = 0x88u;
    /* FIFO_WTM (5.2.47-48): 10 frames x 12 bytes = 120 = 0x0078. */
    r->fifo_wtm[0] = 0x78u;
    r->fifo_wtm[1] = 0x00u;
    /* FIFO_CONFIG_0 (5.2.49): fifo_stop_on_full 1, fifo_time_en 0 (no sensortime
     * frame in a headerless FIFO). FIFO_CONFIG_1 (5.2.50): fifo_gyr_en b7,
     * fifo_acc_en b6, no aux, no header, no tags -> 0xC0. */
    r->fifo_config[0] = 0x01u;
    r->fifo_config[1] = 0xC0u;
    /* INT1_IO_CTRL (5.2.58): output_en b3, push-pull (od 0), active high (lvl b1)
     * -> 0x0A; INT_LATCH (5.2.60): non-latched, INT1 follows the watermark
     * condition; INT_MAP_DATA (5.2.63): fwm_int1 b1 only. */
    r->int1_io_ctrl = 0x0Au;
    r->int_latch = 0x00u;
    r->int_map_data = 0x02u;
    /* PWR_CONF (5.2.84): adv_power_save 0, fifo_self_wake_up 1 (its reset value;
     * used only in low-power mode), fup_en 0 -> 0x02. PWR_CTRL (5.2.85): gyr_en
     * b1, acc_en b2; aux and the BMI270 temperature sensor off -> 0x06. */
    r->pwr_conf = 0x02u;
    r->pwr_ctrl = 0x06u;
}

unsigned bmi270_config_words(const bmi270_regs_t *r, uint32_t out[BMI270_CONFIG_WORDS])
{
    const uint8_t pairs[BMI270_CONFIG_WORDS][2] = {
        {BMI270_ACC_CONF, r->acc_conf},          {BMI270_ACC_RANGE, r->acc_range},
        {BMI270_GYR_CONF, r->gyr_conf},          {BMI270_GYR_RANGE, r->gyr_range},
        {BMI270_FIFO_DOWNS, r->fifo_downs},      {BMI270_FIFO_WTM_0, r->fifo_wtm[0]},
        {BMI270_FIFO_WTM_1, r->fifo_wtm[1]},     {BMI270_FIFO_CONFIG_0, r->fifo_config[0]},
        {BMI270_FIFO_CONFIG_1, r->fifo_config[1]}, {BMI270_INT1_IO_CTRL, r->int1_io_ctrl},
        {BMI270_INT_LATCH, r->int_latch},        {BMI270_INT_MAP_DATA, r->int_map_data},
        {BMI270_PWR_CONF, r->pwr_conf},          {BMI270_PWR_CTRL, r->pwr_ctrl},
    };
    for (unsigned i = 0; i < BMI270_CONFIG_WORDS; i++) {
        out[i] = (uint32_t)pairs[i][0] << 24 | pairs[i][1];
    }
    return BMI270_CONFIG_WORDS;
}

bmi270_err_t bmi270_write(const bmi270_bus_t *bus, uint8_t reg, const uint8_t *data, size_t n)
{
    if (n == 0 || n + 1u > XFER_MAX) {
        return BMI270_ERR_BUS;
    }
    s_tx[0] = reg & (uint8_t)~BMI270_READ;
    memcpy(&s_tx[1], data, n);
    int failed = bus->xfer(bus->ctx, s_tx, s_rx, n + 1u);
    bus->delay_us(bus->ctx, IDLE_WRITE_US);
    return failed ? BMI270_ERR_BUS : BMI270_OK;
}

bmi270_err_t bmi270_read(const bmi270_bus_t *bus, uint8_t reg, uint8_t *data, size_t n)
{
    if (n == 0 || n + 2u > XFER_MAX) {
        return BMI270_ERR_BUS;
    }
    memset(s_tx, 0, n + 2u);
    s_tx[0] = reg | BMI270_READ;
    int failed = bus->xfer(bus->ctx, s_tx, s_rx, n + 2u);
    bus->delay_us(bus->ctx, IDLE_READ_US);
    if (failed) {
        return BMI270_ERR_BUS;
    }
    memcpy(data, &s_rx[2], n); /* s_rx[1] is the dummy byte (section 6.4) */
    return BMI270_OK;
}

static bmi270_err_t write1(const bmi270_bus_t *bus, uint8_t reg, uint8_t value)
{
    return bmi270_write(bus, reg, &value, 1);
}

/* Read the configuration back; PWR_CTRL only once the sensors were switched on. */
static bmi270_err_t read_back(const bmi270_bus_t *bus, const bmi270_regs_t *r, bool sensors_on)
{
    uint8_t a[10], b[6], c[2];
    if (bmi270_read(bus, BMI270_ACC_CONF, a, sizeof(a))
        || bmi270_read(bus, BMI270_INT1_IO_CTRL, b, sizeof(b))
        || bmi270_read(bus, BMI270_PWR_CONF, c, sizeof(c))) {
        return BMI270_ERR_BUS;
    }
    /* Masks keep the defined bits only (0x44 AUX_CONF, 0x54, 0x56, 0x57 unused). */
    const struct {
        uint8_t got, want, mask;
    } checks[] = {
        {a[0], r->acc_conf, 0xFFu},       {a[1], r->acc_range, 0x03u},
        {a[2], r->gyr_conf, 0xFFu},       {a[3], r->gyr_range, 0x0Fu},
        {a[5], r->fifo_downs, 0xFFu},     {a[6], r->fifo_wtm[0], 0xFFu},
        {a[7], r->fifo_wtm[1], 0x1Fu},    {a[8], r->fifo_config[0], 0x03u},
        {a[9], r->fifo_config[1], 0xFFu}, {b[0], r->int1_io_ctrl, 0x1Eu},
        {b[2], r->int_latch, 0x01u},      {b[5], r->int_map_data, 0xFFu},
        {c[0], r->pwr_conf, 0x07u},       {c[1], sensors_on ? r->pwr_ctrl : 0u, 0x0Fu},
    };
    for (size_t i = 0; i < sizeof(checks) / sizeof(checks[0]); i++) {
        if ((checks[i].got ^ checks[i].want) & checks[i].mask) {
            return BMI270_ERR_READBACK;
        }
    }
    return BMI270_OK;
}

bmi270_err_t bmi270_start(const bmi270_bus_t *bus, const bmi270_regs_t *r,
                          const uint8_t *config)
{
    uint8_t v;
    /* Section 6.3: a read gives CSB its rising edge (its answer is not valid);
     * the soft reset puts the interface back to I2C, so once more after it. */
    if (bmi270_read(bus, BMI270_CHIP_ID, &v, 1)) {
        return BMI270_ERR_BUS;
    }
    bus->delay_us(bus->ctx, SPI_SWITCH_US);
    if (write1(bus, BMI270_CMD, BMI270_CMD_SOFTRESET)) {
        return BMI270_ERR_BUS;
    }
    bus->delay_us(bus->ctx, RESET_WAIT_US);
    if (bmi270_read(bus, BMI270_CHIP_ID, &v, 1)) {
        return BMI270_ERR_BUS;
    }
    bus->delay_us(bus->ctx, SPI_SWITCH_US);
    if (bmi270_read(bus, BMI270_CHIP_ID, &v, 1)) {
        return BMI270_ERR_BUS;
    }
    if (v != BMI270_CHIP_ID_VALUE) {
        return BMI270_ERR_CHIP_ID;
    }
    /* Section 4.4: advanced power save off, prepare, upload, complete. The
     * upload goes in BMI270_INIT_CHUNK bursts; INIT_ADDR is the byte offset / 2
     * (bits 3:0 in INIT_ADDR_0, bits 11:4 in INIT_ADDR_1, footnote 4). */
    if (write1(bus, BMI270_PWR_CONF, 0x00u) || write1(bus, BMI270_INIT_CTRL, 0x00u)) {
        return BMI270_ERR_BUS;
    }
    for (uint32_t off = 0; off < BMI270_CONFIG_SIZE; off += BMI270_INIT_CHUNK) {
        const uint8_t addr[2] = {(uint8_t)((off / 2u) & 0x0Fu), (uint8_t)((off / 2u) >> 4)};
        if (bmi270_write(bus, BMI270_INIT_ADDR_0, addr, sizeof(addr))
            || bmi270_write(bus, BMI270_INIT_DATA, &config[off], BMI270_INIT_CHUNK)) {
            return BMI270_ERR_BUS;
        }
    }
    if (write1(bus, BMI270_INIT_CTRL, 0x01u)) { /* only once after a reset */
        return BMI270_ERR_BUS;
    }
    bus->delay_us(bus->ctx, INIT_WAIT_US);
    for (int i = 0;; i++) {
        if (bmi270_read(bus, BMI270_INTERNAL_STATUS, &v, 1)) {
            return BMI270_ERR_BUS;
        }
        if ((v & BMI270_STATUS_MESSAGE) == BMI270_STATUS_INIT_OK) {
            break;
        }
        if (i == INIT_POLLS) {
            return BMI270_ERR_INIT;
        }
        bus->delay_us(bus->ctx, 1000u);
    }
    /* Configuration mode: write everything but PWR_CTRL, then read it back.
     * EVENT (5.2.27) also reports an ACC_CONF / GYR_CONF the chip rejects, and
     * reading it clears por_detected, which bmi270_check watches from now on. */
    const struct {
        uint8_t reg, value;
    } writes[] = {
        {BMI270_ACC_CONF, r->acc_conf},          {BMI270_ACC_RANGE, r->acc_range},
        {BMI270_GYR_CONF, r->gyr_conf},          {BMI270_GYR_RANGE, r->gyr_range},
        {BMI270_FIFO_DOWNS, r->fifo_downs},      {BMI270_FIFO_WTM_0, r->fifo_wtm[0]},
        {BMI270_FIFO_WTM_1, r->fifo_wtm[1]},     {BMI270_FIFO_CONFIG_0, r->fifo_config[0]},
        {BMI270_FIFO_CONFIG_1, r->fifo_config[1]}, {BMI270_INT1_IO_CTRL, r->int1_io_ctrl},
        {BMI270_INT_LATCH, r->int_latch},        {BMI270_INT_MAP_DATA, r->int_map_data},
        {BMI270_PWR_CONF, r->pwr_conf},
    };
    for (size_t i = 0; i < sizeof(writes) / sizeof(writes[0]); i++) {
        if (write1(bus, writes[i].reg, writes[i].value)) {
            return BMI270_ERR_BUS;
        }
    }
    bmi270_err_t err = read_back(bus, r, false);
    if (err != BMI270_OK) {
        return err;
    }
    if (bmi270_read(bus, BMI270_EVENT, &v, 1)) {
        return BMI270_ERR_BUS;
    }
    if (v & BMI270_EVENT_ERROR) {
        return BMI270_ERR_READBACK;
    }
    /* Sensors on; once the gyroscope runs, start the FIFO empty (frames written
     * while it starts up may be incomplete, section 4.7.3). */
    if (write1(bus, BMI270_PWR_CTRL, r->pwr_ctrl)) {
        return BMI270_ERR_BUS;
    }
    bus->delay_us(bus->ctx, START_UP_US);
    if (write1(bus, BMI270_CMD, BMI270_CMD_FIFO_FLUSH)) {
        return BMI270_ERR_BUS;
    }
    return read_back(bus, r, true);
}

bmi270_err_t bmi270_check(const bmi270_bus_t *bus, const bmi270_regs_t *r)
{
    uint8_t id, err, event, status;
    if (bmi270_read(bus, BMI270_CHIP_ID, &id, 1) || bmi270_read(bus, BMI270_ERR_REG, &err, 1)
        || bmi270_read(bus, BMI270_EVENT, &event, 1)
        || bmi270_read(bus, BMI270_INTERNAL_STATUS, &status, 1)) {
        return BMI270_ERR_BUS;
    }
    if (id != BMI270_CHIP_ID_VALUE) {
        return BMI270_ERR_CHIP_ID;
    }
    if ((err & BMI270_ERR_FATAL) || (event & (BMI270_EVENT_POR | BMI270_EVENT_ERROR))
        || (status & BMI270_STATUS_MESSAGE) != BMI270_STATUS_INIT_OK) {
        return BMI270_ERR_STATE;
    }
    return read_back(bus, r, true);
}

bmi270_err_t bmi270_latch(const bmi270_bus_t *bus, bmi270_latch_t *latch)
{
    uint8_t len[2];
    *latch = (bmi270_latch_t){0};
    if (bmi270_read(bus, BMI270_FIFO_LENGTH_0, len, sizeof(len))) {
        return BMI270_ERR_BUS;
    }
    /* FIFO_LENGTH_1 bits 5:0 are bits 13:8 (5.2.37). */
    uint16_t length = (uint16_t)(len[0] | ((len[1] & 0x3Fu) << 8));
    if (length > BMI270_MAX_FRAMES * BMI270_FRAME_SIZE || length % BMI270_FRAME_SIZE) {
        return BMI270_ERR_STATE; /* not a fill level of whole frames */
    }
    latch->length = length;
    latch->frames = length / BMI270_FRAME_SIZE;
    /* With fifo_stop_on_full the chip may drop the newest frame once the free
     * space is below the largest frame (4.7.2); conservative: below 21 bytes. */
    latch->full = latch->length + BMI270_MAX_FRAME > BMI270_FIFO_SIZE;
    return BMI270_OK;
}

bmi270_err_t bmi270_flush(const bmi270_bus_t *bus)
{
    return write1(bus, BMI270_CMD, BMI270_CMD_FIFO_FLUSH);
}

bmi270_err_t bmi270_read_frames(const bmi270_bus_t *bus, uint16_t frames, bmi270_frames_t *out)
{
    out->count = 0;
    if (frames == 0 || frames > BMI270_MAX_FRAMES) {
        return BMI270_ERR_BUS;
    }
    /* A frame read whole leaves the FIFO; reading exactly the latched frames
     * leaves the later ones for the next read (4.7.2). Little endian words. */
    static uint8_t data[BMI270_MAX_FRAMES * BMI270_FRAME_SIZE];
    if (bmi270_read(bus, BMI270_FIFO_DATA, data, (size_t)frames * BMI270_FRAME_SIZE)) {
        return BMI270_ERR_BUS;
    }
    for (uint16_t f = 0; f < frames; f++) {
        const uint8_t *b = &data[f * BMI270_FRAME_SIZE];
        for (unsigned k = 0; k < 3u; k++) {
            /* Bytes 0-5 gyr X, Y, Z; bytes 6-11 acc X, Y, Z (section 4.7.1). */
            out->value[f][3u + k] = (int16_t)(uint16_t)(b[2u * k] | (b[2u * k + 1u] << 8));
            out->value[f][k] = (int16_t)(uint16_t)(b[6u + 2u * k] | (b[7u + 2u * k] << 8));
        }
    }
    out->count = frames;
    return BMI270_OK;
}
