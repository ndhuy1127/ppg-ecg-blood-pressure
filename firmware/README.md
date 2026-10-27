# Firmware

> **Trạng thái:** firmware khung V1-module gửi
> [Packet Schema V0.2](../configs/hardware/Packet_Schema_V0.2.md) từ 2026-10-24
> (bước 2a của mục 9: encoder V0.2, packet thông tin thiết bị `0xD1`, chuyển tiếp
> bit 5; bước 2b: IMU giả sáu trục, chia phần tồn đọng, neo lại sau FIFO đầy; bước
> 2c: mốc `SAMP` của ECG với bit 8, xung lấy từ nguồn ECG giả; bước 2d: PPG thức
> theo ngắt `PPG_RDY`, đọc hết FIFO khi có 8 mẫu). Build được (2026-10-24, RAM 4,9 %,
> flash 20,4 % của phân vùng 1 MB) nhưng **chưa chạy trên bo** (chưa có phần cứng).
> Bản build mặc định: mọi giá trị ECG/PPG/IMU và mọi xung `SAMP` là dữ liệu
> **giả**, chỉ để kiểm đường packet MCU → USB → logger, không phải tín hiệu sinh
> lý. MCPWM capture thật đã viết nhưng tắt và chưa chạy. Từ 2026-10-25 có driver
> MAX30001 (mục "Driver MAX30001"), bật bằng bản build `esp32s3_devkitc_ecg_real`;
> **chưa chạy trên chip**. Driver MAX30101 (mục "Driver MAX30101") bật bằng
> `esp32s3_devkitc_ppg_real`, cũng chưa chạy trên chip. Driver BMI270 (mục "Driver
> BMI270") bật bằng `esp32s3_devkitc_imu_real`, cũng chưa chạy trên chip.

- **app/**: `main.c` (task, hàng đợi, cổng USB, nút t0, thông tin thiết bị, đọc
  IMU, đọc ECG có mốc `SAMP`), `imu_plan.c` (chỉ số, `STATUS` và cách chia packet
  của một lần đọc FIFO BMI270 theo V0.2 mục 3–5; C thuần), `samp_map.c` (ánh xạ
  xung `SAMP` ↔ mẫu ECG, kiểm danh tính, chính sách khởi động lại; V0.2 mục 7.2–7.3;
  C thuần),
  `packet_wire.c` (encoder Packet Schema V0.2, đóng gói payload `0xD1` và phép tự
  kiểm lúc khởi động; C thuần, không phụ thuộc ESP-IDF; tên giống codec Python
  `software/data_io/packet_wire.py`, trước 2026-10-24 là `packet_v01.c`).
- **drivers/**: `max30001.c` (driver MAX30001 lõi, C thuần, không phụ thuộc
  ESP-IDF), `max30001_esp.c` (SPI và ngắt INTB trên ESP32-S3); `max30101.c` (driver
  MAX30101 lõi, C thuần), `max30101_esp.c` (I²C và ngắt INT); `bmi270.c` (driver
  BMI270 lõi, C thuần), `bmi270_config.c` (microcode 8 KB của Bosch, BSD-3-Clause,
  xem [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)), `bmi270_esp.c` (SPI có DMA
  và ngắt INT1);
  `fake_afe.c`, nguồn mẫu giả thay cho MAX30001/MAX30101/BMI270
  (FIFO có độ sâu cấu hình được, đầy thì giữ nội dung và bỏ mẫu mới; ECG giả phát
  xung `SAMP`); `samp_edges.c`, bộ đệm vòng 64 cạnh `SAMP`; `samp_capture.c`, MCPWM
  capture thật trên GPIO47 và quy đổi sang `esp_timer` (chưa chạy trên chip).
- **boards/**: `board_v1_module.h`, GPIO theo bảng A.7 của
  [custom_board_proposal.md](../configs/hardware/custom_board_proposal.md).
- **include/**: `packet_wire.h`, `imu_plan.h`, `samp_map.h`, `samp_edges.h`,
  `samp_capture.h`, `fake_afe.h`, `max30001.h`, `max30001_esp.h`, `packet_kat.h`
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
  giả"); [tests/test_firmware_samp_map.py](../tests/test_firmware_samp_map.py) làm
  vậy với `app/samp_map.c` (xem mục "Mốc `SAMP` của ECG").

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
pio run -d firmware -e esp32s3_devkitc_samp_faults    # build có lỗi xung SAMP giả (mục "Mốc SAMP")
pio run -d firmware -e esp32s3_devkitc_ppg_delay      # build có đọc PPG trễ (mục "Đọc PPG")
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
của ESP32-S3. **Chưa kiểm trên bo**: đọc nhãn in cạnh cổng khi nhận hàng. Không cần
đọc log UART0 để điền metadata phiên: phiên bản ứng dụng và ELF SHA-256 đi trong packet
`0xD1`, `SESSION_ID` trong mọi packet; `firmware_version` của metadata chỉ là phiên bản
ứng dụng ([packet_logger.md](../docs/protocol/packet_logger.md), mục Metadata phiên).

Khi khởi động, firmware kiểm encoder với `packet_kat.h` (`pkt_self_test`): CRC
`"123456789"` = `0x29B1`, `T_FIRST_US`, packet ECG mẫu 50 byte (packet mẫu V0.1 của
`tests/fixtures/packet_v3_expected.json` với `VERSION = 2` và `STATUS` bit 4, 8) và
packet thông tin thiết bị mẫu 142 byte. Sai thì không gửi packet nào và LED trạng
thái nháy nhanh. Known-answer V0.1 vẫn nằm trong fixture làm bản cũ.

## Luồng dữ liệu giả

| `CHANNEL_ID` | Nguồn | `FS_NOMINAL_MHZ` | Chu kỳ thật | N mỗi packet | `DATA[i]` với `k = FIRST_SAMPLE_INDEX + i` |
| --- | --- | ---: | --- | ---: | --- |
| `0xE1` | ECG giả, giống MAX30001, kèm một xung `SAMP` mỗi mẫu | 512 000 | 1 953 µs (≈ 512,03 Hz, lệch +64 ppm so với danh định) | 16 | Word 24 bit: mẫu 18 bit bù hai `(k mod 2048) − 1024` ở bit 23…6, ETAG = PTAG = 0 |
| `0xF1`–`0xF3` | PPG giả, giống MAX30101 chế độ multi-LED 3 khe ở tốc độ V1 (200 sps), báo ngắt mỗi mẫu như `PPG_RDY` | 200 000 | 5 000 µs | 8 (nhiều hơn khi đọc trễ) | `(k mod 4096) + 32 768 × s`, `s` = 1, 2, 3 theo khe |
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

## Đọc PPG (V0.2 bước 2d)

`PPG_RDY` giữ chân INT ở mức thấp tới khi đọc `Interrupt Status 1` (0x00), và mẫu
đến khi cờ chưa xóa không tạo cạnh mới, nên driver phải đọc 0x00 sau **mỗi** ngắt
(spec mục 7.6). Driver MAX30101 thật làm việc này: `max30101_latch` đọc 0x00 ở mỗi
lần thức dậy, trước khi đọc con trỏ FIFO (có từ 2026-10-25, chưa chạy trên chip).
Nguồn giả chỉ báo đúng một lần cho mỗi mẫu được lưu, không mô phỏng chân INT giữ mức
thấp. Ngắt chỉ đánh thức
task; số mẫu đang chờ lấy từ con trỏ FIFO (`fake_afe_waiting`), không từ số ngắt
đã đếm, nên ngắt bị nuốt hay ngắt còn tồn sau một lần đọc trễ không làm lệch các lần
đọc sau. Khi có 8 mẫu thì chốt con trỏ, lấy `T_ANCHOR_US` và đọc **hết** số mẫu có
trong FIFO lúc chốt (thường 8, nhiều hơn nếu đọc trễ), không cố định 8.

Nếu bring-up cho thấy `PPG_RDY` không chạy ở chế độ ba khe, đặt
`BOARD_PPG_READ_PERIOD_MS` (trong `board_v1_module.h`, ví dụ 40) để đọc theo timer:
vẫn đọc hết FIFO, nhưng mốc có thể muộn tới một chu kỳ PPG (5 ms) và cần hồi quy
offline. Env `esp32s3_devkitc_ppg_delay` (cờ `FAKE_PPG_DELAY=1`) cứ mỗi 10 s cho task
PPG chờ 12 ms trước khi chốt, nên lần đọc đó có khoảng 10 mẫu.

## Mốc `SAMP` của ECG (V0.2 bước 2c)

Mỗi mẫu ECG có một cạnh `SAMP`. Callback capture (hoặc nguồn ECG giả) chỉ ghi giá
trị đã chốt vào bộ đệm vòng 64 mục (`samp_edges.c`); số cạnh `e` đếm từ 0 sau mỗi
lần khởi động ánh xạ, và mỗi ô giữ `e` của nó, nên cạnh chưa tới hoặc đã bị ghi đè
không tra được. Task đọc ECG (`ecg_reader_task`):

1. Chốt FIFO và ghi mốc đọc FIFO như V0.1.
2. Chờ tối đa hai chu kỳ mẫu cho cạnh của mẫu cuối packet (`e = k_last`).
3. `samp_map_packet` kiểm mọi cạnh từ cạnh của mẫu cuối packet trước (cạnh 0 với
   packet đầu của kỷ nguyên) tới cạnh `k_last`: phải có đủ, mọi khoảng cách nằm trong
   1 953,125 µs ± 22 µs (tạm), và cạnh `k_last` không muộn hơn mốc đọc FIFO cộng hai
   chu kỳ. Đạt thì `T_ANCHOR_US` là thời điểm cạnh đó và bật bit 8; không đạt (thiếu
   cạnh, cạnh tới muộn, khoảng quá ngắn: xung thừa, quá dài: xung mất hoặc giá trị
   chốt bị ghi đè, chỉ số không liền, FIFO tràn) thì chuyển `LỖI`, dùng mốc đọc FIFO,
   không bit 8.
4. Ở `LỖI` 1 s (và cách lần khởi động lại trước ít nhất 10 s, chốt 2026-10-24) thì
   khởi động lại ánh xạ: dừng chuyển đổi, xóa bộ đệm vòng, `SYNCH` (với nguồn giả:
   chạy lại đồng hồ mẫu), chỉ số mẫu và số cạnh về 0, packet kế bật bit 5. Với nguồn
   giả, `esp_timer_stop` không chờ callback đã phát; `fake_afe_stop` đặt một timer
   một lần trên cùng task esp_timer và chờ nó chạy (task chạy callback lần lượt), nên
   khi hàm trả về thì không còn cạnh nào của kỷ nguyên cũ lọt vào bộ đệm vừa xóa.
   Gốc thời gian của nguồn giả lấy giữa hai lần đọc `esp_timer` kẹp lời gọi khởi
   động timer.

Nguồn ECG giả đặt cạnh ở thời điểm báo thức lý tưởng của mẫu cộng sai số 0–3 µs (như
sai số capture). Env `esp32s3_devkitc_samp_faults` (cờ `FAKE_SAMP_FAULTS=1`) cứ mỗi
20 s bỏ một cạnh (giây thứ 5: như xung mất hoặc bị ghi đè) và thêm một cạnh giả nửa
chu kỳ trước một cạnh thật (giây thứ 15: như xung thừa).

UART0 in mỗi 10 s: trạng thái ánh xạ, số packet có bit 8 và dùng mốc đọc FIFO, số
lần vào `LỖI` theo nguyên nhân (xung mất hoặc bị ghi đè không phân biệt được: đều là
một khoảng cỡ hai chu kỳ), số lần khởi động lại.

**MCPWM capture thật** (`samp_capture.c`, bật bằng `BOARD_SAMP_CAPTURE=1` trong
`board_v1_module.h`; cực tính cạnh `BOARD_SAMP_RISING_EDGE`, tạm cạnh xuống):
**chưa chạy trên chip**. Kênh capture chốt bộ đếm MCPWM (80 MHz) tại cạnh GPIO47;
kênh thứ hai không nối GPIO được chốt bằng phần mềm giữa hai lần đọc `esp_timer`
(cặp kẹp, chỉ nhận khi hai lần đọc cách nhau dưới 2 µs) mỗi 100 ms; giá trị capture
quy đổi theo tỉ lệ danh định từ cặp gần nhất (hai đồng hồ cùng thạch anh; spec mục
7.1), chỉ khi cặp đó chưa quá 1 s, nếu không thì cạnh coi như thiếu. UART0 in số cặp
nhận, bị loại, sai số quy đổi lớn nhất và số lần từ chối quy đổi vì không có cặp
mới. `CONFIG_MCPWM_ISR_CACHE_SAFE=y`
trong `sdkconfig.defaults`. Khi có MAX30001 thật thì driver làm phần dừng, xóa và
`SYNCH` thay cho nguồn giả.

## Quy ước packet của firmware

Trả lời các câu hỏi D trong [hướng dẫn logger](../docs/protocol/packet_logger.md):

| Câu | Quy ước |
| --- | --- |
| D1 | `CRC16` little-endian như các trường khác |
| D2 | `VERSION` luôn `0x02` từ 2026-10-24 (Packet Schema V0.2; bản firmware trước gửi `0x01`). Đổi layout hoặc ý nghĩa trường thì tăng `VERSION` cùng bản firmware mới; không trộn hai version trong một phiên |
| D3 | `SEQ` gán **lúc gửi**, khi lấy packet ra khỏi hàng đợi MCU. Thiếu `SEQ`: packet mất sau hàng đợi (USB không nhận trong 20 ms). Hàng đợi MCU đầy: packet bị bỏ trước khi có `SEQ`; packet kế của kênh đó bật bit 1 và có `FIRST_SAMPLE_INDEX` nhảy, `SEQ` vẫn liên tục. FIFO AFE tràn: bit 0 bật ở packet đọc lúc phát hiện, khoảng mất nằm sau mẫu cuối của packet đó, packet kế có `FIRST_SAMPLE_INDEX` nhảy. Nếu packet mang bit 0, 1 hoặc 5 bị bỏ ở hàng đợi, hoặc firmware gửi thất bại (driver USB không nhận đủ packet trong 20 ms), các bit đó chuyển sang packet gửi được kế tiếp của kênh (sửa 2026-10-23; trước đó chỉ chuyển bit 1 và chỉ khi gửi thất bại; bit 5 thêm 2026-10-24 theo V0.2 mục 5), để bước nhảy index vẫn có lời giải thích theo R2 và packet kế vẫn mở chuỗi mới. Packet đã vào bộ đệm driver mà sau đó mất trên đường USB thì firmware không biết, nên không chuyển bit; logger vẫn thấy khoảng `SEQ`. Firmware sinh bit 5 khi neo lại (ECG khởi động lại, IMU và PPG đọc lại; các mục dưới) |
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

## Xung kích thích đồng bộ, sự kiện mã 3 (2026-10-25, chưa chạy trên chip)

Cho phép đo đồng bộ 10 phút
([sync_10min_test_plan.md](../hardware/test_reports/sync_10min_test_plan.md) mục
3–4). Bật bằng `BOARD_STIM=1`; bản build `esp32s3_devkitc_sync10` bật cùng lúc ba chip
thật, capture `SAMP` có bit 8 (`BOARD_SAMP_VERIFIED=1`) và xung. Chỉ nạp bản này sau
khi bring-up mục 7 đã xác nhận cạnh `SAMP` khớp mẫu đầu tiên của FIFO.

- GPIO6 (J3 chân 1) lên mức cao 2 s sau khi khởi động, rồi cứ 1 s cộng độ lệch đều
  trong [0; 1 953) µs (một chu kỳ mẫu ECG), xuống sau 50 ms. Hai one-shot
  `esp_timer`; lịch theo thời điểm đích nên trễ callback không cộng dồn.
- Mỗi cạnh lên thành packet sự kiện `0xC1` mã `3`; `T_ANCHOR_US` = `esp_timer` ngay sau
  khi đặt chân lên cao. Không lọc dội (cạnh do MCU tạo); số thứ tự sự kiện đếm chung
  với nút t0; mất ở hàng đợi thì packet sự kiện sau có bit 1, như t0.
- Seed của dãy độ lệch là `SESSION_ID` (`stim_plan.c`, xorshift32): mỗi lần khởi
  động một dãy mới, tái lập được từ chính luồng dữ liệu.
- **Test** [tests/test_firmware_stim_plan.py](../tests/test_firmware_stim_plan.py):
  dãy khoảng cách khớp một xorshift32 viết độc lập bằng Python, luôn trong
  [1 s; 1 s + 1 953 µs), và pha của 600 cạnh phủ đều chu kỳ mẫu ECG. Phần GPIO và
  `esp_timer` trong `main.c` chỉ kiểm bằng build.

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
   Bản mặc định: mọi packet ECG có bit 8, logger không báo gì về `SAMP`. Bản
   `esp32s3_devkitc_samp_faults`: mỗi lỗi giả cho khoảng 32 packet ECG không bit 8 rồi
   một lần neo lại (bit 5), không có `timestamp_anomaly` hay
   `samp_resumed_without_reanchor`. Bản `esp32s3_devkitc_ppg_delay`: mỗi 10 s một
   packet PPG mỗi khe có khoảng 10 mẫu, logger không báo gì.
5. Bấm t0 vài lần: có packet `0xC1` tương ứng.

## Driver MAX30001 (2026-10-25, chưa chạy trên chip)

Bật bằng `pio run -d firmware -e esp32s3_devkitc_ecg_real` (`BOARD_ECG_REAL=1`,
`BOARD_SAMP_CAPTURE=1`); PPG và IMU vẫn là nguồn giả. Dùng ở bring-up mục 7, khi
breakout đã cắm vào bo đế.

- **Cấu hình** (`max30001_v1_regs`, theo A.2 của
  [custom_board_proposal.md](../configs/hardware/custom_board_proposal.md), chốt
  2026-10-23 tới 2026-10-25):
  - 512 sps (`FMSTR 00`); gain 20 V/V; `ECG_DLPF` 40,96 Hz; tắt `ECG_DHPF`;
  - lead-off DC 10 nA, VMID ± 400 mV; fast recovery tự động; tắt lead bias nội;
  - BioZ, PACE và bộ dò R của chip đều tắt;
  - INTB = `EINT` (`EFIT = 15`), INT2B = `SAMP` mỗi mẫu, tự xóa; cả hai ra CMOS.

  Giá trị từng thanh ghi và trang datasheet ghi trong `max30001.c`. Khi khởi động:
  reset mềm, bỏ lần đọc đầu (datasheet tr. 47), kiểm `INFO`, ghi rồi đọc lại từng
  thanh ghi (bỏ các bit không dùng), chờ PLL khóa (hai lần đọc `STATUS` liên tiếp
  không có `PLLINT`, tối đa 1 s).
- **Bắt đầu bản ghi** (`max30001_restart`): tắt `SAMP` trên INT2B, xóa bộ đệm cạnh và
  khởi động lại ánh xạ, gửi `SYNCH`, bật lại `SAMP`. Trình tự này **chưa đảm bảo**
  cạnh đầu tiên sau `SYNCH` là của mẫu FIFO đầu tiên. Tắt `SAMP` chỉ chặn đường ra,
  không dừng chuyển đổi (tr. 43). Chuyển đổi chạy lại từ cạnh clock kế sau `SYNCH`
  (tr. 46), và lệnh bật lại `SAMP` là một giao dịch SPI có thể bị chen ngang. Nếu
  lỡ cạnh đầu thì mọi mốc lệch cố định một mẫu, và phép kiểm khoảng cách không phát
  hiện được (Codex review 2026-10-25). Vì vậy **bit 8 tắt** cho tới khi bring-up
  xác nhận trên chip thật và build với `BOARD_SAMP_VERIFIED=1`:
  - ánh xạ vẫn chạy;
  - log UART0 in khoảng (thời điểm đọc FIFO − cạnh `SAMP` của mẫu cuối packet),
    chỉ tính các lần đọc kết thúc ở EOF;
  - khớp đúng thì khoảng này nằm trong 0 tới khoảng một chu kỳ mẫu cộng thời gian
    đọc; lệch một mẫu thì cả khoảng dịch đi 1,953 ms.

  Chỉ một lần `SYNCH` thành công mới mở bản ghi mới (chỉ số về 0, bit 5). Các cờ
  chưa kịp gửi (bit 0, 2, 3) được giữ sang packet đầu của bản ghi mới. Lỗi thì giữ
  chỉ số, neo lại theo thời gian (bit 3 và bit 5) và giữ ánh xạ ở `LỖI`.
- **Khởi động lỗi** (`INFO`, đọc lại, PLL hay `SYNCH`): `max30001_start` được thử tối
  đa 10 lần cách nhau 100 ms (`AFE_START_TRIES`, `AFE_START_RETRY_MS`, chung cho cả ba
  chip, chốt 2026-10-25; mỗi lần bắt đầu bằng reset chip); vẫn lỗi thì ghi
  `EN_INT = 0`, gỡ ngắt INTB, rồi **tạm dừng** task chứ không xóa. Logger thấy kênh
  không có packet nào (`channel_missing` nếu metadata khai báo). Một ngắt INTB đang chạy ở lõi kia vẫn
  có thể báo vào task, nên handle phải còn hợp lệ.
- **Kiểm sức khỏe khi đang chạy (2026-10-25):** mỗi 1 s, bất kể INTB, `max30001_check`
  đọc `INFO` và đọc lại 8 thanh ghi cấu hình (cùng mặt nạ như lúc khởi động). Quá
  40 ms không có mẫu thì vẫn đọc FIFO (INTB kẹt mức cao; FIFO 32 mẫu chỉ chứa 62,5 ms ở
  512 sps); quá 2 s không có mẫu thì coi
  là chip im lặng. Kiểm lỗi hay chip im lặng: khởi động lại (reset, cấu hình, PLL,
  `SYNCH`) mỗi 100 ms tới khi được, không gửi packet trong lúc đó; chỉ số bắt đầu lại từ
  0 với bit 5 và `0xD2` báo thế hệ mới. Trước đó, chip bị reset do sụt nguồn nằm im
  với INTB mức cao và ECG dừng mà không ai biết. Khi tới lúc khởi động lại ánh xạ
  `SAMP`, vòng đó luôn đọc FIFO trước rồi mới `SYNCH` (`SYNCH` xóa FIFO, nên không bỏ
  mất khoảng 16 mẫu còn trong đó; sửa 2026-10-25). Các quyết định thời điểm nằm trong
  `app/ecg_loop.c` (C thuần), test bằng
  [tests/test_firmware_ecg_loop.py](../tests/test_firmware_ecg_loop.py).
- **Đọc FIFO** (`max30001_read_fifo`):
  - đọc burst `0x20` trong **một** khung CS (CS điều khiển bằng GPIO), dừng ở word EOF
    (`010`/`011`), word rỗng (`110`), word tràn (`111`), tag không dùng (`10x`) hoặc
    32 word; không bao giờ đọc quá word EOF (tr. 64);
  - mốc đọc FIFO lấy ngay sau word EOF (V0.1 mục 5.2);
  - `DATA` là nguyên word 24 bit, giữ ETAG/PTAG (V0.1 mục 8).
- **Mỗi lần đọc** (task `ecg_reader` trong `main.c`):
  - Thức theo cạnh xuống của INTB. Cứ 10 ms nếu INTB vẫn ở mức thấp thì đọc luôn, phòng
    khi lỡ cạnh; sau ngưỡng `EFIT` FIFO chỉ còn khoảng 31 ms trống.
  - Đọc FIFO, lấy mốc, đọc `STATUS`. Quyết định do `ecg_read_plan` (`app/ecg_read.c`,
    C thuần) đưa ra:
    - `DCLOFFINT` → bit 2; mất khóa PLL → bit 3 và ánh xạ `LỖI`. Hai cờ này được giữ
      tới packet kế tiếp được gửi, kể cả qua các lần đọc rỗng.
    - Tràn (`111` hoặc `EOVF`): dữ liệu hỏng (tr. 41, 64–65), nên **bỏ cả lần đọc**,
      gửi `FIFO_RST`, packet kế tiếp neo lại theo thời gian với bit 0 và bit 5 (V0.1
      mục 9).
    - Tag lạ (`10x`) hoặc đọc SPI lỗi: không gửi gì, packet kế tiếp có bit 3 và bit 5
      (tag lạ thì gửi thêm `FIFO_RST`; tag lạ cùng lúc với `EOVF` vẫn giữ bit 0).
    - Nguyên nhân lỗi ánh xạ được đếm riêng trong log: tràn FIFO, chỉ số neo lại,
      lỗi AFE (SPI, PLL, `SYNCH` hay `FIFO_RST` thất bại; `SAMP_AFE`).
    - Đọc đủ 32 word mà không gặp EOF: mẫu vẫn hợp lệ nhưng mốc đọc FIFO không còn
      giới hạn sai số, nên gửi như lần đọc FIFO đầy (bit 0), packet kế neo lại
      (bit 5).
    - Chỉ số theo `imu_plan_read`. Mọi lần neo lại theo thời gian đều chuyển ánh xạ
      `SAMP` sang `LỖI`, rồi khởi động lại bằng `SYNCH` theo chính sách 1 s / 10 s.
- **Tự kiểm không cần người** (`max30001_cal_regs`): nguồn hiệu chuẩn nội lưỡng cực
  0,5 mV, 1 Hz vào hai đầu vào đã ngắt khỏi chân, lead-off tắt (tr. 50–51). Chưa nối
  vào lệnh nào; dùng ở bring-up.
- **Test** [tests/test_firmware_ecg_read.py](../tests/test_firmware_ecg_read.py):
  biên dịch `app/ecg_read.c` (cùng `imu_plan.c`, `packet_wire.c`) và kiểm các quy tắc
  trên với đáp án lấy từ Packet Schema (gồm công thức neo lại của V0.2 mục 5).
  Không chạy task, SPI hay chip.
- **Test** [tests/test_firmware_max30001.py](../tests/test_firmware_max30001.py):
  biên dịch `drivers/max30001.c` trên máy tính và chạy với một MAX30001 mô phỏng
  (khung SPI 32 clock, lệnh = địa chỉ << 1 | R/W, ghi thực thi ở clock 32, lần đọc
  đầu sau reset không hợp lệ, `PLLINT` chốt, FIFO burst).
  - Các word thanh ghi so với giá trị tính tay từ bảng thanh ghi tr. 43–53.
  - Kiểm: thứ tự khởi động, từ chối `INFO` sai, đọc lại sai, PLL không khóa, dừng
    đúng ở EOF và không đọc thêm, các tag rỗng/tràn/fast/lạ, thứ tự `SYNCH`.
  - Mô phỏng do chính dự án viết, nên không bắt được chi tiết datasheet mà cả hai
    cùng hiểu sai; chip thật kiểm ở bring-up mục 7.
- Chưa có: đo độ trễ hiệu dụng `L` (bit 4 vẫn bật), lệnh chạy tự kiểm từ PC, ghi
  cấu hình thanh ghi vào metadata phiên.

## Driver MAX30101 (2026-10-25, chưa chạy trên chip)

Bật bằng `pio run -d firmware -e esp32s3_devkitc_ppg_real` (`BOARD_PPG_REAL=1`); ECG
và IMU vẫn là nguồn giả. Dùng ở bring-up mục 8. Datasheet MAX30101 19-8453 Rev 2
(bản do SparkFun lưu, SHA-256
`f86d26404be5ab1ee9a0b149a9244f102cee039cdd5efca63f60b706418371a1`).

- **Cấu hình** (`max30101_v1_regs`, theo A.3 của
  [custom_board_proposal.md](../configs/hardware/custom_board_proposal.md), chốt
  2026-10-24/25):
  - multi-LED: `SLOT1` xanh, `SLOT2` đỏ, `SLOT3` IR; 200 sps; `SMP_AVE = 1`;
  - FIFO không ghi đè khi đầy; dải ADC 16 384 nA;
  - độ rộng xung 411 µs (18 bit). Đổi bằng `-DBOARD_PPG_LED_PW_US=215`; giá trị cuối
    chọn ở bring-up;
  - ngắt `PPG_RDY` và `ALC_OVF`.

  Dòng LED mặc định 7,2 mA mỗi màu, chỉ là điểm xuất phát: đỏ và IR mã `0x24`; xanh
  mã `0x12` cho mỗi nhánh vì khe `011` bật cùng lúc LED3 và LED4 (tr. 22), tổng
  7,2 mA. `max30101_set_currents` nhận mã **mỗi nhánh** xanh. Dòng LED hiệu chuẩn theo
  người (protocol v0.2 mục 6.1) bằng lệnh `SET_PPG_LED` từ PC (mục "Cấu hình AFE `0xD2`
  và lệnh từ PC" dưới đây). Khi khởi động: `RESET` rồi chờ tự xóa, kiểm `PART_ID =
  0x15`, xóa cờ ngắt, ghi rồi đọc lại cấu hình, xóa ba con trỏ FIFO, vào chế độ
  multi-LED **sau cùng** (datasheet tr. 15–19). Lỗi thì thử lại tối đa 10 lần cách
  nhau 100 ms như MAX30001, rồi mới dừng task.
- **Mỗi lần đọc** (task `ppg_reader` trong `main.c`, V0.2 mục 7.6):
  - Thức theo cạnh xuống của INT, và cứ 10 ms không có cạnh nào thì vẫn xem FIFO, bất
    kể INT ở mức nào (INT kẹt, hoặc FIFO đầy đúng 32 mẫu: chip không lưu thêm mẫu
    nên có thể không có `PPG_RDY` mới). Ở chế độ đọc theo timer
    (`BOARD_PPG_READ_PERIOD_MS > 0`) thì xem FIFO mỗi chu kỳ timer, không theo INT.
  - Đọc `Interrupt Status 1` (xóa `PPG_RDY`), rồi ba con trỏ FIFO trong một lượt; lấy
    `T_ANCHOR_US` ngay sau lượt đó (V0.1 mục 5.1). Cờ của `Status 1` đã đọc (nên đã
    xóa) vẫn được xử lý dù lượt đọc con trỏ sau đó lỗi.
  - Khi có ít nhất 8 mẫu (hay bất kỳ, nếu đọc theo timer) thì đọc **mọi** mẫu có lúc
    chốt trong một lượt `FIFO_DATA`.
  - `ppg_read_plan` (`app/ppg_read.c`, C thuần) quyết định:
    - FIFO đầy (32 mẫu): bit 0, lần sau neo lại theo thời gian với bit 5, không dùng
      `OVF_COUNTER` (V0.2 mục 7.6, sửa 2026-10-25);
    - `ALC_OVF` → bit 6, giữ tới packet kế tiếp được gửi;
    - lỗi I²C bất kỳ → không gửi gì, lần sau có bit 3 và bit 5;
    - cấu hình lại chip (`max30101_start`, gồm `RESET`) khi: `PWR_RDY` giữa chừng (sụt
      nguồn, chip đã tự reset); đọc `Status 1` lỗi (lượt đọc hỏng có thể đã xóa
      `PWR_RDY`); đọc `FIFO_DATA` lỗi (chip đã lấy ra một phần mẫu; thêm bit 0 nếu
      FIFO lúc đó đầy). Thử lại mỗi 100 ms tới khi thành công, **không** gửi packet
      nào trong lúc đó. Chỉ lỗi đọc con trỏ thì không cần cấu hình lại.

    Chỉ dùng con trỏ thì FIFO đầy đúng 32 mẫu mà chưa mất mẫu nào trông như rỗng;
    một mẫu sau nó hiện ra là đầy (`OVF_COUNTER = 1`), và lần xem kế tiếp sẽ thấy.
  - Ba khe của một lần đọc dùng chung `FIRST_SAMPLE_INDEX`, `T_ANCHOR_US` và
    `STATUS`; `DATA` là số đếm ADC 18 bit.
- **Nhiệt độ trong chip, kênh `0xB1`** (Packet Schema V0.2 mục 11, chốt 2026-10-25):
  - đo mỗi 1 s, mỗi packet một giá trị `TINT × 16 + TFRAC` (1/16 °C, có dấu), trong
    task `ppg_reader` (cùng bus I²C) ở mọi vòng lặp, kể cả vòng không gửi PPG;
  - máy trạng thái `app/die_temp.c` (C thuần): nhịp k ở t₀ + k s theo `esp_timer`
    (t₀ giữ qua reset chip), `FIRST_SAMPLE_INDEX` = k; chỉ bắt đầu đo trong 50 ms sau
    nhịp (muộn hơn thì bỏ nhịp đó); không bao giờ hai lần đo chồng nhau; kết quả phải
    đọc xong trước nhịp + 100 ms, nếu không thì bỏ. Đọc theo timer thì
    `BOARD_PPG_READ_PERIOD_MS` tối đa 40 (lớn hơn thì không build);
  - `T_ANCHOR_US` = `T_FIRST_US` = ngay sau khi đọc ra; không bật bit 4, không dùng
    bit 0/5 (mọi khoảng trống biết độ dài); bit 3 trên packet sau một lần đo lỗi,
    quá hạn hay reset chip. `die_temp_abort` được gọi **trước** mọi lần cấu hình lại:
    sau `RESET`, `TEMP_EN` đọc ra 0 và thanh ghi nhiệt độ về 0, trông như có kết quả.
    `max30101_temp_read` đọc thêm `MODE_CONFIG` sau `TINT`/`TFRAC` để bắt sụt nguồn
    giữa lần đọc `Status 1` và lần đọc nhiệt độ (`MAX30101_ERR_MODE`);
  - env `ppg_real` chỉ gửi giá trị đọc từ chip, không bao giờ thay bằng giá trị giả.
    Env toàn nguồn giả gửi 25 °C cộng răng cưa 1/16 °C (chuyển đổi giả 29 ms) qua cùng
    máy trạng thái; dữ liệu đó là `SYNTHETIC`.
- **Test** [tests/test_firmware_die_temp.py](../tests/test_firmware_die_temp.py):
  `app/die_temp.c` trên máy tính (lưới nhịp, đo trễ, quá hạn, lỗi, reset chip).
- **Test** [tests/test_firmware_max30101.py](../tests/test_firmware_max30101.py):
  biên dịch `drivers/max30101.c` và `app/ppg_read.c`, chạy với một MAX30101 mô
  phỏng:
  - đọc/ghi tự tăng địa chỉ, riêng `FIFO_DATA` không tăng;
  - `RESET` tự xóa; cờ ngắt xóa khi đọc; `TEMP_EN` tự xóa.

  Các byte thanh ghi so với giá trị tính tay từ bảng tr. 11–23. Mô phỏng do dự án
  viết, nên chip thật kiểm ở bring-up mục 8.

## Driver BMI270 (2026-10-25, chưa chạy trên chip)

Bật bằng `pio run -d firmware -e esp32s3_devkitc_imu_real` (`BOARD_IMU_REAL=1`); ECG
và PPG vẫn là nguồn giả. Dùng ở bring-up mục 8, bước 5. Datasheet BMI270
BST-BMI270-DS000-08 rev 1.6 (3/2026, SHA-256
`f68ce3c74f011a80bbe4b0279c4abe9609a71a5dcda75a951381d77112e005fb`).

- **Bus:** SPI bus 2 của V1-module (GPIO10 CS phần cứng, 11 MOSI, 12 SCK, 13 MISO),
  `SPI3_HOST` có DMA nên đọc 170 frame trong một giao dịch, chế độ 0, 1 MHz
  (`BOARD_IMU_SPI_HZ`, lên 2 MHz sau khi đo scope). Chip khởi động ở I²C; cạnh lên
  của CSB chuyển sang SPI sau 200 µs, lại như vậy sau soft reset; mỗi lần đọc có
  một byte giả trước dữ liệu (datasheet mục 6.3–6.4). Sau mỗi lần ghi chờ 450 µs,
  sau mỗi lần đọc 2 µs (Table 19).
- **Khởi động** (`bmi270_start`): đọc giả để chuyển SPI, soft reset, đọc giả lần
  nữa, kiểm `CHIP_ID = 0x24`; tắt advanced power save, tải microcode 8 KB của Bosch
  vào `INIT_DATA` theo 32 lượt 256 byte (`INIT_ADDR` = offset / 2), `INIT_CTRL = 1`,
  chờ `INTERNAL_STATUS = init_ok` (mục 4.4); ghi cấu hình, đọc lại, kiểm
  `EVENT.error_code`; bật cảm biến, chờ 80 ms cho con quay khởi động (45 ms điển
  hình) rồi xóa FIFO. Lần khởi động đầu thử tối đa 10 lần cách nhau 100 ms rồi mới
  bỏ (không có packet IMU). Ngắt INT1 chỉ bật khi chip đã cấu hình xong (sau reset
  INT1 không được lái; GPIO14 có pull-down): kiểu ngắt để `GPIO_INTR_DISABLE` tới
  lúc đó, vì `gpio_isr_handler_add` của ESP-IDF tự bật lại ngắt của chân.
- **Cấu hình V1** (`bmi270_v1_regs`, Packet Schema V0.2 mục 3, giá trị chốt
  2026-10-25): `ACC_CONF` 0xA8, `ACC_RANGE` 0x01 (±4 g), `GYR_CONF` 0xE8 (lọc và
  nhiễu ở chế độ hiệu năng), `GYR_RANGE` 0x02 (±500 °/s), `FIFO_DOWNS` 0x88, watermark
  120 byte (10 frame), `FIFO_CONFIG_0` 0x01 (dừng khi đầy, không frame sensortime),
  `FIFO_CONFIG_1` 0xC0 (con quay và gia tốc, không header), `INT1_IO_CTRL` 0x0A
  (push-pull, mức cao), `INT_LATCH` 0 (không chốt), `INT_MAP_DATA` 0x02 (watermark lên
  INT1), `PWR_CONF` 0x02, `PWR_CTRL` 0x06 (không bật cảm biến nhiệt của BMI270).
- **Mỗi lần đọc** (task `imu_reader` trong `main.c`, V0.2 mục 3–5):
  - Thức theo cạnh lên của INT1, và cứ 20 ms không có cạnh thì vẫn xem FIFO (INT1
    không chốt, giữ mức cao khi FIFO còn trên watermark nên đọc trễ không có cạnh
    mới).
  - Đọc `FIFO_LENGTH`, lấy `T_ANCHOR_US` ngay sau đó; khi có ít nhất 10 frame (hoặc
    FIFO đầy) đọc **đúng** số frame đã chốt trong một lượt `FIFO_DATA`; frame đến sau
    nằm lại cho lần sau (frame đọc trọn mới bị xóa, mục 4.7.2). Độ dài không phải
    bội của 12 hay lớn hơn 2 040 byte (MISO treo mức cao đọc ra 0x3FFF) không phải
    mức FIFO, vì FIFO không header chỉ chứa frame trọn và bộ đếm nhảy theo frame
    trọn (mục 4.7.1, 5.2.36): lần đọc hỏng và kiểm sức khỏe chip ở lần thức kế
    tiếp (trong 20 ms).
  - Lượt đọc frame lỗi có thể đã lấy ra một phần frame: xóa FIFO (`CMD` 0xB0) trước
    khi đọc tiếp, để frame còn lại từ trước khoảng mất không nằm chung lượt với frame
    sau nó; giữ bit 0 nếu FIFO lúc đó đầy. Xóa cũng lỗi thì khởi động lại chip (bước
    khởi động kết thúc bằng xóa FIFO).
  - FIFO coi là đầy khi còn dưới 21 byte trống: khi dừng lúc đầy, chip có thể bỏ
    frame mới nhất lúc chỗ trống nhỏ hơn frame lớn nhất (mục 4.7.2); 21 byte là frame
    lớn nhất mọi chế độ (1 + 8 + 6 + 6), nên cờ là bảo thủ (V0.2 mục 5).
  - `imu_plan_read` cho chỉ số, các phần tối đa 32 frame (bit 7), bit 0 khi đầy và
    neo lại sau đó (bit 5); đọc lỗi thì không gửi, lần sau neo lại (bit 3 và 5).
  - Frame không header 12 byte: con quay X, Y, Z rồi gia tốc X, Y, Z, byte thấp trước
    (mục 4.7.1); packet `0xA1`–`0xA6` là gia tốc X, Y, Z rồi con quay X, Y, Z.
- **Kiểm sức khỏe** mỗi 1 s (`bmi270_check`): `CHIP_ID`, `EVENT.por_detected` (bật
  sau mỗi lần reset, khởi động đã xóa nó), `ERR_REG.fatal_err`, `INTERNAL_STATUS` và
  đọc lại cấu hình. Sai thì khởi động lại chip, thử lại mỗi 100 ms tới khi được,
  **không** gửi packet trong lúc đó; packet đầu sau đó neo lại (bit 3 và 5). Sụt
  nguồn làm BMI270 về I²C và chưa khởi tạo, không còn dữ liệu, nên chỉ kiểm này bắt
  được.
- **Test** [tests/test_firmware_bmi270.py](../tests/test_firmware_bmi270.py): biên
  dịch `drivers/bmi270.c` với microcode, chạy với một BMI270 mô phỏng ở mức SPI thô
  (chuyển I²C → SPI, byte giả, soft reset, `INIT_ADDR`/`INIT_DATA`, FIFO lấy ra từng
  frame trọn và gửi lại frame đọc dở, lỗi bus trước hoặc sau khi đã lấy dữ liệu,
  `EVENT` xóa khi đọc), và kiểm SHA-256 của microcode. Vòng đọc trong `main.c`
  (ngắt, kiểm định kỳ, khởi động lại) không chạy trên máy tính. Mô phỏng do dự án
  viết, nên chip thật kiểm ở bring-up.

## Cấu hình AFE `0xD2` và lệnh từ PC (2026-10-25, chưa chạy trên chip)

Packet Schema V0.2 mục 12–13.

- **Task điều khiển** (`ctl_task` trong `main.c`) là nơi duy nhất tạo `0xD2` và `0xD3`
  (một producer mỗi kênh). Nó đọc cổng USB Serial/JTAG liên tục (lượt 10 ms, bộ đệm RX
  1 024 byte), bỏ khung dở quá 100 ms, tách khung bằng `cmd_wire.c`, và không bao giờ
  đứng chờ task khác.
- **`0xD2`:** mỗi task đọc công bố từng bước chuyển trạng thái của AFE của nó
  (`afe_publish`, qua hàng đợi 8 phần tử): nguồn giả lúc khởi động; chip khi cấu hình
  xong (thế hệ tăng), khi chờ cấu hình lại, khi bị bỏ. Task điều khiển gửi mỗi bước
  chuyển và nhắc lại trạng thái mới nhất của mọi AFE mỗi 10 s; hàng đợi đầy thì nó gửi
  trạng thái mới nhất của AFE đó kèm bit 1. Chọn gửi gì, kèm bit 1 hay không là
  `afe_order.c` (C thuần, Packet Schema V0.2 mục 12): không gửi trạng thái cũ sau trạng
  thái mới, mất mát được giữ tới khi một `0xD2` mang bit 1, số thứ tự 64 bit. Thanh ghi
  lấy từ `max30001_config_words`, `max30101_config_words`, `bmi270_config_words`.
- **`PING` và `SET_PPG_LED`:** `cmd_exec.c` (C thuần) quyết định: kiểm `SESSION_ID`
  đích, giới hạn mã 127 (`CMD_LED_CODE_MAX`, tạm), trạng thái chip; nhớ yêu cầu gần
  nhất nên gửi lại cùng byte được trả lại kết quả cũ mà không chạm chip. Task PPG (chủ
  bus I²C) đổi dòng bằng `max30101_start` với dòng mới: `RESET` xóa FIFO, packet PPG kế
  tiếp neo lại (bit 5); lỗi thì cấu hình lại bằng dòng cũ (kết quả 5). Yêu cầu và trả lời
  mang token, nên trả lời muộn không bị gán cho yêu cầu khác; yêu cầu task PPG chưa nhận
  sau 2 s được rút lại (kết quả 4). Bản build PPG giả trả "không có chip".
- **Test:** [tests/test_firmware_cmd_wire.py](../tests/test_firmware_cmd_wire.py) (tách
  khung, so với bộ mã hóa Python), [tests/test_firmware_control.py](../tests/test_firmware_control.py)
  (`DATA` của `0xD2` qua bộ kiểm của receiver; quyết định lệnh),
  [tests/test_firmware_afe_order.py](../tests/test_firmware_afe_order.py) (thứ tự và
  bit 1 của `0xD2`, gồm hàng đợi đầy rồi im, mất mát thấy sau khi trạng thái mới đã đi,
  số thứ tự quá 32 bit). Task điều khiển, hàng đợi và cổng USB trong `main.c` chỉ kiểm
  bằng build.

## Chưa có

- Chạy thử MCPWM capture thật trên chip (nối vòng GPIO trên DevKitC trần, rồi
  INT2B của MAX30001); kiểm `PPG_RDY` ở chế độ ba khe của MAX30101 thật.
- Quét dòng LED tự động khi hiệu chuẩn; lệnh bắt đầu/dừng và đổi cấu hình khác.

