# An toàn buổi đo và quy tắc dừng — bản nháp v0.1

> Bản nháp chưa được phê duyệt. Không phải hướng dẫn xử trí y khoa. Ngưỡng huyết
> áp dừng phiên **chưa có nguồn** và chờ thầy/hội đồng (mục 3). Huy soạn
> 2026-10-21; thiết bị theo [V1-module](../../configs/hardware/custom_board_proposal.md),
> nghiệm pháp theo [protocol v0.2 mục 6.4](../protocol/protocol_outline_v0.2.md).

## 1. Kiểm tra trước khi gắn thiết bị lên người

Một người đọc, một người kiểm; ghi vào nhật ký buổi (chỉ mã, không tên).

- [ ] Có văn bản phê duyệt đạo đức còn hiệu lực cho đúng protocol đang dùng.
- [ ] Biên bản đo dòng rò trên bo V1 thật (so với giới hạn IEC 60601-1 cho loại
      bộ phận ứng dụng tương ứng) đã có và được Đức Anh ký. **Hiện chưa có.**
- [ ] Laptop chạy pin: đã rút sạc; không nối màn hình ngoài, ổ cứng có nguồn
      riêng, hub USB có nguồn hay cáp mạng.
- [ ] ESP32-S3 DevKitC chỉ nối laptop qua một cáp USB; không có nguồn nào khác
      vào bo đế.
- [ ] Bo cổ tay: không cạnh sắc; đầu nối Qwiic đã tháo hoặc có giá đỡ để không
      chạm da (A.3); tấm che cửa sổ quang nguyên vẹn; cáp dẹt không đứt, đúng chiều.
- [ ] Bo không nóng sau 5 phút chạy không tải [thời lượng 5 phút là đề xuất, chưa
      có nguồn; cách đo nhiệt và ngưỡng: chờ Đức Anh].
- [ ] Điện cực Ag/AgCl còn hạn, bao bì nguyên; dùng mới cho mỗi buổi.
- [ ] Máy cuff đúng model đã chọn, đúng cỡ vòng bít, hoạt động bình thường.
- [ ] Phiếu sàng lọc của buổi này: đủ điều kiện.

## 2. Dừng ngay buổi đo

Dừng ngay, tháo vòng bít, dừng nghiệm pháp, tháo điện cực và bo cổ tay khi:

1. Người tham gia yêu cầu dừng (không cần lý do).
2. Người tham gia báo hoặc có biểu hiện: chóng mặt, choáng, buồn nôn, đau ngực,
   hồi hộp, khó thở, lo âu rõ, tê/đau tay kéo dài sau khi cuff xả.
3. Da tại vị trí điện cực hoặc bo cổ tay đỏ, ngứa, rát, phồng.
4. Thiết bị nóng bất thường, có mùi khét, khói, hở dây; laptop bị cắm sạc hoặc nối
   thiết bị dùng điện lưới trong khi đang đeo.
5. Máy cuff báo lỗi, bơm không xả hoặc bơm quá mức.
6. Số đo cuff vượt ngưỡng dừng ở mục 3.

Dừng một **nghiệm pháp** (không nhất thiết cả buổi) khi:

- Thở chậm: chóng mặt, tê đầu ngón tay, khó chịu khi thở.
- Tính nhẩm: người tham gia muốn dừng hoặc căng thẳng rõ.
- Nước lạnh (bàn chân): đau không chịu được, hoặc hết thời lượng tối đa
  [thời lượng: chưa có nguồn, chờ chốt]; rút chân ra ngay khi người tham gia muốn.
- Đạp xe tư thế ngồi: mệt, khó thở, đau cơ, hoặc hết thời lượng đã duyệt.

Sau khi dừng: người tham gia ngồi nghỉ, nhóm hỏi lại triệu chứng sau [số] phút.
Nhóm **không chẩn đoán hay tư vấn y khoa**; khi triệu chứng không hết hoặc số đo
vượt ngưỡng, hướng dẫn người tham gia tới [cơ sở y tế/đầu mối — chờ xác nhận].

## 3. Ngưỡng huyết áp dừng phiên — chờ quyết định

Khung đạo đức v0.1 ghi ví dụ SBP > 180 mmHg hoặc DBP > 110 mmHg mà **chưa có
nguồn**. Bản này không khóa ngưỡng. Cần thầy/hội đồng quyết định: (a) ngưỡng
dừng phiên, (b) ngưỡng không cho bắt đầu nghiệm pháp, (c) có báo số đo cho người
tham gia không, (d) ai là đầu mối y tế khi vượt ngưỡng. Ngưỡng chỉ dùng cho an
toàn; **không dùng để loại dữ liệu khỏi phân tích**.

## 4. Ghi nhận sự cố

Mỗi lần dừng ghi một dòng vào nhật ký sự cố (chỉ mã):

| Trường | Ghi chú |
| --- | --- |
| `subject_id`, `session_id`, `event_id` | Mã nghiên cứu |
| Thời điểm, nghiệm pháp đang làm | |
| Lý do dừng (mục 2, số thứ tự) | |
| Triệu chứng, xử trí, thời gian hồi phục | Mô tả ngắn, không chẩn đoán |
| Người ghi (mã nhóm) | |
| Đã báo giảng viên/hội đồng chưa, ngày | Quy định báo cáo: [chờ hội đồng] |

Lượt đo bị dừng vẫn giữ trong log raw, gắn cờ. Không xóa để "làm sạch" kết quả.
Protocol v0.2 mục 10 hiện chỉ có quy tắc cho lượt mất nhãn cuff và lượt mất ECG,
**chưa có** quy tắc dùng lượt bị dừng trong phân tích: cần bổ sung vào mục 10
trước khi nộp hồ sơ (chờ quyết định).
