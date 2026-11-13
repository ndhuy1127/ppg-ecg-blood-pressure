# Checklist bring-up V1-module

> **Trạng thái: đề xuất ngày 2026-11-07, duyệt ngày 2026-11-14.** Phần cứng dự kiến về trong Tuần 8. File này
> chỉ để đánh dấu tiến độ; nội dung từng bước nằm ở [trình tự bring-up](v1_bringup_procedure.md)
> (BU) và [kế hoạch đo dòng rò, thử nhiệt và VLED](leakage_thermal_test_plan_v1.md) (AT).
> Bước nào không đạt thì dừng ở đó, ghi lại, xử lý xong mới đi tiếp. Không gắn điện cực lên người.

## A. Chuẩn bị trước khi hàng về (làm được ngay)

- [ ] **Dụng cụ** (BU mục 0):
  - đồng hồ vạn năng true-RMS, oscilloscope 2 kênh, thước kẹp, USB tester;
  - điện trở shunt cho đường 5 V;
  - cặp nhiệt hoặc nhiệt kế hồng ngoại.
- [ ] **Dây đo:** que móc cho test point TP1–TP4; dây cá sấu nối GND; dây ngắn cho chân C2 của
  bo cổ tay (không có test point).
- [ ] **Jig nạp:** bo Waveshare nạp qua USB native, không cần jig riêng. Chuẩn bị:
  - [ ] một cáp USB-C có dữ liệu, đã thử với laptop đo;
  - [ ] nút BOOT/RESET dễ bấm khi đã lắp lên bo đế, hoặc dây nối để bấm từ ngoài;
  - [x] ghi lệnh nạp cho từng env (bảng Firmware dưới; chép vào báo cáo khi nạp).
- [x] **Firmware:** build sẵn các env `esp32s3_devkitc` (khung), `esp32s3_devkitc_ppg_real`,
  `esp32s3_devkitc_all_real`, `esp32s3_devkitc_sync10`. Ghi commit và ELF SHA-256
  ([firmware/README.md](../../firmware/README.md)). Đã build 2026-11-13 (bảng dưới).
- [ ] **Logger:**
  - [ ] chạy thử `record --port` với bo Waveshare đứng riêng ngay khi có;
  - [x] chuẩn bị metadata `packet-session-metadata-v1` cho bring-up, `subject_id` null kèm lý do
    (2026-11-13, mục "Logger không cần thiết bị" dưới);
  - [x] nơi ghi ngoài `data/raw/` ([packet_logger.md](../../docs/protocol/packet_logger.md)):
    `runs/bringup_v1/<YYYY-MM-DD>_<bước>/` (chốt 2026-11-13);
  - [ ] thử `--dc-every-s 2` và `device_command.py ping` trên bo. Đã thử `--dc-every-s 2` trên
    luồng giả (dưới); `ping` cần `record --port --commands`, chưa làm được khi chưa có bo.
- [ ] **Bản in:** bản in PCB 1:1 của hai bo. Mạch đo dòng rò MD (AT mục 2) dựng sẵn, đã kiểm
  bằng dòng đã biết.
- [x] **Mẫu báo cáo:** tạo trước `hardware/test_reports/<ngày>_v1_bringup.md` theo BU mục 11.
  Đã tạo 2026-11-13: [YYYY-MM-DD_v1_bringup.md](YYYY-MM-DD_v1_bringup.md); đổi tên theo ngày
  thật khi bắt đầu.
- [ ] **Đối chiếu tiêu chuẩn:** các giới hạn của AT mục 2 và 4 đối chiếu với nguyên văn
  IEC 60601-1 (ghi số trang). Hẹn người có chuyên môn duyệt biên bản.

### Firmware build sẵn (2026-11-13)

- Commit `0df0ba69075ea5e97355d71af27e70556362c8ab`; `PLATFORMIO_BUILD_FLAGS`: không đặt.
  PlatformIO Core 6.1.19, `espressif32@6.13.0`, ESP-IDF 5.5.3.
- Build sạch: `pio run -d firmware -e <env> -t clean`, rồi `pio run -d firmware -e <env> -j 1`.
  Phiên bản ứng dụng nhúng trong image (`esp_app_desc_t.version`) là `0df0ba6`.
- ELF SHA-256 là SHA-256 của `firmware/.pio/build/<env>/firmware.elf`. Đã kiểm: trùng
  `app_elf_sha256` nhúng trong `firmware.bin`, tức giá trị packet `0xD1` sẽ gửi.
- Lệnh nạp (COM do Windows gán): `pio run -d firmware -e <env> -t upload --upload-port COMx`.

| Env | ELF SHA-256 |
| --- | --- |
| `esp32s3_devkitc` | `cd70883c827e595e9955110c5c3850a8565063913e559e0bcdc8228dc367db86` |
| `esp32s3_devkitc_ppg_real` | `ca5888de34964c0eb4e44d90652c687293e144cd1fcdda19e01bfff3c24f7671` |
| `esp32s3_devkitc_all_real` | `a58741d94feaf4fc3e45a5c603ece3a73f2defce74e672a77fc10190119244f6` |
| `esp32s3_devkitc_sync10` | `59fb0d93c8cfd148b45dc90a65190abd14a0d72965912aa120cca5c6535f1d0b` |

- Build tăng dần trên `.pio/build` cũ giữ phiên bản cũ trong image: lần build đầu ngày
  2026-11-13 cho `4ee3e6d-dirty`, ngày 2026-10-29. Vì vậy build sạch trước khi ghi ELF SHA-256.
- Phiên bản lấy từ `git describe`, nên build lại sau một commit mới cho ELF SHA-256 khác bảng
  trên. Nạp bản nào thì ghi hash của chính bản đó.
- `sync10` ở đây dùng cực tính `SAMP` và độ rộng xung mặc định (0, 411 µs). Đây chỉ là kiểm
  build. Bản nạp thật build lại với giá trị đo ở BU mục 7 bước 4 và mục 8.

### Logger không cần thiết bị (2026-11-13)

- Metadata bring-up: [metadata/v1_bringup_s2_default_env.json](metadata/v1_bringup_s2_default_env.json)
  (SHA-256 `a2eda2bc2e12cc26ac7343082230d35b9d671531d2f982596ee99773e100a608`). Dùng cho BU mục 2
  với env `esp32s3_devkitc`. Qua `validate_metadata`. Khi nhận bo: điền `device_id`.
- Chốt 2026-11-13, duyệt 2026-11-14: `source_type` là `DEVICE` vì byte đến từ bo thật, dù env mặc định
  gửi giá trị giả. Kênh ghi rõ "nguồn giả" trong `sensor`. Logger sẽ báo `afe_fake_source`
  với env này; đó là kết quả chờ đợi. Cùng ngày, Packet Schema V0.2 mục 11.1 sửa theo cùng
  quy tắc (`DEVICE` khi byte đến từ MCU thật, `SYNTHETIC` chỉ cho luồng PC sinh), duyệt 2026-11-14.
- Env có chip thật (`ppg_real`, `all_real`, `sync10`) cần metadata riêng, có `afe_config` theo
  `0xD2`. Chưa tạo.
- Chạy thử:

  ```powershell
  .\.venv\Scripts\python.exe scripts/simulate_packets.py --config configs/hardware/packet_simulation_v3_v02.json --case valid --output runs/bringup_v1/2026-11-13_dryrun_sim_valid
  .\.venv\Scripts\python.exe scripts/packet_logger.py record --source-file runs/bringup_v1/2026-11-13_dryrun_sim_valid/stream.bin --metadata hardware/test_reports/metadata/v1_bringup_s2_default_env.json --dc-every-s 2 --output runs/bringup_v1/2026-11-13_dryrun_record
  ```

- Kết quả: exit 0; 77 packet, 6 230 byte; SHA-256 `raw.bin` =
  `a4132f8e349ada9884101359a2f3f3ea4c7c9e18909b2671b4613f887f1e3ab5`, trùng luồng giả.
  10 issue, đều do luồng giả khác firmware thật: `channel_missing` 2 (không có `0xF3`, `0xB1`),
  `fs_metadata_mismatch` 2 (PPG giả 100 sps, metadata 200 sps), `firmware_metadata_mismatch` 1,
  `device_info_anchor_inconsistent` 2 (`0xD1` giả mỗi 0,3 s), `afe_config_missing` 3 (không có
  `0xD2`).
- Không có dòng DC nào: nguồn file đọc hết trong chưa tới 2 s, mà dòng DC in theo đồng hồ PC.
  Chạy lại cùng luồng qua `record()` với nguồn đọc chậm (64 byte mỗi 0,1 s, chỉ để thử): có 4
  dòng DC, có `STALE` khi hết mẫu, cùng 10 issue. Dòng DC thật kiểm khi có bo.

## B. Khi hàng về

| # | Bước | Chi tiết | Đạt | Ghi chú |
| --- | --- | --- | --- | --- |
| 1 | Kiểm khi nhận (chưa hàn, chưa cấp nguồn) | BU mục 1 | [ ] | |
| 2 | Bo Waveshare đứng riêng: nạp env khung, `record` 10 phút | BU mục 2 | [ ] | |
| 3 | PCB trần: thông mạch, chập | BU mục 3 | [ ] | |
| 4 | Sửa module trước khi lắp | BU mục 4 | [ ] | |
| 5 | Hàn và lắp | BU mục 5 | [ ] | |
| 6 | Bo đế với bo Waveshare | BU mục 6 | [ ] | |
| 7 | MAX30001 trên bo đế, nguồn SAMP | BU mục 7 | [ ] | |
| 8 | Bo cổ tay qua cáp: nguồn, I²C, SPI, PPG, IMU | BU mục 8 bước 1–8 | [ ] | |
| 9 | **VLED+:** V1 không tải 4,9–5,3 V; V2 đỉnh khởi động ≤ 5,5 V; V3 trong xung `0x7F` 4,5–5,5 V; V4 ghi chú nếu 5,0–5,3 V | AT mục 3 | [ ] | |
| 10 | Nhiễu đèn trên PPG | BU mục 8 bước 10 | [ ] | |
| 11 | Đo đồng bộ: thử trước 1 phút (kích thích PPG thấy được), 5 lần 10 phút, 1 lần 120 phút; tiêu chí A1–A9 | BU mục 9, [sync_10min_test_plan.md](sync_10min_test_plan.md) mục 3, 4, 9 | [ ] | |
| 12 | Chạy cả hệ 120 phút, gộp với thử nhiệt: `record --commands`, LED `0x7F`, nhiệt độ bo cổ tay ≤ 41 °C, đủ file và manifest, ghi đỉnh RAM | BU mục 8 bước 9; AT mục 4 | [ ] | |
| 13 | Đo dòng rò: bệnh nhân và phụ, AC và DC, ≤ 50 % giới hạn | AT mục 2 | [ ] | |
| 14 | Biên bản dòng rò và nhiệt có chữ ký người có chuyên môn | AT mục 5 | [ ] | |

**Ba phép kiểm chặn đường thời gian** (ghi 2026-11-11, duyệt 2026-11-14). Mọi mốc thời gian
dựa vào ba hành vi của chip mà datasheet không bảo đảm. Bước nào dưới đây không đạt thì dừng,
không đi tiếp sang bước 11:

- [ ] **Ở bước 7:** cạnh `SAMP` đầu tiên ứng với mẫu đầu tiên của FIFO ECG (BU mục 7 bước 4).
  Lệch cố định một mẫu là 1,953 ms và logger không tự phát hiện được; tiêu chí A8 của kế hoạch
  đo đồng bộ kiểm lại độc lập.
- [ ] **Ở bước 8:** ba khe ở 200 sps chạy được với độ rộng xung đã chọn: `SPO2_SR` đọc lại đúng
  và tốc độ ra mỗi khe trong 200 sps ± 3 %
  ([interface_power_sampling_v0.md](../../configs/hardware/interface_power_sampling_v0.md) mục 6).
- [ ] **Ở bước 8:** `PPG_RDY` báo mỗi mẫu ở chế độ ba khe (BU mục 8 bước 6); nếu không thì ghi
  cách đọc FIFO thay thế và kiểm lại tiêu chí A3.

Chỉ sau bước 14, và khi đã có phê duyệt phù hợp, mới tới G2 trên thành viên nhóm (K3–K5 của
protocol mục 5.4, khóa ngưỡng SQI theo [SQI v1](../../docs/protocol/sqi_specification_v1.md)
mục 6).
