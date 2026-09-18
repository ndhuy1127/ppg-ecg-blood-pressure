# Phần mềm

Các module được tách theo trách nhiệm:

- **data_io/**: đọc, kiểm tra schema và ghi dữ liệu được phép.
- **preprocessing/**: làm sạch và chuẩn hóa tín hiệu.
- **signal_processing/**: xử lý ECG/PPG và đánh giá chất lượng tín hiệu.
- **feature_extraction/**: trích đặc trưng, gồm đặc trưng PAT theo định nghĩa.
- **models/**: huấn luyện và suy luận mô hình.
- **evaluation/**: chỉ số và quy trình đánh giá.
- **deployment/**: giao diện triển khai sau khi mô hình được thẩm định.

Hiện các module chỉ là khung package; chưa có thuật toán ước lượng huyết áp.
