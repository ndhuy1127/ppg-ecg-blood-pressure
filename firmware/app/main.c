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
#include <string.h>
#include <stdlib.h>

#include "afe_order.h"
#include "bmi270.h"
#include "bmi270_config.h"
#include "bmi270_esp.h"
#include "board_v1_module.h"
#include "cmd_exec.h"
#include "cmd_wire.h"
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
#include "ecg_loop.h"
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
#include "stim_plan.h"

static const char *TAG = "fw";

#define TX_QUEUE_LEN 64
#define TX_TIMEOUT_MS 20
#define USB_TX_BUFFER_BYTES 8192
#define USB_RX_BUFFER_BYTES 1024 /* commands, read continuously (V0.2 section 13) */
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

/* A chip that fails to start at boot is tried AFE_START_TRIES times,
 * AFE_START_RETRY_MS apart (its start begins with a reset), before its reader
 * gives up and sends no packets of it (decided 2026-10-25). */
#define AFE_START_TRIES 10
#define AFE_START_RETRY_MS 100
#define PPG_DELAY_MS 12

enum {
    CH_ECG, CH_PPG1, CH_PPG2, CH_PPG3, CH_PPG4, CH_EVENT, CH_DEVICE_INFO,
    CH_ACC_X, CH_ACC_Y, CH_ACC_Z, CH_GYR_X, CH_GYR_Y, CH_GYR_Z, CH_DIE_TEMP,
    CH_AFE_CONFIG, CH_COMMAND_ACK, CH_COUNT
};
static const uint8_t CHANNEL_IDS[CH_COUNT] = {
    PKT_CH_ECG, PKT_CH_PPG_SLOT1, PKT_CH_PPG_SLOT2, PKT_CH_PPG_SLOT3,
    PKT_CH_PPG_SLOT4, PKT_CH_EVENT, PKT_CH_DEVICE_INFO, PKT_CH_ACC_X,
    PKT_CH_ACC_Y, PKT_CH_ACC_Z, PKT_CH_GYR_X, PKT_CH_GYR_Y, PKT_CH_GYR_Z,
    PKT_CH_DIE_TEMP, PKT_CH_AFE_CONFIG, PKT_CH_COMMAND_ACK,
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

/* One event (the t0 button, a sync stimulus pulse, or a MARK_EVENT command),
 * with the edges of its source that the queue dropped just before it (always 0
 * for a command: a full queue answers it BUSY instead). */
typedef struct {
    int64_t t_us;
    uint32_t lost_before;
    uint8_t code; /* PKT_EVENT_T0, PKT_EVENT_SYNC_PULSE, or 2 / 4 from MARK_EVENT */
} event_edge_t;

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
static bool enqueue(pkt_t *p)
{
    int k = channel_index(p->channel_id);
    /* 0xD2 interleaves three AFEs on one channel: the control task keeps bit 1
     * per AFE itself (V0.2 section 12), so nothing is carried here. */
    bool carries = p->channel_id != PKT_CH_AFE_CONFIG;
    if (carries) {
        p->status |= s_drop_bits[k];
    }
    if (xQueueSend(s_tx_queue, p, 0) == pdTRUE) {
        s_drop_bits[k] = 0;
        return true;
    }
    if (carries) {
        s_drop_bits[k] = (p->status & CARRY_BITS) | PKT_STATUS_MCU_BUFFER_OVERFLOW;
    }
    s_stats[k].queue_drop++;
    return false;
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
            /* Not for 0xD2 (one channel, three AFEs): its SEQ gap shows the loss. */
            carry[k] = p.channel_id != PKT_CH_AFE_CONFIG ? p.status & CARRY_BITS : 0u;
        }
    }
}

/*
 * AFE states for 0xD2 (V0.2 section 12). Each reader publishes every change of
 * its AFE's state (fake source at start; chip configured, waiting for
 * reconfiguration, given up): into s_afe_latest, always, and through
 * s_afe_queue, so no transition is overwritten before it is sent; only the
 * control task makes 0xD2 packets. A transition the full queue refused leaves its
 * order in s_afe_lost: the control task then sends that AFE's latest state with
 * STATUS bit 1 (afe_order.h). The generation counts successful configurations
 * since boot.
 */
typedef struct {
    uint8_t afe, source;
    bool configured;
    uint32_t generation;
    uint16_t n;
    uint32_t words[PKT_AFE_MAX_REGS];
    int64_t since_us; /* T_ANCHOR_US: when this state began */
    uint64_t order;   /* publication order of this AFE's states, from 1 */
} afe_state_t;

#define AFE_QUEUE_LEN 8
static QueueHandle_t s_afe_queue;
static afe_state_t s_afe_latest[3]; /* under s_afe_lock */
static bool s_afe_known[3];          /* under s_afe_lock */
static uint64_t s_afe_order[3];      /* under s_afe_lock */
static uint64_t s_afe_lost[3];       /* under s_afe_lock: newest order not queued, or 0 */
static portMUX_TYPE s_afe_lock = portMUX_INITIALIZER_UNLOCKED;

static void afe_publish(uint8_t afe, uint8_t source, bool configured, uint32_t generation,
                        const uint32_t *words, uint16_t n)
{
    afe_state_t s = {
        .afe = afe,
        .source = source,
        .configured = configured,
        .generation = generation,
        .n = words != NULL ? (n > PKT_AFE_MAX_REGS ? PKT_AFE_MAX_REGS : n) : 0u,
        .since_us = esp_timer_get_time(),
    };
    if (s.n > 0) {
        memcpy(s.words, words, s.n * sizeof(uint32_t));
    }
    taskENTER_CRITICAL(&s_afe_lock);
    s.order = ++s_afe_order[afe - 1u];
    s_afe_latest[afe - 1u] = s;
    s_afe_known[afe - 1u] = true;
    taskEXIT_CRITICAL(&s_afe_lock);
    /* The control task never sends a state older than one it already sent
     * (`order`), so the latest-state sends below cannot be overtaken. */
    if (xQueueSend(s_afe_queue, &s, 0) != pdTRUE) {
        taskENTER_CRITICAL(&s_afe_lock);
        s_afe_lost[afe - 1u] = s.order;
        taskEXIT_CRITICAL(&s_afe_lock);
    }
}

/* PPG side of the LED command (V0.2 section 13): the control task asks, the PPG
 * reader (owner of the I2C bus) answers with the request's token, so a late
 * answer can never be taken for another request's. */
typedef struct {
    uint32_t token;
    uint8_t green, red, ir;
} led_request_t;
typedef struct {
    uint32_t token;
    uint8_t result;
    uint32_t generation;
} led_reply_t;
static QueueHandle_t s_led_request, s_led_reply;
static volatile cmd_ppg_state_t s_ppg_cmd_state = CMD_PPG_NONE;

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

static uint32_t s_ppg_generation; /* successful configurations since boot */

/* State for 0xD2 and for the LED command: configured with s_ppg_regs, or not. */
static void ppg_publish(bool configured)
{
    uint32_t words[MAX30101_CONFIG_WORDS];
    unsigned n = max30101_config_words(&s_ppg_regs, words);
    afe_publish(PKT_AFE_MAX30101, PKT_AFE_SOURCE_CHIP, configured, s_ppg_generation, words,
                (uint16_t)n);
    s_ppg_cmd_state = configured ? CMD_PPG_READY : CMD_PPG_BUSY;
}

static void ppg_give_up(const char *what, int err)
{
    ESP_LOGE(TAG, "MAX30101 %s failed (%d): no PPG packets", what, err);
    s_ppg_cmd_state = CMD_PPG_NONE;
    afe_publish(PKT_AFE_MAX30101, PKT_AFE_SOURCE_CHIP, false, s_ppg_generation, NULL, 0);
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
    max30101_err_t err = MAX30101_ERR_BUS;
    for (int i = 0; i < AFE_START_TRIES && err != MAX30101_OK; i++) {
        if (i > 0) {
            vTaskDelay(pdMS_TO_TICKS(AFE_START_RETRY_MS));
        }
        err = max30101_start(&s_ppg_bus, &s_ppg_regs, &rev);
    }
    ESP_LOGI(TAG, "MAX30101 REV_ID 0x%02X, LED_PW %u us, start %d", rev,
             (unsigned)BOARD_PPG_LED_PW_US, (int)err);
    if (err != MAX30101_OK) {
        ppg_give_up("start", (int)err);
    }
    s_ppg_generation = 1;
    ppg_publish(true);
    bool published_down = false;
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
        led_request_t req;
        if (xQueueReceive(s_led_request, &req, 0) == pdTRUE) {
            /* V0.2 section 13: new LED currents through a full reconfiguration
             * (RESET empties the FIFO), so the next packet re-anchors (bit 5) and
             * no chain mixes old and new currents. The old currents stay in
             * s_ppg_regs until the new ones are verified. */
            led_reply_t reply = {.token = req.token, .result = CMD_RESULT_BUSY};
            if (!ppg.needs_reconfigure) {
                max30101_regs_t staged = s_ppg_regs;
                max30101_set_currents(&staged, req.green, req.red, req.ir);
                die_temp_abort(&temp);
                ppg.index.reanchor = true;
                err = max30101_start(&s_ppg_bus, &staged, &rev);
                if (err == MAX30101_OK) {
                    s_ppg_regs = staged;
                    s_ppg_generation++;
                    ppg_publish(true);
                    reply.result = CMD_RESULT_OK;
                    reply.generation = s_ppg_generation;
                    ESP_LOGW(TAG, "MAX30101 LED codes green %u (per sink), red %u, IR %u",
                             req.green, req.red, req.ir);
                } else {
                    /* Back to the old currents through the reconfiguration path. */
                    ESP_LOGE(TAG, "MAX30101 LED change failed (%d)", (int)err);
                    imu_index_read_failed(&ppg.index);
                    ppg.needs_reconfigure = true;
                    next_reconfigure_us = 0;
                    ppg_publish(false);
                    published_down = true;
                    reply.result = CMD_RESULT_CHIP_ERROR;
                }
            }
            xQueueSend(s_led_reply, &reply, 0);
            continue;
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
            if (!published_down) {
                ppg_publish(false);
                published_down = true;
            }
        }
        if (plan.reconfigure && esp_timer_get_time() >= next_reconfigure_us) {
            next_reconfigure_us = esp_timer_get_time() + PPG_RECONFIGURE_MS * 1000LL;
            err = max30101_start(&s_ppg_bus, &s_ppg_regs, &rev);
            if (err == MAX30101_OK) {
                ppg_read_reconfigured(&ppg);
                s_ppg_generation++;
                ppg_publish(true);
                published_down = false;
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
    afe_publish(PKT_AFE_MAX30101, PKT_AFE_SOURCE_FAKE, true, 0, NULL, 0);
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
 * Health (2026-10-25; timing in ecg_loop.h): every ECG_CHECK_US, whatever INTB
 * does, max30001_check reads INFO and the configuration back; with no sample for
 * ECG_STALL_US (less than the 62.5 ms the FIFO holds) the FIFO is read anyway, so
 * a stuck-high INTB does not overflow it, and with none for ECG_DEAD_US the chip
 * counts as silent. A failed check or a silent chip is started again (reset,
 * configure, SYNCH) every ECG_RESTART_US until that works, with no packet
 * meanwhile; the index then restarts at 0 with bit 5 and 0xD2 shows the new
 * generation. Without this, a chip reset by a brownout stays silent with INTB
 * high and the ECG stops unnoticed. A mapping restart (SYNCH) comes right after a
 * FIFO read, so the samples still in the FIFO are sent first.
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

static uint32_t s_ecg_generation; /* successful configurations since boot */

static void ecg_give_up(const char *what, int err)
{
    ESP_LOGE(TAG, "MAX30001 %s failed (%d): no ECG packets", what, err);
    afe_publish(PKT_AFE_MAX30001, PKT_AFE_SOURCE_CHIP, false, s_ecg_generation, NULL, 0);
    max30001_write(&s_ecg_bus, MAX30001_EN_INT, 0); /* best effort: quiet INTB */
    max30001_esp_stop();
    /* Suspend rather than delete: an INTB ISR already running on the other
     * core may still notify this task, so its handle must stay valid. */
    for (;;) {
        vTaskSuspend(NULL);
    }
}

/*
 * The chip failed its check or went silent: start it again (reset, configure,
 * PLL) and restart the mapping with SYNCH. The index restarts at 0 with bit 5
 * (ecg_read_init restart), as after any SYNCH. 0xD2 gets the new generation.
 */
static bool ecg_start_again(ecg_read_t *ecg)
{
    uint32_t info = 0;
    max30001_err_t err = max30001_start(&s_ecg_bus, &s_ecg_regs, ECG_PLL_TIMEOUT_MS, &info);
    if (err == MAX30001_OK) {
        err = max30001_restart(&s_ecg_bus, &s_ecg_regs, ecg_mapping_start, NULL);
    }
    if (err != MAX30001_OK) {
        ESP_LOGE(TAG, "MAX30001 start failed (%d), retrying", (int)err);
        return false;
    }
    ecg_read_init(ecg, true);
    uint32_t words[MAX30001_CONFIG_WORDS];
    unsigned n = max30001_config_words(&s_ecg_regs, words);
    s_ecg_generation++;
    afe_publish(PKT_AFE_MAX30001, PKT_AFE_SOURCE_CHIP, true, s_ecg_generation, words,
                (uint16_t)n);
    ESP_LOGW(TAG, "MAX30001 started again");
    return true;
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
    max30001_err_t err = MAX30001_ERR_BUS;
    for (int i = 0; i < AFE_START_TRIES && err != MAX30001_OK; i++) {
        if (i > 0) {
            vTaskDelay(pdMS_TO_TICKS(AFE_START_RETRY_MS));
        }
        err = max30001_start(&s_ecg_bus, &s_ecg_regs, ECG_PLL_TIMEOUT_MS, &info);
    }
    ESP_LOGI(TAG, "MAX30001 INFO 0x%06" PRIx32 ", start %d", info, (int)err);
    if (err != MAX30001_OK) {
        ecg_give_up("start", (int)err);
    }
    {
        uint32_t words[MAX30001_CONFIG_WORDS];
        unsigned n = max30001_config_words(&s_ecg_regs, words);
        s_ecg_generation = 1;
        afe_publish(PKT_AFE_MAX30001, PKT_AFE_SOURCE_CHIP, true, s_ecg_generation, words,
                    (uint16_t)n);
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
    ecg_loop_t loop;
    ecg_loop_init(&loop, esp_timer_get_time());
    for (;;) {
        bool woke = ulTaskNotifyTake(pdTRUE, pdMS_TO_TICKS(ECG_POLL_MS)) != 0;
        int64_t now = esp_timer_get_time();
        if (loop.down) {
            if (ecg_loop_start_due(&loop, now) && ecg_start_again(&ecg)) {
                ecg_loop_up(&loop, esp_timer_get_time());
            }
            continue;
        }
        /* A reset chip (brownout) is silent with INTB high: only this sees it. */
        bool dead;
        if (ecg_loop_check_due(&loop, now, &dead)) {
            err = max30001_check(&s_ecg_bus, &s_ecg_regs);
            if (err != MAX30001_OK || dead) {
                ESP_LOGE(TAG, "MAX30001 %s (%d): starting it again",
                         err != MAX30001_OK ? "check failed" : "silent", (int)err);
                imu_index_read_failed(&ecg.index);
                samp_map_error(&s_samp, SAMP_AFE, now);
                afe_publish(PKT_AFE_MAX30001, PKT_AFE_SOURCE_CHIP, false, s_ecg_generation,
                            NULL, 0);
                ecg_loop_down(&loop, now);
                continue;
            }
        }
        bool synch = samp_map_restart_due(&s_samp, esp_timer_get_time());
        if (!ecg_loop_read_due(&loop, now, woke, max30001_esp_intb_low(), synch)) {
            continue; /* no edge, INTB high, samples recent, no SYNCH: wait */
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
            ecg_loop_samples(&loop, (int64_t)t_read);
        }
        if (synch) {
            /* After the read: SYNCH clears the FIFO, so it held nothing unsent. */
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
    afe_publish(PKT_AFE_MAX30001, PKT_AFE_SOURCE_FAKE, true, 0, NULL, 0);
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
 * first start is tried AFE_START_TRIES times before giving up.
 */
#define IMU_FS_NOMINAL_MHZ 100000u
#define IMU_WATERMARK_FRAMES 10u
#define IMU_POLL_MS 20
#define IMU_CHECK_MS 1000
#define IMU_RESTART_MS 100

static const uint8_t IMU_CHANNELS[BMI270_AXES] = {
    PKT_CH_ACC_X, PKT_CH_ACC_Y, PKT_CH_ACC_Z, PKT_CH_GYR_X, PKT_CH_GYR_Y, PKT_CH_GYR_Z};

static bmi270_bus_t s_imu_bus;
static bmi270_regs_t s_imu_regs;

static uint32_t s_imu_generation; /* successful configurations since boot */

static void imu_publish(bool configured)
{
    uint32_t words[BMI270_CONFIG_WORDS];
    unsigned n = bmi270_config_words(&s_imu_regs, words);
    afe_publish(PKT_AFE_BMI270, PKT_AFE_SOURCE_CHIP, configured, s_imu_generation, words,
                (uint16_t)n);
}

static void imu_give_up(int err)
{
    ESP_LOGE(TAG, "BMI270 start failed (%d): no IMU packets", err);
    imu_publish(false);
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
    for (int i = 0; i < AFE_START_TRIES && err != BMI270_OK; i++) {
        if (i > 0) {
            vTaskDelay(pdMS_TO_TICKS(AFE_START_RETRY_MS));
        }
        err = bmi270_start(&s_imu_bus, &s_imu_regs, bmi270_config_file);
    }
    ESP_LOGI(TAG, "BMI270 start %d, SPI %u Hz", (int)err, (unsigned)BOARD_IMU_SPI_HZ);
    if (err != BMI270_OK) {
        imu_give_up((int)err);
    }
    s_imu_generation = 1;
    imu_publish(true);
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
                imu_publish(false);
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
            s_imu_generation++;
            imu_publish(true);
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
                imu_publish(false);
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
    afe_publish(PKT_AFE_BMI270, PKT_AFE_SOURCE_FAKE, true, 0, NULL, 0);
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
    const event_edge_t edge = {.t_us = now, .lost_before = lost_since_queued,
                               .code = PKT_EVENT_T0};
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
 * confirmed events of the session (every code), FS_NOMINAL_MHZ 0, STATUS bit 4
 * off. An edge the queue dropped was never confirmed, so it does not take an
 * ordinal; the next event packet sets bit 1 instead (possible lost event). The
 * t0 button is debounced; a sync pulse (code 3) is the MCU's own edge; a
 * MARK_EVENT (code 2 or 4, V0.2 section 13) carries the time the control task
 * read the command frame, and comes through here so that 0xC1 keeps one
 * producer and one ordinal count.
 */
static void event_task(void *arg)
{
    uint32_t ordinal = 0;
    bool edges_lost = false;
    event_edge_t edge;
    for (;;) {
        xQueueReceive(s_event_queue, &edge, portMAX_DELAY);
        if (edge.lost_before > 0) {
            edges_lost = true; /* kept until an event is sent, even past a bounce */
        }
        if (edge.code == PKT_EVENT_T0) {
            vTaskDelay(pdMS_TO_TICKS(T0_CONFIRM_MS));
            if (gpio_get_level(BOARD_T0_GPIO) != 0) {
                continue; /* released again: bounce, not a press */
            }
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
            .data = {edge.code},
        };
        edges_lost = false;
        enqueue(&p);
        if (edge.code == PKT_EVENT_T0) {
            ESP_LOGI(TAG, "t0 event %" PRIu32 " at %" PRId64 " us", p.first_sample_index,
                     edge.t_us);
        } else if (edge.code != PKT_EVENT_SYNC_PULSE) {
            ESP_LOGI(TAG, "MARK_EVENT code %u, event %" PRIu32 " at %" PRId64 " us",
                     (unsigned)edge.code, p.first_sample_index, edge.t_us);
        }
    }
}

#if BOARD_STIM
/*
 * Sync stimulus (hardware/test_reports/sync_10min_test_plan.md sections 3-4):
 * GPIO6 (J3) goes high at scheduled times STIM_PERIOD_US + U[0, STIM_JITTER_US)
 * apart (stim_plan.c, seeded with the SESSION_ID) and low STIM_WIDTH_US later;
 * the first edge comes STIM_FIRST_US after the start. Each rising edge becomes an
 * event packet with code 3 whose T_ANCHOR_US is esp_timer read right after the
 * pin was set. The schedule follows target times, so callback latency does not
 * add up. Callbacks run in the esp_timer task.
 */
static esp_timer_handle_t s_stim_rise, s_stim_fall;
static stim_plan_t s_stim_plan;
static int64_t s_stim_next_us;

static void stim_fall(void *arg)
{
    (void)arg;
    gpio_set_level(BOARD_STIM_GPIO, 0);
}

static void stim_rise(void *arg)
{
    (void)arg;
    static uint32_t lost_since_queued;
    gpio_set_level(BOARD_STIM_GPIO, 1);
    int64_t now = esp_timer_get_time(); /* right after the edge */
    esp_timer_start_once(s_stim_fall, STIM_WIDTH_US);
    const event_edge_t edge = {.t_us = now, .lost_before = lost_since_queued,
                               .code = PKT_EVENT_SYNC_PULSE};
    if (xQueueSend(s_event_queue, &edge, 0) == pdTRUE) {
        lost_since_queued = 0;
    } else {
        lost_since_queued++;
        s_events_lost++;
    }
    s_stim_next_us += stim_next_interval_us(&s_stim_plan);
    int64_t wait = s_stim_next_us - esp_timer_get_time();
    esp_timer_start_once(s_stim_rise, wait > 0 ? (uint64_t)wait : 1u);
}

static void stim_start(void)
{
    const gpio_config_t out = {
        .pin_bit_mask = 1ULL << BOARD_STIM_GPIO,
        .mode = GPIO_MODE_OUTPUT,
    };
    ESP_ERROR_CHECK(gpio_set_level(BOARD_STIM_GPIO, 0));
    ESP_ERROR_CHECK(gpio_config(&out));
    stim_plan_init(&s_stim_plan, s_session_id);
    const esp_timer_create_args_t rise = {.callback = stim_rise, .name = "stim_rise"};
    const esp_timer_create_args_t fall = {.callback = stim_fall, .name = "stim_fall"};
    ESP_ERROR_CHECK(esp_timer_create(&rise, &s_stim_rise));
    ESP_ERROR_CHECK(esp_timer_create(&fall, &s_stim_fall));
    s_stim_next_us = esp_timer_get_time() + STIM_FIRST_US;
    ESP_ERROR_CHECK(esp_timer_start_once(s_stim_rise, STIM_FIRST_US));
    ESP_LOGW(TAG, "sync stimulus on GPIO%d: %u us + U[0, %u) us, %u us wide, seed "
                  "SESSION_ID", BOARD_STIM_GPIO, (unsigned)STIM_PERIOD_US,
             (unsigned)STIM_JITTER_US, (unsigned)STIM_WIDTH_US);
}
#endif /* BOARD_STIM */

/*
 * Control task (V0.2 sections 12-13): the only producer of 0xD2 and 0xD3. It
 * reads commands from the USB Serial/JTAG port continuously (CTL_RX_MS reads),
 * drops a partial frame idle for CTL_PARTIAL_US, and answers each frame
 * (cmd_exec.c decides). An LED change is handed to the PPG reader and answered
 * when its reply with the same token comes, without blocking this loop; a retry
 * of that request meanwhile is ignored, its CMD_SEQ with other bytes gets
 * REQUEST_REUSED, another LED request gets BUSY. A request
 * the PPG reader has not taken after LED_TAKE_US is withdrawn (BUSY: not done);
 * one it took is waited for, never given a made-up result. A MARK_EVENT is
 * queued for the event task with the time its frame was read (rx_us), then
 * answered; a full event queue answers BUSY (not done, no event). Each AFE's 0xD2
 * goes out on every state transition and every AFE_CONFIG_PERIOD_US.
 */
#define CTL_RX_MS 10
#define CTL_PARTIAL_US 100000LL
#define AFE_CONFIG_PERIOD_US 10000000LL
#define LED_TAKE_US 2000000LL

typedef struct {
    cmd_exec_t exec;
    uint32_t ack_ordinal;
    bool inflight; /* an LED request handed to the PPG reader */
    cmd_frame_t inflight_frame;
    uint32_t inflight_ticket; /* its arrival order (cmd_exec.h) */
    uint32_t token;
    int64_t inflight_since_us;
    /* esp_timer right after the USB read that returned the bytes being parsed:
     * the time a MARK_EVENT was received (V0.2 section 13). */
    int64_t rx_us;
} ctl_t;

static bool same_frame(const cmd_frame_t *a, const cmd_frame_t *b)
{
    return a->id == b->id && a->seq == b->seq && a->len == b->len
           && memcmp(a->params, b->params, a->len) == 0;
}

static void ctl_ack(ctl_t *c, const cmd_frame_t *f, uint8_t result, uint32_t generation)
{
    int64_t now = esp_timer_get_time();
    pkt_t p = {
        .channel_id = PKT_CH_COMMAND_ACK,
        .session_id = s_session_id,
        .first_sample_index = c->ack_ordinal++,
        .t_anchor_us = (uint64_t)now,
        .t_first_us = (uint64_t)now,
        .fs_nominal_mhz = 0,
        .sample_count = PKT_COMMAND_ACK_COUNT,
        .status = 0,
    };
    pkt_command_ack_data(f->id, f->seq, result, generation, p.data);
    enqueue(&p);
}

static void ctl_on_frame(void *ctx, const cmd_frame_t *f)
{
    ctl_t *c = ctx;
    if (c->inflight && same_frame(f, &c->inflight_frame)) {
        return; /* a retry of the request being applied: answered when it is done */
    }
    if (c->inflight && f->seq == c->inflight_frame.seq) {
        /* The CMD_SEQ of the request being applied with other bytes: refused as a
         * reused CMD_SEQ (result 6), the request in flight is not touched. */
        ctl_ack(c, f, CMD_RESULT_REQUEST_REUSED, 0);
        return;
    }
    cmd_action_t a = cmd_exec_decide(&c->exec, f, s_session_id,
                                     c->inflight ? CMD_PPG_BUSY : s_ppg_cmd_state);
    if (a.apply_led) {
        const led_request_t req = {.token = ++c->token, .green = a.green, .red = a.red,
                                   .ir = a.ir};
        if (xQueueSend(s_led_request, &req, 0) == pdTRUE) {
            c->inflight = true;
            c->inflight_frame = *f;
            c->inflight_ticket = a.ticket;
            c->inflight_since_us = esp_timer_get_time();
            return;
        }
        a.result = CMD_RESULT_BUSY;
        a.generation = 0;
    }
    if (a.mark_event) {
        /* Through the queue of the t0 button, so the event task stays the only
         * producer of 0xC1 and counts this event with the others. */
        const event_edge_t edge = {.t_us = c->rx_us, .lost_before = 0,
                                   .code = a.event_code};
        a.result = xQueueSend(s_event_queue, &edge, 0) == pdTRUE ? CMD_RESULT_OK
                                                                  : CMD_RESULT_BUSY;
        a.generation = 0;
    }
    if (!a.repeat) {
        cmd_exec_done(&c->exec, f, a.result, a.generation, a.ticket);
    }
    ctl_ack(c, f, a.result, a.generation);
}

/* The PPG reader's answer to the request in flight, or its withdrawal. */
static void ctl_led_progress(ctl_t *c, int64_t now)
{
    led_reply_t reply;
    while (c->inflight && xQueueReceive(s_led_reply, &reply, 0) == pdTRUE) {
        if (reply.token != c->token) {
            continue; /* not the request in flight */
        }
        c->inflight = false;
        cmd_exec_done(&c->exec, &c->inflight_frame, reply.result, reply.generation,
                      c->inflight_ticket);
        ctl_ack(c, &c->inflight_frame, reply.result, reply.generation);
    }
    led_request_t untaken;
    if (c->inflight && now - c->inflight_since_us > LED_TAKE_US
        && xQueueReceive(s_led_request, &untaken, 0) == pdTRUE) {
        c->inflight = false; /* never taken: not done */
        ctl_ack(c, &c->inflight_frame, CMD_RESULT_BUSY, 0);
    }
}

typedef struct {
    uint32_t ordinal;
    afe_order_t order;
} ctl_config_t;

/* One 0xD2 of state `s`, if afe_order.h allows it, with bit 1 as it says. */
static void ctl_send_config(const afe_state_t *s, ctl_config_t *cc, bool repeat)
{
    bool bit1;
    if (!afe_order_decide(&cc->order, s->afe, s->order, repeat, &bit1)) {
        return;
    }
    pkt_t p = {
        .channel_id = PKT_CH_AFE_CONFIG,
        .session_id = s_session_id,
        .first_sample_index = cc->ordinal++,
        .t_anchor_us = (uint64_t)s->since_us,
        .t_first_us = (uint64_t)s->since_us,
        .fs_nominal_mhz = 0,
        .status = bit1 ? PKT_STATUS_MCU_BUFFER_OVERFLOW : 0,
    };
    p.sample_count = pkt_afe_config_data(s->afe, s->source, s->configured, s->generation,
                                         s->words, s->n, p.data);
    afe_order_sent(&cc->order, s->afe, s->order, enqueue(&p));
}

/* The latest state of each known AFE: the periodic `repeat`, or else only for an
 * AFE with a lost transition that no state from the queue carried. */
static void ctl_send_latest(ctl_config_t *cc, bool repeat)
{
    for (uint8_t afe = 1; afe <= 3u; afe++) {
        static afe_state_t s;
        bool known;
        if (!repeat && !afe_order_pending(&cc->order, afe)) {
            continue;
        }
        taskENTER_CRITICAL(&s_afe_lock);
        s = s_afe_latest[afe - 1u];
        known = s_afe_known[afe - 1u];
        taskEXIT_CRITICAL(&s_afe_lock);
        if (known) {
            ctl_send_config(&s, cc, repeat);
        }
    }
}

static void ctl_task(void *arg)
{
    (void)arg;
    static ctl_t c;
    static ctl_config_t cc;
    afe_order_init(&cc.order);
    cmd_exec_init(&c.exec);
    cmd_parser_t parser;
    cmd_parser_init(&parser);
    uint8_t rx[64];
    int64_t last_rx = 0;
    int64_t next_all = esp_timer_get_time() + AFE_CONFIG_PERIOD_US;
    for (;;) {
        int n = usb_serial_jtag_read_bytes(rx, sizeof(rx), pdMS_TO_TICKS(CTL_RX_MS));
        int64_t now = esp_timer_get_time();
        if (n > 0) {
            last_rx = now;
            c.rx_us = now;
            cmd_parser_feed(&parser, rx, (size_t)n, ctl_on_frame, &c);
        } else if (parser.n > 0 && now - last_rx > CTL_PARTIAL_US) {
            parser.n = 0; /* a frame that never finished */
            parser.dropped++;
        }
        ctl_led_progress(&c, now);
        /* Lost transitions first, so a newer state from the queue carries bit 1. */
        uint64_t lost[3];
        taskENTER_CRITICAL(&s_afe_lock);
        memcpy(lost, s_afe_lost, sizeof(lost));
        memset(s_afe_lost, 0, sizeof(s_afe_lost));
        taskEXIT_CRITICAL(&s_afe_lock);
        for (uint8_t afe = 1; afe <= 3u; afe++) {
            afe_order_lost(&cc.order, afe, lost[afe - 1u]);
        }
        static afe_state_t s;
        while (xQueueReceive(s_afe_queue, &s, 0) == pdTRUE) {
            ctl_send_config(&s, &cc, false);
        }
        ctl_send_latest(&cc, false);
        if (now >= next_all) {
            next_all = now + AFE_CONFIG_PERIOD_US;
            ctl_send_latest(&cc, true);
        }
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
    s_event_queue = xQueueCreate(EVENT_QUEUE_LEN, sizeof(event_edge_t));
    s_led_request = xQueueCreate(1, sizeof(led_request_t));
    s_led_reply = xQueueCreate(2, sizeof(led_reply_t));
    s_afe_queue = xQueueCreate(AFE_QUEUE_LEN, sizeof(afe_state_t));
    if (s_tx_queue == NULL || s_event_queue == NULL || s_led_request == NULL
        || s_led_reply == NULL || s_afe_queue == NULL) {
        ESP_LOGE(TAG, "cannot create queues");
        abort();
    }
    if (xTaskCreate(tx_task, "pkt_tx", 4096, NULL, 5, NULL) != pdPASS
        || xTaskCreate(device_info_task, "dev_info", 3072, NULL, 4, NULL) != pdPASS
        || xTaskCreate(event_task, "t0_event", 3072, NULL, 6, NULL) != pdPASS
        || xTaskCreate(ctl_task, "ctl", 4096, NULL, 5, NULL) != pdPASS) {
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
#if BOARD_STIM
    stim_start();
#endif

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
