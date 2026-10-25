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

/* J3 pin 1 (pin 2 is GND): pulse output for the 10-minute sync stimulus
 * (hardware/test_reports/sync_10min_test_plan.md, section 3). */
#define BOARD_STIM_GPIO 6

/* MAX30001 on SPI bus 1. */
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
 * edge polarity is measured at bring-up; falling until then. */
#ifndef BOARD_SAMP_CAPTURE
#define BOARD_SAMP_CAPTURE 0
#endif
#ifndef BOARD_SAMP_RISING_EDGE
#define BOARD_SAMP_RISING_EDGE 0
#endif

/* PPG read (Packet Schema V0.2 section 7.6): 0 counts PPG_RDY interrupts and
 * drains the FIFO at the 8th sample; a period in ms reads on a timer instead,
 * if bring-up shows that PPG_RDY does not work in the three-slot mode. */
#ifndef BOARD_PPG_READ_PERIOD_MS
#define BOARD_PPG_READ_PERIOD_MS 0
#endif

/* MAX30101 on I2C bus 1. BOARD_PPG_REAL 1 reads it (drivers/max30101.c, not run
 * on a chip yet) instead of the fake PPG source; 400 kHz, 100 kHz if the rising
 * edges through the cable are too slow (custom_board_proposal.md A.2). LED pulse
 * width 411 or 215 us, chosen at bring-up (A.6 section 3). */
#ifndef BOARD_PPG_REAL
#define BOARD_PPG_REAL 0
#endif
#ifndef BOARD_PPG_I2C_HZ
#define BOARD_PPG_I2C_HZ 400000
#endif
#ifndef BOARD_PPG_LED_PW_US
#define BOARD_PPG_LED_PW_US 411
#endif
#define BOARD_PPG_SDA_GPIO 8
#define BOARD_PPG_SCL_GPIO 9
#define BOARD_PPG_INT_GPIO 18

/* BMI270 on SPI bus 2. */
#define BOARD_BMI_CS_GPIO 10
#define BOARD_BMI_MOSI_GPIO 11
#define BOARD_BMI_SCK_GPIO 12
#define BOARD_BMI_MISO_GPIO 13
#define BOARD_BMI_INT_GPIO 14
