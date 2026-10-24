idf_component_register(
    SRCS "main.c" "packet_wire.c" "../drivers/fake_afe.c"
    INCLUDE_DIRS "../include" "../boards"
    PRIV_REQUIRES
        bootloader_support
        esp_app_format
        esp_driver_gpio
        esp_driver_usb_serial_jtag
        esp_hw_support
        esp_timer
)
