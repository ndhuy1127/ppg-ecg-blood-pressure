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
3. Config [b3_pulsedb_v0.json](../../configs/models/b3_pulsedb_v0.json).

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

## B3

[xgboost_baseline.py](../../software/models/xgboost_baseline.py): hai
`XGBRegressor` riêng cho SBP và DBP. Tham số và seed đặt trong config;
`n_jobs` phải là số nguyên dương cố định để kết quả tái lập. Không có
imputation, chuẩn hóa hay chọn đặc trưng. Mỗi dòng train có trọng số bằng nhau,
nên người có nhiều đoạn có ảnh hưởng lớn hơn. Siêu tham số giữ nguyên bản của
Linh, **chưa tuning**. Nếu tuning sau này thì chỉ dùng val.

## Chạy

```powershell
.\.venv\Scripts\python.exe scripts/build_pulsedb_split.py --config data/processed/linh_split_config.json --output data/processed/pulsedb_split_run_01
.\.venv\Scripts\python.exe scripts/run_b3_pulsedb.py --raw <đường dẫn .mat> --split-dir data/processed/pulsedb_split_run_01
```

Tùy chọn: `--config` (mặc định `configs/models/b3_pulsedb_v0.json`) và
`--output` (thư mục mới). Reader nạp toàn bộ file vào RAM; inventory được
hash lại cho mọi dòng.

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
SYNTHETIC. Chưa chạy trên raw thật. Hash config model và code tính trên nội dung
đã đổi CRLF thành LF (như blob trong Git), nên không phụ thuộc checkout Windows hay
Linux; raw, inventory, manifest, config split và output vẫn hash theo byte.

## Ghi nhận và việc còn mở

- Bản cũ đã chạy và công bố MAE trên test (`docs/testing.md`,
  `notebooks/metrics_all_splits.csv`, notebook `week4-train-xgboost.ipynb`).
  Không được dùng các số đó để chọn model; cần ghi sai lệch này vào báo cáo.
- CSV 1.000 đoạn lịch sử không chạy được với runner này vì không có inventory.
- Cần chốt nội dung `pool_decision`: `VitalDB_AAMI_Cal_Subset` trùng người với
  AAMI Test. Runner chỉ kiểm tra trường này có mặt, không đánh giá nội dung. Xem
  [provenance](../pulsedb_provenance.md).
- Cần CI trên Python 3.11; `xgboost` 3.3 trở lên yêu cầu Python ≥ 3.12, nên repo
  pin 3.2.0.

## Kiểm tra

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_b3_pipeline.py
.\.venv\Scripts\python.exe -m ruff check .
```
