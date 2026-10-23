# Báo cáo tiến độ Tuần 4

> **Giai đoạn:** Tuần 4 / 28 tuần (2026-10-11 → 2026-10-20)
>
> **Thành viên:** Linh, Trương Đức Anh, Nguyễn Đức Huy

## 1. Tóm tắt công việc của tuần (mục tiêu)

Theo [kế hoạch Tuần 4](../../../docs/plans/WEEK_04.md), tuần này dựng baseline đầu
tiên và hoàn thiện thiết kế mạch:

1. Pipeline đọc dữ liệu → đặc trưng → huấn luyện → đánh giá; baseline B3 XGBoost
   dự đoán SBP/DBP, so với B0 trên cùng split.
2. Hoàn thiện schematic V1 và pin map.
3. Bộ đặc trưng/SQI v0, kiểm tra mốc R/foot/PAT, bootstrap theo người.

## 2. Thành viên phụ trách và phân công công việc

| Thành viên | Công việc Tuần 4 |
| --- | --- |
| Linh | Pipeline PulseDB với đặc trưng ECG/PPG đơn giản, B3 XGBoost, tài liệu kiểm thử pipeline |
| Đức Anh | Sửa schematic V1, pin map V1 cho ESP32-S3-DevKitC-1 |
| Huy | Đặc trưng/SQI v0, mốc R/foot và ghép PAT, bootstrap theo người, API đánh giá bảng dự đoán; đưa B3 lên split v2; tài liệu phần cứng V1-module và thiết kế KiCad; cập nhật y văn |

## 3. Tóm tắt công việc đã hoàn thành của từng người

### Linh

- Pipeline PulseDB đầu tiên: `features.py` (12 đặc trưng thống kê ECG/PPG),
  `pipeline.py`, `train.py`, `evaluate.py`.
- Notebook huấn luyện XGBoost (`week4-train-xgboost.ipynb`) và bảng metrics theo split.
- Tài liệu kiểm thử pipeline (`docs/testing.md`) và cập nhật provenance PulseDB.

### Đức Anh

- Sửa schematic V1 (`V1.SchDoc`).
- Viết pin map V1: MAX30001 và BMI270 chung bus SPI (SCK GPIO11, MOSI GPIO10, MISO
  GPIO13, CS riêng GPIO14/GPIO12); PPG qua I²C (SDA GPIO8, SCL GPIO9, INT GPIO6);
  ngắt ECG GPIO5, IMU GPIO4.

### Huy

- **Đặc trưng/SQI `features-sqi-v1`:** 8 đặc trưng PPG/HR/PAT có tên, công thức,
  đơn vị, điều kiện và lý do thiếu; nhãn/ABP không tham gia trích đặc trưng hay SQI.
- **Mốc tín hiệu:** R bằng prominence/refractory, PPG foot bằng tiếp tuyến tại
  sườn lên cực đại, ghép nhịp R → foot duy nhất; hỗ trợ fs riêng từng kênh,
  timestamp s/ms/µs, độ trễ upstream.
- **SQI:** kiểm tra giá trị hữu hạn, tín hiệu phẳng, số nhịp, hình dạng và ghép PAT;
  trả cờ và lý do, không tự loại hay sửa raw.
- **Bootstrap theo người:** CI percentile 95%, seed 20261013, 2000 lượt, lấy lại
  cụm người giữ toàn bộ quan sát; các model dùng chung lượt lấy mẫu.
- **API `evaluate_prediction_table`:** kiểm tra bảng dự đoán với inventory/manifest
  v2 (ID mẫu, người, split, thiếu/thừa/trùng dòng).
- Runner fixture analytic sinh JSON/CSV/SVG có hash config/code/input/hình.
- Sửa lỗi foot ở nhịp tim cao: khi RR < 0,5 s, hai nhịp có thể dùng chung một
  valley; trên 3.000 cửa sổ giả lập (RR 0,41–1,2 s) có 7 lần dừng batch trước khi
  sửa, 0 lần sau khi sửa.
- **B3 trên split v2:** chuyển pipeline B3 của Linh sang runner `run_b3_pulsedb.py`:
  đọc raw `.mat` + thư mục split v2, kiểm hash raw với inventory, fit B0/B3 trên
  train, chấm điểm chỉ trên val, không trích đặc trưng tập test; `XGBoostBaseline`
  một regressor cho mỗi đầu ra, seed và `n_jobs` cố định.
- Làm chặt reader/validator PulseDB, split và hash provenance không phụ thuộc CRLF.
- **Phần cứng V1-module:** tài liệu V1 dùng module (Phần A) và bản chip trần (Phần
  B), bảng nguồn/giao tiếp/lấy mẫu V0, kế hoạch đo đồng bộ 10 phút trên bench,
  thiết kế KiCad bo đế và bo cổ tay.
- **Y văn:** bổ sung nguồn 2015–2026 cho RQ1–RQ3 (khuyến cáo validation ESH 2023,
  AHA 2025, Mukkamala 2021; dự án Aurora; SQI và risk–coverage), cập nhật RQ và protocol.

## 4. Danh mục sản phẩm đầu ra và đường dẫn

| STT | Sản phẩm | Người làm | Đường dẫn |
| --- | --- | --- | --- |
| 1 | Notebook huấn luyện XGBoost | Linh | [week4-train-xgboost.ipynb](../../../notebooks/week4-train-xgboost.ipynb) |
| 2 | Tài liệu kiểm thử pipeline (bản commit `acc8b8b`) | Linh | [testing.md](../../../docs/testing.md) |
| 3 | Đặc trưng thống kê ECG/PPG | Linh (Huy chỉnh lại) | [features.py](../../../software/pulsedb/features.py) |
| 4 | Schematic V1 (bản sửa) | Đức Anh | [V1.SchDoc](https://github.com/ndhuy1127/ppg-ecg-blood-pressure/blob/bb6605bcadd93390fd6de3aae12c517ce7960ec1/hardware/schematics/V1.SchDoc) (Altium; nhánh `dev/ducanh`, commit `bb6605b`); bản hiện hành: [KiCad V1-module](../../../hardware/kicad/v1_module/) |
| 5 | Pin map V1 | Đức Anh | [Pin_Map_V1.md](https://github.com/ndhuy1127/ppg-ecg-blood-pressure/blob/9073aa81a58757f28dffd52f42fb15369ae5cd86/configs/hardware/Pin_Map_V1.md) (nhánh `dev/ducanh`, commit `9073aa8`); bản hiện hành: [custom_board_proposal.md](../../../configs/hardware/custom_board_proposal.md) A.7 |
| 6 | Mốc R/foot, ghép PAT | Huy | [fiducials.py](../../../software/signal_processing/fiducials.py) |
| 7 | Đặc trưng/SQI | Huy | [week04.py](../../../software/feature_extraction/week04.py) |
| 8 | Bootstrap, đánh giá bảng dự đoán | Huy | [subject_bootstrap.py](../../../software/evaluation/subject_bootstrap.py) |
| 9 | Config ngưỡng và bootstrap | Huy | [week04_huy.json](../../../configs/data/week04_huy.json) |
| 10 | Định nghĩa, API, ví dụ | Huy | [week04_features_sqi_bootstrap.md](../../../docs/protocol/week04_features_sqi_bootstrap.md) |
| 11 | Runner fixture | Huy | [demo_week04_huy.py](../../../scripts/demo_week04_huy.py) |
| 12 | Test Tuần 4 | Huy | [test_week04_features.py](../../../tests/test_week04_features.py), [test_subject_bootstrap.py](../../../tests/test_subject_bootstrap.py) |
| 13 | Kết quả fixture | Huy | [fixture_checks.json](fixture_checks.json), [fixture_features.csv](fixture_features.csv), [verification.txt](verification.txt) |
| 14 | Hình R/foot/PAT fixture | Huy | [week04_synthetic_fiducials.svg](../../figures/week04_synthetic_fiducials.svg) |
| 15 | Runner B0/B3 trên split v2 | Huy | [run_b3_pulsedb.py](../../../scripts/run_b3_pulsedb.py), [pipeline.py](../../../software/pulsedb/pipeline.py), [xgboost_baseline.py](../../../software/models/xgboost_baseline.py), [b3_pulsedb_v0.json](../../../configs/models/b3_pulsedb_v0.json), [test_b3_pipeline.py](../../../tests/test_b3_pipeline.py), [hướng dẫn](../../../docs/protocol/run_b3_pulsedb.md) |
| 16 | Tài liệu phần cứng V1-module | Huy | [custom_board_proposal.md](../../../configs/hardware/custom_board_proposal.md), [interface_power_sampling_v0.md](../../../configs/hardware/interface_power_sampling_v0.md), [sync_10min_test_plan.md](../../../hardware/test_reports/sync_10min_test_plan.md) |
| 17 | Thiết kế KiCad V1-module | Huy | [hardware/kicad/v1_module/](../../../hardware/kicad/v1_module/) |
| 18 | Y văn bổ sung | Huy | [literature_update_2026-10-14.md](../../../docs/literature/literature_update_2026-10-14.md) |

Ghi chú mục 13: các file kết quả fixture là lần chạy ngày 2026-10-13 bằng
`features-sqi-v0` (commit `8472721`, working tree chưa commit) và được giữ làm bản
ghi lịch sử, không sinh lại. Code hiện hành là `features-sqi-v1` (commit `645df5d`:
nhịp sát biên không bị tính là PAT không ghép). Ngày 2026-10-24 chạy lại runner vào
thư mục tạm: đặc trưng, cờ và tóm tắt trùng với bản v0. Có hai khác biệt: mỗi dòng
có thêm `pat_edge_unpaired_r_count` và `pat_edge_unpaired_foot_count` (đều bằng 0),
và trạng thái bootstrap là `few_subjects` (3 người, quy tắc thêm ngày 2026-10-23).
Hành vi v1 được kiểm bằng [test_week04_features.py](../../../tests/test_week04_features.py).

## 5. Tóm tắt các nội dung chuyên môn chính

### 5.1. Đặc trưng v1 (Huy)

| Đặc trưng | Định nghĩa |
| --- | --- |
| `ppg_std` | SD `ddof=0` của PPG đã xử lý |
| `ppg_amplitude_median` | Median (peak − valley trước peak) |
| `ppg_rise_time_median_ms` | Median (peak − foot tiếp tuyến), ms |
| `ppg_width50_median_ms` | Median độ rộng tại nửa biên độ, ms |
| `ppg_hr_bpm` | 60 / median khoảng foot liên tiếp |
| `ecg_hr_bpm` | 60 / median RR |
| `pat_median_ms` | Median (PPG foot − ECG R) × 1000, ms |
| `pat_iqr_ms` | P75 − P25 của PAT từng nhịp, ms |

- PAT là khoảng R peak → PPG foot (PAT = PEP + PTT), không gọi là PTT. PAT thiếu giữ
  `None`, không thành 0; không dùng PAT để suy ra lệch clock.
- Fixture SYNTHETIC: R tại 1..8 s, foot = R + 0,2 s, thời gian lên 160 ms, width50
  200 ms, HR 60 bpm. Trên 5 đoạn: 2 đoạn có đặc trưng PPG/HR, 1 đoạn có PAT, 4 đoạn
  gắn cờ.

### 5.2. Pipeline B3 (Linh, Huy)

- Đặc trưng `pulsedb-simple-stats-v0`: mean, std, min, max, range, rms cho ECG và
  PPG (12 đặc trưng), không nhận ABP, nhãn, ID hay hash.
- XGBoost: 300 cây, độ sâu 4, learning rate 0,05, seed 42, `n_jobs` 1.
- Fit trên train, đánh giá trên val; tập test không được trích đặc trưng.
- Bản pipeline đầu (`acc8b8b`) có chấm điểm trên test; các số đó không dùng để chọn
  mô hình, đặc trưng hay ngưỡng.

### 5.3. Phần cứng V1 (Đức Anh, Huy)

- Schematic V1 của Đức Anh: ESP32-S3 + MAX30001 + MAX30102 + BMI270; MAX30001 và
  BMI270 chung bus SPI.
- V1-module (Phần A): bo đế ESP32-S3-DevKitC-1 + breakout MAX30001 (SPI riêng),
  bo cổ tay MAX30101 (I²C riêng) + BMI270, cấp nguồn qua USB từ laptop chạy pin.
- Kế hoạch đo 10 phút trên bench: tốc độ lấy mẫu thực, drift, jitter của
  `T_ANCHOR_US`, độ trễ và lệch ECG–PPG, tỷ lệ mất packet; không dùng PAT để suy lệch clock.

## 6. Kết quả kiểm tra kỹ thuật

Chạy từ Git root bằng `.venv` (Python 3.13.12, NumPy 2.5.3, SciPy 1.18.1):

| Ngày | Lệnh | Kết quả |
| --- | --- | --- |
| 2026-10-13 | `python -B -m pytest -q -p no:cacheprovider` | **257 passed in 5.69s** (gồm 58 test Tuần 4) |
| 2026-10-13 | `python -m ruff check .` | Đạt |
| 2026-10-13 | `python scripts/check_environment.py`, `python -m pip check` | Đạt |
| 2026-10-13 | `python scripts/demo_week04_huy.py` | Exit 0, sinh JSON/CSV/SVG |
| 2026-10-13 | `git diff --check` | Đạt |
| 2026-10-14 | `pytest -q -p no:cacheprovider` sau khi sửa lỗi foot | **258 passed**; bảng fixture không đổi |

Test bao phủ: mốc/PAT đã biết, fs 250/125 và 512/128 Hz, cực tính, độ trễ, đơn vị
timestamp, gap, timestamp lỗi, tín hiệu thiếu/phẳng/NaN/Inf, nhịp thiếu, PAT mơ hồ,
hình dạng, số nhịp không đủ; bootstrap với người lặp, seed, ít người; bảng dự đoán
sai khớp; tương thích baseline/reader/manifest/metrics. Thêm test hồi quy RR 0,42 s
(fail khi bỏ bản sửa). Runner B3 có test SYNTHETIC trong `tests/test_b3_pipeline.py`:
đổi waveform hoặc nhãn test thì dự đoán không đổi.
