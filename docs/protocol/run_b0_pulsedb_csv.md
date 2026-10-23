# Chạy B0 từ CSV PulseDB của Linh

Đây là runner mới cho API B0/metrics Tuần 3, chỉ fit train và đánh giá val.
Không đổi split, đọc waveform, dùng nhãn test, hoặc chạy B1. Kết quả là mô tả
BP tuyệt đối trên các dòng nhãn ABP công khai; chưa thay đánh giá cuff/ΔBP.

## Đầu vào

CSV UTF-8 có các cột `sample_id,subject_id,source,split,sbp,dbp,sample_hash`.
Giữ nguyên giá trị split `train`, `val`, `test` của Linh. Xác nhận đơn vị mmHg
từ tài liệu nguồn. Lưu CSV ngoài Git, ví dụ `data/processed/linh_week03/`.

CSV không được kèm trong commit runner, và từ 2026-10-24 không còn trong cây Git
hiện tại. Để chạy trên máy khác, lấy đúng file
`notebooks/pulsedb_manifest_1000.csv` từ commit `1f218eb` (nhánh `dev/ngoclinh`:
`git show 1f218eb:notebooks/pulsedb_manifest_1000.csv`, hoặc Raw trên GitHub), rồi
lưu tại
`data/processed/linh_week03/pulsedb_manifest_1000.csv`. Giữ nguyên bytes của
file, không mở và lưu lại bằng Excel. So SHA256 với `manifest_sha256` trong
`configs/data/b0_pulsedb_validation.json`:

```powershell
Get-FileHash -Algorithm SHA256 data/processed/linh_week03/pulsedb_manifest_1000.csv
```

Hash khớp chỉ xác nhận đúng CSV đã bàn giao; không thay xác minh raw/nguồn.

Runner kiểm tra header, metadata, khóa source/sample_id trùng, giao người và
sample_hash giao split. Nhãn train/val phải là số hữu hạn. Không tự bỏ dòng.
Chỉ xem metadata của test để kiểm tra leakage, không dùng nhãn BP của test.

Với CSV split v2 có cột `waveform_hash`, runner yêu cầu SHA256 lowercase hợp lệ
và từ chối hash waveform xuất hiện ở nhiều split, kể cả khi ID/nhãn và
`sample_hash` khác nhau. Bản lặp trong cùng split được giữ nguyên. CSV lịch sử
không có cột này vẫn chạy và log ghi rõ chưa kiểm tra waveform-only leakage.
Không đổi split, trọng số hoặc cách dùng nhãn test. Kiểm tra này không thay
`validate_manifest(manifest, inventory)` của pipeline split: phải đối chiếu
inventory, raw/hash và report bàn giao trước đánh giá chính thức.

## Chạy

Mở `scripts/run_b0_pulsedb_csv.py` trong VSCode và bấm **Run Python File in
Terminal**. Khi không có đối số, script đọc
`configs/data/b0_pulsedb_validation.json`: CSV cục bộ đã bàn giao, đơn vị mmHg,
seed 72, ref `1f218eb` và hash CSV đã ghi nhận. Đường dẫn CSV được tính từ repo,
không phụ thuộc thư mục Terminal. Script không tự tải dữ liệu nếu file thiếu.

```powershell
python scripts/run_b0_pulsedb_csv.py
```

Hash mặc định phải khớp CSV đã ghi nhận. Với CSV khác, truyền đường dẫn và
`--unit mmHg` rõ ràng; seed/ref của cấu hình mặc định không tự áp sang CSV mới.

Từ checkout có baseline/metrics của Huy:

```powershell
python scripts/run_b0_pulsedb_csv.py data/processed/linh_week03/pulsedb_manifest_1000.csv --unit mmHg --split-seed 72 --manifest-ref 1f218eb
```

Seed 72 được ghi từ code notebook `week3-split-hash.ipynb` của Linh ở commit
`1f218eb`. Runner không chia lại dữ liệu. Khi dùng bản bàn giao khác, chỉ ghi
seed đúng theo bằng chứng của bản đó; không tự giả định 72.

Đầu ra gồm mức B0, số mẫu/người từng split, MAE/bias/SD theo dòng, MAE/bias
trung bình đều theo người. File `runs/b0_pulsedb/<run>/metrics.json` lưu config,
hash CSV, seed split nếu biết, môi trường, commit và hash các file code, trạng
thái workspace, log kiểm tra và giới hạn. Không lưu bảng/ID từng người.
Mỗi lần chạy tạo thư mục mới. `--output` tùy chọn nhận đường dẫn JSON mới;
script từ chối ghi đè file đã tồn tại.

## Giới hạn

- Notebook Linh đọc `file_paths[0]` nhưng ghi tên source cố định; cần xác nhận
  checksum/tên file thực đọc. CSV không tự chứng minh metadata source đúng.
- sample_hash gồm cả metadata và waveform theo code notebook; runner chỉ
  kiểm tra chuỗi hash trong CSV, chưa tái tạo hash từ raw.
- Xác nhận mapping người, việc chọn pool 100 người × 10 đoạn và cách chia lại
  subset so với các holdout gốc; sample_id đánh lại không thay index raw gốc.
- B0 tính trung bình đều theo dòng; trọng số và đơn vị quan sát chưa chốt.
- Không có chronology/calibration nên chưa chạy B1 trên CSV này.
- Test runner dùng dữ liệu tự tạo; không thay CI Python 3.11.

## Kiểm tra runner

```powershell
python -m pytest -q tests/test_b0_pulsedb_csv.py tests/test_week_03_baselines.py tests/test_bp_metrics.py -p no:cacheprovider
python -m ruff check .
```
