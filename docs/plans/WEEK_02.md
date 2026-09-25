# Kế hoạch Tuần 2 — dữ liệu công khai và tín hiệu v0

## Mục tiêu và ranh giới

- Kiểm tra khả năng đọc một phần PulseDB được phép dùng, giữ nguyên nguồn gốc và phiên bản dữ liệu.
- Tạo bản ghi PPG/ECG v0 có timestamp từ hệ phần cứng, nếu board và điều kiện an toàn đã sẵn sàng.
- Chuẩn hóa khái niệm PAT, đơn vị quan sát, nhãn và cửa sổ để Linh và Đức Anh có thể thống nhất giao diện.
- Chưa tuyển người hoặc đo trên người bằng prototype khi chưa có phê duyệt đạo đức và kiểm tra an toàn cần thiết. Kiểm thử bàn máy hoặc dữ liệu mô phỏng không được ghi thành dữ liệu người tham gia.

## Phân công và tiêu chí kiểm tra

| Phụ trách | Việc Tuần 2 theo tài liệu phân công | Đầu ra cần có để nghiệm thu | Phụ thuộc / trạng thái lúc lập kế hoạch |
| --- | --- | --- | --- |
| Linh | Xác nhận quyền sử dụng và nguồn PulseDB; ghi phiên bản, checksum; viết trình đọc metadata, ECG, PPG, ABP và nhãn; notebook khám phá ít nhất 1.000 đoạn; test file thiếu, metadata trùng và sai kênh. | Mã đọc + test + notebook có thể chạy lại, báo cáo ánh xạ `subject_id`, độ dài, missing value, đơn vị và tần số lấy mẫu. | **Chưa xác nhận:** chưa có dataset, manifest hoặc trình đọc trong repo. Cần đối chiếu điều khoản của đúng bản dữ liệu trước khi tải. |
| Đức Anh | Lắp và kiểm tra board v0, nguồn, giao tiếp, cấu hình cảm biến, nhiễu và bão hòa; xuất bản ghi PPG/ECG ngắn với timestamp và nhật ký cấu hình. | Log cấu hình, bằng chứng hai kênh nhận diện được, không bão hòa kéo dài, timestamp tăng đơn điệu; file thô lưu ngoài Git nếu là dữ liệu thật. | **Đã có BOM v0.1 trong repo; chưa xác nhận** firmware, board hoạt động hay bản ghi v0. Việc đo trên người phụ thuộc phê duyệt đạo đức và kiểm tra an toàn. |
| Huy | Tổng hợp PAT/PTT/PEP/PWA; định nghĩa lần đo cuff, quan sát, nhãn, các cửa sổ ứng viên 10/20/30/60 giây; kiểm tra trực quan lỗi R peak, baseline wander và PPG foot khi có bản ghi v0. | [Tài liệu định nghĩa mẫu, nhãn và glossary](../protocol/week_02_sample_label_glossary.md); phiếu kiểm tra trực quan đã điền khi nhận được bản ghi. | **Đã có bản thảo định nghĩa, chưa được review; chưa có kiểm tra tín hiệu v0.** Cần Linh xác nhận ánh xạ PulseDB và Đức Anh xác nhận timestamp/logger. |

## Việc chung và mốc đóng tuần

1. Review chéo notebook PulseDB và một bản ghi v0; ghi tên người review, commit hoặc phiên bản file, lỗi và quyết định vào báo cáo tuần.
2. Đối chiếu quy ước nhãn PulseDB với nhãn cuff của prototype. PulseDB có ABP waveform; không dùng đoạn ABP như một lần đo cuff độc lập.
3. Chỉ đánh dấu mốc Tuần 2 đạt khi notebook đọc lại được ít nhất 1.000 đoạn ánh xạ đúng người và có bản ghi v0 đạt tiêu chí kênh/timestamp trong phạm vi được phép thu.
4. Ghi các vấn đề cần sửa trước Tuần 3 vào [báo cáo Tuần 2](../../reports/weekly/week_02/README.md).

## Vấn đề cần nhóm quyết định

- Bản PulseDB, điều khoản sử dụng, nơi lưu và checksum manifest; schema thật phải được kiểm tra trên tệp được phép dùng trước khi khóa trình đọc.
- Danh sách trường logger, đơn vị tín hiệu, clock chung và cách lưu thời điểm bắt đầu bơm cuff.
- Cửa sổ phân tích chính và ngưỡng SQI chỉ được khóa trước trên pilot/validation; 10/20/30/60 giây hiện là ứng viên phân tích độ nhạy.
- Tài liệu phân công đề cập sáu giai đoạn và G1–G6. Các mốc đó vẫn là đề xuất của tài liệu ngoài repo, chờ nhóm xác nhận trước khi coi là kế hoạch đã khóa.

## Nguồn đối chiếu

- `Phan_cong_cong_viec_chi_tiet_28_tuan_Linh_Duc_Anh_Huy.docx`, mục “Tuần 2 — Dữ liệu công khai và tín hiệu v0 đầu tiên” (tệp do người dùng cung cấp, không commit vì nằm ngoài repo).
- [Protocol v0.1](../protocol/protocol_outline_v0.1.md), [chính sách dữ liệu](../DATA_POLICY.md), [câu hỏi nghiên cứu](../research_questions_v0.1.md).
- [Bài công bố PulseDB](https://doi.org/10.3389/fdgth.2022.1090854) và [repository của tác giả](https://github.com/pulselabteam/PulseDB).
