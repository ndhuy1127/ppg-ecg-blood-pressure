# Firmware

> **Trạng thái:** firmware khung V1-module gửi
> [Packet Schema V0.2](../configs/hardware/Packet_Schema_V0.2.md) từ 2026-10-24
> (bước 2a của mục 9: encoder V0.2, packet thông tin thiết bị `0xD1`, chuyển tiếp
> bit 5; bước 2b: IMU giả sáu trục, chia phần tồn đọng, neo lại sau FIFO đầy). Build
> được (2026-10-24, RAM 4,5 %, flash 20,1 % của phân vùng 1 MB) nhưng **chưa chạy
> trên bo** (chưa có phần cứng). Chưa có driver AFE hay BMI270: mọi giá trị
> ECG/PPG/IMU là dữ liệu **giả**, chỉ để kiểm đường packet MCU → USB → logger, không
> phải tín hiệu sinh lý. Chưa có mốc `SAMP` (bit 8) và cách đọc FIFO PPG mới (bước
> 2c–2d).

- **app/**: `main.c` (task, hàng đợi, cổng USB, nút t0, thông tin thiết bị, đọc
  IMU), `imu_plan.c` (chỉ số, `STATUS` và cách chia packet của một lần đọc FIFO
  BMI270 theo V0.2 mục 3–5; C thuần),
  `packet_wire.c` (encoder Packet Schema V0.2, đóng gói payload `0xD1` và phép tự
  kiểm lúc khởi động; C thuần, không phụ thuộc ESP-IDF; tên giống codec Python
  `software/data_io/packet_wire.py`, trước 2026-10-24 là `packet_v01.c`).
- **drivers/**: `fake_afe.c`, nguồn mẫu giả thay cho MAX30001/MAX30101/BMI270
  (FIFO có độ sâu cấu hình được, đầy thì giữ nội dung và bỏ mẫu mới).
- **boards/**: `board_v1_module.h`, GPIO theo bảng A.7 của
  [custom_board_proposal.md](../configs/hardware/custom_board_proposal.md).
- **include/**: `packet_wire.h`, `imu_plan.h`, `fake_afe.h`, `packet_kat.h`
  (known-answer V0.2 của encoder).
- **tests/**: chưa có test chạy trên bo. Known-answer của encoder được dựng lại
  độc lập (Python `struct` và `binascii.crc_hqx`) và đối chiếu với codec Python bằng
  [tests/test_firmware_packet_kat.py](../tests/test_firmware_packet_kat.py) (không
  biên dịch C). [tests/test_firmware_c_encoder.py](../tests/test_firmware_c_encoder.py)
  biên dịch `app/packet_wire.c` bằng trình biên dịch C của máy (`$CC`, `cc`, `gcc`
  hoặc `clang`; không có thì bỏ qua, CI Ubuntu có `gcc`), chạy chính hàm tự kiểm
  lúc khởi động (`pkt_self_test`), so packet V0.2 ngẫu nhiên (seed cố định, mọi mã
  kênh, IMU ở biên int16) với `packet_wire.py`, và so payload `0xD1` (hash có word
  bit 31, chuỗi ASCII 0–31 byte, từ chối chuỗi 32 byte hoặc không phải ASCII) với
  `device_info_data`. Test này chỉ kiểm encoder, không kiểm ISR, task, USB hay phần
  cứng. [tests/test_firmware_imu_plan.py](../tests/test_firmware_imu_plan.py) biên
  dịch `app/imu_plan.c` theo cùng cách và so với spec V0.2 mục 3–5 (xem mục "IMU
  giả").

Không commit khóa hoặc thông tin kết nối thật.

## Board và toolchain

| Mục | Giá trị |
| --- | --- |
| Board | ESP32-S3-DevKitC-1-N8R8 chính hãng (dòng 6 của [danh sách mua](../hardware/bom/purchase_list_v1_module.md), chốt 2026-10-24) |
| Board PlatformIO | `esp32-s3-devkitc-1`. Image khai báo flash 2 MB (mặc định ESP-IDF), không bật PSRAM, nên nạp được lên bo 8 MB |
| Toolchain | PlatformIO Core 6.1.19, platform `espressif32@6.13.0`, ESP-IDF 5.5.3 (`framework-espidf` 3.50503.0), GCC xtensa 14.2.0 |
| Cấu hình | [platformio.ini](platformio.ini), [sdkconfig.defaults](sdkconfig.defaults) |

`sdkconfig.<env>`, `.pio/` do build sinh ra và được Git bỏ qua. Trên máy còn ít
RAM trống, GCC có thể lỗi "internal compiler error: Segmentation fault" khi build
song song các file của ESP-IDF (gặp 2026-10-24 với `esp_lcd_panel_rgb.c`, còn 2,5 GB
trống); build tuần tự bằng `pio run -d firmware -j 1` thì qua.

## Lệnh

Chạy từ Git root. Nếu `pio` chưa có trong PATH, dùng
`%USERPROFILE%\.platformio\penv\Scripts\pio.exe`.

```powershell
pio run -d firmware                                   # build
pio run -d firmware -e esp32s3_devkitc_imu_stall      # build có dừng đọc IMU (mục "IMU giả")
pio run -d firmware -t upload --upload-port COM5      # nạp (COM5 là ví dụ)
pio device monitor -d firmware -p COM6 -b 115200      # log chữ trên UART0
```

## Hai cổng USB

| Cổng | Nội dung |
| --- | --- |
| USB native (USB Serial/JTAG của ESP32-S3) | Packet nhị phân V0.2. Lúc khởi động, trước packet đầu tiên có thể có chữ của ROM và bootloader; decoder bỏ qua và báo là byte bị bỏ. Khi đã chạy, firmware không ghi chữ ra cổng này |
| UART0 (cổng COM qua chip cầu USB–UART), 115 200 baud | Log chữ: tên và phiên bản firmware, ESP-IDF, ELF SHA-256, kết quả tự kiểm encoder, `SESSION_ID`, thống kê mỗi 10 s |

Bo chính hãng có hai cổng Micro-USB: theo
[hướng dẫn DevKitC-1 v1.1](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html),
cổng USB-to-UART (nhãn UART) đi qua chip cầu, cổng còn lại (nhãn USB) là USB native
của ESP32-S3. **Chưa kiểm trên bo**: đọc nhãn in cạnh cổng khi nhận hàng. Ghi ELF
SHA-256 và `SESSION_ID` từ log UART0 vào metadata phiên (schema mục 11).

Khi khởi động, firmware kiểm encoder với `packet_kat.h` (`pkt_self_test`): CRC
`"123456789"` = `0x29B1`, `T_FIRST_US`, packet ECG mẫu 50 byte (packet mẫu V0.1 của
`tests/fixtures/packet_v3_expected.json` với `VERSION = 2` và `STATUS` bit 4, 8) và
packet thông tin thiết bị mẫu 142 byte. Sai thì không gửi packet nào và LED trạng
thái nháy nhanh. Known-answer V0.1 vẫn nằm trong fixture làm bản cũ.

## Luồng dữ liệu giả

| `CHANNEL_ID` | Nguồn | `FS_NOMINAL_MHZ` | Chu kỳ thật | N mỗi packet | `DATA[i]` với `k = FIRST_SAMPLE_INDEX + i` |
| --- | --- | ---: | --- | ---: | --- |
| `0xE1` | ECG giả, giống MAX30001 | 512 000 | 1 953 µs (≈ 512,03 Hz, lệch +64 ppm so với danh định) | 16 | Word 24 bit: mẫu 18 bit bù hai `(k mod 2048) − 1024` ở bit 23…6, ETAG = PTAG = 0 |
| `0xF1`–`0xF3` | PPG giả, giống MAX30101 chế độ multi-LED 3 khe ở tốc độ V1 (200 sps) | 200 000 | 5 000 µs | 8 | `(k mod 4096) + 32 768 × s`, `s` = 1, 2, 3 theo khe |
| `0xA1`–`0xA6` | IMU giả, giống BMI270 cấu hình V1 (V0.2 mục 3): gia tốc X/Y/Z, con quay X/Y/Z | 100 000 | 10 000 µs; FIFO 170 frame, watermark 10 | 10 (tới 32 mỗi packet khi tồn đọng) | Int16 có dấu `((k · 257 + s · 8191) mod 65 536) − 32 768`, `s` = 0…5 theo trục; chạm cả hai biên −32 768 và 32 767 |
| `0xC1` | Nút t0 | 0 | — | 1 | Mã sự kiện `1` |
| `0xD1` | Thông tin thiết bị (V0.2 mục 6) | 0 | Một lần ngay sau khi driver USB khởi động, rồi mỗi 10 s | 25 | Layout 1, ELF SHA-256, `esp_app_desc_t.version`, `esp_app_desc_t.idf_ver` |

`DATA` là hàm của chỉ số mẫu, nên receiver kiểm được từng mẫu. Độ lệch +64 ppm của
ECG giả là cố ý: hồi quy tốc độ thực ở phép đo 10 phút phải thấy nó.

Nguồn giả ECG/PPG có FIFO 32 mẫu, IMU 170 frame. Task đọc **chốt** số mẫu đang
chờ, lấy `T_ANCHOR_US` ngay sau đó rồi đọc đúng số mẫu đã chốt (schema mục 5). FIFO
đầy thì mẫu mới bị mất như MAX3010x với `FIFO_ROLLOVER_EN = 0` hay BMI270 với
`fifo_stop_on_full = 1`.

## IMU giả (V0.2 bước 2b)

Sáu trục của một lần đọc dùng chung `FIRST_SAMPLE_INDEX`, `T_ANCHOR_US` và `STATUS`
(`imu_plan.c`):

- Lần đọc hơn 32 frame được chia thành các packet tối đa 32 frame; mọi phần dùng
  anchor của lần đọc, phần nào không chứa frame mới nhất thì bật bit 7 (V0.2 mục 4).
- Lần đọc gặp FIFO đầy (170 frame, không còn chỗ cho một frame nữa) bật bit 0 trên
  mọi packet. Lần đọc kế tiếp neo lại chỉ số bằng công thức V0.2 mục 5 từ lần đọc
  tin cậy gần nhất và bật bit 5 ở packet đầu tiên mỗi trục. Nếu lần đọc kế tiếp
  cũng đầy, hoặc chưa có lần đọc tin cậy, thì chỉ số chỉ tiếp tục (`+1`) và vẫn bật
  bit 5. Lần đọc lỗi (hàm `imu_index_read_failed`, dành cho driver thật) không gửi
  gì; lần sau bật bit 3 và bit 5.
- `DATA` theo chỉ số **thật**, nên neo lại sai sẽ lộ ra thành `DATA` không khớp
  `FIRST_SAMPLE_INDEX`. Số frame mất thật in ra UART0 làm đáp án (BMI270 không báo
  số này), cùng chỉ số đã neo lại và chỉ số thật.

Env `esp32s3_devkitc_imu_stall` (cờ `FAKE_IMU_STALLS=1`) cố ý dừng đọc IMU mỗi 30 s:
500 ms ở giây thứ 10 (khoảng 60 frame: hai packet mỗi trục, packet đầu có bit 7) và
2 500 ms ở giây thứ 20 (FIFO đầy, mất khoảng 90 frame: bit 0, lần sau neo lại với
bit 5). Bản mặc định không dừng đọc. Lần đọc đầy tạo 36 packet liền (6 phần × 6 trục),
vẫn dưới hàng đợi MCU 64 packet nhưng có thể đẩy packet ECG/PPG vào tràn hàng đợi nếu
USB chậm; khi đó bit 1 báo như thường.

## Quy ước packet của firmware

Trả lời các câu hỏi D trong [hướng dẫn logger](../docs/protocol/packet_logger.md):

| Câu | Quy ước |
| --- | --- |
| D1 | `CRC16` little-endian như các trường khác |
| D2 | `VERSION` luôn `0x02` từ 2026-10-24 (Packet Schema V0.2; bản firmware trước gửi `0x01`). Đổi layout hoặc ý nghĩa trường thì tăng `VERSION` cùng bản firmware mới; không trộn hai version trong một phiên |
| D3 | `SEQ` gán **lúc gửi**, khi lấy packet ra khỏi hàng đợi MCU. Thiếu `SEQ`: packet mất sau hàng đợi (USB không nhận trong 20 ms). Hàng đợi MCU đầy: packet bị bỏ trước khi có `SEQ`; packet kế của kênh đó bật bit 1 và có `FIRST_SAMPLE_INDEX` nhảy, `SEQ` vẫn liên tục. FIFO AFE tràn: bit 0 bật ở packet đọc lúc phát hiện, khoảng mất nằm sau mẫu cuối của packet đó, packet kế có `FIRST_SAMPLE_INDEX` nhảy. Nếu packet mang bit 0, 1 hoặc 5 bị bỏ ở hàng đợi, hoặc firmware gửi thất bại (driver USB không nhận đủ packet trong 20 ms), các bit đó chuyển sang packet gửi được kế tiếp của kênh (sửa 2026-10-23; trước đó chỉ chuyển bit 1 và chỉ khi gửi thất bại; bit 5 thêm 2026-10-24 theo V0.2 mục 5), để bước nhảy index vẫn có lời giải thích theo R2 và packet kế vẫn mở chuỗi mới. Packet đã vào bộ đệm driver mà sau đó mất trên đường USB thì firmware không biết, nên không chuyển bit; logger vẫn thấy khoảng `SEQ`. Firmware khung chưa sinh bit 5 |
| D4 | Bit 4 bật trên mọi packet ECG/PPG cho tới khi đo xong độ trễ hiệu dụng `L` của cấu hình; không bật trên `0xC1` |
| D5 | `SEQ` (riêng từng kênh) và `FIRST_SAMPLE_INDEX` bắt đầu từ 0 ở mỗi phiên. `SESSION_ID` là số ngẫu nhiên 32 bit lấy lúc khởi động. `0xD1`: `FIRST_SAMPLE_INDEX` là số thứ tự packet thông tin, đếm cả packet bị bỏ ở hàng đợi; `STATUS` = 0, có thể có bit 1 |
| D6 | `0xC1`: `SEQ` đếm riêng; `FIRST_SAMPLE_INDEX` = số thứ tự sự kiện trong phiên (0, 1, …); `FS_NOMINAL_MHZ` = 0; `T_ANCHOR_US` = `T_FIRST_US` = thời điểm cạnh xuống đầu tiên của nút |
| D7 | Không bao giờ gửi `SAMPLE_COUNT = 0` |
| D8 | Chờ bench |
| D9 | USB Serial/JTAG không có baud. Bộ đệm TX của driver 8 192 byte, hàng đợi MCU 64 packet, timeout ghi 20 ms. Firmware không ghi chữ ra cổng packet; lúc khởi động có thể có chữ của ROM và bootloader |
| D10 | Chờ phép đo 10 phút |

## Nút t0

GPIO4, tích cực mức thấp, có kéo lên trong chip (bo đế V1 có thêm 10 kΩ và
100 nF). Trên DevKitC trần: nối công tắc giữa GPIO4 và GND. Thời điểm sự kiện là
cạnh xuống đầu tiên; bỏ qua cạnh trong 200 ms sau đó, và chỉ nhận nếu nút vẫn
được giữ sau 20 ms (lọc dội khi nhả). `FIRST_SAMPLE_INDEX` của `0xC1` chỉ đếm sự
kiện đã qua lọc dội. Nếu hàng đợi của ISR (8 cạnh) đầy, cạnh đó bị bỏ trước khi lọc
dội nên không có số thứ tự; số cạnh bị bỏ đi kèm cạnh được xếp hàng kế tiếp, và
packet sự kiện gửi kế tiếp bật bit 1 (có thể đã mất một lần bấm, logger báo
`events_lost_before_send` với số lượng không xác định). Packet sự kiện bị bỏ ở hàng
đợi MCU thì đã có số thứ tự, nên logger đếm được số sự kiện mất.

## Kiểm tra khi có bo (chưa làm)

Đây là phần firmware của
[trình tự bring-up](../hardware/test_reports/v1_bringup_procedure.md) mục 2.

1. Nạp, mở UART0: thấy `packet self-test passed` và `SESSION_ID`.
2. Ghi cổng USB native trong 10 phút chạy không tải bằng logger:
   `python scripts/packet_logger.py record --port COMx --duration-s 600 --metadata ...`
   ([hướng dẫn](../docs/protocol/packet_logger.md)). Cổng được mở với DTR/RTS ở mức
   không kích hoạt; kiểm rằng mở cổng không làm chip khởi động lại (`SESSION_ID`
   trên UART0 không đổi).
3. Trong kết quả: `SEQ` và `T_ANCHOR_US` tăng đơn điệu, không lỗi CRC, `DATA` khớp
   công thức ở trên; `device_info` của phiên có ELF SHA-256 trùng log UART0 và
   khoảng 60 packet hợp lệ.
4. Nạp bản `esp32s3_devkitc_imu_stall`, ghi vài phút: mỗi 30 s logger thấy một lần
   đọc IMU có bit 7 và một lần đầy (bit 0) rồi neo lại (`sample_index_reanchored`
   mỗi trục), `DATA` vẫn khớp chỉ số; chỉ số neo lại trùng chỉ số thật in trên UART0.
5. Bấm t0 vài lần: có packet `0xC1` tương ứng.

## Chưa có

- Driver MAX30001, MAX30101, BMI270 (gồm phát hiện đầy theo độ dài FIFO thật và
  gọi `imu_index_read_failed` khi đọc lỗi).
- Xung `SAMP` của MAX30001 trên GPIO47 (INT2B) với MCPWM capture và bit 8 (V0.2
  bước 2c), PPG xóa ngắt mỗi mẫu và đọc hết FIFO (bước 2d).
- Packet sự kiện mã `3` (xung kích thích) cho phép đo 10 phút.
- Lệnh từ PC (bắt đầu/dừng, đổi cấu hình).
