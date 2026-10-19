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

Đã có baseline hằng số B0/B1, metrics BP và bộ kiểm tra đầu vào; các phần này
được kiểm thử bằng dữ liệu giả lập. Repo còn có code reader/validator/visualizer
PulseDB ở `pulsedb/`; sự tồn tại của code không chứng minh dataset/split đã được
nghiệm thu. Các thư mục chỉ chứa `__init__.py` vẫn là khung package.

| File / thư mục | Làm gì | Dữ liệu đi qua |
| --- | --- | --- |
| [_bp_validation.py](_bp_validation.py) | Kiểm tra shape, kiểu số, giá trị hữu hạn và mã người dùng chung | Mảng BP `(n, 2)` hoặc danh sách ID được caller cung cấp |
| [models/constant_baselines.py](models/constant_baselines.py) | Tính dự đoán hằng số B0/B1 | Nhãn train hoặc calibration → cặp dự đoán `[SBP, DBP]` |
| [models/xgboost_baseline.py](models/xgboost_baseline.py) | B3: XGBoost riêng SBP/DBP | Đặc trưng + nhãn train → model; đặc trưng val → `[SBP, DBP]` |
| [pulsedb/features.py](pulsedb/features.py), [pulsedb/pipeline.py](pulsedb/pipeline.py) | 12 đặc trưng ECG/PPG đơn giản; fit B0/B3 trên train, đánh giá val | Đoạn PulseDB + manifest/inventory split v2 → dự đoán và metrics |
| [evaluation/bp_metrics.py](evaluation/bp_metrics.py) | Tính MAE/bias/SD và tổng hợp theo người | Nhãn tham chiếu + dự đoán + ID người → kết quả đánh giá |

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
