# Chạy B0/B3 trên PulseDB split v2

## Phạm vi

Bản sửa pipeline B3 XGBoost của Linh (commit `acc8b8b`, PR #22). Các điểm khác
bản gốc:

- Dùng split `pulsedb-split-v2` có inventory, thay CSV 1.000 đoạn với
  `sample_id` 0..N-1. Không tự chọn 10 đoạn/người.
- Chỉ fit trên train, chỉ đánh giá val. Đoạn test không được trích đặc trưng,
  dự đoán hay chấm điểm.
- B0 và B3 chạy cùng một lần, trên cùng các dòng val và cùng lượt bootstrap.
- Metrics qua `evaluate_prediction_table`: MAE/bias trung bình đều theo người,
  MAE/bias/SD theo mẫu (`ddof=1`, `None` khi n=1), CI 95% bootstrap theo người.
  Từ 2026-10-23 có thêm hiệu ghép cặp B3 − B0 của MAE (`evaluation.contrasts`,
  một dòng cho mỗi huyết áp dưới bảng `baseline_table.md`), tính trong từng lượt
  bootstrap chung. Đây là so sánh BP tuyệt đối trên PulseDB, không phải kết quả
  ΔBP của RQ1.
- Config, seed, hash input, commit và phiên bản thư viện được ghi kèm output.
  Runner nằm trong `scripts/`, ghi vào `runs/`, không ghi đè.

Kết quả là BP tuyệt đối trên nhãn ABP công khai của một subset PulseDB. Đây
không phải đánh giá cuff, ΔBP cross-session hay thiết bị. B1 không chạy vì
chưa có chronology/calibration.

## Đầu vào

1. File raw `.mat` đã chọn làm pool, lưu ngoài Git.
2. Thư mục split do `scripts/build_pulsedb_split.py` tạo, gồm `inventory.csv`,
   `manifest.csv`, `config.json` và `report.json`. Xem
   [hướng dẫn split](run_pulsedb_split.md).
3. Config [b3_pulsedb_v0.json](../../configs/models/b3_pulsedb_v0.json) hoặc
   [b3_pulsedb_v1.json](../../configs/models/b3_pulsedb_v1.json) (mục
   `b3-pipeline-v1` dưới). v0 đọc cả file bằng `mat73`; v1 chỉ đọc các dòng có trong
   inventory bằng reader `h5py`, từng khối.

Trước khi fit, runner dừng nếu có bất kỳ điểm nào sau không khớp:

- `report.json` của split phải là object có `schema_version` `pulsedb-split-v2`;
- SHA-256 của raw (trước và sau khi đọc), `inventory.csv`, `manifest.csv` và
  `config.json` so với `report.json` của split;
- `config.json` của split phải có `pool_decision` không rỗng (được chép vào
  `split_pool_decision` của report);
- `source_sha256` của mọi dòng inventory phải bằng SHA-256 của file raw;
- `validate_manifest`: thiếu/thêm/sửa dòng, giao người hoặc hash giữa các split;
- inventory dựng lại từ raw qua reader của repo phải trùng từng byte với
  inventory bàn giao, tức `sample_hash`/`waveform_hash` được tính lại từ waveform.

## Đặc trưng `pulsedb-simple-stats-v0`

Module: [features.py](../../software/pulsedb/features.py). Mỗi đoạn cho 12 đặc
trưng, tính trên toàn bộ đoạn (1.250 mẫu, 10 s theo provenance):

| Tên | Công thức |
| --- | --- |
| `<kênh>_mean` | Trung bình |
| `<kênh>_std` | Độ lệch chuẩn quần thể, `ddof=0` |
| `<kênh>_min`, `<kênh>_max` | Giá trị nhỏ nhất/lớn nhất |
| `<kênh>_range` | `max - min` |
| `<kênh>_rms` | `sqrt(mean(x^2))` |

`<kênh>` là `ecg` và `ppg`. Đơn vị là đơn vị biên độ của nguồn; đơn vị và cách
chuẩn hóa `ECG_F`/`PPG_F` **chưa được xác minh**. Nếu kênh đã chuẩn hóa theo
đoạn, vài đặc trưng có thể là hằng số; runner liệt kê chúng trong
`constant_train_features`.

Hàm chỉ nhận vector ECG và PPG, không nhận ABP, nhãn BP, ID người hay hash.
Không impute: NaN/Inf, vector rỗng hoặc masked array gây `ValueError`. PAT và
module `features-sqi-v1` chưa được tích hợp.

**Quyết định 2026-10-25 (Huy):** B3 (kể cả `b3-pipeline-v1`) giữ đặc trưng
`pulsedb-simple-stats-v0` để đóng baseline G1. PAT, nhịp tim và SQI đi vào một
model **B4** riêng, chỉ sau khi đánh dấu tay trên train/val (không bao giờ test)
xác nhận mốc R/foot ([tài liệu mốc Tuần 5](week05_fiducials_pat_validity.md) mục
8). Báo B4 − B3 ghép cặp theo người để biết PAT thêm được bao nhiêu. Lý do: mốc chưa
thẩm định; PPG của PulseDB là PPG ngón tay 125 Hz, khác cổ tay của thiết bị; lọc theo
SQI làm đổi tập được đánh giá và ngưỡng SQI chưa có nguồn.

**Điều kiện xây B4 (chốt 2026-10-25,
[tài liệu mốc Tuần 5](week05_fiducials_pat_validity.md) mục 9):** lệnh `gate` phải
kết luận `B4_ALLOWED`. Nghĩa là phương pháp R và foot chọn trên 20 người train đạt
mọi ngưỡng, được xác nhận một lần trên 20 người train khác, và độ lặp lại của người
đánh dấu đạt. Người val không dùng để chọn mốc. Khi có B4, báo thêm mô hình đối
chứng B3 + HR/SQI (không có PAT), trên cùng các dòng val, để biết phần cải thiện có
đến từ PAT hay không. PAT trên PulseDB chỉ là đặc trưng tương đối (bộ lọc của
PulseDB chưa rõ là zero-phase hay causal).

## B3

[xgboost_baseline.py](../../software/models/xgboost_baseline.py): hai
`XGBRegressor` riêng cho SBP và DBP. Tham số và seed đặt trong config;
`n_jobs` phải là số nguyên dương cố định để kết quả tái lập. Không có
imputation, chuẩn hóa hay chọn đặc trưng. Ở v0 mỗi dòng train có trọng số bằng
nhau, nên người có nhiều đoạn có ảnh hưởng lớn hơn; v1 cân theo người (mục dưới).
Siêu tham số giữ nguyên bản của Linh, **chưa tuning**. Nếu tuning sau này thì chỉ
dùng val.

## `b3-pipeline-v1` (triển khai 2026-10-25)

Kế hoạch chốt ngày 2026-10-24 ([provenance](../pulsedb_provenance.md) mục 9). Config
v1 chỉ khác v0 ở `schema_version` và hai trường ghi rõ quy tắc; `load_config` từ
chối giá trị khác:

- `label_qc: "exclude_dbp_ge_sbp"`: bỏ các dòng **train/val** có DBP ≥ SBP khỏi fit
  và chấm điểm. Inventory và manifest bàn giao vẫn giữ đủ dòng. Pipeline tạo cặp
  manifest/inventory đã rút gọn, nên `validate_manifest` vẫn kiểm bảo toàn giữa
  hai bảng đó. Quy tắc **không áp cho dòng test** (số dòng test bị loại ghi `null`):
  dòng test vẫn không được trích đặc trưng, dự đoán hay chấm; nhãn của chúng chỉ đi
  qua bước băm lại inventory (`verify_inputs`) như ở v0, không được tóm tắt. Quy tắc
  sẽ áp khi đánh giá test bằng script khóa. Report ghi số dòng loại theo
  split và phân bố hiệu áp (SBP − DBP) của train trước QC (`min`, `p01`, `p05`,
  `p50`, `p95`, `p99`, `max`, số dòng ≤ 0).
- `train_weighting: "inverse_subject_rows"`: dòng train của người có n_s dòng (sau
  QC) nặng 1/n_s, rồi nhân chung một hằng số để trọng số trung bình bằng 1 (tổng
  bằng số dòng). Mỗi người có tổng trọng số như nhau. B0 thành trung bình các
  trung bình theo người; hằng số chung không đổi kết quả này. B3 truyền
  `sample_weight` cho cả hai `XGBRegressor`. Chọn trung bình 1 để tổng hessian
  của hàm mất mát bình phương vẫn bằng số dòng như v0, nên các thiết lập tuyệt đối
  của XGBoost (ngưỡng `min_child_weight` mặc định 1, phạt `reg_lambda` mặc định 1)
  tác động trên cùng thang toàn cục. Nếu dùng đúng 1/n_s thì tổng trọng số chỉ bằng
  số người, và một lá cần trọng số tương đương cả một người mới được tách
  (Codex review 2026-10-25 đồng ý giữ trung bình 1).
- Đặc trưng, siêu tham số, seed B3 và bootstrap giữ như v0 (quyết định B3/B4 ở
  trên).

Report v1 có thêm `reader`, `label_qc` và `train_weighting`. `split_counts` của
train/val là số dòng/người **sau** QC, đúng tập được fit và chấm.

## Chạy

```powershell
.\.venv\Scripts\python.exe scripts/build_pulsedb_split.py --config data/processed/linh_split_config.json --output data/processed/pulsedb_split_run_01
.\.venv\Scripts\python.exe scripts/run_b3_pulsedb.py --raw <đường dẫn .mat> --split-dir data/processed/pulsedb_split_run_01
```

Tùy chọn: `--config` (mặc định `configs/models/b3_pulsedb_v0.json`) và
`--output` (thư mục mới). Với v0, reader nạp toàn bộ file vào RAM. Với v1, reader
`h5py` chỉ đọc các dòng inventory, mỗi lần một khối. Cả hai đều hash lại mọi dòng
inventory.

v0 từ chối ngay (trước khi đọc raw) split có `subject_subsample`, vì inventory
của nó chỉ gồm một phần dòng của file. Pool Train 400 người (2026-10-25):

```powershell
.\.venv\Scripts\python.exe scripts/build_pulsedb_split.py --config configs/data/pulsedb_train400_split.json --output data/processed/pulsedb_train400_split_run01
.\.venv\Scripts\python.exe scripts/run_b3_pulsedb.py --raw data/raw/pulsedb/VitalDB_Train_Subset.mat --split-dir data/processed/pulsedb_train400_split_run01 --config configs/models/b3_pulsedb_v1.json
```

## Đầu ra `runs/b3_pulsedb/<UTC>/`

| File | Nội dung |
| --- | --- |
| `report.json` | Config, hash input, `pool_decision`, số người/đoạn mỗi split, B0, metrics/CI, log kiểm tra, giới hạn, commit, hash code (`sha256_lf`), môi trường, `outputs_sha256` của bốn file dưới; không có ID người. Ghi **sau cùng**: thiếu file này nghĩa là lần chạy không hoàn tất |
| `baseline_table.md` | Bảng B0/B3 riêng SBP/DBP trên val, sinh bằng mã; không có ID người |
| `predictions_val.csv` | `sample_id, subject_id, split, model, pred_sbp, pred_dbp`; **có ID**, giữ ngoài Git |
| `xgboost_sbp.json`, `xgboost_dbp.json` | Model B3 |

## Tái lập

Cùng raw, split, config, code và môi trường cho cùng metrics, cùng file dự
đoán và cùng file model theo từng byte. Test kiểm tra điều này trên dữ liệu
SYNTHETIC. Lần chạy đầu trên raw thật (2026-10-25, `b3-pipeline-v1`, PulseDB
Train 400 người): [kết quả và hash](../../reports/weekly/week_05/pulsedb_b3_v1/README.md).
Hash config model và code tính trên nội dung
đã đổi CRLF thành LF (như blob trong Git), nên không phụ thuộc checkout Windows hay
Linux; raw, inventory, manifest, config split và output vẫn hash theo byte.

## Ghi nhận và việc còn mở

- Bản cũ đã chạy và công bố MAE trên test (`docs/testing.md`,
  `notebooks/metrics_all_splits.csv`, gỡ khỏi Git ngày 2026-10-24, còn trong lịch
  sử ở commit `acc8b8b`; notebook `week4-train-xgboost.ipynb`).
  Không được dùng các số đó để chọn model; cần ghi sai lệch này vào báo cáo.
- CSV 1.000 đoạn lịch sử không chạy được với runner này vì không có inventory.
- Pool đã chốt ngày 2026-10-24: `VitalDB_Train_Subset`, mẫu con 400 người (seed
  20261024), CalFree Test làm tập kiểm tra ngoài
  ([provenance](../pulsedb_provenance.md)). Runner chỉ kiểm tra trường
  `pool_decision` có mặt, không đánh giá nội dung.

**Kế hoạch `b3-pipeline-v1` (chốt 2026-10-24; đã triển khai ngày 2026-10-25, xem
mục `b3-pipeline-v1` ở trên; `b3-pipeline-v0` giữ nguyên hành vi):**

- Đọc pool Train bằng reader đọc từng phần (`h5py`), chỉ các dòng của 400 người đã
  chọn.
- QC nhãn: loại dòng DBP ≥ SBP khỏi fit và chấm điểm ở mọi split, báo số dòng loại
  theo split và phân bố hiệu áp trên train (provenance mục 9).
- **Trọng số theo người:** mỗi dòng train nặng 1/n_s (n_s = số dòng còn lại của người
  đó sau QC). B0 là trung bình của các trung bình theo người; B3 truyền
  `sample_weight` cho XGBoost. Lý do: chỉ số chính là MAE trung bình đều theo người;
  trọng số theo dòng làm người có nhiều đoạn nặng hơn.
- Báo hiệu B3 − B0 ghép cặp như v0 (đã có).
- Cần CI trên Python 3.11; `xgboost` 3.3 trở lên yêu cầu Python ≥ 3.12, nên repo
  pin 3.2.0.

## Kiểm tra

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_b3_pipeline.py
.\.venv\Scripts\python.exe -m ruff check .
```
