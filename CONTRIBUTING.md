# Hướng dẫn đóng góp

## Nhánh và pull request

- Không làm việc hoặc commit trực tiếp trên **main**.
- Đồng bộ **develop** trước khi bắt đầu.
- Đặt tên nhánh theo dạng **dev/ten-thanh-vien**, **feat/mo-ta-ngan**,
  **fix/mo-ta-ngan**, **docs/mo-ta-ngan** hoặc **chore/mo-ta-ngan**.
- Tạo pull request vào **develop**. Chỉ đưa **develop** vào **main** tại mốc ổn
  định đã được nhóm thống nhất.
- CI phải thành công trước khi merge.

## Commit

Giữ commit nhỏ, có một mục đích rõ ràng và viết thông điệp không dấu:

~~~text
feat: them tinh nang
fix: sua loi
docs: cap nhat tai lieu
test: them kiem thu
chore: cap nhat cau hinh
refactor: tai cau truc ma nguon
~~~

## Quy tắc dữ liệu

Không commit dữ liệu người tham gia, thông tin định danh, dữ liệu raw/interim/
processed dung lượng lớn, tệp bí mật hoặc artifact mô hình. Chỉ thêm mẫu nhỏ đã
ẩn danh vào **data/sample/** sau khi kiểm tra
[chính sách dữ liệu](docs/DATA_POLICY.md).

## Definition of Done

Một thay đổi chỉ hoàn thành khi:

- Phạm vi và tiêu chí của issue đã được đáp ứng.
- Mã nguồn, cấu hình và tài liệu liên quan đã được cập nhật.
- Kiểm thử phù hợp đã được thêm và chạy thành công.
- **ruff check .**, **pytest -q** và kiểm tra môi trường đều thành công.
- Không có dữ liệu nhạy cảm, bí mật hoặc file lớn ngoài chính sách.
- CI thành công và pull request sẵn sàng merge vào **develop**.
