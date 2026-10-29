# Quản lý và giả danh hóa dữ liệu người tham gia — bản nháp v0.1

> Bản nháp chưa được phê duyệt và chưa triển khai. Kế hoạch này dựa trên
> [khung đạo đức v0.1 mục 5](ethics_outline_v0.1.md) và
> [chính sách dữ liệu](../DATA_POLICY.md). Thời hạn lưu, nơi lưu, người quản lý và
> mốc khóa dữ liệu là đề xuất, chờ thầy/hội đồng. Huy soạn ngày 2026-10-21;
> cập nhật 2026-10-29 ở các phần rút lui, phiếu giấy có danh tính, gán mã và thời
> hạn lưu.

## 1. Dữ liệu thu thập và nơi tạo ra

| Loại | Tạo ở đâu | Có định danh? |
| --- | --- | --- |
| Phiếu đồng thuận có chữ ký | Giấy | Có (họ tên, chữ ký, mã `subject_id`) |
| Bảng liên kết danh tính với `subject_id` | File đã mã hóa, trên máy quản lý dữ liệu | Có |
| Thông tin liên lạc để hẹn lịch và nhắn tin nhắc trước buổi đo | Lưu cùng chỗ với bảng liên kết, không đưa vào dữ liệu nghiên cứu | Có; xóa khi người đó xong buổi cuối hoặc rút lui |
| Phiếu sàng lọc | Giấy, chỉ ghi `subject_id` | Không trực tiếp; có tuổi, tay thuận và các câu trả lời về sức khỏe |
| Tín hiệu raw ECG/PPG/IMU, sự kiện `t0` | Logger trên laptop (qua USB) | Không trực tiếp; waveform là dữ liệu sinh trắc nên không phải ẩn danh tuyệt đối |
| Số đo cuff (SBP, DBP, mạch) và thời điểm đo | Biểu mẫu nghiên cứu theo `event_id` | Không trực tiếp |
| Metadata buổi (thanh ghi AFE, firmware, vị trí đeo, nhiệt độ phòng) | Logger/biểu mẫu | Không |
| Nhật ký sự cố | Biểu mẫu, chỉ ghi mã | Không trực tiếp |

Nhóm không thu mã sinh viên, CCCD, ngày sinh đầy đủ, ảnh, video hay vị trí GPS. Họ tên
chỉ có trên phiếu đồng thuận giấy và trong bảng liên kết; thông tin liên lạc để hẹn lịch
lưu cùng bảng liên kết (xem bảng trên). Dữ liệu nghiên cứu, tức mọi thứ chỉ mang mã
`subject_id`, không chứa họ tên, số điện thoại hay email.

## 2. Giả danh hóa

- `subject_id` có dạng `SUB001` và được gán ngẫu nhiên (chốt 2026-10-29). Trước khi
  tuyển, người quản lý dữ liệu tạo danh sách `SUB001`–`SUB025` theo thứ tự xáo trộn
  bằng một seed giữ kín, không ghi vào repo và được cất cùng bảng liên kết. Mỗi người
  đăng ký nhận mã kế tiếp trong danh sách, nên không suy ra được mã từ thứ tự đăng ký
  hay từ danh tính. `session_id` và `event_id` theo
  [quy ước dữ liệu](../quy_uoc_du_lieu.md).
- Đây là **giả danh hóa**, không phải ẩn danh: bảng liên kết vẫn tồn tại, và waveform
  cùng metadata vẫn có rủi ro bị tái nhận diện.
- Có hai nơi nối danh tính với mã:
  - bảng liên kết: được mã hóa bằng [công cụ, ví dụ AES-256 — chờ chốt], lưu trên
    thiết bị riêng không đồng bộ lên đám mây, và chỉ
    [người quản lý dữ liệu — đề xuất Huy, dự phòng Linh; chờ xác nhận] mở được;
  - phiếu đồng thuận giấy, có họ tên và mã. Người tham gia cần mã để rút lui, nên mã
    vẫn được ghi trên phiếu. Phiếu được cất trong tủ có khóa, ở bìa riêng.
- Phiếu sàng lọc giấy (dữ liệu sức khỏe theo mã) được cất ở bìa khác, không cùng bìa
  với phiếu đồng thuận, để thông tin sức khỏe và họ tên không nằm chung một chỗ.
- Tuổi được lưu theo năm; không lưu ngày sinh.

## 3. Lưu trữ và quyền truy cập

- Dữ liệu raw là bất biến: không sửa, không ghi đè, không xóa để làm sạch kết quả.
  Mỗi phiên có manifest và SHA-256 tạo lúc ghi (logger của Linh, Tuần 5). Có hai
  ngoại lệ, đều có nhật ký: xóa theo yêu cầu rút lui (mục 4; thêm 2026-10-26) và
  tiêu hủy khi hết hạn lưu (mục 5; thêm 2026-10-29). Dữ liệu dẫn xuất có version và
  truy ngược được về raw, config và commit.
- Nơi lưu: [ổ nghiên cứu của phòng thí nghiệm / máy trạm có mật khẩu — chờ chốt], có
  bản sao lưu [nơi, tần suất — chờ chốt].
- Quyền truy cập: ba thành viên nhóm và giảng viên hướng dẫn. Không chia sẻ ra ngoài
  khi chưa có phê duyệt.
- **Không bao giờ commit** lên Git dữ liệu người tham gia, bảng liên kết, phiếu đã
  scan hay file đánh dấu tay trên dữ liệu người. `.gitignore` đã chặn `data/raw/`,
  `data/interim/`, `data/processed/`, `runs/`, `*.npz`, `*.npy`…, nhưng vẫn phải
  kiểm tra `git status` trước mỗi commit.

## 4. Rút lui và xóa

(Đề xuất của nhóm 2026-10-29, chờ thầy/hội đồng.)

- Khi một người rút lui, nhóm ngừng thu dữ liệu của người đó. Người rút lui chọn xóa
  hay giữ dữ liệu đã thu. Lựa chọn này được ghi vào nhật ký rút lui, gồm mã, ngày,
  lựa chọn và người ghi, không kèm danh tính.
- Nếu người đó chọn xóa và yêu cầu đến trước mốc khóa:
  - xóa raw, dữ liệu dẫn xuất, các bản xuất, dòng tương ứng trong bảng liên kết và
    thông tin liên lạc, kể cả trên bản sao lưu. Nếu sau này có phục hồi từ bản sao
    lưu cũ thì dùng nhật ký xóa để xóa lại trước khi dùng dữ liệu;
  - hủy phiếu sàng lọc giấy;
  - giữ phiếu đồng thuận làm hồ sơ về việc đồng thuận;
  - ghi lại thao tác xóa (mã, ngày, người làm).
- Mốc khóa là một snapshot dữ liệu có SHA-256, được khóa trước lần phân tích chính
  đầu tiên ở cổng G4 (Tuần 20, dự kiến tuần 2027-01-28 đến 2027-02-03). Ngày chính
  xác sẽ được ghi vào phiếu thông tin mục 6 trước khi nộp.
- Sau mốc khóa, yêu cầu xóa không thực hiện được, vì dữ liệu đã nằm trong các phân
  tích đã khóa (LOSO, manifest có hash) và xóa một người sẽ làm đổi mọi lượt đánh
  giá. Nhóm vẫn ngừng thu thêm dữ liệu của người đó.
- Nhóm không chọn ngày công bố làm mốc khóa, vì ngày này không biết trước nên không
  cam kết được với người tham gia.

## 5. Thời hạn lưu và tiêu hủy

- Thời hạn lưu theo quy định lưu trữ của trường/hội đồng [hỏi thầy]. Nếu không có
  quy định (chốt 2026-10-29), dữ liệu được giữ 03 năm rồi tiêu hủy. Thời hạn này tính
  từ mốc muộn hơn trong hai mốc: kết thúc đề tài và công bố kết quả. Nếu không có
  công bố thì tính từ ngày kết thúc đề tài, nên mốc luôn là một ngày cụ thể. Phiếu
  thông tin mục 5 dùng cùng cách diễn đạt.
- Cách tiêu hủy: xóa an toàn theo loại thiết bị lưu trữ, hủy phiếu giấy bằng máy
  hủy và lập biên bản tiêu hủy.

## 6. Sự cố dữ liệu

Xử lý theo khung v0.1 mục 5.4:

- dừng commit và đồng bộ;
- báo nhóm và giảng viên;
- nếu lỡ commit, gỡ dữ liệu khỏi lịch sử Git (git filter-repo);
- đánh giá phạm vi;
- báo người tham gia nếu có nguy cơ lộ danh tính.

Thời hạn và kênh báo cho hội đồng: [chờ hội đồng].

## 7. Chia sẻ và công bố

Chỉ công bố số liệu tổng hợp. Việc có chia sẻ dữ liệu đã giả danh hóa ra ngoài (ví
dụ lên kho dữ liệu mở) hay không, và có cần đồng thuận riêng hay không:
[chờ thầy/hội đồng]. Phiếu đồng thuận hiện chưa hứa điều này.
