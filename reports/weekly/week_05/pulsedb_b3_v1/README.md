# B0/B3 trên PulseDB Train 400 người (`b3-pipeline-v1`, 2026-10-25)

Nhãn ABP công khai của PulseDB (`VitalDB_Train_Subset.mat`, Kaggle version 4). Đây
không phải nhãn cuff hay dữ liệu thiết bị. Chỉ đánh giá trên **val**. Tập test của
split và CalFree Test (tập kiểm tra ngoài) chưa được chấm.

## File

| File | Nội dung | SHA-256 bản gốc |
| --- | --- | --- |
| `baseline_table.md` | Bảng B0/B3 trên val, sinh bằng mã | `cad00ea4de97b3dd98ffe65aae297874e7ff1429e9068db727327b2efcb06829` |
| `b3_report.json` | `report.json` của runner: config, hash input, QC, metrics/CI, log kiểm tra, giới hạn, môi trường, hash code | `7e80fd30d285a0fc72d41ca9cabe7796ec41fe440ad4c29b4de7748c5f28a2f1` |
| `split_report.json` | `report.json` của split 400 người (`_run01`) | `d420bc878e3330ce485f11367afa1dba8109be8d91bffd332cc196bda9991b53` |
| `compare_readers_aami_test.json` | So reader `h5py` với `mat73` trên AAMI Test | — |

Bản gốc ở `runs/b3_pulsedb/20261024T193656162418Z/` và
`data/processed/pulsedb_train400_split_run01/` (ngoài Git). `predictions_val.csv`
chứa ID người nên không chép vào đây; SHA-256 của nó có trong `outputs_sha256` của
`b3_report.json`. Ba file JSON/bảng ở đây không chứa ID người.

Lần chạy dùng commit `4be5a6d` cộng các thay đổi chưa commit
(`workspace_has_changes: true`). Code đúng như lúc chạy được xác định bằng
`code_provenance.sha256_lf` (hash nội dung LF của từng file), không phải bằng commit.
Môi trường: Python 3.11.7, numpy 1.26.4, pandas 2.2.1, xgboost 3.2.0, h5py 3.16.0,
mat73 0.65 (đúng `requirements.txt`).

## Kết quả (val: 40 người, 14.400 đoạn)

| Model | Target | MAE theo người [CI 95%] | Bias theo người [CI 95%] | SD mẫu |
| --- | --- | --- | --- | ---: |
| B0 | SBP | 15,11 [13,47; 16,88] | 4,30 [0,79; 7,67] | 18,79 |
| B0 | DBP | 10,40 [9,12; 11,80] | 2,12 [−0,92; 5,14] | 12,78 |
| B3 | SBP | 14,58 [12,89; 16,49] | 3,96 [0,33; 7,52] | 18,39 |
| B3 | DBP | 10,12 [8,94; 11,44] | 1,44 [−1,56; 4,33] | 12,49 |

Hiệu ghép cặp B3 − B0 của MAE theo người: SBP −0,52 [−1,35; 0,58], DBP −0,28
[−0,86; 0,36] mmHg. CI 95% bootstrap theo người, 2.000 lượt, seed 20261013, cùng
lượt rút cho hai model. Cả hai khoảng đều chứa 0, nên **trên val chưa thấy B3 tốt
hơn B0**. Đơn vị mmHg; sai số = dự đoán − tham chiếu.

## Cách đọc

- Mỗi người có đúng 360 đoạn và QC loại 0 dòng, nên trọng số 1/n_s của v1 đều bằng
  1. Vì vậy MAE theo mẫu trùng MAE theo người, và B0 bằng trung bình train thường
  (SBP 116,07; DBP 63,44 mmHg).
- ECG/PPG của PulseDB Subset đã được chuẩn hóa min-max về [0, 1] theo từng đoạn
  ([provenance](../../../../docs/pulsedb_provenance.md) mục 6). `ecg_min`/`ppg_min`
  là hằng số. `max`/`range` chỉ khác nhau 1 ulp, và không cây nào chia theo chúng:
  model chỉ dùng `mean`, `std`, `rms` của hai kênh. Bộ đặc trưng
  `pulsedb-simple-stats-v0` gần như không còn thông tin biên độ, nên kết quả gần B0
  là đúng với dự đoán.
- Bias dương (B0 SBP +4,3 mmHg) đến từ việc trung bình SBP của val (111,8) thấp hơn
  của train (116,1); 40 người val là một mẫu nhỏ.
- Chưa tuning siêu tham số và chưa chọn model. Theo quyết định B3/B4 (2026-10-25),
  B3 giữ đơn giản để đóng baseline G1; PAT/HR/SQI để cho B4.

## Bối cảnh từ tài liệu (đọc ngày 2026-10-25)

Bài báo PulseDB ([PMC9944565](https://pmc.ncbi.nlm.nih.gov/articles/PMC9944565/),
mục 3.3) **không công bố số** cho ResNet-18 1D của họ trên CalFree; chỉ có đường cong
ở Hình 5. Bài báo ghi rằng tập CalFree có dấu hiệu quá khớp ngay trong 20 epoch
đầu, và lúc đầu mô hình dự đoán mọi giá trị bằng BP trung bình của train. Bảng 5
của bài tóm tắt bốn nghiên cứu khác, ở chế độ không hiệu chuẩn:

| Nghiên cứu (số tham chiếu trong bài PulseDB) | SBP: r / MAE (mmHg) | DBP: r / MAE (mmHg) |
| --- | --- | --- |
| [9] RNN, PPG | 0,44 / 14,39 | 0,44 / 6,57 |
| [10] CNN, PPG + ECG | 0,22 / 12,49 | 0,31 / 8,03 |
| [20] CNN, PPG + ECG | — / 9,30 | — / 5,12 |
| [12] CNN + RNN, PPG | — / 15,41 | — / 12,38 |

Bài kết luận rằng các mô hình này tổng quát hóa kém sang người chưa thấy. B3 ở đây
(SBP r 0,24, MAE 14,6; DBP r 0,23, MAE 10,1 trên val) nằm trong khoảng đó. Tuy vậy
**không so sánh trực tiếp được**: khác dataset, cách chia, nhãn và cách chọn đoạn.
Các số trên là nguồn thứ cấp (bảng tóm tắt của PulseDB), chưa đối chiếu với bài gốc.
