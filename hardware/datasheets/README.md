# Datasheet và tài liệu nguồn

Repo không lưu file PDF datasheet. Bảng dưới ghi tài liệu chính thức, phiên bản đã
đọc và các thông số đang dùng trong
`configs/hardware/interface_power_sampling_v0.md` và
`configs/hardware/Packet_Schema_V0.1.md`, kèm số trang để kiểm tra lại.

Tất cả tài liệu dưới đây đã được đọc trực tiếp bản PDF gốc. Ba datasheet của
Analog Devices/Maxim do nhóm tải bằng trình duyệt (trang analog.com chặn công cụ
tải tự động). Khi nhà sản xuất ra revision mới, cập nhật cột "Phiên bản" và đối
chiếu lại.

| Linh kiện | Tài liệu | Phiên bản | Thông số đang dùng (trang) |
| --- | --- | --- | --- |
| ESP32-S3 | [ESP32-S3 Series Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf) | v2.2 | VIH ≥ 0,75·VDD, VIL ≤ 0,25·VDD; chân strapping 0, 3, 45, 46 |
| ESP32-S3-DevKitC-1 | [User Guide v1.1](https://github.com/espressif/esp-dev-kits/blob/master/docs/en/esp32-s3-devkitc-1/user_guide_v1.1.rst) | v1.1 | Ba cách cấp nguồn loại trừ nhau (USB, 5V, 3V3); sơ đồ header J1/J3 |
| BMI270 | [BST-BMI270-DS000](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf) | Rev 1.6, BST-BMI270-DS000-08 | VDD 1,71–3,6 V; VDDIO 1,2–3,6 V cấp riêng cho giao tiếp; tụ 100 nF tại VDDIO và VDD |
| MAX30001 breakout | [ProtoCentral pc_max30001_brk_v1.0](https://github.com/Protocentral/protocentral_max30001/tree/master/hardware) | Eagle v1.0 | Header VDD 3,3 V; LDO AP2112K-1.8; TXB0108; dao động 32,768 kHz; điện trở nối tiếp 51 kΩ trên ngõ ECG. README cùng repo ghi pinout khác → kiểm tra revision board nhận về |
| MAX30001 | [Datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/max30001.pdf) | Rev 3 (1/23), 19-100133 | Nguồn AVDD/DVDD 1,1–2,0 V, OVDD 1,65–3,6 V (tr. 8); VREF 0,995–1,005 V (tr. 8); SCLK ≤ 12 MHz (tr. 10); không có chân SYNCH, INTB/INT2B tích cực thấp (tr. 18–19); đổi mẫu sang mV (tr. 24, 65); độ trễ ECG theo tốc độ (tr. 26, Bảng 4); FMSTR suy ra từ FCLK (tr. 27, Bảng 6); SPI, con trỏ FIFO (tr. 36); STATUS gồm EINT, EOVF, DCLOFFINT, SAMP (tr. 41–42); INTB_TYPE (tr. 43); EFIT, SAMP_IT (tr. 44); SYNCH, FIFO_RST (tr. 46); bảng tốc độ ECG (tr. 49, Bảng 26; tr. 52); gain (tr. 53); cấu trúc word FIFO và ETAG (tr. 64–65, Bảng 47–48) |
| MAX30101 | [Datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX30101.pdf) | Rev 3 (6/20), 19-8453 | VDD 1,7–2,0 V; VLED+ 3,1–5,0 V (đỏ/IR), 4,5–5,5 V (xanh) (tr. 2); clock ADC 10,2–10,8 MHz (tr. 3); bước sóng IR 870/880/900 nm, đỏ 650/660/670 nm, xanh 530/537/545 nm (tr. 4; sơ đồ chức năng tr. 10 ghi 527 nm, dùng bảng đặc tính tr. 4); OVF_COUNTER (tr. 14); SMP_AVE, FIFO_ROLLOVER_EN (tr. 18); chế độ LED, tốc độ (tr. 19); khe multi-LED (tr. 20–21); khoảng cách khe (tr. 22, Bảng 11); tổ hợp được phép (tr. 29–30, Bảng 15–16); INT open-drain (tr. 30) |
| MAX30102 | [Datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/max30102.pdf) | Rev 1 (10/18), 19-7740 | VDD 1,7–2,0 V; VLED+ 3,1–5,0 V (tr. 2); clock ADC 10,32–10,64 MHz (tr. 3); bước sóng IR 870/880/900 nm, đỏ 650/660/670 nm, không có LED xanh (tr. 4); I²C 0xAE/0xAF, ≤ 400 kHz (tr. 5); ALC_OVF (tr. 12); OVF_COUNTER (tr. 13); cấu trúc FIFO (tr. 14–15); mã giả đọc FIFO (tr. 16); SMP_AVE, FIFO_ROLLOVER_EN, FIFO_A_FULL (tr. 17); chế độ LED, dải ADC (tr. 18); tốc độ, độ rộng xung (tr. 19); khe multi-LED (tr. 21); tổ hợp được phép, bypass VLED+ (tr. 23); INT open-drain (tr. 24); khoảng cách khe (tr. 25, Bảng 14) |

Thông số chưa có trong tài liệu nào ở trên và **phải đo**: độ trễ bên trong
MAX3010x, sai số tốc độ lấy mẫu thực của MAX3010x, hành vi của TXB0108 trên đường
MISO/INTB (chưa đọc datasheet TXB0108), mức pull-up thực của module PPG mua về.
