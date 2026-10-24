/*
 * Firmware skeleton for the V1-module: fake ECG/PPG sources, t0 event packets
 * and device info packets in Packet Schema V0.2
 * (configs/hardware/Packet_Schema_V0.2.md), sent as binary on the native USB
 * Serial/JTAG port. Text logs go to UART0 only, so the packet port carries
 * packets alone (schema section 13). No AFE driver yet: every ECG/PPG value
 * comes from fake_afe.
 */
#include <inttypes.h>
#include <stdlib.h>

#include "board_v1_module.h"
#include "bootloader_random.h"
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
#include "imu_plan.h"
#include "packet_wire.h"

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
static const fake_afe_config_t ECG_FAKE = {
    .name = "fake_ecg",
    .n_slots = 1,
    .channel_ids = {PKT_CH_ECG},
    .fs_nominal_mhz = 512000,
    .period_us = 1953,
    .batch = 16,
    .depth = 32,
};
static const fake_afe_config_t PPG_FAKE = {
    .name = "fake_ppg",
    .n_slots = 3,
    .channel_ids = {PKT_CH_PPG_SLOT1, PKT_CH_PPG_SLOT2, PKT_CH_PPG_SLOT3},
    .fs_nominal_mhz = 200000,
    .period_us = 5000,
    .batch = 8,
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

enum {
    CH_ECG, CH_PPG1, CH_PPG2, CH_PPG3, CH_PPG4, CH_EVENT, CH_DEVICE_INFO,
    CH_ACC_X, CH_ACC_Y, CH_ACC_Z, CH_GYR_X, CH_GYR_Y, CH_GYR_Z, CH_COUNT
};
static const uint8_t CHANNEL_IDS[CH_COUNT] = {
    PKT_CH_ECG, PKT_CH_PPG_SLOT1, PKT_CH_PPG_SLOT2, PKT_CH_PPG_SLOT3,
    PKT_CH_PPG_SLOT4, PKT_CH_EVENT, PKT_CH_DEVICE_INFO, PKT_CH_ACC_X,
    PKT_CH_ACC_Y, PKT_CH_ACC_Z, PKT_CH_GYR_X, PKT_CH_GYR_Y, PKT_CH_GYR_Z,
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

static void afe_reader_task(void *arg)
{
    const fake_afe_config_t *cfg = arg;
    fake_afe_t *afe;
    ESP_ERROR_CHECK(fake_afe_start(cfg, xTaskGetCurrentTaskHandle(), &afe));
    for (;;) {
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
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

    if (xTaskCreate(afe_reader_task, "ecg_reader", 4096, (void *)&ECG_FAKE, 6, NULL) != pdPASS
        || xTaskCreate(afe_reader_task, "ppg_reader", 4096, (void *)&PPG_FAKE, 6, NULL) != pdPASS
        || xTaskCreate(imu_reader_task, "imu_reader", 4096, NULL, 6, NULL) != pdPASS) {
        ESP_LOGE(TAG, "cannot create reader tasks");
        abort();
    }
    ESP_LOGI(TAG, "streaming FAKE data: ECG 0xE1 %u us x %u, PPG 0xF1-0xF3 %u us x %u, "
                  "IMU 0xA1-0xA6 %u us x %u%s, t0 on GPIO%d",
             (unsigned)ECG_FAKE.period_us, (unsigned)ECG_FAKE.batch, (unsigned)PPG_FAKE.period_us,
             (unsigned)PPG_FAKE.batch, (unsigned)IMU_FAKE.period_us, (unsigned)IMU_FAKE.batch,
             FAKE_IMU_STALLS ? " with read stalls" : "", BOARD_T0_GPIO);

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
