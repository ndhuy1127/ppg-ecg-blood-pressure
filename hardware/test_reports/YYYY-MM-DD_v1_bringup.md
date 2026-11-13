# Báo cáo bring-up V1-module — YYYY-MM-DD

> **Mẫu, chưa điền** (tạo 2026-11-13). Khi bắt đầu bring-up: đổi tên file thành ngày thật
> (`<YYYY-MM-DD>_v1_bringup.md`), điền từng ô. Mục theo
> [trình tự bring-up](v1_bringup_procedure.md) (BU) mục 11; tiến độ ở
> [checklist](v1_bringup_checklist.md). Ô để trống là chưa đo. Bước không làm thì ghi
> "không làm" kèm lý do, không để trống.
>
> **An toàn:** chỉ tín hiệu nhân tạo. Không gắn điện cực lên người.

## 1. Thông tin chung

| Mục | Giá trị |
| --- | --- |
| Ngày | |
| Người làm | |
| Revision bo đế (title block KiCad) | |
| Revision bo cổ tay (title block KiCad) | |
| Nhiệt độ phòng (°C) | |
| Laptop chạy pin, đã rút sạc | |

## 2. Firmware đã nạp

Một dòng cho mỗi lần nạp. ELF SHA-256 là thứ định danh bản đã nạp
([firmware/README.md](../../firmware/README.md) mục "Bản build"). Bản build sẵn trước khi
hàng về ghi ở [checklist](v1_bringup_checklist.md) mục A; nạp bản nào thì chép dòng đó vào
đây.

| Lần nạp | Commit | Env | `PLATFORMIO_BUILD_FLAGS` (nguyên văn, hay "không đặt") | ELF SHA-256 | Lệnh nạp | Cổng COM |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

## 3. Kiểm khi nhận hàng (BU mục 1)

Ghi riêng giá trị thiết kế/datasheet và giá trị đo.

| Module | Kiểm | Thiết kế/datasheet | Đo được | Đạt |
| --- | --- | --- | --- | --- |
| Bo Waveshare | Khoảng cách tâm hai hàng chân (mm) | 22,86 | | |
| Bo Waveshare | Ký hiệu module | ESP32-S3-WROOM-1-N8R8 | | |
| Bo Waveshare | Mã khắc LDO 3,3 V | — | | |
| Bo Waveshare | Nhãn chân so với bảng A.7 | Bảng A.7 | | |
| Breakout MAX30001 | Revision; R3, R7, R8, SV1 | `pc_max30001_brk_v1.0` | | |
| Cáp ECG | Số dây; LA/RA/RL ↔ ring/tip/sleeve | 3 dây; LA ring, RA tip, RL sleeve | | |
| SparkFun MAX30101 | Mã, JP1, hàng chân | SEN-16474 | | |
| SparkFun BMI270 | Mã, kích thước, jumper | SEN-22397, 1" × 1" | | |
| Bo Waveshare | Kích thước, bước chân, lỗ vít (mm) | Footprint KiCad | | |
| Breakout MAX30001 | Kích thước, bước chân, lỗ vít (mm) | Footprint KiCad | | |
| SparkFun MAX30101 | Kích thước, bước chân, lỗ vít (mm) | Footprint KiCad | | |
| SparkFun BMI270 | Kích thước, bước chân, lỗ vít (mm) | Footprint KiCad | | |
| Cả bốn module | Đặt lên bản in 1:1 | Trùng footprint | | |

## 4. Bo Waveshare đứng riêng (BU mục 2)

| Bước | Mục | Chờ đợi | Kết quả | Đạt |
| --- | --- | --- | --- | --- |
| 1 | Cổng COM USB native (`303A:1001`) | — | | |
| 1 | Cổng COM CH343 (log UART0) | — | | |
| 1 | `bMaxPower` của hub CH334 | — | | |
| 1 | `bMaxPower` của `303A:1001` | — | | |
| 2 | `chip_id` (nguyên văn, khối dưới) | ESP32-S3 | | |
| 2 | `espefuse summary`: `VDD_SPI_FORCE`, `VDD_SPI_TIEH` | 1, 1 | | |
| 3 | Log UART0: `packet self-test passed`, `SESSION_ID`, ELF SHA-256 | ELF SHA-256 trùng mục 2 | | |
| 4 | 3V3–GND (V) | khoảng 3,3 | | |
| 4 | Dòng USB tester, firmware khung (mA) | mốc so sánh | | |
| 5 | Ghi 10 phút không tải: đường dẫn bản ghi | ngoài `data/raw/` | | |
| 5 | `skipped_bytes` chỉ ở offset 0 | có | | |
| 5 | `SEQ`, `T_ANCHOR_US` tăng đơn điệu | có | | |
| 5 | `DATA` khớp công thức firmware README | có | | |
| 5 | Mọi packet `VERSION = 2` | có | | |
| 5 | `device_info`: ELF SHA-256 trùng UART0; số packet hợp lệ | khoảng 60 | | |
| 5 | Mọi packet ECG có bit 8 | có | | |
| 5 | Đủ sáu trục IMU | có | | |
| 6 | `imu_stall`: so với firmware README | — | | |
| 6 | `samp_faults`: so với firmware README | — | | |
| 6 | `ppg_delay`: so với firmware README | — | | |
| 7 | `ping`, `mark cuff_end`, `mark operator`: `acked`, kết quả 0 | có | | |
| 7 | `set-ppg-led --red 128 --allow-over-firmware-limit`: kết quả 8 | `out_of_range` | | |
| 7 | Không có `--allow-...`: `device_command.py` từ chối mã 128 | không ghi hộp thư | | |
| 7 | `0xC1` mã 2 và 4; `T_ANCHOR_US` không sau `0xD3` tương ứng | có | | |
| 7 | Hiệu `T_ANCHOR_US` `0xD3` − `0xC1` (µs), chỉ tham khảo | — | | |

Kết quả nguyên văn `chip_id` và `espefuse summary` (các trường VDD_SPI):

```text

```

## 5. PCB trần (BU mục 3)

| Bước | Mục | Chờ đợi | Kết quả | Đạt |
| --- | --- | --- | --- | --- |
| 1 | Soi kính lúp; khe phay bo cổ tay (mm) | không cầu đồng; 3 × 22 | | |
| 2 | Điện trở 3V3–GND bo đế (Ω) | không chập | | |
| 2 | Điện trở 3V3–GND bo cổ tay (Ω) | không chập | | |
| 3 | Thông mạch J2 ↔ U1 theo A.7 | đủ | | |
| 3 | Thông mạch J1 ↔ M1/M3 theo A.7 | đủ | | |
| 3 | GND ở chân 2, 4, 6, 8, 10, 12, 14 | có | | |
| 3 | J3.1 ↔ pad 6 U1; J3.2 ↔ GND | có | | |

## 6. Sửa module (BU mục 4)

| Module | Việc | Chờ đợi | Kết quả | Đạt |
| --- | --- | --- | --- | --- |
| Breakout MAX30001 | R3 mới đo trước khi hàn (kΩ) | 220 ±1 % | | |
| Breakout MAX30001 | Pad R7, R8 | hở mạch | | |
| Breakout MAX30001 | Header SV1; đặt lên bản in 1:1 | GND trùng J1.1, lỗ vít trùng | | |
| SparkFun MAX30101 | Cắt JP1 | LED nguồn không sáng | | |
| SparkFun BMI270 | Cắt `I2C`, `ADR` | hở mạch | | |

## 7. Hàn và lắp (BU mục 5)

| Bo | Bước | Chờ đợi | Kết quả | Đạt |
| --- | --- | --- | --- | --- |
| Bo đế | 4: 3V3–GND sau hàn (Ω) | không chập | | |
| Bo cổ tay | 1: J1 thông mạch chân 1 cáp ↔ lỗ J1.1 trước khi hàn | thông | | |
| Bo cổ tay | 3: M3 lắp mặt chip quay ra ngoài | có | | |
| Bo cổ tay | 4: 3V3–GND sau hàn (Ω) | không chập | | |

## 8. Bo đế với bo Waveshare (BU mục 6)

| Bước | Mục | Chờ đợi | Đo được | Đạt |
| --- | --- | --- | --- | --- |
| 1 | Hướng bo Waveshare theo silkscreen | đúng | | |
| 2 | Dòng lúc cắm (mA) | thấp hơn khoảng 61 | | |
| 2 | Dòng ổn định (mA) | thấp hơn khoảng 61 | | |
| 2 | TP1–TP2 (V) | khoảng 3,3 | | |
| 3 | D1 nháy 0,5 s | có | | |
| 4 | TP6 cao khi nhả, thấp khi nhấn SW1 | có | | |
| 4 | Mỗi lần nhấn: `t0 event` trên UART0 và một `0xC1` | có | | |

## 9. MAX30001 trên bo đế (BU mục 7)

| Bước | Mục | Chờ đợi | Đo được | Đạt |
| --- | --- | --- | --- | --- |
| 1 | 3V3 (V) | khoảng 3,3 | | |
| 1 | LDO 1,8 V breakout (V) | khoảng 1,8 | | |
| 1 | Dòng USB (mA) | — | | |
| 2 | `INFO` (0x0F), nửa byte cao | `0x5` | | |
| 3 | Đọc lại thanh ghi cấu hình A.2 | khớp | | |
| 4 | INTB (GPIO21), tần số (Hz) | 32 | | |
| 4 | INT2B (GPIO47), tần số (Hz) | 512 | | |
| 4 | INT2B biên độ (V) | khoảng 3,3 | | |
| 4 | Cực tính `SAMP` | — | | |
| 4 | Độ rộng xung `SAMP` (µs) | khoảng 488 | | |
| 4 | Rung trước/sau TXB0108 | — | | |
| 4 | MCPWM capture: cặp nhận/loại, sai số quy đổi (µs) | < 5 | | |
| 4 | "ECG FIFO read - SAMP edge of the last sample" (ms), qua nhiều lần khởi động lại ánh xạ | 0 tới khoảng 2 | | |
| 4 | Xung đầu sau `SYNCH` ứng với mẫu đầu FIFO | có | | |
| 5 | Mức chung ở đầu vào (V) | 0,29–1,39 | | |
| 5 | Xung dương LA so với RA cho mẫu dương | có | | |
| 5 | ETAG mẫu hợp lệ | có | | |
| 5 | Tháo một đầu bấm: `DCLOFFINT`, `STATUS` bit 2 | có | | |
| 6 | Simulator ECG: số R-peak khớp nhịp đặt (hay "không làm") | — | | |

## 10. Bo cổ tay qua cáp (BU mục 8)

| Bước | Mục | Chờ đợi | Đo được | Đạt |
| --- | --- | --- | --- | --- |
| 1 | Thông mạch cáp 16 dây; đo xuyên hệ | đủ, 3V3 không chập GND | | |
| 2 | 3V3 tại C2 bo cổ tay (V) | khoảng 3,3 | | |
| 2 | Dòng 5 V USB, LED mã mặc định (mA) | khoảng 61 | | |
| 2 | Dòng 5 V USB, LED `0x7F` (mA) | khoảng 112 | | |
| 2 | Dòng khởi động qua shunt (ảnh) | — | | |
| 3 | V1: VLED+ không tải (V) | 4,9–5,3 | | |
| 3 | V2: đỉnh khởi động (V) | ≤ 5,5 | | |
| 3 | V3: trong xung `0x7F` (V) | 4,5–5,5 | | |
| 3 | V4: ghi chú nếu 5,0–5,3 V | — | | |
| 4 | Quét I²C | chỉ `0x57` | | |
| 4 | `PART_ID` (0xFF) | `0x15` | | |
| 4 | Sườn lên SCL tại TP4 (ns); tốc độ I²C dùng | — | | |
| 5 | `CHIP_ID` BMI270 (0x00) | `0x24` | | |
| 5 | Trạng thái khởi tạo BMI270 | đạt | | |
| 5 | SCK tại TP5; tốc độ SPI dùng | — | | |
| 5 | Dấu trục: +X, +Y, +Z hướng lên | khớp (−X, +Y, −Z) | | |
| 6 | `SPO2_SR` đọc lại | — | | |
| 6 | Tốc độ ra khe 1, 2, 3 (sps) | 200 ± 3 % | | |
| 6 | `PPG_RDY` báo mỗi mẫu ở ba khe | — | | |
| 8 | 3V3 bo Waveshare, VCC breakout, 1,8 V breakout, 3V3 tại M1 (V) | — | | |
| 8 | Nhiễu ECG khi bật/tắt LED PPG | — | | |
| 8 | SCK, MOSI, CS tại BMI270; MISO tại MCU (1 và 2 MHz) | — | | |
| 8 | Sườn lên I²C hai phía bộ chuyển mức (ns) | ≤ 300 | | |
| 8 | Sườn giả trên `PPG_SCL`, `T0_BTN`, `ECG_CS` | không | | |
| 10 | Nhiễu đèn (a) hộp tối, (b) đèn bật, (c) đèn tắt: tần số, biên độ đỉnh so với nền | không đỉnh rõ ở 0,5–8 Hz | | |

**Chạy cả hệ 120 phút (BU mục 8 bước 9; AT mục 4).** Mỗi 15 phút một dòng.

| Phút | Dòng 5 V USB (mA) | 3V3 TP1–TP2 (V) | Nhiệt độ vỏ LDO (°C) | Nhiệt độ bo cổ tay (°C) | Nhiệt độ phòng (°C) |
| ---: | --- | --- | --- | --- | --- |
| 0 | | | | | |
| 15 | | | | | |
| 30 | | | | | |
| 45 | | | | | |
| 60 | | | | | |
| 75 | | | | | |
| 90 | | | | | |
| 105 | | | | | |
| 120 | | | | | |

Đỉnh RAM tiến trình logger: ____ . Pin laptop còn ở phút 120: ____ .

## 11. Đo đồng bộ 10 phút (BU mục 9)

Ghi theo [sync_10min_test_plan.md](sync_10min_test_plan.md). Ở đây chỉ ghi env, cờ build
và đường dẫn bản ghi.

| Lần | Env | `PLATFORMIO_BUILD_FLAGS` | ELF SHA-256 | Đường dẫn bản ghi | Kết quả A1–A9 |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

## 12. Dòng rò và nhiệt (BU mục 10)

Ghi theo [leakage_thermal_test_plan_v1.md](leakage_thermal_test_plan_v1.md). Ở đây chỉ ghi
đường dẫn biên bản và kết luận.

| Mục | Giá trị |
| --- | --- |
| Đường dẫn biên bản | |
| Kết luận | |

## 13. Bản ghi packet

Một dòng mỗi lần `record`. Bản ghi bring-up nằm ngoài `data/raw/`.

| Bước BU | Env | `SESSION_ID` (`device_session_id`) | Đường dẫn bản ghi | SHA-256 `raw.bin` | Metadata dùng | `issue_counts` đáng chú ý |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

## 14. Ảnh và file lớn

Lưu ngoài Git (`runs/`). Ghi đường dẫn và SHA-256.

| File | Bước BU | SHA-256 |
| --- | --- | --- |
| | | |

## 15. Bước không đạt và cách xử lý

| Bước BU | Hiện tượng | Cách xử lý | Kết quả sau xử lý |
| --- | --- | --- | --- |
| | | | |
