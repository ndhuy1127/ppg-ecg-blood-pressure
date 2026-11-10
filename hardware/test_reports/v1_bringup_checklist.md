# Checklist bring-up V1-module

> **Trạng thái: đề xuất ngày 2026-11-07, chờ duyệt.** Phần cứng dự kiến về trong Tuần 8. File này
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
  - một cáp USB-C có dữ liệu, đã thử với laptop đo;
  - nút BOOT/RESET dễ bấm khi đã lắp lên bo đế, hoặc dây nối để bấm từ ngoài;
  - ghi lệnh nạp cho từng env vào báo cáo.
- [ ] **Firmware:** build sẵn các env `esp32s3_devkitc` (khung), `esp32s3_devkitc_ppg_real`,
  `esp32s3_devkitc_all_real`, `esp32s3_devkitc_sync10`. Ghi commit và ELF SHA-256
  ([firmware/README.md](../../firmware/README.md)).
- [ ] **Logger:**
  - chạy thử `record --port` với bo Waveshare đứng riêng ngay khi có;
  - chuẩn bị metadata `packet-session-metadata-v1` cho bring-up, `subject_id` null kèm lý do;
  - nơi ghi ngoài `data/raw/` ([packet_logger.md](../../docs/protocol/packet_logger.md));
  - thử `--dc-every-s 2` và `device_command.py ping`.
- [ ] **Bản in:** bản in PCB 1:1 của hai bo. Mạch đo dòng rò MD (AT mục 2) dựng sẵn, đã kiểm
  bằng dòng đã biết.
- [ ] **Mẫu báo cáo:** tạo trước `hardware/test_reports/<ngày>_v1_bringup.md` theo BU mục 11.
- [ ] **Đối chiếu tiêu chuẩn:** các giới hạn của AT mục 2 và 4 đối chiếu với nguyên văn
  IEC 60601-1 (ghi số trang). Hẹn người có chuyên môn duyệt biên bản.

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
| 11 | Đo đồng bộ 10 phút | BU mục 9, [sync_10min_test_plan.md](sync_10min_test_plan.md) | [ ] | |
| 12 | Chạy cả hệ 120 phút, gộp với thử nhiệt: `record --commands`, LED `0x7F`, nhiệt độ bo cổ tay ≤ 41 °C, đủ file và manifest, ghi đỉnh RAM | BU mục 8 bước 9; AT mục 4 | [ ] | |
| 13 | Đo dòng rò: bệnh nhân và phụ, AC và DC, ≤ 50 % giới hạn | AT mục 2 | [ ] | |
| 14 | Biên bản dòng rò và nhiệt có chữ ký người có chuyên môn | AT mục 5 | [ ] | |

Chỉ sau bước 14, và khi đã có phê duyệt phù hợp, mới tới G2 trên thành viên nhóm (K3–K5 của
protocol mục 5.4, khóa ngưỡng SQI theo [SQI v1](../../docs/protocol/sqi_specification_v1.md)
mục 6).
