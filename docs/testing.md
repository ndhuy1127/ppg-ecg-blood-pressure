# Hướng dẫn kiểm thử Pipeline PulseDB

> **Tài liệu lịch sử.** Mô tả pipeline cũ của commit `acc8b8b`. Các file
> `software/pulsedb/train.py` và `evaluate.py` đã bị xóa, nên lệnh ở mục 5 và 8
> không còn chạy. Pipeline hiện tại: [run_b3_pulsedb.md](protocol/run_b3_pulsedb.md).
> Pipeline cũ đã chấm điểm trên tập **test**; không dùng số ở mục 7 để chọn model.
> Số ở mục 7 cũng không khớp `notebooks/metrics_all_splits.csv` (ví dụ SBP val
> 20.16 so với 20.66). Chưa rõ nguyên nhân vì không có log chạy.
> Hai CSV `notebooks/pulsedb_manifest_1000.csv` và `notebooks/metrics_all_splits.csv`
> đã gỡ khỏi Git ngày 2026-10-24 (còn trong lịch sử, commit `1f218eb`, `acc8b8b`);
> các lệnh dưới đây cần lấy lại file bằng `git show` trước khi chạy.

## 1. Mục đích

Tài liệu này hướng dẫn cách chạy kiểm thử pipeline dự đoán huyết áp từ tín hiệu ECG và PPG, kiểm tra tính hợp lệ của Manifest và xác nhận các file kết quả được tạo ra.

## 2. Yêu cầu môi trường

- Python 3.11 trở lên.
- Đã cài đặt các thư viện trong môi trường ảo `.venv`.
- Đã có dữ liệu PulseDB tại `data/pulsedb_data/VitalDB_AAMI_Cal_Subset.mat`.
- Đã có Manifest tại `notebooks/pulsedb_manifest_1000.csv`.

Kích hoạt môi trường ảo trước khi chạy lệnh kiểm thử:

```bash
source .venv/bin/activate
```

## 3. Kiểm thử tự động

Tại thư mục gốc của project, chạy:

```bash
pytest -v
```

Lệnh này chạy các test được khai báo trong thư mục `tests/` và hiển thị tên từng test cùng kết quả.

**Kết quả mong đợi:** tất cả test đều vượt qua, không có test thất bại.

Ví dụ kết quả đã ghi nhận:

```text
7 passed in 0.10s
```

Kết quả trên xác nhận 7 test hiện có đã vượt qua tại thời điểm chạy.

## 4. Kiểm tra tính hợp lệ của Manifest

Manifest được sử dụng để xác định mẫu dữ liệu và tập train, validation, test.

Các nội dung cần kiểm tra:

- Có đủ các cột bắt buộc: `sample_id`, `subject_id`, `source`, `split`, `sbp`, `dbp`, `sample_hash`.
- Không có `sample_id` trùng lặp.
- Các giá trị `split` chỉ thuộc `train`, `val`, `test`.
- Không có một `subject_id` xuất hiện ở nhiều tập dữ liệu.
- Hash của từng mẫu khớp với dữ liệu được đọc từ file `.mat`.

Kết quả đối chiếu đã ghi nhận:

| Nội dung | Kết quả |
|---|---:|
| Số mẫu trong Manifest | 1.000 |
| Số segments được chọn | 1.000 |
| Subject khớp theo thứ tự | True |
| Hash khớp theo thứ tự | True |
| Số hash khớp | 1.000 |

Các kết quả này cho thấy 1.000 mẫu được chọn khớp với Manifest theo thứ tự kiểm tra.

## 5. Chạy toàn bộ pipeline

Chạy lệnh sau tại thư mục gốc của project:

```bash
python -m software.pulsedb.pipeline \
  --data "data/pulsedb_data/VitalDB_AAMI_Cal_Subset.mat" \
  --manifest "notebooks/pulsedb_manifest_1000.csv"
```

Pipeline thực hiện các bước chính:

1. Đọc dữ liệu PulseDB.
2. Kiểm tra cấu trúc và tính hợp lệ của Manifest.
3. Đối chiếu `subject_id` giữa dữ liệu và Manifest.
4. Trích xuất đặc trưng từ ECG và PPG.
5. Huấn luyện mô hình dự đoán SBP và DBP trên tập train.
6. Đánh giá mô hình trên tập validation và test.
7. Lưu các file kết quả.

**Kết quả mong đợi:** pipeline hoàn thành mà không phát sinh lỗi và hiển thị bảng đánh giá mô hình.

## 6. Kiểm tra các file đầu ra

Sau khi pipeline chạy thành công, thực hiện:

```bash
ls -lh outputs
```

Các file đầu ra đã được tạo trong lần chạy trước:

| File | Mục đích |
|---|---|
| `features.csv` | Lưu các đặc trưng đã trích xuất |
| `metrics.csv` | Lưu các chỉ số đánh giá mô hình |
| `xgboost_sbp.json` | Lưu mô hình dự đoán SBP |
| `xgboost_dbp.json` | Lưu mô hình dự đoán DBP |

Có thể kiểm tra bảng chỉ số bằng:

```bash
cat outputs/metrics.csv
```

## 7. Kết quả đánh giá đã ghi nhận

| Tập dữ liệu | Mục tiêu | Số mẫu | MAE (mmHg) |
|---|---|---:|---:|
| Validation | SBP | 100 | 20.16 |
| Validation | DBP | 100 | 9.96 |
| Test | SBP | 100 | 21.44 |
| Test | DBP | 100 | 10.29 |

Đây là kết quả ban đầu của mô hình sử dụng các đặc trưng thống kê đơn giản từ ECG và PPG. Các chỉ số này cần được cải thiện và không được xem là bằng chứng về khả năng sử dụng lâm sàng.

## 8. Lưu bằng chứng kiểm thử

Để lưu log kiểm thử tự động:

```bash
mkdir -p evidence
pytest -v 2>&1 | tee evidence/pytest.log
```

Để lưu log chạy pipeline:

```bash
python -m software.pulsedb.pipeline \
  --data "data/pulsedb_data/VitalDB_AAMI_Cal_Subset.mat" \
  --manifest "notebooks/pulsedb_manifest_1000.csv" \
  2>&1 | tee evidence/pipeline_run.log
```

Sau khi chạy, kiểm tra các file log trong thư mục `evidence/`. Chỉ ghi nhận kiểm thử thành công khi lệnh kết thúc bình thường và log thể hiện kết quả tương ứng.

## 9. Tiêu chí hoàn thành

- [ ] Các test tự động đều vượt qua.
- [ ] Manifest hợp lệ, không có subject leakage.
- [ ] Hash của mẫu khớp với dữ liệu nguồn.
- [ ] Pipeline chạy hoàn chỉnh.
- [ ] Các file đầu ra được tạo và đọc được.
- [ ] Log kiểm thử được lưu để đối chiếu khi nghiệm thu.

**Lưu ý:** Không đưa toàn bộ dataset PulseDB dung lượng lớn lên Git. Chỉ đưa mã nguồn, tài liệu hướng dẫn và các bằng chứng cần thiết theo quy định của project.
