/*
 * ESP-IDF side of the BMI270 driver; see bmi270_esp.h.
 */
#include "bmi270_esp.h"

#include <stddef.h>
#include <string.h>

#include "board_v1_module.h"
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_attr.h"
#include "esp_heap_caps.h"
#include "esp_rom_sys.h"

#define IMU_SPI_HOST SPI3_HOST /* SPI2_HOST is the MAX30001's */
#define IMU_XFER_MAX 2048      /* > 2 + 170 * 12 = 2042 */

static spi_device_handle_t s_dev;
static uint8_t *s_dma_tx, *s_dma_rx;
static TaskHandle_t volatile s_reader; /* read by the ISR */

static int xfer(void *ctx, const uint8_t *tx, uint8_t *rx, size_t n)
{
    (void)ctx;
    if (n > IMU_XFER_MAX) {
        return -1;
    }
    memcpy(s_dma_tx, tx, n); /* DMA-capable buffers; the core's may not be */
    spi_transaction_t t = {.length = n * 8u, .tx_buffer = s_dma_tx, .rx_buffer = s_dma_rx};
    if (spi_device_transmit(s_dev, &t) != ESP_OK) {
        return -1;
    }
    memcpy(rx, s_dma_rx, n);
    return 0;
}

static void delay_us(void *ctx, uint32_t us)
{
    (void)ctx;
    if (us >= 2000u) {
        vTaskDelay(pdMS_TO_TICKS((us + 999u) / 1000u) + 1); /* at least `us` */
    } else {
        esp_rom_delay_us(us);
    }
}

static void IRAM_ATTR int1_isr(void *arg)
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

void bmi270_esp_int_enable(bool on)
{
    /* The type, not only the enable bit: gpio_isr_handler_add enables the
     * interrupt of its pin whatever was set before. */
    if (on) {
        gpio_set_intr_type(BOARD_BMI_INT_GPIO, GPIO_INTR_POSEDGE);
        gpio_intr_enable(BOARD_BMI_INT_GPIO);
    } else {
        gpio_intr_disable(BOARD_BMI_INT_GPIO);
        gpio_set_intr_type(BOARD_BMI_INT_GPIO, GPIO_INTR_DISABLE);
    }
}

void bmi270_esp_stop(void)
{
    gpio_intr_disable(BOARD_BMI_INT_GPIO);
    gpio_isr_handler_remove(BOARD_BMI_INT_GPIO);
    s_reader = NULL;
}

esp_err_t bmi270_esp_init(bmi270_bus_t *bus, uint32_t clock_hz, TaskHandle_t reader)
{
    s_reader = reader;
    s_dma_tx = heap_caps_malloc(IMU_XFER_MAX, MALLOC_CAP_DMA);
    s_dma_rx = heap_caps_malloc(IMU_XFER_MAX, MALLOC_CAP_DMA);
    esp_err_t err = s_dma_tx != NULL && s_dma_rx != NULL ? ESP_OK : ESP_ERR_NO_MEM;
    const spi_bus_config_t spi = {
        .mosi_io_num = BOARD_BMI_MOSI_GPIO,
        .miso_io_num = BOARD_BMI_MISO_GPIO,
        .sclk_io_num = BOARD_BMI_SCK_GPIO,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = IMU_XFER_MAX,
    };
    if (err == ESP_OK) {
        err = spi_bus_initialize(IMU_SPI_HOST, &spi, SPI_DMA_CH_AUTO);
    }
    /* CSB is the hardware CS, high between transactions: every transaction
     * ends with the rising edge that selects SPI (datasheet section 6.3). */
    const spi_device_interface_config_t dev = {
        .mode = 0, /* CPOL 0, CPHA 0; the chip also accepts mode 3 (section 6.4) */
        .clock_speed_hz = (int)clock_hz,
        .spics_io_num = BOARD_BMI_CS_GPIO,
        .queue_size = 1,
    };
    if (err == ESP_OK) {
        err = spi_bus_add_device(IMU_SPI_HOST, &dev, &s_dev);
    }
    /* INT1 is push-pull, active high once configured (INT1_IO_CTRL 0x0A) but not
     * driven after a reset: a pull-down keeps it low meanwhile. */
    const gpio_config_t int1 = {
        .pin_bit_mask = 1ULL << BOARD_BMI_INT_GPIO,
        .mode = GPIO_MODE_INPUT,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type = GPIO_INTR_DISABLE, /* POSEDGE once configured */
    };
    if (err == ESP_OK) {
        err = gpio_config(&int1);
    }
    if (err == ESP_OK) {
        err = gpio_isr_handler_add(BOARD_BMI_INT_GPIO, int1_isr, NULL);
    }
    *bus = (bmi270_bus_t){.ctx = NULL, .xfer = xfer, .delay_us = delay_us};
    return err;
}
