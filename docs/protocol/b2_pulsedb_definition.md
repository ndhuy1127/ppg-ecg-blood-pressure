# Định nghĩa B2 trên PulseDB: nhân khẩu học cộng HR

> **Trạng thái:** đề xuất ngày 2026-10-26, **chờ Huy duyệt**. Code và test SYNTHETIC
> đã có (mục 8), chưa chạy trên PulseDB, chưa có số B2 nào. Định nghĩa này phải được duyệt và commit **trước** khi tính
> bất kỳ số B2 nào trên val (kế hoạch Tuần 6, việc 2 của Huy). Sau khi đã thấy kết quả
> thì không đổi đặc trưng, bộ dò, ngưỡng, learner hay phép so sánh; nếu phải đổi thì
> tạo version mới và báo cả hai.

## 1. Phạm vi

- Dùng đúng split `pulsedb-split-v2` của lần chạy B3 (`b3-pipeline-v1`, pool VitalDB
  Train 400 người, seed 72). Config ghim bốn hash của split đó (`split_sha256`: raw,
  inventory, manifest, config, chép từ
  `reports/weekly/week_05/pulsedb_b3_v1/split_report.json`); runner từ chối split có
  hash khác trước khi đọc đoạn nào (thêm 2026-10-26). Dự đoán SBP và DBP tuyệt đối
  (mmHg), mỗi đại lượng một model. Giữ QC nhãn `exclude_dbp_ge_sbp` của v1; không thêm lọc nào dựa trên BP.
- Fit trên train, chấm val. Đoạn test không được trích đặc trưng, dự đoán hay chấm.
- Nhãn là ABP xâm lấn công khai của bệnh nhân phẫu thuật VitalDB, không phải cuff,
  không phải ΔBP, không phải thiết bị của nhóm. Không kết luận ngoài val PulseDB.

## 2. Đặc trưng

- **B2a** (5 đặc trưng): `age_y`, `sex` (F = 0, M = 1), `height_cm`, `weight_kg`,
  `bmi_kg_m2`, lấy nguyên từ PulseDB.
  - Giới tính lấy qua `normalize_gender` của reader. Giá trị khác M/F làm run dừng
    (`ValueError`), không mã hóa thành "khác".
  - Mọi trường phải hữu hạn. Mỗi người phải có cùng giá trị ở mọi đoạn (kiểm và báo,
    lệch thì dừng).
  - Giữ trẻ em: dùng BMI như nguồn cung cấp, không phân loại BMI người lớn, không loại
    theo tuổi.
- **B2b** (6 đặc trưng, version `pulsedb-demographics-hr-v0`): B2a cộng `hr_bpm`.
- Không dùng ABP, nhãn, ID người hay hash làm đầu vào. ID chỉ để nhóm và ghép.

## 3. HR từ ECG

- Chỉ dùng `ECG_F`, 1 250 mẫu ở 125 Hz (đoạn 10 s). Dùng `prepare` rồi `r_peaks`
  (`software/signal_processing/fiducials.py`) với cấu hình cố định:
  - `r_method = "derivative_energy"`, `r_energy_window_s = 0,1`,
    `r_energy_threshold = "quantile"`;
  - `refractory_s = 0,25`;
  - `prominence_fraction = 0,2`, `ecg_polarity = 1`, `filter_mode = "none"`,
    `edge_s = 0,1`, `flat_std = 1e-8`.
- `hr_bpm = 60 / trung vị(hiệu các thời điểm R liên tiếp)`, dùng mọi đỉnh dò được,
  không cắt R–R.
- HR **không có** khi `prepare` gắn cờ, có ít hơn 4 đỉnh R, kết quả không hữu hạn,
  hoặc nằm ngoài [30, 220] bpm (gồm hai đầu). Không cắt ngưỡng, không điền giá trị.
- Đây là **ước lượng tốc độ đỉnh ECG chưa được nghiệm thu**, không phải HR đã kiểm
  chứng. Bộ dò R chưa qua cổng Tuần 5 (cổng đó chỉ quyết định B4). Lọt qua [30, 220]
  không chứng minh HR đúng: mất nhịp, bắt nhầm sóng T hay đảo cực vẫn cho số hợp lý.
  B2b thất bại không có nghĩa HR sinh lý vô ích.

**Vì sao chọn như vậy:**
- `refractory_s` mặc định 0,4 s chặn HR ở 150 bpm (50 mẫu ở 125 Hz). Nhịp nhanh khi đó
  bị dò thành nửa tần số mà vẫn lọt [30, 220]. Pool có trẻ nhỏ (tuổi thấp nhất 0,4
  năm), nên 0,25 s là cần.
- Ở 0,25 s, `prominence` bắt đỉnh T ở mọi bản ghi SYNTHETIC HR 60 (44 FP), làm HR gấp
  đôi. `derivative_energy` cho 7 FP, đều ở bản ghi nhiễu
  ([Tuần 5 mục 5.1](week05_fiducials_pat_validity.md)). Đây là bằng chứng SYNTHETIC,
  không phải trên PulseDB.

## 4. Hàng thiếu HR: hai bảng so sánh định trước

| Bảng | Dòng train | Dòng val | Model |
| --- | --- | --- | --- |
| Đủ | Mọi dòng qua QC | Mọi dòng qua QC | B0, B2a, B3 |
| Có HR | Qua QC và có HR | Qua QC và có HR | B0, B2a, B2b, B3, fit lại trên đúng các dòng này |

- Mỗi bảng có model riêng, đặt tên khác nhau (ví dụ `B3@hr_available`). Không so B2b
  của bảng "có HR" với B3 của bảng "đủ".
- Báo số dòng bị loại, số người mất hẳn, độ phủ theo dòng và theo người, tách mô tả
  theo `< 18` / `≥ 18` tuổi và theo giới. Manifest gốc giữ nguyên; mặt nạ dòng có HR
  ghi riêng trong `hr_mask.csv` (`sample_id`, `split`, `has_hr` cho mọi dòng train và
  val sau QC; không có ID người), có hash trong report.

## 5. Learner và đánh giá

- Hai `XGBRegressor` qua `XGBoostBaseline`, đúng tham số và seed 42 của
  `configs/models/b3_pulsedb_v1.json`, không tinh chỉnh, không dừng sớm trên val.
- Trọng số train `inverse_subject_rows` tính lại **sau** khi lọc theo bảng, chuẩn hóa
  trung bình bằng 1 như pipeline v1.
- Metrics như B3: MAE/bias trung bình đều theo người, sai số = dự đoán − tham chiếu;
  2 000 lượt bootstrap theo người ghép cặp, seed 20261013, CI percentile 95 %. CI mô tả
  độ bất định theo người val với model đã fit, không gồm độ bất định khi huấn luyện.
- Phép so sánh chính, trong bảng "có HR": B2b − B0, B3 − B2b, và B2b − B2a (phần HR
  thêm vào). Trong bảng "đủ": B2a − B0 và B3 − B2a.
- B3 − B2b **không** đo phần lợi thêm của dạng sóng so với nhân khẩu học, vì B3 không
  có nhân khẩu học: hai bên là hai bộ đặc trưng khác nhau. Muốn đo phần thêm thì cần
  model B2 + đặc trưng dạng sóng, chưa nằm trong định nghĩa này.
- Ridge (đặc trưng chuẩn hóa) chỉ được thêm như phân tích độ nhạy định trước, ghi vào
  đây trước khi chạy; không thay XGBoost sau khi thấy kết quả val.

## 6. Provenance và giới hạn

- Ghi config, commit, thứ tự đặc trưng, hash raw/split, hash mặt nạ HR, số dòng loại,
  môi trường, và việc config cùng định nghĩa này đã commit nguyên trạng hay chưa
  (`approval_committed`); runner trong `scripts/`, output trong `runs/`, không ghi đè.
- Nhân khẩu học là hằng số theo người, nên mang thông tin giữa người; B2 có chủ yếu là
  bộ dự đoán giữa người hay không thì chưa xác định.
- Khoảng 320 người train độc lập; trọng số theo người tránh để bản ghi dài lấn át
  nhưng không tạo thêm quan sát nhân khẩu học độc lập.
- **Ghi nhận:** ngày 2026-10-26, khi soạn định nghĩa này, đã đọc phạm vi các cột Age,
  Height, Weight, BMI (không có NaN; tuổi 0,4–92) và Gender (M/F) trên **cả** file
  VitalDB Train, gồm cả người thuộc val và test của split. Không đọc nhãn hay tín hiệu.
  Đó là lộ biến đầu vào, không phải lộ nhãn; không dùng thêm biến đầu vào của val/test
  cho quyết định thiết kế nào khác.

## 7. Review

Codex phản biện ngày 2026-10-26 (một vòng). Nhận: phương án hai bảng, ghép cả dòng
train, refractory 0,25 s, đóng băng mọi lựa chọn trước khi chấm, ghi lộ biến đầu vào,
B3 − B2b không phải phần lợi thêm. Không nhận: `prominence` ở 0,25 s (Codex đề xuất),
vì kết quả SYNTHETIC Tuần 5 cho thấy nó bắt đỉnh T.

## 8. Code và cách chạy (2026-10-26)

- Đặc trưng: `software/pulsedb/features_b2.py` (`HR_CONFIG` đóng băng như mục 3).
- Hai bảng: `software/pulsedb/pipeline_b2.py` (`run_b2`), config
  `configs/models/b2_pulsedb_v0.json` (tham số và seed lấy đúng từ B3 v1; test kiểm
  điều này).
- Runner: `scripts/run_b2_pulsedb.py --raw <file .mat> --split-dir <thư mục split v2>`,
  ghi `b2_table.md`, `hr_mask.csv`, `predictions_val_<bảng>.csv` (có ID người, ngoài
  Git) và `report.json` vào thư mục mới trong `runs/b2_pulsedb/`, không ghi đè. Phần
  kiểm đầu vào dùng chung `load_split` của `scripts/run_b3_pulsedb.py`.
- **Chốt chặn (sửa 2026-10-26 theo review):** `status` chỉ nhận hai giá trị,
  `PENDING_APPROVAL_NOT_RUN` và `APPROVED_NOT_TEST_EVALUATED`; giá trị khác (rỗng, gõ
  sai) làm config bị từ chối. Runner chỉ chạy với `APPROVED_NOT_TEST_EVALUATED`, và chỉ
  khi config cùng file định nghĩa này đã được Git theo dõi và không khác `HEAD`; nếu
  không thì dừng trước khi đọc raw. Khi Huy duyệt, đổi `status` trong một commit riêng
  rồi mới chạy, để lịch sử Git cho thấy định nghĩa có trước số liệu. Runner không có
  tham số bỏ qua chốt này; file bị symlink không được tính là đã commit. Test SYNTHETIC
  (config nằm ngoài repo) thay phép kiểm Git bằng `monkeypatch`.
- Test SYNTHETIC: `tests/test_b2_pipeline.py` (HR đúng ở 45–180 bpm, là trung vị chứ
  không phải trung bình R–R khi nhịp không đều, không bị sóng T làm gấp đôi; thiếu HR;
  mã hóa giới tính; chỉ hai trạng thái; split ghim đúng lần chạy B3 v1; hai bảng đúng
  dòng; mỗi learner nhận đúng dòng, cột và trọng số 1/n_s của bảng mình; không trích
  đặc trưng dòng test (`verify_inputs` vẫn duyệt mọi dòng để băm lại inventory, như
  B3); nhãn val/test không đổi dự đoán; runner từ chối khi chưa duyệt, chưa commit hay
  split khác; `hr_mask.csv` và output không có ID người).
