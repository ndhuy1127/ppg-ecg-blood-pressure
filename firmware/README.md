# Firmware

> **Trạng thái:** firmware khung V1-module, build được (2026-10-23, RAM 4,5 %, flash
> 19,8 % của phân vùng 1 MB) nhưng **chưa chạy trên bo**
> (chưa có phần cứng). Chưa có driver AFE: mọi giá trị ECG/PPG là dữ liệu **giả**,
> chỉ để kiểm đường packet MCU → USB → logger, không phải tín hiệu sinh lý.

- **app/**: `main.c` (task, hàng đợi, cổng USB, nút t0), `packet_v01.c` (encoder
  Packet Schema V0.1, C thuần, không phụ thuộc ESP-IDF).
- **drivers/**: `fake_afe.c`, nguồn mẫu giả thay cho MAX30001/MAX30101.
- **boards/**: `board_v1_module.h`, GPIO theo bảng A.7 của
  [custom_board_proposal.md](../configs/hardware/custom_board_proposal.md).
- **include/**: `packet_v01.h`, `fake_afe.h`, `packet_kat.h` (known-answer của
  encoder).
- **tests/**: chưa có test chạy trên bo. Known-answer của encoder được đối chiếu
  với codec Python bằng
  [tests/test_firmware_packet_kat.py](../tests/test_firmware_packet_kat.py).

Không commit khóa hoặc thông tin kết nối thật.

## Board và toolchain

| Mục | Giá trị |
| --- | --- |
| Board | ESP32-S3 DevKitC N16R8 (bo OEM trong [danh sách mua](../hardware/bom/purchase_list_v1_module.md)) hoặc ESP32-S3-DevKitC-1-N8R8 chính hãng |
| Board PlatformIO | `esp32-s3-devkitc-1`. Image khai báo flash 2 MB (mặc định ESP-IDF), không bật PSRAM, nên nạp được lên bo 8 MB và 16 MB |
| Toolchain | PlatformIO Core 6.1.19, platform `espressif32@6.13.0`, ESP-IDF 5.5.3 (`framework-espidf` 3.50503.0), GCC xtensa 14.2.0 |
| Cấu hình | [platformio.ini](platformio.ini), [sdkconfig.defaults](sdkconfig.defaults) |

`sdkconfig.<env>`, `.pio/` do build sinh ra và được Git bỏ qua.

## Lệnh

Chạy từ Git root. Nếu `pio` chưa có trong PATH, dùng
`%USERPROFILE%\.platformio\penv\Scripts\pio.exe`.

```powershell
pio run -d firmware                                   # build
pio run -d firmware -t upload --upload-port COM5      # nạp (COM5 là ví dụ)
pio device monitor -d firmware -p COM6 -b 115200      # log chữ trên UART0
```

## Hai cổng USB

| Cổng | Nội dung |
| --- | --- |
| USB native (USB Serial/JTAG của ESP32-S3) | Packet nhị phân V0.1. Lúc khởi động, trước packet đầu tiên có thể có chữ của ROM và bootloader; decoder bỏ qua và báo là byte bị bỏ. Khi đã chạy, firmware không ghi chữ ra cổng này |
| UART0 (cổng COM qua chip cầu USB–UART), 115 200 baud | Log chữ: tên và phiên bản firmware, ESP-IDF, ELF SHA-256, kết quả tự kiểm encoder, `SESSION_ID`, thống kê mỗi 10 s |

Cổng nào trên bo OEM là USB native, cổng nào là chip cầu: **chưa kiểm trên bo**;
xem nhãn in cạnh cổng khi nhận hàng. Ghi ELF SHA-256 và `SESSION_ID` từ log UART0
vào metadata phiên (schema mục 11).

Khi khởi động, firmware kiểm encoder với `packet_kat.h` (CRC `"123456789"` =
`0x29B1`, packet mẫu 50 byte của `tests/fixtures/packet_v3_expected.json`). Sai
thì không gửi packet nào và LED trạng thái nháy nhanh.

## Luồng dữ liệu giả

| `CHANNEL_ID` | Nguồn | `FS_NOMINAL_MHZ` | Chu kỳ thật | N mỗi packet | `DATA[i]` với `k = FIRST_SAMPLE_INDEX + i` |
| --- | --- | ---: | --- | ---: | --- |
| `0xE1` | ECG giả, giống MAX30001 | 512 000 | 1 953 µs (≈ 512,03 Hz, lệch +64 ppm so với danh định) | 16 | Word 24 bit: mẫu 18 bit bù hai `(k mod 2048) − 1024` ở bit 23…6, ETAG = PTAG = 0 |
| `0xF1`–`0xF3` | PPG giả, giống MAX30101 chế độ multi-LED 3 khe | 100 000 | 10 000 µs | 4 | `(k mod 4096) + 32 768 × s`, `s` = 1, 2, 3 theo khe |
| `0xC1` | Nút t0 | 0 | — | 1 | Mã sự kiện `1` |

`DATA` là hàm của chỉ số mẫu, nên receiver kiểm được từng mẫu. Độ lệch +64 ppm của
ECG giả là cố ý: hồi quy tốc độ thực ở phép đo 10 phút phải thấy nó.

Nguồn giả có FIFO 32 mẫu. Task đọc **chốt** số mẫu đang chờ, lấy `T_ANCHOR_US`
ngay sau đó rồi đọc đúng số mẫu đã chốt (schema mục 5). FIFO đầy thì mẫu mới bị
mất như MAX3010x với `FIFO_ROLLOVER_EN = 0`.

## Quy ước packet của firmware

Trả lời các câu hỏi D trong [hướng dẫn logger](../docs/protocol/packet_logger.md):

| Câu | Quy ước |
| --- | --- |
| D1 | `CRC16` little-endian như các trường khác |
| D2 | `VERSION` luôn `0x01`. Đổi layout hoặc ý nghĩa trường thì tăng `VERSION` cùng bản firmware mới; không trộn hai version trong một phiên |
| D3 | `SEQ` gán **lúc gửi**, khi lấy packet ra khỏi hàng đợi MCU. Thiếu `SEQ`: packet mất sau hàng đợi (USB không nhận trong 20 ms). Hàng đợi MCU đầy: packet bị bỏ trước khi có `SEQ`; packet kế của kênh đó bật bit 1 và có `FIRST_SAMPLE_INDEX` nhảy, `SEQ` vẫn liên tục. Nếu chính packet mang bit 1 lại mất trên USB, bit 1 chuyển sang packet gửi được kế tiếp của kênh. FIFO AFE tràn: bit 0 bật ở packet đọc lúc phát hiện, khoảng mất nằm sau mẫu cuối của packet đó, packet kế có `FIRST_SAMPLE_INDEX` nhảy. Firmware khung chưa sinh bit 5 |
| D4 | Bit 4 bật trên mọi packet ECG/PPG cho tới khi đo xong độ trễ hiệu dụng `L` của cấu hình; không bật trên `0xC1` |
| D5 | `SEQ` (riêng từng kênh) và `FIRST_SAMPLE_INDEX` bắt đầu từ 0 ở mỗi phiên. `SESSION_ID` là số ngẫu nhiên 32 bit lấy lúc khởi động |
| D6 | `0xC1`: `SEQ` đếm riêng; `FIRST_SAMPLE_INDEX` = số thứ tự sự kiện trong phiên (0, 1, …); `FS_NOMINAL_MHZ` = 0; `T_ANCHOR_US` = `T_FIRST_US` = thời điểm cạnh xuống đầu tiên của nút |
| D7 | Không bao giờ gửi `SAMPLE_COUNT = 0` |
| D8 | Chờ bench |
| D9 | USB Serial/JTAG không có baud. Bộ đệm TX của driver 8 192 byte, hàng đợi MCU 64 packet, timeout ghi 20 ms. Firmware không ghi chữ ra cổng packet; lúc khởi động có thể có chữ của ROM và bootloader |
| D10 | Chờ phép đo 10 phút |

## Nút t0

GPIO4, tích cực mức thấp, có kéo lên trong chip (bo đế V1 có thêm 10 kΩ và
100 nF). Trên DevKitC trần: nối công tắc giữa GPIO4 và GND. Thời điểm sự kiện là
cạnh xuống đầu tiên; bỏ qua cạnh trong 200 ms sau đó, và chỉ nhận nếu nút vẫn
được giữ sau 20 ms (lọc dội khi nhả).

## Kiểm tra khi có bo (chưa làm)

Đây là phần firmware của
[trình tự bring-up](../hardware/test_reports/v1_bringup_procedure.md) mục 2.

1. Nạp, mở UART0: thấy `packet self-test passed` và `SESSION_ID`.
2. Ghi luồng byte của cổng USB native ra file trong 10 phút chạy không tải. Logger
   chưa đọc cổng serial trực tiếp vì `pyserial` chưa được duyệt; cách ghi cổng ra
   file chốt khi có bo.
3. `python scripts/packet_logger.py record --source-file ...`
   ([hướng dẫn](../docs/protocol/packet_logger.md)): `SEQ` và `T_ANCHOR_US` tăng
   đơn điệu, không lỗi CRC, `DATA` khớp công thức ở trên.
4. Bấm t0 vài lần: có packet `0xC1` tương ứng.

## Chưa có

- Driver MAX30001, MAX30101, BMI270.
- Xung `SAMP` của MAX30001 trên GPIO47 (INT2B).
- Packet sự kiện mã `3` (xung kích thích) cho phép đo 10 phút.
- Lệnh từ PC (bắt đầu/dừng, đổi cấu hình).
