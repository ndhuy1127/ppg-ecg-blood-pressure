# Quản lý và giả danh hóa dữ liệu người tham gia — bản nháp v0.1

> Bản nháp chưa được phê duyệt, chưa triển khai. Kế thừa
> [khung đạo đức v0.1 mục 5](ethics_outline_v0.1.md) và
> [chính sách dữ liệu](../DATA_POLICY.md). Thời hạn lưu, nơi lưu, người quản lý và
> mốc khóa dữ liệu là đề xuất, chờ thầy/hội đồng. Huy soạn 2026-10-21; cập nhật
> 2026-10-29 (rút lui, phiếu giấy có danh tính, gán mã, thời hạn lưu).

## 1. Dữ liệu thu và nơi tạo

| Loại | Tạo ở đâu | Có định danh? |
| --- | --- | --- |
| Phiếu đồng thuận có chữ ký | Giấy | Có (họ tên, chữ ký, mã `subject_id`) |
| Bảng liên kết danh tính ↔ `subject_id` | File mã hóa, máy quản lý dữ liệu | Có |
| Thông tin liên lạc để hẹn lịch và nhắn nhắc trước buổi đo | Cùng chỗ với bảng liên kết, không vào dữ liệu nghiên cứu | Có; xóa khi người đó xong buổi cuối hoặc rút lui |
| Phiếu sàng lọc | Giấy, chỉ mang `subject_id` | Không trực tiếp; có tuổi, tay thuận, trả lời sức khỏe |
| Tín hiệu raw ECG/PPG/IMU, sự kiện `t0` | Logger trên laptop (qua USB) | Không trực tiếp; waveform sinh trắc không phải ẩn danh tuyệt đối |
| Số đo cuff (SBP, DBP, mạch) và thời điểm | Biểu mẫu nghiên cứu theo `event_id` | Không trực tiếp |
| Metadata buổi (thanh ghi AFE, firmware, vị trí đeo, nhiệt độ phòng) | Logger/biểu mẫu | Không |
| Nhật ký sự cố | Biểu mẫu, chỉ mã | Không trực tiếp |

Không thu: họ tên, số điện thoại, email, mã sinh viên, CCCD, ngày sinh đầy đủ,
ảnh, video, vị trí GPS.

## 2. Giả danh hóa

- `subject_id` dạng `SUB001` gán ngẫu nhiên (chốt 2026-10-29). Trước khi tuyển,
  người quản lý dữ liệu sinh danh sách `SUB001`–`SUB025` theo thứ tự xáo trộn
  bằng một seed giữ kín, không ghi vào repo, cất cùng bảng liên kết. Mỗi người đăng
  ký nhận mã kế tiếp trong danh sách, nên mã không suy ra được từ thứ tự đăng ký
  hay danh tính. `session_id`, `event_id` theo
  [quy ước dữ liệu](../quy_uoc_du_lieu.md).
- Đây là **giả danh hóa**, không phải ẩn danh: còn bảng liên kết, và waveform/
  metadata vẫn có rủi ro tái nhận diện.
- Có hai nơi nối danh tính với mã:
  - bảng liên kết: mã hóa [công cụ, ví dụ AES-256 — chờ chốt], lưu trên thiết bị
    riêng không đồng bộ đám mây, chỉ [người quản lý dữ liệu — đề xuất Huy, dự phòng
    Linh; chờ xác nhận] mở được;
  - phiếu đồng thuận giấy, có họ tên và mã. Người tham gia cần mã để rút lui, nên
    vẫn ghi mã trên phiếu. Phiếu cất tủ khóa, bìa riêng.
- Phiếu sàng lọc giấy (dữ liệu sức khỏe theo mã) cất ở bìa khác, không cùng bìa với
  phiếu đồng thuận, để sức khỏe và họ tên không nằm chung.
- Tuổi lưu theo năm; không lưu ngày sinh.

## 3. Lưu trữ và quyền truy cập

- Raw bất biến: không sửa, không ghi đè, không xóa để làm sạch kết quả; mỗi phiên có
  manifest và SHA-256 khi ghi (logger của Linh, Tuần 5). Ngoại lệ là xóa theo
  yêu cầu rút lui (mục 4; thêm 2026-10-26) và tiêu hủy khi hết hạn lưu (mục 5; thêm
  2026-10-29), đều có nhật ký.
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

(Đề xuất của nhóm 2026-10-29, chờ thầy/hội đồng.)

- Khi một người rút lui, nhóm ngừng thu dữ liệu của người đó. Người rút lui chọn
  xóa hay giữ dữ liệu đã thu. Lựa chọn ghi vào nhật ký rút lui: mã, ngày, lựa chọn,
  người ghi, không kèm danh tính.
- Chọn xóa và yêu cầu đến trước mốc khóa:
  - xóa raw, dẫn xuất, bản xuất, dòng trong bảng liên kết và thông tin liên lạc,
    trên cả bản sao lưu. Nếu sau này phục hồi từ bản sao lưu cũ thì dùng nhật ký
    xóa để xóa lại trước khi dùng dữ liệu;
  - hủy phiếu sàng lọc giấy;
  - giữ phiếu đồng thuận làm hồ sơ đồng thuận;
  - ghi lại thao tác xóa (mã, ngày, người làm).
- Mốc khóa: snapshot dữ liệu có SHA-256, khóa trước lần phân tích chính đầu tiên ở
  cổng G4 (Tuần 20, dự kiến tuần 2027-01-28 → 2027-02-03). Ngày chính xác ghi vào
  phiếu thông tin mục 6 trước khi nộp.
- Sau mốc khóa, yêu cầu xóa không thực hiện được: dữ liệu đã nằm trong các phân
  tích đã khóa (LOSO, manifest có hash), xóa một người sẽ đổi mọi lượt đánh giá.
  Nhóm vẫn ngừng thu thêm dữ liệu của người đó.
- Không chọn mốc là ngày công bố vì ngày này không biết trước nên không cam kết được
  với người tham gia.

## 5. Thời hạn lưu và tiêu hủy

- Theo quy định lưu trữ của trường/hội đồng [hỏi thầy]. Nếu không có quy định
  (chốt 2026-10-29): giữ 03 năm kể từ mốc muộn hơn trong hai mốc kết thúc đề tài
  và công bố kết quả, rồi tiêu hủy. Không có công bố thì tính từ ngày kết thúc đề
  tài, nên mốc luôn ra một ngày cụ thể. Phiếu thông tin mục 5 dùng cùng cách diễn
  đạt.
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
