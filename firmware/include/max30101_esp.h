/*
 * ESP-IDF side of the MAX30101 driver (max30101.h): I2C bus 1 of the V1-module
 * (board_v1_module.h, GPIO8 SDA, GPIO9 SCL; pull-ups on the SparkFun board) at
 * `clock_hz`, and the open-drain INT (4.7 kOhm pull-up on the board) on a
 * falling edge notifying the reader task. Not run on a chip yet.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "max30101.h"

/* Needs the GPIO ISR service installed. */
esp_err_t max30101_esp_init(max30101_bus_t *bus, uint32_t clock_hz, TaskHandle_t reader);

/* Stop the INT interrupt before the reader task stops for good. */
void max30101_esp_stop(void);
