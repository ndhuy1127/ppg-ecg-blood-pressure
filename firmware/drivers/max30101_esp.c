/*
 * ESP-IDF side of the MAX30101 driver; see max30101_esp.h.
 */
#include "max30101_esp.h"

#include <stddef.h>

#include "board_v1_module.h"
#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "esp_attr.h"

#define PPG_I2C_PORT I2C_NUM_0
#define PPG_I2C_TIMEOUT_MS 20
#define PPG_I2C_MAX_WRITE 8 /* register + the longest block written (4 LED bytes) */

static i2c_master_bus_handle_t s_bus;
static i2c_master_dev_handle_t s_dev;
static TaskHandle_t volatile s_reader; /* read by the ISR */

static int bus_write(void *ctx, uint8_t reg, const uint8_t *data, size_t n)
{
    (void)ctx;
    uint8_t buf[PPG_I2C_MAX_WRITE];
    if (n + 1 > sizeof(buf)) {
        return -1;
    }
    buf[0] = reg;
    for (size_t i = 0; i < n; i++) {
        buf[i + 1] = data[i];
    }
    return i2c_master_transmit(s_dev, buf, n + 1, PPG_I2C_TIMEOUT_MS) == ESP_OK ? 0 : -1;
}

static int bus_read(void *ctx, uint8_t reg, uint8_t *data, size_t n)
{
    (void)ctx;
    /* Register address, repeated start, then n bytes (datasheet p. 17). */
    return i2c_master_transmit_receive(s_dev, &reg, 1, data, n, PPG_I2C_TIMEOUT_MS) == ESP_OK
               ? 0
               : -1;
}

static void delay_ms(void *ctx, uint32_t ms)
{
    (void)ctx;
    vTaskDelay(pdMS_TO_TICKS(ms) + 1); /* at least `ms`, whatever the tick */
}

static void IRAM_ATTR int_isr(void *arg)
{
    (void)arg;
    TaskHandle_t reader = s_reader;
    if (reader == NULL) {
        return;
    }
    BaseType_t woken = pdFALSE;
    vTaskNotifyGiveFromISR(reader, &woken);
    portYIELD_FROM_ISR(woken);
}

void max30101_esp_stop(void)
{
    gpio_intr_disable(BOARD_PPG_INT_GPIO);
    gpio_isr_handler_remove(BOARD_PPG_INT_GPIO);
    s_reader = NULL;
}

esp_err_t max30101_esp_init(max30101_bus_t *bus, uint32_t clock_hz, TaskHandle_t reader)
{
    s_reader = reader;
    const i2c_master_bus_config_t bus_cfg = {
        .i2c_port = PPG_I2C_PORT,
        .sda_io_num = BOARD_PPG_SDA_GPIO,
        .scl_io_num = BOARD_PPG_SCL_GPIO,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = false, /* 2.2 kOhm on the SparkFun board */
    };
    esp_err_t err = i2c_new_master_bus(&bus_cfg, &s_bus);
    const i2c_device_config_t dev_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = MAX30101_I2C_ADDR,
        .scl_speed_hz = clock_hz,
    };
    if (err == ESP_OK) {
        err = i2c_master_bus_add_device(s_bus, &dev_cfg, &s_dev);
    }
    /* INT is open-drain, active low, pulled up to 3.3 V on the SparkFun board. */
    const gpio_config_t intr = {
        .pin_bit_mask = 1ULL << BOARD_PPG_INT_GPIO,
        .mode = GPIO_MODE_INPUT,
        .intr_type = GPIO_INTR_NEGEDGE,
    };
    if (err == ESP_OK) {
        err = gpio_config(&intr);
    }
    if (err == ESP_OK) {
        err = gpio_isr_handler_add(BOARD_PPG_INT_GPIO, int_isr, NULL);
    }
    *bus = (max30101_bus_t){.ctx = NULL, .write = bus_write, .read = bus_read,
                            .delay_ms = delay_ms};
    return err;
}
