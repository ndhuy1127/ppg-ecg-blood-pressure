idf_component_register(
    SRCS "main.c" "packet_wire.c" "imu_plan.c" "samp_map.c" "ecg_read.c"
         "../drivers/fake_afe.c" "../drivers/samp_edges.c" "../drivers/samp_capture.c"
         "../drivers/max30001.c" "../drivers/max30001_esp.c"
    INCLUDE_DIRS "../include" "../boards"
    PRIV_REQUIRES
        bootloader_support
        esp_app_format
        esp_driver_gpio
        esp_driver_mcpwm
        esp_driver_spi
        esp_driver_usb_serial_jtag
        esp_hw_support
        esp_timer
)
