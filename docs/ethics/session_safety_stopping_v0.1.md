# An toàn buổi đo và quy tắc dừng — bản nháp v0.1

> Bản nháp chưa được phê duyệt. Đây không phải hướng dẫn xử trí y khoa. Ngưỡng huyết
> áp ở mục 3 và phương pháp đo dòng rò ở mục 1 là đề xuất của nhóm (2026-10-29),
> chờ thầy/bác sĩ/hội đồng duyệt. Huy soạn ngày 2026-10-21; phần thiết bị theo
> [V1-module](../../configs/hardware/custom_board_proposal.md), phần nghiệm pháp theo
> [protocol v0.3 mục 6.4](../protocol/protocol_outline_v0.2.md).

## 1. Kiểm tra trước khi gắn thiết bị lên người

Một người đọc, một người kiểm tra; kết quả ghi vào nhật ký buổi đo (chỉ ghi mã,
không ghi tên).

- [ ] Có văn bản phê duyệt đạo đức còn hiệu lực cho đúng protocol đang dùng.
- [ ] Đã có biên bản đo dòng rò trên bo V1 thật, có so với giới hạn IEC 60601-1
      cho loại bộ phận ứng dụng tương ứng, và biên bản đã được Đức Anh ký.
      **Hiện chưa có.** Phương pháp đo (đề xuất của nhóm 2026-10-29, chờ thầy):
  - Đo dòng rò bệnh nhân qua từng điện cực ECG và qua bo cổ tay.
  - Ưu tiên mượn máy phân tích an toàn điện y tế từ phòng vật tư thiết bị y tế hoặc
    bệnh viện. Nếu không mượn được thì tự dựng mạch đo MD theo IEC 60601-1, đo bằng
    đồng hồ vạn năng và ghi rõ giới hạn đo cùng độ bất định.
  - Đo trên đúng cấu hình dùng trong buổi đo: PCB V1, bo MCU, cáp USB và laptop chạy
    pin.
  - Loại bộ phận ứng dụng dự kiến là BF (điện cực dán ngoài da), cần xác nhận. Giới
    hạn dùng để so sánh sẽ được trích từ bản tiêu chuẩn khi viết biên bản.
  - Biên bản ghi phạm vi phép đo: dòng rò bệnh nhân và dòng phụ giữa các điện cực, ở
    điều kiện bình thường và điều kiện lỗi đơn, cả thành phần AC lẫn DC. Phần nào
    dụng cụ không đo được thì ghi rõ là chưa đo.
- [ ] Laptop chạy pin: đã rút sạc, không nối màn hình ngoài, ổ cứng có nguồn riêng,
      hub USB có nguồn hay cáp mạng.
- [ ] Bo MCU ESP32-S3 chỉ nối với laptop qua một cáp USB-C; không có nguồn nào khác
      cấp vào bo đế.
- [ ] Bo cổ tay:
  - không có cạnh sắc;
  - đầu nối Qwiic đã được tháo, hoặc có giá đỡ để không chạm da (A.3);
  - tấm che cửa sổ quang còn nguyên vẹn;
  - cáp dẹt không bị đứt và được cắm đúng chiều.
- [ ] Bo không nóng sau 5 phút chạy không tải [thời lượng 5 phút là đề xuất, chưa
      có nguồn; cách đo nhiệt và ngưỡng: chờ Đức Anh].
- [ ] Mã dòng LED PPG không vượt trần của nghiên cứu: `0x7F` cho mỗi mã, tức khoảng
      25,4 mA cho mỗi nhánh LED (chốt 2026-10-29, Packet Schema V0.2 mục 13). Cả
      phần mềm PC lẫn firmware đều từ chối mã lớn hơn. Sau bring-up, trần có thể được
      hạ thấp hơn, nhưng không được nâng lên nếu không sửa đổi spec.
- [ ] Điện cực Ag/AgCl còn hạn dùng, bao bì còn nguyên; mỗi buổi dùng điện cực mới.
- [ ] Máy cuff đúng model đã chọn, vòng bít đúng cỡ, máy hoạt động bình thường.
- [ ] Phiếu sàng lọc của buổi này cho kết quả đủ điều kiện.

## 2. Dừng ngay buổi đo

Dừng ngay buổi đo, tháo vòng bít, dừng nghiệm pháp, tháo điện cực và bo cổ tay trong
các trường hợp sau:

1. Người tham gia yêu cầu dừng, không cần nêu lý do.
2. Người tham gia báo hoặc có biểu hiện một trong các triệu chứng: chóng mặt, choáng,
   buồn nôn, đau ngực, hồi hộp, khó thở, lo âu rõ, tê hoặc đau tay kéo dài sau khi
   cuff đã xả.
3. Da tại vị trí dán điện cực hoặc đeo bo cổ tay bị đỏ, ngứa, rát hoặc phồng.
4. Thiết bị nóng bất thường, có mùi khét, bốc khói hoặc hở dây; hoặc laptop bị cắm
   sạc hay bị nối với thiết bị dùng điện lưới trong khi người tham gia đang đeo.
5. Máy cuff bơm mà không xả, bơm quá mức hoặc báo lỗi phần cứng. Nếu máy xả bình
   thường nhưng không ra kết quả (lỗi đọc) thì đó không phải lý do dừng: được đo
   lại, miễn là vẫn trong trần số lần bơm của protocol mục 6.4.
6. Số đo cuff bằng hoặc cao hơn ngưỡng dừng ở mục 3.

Dừng một **nghiệm pháp** (không nhất thiết dừng cả buổi) khi:

- Người tham gia muốn dừng nghiệm pháp đó và không có triệu chứng nào trong danh
  sách trên.
- Thở chậm: người tham gia bị tê đầu ngón tay hoặc khó chịu khi thở. Khi đó người
  tham gia trở lại thở bình thường và ngồi nghỉ.
- Tính nhẩm: người tham gia muốn dừng, hoặc căng thẳng rõ nhưng không có triệu chứng
  nào trong danh sách trên.

Thứ tự ưu tiên (sửa 2026-10-30):
- Nếu có bất kỳ triệu chứng nào trong danh sách dừng buổi (ý 2 ở trên, kể cả chóng
  mặt và lo âu rõ) thì dừng cả buổi, kể cả khi đang làm nghiệm pháp. Danh sách dừng
  nghiệm pháp chỉ áp dụng khi không có các triệu chứng đó.
- Nếu tê đầu ngón tay hay khó chịu khi thở không hết sau 5 phút nghỉ thì cũng dừng
  cả buổi.

Từ 2026-10-29, protocol không còn nghiệm pháp ngâm chân nước lạnh (M3) và đạp xe
(M4), nên không có quy tắc dừng cho hai nghiệm pháp này.

Sau khi dừng, người tham gia ngồi nghỉ. Nhóm hỏi lại về triệu chứng sau 5 phút và
hỏi thêm một lần nữa trước khi người tham gia ra về (đề xuất của nhóm 2026-10-29,
chưa có nguồn). Nhóm **không chẩn đoán hay tư vấn y khoa**. Khi triệu chứng không
hết hoặc số đo bằng hoặc cao hơn ngưỡng, nhóm hướng dẫn người tham gia tới
[cơ sở y tế/đầu mối — chờ xác nhận].

## 3. Ngưỡng huyết áp — đề xuất của nhóm (2026-10-29), chờ thầy/bác sĩ duyệt

| Tình huống | Xử lý |
| --- | --- |
| (a) Bất kỳ lần đo cuff nào có SBP ≥ 180 mmHg hoặc DBP ≥ 110 mmHg | Dừng buổi đo (mục 2, ý 6) |
| (b) Trung bình các lần đo cuff M0 của buổi có SBP ≥ 140 mmHg hoặc DBP ≥ 90 mmHg | Không làm M1, M2 trong buổi đó; chỉ đo M0 |
| (c) Số đo rơi vào (a) hoặc (b) | Báo số đo cho người tham gia, kèm câu "đây là số đo trong nghiên cứu, không phải chẩn đoán", và khuyên người tham gia đi khám |
| (d) Đầu mối y tế | [cơ sở y tế/đầu mối — chờ xác nhận] |

- Nguồn dự kiến cho hai mức này là phân độ tăng huyết áp trong hướng dẫn ESH/ESC:
  180/110 là ngưỡng độ 3, còn 140/90 là ngưỡng tăng huyết áp khi đo tại cơ sở y tế.
  **Chưa đọc nguyên văn**: phải đọc và ghi số trang trước khi đưa vào hồ sơ.
- Ngưỡng được tính trên số do máy cuff hiển thị, không tính trên ước lượng của thiết
  bị nghiên cứu.
- Ngưỡng chỉ dùng cho an toàn, **không dùng để loại dữ liệu khỏi phân tích**. Quy
  tắc sử dụng các lượt đo bị dừng nằm ở protocol mục 10.

## 4. Ghi nhận sự cố

Mỗi lần dừng, ghi một dòng vào nhật ký sự cố (chỉ ghi mã):

| Trường | Ghi chú |
| --- | --- |
| `subject_id`, `session_id`, `event_id` | Mã nghiên cứu |
| Thời điểm, nghiệm pháp đang làm | |
| Lý do dừng (số thứ tự ở mục 2) | |
| Triệu chứng, xử trí, thời gian hồi phục | Mô tả ngắn, không chẩn đoán |
| Người ghi (mã nhóm) | |
| Đã báo giảng viên/hội đồng chưa, ngày báo | Quy định báo cáo: [chờ hội đồng] |

Lượt đo bị dừng vẫn được giữ trong log raw và được gắn cờ. Không xóa lượt đo để
"làm sạch" kết quả. Quy tắc sử dụng trong phân tích nằm ở protocol mục 10
(chốt 2026-10-29). Lượt đã có nhãn cuff đầy đủ thì được giữ, kể cả khi buổi đo
dừng sau đó. Số lượt bị dừng được báo cáo theo nghiệm pháp và theo người, kèm phân
tích độ nhạy loại các lượt mang cờ dừng.
