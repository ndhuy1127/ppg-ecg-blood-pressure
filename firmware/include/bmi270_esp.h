/*
 * ESP-IDF side of the BMI270 driver (bmi270.h): SPI bus 2 of the V1-module
 * (board_v1_module.h, GPIO10 CS, 11 MOSI, 12 SCK, 13 MISO; SPI3_HOST with DMA, so
 * a 170-frame FIFO read is one transaction) at `clock_hz`, mode 0, and INT1
 * (push-pull, active high, GPIO14) on a rising edge notifying the reader task.
 * Not run on a chip yet.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "bmi270.h"
#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

/* Needs the GPIO ISR service installed. The INT1 interrupt starts disabled
 * (its type stays GPIO_INTR_DISABLE until bmi270_esp_int_enable). */
esp_err_t bmi270_esp_init(bmi270_bus_t *bus, uint32_t clock_hz, TaskHandle_t reader);

/* INT1 interrupt on only while the chip is configured: after a reset INT1 is
 * not driven (INT1_IO_CTRL output_en = 0). */
void bmi270_esp_int_enable(bool on);

/* Stop the INT1 interrupt before the reader task stops for good. */
void bmi270_esp_stop(void);
