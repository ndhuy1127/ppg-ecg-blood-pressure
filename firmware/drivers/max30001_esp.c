/*
 * ESP-IDF side of the MAX30001 driver; see max30001_esp.h.
 */
#include "max30001_esp.h"

#include <stdbool.h>
#include <stddef.h>

#include "board_v1_module.h"
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_attr.h"

#define ECG_SPI_HOST SPI2_HOST

static spi_device_handle_t s_dev;
static TaskHandle_t volatile s_reader; /* read by the ISR */

static void cs(void *ctx, bool active)
{
    (void)ctx;
    gpio_set_level(BOARD_ECG_CS_GPIO, active ? 0 : 1); /* CSB is active low */
}

static int xfer(void *ctx, const uint8_t *tx, uint8_t *rx, size_t n)
{
    (void)ctx;
    spi_transaction_t t = {.length = n * 8u, .tx_buffer = tx, .rx_buffer = rx};
    return spi_device_polling_transmit(s_dev, &t) == ESP_OK ? 0 : -1;
}

static void delay_ms(void *ctx, uint32_t ms)
{
    (void)ctx;
    vTaskDelay(pdMS_TO_TICKS(ms) + 1); /* at least `ms`, whatever the tick */
}

static void IRAM_ATTR intb_isr(void *arg)
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

bool max30001_esp_intb_low(void)
{
    return gpio_get_level(BOARD_ECG_INTB_GPIO) == 0;
}

void max30001_esp_stop(void)
{
    gpio_intr_disable(BOARD_ECG_INTB_GPIO);
    gpio_isr_handler_remove(BOARD_ECG_INTB_GPIO);
    s_reader = NULL;
}

esp_err_t max30001_esp_init(max30001_bus_t *bus, uint32_t clock_hz, TaskHandle_t reader)
{
    s_reader = reader;
    /* Output latch high before the pin becomes an output: CSB never pulses low. */
    gpio_set_level(BOARD_ECG_CS_GPIO, 1);
    const gpio_config_t csb = {
        .pin_bit_mask = 1ULL << BOARD_ECG_CS_GPIO,
        .mode = GPIO_MODE_OUTPUT,
    };
    esp_err_t err = gpio_config(&csb);
    if (err == ESP_OK) {
        err = gpio_set_level(BOARD_ECG_CS_GPIO, 1);
    }
    const spi_bus_config_t spi = {
        .mosi_io_num = BOARD_ECG_MOSI_GPIO,
        .miso_io_num = BOARD_ECG_MISO_GPIO,
        .sclk_io_num = BOARD_ECG_SCLK_GPIO,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = 64,
    };
    if (err == ESP_OK) {
        err = spi_bus_initialize(ECG_SPI_HOST, &spi, SPI_DMA_DISABLED);
    }
    const spi_device_interface_config_t dev = {
        .mode = 0, /* CPOL 0, CPHA 0 (datasheet p. 36) */
        .clock_speed_hz = (int)clock_hz,
        .spics_io_num = -1, /* CSB is a GPIO, held by max30001.c */
        .queue_size = 1,
    };
    if (err == ESP_OK) {
        err = spi_bus_add_device(ECG_SPI_HOST, &dev, &s_dev);
    }
    /* INTB is a CMOS output through the TXB0108 (INTB_TYPE 01): no pull. */
    const gpio_config_t intb = {
        .pin_bit_mask = 1ULL << BOARD_ECG_INTB_GPIO,
        .mode = GPIO_MODE_INPUT,
        .intr_type = GPIO_INTR_NEGEDGE,
    };
    if (err == ESP_OK) {
        err = gpio_config(&intb);
    }
    if (err == ESP_OK) {
        err = gpio_isr_handler_add(BOARD_ECG_INTB_GPIO, intb_isr, NULL);
    }
    *bus = (max30001_bus_t){.ctx = NULL, .cs = cs, .xfer = xfer, .delay_ms = delay_ms};
    return err;
}
