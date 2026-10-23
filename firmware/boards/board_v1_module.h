/*
 * GPIO map of the KiCad V1-module base board
 * (configs/hardware/custom_board_proposal.md, section A.7). The skeleton uses
 * only the t0 button and the status LED; the AFE pins are listed for the
 * drivers that will replace fake_afe.
 */
#pragma once

/* t0 button SW1: 10 kOhm pull-up and 100 nF on the board, active low. On a
 * bare DevKitC, a switch from GPIO4 to GND works (internal pull-up is on).
 * Define BOARD_T0_GPIO at compile time to use another pin. */
#ifndef BOARD_T0_GPIO
#define BOARD_T0_GPIO 4
#endif
#define BOARD_LED_STAT_GPIO 5

/* MAX30001 on SPI bus 1. */
#define BOARD_ECG_CS_GPIO 7
#define BOARD_ECG_SCLK_GPIO 15
#define BOARD_ECG_MOSI_GPIO 16
#define BOARD_ECG_MISO_GPIO 17
#define BOARD_ECG_INTB_GPIO 21
#define BOARD_ECG_INT2B_GPIO 47

/* MAX30101 on I2C bus 1. */
#define BOARD_PPG_SDA_GPIO 8
#define BOARD_PPG_SCL_GPIO 9
#define BOARD_PPG_INT_GPIO 18

/* BMI270 on SPI bus 2. */
#define BOARD_BMI_CS_GPIO 10
#define BOARD_BMI_MOSI_GPIO 11
#define BOARD_BMI_SCK_GPIO 12
#define BOARD_BMI_MISO_GPIO 13
#define BOARD_BMI_INT_GPIO 14
