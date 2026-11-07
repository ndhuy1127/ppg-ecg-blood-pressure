# Theo dõi thí nghiệm và kiểm tính tất định nhiều seed

> **Trạng thái:** viết ngày 2026-11-07 theo kế hoạch Tuần 6 (theo dõi thí nghiệm, mục 1–2
> của phần Linh). Không thêm dependency: không dùng MLflow, chỉ dùng các `report.json` mà
> runner đã ghi, cộng một thư mục bảng tổng hợp trong `runs/` (ngoài Git). Chỉ dùng val;
> test và CalFree không được đọc.

## 1. Mỗi kết quả truy ngược được tới đâu

Mỗi runner (`run_b3_pulsedb.py`, `run_b2_pulsedb.py`) ghi `report.json` **cuối cùng**, sau
mọi file khác, nên có `report.json` nghĩa là lần chạy đã xong. `report.json` đã có sẵn những
gì kế hoạch đòi; [run_registry.py](../../software/evaluation/run_registry.py) đọc lại thành
một dòng cho mỗi lần chạy, bảng, model và đầu ra (SBP, DBP):

| Trường | Lấy từ `report.json` |
| --- | --- |
| `experiment`, `run_id` | Tên thư mục (mục 2) |
| `git_commit`, `workspace_has_changes` | `code_provenance` (có thay đổi chưa commit thì bảng đánh dấu `*`; SHA-256 từng file mã vẫn ở `report.json`) |
| `config_sha256` | `inputs_sha256.config` (config mang cả seed) |
| `raw_sha256`, `split_inventory_sha256`, `split_manifest_sha256` | `inputs_sha256` |
| `model_seeds`, `bootstrap_seed` | `config` (mọi mục có `seed`, trừ `bootstrap`; ví dụ `b3=42`) |
| `evaluation_split` | `config.evaluation_split`; khác `val` thì không được ghi vào bảng |
| Metrics | MAE và bias trung bình đều theo người, SD theo mẫu, cùng CI bootstrap theo người |

Báo cáo thiếu một trường truy vết, không phải lần chạy model, hay chấm trên tập khác val thì
được liệt kê ở mục "Skipped" kèm lý do, không bị bỏ im lặng. Thư mục không có `report.json`
(chạy dở, hoặc runner cũ như `run_b0_pulsedb_csv.py`) cũng được liệt kê.

## 2. Quy ước tên thí nghiệm và artifact (khóa 2026-11-07)

- Mỗi thí nghiệm một thư mục `runs/<experiment>/`, tên viết thường, gạch dưới:
  `b3_pulsedb`, `b2_pulsedb`, `b3_multiseed`. Thí nghiệm mới thì thêm tên mới, không dùng
  lại tên cũ cho phương pháp khác.
- Mỗi lần chạy một thư mục con mới `<UTC>` dạng `20261107T093000123456Z`; runner từ chối ghi
  đè. Lần chạy nhiều seed có thư mục con `seed_<n>/` cho từng seed.
- Bảng tổng hợp ở `runs/registry/<UTC>/` (`runs.csv`, `runs.md`, `report.json`). Đây là
  bảng sinh ra từ các `report.json`; không sửa số bằng tay. Bảng mới thì chạy lại lệnh.
- Dự đoán theo dòng (`predictions_val*.csv`) có ID người, nên `runs/` luôn ở ngoài Git. Báo
  cáo tuần chỉ chép bảng tổng hợp và hash.

## 3. Kiểm tính tất định nhiều seed

Kế hoạch Tuần 6 (sửa 2026-10-29): B0 không có seed; B3 v1 không lấy mẫu con (không có
`subsample`, `colsample_*`), nên đổi seed của XGBoost không được làm đổi kết quả. Lần chạy
nhiều seed vì vậy chỉ kiểm tính tất định, kỳ vọng SD = 0. Độ bất định lấy từ CI bootstrap
theo người của từng lần chạy, không lấy từ độ lệch giữa các seed. Không đổi seed split 72,
không đổi seed bootstrap, không thêm lấy mẫu con để tạo phương sai.

[run_b3_multiseed.py](../../scripts/run_b3_multiseed.py) chạy B3 runner một lần cho mỗi seed
(mặc định 42, 43, 44) với config chỉ khác `b3.seed`, rồi:

- so SHA-256 của `predictions_val.csv` giữa các seed;
- so từng metrics điểm (`seed_spread`): min, max, max − min, SD (`ddof=1`);
- ghi `status`: `DETERMINISTIC` khi dự đoán trùng từng byte và mọi max − min = 0, ngược lại
  `DIFFERS`. `DIFFERS` là một phát hiện phải báo, không lấy trung bình.

Các lần chạy được so phải trùng commit, raw, split, seed bootstrap và tập chấm; khác thì
dừng, vì khi đó không chỉ seed thay đổi.

## 4. Cách chạy

```powershell
python scripts/run_b3_multiseed.py --raw data/raw/pulsedb/VitalDB_Train_Subset.mat `
  --split-dir data/processed/pulsedb_train400_split_run01
python scripts/collect_runs.py
```

`collect_runs.py` mặc định đọc `b3_pulsedb`, `b2_pulsedb`, `b3_multiseed`; chọn khác bằng
`--experiments`. Mỗi lần B3 đọc lại raw bằng reader `h5py` từng khối (khoảng 3 phút một lần
trên máy của nhóm).

## 5. Test

[tests/test_run_registry.py](../../tests/test_run_registry.py), báo cáo dựng tay, không đọc
dữ liệu: đủ trường truy vết; báo cáo B2 hai bảng; từ chối báo cáo không phải val, thiếu
commit, hash sai, không phải lần chạy model; CI hỏng vẫn giữ dòng; SD = 0 khi giống nhau và
bắt được khác biệt; từ chối so các lần chạy khác nhau ngoài seed; config nhiều seed chỉ khác
`b3.seed`; `collect` liệt kê đủ lần chạy và lý do bỏ qua, không ghi đè.

## 6. Giới hạn

- Chỉ đọc báo cáo của runner hiện có; `run_b0_pulsedb_csv.py` (bản cũ, `metrics.json`) chưa
  được đọc, chỉ được liệt kê.
- Bảng không thay cho việc đọc `limitations` trong từng `report.json`.
- Tính tất định được kiểm trên một máy (Windows, Python 3.11.9, xgboost 3.2.0); máy hay bản
  thư viện khác có thể cho số khác ở chữ số cuối.
