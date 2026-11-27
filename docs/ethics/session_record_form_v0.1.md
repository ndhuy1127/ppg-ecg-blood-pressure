# Phiếu ghi buổi đo — mẫu trống v0.1

> **Ghi chú nội bộ (không đưa vào bản nộp).** Mẫu trống, soạn 2026-10-31 sau rà soát cuối, vì hội
> đồng cần mọi công cụ thu thập số liệu. Các trường lấy từ [protocol v0.3](../protocol/protocol_outline_v0.2.md)
> mục 6.1–6.4 và [an toàn buổi đo](session_safety_stopping_v0.1.md); không thêm biến mới ngoài
> giới tính (ghi ở phiếu sàng lọc). Đây là bản giấy của "biểu mẫu nghiên cứu" trong protocol 6.2.
> Tệp số `cuff_log` mà metadata `packet-session-metadata-v1` trỏ tới vẫn chưa chốt định dạng
> ([hướng dẫn logger](../protocol/packet_logger.md), mục "Metadata phiên"); khi chốt thì dùng đúng
> các cột của bảng C. Phần dưới đường kẻ là đúng nội dung bản nộp.
>
> Sửa 2026-11-21: ô buổi chỉ còn 1 và 2 (chốt 2026-11-19); mục B thêm điện trở từng dây của đầu
> chuyển điện cực và kiểm giá đỡ bo cổ tay, vì bảng kiểm an toàn mục 2 (sửa 2026-11-19) yêu cầu đo
> và ghi trước mỗi buổi. Ngưỡng trên, ngưỡng dưới của điện trở còn chờ bảng phân tích lỗi đơn.

---

Phiếu chỉ ghi mã, không ghi họ tên. Bản giấy được cất cùng bìa với phiếu sàng lọc, **không** cùng
bìa với phiếu đồng thuận. Số đo được nhập vào tệp nhật ký đo của buổi (cùng mã) ngay trong ngày đo.

## A. Thông tin buổi đo

<!-- cols: 34,33,33; noheader -->
| Mã nghiên cứu: SUB____ | Buổi: S____ (☐ 1 ☐ 2) | Ngày: ____/____/______ |
| --- | --- | --- |
| Giờ bắt đầu: ____:____ | Nhiệt độ phòng: ______ °C | Phiên bản đề cương: ____ |
| Người vận hành (mã): ____ | Người theo dõi (mã): ____ | |

## B. Trước khi đo

- ☐ Đã làm đủ bảng kiểm an toàn (quy trình an toàn, mục 2).
- Điện trở đầu chuyển điện cực, đo trước khi gắn (kΩ): dây cổ tay trái ______ dây cổ tay phải ______
  dây tham chiếu ______; ☐ cả ba nằm trong ngưỡng [ngưỡng dưới–ngưỡng trên của từng dây]
- ☐ Giá đỡ bo cổ tay còn nguyên, che kín đầu nối và đèn báo.
- Buổi 2: số ngày kể từ buổi 1: ______ (từ 7 tới 28 ngày)
- ☐ Phiếu sàng lọc của buổi này: đủ điều kiện.
- ☐ Người tham gia đồng ý tiếp tục. Nghiệm pháp đã đồng ý trong phiếu đồng thuận: ☐ thở chậm
  ☐ tính nhẩm.
- Vị trí bo cổ tay: cách mỏm trâm trụ ______ cm; nấc dây đeo: ______. Cỡ vòng bít: ______.
- Mức dòng LED (mã): xanh ______ đỏ ______ hồng ngoại ______
  ☐ buổi 1: chỉnh và khóa  ☐ buổi 2: dùng lại mức đã khóa  ☐ chỉnh lại một lần (sai lệch đề cương)
- Màu chưa vào khoảng sau 6 vòng chỉnh (nếu có): ______

## C. Các lượt đo huyết áp (tay phải)

<!-- cols: 9,14,8,12,10,11,9,27; small -->
| Mã lượt | Nghiệm pháp (M0/M1/M2) | Đo lại (lượt gốc, lý do) | Giờ bấm nút đánh dấu | Tâm thu (mmHg) | Tâm trương (mmHg) | Mạch (/phút) | Ghi chú (cử động, lỗi máy, dừng) |
| --- | --- | :---: | --- | --- | --- | --- | --- |
| E01<br> | | ^☐ | | | | | |
| E02<br> | | ^☐ | | | | | |
| E03<br> | | ^☐ | | | | | |
| E04<br> | | ^☐ | | | | | |
| E05<br> | | ^☐ | | | | | |
| E06<br> | | ^☐ | | | | | |

Trần: 6 lần bơm mỗi buổi, gồm tối đa 2 lần đo lại; buổi chỉ có M0 thì tối đa 4 lần. Buổi 1 cộng
thêm 2 lần đo hai tay khi sàng lọc (trần 8, hoặc 6 nếu chỉ có M0). Giữa hai lần bơm nghỉ ít nhất
2 phút.

Đo lại chỉ ở M0. Ô "Đo lại" ghi mã của lượt **ngay trước** ở cùng vị trí (lần đo lại thứ hai ghi mã
của lần đo lại thứ nhất) và lý do: **KQ** (máy xả bình thường, không ra kết quả)
hoặc **CĐ** (thấy cử động trong 60 s trước cuff, đã ghi **trước khi bấm nút đánh dấu**). Không đo lại
vì số huyết áp hay vì tín hiệu trên màn hình.

**Trung bình M0 của buổi:** ______/______ mmHg

- ☐ dưới 140/90: làm những nghiệm pháp mà người tham gia đã đồng ý
- ☐ từ 140/90 trở lên: chỉ đo M0, báo số đo và khuyên đi khám
- ☐ có lần đo từ 180/110 trở lên: dừng buổi, ghi nhật ký sự cố

## D. Nghiệm pháp

- **M1 – Thở chậm:** giờ bắt đầu ____:____ (đã đánh dấu sự kiện ☐); ☐ hoàn thành ☐ dừng, lý do:
  ______
- **Nghỉ giữa M1 và M2:** từ ____:____ đến ____:____ (ít nhất 5 phút); ☐ người tham gia không còn
  chóng mặt hay tê đầu ngón tay
- **M2 – Tính nhẩm:** giờ bắt đầu ____:____ (đã đánh dấu sự kiện ☐); số bắt đầu ______; số người tham
  gia nói ra ______; ☐ hoàn thành ☐ dừng, lý do: ______

## E. Kết thúc buổi đo

- Giờ kết thúc: ____:____. Số lần bơm cho các lượt đo: ______; buổi 1 cộng 2 lần đo hai tay khi
  sàng lọc, tổng cả buổi: ______.
- Hỏi triệu chứng sau 5 phút nghỉ: ☐ không có ☐ có: ______
- Hỏi triệu chứng trước khi ra về: ☐ không có ☐ có: ______; nếu có, người tham gia đã đồng ý được
  hỏi thăm (mục 9 của phiếu đồng thuận): ☐ có ☐ không
- ☐ Đã dặn người tham gia liên hệ nhóm nếu có phản ứng da hay khó chịu sau buổi đo.
- Dừng buổi: ☐ không ☐ có, số nhật ký sự cố: ______
- Sai lệch đề cương (nếu có): ______
- Buổi 1: lịch buổi 2 ☐ xác nhận trực tiếp ☐ nhắn tin (chỉ khi người tham gia đồng ý ở mục 9 của
  phiếu đồng thuận); ngày dự kiến: ____/____/______ (cách buổi 1 từ 7 tới 28 ngày, không muộn hơn
  14/05/2027)

Người ghi (mã nhóm): ______   Chữ ký: ______________   Người kiểm tra (mã nhóm): ______
