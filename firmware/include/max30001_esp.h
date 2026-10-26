/*
 * ESP-IDF side of the MAX30001 driver (max30001.h): SPI bus 1 of the V1-module
 * (board_v1_module.h) on SPI2_HOST, mode 0, with CSB driven as a GPIO so that a
 * burst FIFO read stays in one CS frame however many words it takes; INTB on a
 * falling edge notifies the reader task. Not run on a chip yet.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "max30001.h"

/* Needs the GPIO ISR service installed. `reader` gets xTaskNotifyGive on each
 * INTB falling edge (ECG FIFO threshold reached). */
esp_err_t max30001_esp_init(max30001_bus_t *bus, uint32_t clock_hz, TaskHandle_t reader);

/* INTB is low now (EINT asserted), for a reader that missed the edge. */
bool max30001_esp_intb_low(void);

/* Stop the INTB interrupt before the reader task goes away. */
void max30001_esp_stop(void);
