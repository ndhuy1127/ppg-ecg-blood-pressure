# Quy trình làm việc

## Luồng thay đổi

1. Đồng bộ nhánh **develop** từ remote.
2. Chuyển sang nhánh cá nhân hoặc tạo nhánh công việc từ **develop**.
3. Thực hiện các commit nhỏ, mỗi commit có ý nghĩa và phạm vi rõ ràng.
4. Push lên nhánh cá nhân.
5. Tạo pull request vào **develop** và liên kết issue.
6. Một thành viên khác thực hiện review chéo.
7. Sửa các góp ý và bảo đảm CI thành công.
8. Chỉ merge **develop** vào **main** tại mốc ổn định được nhóm thống nhất.

Ví dụ:

~~~bash
git switch develop
git pull --ff-only origin develop
git switch dev/ten-thanh-vien
git merge --ff-only develop
~~~

Không force-push lên nhánh dùng chung và không làm trực tiếp trên **main**.

## Quy ước commit

Thông điệp commit viết ngắn gọn, không dấu:

~~~text
feat: them tinh nang
fix: sua loi
docs: cap nhat tai lieu
test: them kiem thu
chore: cap nhat cau hinh
refactor: tai cau truc ma nguon
~~~

Pull request cần mô tả cách kiểm tra, kết quả kiểm tra và tác động tới dữ liệu,
phần cứng hoặc protocol nếu có.
