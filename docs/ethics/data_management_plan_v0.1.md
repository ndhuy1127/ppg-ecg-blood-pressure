# Quản lý và giả danh hóa dữ liệu người tham gia — bản nháp v0.1

> Bản nháp chưa được phê duyệt, chưa triển khai. Kế thừa
> [khung đạo đức v0.1 mục 5](ethics_outline_v0.1.md) và
> [chính sách dữ liệu](../DATA_POLICY.md). Thời hạn lưu, nơi lưu và người quản lý
> là đề xuất, chờ thầy/hội đồng. Huy soạn 2026-10-21.

## 1. Dữ liệu thu và nơi tạo

| Loại | Tạo ở đâu | Có định danh? |
| --- | --- | --- |
| Phiếu đồng thuận có chữ ký | Giấy | Có (họ tên, chữ ký) |
| Bảng liên kết danh tính ↔ `subject_id` | File mã hóa, máy quản lý dữ liệu | Có |
| Phiếu sàng lọc | Giấy, chỉ mang `subject_id` | Không trực tiếp; có tuổi, tay thuận, trả lời sức khỏe |
| Tín hiệu raw ECG/PPG/IMU, sự kiện `t0` | Logger trên laptop (qua USB) | Không trực tiếp; waveform sinh trắc không phải ẩn danh tuyệt đối |
| Số đo cuff (SBP, DBP, mạch) và thời điểm | Biểu mẫu nghiên cứu theo `event_id` | Không trực tiếp |
| Metadata buổi (thanh ghi AFE, firmware, vị trí đeo, nhiệt độ phòng) | Logger/biểu mẫu | Không |
| Nhật ký sự cố | Biểu mẫu, chỉ mã | Không trực tiếp |

Không thu: họ tên, số điện thoại, email, mã sinh viên, CCCD, ngày sinh đầy đủ,
ảnh, video, vị trí GPS.

## 2. Giả danh hóa

- `subject_id` dạng `SUB001` gán theo thứ tự đăng ký hoặc ngẫu nhiên, không suy
  ra được từ danh tính; `session_id`, `event_id` theo
  [quy ước dữ liệu](../quy_uoc_du_lieu.md).
- Đây là **giả danh hóa**, không phải ẩn danh: còn bảng liên kết, và waveform/
  metadata vẫn có rủi ro tái nhận diện.
- Bảng liên kết là file duy nhất có danh tính: mã hóa [công cụ, ví dụ AES-256 —
  chờ chốt], lưu trên thiết bị riêng không đồng bộ đám mây, chỉ [người quản lý
  dữ liệu — đề xuất Huy, dự phòng Linh; chờ xác nhận] mở được.
- Tuổi lưu theo năm; không lưu ngày sinh.

## 3. Lưu trữ và quyền truy cập

- Raw bất biến: không sửa, không ghi đè, không xóa để làm sạch kết quả; mỗi phiên có
  manifest và SHA-256 khi ghi (logger của Linh, Tuần 5). Ngoại lệ duy nhất là xóa theo
  yêu cầu rút lui, có nhật ký (mục 4; thêm 2026-10-26).
  Dẫn xuất có version và truy về raw, config, commit.
- Nơi lưu: [ổ nghiên cứu của phòng thí nghiệm / máy trạm có mật khẩu — chờ chốt],
  có bản sao lưu [nơi, tần suất — chờ chốt].
- Quyền: ba thành viên nhóm và giảng viên hướng dẫn. Không chia sẻ ra ngoài khi
  chưa có phê duyệt.
- **Không bao giờ commit** dữ liệu người tham gia, bảng liên kết, phiếu scan
  hay file đánh dấu tay trên dữ liệu người lên Git. `.gitignore` đã chặn
  `data/raw/`, `data/interim/`, `data/processed/`, `runs/`, `*.npz`, `*.npy`…;
  vẫn phải kiểm `git status` trước mỗi commit.

## 4. Rút lui và xóa

- Người tham gia rút lui: xóa raw, dẫn xuất và dòng trong bảng liên kết của mã đó,
  ghi lại thao tác xóa (mã, ngày, người làm) không kèm danh tính.
- Mốc sau đó không xóa được khỏi kết quả: [đề xuất: snapshot dữ liệu khóa ở cổng
  G4 (Tuần 20) hoặc ngày công bố; chờ xác nhận]. Nêu rõ mốc này trong phiếu thông tin.

## 5. Thời hạn lưu và tiêu hủy

- Đề xuất: giữ tới 03 năm sau công bố (theo khung v0.1), **chưa đối chiếu quy
  định của trường/hội đồng**.
- Tiêu hủy: xóa an toàn theo loại thiết bị lưu trữ; hủy phiếu giấy bằng máy hủy.
  Ghi biên bản tiêu hủy.

## 6. Sự cố dữ liệu

Theo khung v0.1 mục 5.4: dừng commit/đồng bộ, báo nhóm và giảng viên, gỡ dữ liệu
khỏi lịch sử Git (git filter-repo) nếu lỡ commit, đánh giá phạm vi, báo người
tham gia nếu có nguy cơ lộ danh tính. Thời hạn và kênh báo hội đồng: [chờ hội đồng].

## 7. Chia sẻ và công bố

Công bố chỉ số liệu tổng hợp. Có chia sẻ dữ liệu giả danh hóa ra ngoài (ví dụ kho
dữ liệu mở) hay không, và cần đồng thuận riêng không: [chờ thầy/hội đồng]; chưa
hứa trong phiếu đồng thuận.
