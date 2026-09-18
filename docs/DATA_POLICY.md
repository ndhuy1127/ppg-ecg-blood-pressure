# Chính sách dữ liệu và bảo mật

## Dữ liệu không được commit

- Dữ liệu ECG/PPG thật của người tham gia.
- Tên, số điện thoại, địa chỉ hoặc bất kỳ thông tin định danh trực tiếp hay gián
  tiếp nào.
- Dữ liệu **raw**, **interim** hoặc **processed** dung lượng lớn.
- Token, mật khẩu, khóa riêng, file **.env** hoặc bí mật truy cập.
- Artifact mô hình và kết quả thí nghiệm dung lượng lớn.

Không được dựa riêng vào **.gitignore** để bảo vệ dữ liệu nhạy cảm. Người tạo
commit và reviewer đều phải kiểm tra nội dung thay đổi.

## Dữ liệu được phép

Chỉ được đưa dữ liệu mẫu nhỏ, đã ẩn danh và không thể truy ngược vào
**data/sample/**. Mẫu phải có nguồn gốc và mục đích rõ ràng, không chứa metadata
định danh và được review trước khi merge.

## Định danh nghiên cứu

Dữ liệu nghiên cứu phải dùng các khóa:

- **subject_id**: mã người tham gia đã giả danh.
- **session_id**: mã phiên đo.
- **event_id**: mã sự kiện hoặc đoạn tín hiệu trong phiên.

Không dùng tên, số điện thoại hoặc mã bệnh án làm bất kỳ khóa nào.

## Chất lượng tín hiệu

Quyết định giữ, loại hoặc gắn cờ dữ liệu phải dựa trên chỉ số chất lượng tín
hiệu (SQI) và ngưỡng đã định trước trong protocol. Không điều chỉnh tiêu chí sau
khi xem kết quả mô hình nếu chưa có quyết định và lý do được ghi nhận.

## Khi phát hiện vi phạm

Không tiếp tục chia sẻ commit. Thông báo ngay cho nhóm, thu hồi hoặc xoay vòng
bí mật nếu liên quan, và xử lý lịch sử Git theo quy trình ứng phó đã được thống
nhất. Không sao chép dữ liệu vi phạm sang issue hoặc kênh công khai.
