# Quy trình làm việc trên GitHub

Tài liệu này dành cho cả thành viên mới dùng GitHub. Mục tiêu là không mất code, không ghi đè công việc của nhau và mọi thay đổi đều được kiểm tra trước khi ghép vào dự án.

## 1. Các thuật ngữ cần biết

| Thuật ngữ | Giải thích ngắn |
|---|---|
| Repository (repo) | Thư mục dự án được lưu và theo dõi bằng GitHub. |
| Branch (nhánh) | Một bản làm việc tách biệt. Mỗi người làm trên nhánh của mình để không ảnh hưởng người khác. |
| Commit | Một lần lưu thay đổi kèm thông điệp mô tả. |
| Push | Đưa các commit từ máy cá nhân lên GitHub. |
| Pull Request (PR) | Yêu cầu ghép thay đổi từ một nhánh vào nhánh khác để nhóm kiểm tra. |
| CI | Hệ thống tự động chạy kiểm tra mã nguồn và test. Dấu xanh nghĩa là kiểm tra đạt. |
| Merge | Ghép thay đổi của PR vào nhánh đích. |
| Conflict | Hai nhánh cùng sửa một vùng nên Git không tự quyết định được nội dung cần giữ. |

## 2. Vai trò của các nhánh

- main: phiên bản ổn định dùng cho các mốc báo cáo, demo hoặc phát hành.
- develop: nơi tích hợp công việc đã qua CI.
- dev/linh: nhánh làm việc của Linh.
- dev/ducanh: nhánh làm việc của Đức Anh.
- dev/huy: nhánh làm việc của Huy.
- feat/..., fix/..., docs/...: nhánh ngắn hạn cho một nhiệm vụ cụ thể khi cần.

Không commit trực tiếp lên main. Công việc thông thường đi theo luồng:

Nhánh cá nhân → Pull Request → develop → kiểm tra mốc ổn định → main.

## 3. Thiết lập lần đầu trên máy

Cài Git, sau đó mở Terminal hoặc PowerShell và chạy:

    git clone https://github.com/ndhuy1127/ppg-ecg-blood-pressure.git
    cd ppg-ecg-blood-pressure
    git fetch origin

Chuyển sang đúng nhánh cá nhân:

    git switch dev/linh

Linh thay tên nhánh thành dev/linh, Đức Anh dùng dev/ducanh, Huy dùng dev/huy.

Nếu Git báo chưa có nhánh trên máy:

    git switch --track origin/dev/linh

Chỉ thay dev/linh bằng nhánh của đúng thành viên.

## 4. Quy trình làm việc hằng ngày

### Bước 1: Lấy thay đổi mới nhất từ develop

    git fetch origin
    git switch dev/ten-thanh-vien
    git merge origin/develop

Lệnh merge này cho phép đưa thay đổi mới từ develop vào nhánh cá nhân. Không dùng git merge --ff-only develop cho nhánh cá nhân vì lệnh đó có thể thất bại khi cả hai nhánh đều đã có commit.

### Bước 2: Kiểm tra trước khi sửa

    git status

Đảm bảo đang đứng trên đúng nhánh cá nhân và không có file lạ chưa được xử lý.

### Bước 3: Làm một nhiệm vụ có phạm vi nhỏ

Ví dụ:

- Linh sửa pipeline đọc dữ liệu hoặc thêm test.
- Đức Anh cập nhật BOM, sơ đồ mạch hoặc firmware.
- Huy cập nhật xử lý PAT, protocol hoặc tài liệu bài báo.

Không đưa dữ liệu người tham gia, khóa API, mật khẩu, file .env hoặc dữ liệu nhận dạng cá nhân lên GitHub.

### Bước 4: Lưu thay đổi bằng commit

    git status
    git add duong-dan-file-can-luu
    git commit -m "feat: mo ta ngan gon thay doi"

Nên dùng git add với đúng file hoặc thư mục cần lưu. Hạn chế git add . khi chưa xem git status.

Tiền tố commit:

- feat: thêm tính năng.
- fix: sửa lỗi.
- docs: cập nhật tài liệu.
- test: thêm hoặc sửa kiểm thử.
- chore: cấu hình và công việc bảo trì.
- refactor: đổi cấu trúc nhưng không đổi chức năng.

### Bước 5: Đẩy lên GitHub

    git push origin dev/ten-thanh-vien

Nếu là lần đầu đẩy một nhánh mới:

    git push -u origin ten-nhanh

### Bước 6: Tạo Pull Request

1. Mở repository trên GitHub.
2. Chọn Pull requests → New pull request.
3. Chọn base là develop.
4. Chọn compare là nhánh đang làm.
5. Điền mục tiêu, thay đổi chính, cách kiểm tra và ảnh hưởng tới dữ liệu/phần cứng/protocol.
6. Liên kết Issue nếu có.
7. Tạo PR.

Không chọn main làm base cho công việc hằng ngày.

## 5. Kiểm tra và merge

Trước khi merge cần kiểm tra:

- Thay đổi có đúng nhiệm vụ không.
- Có file dữ liệu nhạy cảm hoặc file sinh tự động bị đưa lên không.
- Hướng dẫn chạy có rõ không.
- Test và CI có đạt không.
- Kết quả nghiên cứu có thể tái tạo từ mã và cấu hình đã lưu không.

Chỉ merge khi:

- CI hiển thị màu xanh.
- Không còn conflict.

Merge là ghép thay đổi vào develop; không phải xóa toàn bộ nhánh hoặc mất lịch sử.

## 6. Sau khi PR được merge

Mỗi thành viên đồng bộ lại nhánh cá nhân:

    git fetch origin
    git switch dev/ten-thanh-vien
    git merge origin/develop
    git push origin dev/ten-thanh-vien

Sau đó mới bắt đầu nhiệm vụ tiếp theo.

## 7. Khi gặp conflict

Không xóa nhánh và không force-push. Thực hiện:

    git status

Mở các file Git liệt kê, chọn nội dung đúng và xóa các dấu phân cách conflict. Sau đó:

    git add duong-dan-file-da-sua
    git commit -m "fix: xu ly xung dot voi develop"
    git push origin dev/ten-thanh-vien

Nếu chưa biết xử lý và muốn quay lại trạng thái trước khi merge:

    git merge --abort

Sau đó gửi ảnh lỗi và kết quả git status cho nhóm.

## 8. Khi CI báo lỗi

1. Mở PR và bấm Details tại kiểm tra bị đỏ.
2. Tìm bước đầu tiên bị lỗi, ví dụ Ruff, Pytest hoặc Check environment.
3. Chạy lại trên máy:

    ruff check .
    pytest -q
    python scripts/check_environment.py

4. Sửa lỗi, commit và push lại. GitHub sẽ tự chạy CI lần nữa.

Không merge khi CI còn đỏ, trừ khi cả nhóm đã xác định đó là lỗi hạ tầng và ghi rõ lý do trong PR.

## 9. Quy tắc an toàn dữ liệu nghiên cứu

- data/raw, data/interim và data/processed không được commit.
- Dữ liệu mẫu phải nhỏ, đã ẩn danh và đặt trong data/sample.
- Dùng subject_id ngẫu nhiên; không dùng tên, số điện thoại, email hoặc mã sinh viên.
- Không lưu token, mật khẩu hoặc file .env trong repo.
- Khi nghi ngờ đã push dữ liệu nhạy cảm, dừng làm việc và báo ngay cho cả nhóm.

Xem thêm docs/DATA_POLICY.md.

## 10. Checklist nhanh trước khi tạo PR

- Đang ở đúng nhánh.
- Đã đồng bộ từ origin/develop.
- Chỉ commit file liên quan tới nhiệm vụ.
- Không có dữ liệu nhạy cảm hoặc file lớn.
- Đã chạy Ruff, Pytest và kiểm tra môi trường.
- PR có mô tả cách kiểm tra.
- Base branch là develop.

Nếu chưa chắc một thao tác Git có an toàn hay không, dừng lại và hỏi nhóm trước khi dùng force, reset, rebase hoặc xóa nhánh.
