# An toàn buổi đo và quy tắc dừng — bản nháp v0.1

> Bản nháp chưa được phê duyệt. Không phải hướng dẫn xử trí y khoa. Ngưỡng huyết
> áp ở mục 3 và phương pháp đo dòng rò ở mục 1 là đề xuất của nhóm (2026-10-29),
> chờ thầy/bác sĩ/hội đồng duyệt. Huy soạn 2026-10-21; thiết bị theo
> [V1-module](../../configs/hardware/custom_board_proposal.md), nghiệm pháp theo
> [protocol v0.3 mục 6.4](../protocol/protocol_outline_v0.2.md).

## 1. Kiểm tra trước khi gắn thiết bị lên người

Một người đọc, một người kiểm; ghi vào nhật ký buổi (chỉ mã, không tên).

- [ ] Có văn bản phê duyệt đạo đức còn hiệu lực cho đúng protocol đang dùng.
- [ ] Biên bản đo dòng rò trên bo V1 thật (so với giới hạn IEC 60601-1 cho loại
      bộ phận ứng dụng tương ứng) đã có và được Đức Anh ký. **Hiện chưa có.**
      Phương pháp (đề xuất của nhóm 2026-10-29, chờ thầy):
  - Đo dòng rò bệnh nhân qua từng điện cực ECG và qua bo cổ tay.
  - Ưu tiên mượn máy phân tích an toàn điện y tế (phòng vật tư thiết bị y tế hoặc
    bệnh viện). Không mượn được thì tự dựng mạch đo MD theo IEC 60601-1 và đo bằng
    đồng hồ vạn năng, ghi rõ giới hạn đo và độ bất định.
  - Đo trên đúng cấu hình dùng trong buổi đo: PCB V1, bo MCU, cáp USB, laptop chạy
    pin.
  - Loại bộ phận ứng dụng dự kiến là BF (điện cực dán ngoài da), cần xác nhận.
    Giới hạn so sánh trích từ bản tiêu chuẩn khi viết biên bản.
  - Phạm vi phép đo ghi trong biên bản: dòng rò bệnh nhân và dòng phụ giữa các
    điện cực, điều kiện bình thường và lỗi đơn, thành phần AC và DC. Phần nào dụng
    cụ không đo được thì ghi rõ là chưa đo.
- [ ] Laptop chạy pin: đã rút sạc; không nối màn hình ngoài, ổ cứng có nguồn
      riêng, hub USB có nguồn hay cáp mạng.
- [ ] Bo MCU ESP32-S3 chỉ nối laptop qua một cáp USB-C; không có nguồn nào khác
      vào bo đế.
- [ ] Bo cổ tay: không cạnh sắc; đầu nối Qwiic đã tháo hoặc có giá đỡ để không
      chạm da (A.3); tấm che cửa sổ quang nguyên vẹn; cáp dẹt không đứt, đúng chiều.
- [ ] Bo không nóng sau 5 phút chạy không tải [thời lượng 5 phút là đề xuất, chưa
      có nguồn; cách đo nhiệt và ngưỡng: chờ Đức Anh].
- [ ] Mã dòng LED PPG không vượt trần của nghiên cứu: `0x7F` mỗi mã, khoảng
      25,4 mA mỗi nhánh LED (chốt 2026-10-29, Packet Schema V0.2 mục 13). Phần mềm PC
      từ chối mã lớn hơn, firmware cũng từ chối. Trần có thể hạ thấp hơn sau bring-up,
      không được nâng nếu không sửa đổi spec.
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
5. Máy cuff bơm không xả, bơm quá mức hoặc báo lỗi phần cứng. Máy xả bình thường
   nhưng không ra kết quả (lỗi đọc) thì không phải lý do dừng: được đo lại trong
   trần số lần bơm của protocol mục 6.4.
6. Số đo cuff vượt ngưỡng dừng ở mục 3.

Dừng một **nghiệm pháp** (không nhất thiết cả buổi) khi:

- Người tham gia muốn dừng nghiệm pháp đó mà không có triệu chứng ở danh sách trên.
- Thở chậm: tê đầu ngón tay hoặc khó chịu khi thở; người tham gia trở lại thở bình
  thường và ngồi nghỉ.
- Tính nhẩm: người tham gia muốn dừng, hoặc căng thẳng rõ nhưng không có triệu chứng ở
  danh sách trên.

Thứ tự ưu tiên (sửa 2026-10-30):
- Có bất kỳ triệu chứng nào ở danh sách dừng buổi (ý 2 ở trên, kể cả chóng mặt và lo
  âu rõ) thì dừng cả buổi, kể cả khi đang làm nghiệm pháp. Danh sách dừng nghiệm pháp
  chỉ dùng khi không có các triệu chứng đó.
- Tê đầu ngón tay hay khó chịu khi thở không hết sau 5 phút nghỉ thì cũng dừng cả buổi.

Từ 2026-10-29 protocol không còn nghiệm pháp ngâm chân nước lạnh (M3) và đạp xe
(M4), nên không có quy tắc dừng cho hai nghiệm pháp này.

Sau khi dừng: người tham gia ngồi nghỉ, nhóm hỏi lại triệu chứng sau 5 phút và một
lần nữa trước khi người tham gia ra về (đề xuất của nhóm 2026-10-29, chưa có nguồn).
Nhóm **không chẩn đoán hay tư vấn y khoa**; khi triệu chứng không hết hoặc số đo
vượt ngưỡng, hướng dẫn người tham gia tới [cơ sở y tế/đầu mối — chờ xác nhận].

## 3. Ngưỡng huyết áp — đề xuất của nhóm (2026-10-29), chờ thầy/bác sĩ duyệt

| Tình huống | Xử lý |
| --- | --- |
| (a) Bất kỳ lần cuff nào có SBP ≥ 180 mmHg hoặc DBP ≥ 110 mmHg | Dừng buổi đo (mục 2, ý 6) |
| (b) Trung bình các lần cuff M0 của buổi có SBP ≥ 140 mmHg hoặc DBP ≥ 90 mmHg | Không làm M1, M2 trong buổi đó; chỉ đo M0 |
| (c) Số đo rơi vào (a) hoặc (b) | Báo số đo cho người tham gia, kèm câu "đây là số đo trong nghiên cứu, không phải chẩn đoán", và khuyên đi khám |
| (d) Đầu mối y tế | [cơ sở y tế/đầu mối — chờ xác nhận] |

- Nguồn dự kiến cho hai mức: phân độ tăng huyết áp của hướng dẫn ESH/ESC
  (180/110 là ngưỡng độ 3, 140/90 là ngưỡng tăng huyết áp khi đo tại cơ sở y tế).
  **Chưa đọc nguyên văn**: phải đọc và ghi trang trước khi đưa vào hồ sơ.
- Ngưỡng tính trên số máy cuff hiển thị, không tính trên ước lượng của thiết bị
  nghiên cứu.
- Ngưỡng chỉ dùng cho an toàn; **không dùng để loại dữ liệu khỏi phân tích**.
  Quy tắc dùng lượt bị dừng ở protocol mục 10.

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
Quy tắc dùng trong phân tích ở protocol mục 10 (chốt 2026-10-29). Lượt đã có nhãn
cuff đầy đủ thì giữ, kể cả khi buổi dừng sau đó. Báo số lượt bị dừng theo nghiệm
pháp và theo người, kèm phân tích độ nhạy loại các lượt mang cờ dừng.
