# Protocol nghiên cứu

Lưu protocol và lịch sử phiên bản. Protocol cần xác định quy trình đo, biến đầu
ra, mốc ECG/PPG, PAT, SQI, tiêu chí loại dữ liệu và kế hoạch phân tích.

## Protocol và định nghĩa phương pháp

- [Khung protocol nghiên cứu thực nghiệm v0.3](protocol_outline_v0.2.md): bản
  hiện hành (2026-10-29; tên file giữ `v0.2`). Phân bổ tay/điện cực theo V1-module,
  kiểm tra xung đột, nghiệm pháp tạo ΔBP (M0–M2; M3, M4 bỏ ngày 2026-10-29),
  endpoint RQ1, trục thời gian M2, LOSO
  lồng và tiêu chí pilot. Mục 5.1–5.2 đã xác nhận về phần cứng ngày 2026-10-23; các
  mục ghi "đề xuất của nhóm" chờ thầy, nghiệm pháp chưa được hội đồng đạo đức duyệt.
- [Khung protocol nghiên cứu thực nghiệm v0.1](protocol_outline_v0.1.md): bản
  lịch sử; thiết kế đo lặp nhiều phiên, quy trình đo đối chứng bằng cuff, ghép
  cửa sổ tín hiệu và kế hoạch phân tích thống kê.
- [Định nghĩa mẫu, nhãn và thuật ngữ (Tuần 2)](week_02_sample_label_glossary.md):
  PAT/PTT/PEP/PWA, đơn vị quan sát, cửa sổ ứng viên và metadata tối thiểu.
- [Baseline B0/B1 và chỉ số đánh giá (Tuần 3)](week_03_baselines_metrics.md):
  công thức B0/B1, MAE/bias/SD và đặc tả các chỉ số mở rộng.
- [Đặc trưng, SQI và bootstrap theo người (Tuần 4)](week04_features_sqi_bootstrap.md):
  giao diện trích đặc trưng, mốc R/foot/PAT và CI bootstrap.
- [Mốc R/foot thứ hai, PAT hợp lệ và so với đánh dấu tay (Tuần 5)](week05_fiducials_pat_validity.md):
  phương pháp ứng viên, quy tắc PAT/outlier, công cụ đánh dấu tay và kết quả
  SYNTHETIC; mẫu CSV ở [templates/](templates/manual_fiducials_template.csv).

## Hướng dẫn chạy

- [Chạy B0 trên CSV PulseDB](run_b0_pulsedb_csv.md)
- [Tạo inventory và split PulseDB](run_pulsedb_split.md)
- [Chạy B0/B3 trên PulseDB split v2](run_b3_pulsedb.md)
- [Định nghĩa B2 trên PulseDB](b2_pulsedb_definition.md): nhân khẩu học cộng HR,
  hai bảng so sánh định trước; đề xuất 2026-10-26, chưa duyệt; code có, chưa chạy
- [Đăng ký trước cách chấm test split và CalFree](pulsedb_test_scoring_preregistration.md):
  chấm mọi model đã khóa đúng một lần (chốt 2026-10-29); chưa có script, chưa chấm
- [Sinh và replay packet giả lập](packet_simulation.md): `synthetic-packet-v2`
  (JSON) và `synthetic-packet-v3` (luồng byte theo Packet Schema V0.1)
- [Logger packet phía máy tính](packet_logger.md): decoder `SYNC`/CRC16, kiểm tra
  mục 12 theo kênh, raw bất biến, session manifest; đọc cổng serial trực tiếp
  bằng `pyserial` (`--port`, `--duration-s`)
