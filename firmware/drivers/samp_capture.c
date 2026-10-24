#include "samp_capture.h"

#include <inttypes.h>

#include "driver/mcpwm_cap.h"
#include "esp_attr.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "samp_edges.h"

#define PAIR_PERIOD_MS 100
#define PAIR_MAX_SPREAD_US 2
#define PAIR_MAX_AGE_US 1000000LL
#define SOFT_CATCH_WAIT_TICKS 2

static const char *TAG = "samp_cap";

typedef struct {
    uint32_t ticks;
    int64_t us;
} pair_t;

static mcpwm_cap_channel_handle_t s_soft;
static uint32_t s_resolution_hz;
static DRAM_ATTR volatile uint32_t s_soft_ticks;
static DRAM_ATTR volatile bool s_soft_done;
static portMUX_TYPE s_lock = portMUX_INITIALIZER_UNLOCKED;
static bool s_have_pair;
static pair_t s_pair;
static samp_capture_stats_t s_stats;

static bool IRAM_ATTR on_samp(mcpwm_cap_channel_handle_t chan,
                              const mcpwm_capture_event_data_t *edata, void *user)
{
    samp_edges_push(edata->cap_value);
    return false;
}

static bool IRAM_ATTR on_soft(mcpwm_cap_channel_handle_t chan,
                              const mcpwm_capture_event_data_t *edata, void *user)
{
    s_soft_ticks = edata->cap_value;
    s_soft_done = true;
    return false;
}

/* esp_timer us of a capture value near the pair; the signed difference keeps
 * a counter wrap (every 53.7 s at 80 MHz) harmless within +-26 s. */
static int64_t ticks_to_us(const pair_t *p, uint32_t ticks)
{
    int64_t d = (int32_t)(ticks - p->ticks);
    int64_t half = s_resolution_hz / 2;
    return p->us + (d * 1000000 + (d >= 0 ? half : -half)) / (int64_t)s_resolution_hz;
}

bool samp_capture_to_us(int64_t raw, int64_t *t_us)
{
    portENTER_CRITICAL(&s_lock);
    int64_t now = esp_timer_get_time(); /* inside the lock: no preemption between */
    bool fresh = s_have_pair && now - s_pair.us < PAIR_MAX_AGE_US;
    pair_t p = s_pair;
    if (!fresh) {
        s_stats.stale++;
    }
    portEXIT_CRITICAL(&s_lock);
    if (!fresh) {
        return false; /* the edge counts as missing: the mapping goes to error */
    }
    *t_us = ticks_to_us(&p, (uint32_t)raw);
    return true;
}

samp_capture_stats_t samp_capture_stats(void)
{
    portENTER_CRITICAL(&s_lock);
    samp_capture_stats_t s = s_stats;
    portEXIT_CRITICAL(&s_lock);
    return s;
}

/* Bracketed pairs: esp_timer, software catch, esp_timer, with interrupts off on
 * this core so that nothing runs between the three. */
static void pair_task(void *arg)
{
    static portMUX_TYPE bracket = portMUX_INITIALIZER_UNLOCKED;
    TickType_t wake = xTaskGetTickCount();
    for (;;) {
        s_soft_done = false;
        portENTER_CRITICAL(&bracket);
        int64_t t0 = esp_timer_get_time();
        esp_err_t err = mcpwm_capture_channel_trigger_soft_catch(s_soft);
        int64_t t1 = esp_timer_get_time();
        portEXIT_CRITICAL(&bracket);
        for (int i = 0; i < SOFT_CATCH_WAIT_TICKS && !s_soft_done; i++) {
            vTaskDelay(1);
        }
        bool ok = err == ESP_OK && s_soft_done && t1 - t0 < PAIR_MAX_SPREAD_US;
        pair_t now = {.ticks = s_soft_ticks, .us = (t0 + t1) / 2};
        portENTER_CRITICAL(&s_lock);
        if (!ok) {
            s_stats.pairs_rejected++;
        } else {
            if (s_have_pair) {
                /* Transfer error: the new pair against the old one's prediction. */
                int64_t error_ns = (ticks_to_us(&s_pair, now.ticks) - now.us) * 1000;
                error_ns = error_ns < 0 ? -error_ns : error_ns;
                if (error_ns > s_stats.max_error_ns) {
                    s_stats.max_error_ns = error_ns;
                }
            }
            s_pair = now;
            s_have_pair = true;
            s_stats.pairs++;
        }
        portEXIT_CRITICAL(&s_lock);
        vTaskDelayUntil(&wake, pdMS_TO_TICKS(PAIR_PERIOD_MS));
    }
}

esp_err_t samp_capture_start(int gpio, bool rising_edge)
{
    mcpwm_cap_timer_handle_t timer;
    const mcpwm_capture_timer_config_t timer_cfg = {
        .group_id = 0,
        .clk_src = MCPWM_CAPTURE_CLK_SRC_DEFAULT,
    };
    ESP_RETURN_ON_ERROR(mcpwm_new_capture_timer(&timer_cfg, &timer), TAG, "timer");
    ESP_RETURN_ON_ERROR(mcpwm_capture_timer_get_resolution(timer, &s_resolution_hz), TAG,
                        "resolution");

    /* INT2B is driven CMOS through the TXB0108: no pull (section 7.1). */
    mcpwm_cap_channel_handle_t samp;
    const mcpwm_capture_channel_config_t samp_cfg = {
        .gpio_num = gpio,
        .prescale = 1,
        .flags = {.pos_edge = rising_edge, .neg_edge = !rising_edge},
    };
    ESP_RETURN_ON_ERROR(mcpwm_new_capture_channel(timer, &samp_cfg, &samp), TAG, "samp");
    const mcpwm_capture_channel_config_t soft_cfg = {
        .gpio_num = -1,
        .prescale = 1,
        .flags = {.pos_edge = 1},
    };
    ESP_RETURN_ON_ERROR(mcpwm_new_capture_channel(timer, &soft_cfg, &s_soft), TAG, "soft");

    const mcpwm_capture_event_callbacks_t samp_cbs = {.on_cap = on_samp};
    const mcpwm_capture_event_callbacks_t soft_cbs = {.on_cap = on_soft};
    ESP_RETURN_ON_ERROR(mcpwm_capture_channel_register_event_callbacks(samp, &samp_cbs, NULL),
                        TAG, "samp callback");
    ESP_RETURN_ON_ERROR(mcpwm_capture_channel_register_event_callbacks(s_soft, &soft_cbs, NULL),
                        TAG, "soft callback");
    ESP_RETURN_ON_ERROR(mcpwm_capture_channel_enable(samp), TAG, "enable samp");
    ESP_RETURN_ON_ERROR(mcpwm_capture_channel_enable(s_soft), TAG, "enable soft");
    ESP_RETURN_ON_ERROR(mcpwm_capture_timer_enable(timer), TAG, "enable timer");
    ESP_RETURN_ON_ERROR(mcpwm_capture_timer_start(timer), TAG, "start timer");

    samp_edges_set_converter(samp_capture_to_us);
    if (xTaskCreate(pair_task, "samp_pairs", 3072, NULL, 7, NULL) != pdPASS) {
        return ESP_ERR_NO_MEM;
    }
    ESP_LOGI(TAG, "SAMP capture on GPIO%d, %s edge, %" PRIu32 " Hz", gpio,
             rising_edge ? "rising" : "falling", s_resolution_hz);
    return ESP_OK;
}
