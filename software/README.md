# Phần mềm

Các module được tách theo trách nhiệm:

- **data_io/**: đọc, kiểm tra schema và ghi dữ liệu được phép.
- **preprocessing/**: làm sạch và chuẩn hóa tín hiệu.
- **signal_processing/**: xử lý ECG/PPG và đánh giá chất lượng tín hiệu.
- **feature_extraction/**: trích đặc trưng, gồm đặc trưng PAT theo định nghĩa.
- **models/**: huấn luyện và suy luận mô hình.
- **evaluation/**: chỉ số và quy trình đánh giá.
- **deployment/**: giao diện triển khai sau khi mô hình được thẩm định.

## Code đã có và nên đọc file nào

Đã có reader/validator PulseDB, split theo người có inventory, baseline B0/B1/B3,
mốc ECG/PPG và đặc trưng/SQI sơ bộ, bootstrap theo người, metrics BP và mô phỏng
packet. Các phần này được kiểm thử bằng dữ liệu giả lập; sự tồn tại của code không
chứng minh dataset/split đã được nghiệm thu. `preprocessing/` và `deployment/` chỉ
chứa `__init__.py`.

| File / thư mục | Làm gì | Dữ liệu đi qua |
| --- | --- | --- |
| [_bp_validation.py](_bp_validation.py) | Kiểm tra shape, kiểu số, giá trị hữu hạn và mã người dùng chung | Mảng BP `(n, 2)` hoặc danh sách ID được caller cung cấp |
| [_provenance.py](_provenance.py) | SHA-256 của file text tracked (code, config JSON) sau khi đổi CRLF thành LF | Byte file → hash không phụ thuộc checkout Windows/Linux |
| [pulsedb/reader.py](pulsedb/reader.py), [pulsedb/validator.py](pulsedb/validator.py) | Đọc file Subset PulseDB `.mat`; gắn cờ NaN/Inf, nhãn bất thường, waveform trùng (không xóa dòng) | File `.mat` → `PulseSegment`; segment → bảng cờ |
| [data_io/split_manifest.py](data_io/split_manifest.py) | Inventory, split theo người `pulsedb-split-v2`, kiểm tra bảo toàn/leakage, CSV chuẩn | Segment → inventory → manifest train/val/test |
| [signal_processing/fiducials.py](signal_processing/fiducials.py) | Chuẩn bị kênh, R-peak, PPG foot tiếp tuyến, ghép PAT | Vector ECG/PPG + fs/clock/timestamp → mốc và PAT |
| [feature_extraction/week04.py](feature_extraction/week04.py) | Đặc trưng và cờ SQI theo cửa sổ `features-sqi-v1` | Cửa sổ ECG/PPG có metadata → đặc trưng, quality, flags |
| [models/constant_baselines.py](models/constant_baselines.py) | Tính dự đoán hằng số B0/B1 | Nhãn train hoặc calibration → cặp dự đoán `[SBP, DBP]` |
| [models/xgboost_baseline.py](models/xgboost_baseline.py) | B3: XGBoost riêng SBP/DBP | Đặc trưng + nhãn train → model; đặc trưng val → `[SBP, DBP]` |
| [pulsedb/features.py](pulsedb/features.py), [pulsedb/pipeline.py](pulsedb/pipeline.py) | 12 đặc trưng ECG/PPG đơn giản; fit B0/B3 trên train, đánh giá val | Đoạn PulseDB + manifest/inventory split v2 → dự đoán và metrics |
| [evaluation/bp_metrics.py](evaluation/bp_metrics.py) | Tính MAE/bias/SD và tổng hợp theo người | Nhãn tham chiếu + dự đoán + ID người → kết quả đánh giá |
| [evaluation/subject_bootstrap.py](evaluation/subject_bootstrap.py) | CI bootstrap percentile lấy mẫu theo người; đánh giá bảng dự đoán theo manifest | Dự đoán + manifest/inventory → metrics và CI |
| [data_io/packet_simulation.py](data_io/packet_simulation.py) | Sinh/replay packet ECG/PPG SYNTHETIC `synthetic-packet-v2` với 6 case lỗi | Config/seed → packet → timeline, gap, offset |

Chi tiết đầu vào/đầu ra nằm trong [README models](models/README.md) và
[README evaluation](evaluation/README.md).

## Cách chạy để xem kết quả

Mở [demo_week_03_baselines.py](../scripts/demo_week_03_baselines.py) trong
VSCode, chọn interpreter `.venv` của repo rồi bấm **Run Python File in
Terminal**. Demo tự gọi validation, B0/B1 và metrics; không cần chạy lần lượt
những file trong `software/`. Kết quả JSON hiện ở Terminal.

Các module `software/` chứa hàm/lớp được import và gọi với dữ liệu. Chúng không
có chương trình tạo ví dụ hoặc in kết quả khi chạy riêng. Xem
[README scripts](../scripts/README.md) cho cách chạy và
[README tests](../tests/README.md) cho cách kiểm tra.

## Dữ liệu được chứa và lưu ở đâu

Code B0/B1/metrics không chứa dataset thật và không tự đọc hoặc ghi file dữ
liệu. Các mảng được truyền vào và xử lý trong bộ nhớ; B0/B1 lưu các hằng số đã
fit trong đối tượng Python. Demo/test tự tạo số và ID giả lập.

Quy ước chung: cột **[SBP, DBP]**, đơn vị **mmHg**, ID người là chuỗi giả danh.
Một dòng phải là đơn vị quan sát đã được thống nhất; nhiều cửa sổ cùng lần đo
cuff không tạo nhiều nhãn độc lập. `_bp_validation.py` kiểm tra tính hợp lệ
kỹ thuật, không xác minh nguồn nhãn, split, chronology hoặc ngưỡng BP sinh lý.
Nó trả mảng hợp lệ hoặc báo `ValueError`; không tự bỏ dòng hay điền dữ liệu
thiếu. Hàm `finite_result()` còn báo lỗi khi phép tính tạo giá trị không hữu hạn.

Định nghĩa khoa học, trường hợp lỗi và các quyết định còn mở được giữ
trong [quy ước B0/B1 và metrics](../docs/protocol/week_03_baselines_metrics.md).
Kết quả giả lập chỉ kiểm chứng code/công thức, chưa chứng minh hiệu năng dự án.
