#include "samp_edges.h"

#include "esp_attr.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define SLOT_EMPTY UINT32_MAX

typedef struct {
    uint32_t e;
    int64_t raw;
} slot_t;

/* Internal RAM: the capture ISR may run while the flash cache is off
 * (CONFIG_MCPWM_ISR_CACHE_SAFE). */
static DRAM_ATTR slot_t s_ring[SAMP_RING_LEN];
static DRAM_ATTR uint32_t s_next_e;
static DRAM_ATTR portMUX_TYPE s_lock = portMUX_INITIALIZER_UNLOCKED;
static samp_convert_fn s_convert;

void samp_edges_set_converter(samp_convert_fn convert)
{
    s_convert = convert;
}

void samp_edges_clear(void)
{
    portENTER_CRITICAL(&s_lock);
    for (uint32_t i = 0; i < SAMP_RING_LEN; i++) {
        s_ring[i].e = SLOT_EMPTY;
    }
    s_next_e = 0;
    portEXIT_CRITICAL(&s_lock);
}

void IRAM_ATTR samp_edges_push(int64_t raw)
{
    portENTER_CRITICAL_SAFE(&s_lock);
    uint32_t e = s_next_e++;
    s_ring[e % SAMP_RING_LEN] = (slot_t){.e = e, .raw = raw};
    portEXIT_CRITICAL_SAFE(&s_lock);
}

static bool slot_raw(uint32_t e, int64_t *raw)
{
    portENTER_CRITICAL(&s_lock);
    slot_t slot = s_ring[e % SAMP_RING_LEN];
    portEXIT_CRITICAL(&s_lock);
    *raw = slot.raw;
    return slot.e == e;
}

bool samp_edges_lookup(void *ctx, uint32_t e, int64_t *t_us)
{
    (void)ctx;
    int64_t raw;
    if (!slot_raw(e, &raw)) {
        return false;
    }
    if (s_convert == NULL) {
        *t_us = raw;
        return true;
    }
    return s_convert(raw, t_us);
}

bool samp_edges_wait(uint32_t e, int64_t deadline_us)
{
    /* Waits only; whether the edge is in time is samp_map_packet's check. */
    int64_t raw;
    while (!slot_raw(e, &raw)) {
        if (esp_timer_get_time() >= deadline_us) {
            return false;
        }
        vTaskDelay(1);
    }
    return true;
}
