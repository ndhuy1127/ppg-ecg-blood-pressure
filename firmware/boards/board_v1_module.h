/*
 * GPIO map of the KiCad V1-module base board
 * (configs/hardware/custom_board_proposal.md, section A.7). Since 2026-10-25 the
 * MAX30001, MAX30101 and BMI270 drivers (BOARD_ECG_REAL, BOARD_PPG_REAL,
 * BOARD_IMU_REAL) and the sync stimulus (BOARD_STIM) use these AFE and J3
 * pins, as does the SAMP capture on GPIO47 (BOARD_SAMP_CAPTURE). The default
 * build still runs fake_afe and uses only the t0 button and the status LED.
 *
 * Bus names are logical; ESP-IDF hosts (max30001_esp.c, bmi270_esp.c,
 * max30101_esp.c): ECG SPI bus = SPI2_HOST, IMU SPI bus = SPI3_HOST, PPG I2C
 * bus = I2C_NUM_0. Pins reach the hosts through the GPIO matrix.
 */
#pragma once

/* t0 button SW1: 10 kOhm pull-up and 100 nF on the board, active low. On the
 * MCU board alone (Waveshare, no base board), a switch from GPIO4 to GND works
 * (internal pull-up is on).
 * Define BOARD_T0_GPIO at compile time to use another pin. */
#ifndef BOARD_T0_GPIO
#define BOARD_T0_GPIO 4
#endif
#define BOARD_LED_STAT_GPIO 5

/* J3 pin 1 (pin 2 is GND): pulse output for the 10-minute sync stimulus
 * (hardware/test_reports/sync_10min_test_plan.md, section 3). BOARD_STIM 1
 * drives it and sends event packets with code 3 (main.c, stim_plan.c). */
#define BOARD_STIM_GPIO 6
#ifndef BOARD_STIM
#define BOARD_STIM 0
#endif

/* MAX30001 on the ECG SPI bus (SPI2_HOST). */
#define BOARD_ECG_CS_GPIO 7
#define BOARD_ECG_SCLK_GPIO 15
#define BOARD_ECG_MOSI_GPIO 16
#define BOARD_ECG_MISO_GPIO 17
#define BOARD_ECG_INTB_GPIO 21
#define BOARD_ECG_INT2B_GPIO 47
/* 1 reads a MAX30001 (drivers/max30001.c, not run on a chip yet) instead of the
 * fake ECG source; it needs the SAMP capture too (BOARD_SAMP_CAPTURE 1). SPI
 * clock 4 MHz (custom_board_proposal.md A.2). */
#ifndef BOARD_ECG_REAL
#define BOARD_ECG_REAL 0
#endif
#define BOARD_ECG_SPI_HZ 4000000
/* SAMP on INT2B (Packet Schema V0.2 section 7.1): 1 builds in the MCPWM capture
 * (samp_capture.c, not run on a chip yet) instead of the fake ECG edges. The
 * edge polarity is measured at bring-up (section 7 step 4); falling until then.
 * The measured value is passed at build time, e.g. PLATFORMIO_BUILD_FLAGS=
 * "-DBOARD_SAMP_RISING_EDGE=1" (firmware/README.md, section "Bản build"). */
#ifndef BOARD_SAMP_CAPTURE
#define BOARD_SAMP_CAPTURE 0
#endif
#ifndef BOARD_SAMP_RISING_EDGE
#define BOARD_SAMP_RISING_EDGE 0
#endif
#if BOARD_SAMP_RISING_EDGE != 0 && BOARD_SAMP_RISING_EDGE != 1
#error "BOARD_SAMP_RISING_EDGE must be 0 (falling edge) or 1 (rising edge)"
#endif

/* PPG read (Packet Schema V0.2 section 7.6): 0 wakes the reader on PPG_RDY
 * (an interrupt only wakes it; the FIFO pointers, not a count of interrupts,
 * give the samples waiting) and drains the FIFO once 8 samples wait; a period
 * in ms reads on a timer instead, if bring-up shows that PPG_RDY does not work
 * in the three-slot mode. */
#ifndef BOARD_PPG_READ_PERIOD_MS
#define BOARD_PPG_READ_PERIOD_MS 0
#endif

/* MAX30101 on the PPG I2C bus (I2C_NUM_0). BOARD_PPG_REAL 1 reads it (drivers/max30101.c, not run
 * on a chip yet) instead of the fake PPG source; 400 kHz, 100 kHz if the rising
 * edges through the cable are too slow (custom_board_proposal.md A.2). LED pulse
 * width 411 or 215 us, chosen at bring-up (A.6 section 3) and passed at build
 * time like the SAMP edge above; any other value does not build (the driver
 * would silently take 411). */
#ifndef BOARD_PPG_REAL
#define BOARD_PPG_REAL 0
#endif
#ifndef BOARD_PPG_I2C_HZ
#define BOARD_PPG_I2C_HZ 400000
#endif
#ifndef BOARD_PPG_LED_PW_US
#define BOARD_PPG_LED_PW_US 411
#endif
#if BOARD_PPG_LED_PW_US != 411 && BOARD_PPG_LED_PW_US != 215
#error "BOARD_PPG_LED_PW_US must be 411 or 215"
#endif
#define BOARD_PPG_SDA_GPIO 8
#define BOARD_PPG_SCL_GPIO 9
#define BOARD_PPG_INT_GPIO 18

/* BMI270 on the IMU SPI bus (SPI3_HOST). BOARD_IMU_REAL 1 reads it (drivers/bmi270.c, not run on a
 * chip yet) instead of the fake IMU source; SPI 1 MHz to start, 2 MHz after the
 * scope check through the cable (interface_power_sampling_v0.md). */
#ifndef BOARD_IMU_REAL
#define BOARD_IMU_REAL 0
#endif
#ifndef BOARD_IMU_SPI_HZ
#define BOARD_IMU_SPI_HZ 1000000
#endif
#define BOARD_BMI_CS_GPIO 10
#define BOARD_BMI_MOSI_GPIO 11
#define BOARD_BMI_SCK_GPIO 12
#define BOARD_BMI_MISO_GPIO 13
#define BOARD_BMI_INT_GPIO 14
