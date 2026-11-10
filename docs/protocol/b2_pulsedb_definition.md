# Định nghĩa B2 trên PulseDB: nhân khẩu học cộng HR

> **Trạng thái:** đề xuất ngày 2026-10-26, sửa ngày 2026-11-07 sau review (mục 7).
> **v0** (`configs/models/b2_pulsedb_v0.json`) duyệt nguyên trạng ngày 2026-11-07 bằng commit
> riêng, rồi chạy trên val cùng ngày và **dừng đúng chốt kiểm của mục 2** trước khi fit model
> nào, nên không có số B2 nào (mục 9). **v1** (`configs/models/b2_pulsedb_v1.json`, đề xuất
> 2026-11-07, **duyệt nguyên trạng ngày 2026-11-07** bằng commit riêng, trước khi có số
> nào) chỉ đổi quy tắc nhân khẩu học ở mục 2. Code và test SYNTHETIC
> ở mục 8. Định nghĩa này phải được duyệt và commit **trước** khi tính
> bất kỳ số B2 nào trên val (kế hoạch Tuần 6, việc 2). Sau khi đã thấy kết quả
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
  - Mọi trường phải hữu hạn.
  - v0: mỗi người phải có cùng giá trị ở mọi đoạn (kiểm và báo, lệch thì dừng).
  - v1 (2026-11-07): mỗi đoạn dùng nhân khẩu học của chính nó. Không loại dòng nào, nên
    các bảng vẫn dùng đúng các dòng của B0/B3. Report ghi, riêng cho train và val, số người
    có nhiều hơn một bộ giá trị và độ lệch lớn nhất trong một người của từng trường
    (`demographics_variation`, không có ID người).
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
- **Bảng "có HR" không chấm được (thêm 2026-11-07, trước khi có số):** nếu train hoặc val
  có ít hơn `bootstrap.min_subjects` (2) người có HR, run dừng ngay sau khi tính mặt nạ
  HR, **trước khi fit** bất kỳ model nào của cả hai bảng, nên không có số B2 nào. Khi đó
  ghi lý do và số người có HR, và chỉ chạy lại với một version mới của định nghĩa.
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
  Đó là lộ biến đầu vào, không phải lộ nhãn.
- **Lần xem đó đã ảnh hưởng tới một lựa chọn (ghi rõ 2026-11-07):** `refractory_s = 0,25`
  (mục 3) được biện luận bằng tuổi nhỏ nhất 0,4 năm, con số đọc trên cả file, không phải
  chỉ trên train. Các lựa chọn khác dựa trên train, trên kết quả SYNTHETIC Tuần 5 hoặc
  trên cấu hình B3 v1: bộ dò `derivative_energy`, khoảng [30, 220] bpm, ≥ 4 đỉnh, không
  điền giá trị thiếu, hai bảng, learner và seed. Không sửa lại được tình trạng "chưa từng
  xem"; duyệt định nghĩa này là chấp nhận rằng `refractory_s` có thể đã chịu ảnh hưởng
  của biến đầu vào val/test. Mức ảnh hưởng tới sai số chưa định lượng được; vì nó chỉ đổi
  bộ dò R cho nhịp nhanh, hướng của nó lên MAE không biết trước.

## 7. Review

Phản biện ngày 2026-10-26 (một vòng). Nhận: phương án hai bảng, ghép cả dòng
train, refractory 0,25 s, đóng băng mọi lựa chọn trước khi chấm, ghi lộ biến đầu vào,
B3 − B2b không phải phần lợi thêm. Không nhận: `prominence` ở 0,25 s (được đề xuất),
vì kết quả SYNTHETIC Tuần 5 cho thấy nó bắt đỉnh T.

Review trước khi duyệt, 2026-11-07 (độc lập, là bước review định nghĩa
của kế hoạch Tuần 6; chưa có số nào). Kết luận "duyệt được sau khi sửa"; cả năm
điểm đã được kiểm trên code và đã sửa:

1. Chốt duyệt chỉ kiểm config và file định nghĩa; mã tính HR, fit và chấm có thể khác
   `HEAD`. Nay runner đòi cả `CODE_FILES` đã commit và không đổi (`approval_committed`
   có thêm `code`).
2. Test "từ chối khi chưa duyệt" dùng config thật của repo, nên sẽ hỏng ngay sau commit
   duyệt. Nay test dùng một bản sao `PENDING` và chặn mọi lần đọc dữ liệu.
3. Ảnh hưởng của lần xem biến đầu vào toàn file lên `refractory_s` được ghi rõ (mục 6).
4. Chưa định trước trường hợp bảng "có HR" không chấm được. Nay có quy tắc dừng trước khi
   fit (mục 4) và test.
5. Bản đăng ký chấm test chưa liệt kê model theo từng bảng. Nay đã liệt kê
   ([đăng ký chấm test](pulsedb_test_scoring_preregistration.md) mục 3).

Ghi thêm làm giới hạn, không sửa: bảng "có HR" ước lượng hiệu năng có điều kiện trên
các đoạn đo được HR, nên có thể lệch theo chất lượng tín hiệu; B0 (trung bình) và
XGBoost tối ưu sai số bình phương trong khi chỉ số chính là MAE.

## 8. Code và cách chạy (2026-10-26)

- Đặc trưng: `software/pulsedb/features_b2.py` (`HR_CONFIG` đóng băng như mục 3).
- Hai bảng: `software/pulsedb/pipeline_b2.py` (`run_b2`), config
  `configs/models/b2_pulsedb_v1.json` (mặc định của runner từ 2026-11-07; v0 giữ làm lịch
  sử; tham số và seed lấy đúng từ B3 v1, v1 chỉ khác v0 ở version và `status`; test kiểm
  các điều này).
- Runner: `scripts/run_b2_pulsedb.py --raw <file .mat> --split-dir <thư mục split v2>`,
  ghi `b2_table.md`, `hr_mask.csv`, `predictions_val_<bảng>.csv` (có ID người, ngoài
  Git) và `report.json` vào thư mục mới trong `runs/b2_pulsedb/`, không ghi đè. Phần
  kiểm đầu vào dùng chung `load_split` của `scripts/run_b3_pulsedb.py`.
- **Chốt chặn (sửa 2026-10-26 theo review):** `status` chỉ nhận hai giá trị,
  `PENDING_APPROVAL_NOT_RUN` và `APPROVED_NOT_TEST_EVALUATED`; giá trị khác (rỗng, gõ
  sai) làm config bị từ chối. Runner chỉ chạy với `APPROVED_NOT_TEST_EVALUATED`, và chỉ
  khi config, file định nghĩa này và mọi file mã trong `CODE_FILES` của runner (thêm
  2026-11-07) đã được Git theo dõi và không khác `HEAD`; nếu không thì dừng trước khi
  đọc raw. Khi duyệt xong, đổi `status` trong một commit riêng
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

## 9. Lần chạy v0 và lý do có v1 (2026-11-07)

- v0 chạy trên val ngày 2026-11-07 (commit `1c708df`, worktree sạch) và dừng ở phép kiểm
  "nhân khẩu học khác nhau giữa các đoạn của một người", sau khi tính đặc trưng và HR của
  train và val, **trước khi fit** model nào. Không có dự đoán hay số B2 nào.
- Chẩn đoán chỉ trên train, chỉ số tổng hợp, không xem val/test: 4/320 người train có hai bộ
  giá trị khác nhau (1.440 đoạn); tuổi lệch tối đa 1 năm, cân nặng 2,1 kg, chiều cao 0,6 cm,
  BMI 0,9; giới không đổi. Khác biệt có thật, không phải sai số làm tròn; nhiều khả năng là
  hai ca phẫu thuật của cùng một bệnh nhân (chưa kiểm được trong PulseDB).
- Quyết định ngày 2026-11-07 (chưa có số nào): v1 dùng giá trị của từng đoạn (mục 2). Các
  phương án khác đã xét: lấy giá trị đoạn đầu của mỗi người (giữ giả định hằng số theo
  người), loại những người này (làm tập đánh giá khác B0/B3). Mọi thứ khác giữ như v0.
- v1 được duyệt bằng commit riêng đổi `status` ngày 2026-11-07, trước khi chạy, như v0.
