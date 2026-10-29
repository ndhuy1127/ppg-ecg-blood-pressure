# Datasheet và tài liệu nguồn

Repo không lưu file PDF datasheet. Bảng dưới ghi tài liệu chính thức, phiên bản đã
đọc và các thông số đang dùng trong
`configs/hardware/interface_power_sampling_v0.md`,
`configs/hardware/power_budget_v1.md` và
`configs/hardware/Packet_Schema_V0.1.md`, kèm số trang để kiểm tra lại.

Cột "Phiên bản" ghi bản đã đọc. Nguồn không phải PDF gốc của hãng (file Eagle, bản
HTML, bản do SparkFun lưu, trang sản phẩm, wiki) được ghi rõ ở cột "Tài liệu" hoặc
"Phiên bản". Ba datasheet của
Analog Devices/Maxim do nhóm tải bằng trình duyệt (trang analog.com chặn công cụ
tải tự động). Riêng `configs/hardware/power_budget_v1.md` lấy dòng tiêu thụ của
MAX30001 (Rev 2, 8/19) và MAX30101 (Rev 0, 3/16) từ bản mirror cũ hơn bản trong bảng,
nên số trang ở đó phải đối chiếu lại với Rev 3. Khi nhà sản xuất ra revision mới, cập
nhật cột "Phiên bản" và đối chiếu lại.

| Linh kiện | Tài liệu | Phiên bản | Thông số đang dùng (trang) |
| --- | --- | --- | --- |
| ESP32-S3 | [ESP32-S3 Series Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf) | v2.2 | VIH ≥ 0,75·VDD, VIL ≤ 0,25·VDD; chân strapping 0, 3, 45, 46; GPIO47/48 chạy 1,8 V ở chip ESP32-S3R8V/R16V (Bảng 2-1, chú thích 4, tr. 17); XTAL_32K_P/N là GPIO15/16 (Bảng 2-4 tr. 21, Bảng 2-8 tr. 24); ADC1_CH0–CH9 là GPIO1–10 (Bảng 2-8, tr. 24) |
| ESP32-S3-WROOM-1/1U | [Datasheet](https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf) | v1.8 | N16R8: flash 16 MB Quad SPI, PSRAM 8 MB Octal SPI (Bảng 1-1, tr. 3); VDD_SPI 1,8 V chỉ ở N16R16VA (chú thích 7, tr. 4); module Octal PSRAM (chip ESP32-S3R8/R16V) dùng IO35–37 cho PSRAM, GPIO47/48 chạy 1,8 V chỉ với chip ESP32-S3R16V (chú thích b, c, tr. 12); module có PSRAM cố định VDD_SPI bằng eFuse, không theo GPIO45 (tr. 39) |
| Waveshare ESP32-S3-DEV-KIT-N8R8-M (U1, đặt 2026-10-27) | Wiki sản phẩm và bản vẽ kích thước của Waveshare (URL chưa ghi trong repo) | Đọc ngày 2026-10-27 | Căn cứ vẽ footprint U1 ở V1-draft5 (`configs/hardware/custom_board_proposal.md` A.3, A.6 mục 2): bo 63,30 × 25,40 mm; tâm chân đầu cách mép đầu anten 4,91 mm, tâm chân cuối cách mép đầu USB 5,05 mm; hai hàng 1×22 cách 22,86 mm, thứ tự chân giống DevKitC-1 (wiki: "Compatible with the pinout of ESP32-S3-DevKitC-1"); 4 lỗ Ø2 mm cách hai mép 1,80 mm; một cổng USB-C qua hub CH334 và cầu USB–UART CH343. Vị trí USB-C, BOOT, RESET trên footprint ước từ ảnh. Mã LDO 3,3 V chưa xác định (đọc khi nhận hàng) |
| ESP32-S3-DevKitC-1 (tham chiếu cũ: bo đã đổi sang Waveshare 2026-10-27) | [User Guide v1.1](https://github.com/espressif/esp-dev-kits/blob/master/docs/en/esp32-s3-devkitc-1/user_guide_v1.1.rst); schematic DevKitC v1.1 | v1.1 | Ba cách cấp nguồn loại trừ nhau (USB, 5V, 3V3); sơ đồ header J1/J3 (thứ tự chân U1 vẫn theo bản này); LDO 3,3 V là SGM2212-3.3 (schematic tr. 2) |
| SGM2212 (LDO của DevKitC, tham chiếu cũ) | Datasheet SGM2212 | REV A.2 (7/2023), đối chiếu ngày 2026-10-26 trên bản tải từ trang hãng | Dòng ra 800 mA (tr. 1); dòng chân GND (tr. 6). Dẫn trong `power_budget_v1.md` mục 2 |
| AP2112K-1.8 (LDO 1,8 V trên breakout MAX30001) | Datasheet Diodes | DS39724 Rev 2-2 | Iq 55 µA điển hình, 80 µA tối đa (tr. 5). Dẫn trong `power_budget_v1.md` mục 2 (2026-10-26) |
| TXB0108 (chuyển mức trên breakout MAX30001) | Datasheet TI | SCES643L | ICCA, ICCB tĩnh tối đa 5 µA mỗi phía (tr. 6–7). Dẫn trong `power_budget_v1.md` mục 2 (2026-10-26) |
| SP6214 (LDO 1,8 V trên bo SparkFun MAX30101) | Trang sản phẩm MaxLinear SP6213/SP6214 | Đọc ngày 2026-10-26; sản phẩm đã ngưng, chưa mở datasheet 241DSR00 | Iq 65 µA, dòng GND 135 µA ở 100 mA. Dẫn trong `power_budget_v1.md` mục 2 |
| BMI270 | [BST-BMI270-DS000](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf) | Rev 1.6, BST-BMI270-DS000-08 | VDD 1,71–3,6 V; VDDIO 1,2–3,6 V cấp riêng cho giao tiếp; tụ 100 nF tại VDDIO và VDD |
| MAX30001 breakout | [ProtoCentral pc_max30001_brk_v1.0](https://github.com/Protocentral/protocentral_max30001/tree/master/hardware) | Eagle v1.0 | Header VDD 3,3 V; LDO AP2112K-1.8; TXB0108; dao động 32,768 kHz; điện trở nối tiếp 51 kΩ trên ngõ ECG. README cùng repo ghi pinout khác → kiểm tra revision board nhận về |
| MAX30001 | [Datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/max30001.pdf) | Rev 3 (1/23), 19-100133 | Nguồn AVDD/DVDD 1,1–2,0 V, OVDD 1,65–3,6 V (tr. 8); VREF 0,995–1,005 V (tr. 8); SCLK ≤ 12 MHz (tr. 10); không có chân SYNCH, INTB/INT2B tích cực thấp (tr. 18–19); đổi mẫu sang mV (tr. 24, 65); độ trễ ECG theo tốc độ (tr. 26, Bảng 4); FMSTR suy ra từ FCLK (tr. 27, Bảng 6); SPI, con trỏ FIFO (tr. 36); STATUS gồm EINT, EOVF, DCLOFFINT, SAMP (tr. 41–42); INTB_TYPE (tr. 43); EFIT, SAMP_IT (tr. 44); SYNCH, FIFO_RST (tr. 46); bảng tốc độ ECG (tr. 49, Bảng 26; tr. 52); gain (tr. 53); cấu trúc word FIFO và ETAG (tr. 64–65, Bảng 47–48) |
| MAX30101 | [Datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX30101.pdf) | Rev 3 (6/20), 19-8453 | VDD 1,7–2,0 V; VLED+ 3,1–5,0 V (đỏ/IR), 4,5–5,5 V (xanh) (tr. 2); clock ADC 10,2–10,8 MHz (tr. 3); bước sóng IR 870/880/900 nm, đỏ 650/660/670 nm, xanh 530/537/545 nm (tr. 4; sơ đồ chức năng tr. 10 ghi 527 nm, dùng bảng đặc tính tr. 4); OVF_COUNTER (tr. 14); SMP_AVE, FIFO_ROLLOVER_EN (tr. 18); chế độ LED, tốc độ (tr. 19); khe multi-LED (tr. 20–21); khoảng cách khe (tr. 22, Bảng 11); tổ hợp được phép (tr. 29–30, Bảng 15–16); INT open-drain (tr. 30) |
| MAX30003 / MAX86171 (ghi chú ứng dụng) | [Chips to Measure ECG and PPG with Temporal Correlation](https://www.analog.com/en/resources/design-notes/chips-to-measure-ecg-and-ppg-with-temporal-correlation--maxim-integrated.html) (Maxim app note 6888) | Bản HTML đọc ngày 2026-10-23 | Cạnh xuống của xung đồng bộ (SAMP trên INT2B) đến ngay sau khi mẫu ECG vào FIFO (30 µs), trước cờ FIFO (15 µs); độ trễ mẫu tính tới cạnh đó, 512 sps: 20,839 ms (DLPF bỏ qua), 32,558 ms (DLPF 40 Hz), gồm 1,003 ms trễ lấy mẫu ADC (1,020 ms với FMSTR 32 000 Hz); độ lệch chuẩn đo được khoảng 3–4 µs; PPG MAX86171 lấy mẫu theo xung đồng bộ của ECG cho tương quan thời gian ±5 µs |
| MAX30101 (bản cũ) | [Datasheet do SparkFun lưu](https://cdn.sparkfun.com/assets/8/1/c/9/0/MAX30101_Datasheet.pdf) | Rev 2 (10/18), 19-8453 | Đọc ngày 2026-10-23 để kiểm chế độ multi-LED: bảng tổ hợp được phép chỉ có SpO2 và HR (Bảng 11–12, tr. 24), multi-LED chỉ có khoảng cách khe (Bảng 14, tr. 26); nguồn +5 V tối đa 200 mA trong sơ đồ ứng dụng (tr. 32); địa chỉ I²C 0xAE/0xAF (Bảng 17, tr. 30). Số trang/bảng khác Rev 3 |
| PAM2401 (boost trên bo SparkFun MAX30101) | [Datasheet](https://www.diodes.com/assets/Datasheets/PAM2401.pdf) | DS37285 Rev 1-2 (5/2014) | Dòng ra tới 1 000 mA ở VIN 3 V, VOUT 5 V (tr. 1); VOUT = 0,6 (1 + R1/R2) (tr. 5). Bo SparkFun dùng R1 750 kΩ, R4 100 kΩ (schematic `SparkFun_MAX30101_Qwiic.sch`), tức 5,1 V |
| MAX30102 | [Datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/max30102.pdf) | Rev 1 (10/18), 19-7740 | VDD 1,7–2,0 V; VLED+ 3,1–5,0 V (tr. 2); clock ADC 10,32–10,64 MHz (tr. 3); bước sóng IR 870/880/900 nm, đỏ 650/660/670 nm, không có LED xanh (tr. 4); I²C ≤ 400 kHz (tr. 5); địa chỉ 0xAE/0xAF (tr. 5 [chưa đối chiếu]; `custom_board_proposal.md` ghi tr. 29); ALC_OVF (tr. 12); OVF_COUNTER (tr. 13); cấu trúc FIFO (tr. 14–15); mã giả đọc FIFO (tr. 16); SMP_AVE, FIFO_ROLLOVER_EN, FIFO_A_FULL (tr. 17); chế độ LED, dải ADC (tr. 18); tốc độ, độ rộng xung (tr. 19); khe multi-LED (tr. 21); tổ hợp được phép, bypass VLED+ (tr. 23); INT open-drain (tr. 24); khoảng cách khe (tr. 25, Bảng 14) |

Thông số chưa có trong tài liệu nào ở trên và **phải đo**: độ trễ bên trong
MAX3010x, sai số tốc độ lấy mẫu thực của MAX3010x, hành vi của TXB0108 trên đường
MISO/INTB, mức pull-up thực của module PPG mua về, dòng của hub CH334, cầu CH343 và
LDO trên bo Waveshare (không có datasheet trong repo; đo theo `power_budget_v1.md`).
