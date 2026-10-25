/*
 * Firmware skeleton for the V1-module: fake ECG/PPG/IMU sources, t0 event
 * packets and device info packets in Packet Schema V0.2
 * (configs/hardware/Packet_Schema_V0.2.md), sent as binary on the native USB
 * Serial/JTAG port. Text logs go to UART0 only, so the packet port carries
 * packets alone (schema section 13). ECG comes from a MAX30001 when built with
 * BOARD_ECG_REAL=1 (not run on a chip yet), otherwise from fake_afe like PPG and
 * IMU, and the ECG SAMP edges from the fake ECG source unless the capture is in.
 */
#include <inttypes.h>
#include <stdlib.h>

#include "bmi270.h"
#include "bmi270_config.h"
#include "bmi270_esp.h"
#include "board_v1_module.h"
#include "bootloader_random.h"
#include "die_temp.h"
#include "driver/gpio.h"
#include "driver/usb_serial_jtag.h"
#include "esp_app_desc.h"
#include "esp_log.h"
#include "esp_random.h"
#include "esp_timer.h"
#include "fake_afe.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "ecg_read.h"
#include "imu_plan.h"
#include "max30001.h"
#include "max30001_esp.h"
#include "max30101.h"
#include "max30101_esp.h"
#include "packet_wire.h"
#include "ppg_read.h"
#include "samp_capture.h"
#include "samp_edges.h"
#include "samp_map.h"

static const char *TAG = "fw";

#define TX_QUEUE_LEN 64
#define TX_TIMEOUT_MS 20
#define USB_TX_BUFFER_BYTES 8192
#define USB_RX_BUFFER_BYTES 256
#define EVENT_QUEUE_LEN 8
#define T0_LOCKOUT_US 200000
#define T0_CONFIRM_MS 20
#define LED_PERIOD_MS 500
#define STATS_PERIOD_MS 10000
#define DEVICE_INFO_PERIOD_MS 10000

/*
 * Fake sources, not hardware settings. ECG like MAX30001 at 512 sps with
 * EFIT = 15 (16 samples per read); PPG like MAX30101 multi-LED mode, three
 * slots at 200 sps (the V1 rate), 8 samples per read: 25 packets/s per slot.
 * FIFO_A_FULL cannot fire before 17 unread samples, so a real driver reading 8
 * needs PPG_RDY or a timer. The ECG period of 1953 us is 512.03 Hz, +64 ppm
 * from nominal: the bench rate regression should see it. IMU like BMI270 in
 * the V1 setup (V0.2 section 3): accelerometer and gyroscope at 100 Hz,
 * watermark 10 frames, a 2 KB FIFO of 12-byte frames (170) that stops when full.
 */
static void fake_samp_edge(uint64_t index, int64_t t_us);
static const fake_afe_config_t ECG_FAKE = {
    .name = "fake_ecg",
    .n_slots = 1,
    .channel_ids = {PKT_CH_ECG},
    .fs_nominal_mhz = 512000,
    .period_us = 1953,
    .batch = 16,
    .depth = 32,
    /* The fake ECG source sends a SAMP edge per sample, unless the real
     * capture on INT2B is built in (board_v1_module.h). */
    .on_sample = BOARD_SAMP_CAPTURE ? NULL : fake_samp_edge,
};
static const fake_afe_config_t PPG_FAKE = {
    .name = "fake_ppg",
    .n_slots = 3,
    .channel_ids = {PKT_CH_PPG_SLOT1, PKT_CH_PPG_SLOT2, PKT_CH_PPG_SLOT3},
    .fs_nominal_mhz = 200000,
    .period_us = 5000,
    .batch = 8,
    .notify_each = true, /* PPG_RDY */
    .depth = 32,
};
static const fake_afe_config_t IMU_FAKE = {
    .name = "fake_imu",
    .n_slots = 6,
    .channel_ids = {PKT_CH_ACC_X, PKT_CH_ACC_Y, PKT_CH_ACC_Z,
                    PKT_CH_GYR_X, PKT_CH_GYR_Y, PKT_CH_GYR_Z},
    .fs_nominal_mhz = 100000,
    .period_us = 10000,
    .batch = 10,
    .depth = 170,
};

/*
 * FAKE_IMU_STALLS=1 (PlatformIO env esp32s3_devkitc_imu_stall): the IMU reader
 * stops reading on purpose, every 30 s, for 500 ms at +10 s (about 60 frames:
 * two packets per axis, the first with bit 7) and for 2500 ms at +20 s (the
 * FIFO fills at 170 frames and about 90 are lost: bit 0, then the next read
 * re-anchors with bit 5). V0.2 section 9, step 2b.
 */
#ifndef FAKE_IMU_STALLS
#define FAKE_IMU_STALLS 0
#endif
#define IMU_STALL_PERIOD_US 30000000LL

/*
 * SAMP anchor of the ECG (V0.2 section 7). Tolerance of one edge interval:
 * provisional 20 us plus the ECG rate allowance (1000 ppm of 1953 us, about 2
 * us), to be set after bring-up. Wait at most two sample periods for the edge
 * of a packet's last sample. After an error the mapping restarts 1 s later, at
 * most once per 10 s (decided 2026-10-24).
 */
#define SAMP_TOLERANCE_NS 22000ULL
#define SAMP_WAIT_PERIODS 2
#define SAMP_REMAP_HOLDOFF_US 1000000LL
#define SAMP_REMAP_MIN_GAP_US 10000000LL

/*
 * FAKE_SAMP_FAULTS=1 (PlatformIO env esp32s3_devkitc_samp_faults): every 20 s
 * the fake ECG drops one SAMP edge (at +5 s, like a missed or overwritten
 * capture) and adds a spurious one half a period early (at +15 s), so the
 * mapping goes to the error state and restarts. V0.2 section 9, step 2c.
 */
#ifndef FAKE_SAMP_FAULTS
#define FAKE_SAMP_FAULTS 0
#endif
#define SAMP_FAULT_PERIOD_US 20000000LL

/*
 * FAKE_PPG_DELAY=1 (PlatformIO env esp32s3_devkitc_ppg_delay): every 10 s the
 * PPG reader waits 12 ms before it latches, so the drain finds about 10
 * samples instead of 8 (V0.2 section 7.6, section 9 step 2d).
 */
#ifndef FAKE_PPG_DELAY
#define FAKE_PPG_DELAY 0
#endif
#define PPG_DELAY_PERIOD_US 10000000LL
#define PPG_DELAY_MS 12

enum {
    CH_ECG, CH_PPG1, CH_PPG2, CH_PPG3, CH_PPG4, CH_EVENT, CH_DEVICE_INFO,
    CH_ACC_X, CH_ACC_Y, CH_ACC_Z, CH_GYR_X, CH_GYR_Y, CH_GYR_Z, CH_DIE_TEMP, CH_COUNT
};
static const uint8_t CHANNEL_IDS[CH_COUNT] = {
    PKT_CH_ECG, PKT_CH_PPG_SLOT1, PKT_CH_PPG_SLOT2, PKT_CH_PPG_SLOT3,
    PKT_CH_PPG_SLOT4, PKT_CH_EVENT, PKT_CH_DEVICE_INFO, PKT_CH_ACC_X,
    PKT_CH_ACC_Y, PKT_CH_ACC_Z, PKT_CH_GYR_X, PKT_CH_GYR_Y, PKT_CH_GYR_Z,
    PKT_CH_DIE_TEMP,
};

typedef struct {
    uint32_t sent;
    uint32_t tx_timeout; /* SEQ assigned, packet not accepted by the USB driver */
    uint32_t queue_drop; /* MCU queue full: dropped before SEQ was assigned */
} channel_stats_t;

/* STATUS bits of a packet dropped before USB that move on to the next packet of
 * the channel: 0 and 1 explain a FIRST_SAMPLE_INDEX jump (logger rules R2, R3),
 * 5 marks the re-anchor that the next packet continues (V0.2 section 5). */
#define CARRY_BITS (PKT_STATUS_AFE_FIFO_OVERFLOW | PKT_STATUS_MCU_BUFFER_OVERFLOW                     | PKT_STATUS_INDEX_REANCHORED)

/* One t0 edge from the ISR, with the edges its queue dropped just before it. */
typedef struct {
    int64_t t_us;
    uint32_t lost_before;
} t0_edge_t;

static QueueHandle_t s_tx_queue;
static QueueHandle_t s_event_queue;
static uint32_t s_session_id;
static channel_stats_t s_stats[CH_COUNT];
static uint16_t s_drop_bits[CH_COUNT];
static volatile uint32_t s_events_lost;
static samp_map_t s_samp; /* written by the ECG reader only; read for the log */

static int channel_index(uint8_t channel_id)
{
    for (int k = 0; k < CH_COUNT; k++) {
        if (CHANNEL_IDS[k] == channel_id) {
            return k;
        }
    }
    return -1;
}

/*
 * Called only by the channel's own producer task. A packet dropped here never
 * gets a SEQ, so the next packet of that channel carries STATUS bit 1 and a
 * FIRST_SAMPLE_INDEX jump while SEQ stays continuous (logger rule R3). If the
 * dropped packet carried bit 0 (AFE FIFO overflow), bit 0 moves on as well:
 * the jump then also holds the samples lost in the AFE. So does bit 5: the
 * next packet still starts the new chain (V0.2 section 5).
 */
static void enqueue(pkt_t *p)
{
    int k = channel_index(p->channel_id);
    p->status |= s_drop_bits[k];
    if (xQueueSend(s_tx_queue, p, 0) == pdTRUE) {
        s_drop_bits[k] = 0;
    } else {
        s_drop_bits[k] = (p->status & CARRY_BITS) | PKT_STATUS_MCU_BUFFER_OVERFLOW;
        s_stats[k].queue_drop++;
    }
}

/*
 * The only writer of the packet port. SEQ is assigned here, at send time, and
 * starts at 0 in every session, so a missing SEQ means a packet lost after the
 * MCU queue. usb_serial_jtag_write_bytes takes a whole packet or nothing.
 */
static void tx_task(void *arg)
{
    static uint8_t buf[PKT_MAX_SIZE];
    uint32_t seq[CH_COUNT] = {0};
    /* Bits 0, 1 and 5 of a packet the USB driver did not take (a send failure
     * the firmware sees; a loss after the driver took it is not seen) move to the
     * next packet of the channel; otherwise the index jump or re-anchor it
     * explained would be left unexplained. */
    uint16_t carry[CH_COUNT] = {0};
    pkt_t p;
    for (;;) {
        xQueueReceive(s_tx_queue, &p, portMAX_DELAY);
        int k = channel_index(p.channel_id);
        p.seq = seq[k]++;
        p.status |= carry[k];
        size_t n = pkt_encode(&p, buf, sizeof(buf));
        if (n > 0 && usb_serial_jtag_write_bytes(buf, n, pdMS_TO_TICKS(TX_TIMEOUT_MS)) == (int)n) {
            s_stats[k].sent++;
            carry[k] = 0;
        } else {
            if (n == 0) {
                ESP_LOGE(TAG, "cannot encode packet on channel 0x%02X", p.channel_id);
            }
            s_stats[k].tx_timeout++;
            carry[k] = p.status & CARRY_BITS;
        }
    }
}

/*
 * Die temperature 0xB1 (V0.2 section 11), read in the PPG reader task: one value
 * per packet, T_FIRST_US = T_ANCHOR_US = right after the readout, no bit 4. A
 * reading starts within 50 ms of its tick and is read out by 100 ms after it
 * (die_temp.h), so the reader must look at least every 40 ms or so.
 */
#if BOARD_PPG_READ_PERIOD_MS > 40
#error "BOARD_PPG_READ_PERIOD_MS above 40 ms breaks the die temperature timing (V0.2 11.1)"
#endif
static void send_die_temp(die_temp_packet_t tp, uint64_t anchor_us, int32_t sixteenths)
{
    if (!tp.send) {
        return;
    }
    pkt_t p = {
        .channel_id = PKT_CH_DIE_TEMP,
        .session_id = s_session_id,
        .first_sample_index = tp.index,
        .t_anchor_us = anchor_us,
        .t_first_us = anchor_us,
        .fs_nominal_mhz = DIE_TEMP_FS_MHZ,
        .sample_count = 1,
        .status = tp.status,
    };
    p.data[0] = sixteenths;
    enqueue(&p);
}

#if BOARD_PPG_REAL
/*
 * PPG from a MAX30101 (drivers/max30101.c; not run on a chip yet), V0.2
 * section 7.6. Every INT edge (PPG_RDY, one per sample), and every PPG_POLL_MS
 * without one (INT stuck, or an exactly full FIFO that may raise no new
 * PPG_RDY), or every BOARD_PPG_READ_PERIOD_MS in timer mode, the reader reads
 * Interrupt Status 1 (clearing PPG_RDY) and the FIFO pointers, takes
 * T_ANCHOR_US right after that burst, and once 8 samples wait (any, on a
 * timer) reads every sample present at the latch. ppg_read_plan decides the
 * index, STATUS (bit 0 full, bit 6 ALC_OVF, bits 3+5 after a failure) and a
 * reconfiguration (brownout, failed Status 1 or sample read), retried every
 * PPG_RECONFIGURE_MS until it succeeds, with no packet meanwhile.
 * The three slots of a read share FIRST_SAMPLE_INDEX, T_ANCHOR_US and STATUS;
 * DATA is the 18-bit ADC count. LED currents are the bring-up defaults until
 * the per-subject calibration command exists (protocol v0.2 section 6.1).
 */
#define PPG_FS_NOMINAL_MHZ 200000u
#define PPG_BATCH 8
#define PPG_POLL_MS 10
#define PPG_RECONFIGURE_MS 100

static max30101_bus_t s_ppg_bus;
static max30101_regs_t s_ppg_regs;

/* Die temperature from the chip only: never a made-up value after a failure. */
static void ppg_temp_service(die_temp_t *t)
{
    int64_t now = esp_timer_get_time();
    switch (die_temp_next(t, now)) {
    case DIE_TEMP_START:
        die_temp_started(t, max30101_temp_start(&s_ppg_bus) == MAX30101_OK);
        break;
    case DIE_TEMP_POLL: {
        int32_t value = 0;
        /* Also checks that no brownout reset the chip since the start (the
         * next latch would see PWR_RDY only after this readout). */
        max30101_err_t err = max30101_temp_read(&s_ppg_bus, MAX30101_MODE_MULTI_LED,
                                                &value);
        int64_t anchor = esp_timer_get_time(); /* right after the readout */
        die_temp_read_t result = err == MAX30101_OK         ? DIE_TEMP_READ_OK
                                 : err == MAX30101_ERR_BUSY ? DIE_TEMP_READ_BUSY
                                                            : DIE_TEMP_READ_ERROR;
        send_die_temp(die_temp_polled(t, result, anchor), (uint64_t)anchor, value);
        break;
    }
    default:
        break;
    }
}

static void ppg_give_up(const char *what, int err)
{
    ESP_LOGE(TAG, "MAX30101 %s failed (%d): no PPG packets", what, err);
    max30101_write_reg(&s_ppg_bus, MAX30101_INT_ENABLE1, 0); /* best effort */
    max30101_esp_stop();
    for (;;) {
        vTaskSuspend(NULL); /* keep the handle valid for an ISR in flight */
    }
}

static void ppg_reader_task(void *arg)
{
    (void)arg;
    static const uint8_t SLOT_CHANNELS[MAX30101_SLOTS] = {
        PKT_CH_PPG_SLOT1, PKT_CH_PPG_SLOT2, PKT_CH_PPG_SLOT3};
    ESP_ERROR_CHECK(max30101_esp_init(&s_ppg_bus, BOARD_PPG_I2C_HZ,
                                      xTaskGetCurrentTaskHandle()));
    max30101_v1_regs(&s_ppg_regs, BOARD_PPG_LED_PW_US);
    uint8_t rev = 0;
    max30101_err_t err = max30101_start(&s_ppg_bus, &s_ppg_regs, &rev);
    ESP_LOGI(TAG, "MAX30101 REV_ID 0x%02X, LED_PW %u us, start %d", rev,
             (unsigned)BOARD_PPG_LED_PW_US, (int)err);
    if (err != MAX30101_OK) {
        ppg_give_up("start", (int)err);
    }
    const uint16_t batch = BOARD_PPG_READ_PERIOD_MS > 0 ? 1 : PPG_BATCH;
    ppg_read_t ppg;
    ppg_read_init(&ppg);
    die_temp_t temp;
    die_temp_init(&temp, esp_timer_get_time()); /* t0: kept across chip resets */
    TickType_t wake = xTaskGetTickCount();
    int64_t next_reconfigure_us = 0;
    for (;;) {
        if (BOARD_PPG_READ_PERIOD_MS > 0) {
            vTaskDelayUntil(&wake, pdMS_TO_TICKS(BOARD_PPG_READ_PERIOD_MS));
            ulTaskNotifyTake(pdTRUE, 0); /* the interrupts are not used */
        } else {
            /* A timeout also looks at the FIFO, whatever INT does. */
            ulTaskNotifyTake(pdTRUE, pdMS_TO_TICKS(PPG_POLL_MS));
        }
        max30101_latch_t latch = {0};
        if (!ppg.needs_reconfigure) {
            max30101_latch(&s_ppg_bus, &latch);
        }
        uint64_t anchor = esp_timer_get_time(); /* right after the pointer burst */
        uint16_t count = latch.pointers_ok ? ppg_read_count(&latch, batch) : 0;
        static max30101_samples_t samples;
        bool samples_ok = count == 0
                          || max30101_read_samples(&s_ppg_bus, count, &samples) == MAX30101_OK;
        ppg_read_plan_t plan = ppg_read_plan(&ppg, &latch, count, samples_ok, anchor,
                                             PPG_FS_NOMINAL_MHZ, PKT_STATUS_LATENCY_UNMEASURED);
        if (plan.reconfigure) {
            die_temp_abort(&temp); /* before any RESET: TEMP_EN then reads 0 */
        }
        if (plan.reconfigure && esp_timer_get_time() >= next_reconfigure_us) {
            next_reconfigure_us = esp_timer_get_time() + PPG_RECONFIGURE_MS * 1000LL;
            err = max30101_start(&s_ppg_bus, &s_ppg_regs, &rev);
            if (err == MAX30101_OK) {
                ppg_read_reconfigured(&ppg);
                ESP_LOGW(TAG, "MAX30101 configured again after a brownout or read failure");
            } else {
                ESP_LOGE(TAG, "MAX30101 reconfiguration failed (%d), retrying", (int)err);
            }
        }
        if (!ppg.needs_reconfigure) {
            ppg_temp_service(&temp); /* on every loop, not only with a PPG packet */
        }
        if (!plan.send) {
            continue;
        }
        for (unsigned slot = 0; slot < MAX30101_SLOTS; slot++) {
            pkt_t p = {
                .channel_id = SLOT_CHANNELS[slot],
                .session_id = s_session_id,
                .first_sample_index = plan.chunk.first_index,
                .t_anchor_us = anchor,
                .t_first_us = plan.chunk.t_first_us,
                .fs_nominal_mhz = PPG_FS_NOMINAL_MHZ,
                .sample_count = plan.chunk.count,
                .status = plan.chunk.status,
            };
            for (uint16_t i = 0; i < plan.chunk.count; i++) {
                p.data[i] = (int32_t)samples.value[i][slot];
            }
            enqueue(&p);
        }
    }
}
#else
/*
 * PPG reads (V0.2 section 7.6). PPG_RDY holds INT low until Interrupt Status 1
 * (0x00) is read, and a sample that comes while the flag is set makes no new
 * edge, so the driver clears it after every interrupt (the MAX30101 driver's
 * job; the fake source just notifies once per stored sample). Each interrupt
 * only wakes the reader: the FIFO pointers, not a count of interrupts, say
 * how many samples wait, so a swallowed interrupt or one left over from a
 * late drain cannot shift later reads. At 8 waiting samples it latches the
 * pointers, takes T_ANCHOR_US and reads every sample there (usually 8, more if
 * it was late), never a fixed 8. BOARD_PPG_READ_PERIOD_MS > 0 reads on a timer
 * instead (if PPG_RDY does not work in the three-slot mode); the anchor may then
 * be late by up to one PPG period.
 */
/*
 * Fake die temperature (SYNTHETIC builds only): the conversion takes
 * FAKE_TEMP_CONVERSION_US, the value is 25 degC plus a 1/16 degC sawtooth.
 */
#define FAKE_TEMP_CONVERSION_US 29000

static void fake_temp_service(die_temp_t *t, int64_t *started_us)
{
    int64_t now = esp_timer_get_time();
    switch (die_temp_next(t, now)) {
    case DIE_TEMP_START:
        *started_us = now;
        die_temp_started(t, true);
        break;
    case DIE_TEMP_POLL:
        if (now - *started_us >= FAKE_TEMP_CONVERSION_US) {
            die_temp_packet_t tp = die_temp_polled(t, DIE_TEMP_READ_OK, now);
            send_die_temp(tp, (uint64_t)now, 25 * 16 + (int32_t)(tp.index % 16u));
        }
        break;
    default:
        break;
    }
}

static void ppg_reader_task(void *arg)
{
    const fake_afe_config_t *cfg = &PPG_FAKE;
    fake_afe_t *afe;
    ESP_ERROR_CHECK(fake_afe_start(cfg, xTaskGetCurrentTaskHandle(), &afe));
    die_temp_t temp;
    int64_t temp_started = 0;
    die_temp_init(&temp, esp_timer_get_time());
    int64_t delay_at = PPG_DELAY_PERIOD_US;
    TickType_t wake = xTaskGetTickCount();
    for (;;) {
        if (BOARD_PPG_READ_PERIOD_MS > 0) {
            vTaskDelayUntil(&wake, pdMS_TO_TICKS(BOARD_PPG_READ_PERIOD_MS));
            ulTaskNotifyTake(pdTRUE, 0); /* the interrupts are not used */
        } else {
            ulTaskNotifyTake(pdTRUE, portMAX_DELAY); /* one per fake sample, 5 ms */
        }
        fake_temp_service(&temp, &temp_started);
        if (BOARD_PPG_READ_PERIOD_MS == 0 && fake_afe_waiting(afe) < cfg->batch) {
            continue;
        }
        if (FAKE_PPG_DELAY && esp_timer_get_time() >= delay_at) {
            delay_at += PPG_DELAY_PERIOD_US;
            vTaskDelay(pdMS_TO_TICKS(PPG_DELAY_MS));
        }
        fake_afe_batch_t b = fake_afe_latch(afe);
        if (b.count == 0) {
            continue; /* SAMPLE_COUNT = 0 is never sent */
        }
        uint16_t status = PKT_STATUS_LATENCY_UNMEASURED; /* until L is measured */
        if (b.lost_after > 0) {
            status |= PKT_STATUS_AFE_FIFO_OVERFLOW;
        }
        /* All slots of one read share FIRST_SAMPLE_INDEX and T_ANCHOR_US. */
        for (uint8_t slot = 0; slot < cfg->n_slots; slot++) {
            pkt_t p = {
                .channel_id = cfg->channel_ids[slot],
                .session_id = s_session_id,
                .first_sample_index = (uint32_t)b.first_index,
                .t_anchor_us = b.t_anchor_us,
                .t_first_us = pkt_t_first_us(b.t_anchor_us, b.count, cfg->fs_nominal_mhz),
                .fs_nominal_mhz = cfg->fs_nominal_mhz,
                .sample_count = b.count,
                .status = status,
            };
            for (uint16_t i = 0; i < b.count; i++) {
                p.data[i] = fake_afe_sample(afe, slot, b.first_index + i);
            }
            enqueue(&p);
        }
    }
}

#endif /* BOARD_PPG_REAL */

/*
 * SAMP edge of the fake ECG, from the esp_timer task: the sample's alarm time
 * plus a capture error of 0..3 us (budget below 5 us, V0.2 section 7.1).
 */
static void fake_samp_edge(uint64_t index, int64_t t_us)
{
    static uint32_t lcg = 1;
    static int64_t drop_at = 5000000LL, extra_at = 15000000LL;
    (void)index;
    lcg = lcg * 1664525u + 1013904223u;
    t_us += lcg >> 30;
    if (FAKE_SAMP_FAULTS && t_us >= drop_at) {
        drop_at += SAMP_FAULT_PERIOD_US;
        return;
    }
    if (FAKE_SAMP_FAULTS && t_us >= extra_at) {
        extra_at += SAMP_FAULT_PERIOD_US;
        samp_edges_push(t_us - ECG_FAKE.period_us / 2);
    }
    samp_edges_push(t_us);
}

#if BOARD_ECG_REAL
/*
 * ECG from a MAX30001 (drivers/max30001.c; not run on a chip yet). The reader
 * wakes on an INTB edge, or every ECG_POLL_MS when INTB is still low (a missed
 * edge; the FIFO has about 31 ms of room after EFIT). It reads the FIFO in one
 * burst up to the EOF word, takes the FIFO-read anchor right after it (V0.1
 * section 5.2), reads STATUS, and ecg_read_plan decides the packet, the FIFO
 * reset and the SAMP mapping error (see ecg_read.h). DATA is the raw 24-bit
 * FIFO word, tags included (V0.1 section 8). A mapping restart is a SYNCH
 * (max30001_restart); only a successful one starts a new epoch at index 0.
 *
 * Bit 8 needs BOARD_SAMP_VERIFIED: until bring-up shows that the first SAMP
 * edge after SYNCH belongs to the first FIFO sample (V0.2 section 7.2), a
 * constant one-sample offset would pass every interval check, so packets keep
 * the FIFO-read anchor. The mapping still runs, and the stats log the spread of
 * (FIFO read - edge of the packet's last sample) for that check.
 */
#ifndef BOARD_SAMP_VERIFIED
#define BOARD_SAMP_VERIFIED 0
#endif
#define ECG_FS_NOMINAL_MHZ 512000u
#define ECG_POLL_MS 10
#define ECG_PLL_TIMEOUT_MS 1000

static max30001_bus_t s_ecg_bus;
static max30001_regs_t s_ecg_regs;
static int64_t s_ecg_lag_min_us = INT64_MAX, s_ecg_lag_max_us = INT64_MIN;

static void ecg_mapping_start(void *arg)
{
    (void)arg;
    samp_edges_clear();
    samp_map_restart(&s_samp, esp_timer_get_time());
}

static void ecg_give_up(const char *what, int err)
{
    ESP_LOGE(TAG, "MAX30001 %s failed (%d): no ECG packets", what, err);
    max30001_write(&s_ecg_bus, MAX30001_EN_INT, 0); /* best effort: quiet INTB */
    max30001_esp_stop();
    /* Suspend rather than delete: an INTB ISR already running on the other
     * core may still notify this task, so its handle must stay valid. */
    for (;;) {
        vTaskSuspend(NULL);
    }
}

static void ecg_reader_task(void *arg)
{
    (void)arg;
    const int64_t period_us = (1000000000LL + ECG_FS_NOMINAL_MHZ / 2) / ECG_FS_NOMINAL_MHZ;
    samp_map_init(&s_samp, ECG_FS_NOMINAL_MHZ, SAMP_TOLERANCE_NS, SAMP_REMAP_HOLDOFF_US,
                  SAMP_REMAP_MIN_GAP_US);
    ESP_ERROR_CHECK(max30001_esp_init(&s_ecg_bus, BOARD_ECG_SPI_HZ,
                                      xTaskGetCurrentTaskHandle()));
    max30001_v1_regs(&s_ecg_regs);
    uint32_t info = 0;
    max30001_err_t err = max30001_start(&s_ecg_bus, &s_ecg_regs, ECG_PLL_TIMEOUT_MS, &info);
    ESP_LOGI(TAG, "MAX30001 INFO 0x%06" PRIx32 ", start %d", info, (int)err);
    if (err != MAX30001_OK) {
        ecg_give_up("start", (int)err);
    }
    if (BOARD_SAMP_CAPTURE) {
        ESP_ERROR_CHECK(samp_capture_start(BOARD_ECG_INT2B_GPIO, BOARD_SAMP_RISING_EDGE));
    } else {
        ESP_LOGW(TAG, "no SAMP capture: ECG anchors from FIFO reads only");
    }
    if (!BOARD_SAMP_VERIFIED) {
        ESP_LOGW(TAG, "SAMP alignment not verified: ECG bit 8 off (bring-up section 7)");
    }
    err = max30001_restart(&s_ecg_bus, &s_ecg_regs, ecg_mapping_start, NULL);
    if (err != MAX30001_OK) {
        ecg_give_up("SYNCH", (int)err);
    }
    ecg_read_t ecg;
    ecg_read_init(&ecg, false);
    for (;;) {
        if (ulTaskNotifyTake(pdTRUE, pdMS_TO_TICKS(ECG_POLL_MS)) == 0
            && !max30001_esp_intb_low()) {
            continue; /* no edge and INTB high: below the threshold */
        }
        max30001_fifo_t f;
        uint32_t st = 0;
        bool bus_ok = max30001_read_fifo(&s_ecg_bus, &f) == MAX30001_OK;
        uint64_t t_read = esp_timer_get_time(); /* right after the EOF word, if any */
        bus_ok = bus_ok && max30001_read(&s_ecg_bus, MAX30001_STATUS, &st) == 0;
        ecg_read_plan_t plan = ecg_read_plan(&ecg, &f, bus_ok, st, t_read,
                                             ECG_FS_NOMINAL_MHZ,
                                             PKT_STATUS_LATENCY_UNMEASURED);
        if (plan.fifo_reset && max30001_command(&s_ecg_bus, MAX30001_FIFO_RST) != 0) {
            imu_index_read_failed(&ecg.index);
            plan.mapping_error = true;
            plan.cause = SAMP_AFE;
        }
        if (plan.mapping_error) {
            samp_map_error(&s_samp, plan.cause, esp_timer_get_time());
        }
        if (plan.send) {
            imu_chunk_t *c = &plan.chunk;
            uint64_t anchor = t_read;
            int64_t deadline = (int64_t)t_read + SAMP_WAIT_PERIODS * period_us;
            if (s_samp.state != SAMP_ERROR) {
                samp_edges_wait(c->first_index + c->count - 1u, deadline);
            }
            int64_t edge_us;
            if (samp_map_packet(&s_samp, c->first_index, c->count, samp_edges_lookup, NULL,
                                deadline, esp_timer_get_time(), &edge_us) == SAMP_OK) {
                if (!(c->status & PKT_STATUS_AFE_FIFO_OVERFLOW)) {
                    /* Only drains that ended on EOF have a bounded read time. */
                    int64_t lag = (int64_t)t_read - edge_us;
                    s_ecg_lag_min_us = lag < s_ecg_lag_min_us ? lag : s_ecg_lag_min_us;
                    s_ecg_lag_max_us = lag > s_ecg_lag_max_us ? lag : s_ecg_lag_max_us;
                }
                if (BOARD_SAMP_VERIFIED) {
                    anchor = (uint64_t)edge_us;
                    c->status |= PKT_STATUS_ANCHOR_SAMP;
                }
            }
            pkt_t p = {
                .channel_id = PKT_CH_ECG,
                .session_id = s_session_id,
                .first_sample_index = c->first_index,
                .t_anchor_us = anchor,
                .t_first_us = pkt_t_first_us(anchor, c->count, ECG_FS_NOMINAL_MHZ),
                .fs_nominal_mhz = ECG_FS_NOMINAL_MHZ,
                .sample_count = c->count,
                .status = c->status,
            };
            for (uint16_t i = 0; i < c->count; i++) {
                p.data[i] = (int32_t)f.word[i];
            }
            enqueue(&p);
        }
        if (samp_map_restart_due(&s_samp, esp_timer_get_time())) {
            err = max30001_restart(&s_ecg_bus, &s_ecg_regs, ecg_mapping_start, NULL);
            if (err == MAX30001_OK) {
                ecg_read_init(&ecg, true);
            } else {
                /* Unknown whether SYNCH ran: keep the index, re-anchor it by
                 * time, and keep the mapping in error until the next try. */
                ESP_LOGE(TAG, "MAX30001 SYNCH failed during a mapping restart (%d)", (int)err);
                imu_index_read_failed(&ecg.index);
                samp_map_error(&s_samp, SAMP_AFE, esp_timer_get_time());
            }
            ESP_LOGW(TAG, "SAMP mapping restarted (%" PRIu32 " so far)", s_samp.remaps);
        }
    }
}
#else
/*
 * ECG reads with the SAMP anchor (V0.2 section 7.3). The anchor is the FIFO
 * read time unless samp_map_packet accepts the edges up to the packet's last
 * sample; then it is that edge and the packet sets bit 8. A mapping restart
 * stops the conversions, clears the edge ring and starts again (SYNCH): the
 * index restarts at 0 and the next packet sets bit 5.
 */
static void ecg_reader_task(void *arg)
{
    const fake_afe_config_t *cfg = &ECG_FAKE;
    const int64_t period_us = (1000000000LL + cfg->fs_nominal_mhz / 2) / cfg->fs_nominal_mhz;
    samp_map_init(&s_samp, cfg->fs_nominal_mhz, SAMP_TOLERANCE_NS, SAMP_REMAP_HOLDOFF_US,
                  SAMP_REMAP_MIN_GAP_US);
    if (BOARD_SAMP_CAPTURE) {
        ESP_ERROR_CHECK(samp_capture_start(BOARD_ECG_INT2B_GPIO, BOARD_SAMP_RISING_EDGE));
    }
    /* Mapping start before the first conversion (section 7.2). */
    samp_edges_clear();
    samp_map_restart(&s_samp, esp_timer_get_time());
    fake_afe_t *afe;
    ESP_ERROR_CHECK(fake_afe_start(cfg, xTaskGetCurrentTaskHandle(), &afe));
    uint16_t restart_bits = 0;
    for (;;) {
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        fake_afe_batch_t b = fake_afe_latch(afe);
        if (b.count == 0) {
            continue; /* SAMPLE_COUNT = 0 is never sent */
        }
        uint16_t status = PKT_STATUS_LATENCY_UNMEASURED | restart_bits;
        restart_bits = 0;
        if (b.lost_after > 0) {
            status |= PKT_STATUS_AFE_FIFO_OVERFLOW;
            samp_map_error(&s_samp, SAMP_OVERFLOW, esp_timer_get_time());
        }
        uint32_t k_first = (uint32_t)b.first_index;
        /* The edge of the last sample may come after its data can be read; it
         * must lie within two sample periods of the read (section 7.3). */
        int64_t deadline = (int64_t)b.t_anchor_us + SAMP_WAIT_PERIODS * period_us;
        if (s_samp.state != SAMP_ERROR) {
            samp_edges_wait(k_first + b.count - 1u, deadline);
        }
        uint64_t anchor = b.t_anchor_us;
        int64_t edge_us;
        if (samp_map_packet(&s_samp, k_first, b.count, samp_edges_lookup, NULL, deadline,
                            esp_timer_get_time(), &edge_us) == SAMP_OK) {
            anchor = (uint64_t)edge_us;
            status |= PKT_STATUS_ANCHOR_SAMP;
        }
        pkt_t p = {
            .channel_id = PKT_CH_ECG,
            .session_id = s_session_id,
            .first_sample_index = k_first,
            .t_anchor_us = anchor,
            .t_first_us = pkt_t_first_us(anchor, b.count, cfg->fs_nominal_mhz),
            .fs_nominal_mhz = cfg->fs_nominal_mhz,
            .sample_count = b.count,
            .status = status,
        };
        for (uint16_t i = 0; i < b.count; i++) {
            p.data[i] = fake_afe_sample(afe, 0, b.first_index + i);
        }
        enqueue(&p);
        if (samp_map_restart_due(&s_samp, esp_timer_get_time())) {
            fake_afe_stop(afe);
            samp_edges_clear();
            samp_map_restart(&s_samp, esp_timer_get_time());
            ESP_ERROR_CHECK(fake_afe_resume(afe));
            restart_bits = PKT_STATUS_INDEX_REANCHORED;
            ESP_LOGW(TAG, "SAMP mapping restarted (%" PRIu32 " so far)", s_samp.remaps);
        }
    }
}

#endif /* BOARD_ECG_REAL */

#if BOARD_IMU_REAL
/*
 * IMU from a BMI270 (drivers/bmi270.c; not run on a chip yet), V0.2 sections 3-5.
 * Every INT1 rising edge (FIFO watermark, 10 frames), and every IMU_POLL_MS
 * without one (INT1 is non-latched and stays high while the FIFO is at or above
 * the watermark, so a late reader gets no new edge), the reader reads
 * FIFO_LENGTH, takes T_ANCHOR_US right after it, and once 10 frames wait (or the
 * FIFO is full) reads exactly the latched frames in one burst. imu_plan_read
 * gives the index, the chunks of at most 32 frames (bit 7), bit 0 when full and
 * the re-anchor after it (bit 5); a failed latch or read sends nothing and the
 * next read re-anchors (bits 3 and 5). A read that failed may have taken some
 * frames out, so the FIFO is flushed before reading on (bit 0 kept if it was
 * full): frames kept from before a loss must not join later ones; if the flush
 * fails too, the chip is started again (its start ends with a flush). A FIFO
 * length that is not whole frames calls for a check at the next wake. Every
 * IMU_CHECK_MS
 * bmi270_check makes sure the chip was not reset or broken; if it was, the chip
 * is started again every IMU_RESTART_MS until that works, with no packet and
 * no INT1 interrupt meanwhile, and the next read re-anchors (bits 3 and 5). The
 * first start is tried IMU_START_TRIES times before giving up.
 */
#define IMU_FS_NOMINAL_MHZ 100000u
#define IMU_WATERMARK_FRAMES 10u
#define IMU_POLL_MS 20
#define IMU_CHECK_MS 1000
#define IMU_RESTART_MS 100
#define IMU_START_TRIES 10

static const uint8_t IMU_CHANNELS[BMI270_AXES] = {
    PKT_CH_ACC_X, PKT_CH_ACC_Y, PKT_CH_ACC_Z, PKT_CH_GYR_X, PKT_CH_GYR_Y, PKT_CH_GYR_Z};

static bmi270_bus_t s_imu_bus;
static bmi270_regs_t s_imu_regs;

static void imu_give_up(int err)
{
    ESP_LOGE(TAG, "BMI270 start failed (%d): no IMU packets", err);
    bmi270_esp_stop();
    for (;;) {
        vTaskSuspend(NULL); /* keep the handle valid for an ISR in flight */
    }
}

static void imu_reader_task(void *arg)
{
    (void)arg;
    ESP_ERROR_CHECK(bmi270_esp_init(&s_imu_bus, BOARD_IMU_SPI_HZ,
                                    xTaskGetCurrentTaskHandle()));
    bmi270_v1_regs(&s_imu_regs);
    bmi270_err_t err = BMI270_ERR_BUS;
    for (int i = 0; i < IMU_START_TRIES && err != BMI270_OK; i++) {
        if (i > 0) {
            vTaskDelay(pdMS_TO_TICKS(IMU_RESTART_MS));
        }
        err = bmi270_start(&s_imu_bus, &s_imu_regs, bmi270_config_file);
    }
    ESP_LOGI(TAG, "BMI270 start %d, SPI %u Hz", (int)err, (unsigned)BOARD_IMU_SPI_HZ);
    if (err != BMI270_OK) {
        imu_give_up((int)err);
    }
    bmi270_esp_int_enable(true);
    imu_index_t index;
    imu_index_init(&index, 0);
    imu_chunk_t chunks[IMU_MAX_CHUNKS];
    static bmi270_frames_t frames;
    bool restart = false;
    int64_t next_check = esp_timer_get_time() + IMU_CHECK_MS * 1000LL;
    int64_t next_restart = 0;
    for (;;) {
        ulTaskNotifyTake(pdTRUE, pdMS_TO_TICKS(IMU_POLL_MS));
        int64_t now = esp_timer_get_time();
        if (!restart && now >= next_check) {
            next_check = now + IMU_CHECK_MS * 1000LL;
            err = bmi270_check(&s_imu_bus, &s_imu_regs);
            if (err != BMI270_OK) {
                ESP_LOGE(TAG, "BMI270 check failed (%d): starting it again", (int)err);
                imu_index_read_failed(&index);
                bmi270_esp_int_enable(false);
                restart = true;
            }
        }
        if (restart) {
            if (now < next_restart) {
                continue;
            }
            next_restart = now + IMU_RESTART_MS * 1000LL;
            err = bmi270_start(&s_imu_bus, &s_imu_regs, bmi270_config_file);
            if (err != BMI270_OK) {
                ESP_LOGE(TAG, "BMI270 start failed (%d), retrying", (int)err);
                continue;
            }
            ESP_LOGW(TAG, "BMI270 started again");
            bmi270_esp_int_enable(true);
            restart = false;
            next_check = esp_timer_get_time() + IMU_CHECK_MS * 1000LL;
            continue;
        }
        bmi270_latch_t latch;
        err = bmi270_latch(&s_imu_bus, &latch);
        if (err != BMI270_OK) {
            imu_index_read_failed(&index);
            if (err == BMI270_ERR_STATE) {
                next_check = now; /* not a fill level: is the chip still there? */
            }
            continue;
        }
        uint64_t anchor = esp_timer_get_time(); /* right after FIFO_LENGTH (section 3) */
        if (latch.frames == 0 || (latch.frames < IMU_WATERMARK_FRAMES && !latch.full)) {
            continue;
        }
        if (bmi270_read_frames(&s_imu_bus, latch.frames, &frames) != BMI270_OK) {
            imu_index_read_failed(&index);
            if (latch.full) {
                index.pending |= PKT_STATUS_AFE_FIFO_OVERFLOW; /* frames were lost */
            }
            if (bmi270_flush(&s_imu_bus) != BMI270_OK) {
                ESP_LOGE(TAG, "BMI270 FIFO flush failed: starting it again");
                bmi270_esp_int_enable(false);
                restart = true;
            }
            continue;
        }
        size_t n = imu_plan_read(&index, latch.frames, anchor, latch.full, IMU_FS_NOMINAL_MHZ,
                                 PKT_STATUS_LATENCY_UNMEASURED, chunks, IMU_MAX_CHUNKS);
        for (size_t c = 0; c < n; c++) {
            for (unsigned axis = 0; axis < BMI270_AXES; axis++) {
                pkt_t p = {
                    .channel_id = IMU_CHANNELS[axis],
                    .session_id = s_session_id,
                    .first_sample_index = chunks[c].first_index,
                    .t_anchor_us = anchor,
                    .t_first_us = chunks[c].t_first_us,
                    .fs_nominal_mhz = IMU_FS_NOMINAL_MHZ,
                    .sample_count = chunks[c].count,
                    .status = chunks[c].status,
                };
                for (uint16_t i = 0; i < chunks[c].count; i++) {
                    p.data[i] = frames.value[chunks[c].offset + i][axis];
                }
                enqueue(&p);
            }
        }
    }
}
#else
/*
 * IMU reads (V0.2 sections 3-5), with the fake source in place of a BMI270.
 * The six axes of a read share FIRST_SAMPLE_INDEX, T_ANCHOR_US and STATUS;
 * imu_plan_read splits a read of more than 32 frames and re-anchors after a full
 * FIFO. DATA follows the true sample index, so a wrong re-anchor shows as DATA
 * that does not match FIRST_SAMPLE_INDEX. The true loss is logged on UART0 as
 * the answer key; a BMI270 does not report it.
 */
static void imu_reader_task(void *arg)
{
    const fake_afe_config_t *cfg = &IMU_FAKE;
    fake_afe_t *imu;
    ESP_ERROR_CHECK(fake_afe_start(cfg, xTaskGetCurrentTaskHandle(), &imu));
    imu_index_t index;
    imu_index_init(&index, 0);
    imu_chunk_t chunks[IMU_MAX_CHUNKS];
    int64_t backlog_at = 10000000LL, full_at = 20000000LL;
    for (;;) {
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        if (FAKE_IMU_STALLS) {
            int64_t now = esp_timer_get_time();
            if (now >= backlog_at) {
                backlog_at += IMU_STALL_PERIOD_US;
                vTaskDelay(pdMS_TO_TICKS(500));
            } else if (now >= full_at) {
                full_at += IMU_STALL_PERIOD_US;
                vTaskDelay(pdMS_TO_TICKS(2500));
            }
        }
        fake_afe_batch_t b = fake_afe_latch(imu);
        if (b.count == 0) {
            continue;
        }
        /* Section 5: full when the latched length leaves no room for a frame. */
        bool full = b.count == cfg->depth;
        size_t n = imu_plan_read(&index, b.count, b.t_anchor_us, full, cfg->fs_nominal_mhz,
                                 PKT_STATUS_LATENCY_UNMEASURED, chunks, IMU_MAX_CHUNKS);
        for (size_t c = 0; c < n; c++) {
            for (uint8_t slot = 0; slot < cfg->n_slots; slot++) {
                pkt_t p = {
                    .channel_id = cfg->channel_ids[slot],
                    .session_id = s_session_id,
                    .first_sample_index = chunks[c].first_index,
                    .t_anchor_us = b.t_anchor_us,
                    .t_first_us = chunks[c].t_first_us,
                    .fs_nominal_mhz = cfg->fs_nominal_mhz,
                    .sample_count = chunks[c].count,
                    .status = chunks[c].status,
                };
                for (uint16_t i = 0; i < chunks[c].count; i++) {
                    p.data[i] = fake_afe_sample(imu, slot, b.first_index + chunks[c].offset + i);
                }
                enqueue(&p);
            }
        }
        if (n > 0 && chunks[0].status & PKT_STATUS_INDEX_REANCHORED) {
            ESP_LOGW(TAG, "IMU re-anchored to index %" PRIu32 ", true index %" PRIu32,
                     chunks[0].first_index, (uint32_t)b.first_index);
        }
        if (b.lost_after > 0) {
            ESP_LOGW(TAG, "fake IMU FIFO full: %" PRIu32 " frames lost (answer key)",
                     b.lost_after);
        }
    }
}
#endif /* BOARD_IMU_REAL */

/* Falling edge of the t0 button: keep the time of the first edge. */
static void t0_isr(void *arg)
{
    static int64_t last_us = -T0_LOCKOUT_US;
    /* Edges dropped since the last one queued; only this ISR touches it, and it
     * travels with the next queued edge, so the warning lands on the right event. */
    static uint32_t lost_since_queued;
    int64_t now = esp_timer_get_time();
    if (now - last_us < T0_LOCKOUT_US) {
        return;
    }
    last_us = now;
    const t0_edge_t edge = {.t_us = now, .lost_before = lost_since_queued};
    BaseType_t woken = pdFALSE;
    if (xQueueSendFromISR(s_event_queue, &edge, &woken) == pdTRUE) {
        lost_since_queued = 0;
    } else {
        lost_since_queued++;
        s_events_lost++;
    }
    if (woken) {
        portYIELD_FROM_ISR();
    }
}

/*
 * Event packet 0xC1 (schema section 10): SAMPLE_COUNT 1, DATA[0] the event
 * code, T_ANCHOR_US = T_FIRST_US = edge time, FIRST_SAMPLE_INDEX counts the
 * confirmed events of the session, FS_NOMINAL_MHZ 0, STATUS bit 4 off. An
 * edge the ISR queue dropped was never debounced, so it does not take an
 * ordinal; the next event packet sets bit 1 instead (possible lost press).
 */
static void event_task(void *arg)
{
    uint32_t ordinal = 0;
    bool edges_lost = false;
    t0_edge_t edge;
    for (;;) {
        xQueueReceive(s_event_queue, &edge, portMAX_DELAY);
        if (edge.lost_before > 0) {
            edges_lost = true; /* kept until an event is sent, even past a bounce */
        }
        vTaskDelay(pdMS_TO_TICKS(T0_CONFIRM_MS));
        if (gpio_get_level(BOARD_T0_GPIO) != 0) {
            continue; /* released again: bounce, not a press */
        }
        pkt_t p = {
            .channel_id = PKT_CH_EVENT,
            .session_id = s_session_id,
            .first_sample_index = ordinal++,
            .t_anchor_us = (uint64_t)edge.t_us,
            .t_first_us = (uint64_t)edge.t_us,
            .fs_nominal_mhz = 0,
            .sample_count = 1,
            .status = edges_lost ? PKT_STATUS_MCU_BUFFER_OVERFLOW : 0,
            .data = {PKT_EVENT_T0},
        };
        edges_lost = false;
        enqueue(&p);
        ESP_LOGI(TAG, "t0 event %" PRIu32 " at %" PRId64 " us", p.first_sample_index,
                 edge.t_us);
    }
}

/*
 * Device info packets 0xD1 (V0.2 section 6): one right after the USB driver
 * starts, then every 10 s, so a logger that starts mid-session gets one within
 * 10 s. FIRST_SAMPLE_INDEX counts the packets made in the session, dropped ones
 * included, so the logger can count the ones lost before a SEQ.
 */
static void device_info_task(void *arg)
{
    const esp_app_desc_t *app = esp_app_get_description();
    pkt_t p = {
        .channel_id = PKT_CH_DEVICE_INFO,
        .session_id = s_session_id,
        .fs_nominal_mhz = 0,
        .sample_count = PKT_DEVICE_INFO_COUNT,
    };
    if (!pkt_device_info_data(app->app_elf_sha256, app->version, app->idf_ver, p.data)) {
        /* The logger then reports device_info_missing for the session. */
        ESP_LOGE(TAG, "app or ESP-IDF version is not ASCII of at most 31 bytes: "
                      "no device info packets");
        vTaskDelete(NULL);
    }
    TickType_t wake = xTaskGetTickCount();
    for (uint32_t ordinal = 0;; ordinal++) {
        p.first_sample_index = ordinal;
        p.t_anchor_us = (uint64_t)esp_timer_get_time();
        p.t_first_us = p.t_anchor_us;
        p.status = 0; /* enqueue may add bit 1 */
        enqueue(&p);
        vTaskDelayUntil(&wake, pdMS_TO_TICKS(DEVICE_INFO_PERIOD_MS));
    }
}

static void log_stats(void)
{
    for (int k = 0; k < CH_COUNT; k++) {
        const channel_stats_t *s = &s_stats[k];
        if (s->sent || s->tx_timeout || s->queue_drop) {
            ESP_LOGI(TAG, "ch 0x%02X sent %" PRIu32 " tx_timeout %" PRIu32 " queue_drop %" PRIu32,
                     CHANNEL_IDS[k], s->sent, s->tx_timeout, s->queue_drop);
        }
    }
    if (s_events_lost) {
        ESP_LOGW(TAG, "t0 events lost in ISR queue: %" PRIu32, s_events_lost);
    }
    /* V0.2 section 7.7. A missed and an overwritten capture look the same: one
     * interval of about two periods. */
    static const char *const STATES[] = {"unmapped", "mapped", "error"};
    const uint32_t *r = s_samp.results;
    ESP_LOGI(TAG, "SAMP %s: packets bit 8 %" PRIu32 ", FIFO-read %" PRIu32 "; errors: "
                  "missed/overwritten %" PRIu32 ", extra %" PRIu32 ", edge missing %" PRIu32
                  ", late %" PRIu32 ", index %" PRIu32 ", FIFO overflow %" PRIu32
                  ", AFE %" PRIu32 "; restarts %" PRIu32,
             STATES[s_samp.state], s_samp.packets_samp, s_samp.packets_fifo, r[SAMP_LONG],
             r[SAMP_SHORT], r[SAMP_EDGE_MISSING], r[SAMP_LATE], r[SAMP_INDEX],
             r[SAMP_OVERFLOW], r[SAMP_AFE], s_samp.remaps);
#if BOARD_ECG_REAL
    if (s_ecg_lag_min_us <= s_ecg_lag_max_us) {
        /* Bring-up check of the SAMP alignment (V0.2 section 7.2): with the right
         * edge, the FIFO read follows it by 0 .. about one period plus the read. */
        ESP_LOGI(TAG, "ECG FIFO read - SAMP edge of the last sample: %" PRId64 " .. %" PRId64
                      " us%s", s_ecg_lag_min_us, s_ecg_lag_max_us,
                 BOARD_SAMP_VERIFIED ? "" : " (bit 8 off until verified)");
    }
#endif
    if (BOARD_SAMP_CAPTURE) {
        samp_capture_stats_t c = samp_capture_stats();
        ESP_LOGI(TAG, "SAMP clock pairs %" PRIu32 ", rejected %" PRIu32 ", max error %" PRId64
                      " ns, conversions refused (no fresh pair) %" PRIu32,
                 c.pairs, c.pairs_rejected, c.max_error_ns, c.stale);
    }
}

void app_main(void)
{
    const gpio_config_t led = {
        .pin_bit_mask = 1ULL << BOARD_LED_STAT_GPIO,
        .mode = GPIO_MODE_OUTPUT,
    };
    ESP_ERROR_CHECK(gpio_config(&led));

    const esp_app_desc_t *app = esp_app_get_description();
    char elf_sha[65];
    esp_app_get_elf_sha256(elf_sha, sizeof(elf_sha));
    ESP_LOGI(TAG, "%s %s, ESP-IDF %s, ELF SHA-256 %s", app->project_name, app->version,
             app->idf_ver, elf_sha);

    if (!pkt_self_test()) {
        ESP_LOGE(TAG, "packet self-test FAILED: not streaming");
        for (int level = 0;; level ^= 1) {
            gpio_set_level(BOARD_LED_STAT_GPIO, level);
            vTaskDelay(pdMS_TO_TICKS(50));
        }
    }
    ESP_LOGI(TAG, "packet self-test passed");

    /* New SESSION_ID at every boot; the RF is off, so enable the entropy
     * source while drawing it. */
    bootloader_random_enable();
    s_session_id = esp_random();
    bootloader_random_disable();
    ESP_LOGI(TAG, "SESSION_ID %" PRIu32 " (0x%08" PRIX32 ")", s_session_id, s_session_id);

    usb_serial_jtag_driver_config_t usb = USB_SERIAL_JTAG_DRIVER_CONFIG_DEFAULT();
    usb.tx_buffer_size = USB_TX_BUFFER_BYTES;
    usb.rx_buffer_size = USB_RX_BUFFER_BYTES;
    ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&usb));

    s_tx_queue = xQueueCreate(TX_QUEUE_LEN, sizeof(pkt_t));
    s_event_queue = xQueueCreate(EVENT_QUEUE_LEN, sizeof(t0_edge_t));
    if (s_tx_queue == NULL || s_event_queue == NULL) {
        ESP_LOGE(TAG, "cannot create queues");
        abort();
    }
    if (xTaskCreate(tx_task, "pkt_tx", 4096, NULL, 5, NULL) != pdPASS
        || xTaskCreate(device_info_task, "dev_info", 3072, NULL, 4, NULL) != pdPASS
        || xTaskCreate(event_task, "t0_event", 3072, NULL, 6, NULL) != pdPASS) {
        ESP_LOGE(TAG, "cannot create tasks");
        abort();
    }

    const gpio_config_t t0 = {
        .pin_bit_mask = 1ULL << BOARD_T0_GPIO,
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .intr_type = GPIO_INTR_NEGEDGE,
    };
    ESP_ERROR_CHECK(gpio_config(&t0));
    ESP_ERROR_CHECK(gpio_install_isr_service(0));
    ESP_ERROR_CHECK(gpio_isr_handler_add(BOARD_T0_GPIO, t0_isr, NULL));

    if (xTaskCreate(ecg_reader_task, "ecg_reader", 4096, NULL, 6, NULL) != pdPASS
        || xTaskCreate(ppg_reader_task, "ppg_reader", 4096, NULL, 6, NULL) != pdPASS
        || xTaskCreate(imu_reader_task, "imu_reader", 4096, NULL, 6, NULL) != pdPASS) {
        ESP_LOGE(TAG, "cannot create reader tasks");
        abort();
    }
    ESP_LOGI(TAG, "streaming %s ECG 0xE1 %u us x %u, %s PPG 0xF1-0xF3 %u us x %u, "
                  "%s IMU 0xA1-0xA6 %u us x %u%s, t0 on GPIO%d",
             BOARD_ECG_REAL ? "MAX30001" : "FAKE", (unsigned)ECG_FAKE.period_us,
             (unsigned)ECG_FAKE.batch, BOARD_PPG_REAL ? "MAX30101" : "FAKE",
             (unsigned)PPG_FAKE.period_us, (unsigned)PPG_FAKE.batch,
             BOARD_IMU_REAL ? "BMI270" : "FAKE", (unsigned)IMU_FAKE.period_us,
             (unsigned)IMU_FAKE.batch, FAKE_IMU_STALLS ? " with read stalls" : "",
             BOARD_T0_GPIO);
    if (BOARD_PPG_READ_PERIOD_MS > 0) {
        ESP_LOGW(TAG, "PPG read every %d ms (timer), not on PPG_RDY", BOARD_PPG_READ_PERIOD_MS);
    }

    int level = 0;
    for (int64_t next_stats = esp_timer_get_time() + STATS_PERIOD_MS * 1000LL;;) {
        vTaskDelay(pdMS_TO_TICKS(LED_PERIOD_MS));
        level ^= 1;
        gpio_set_level(BOARD_LED_STAT_GPIO, level);
        if (esp_timer_get_time() >= next_stats) {
            next_stats += STATS_PERIOD_MS * 1000LL;
            log_stats();
        }
    }
}
