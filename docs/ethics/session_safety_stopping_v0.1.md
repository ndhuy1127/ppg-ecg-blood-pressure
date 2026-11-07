# An toàn buổi đo và quy tắc dừng — bản nháp v0.1

> **Ghi chú nội bộ (không đưa vào bản nộp).** Bản nháp chưa được phê duyệt. Đây không phải hướng
> dẫn xử trí y khoa. Phần dưới đường kẻ là đúng nội dung bản nộp; bản Word được dựng từ file
> này. Ô `[...]` chờ thầy, bác sĩ/đầu mối y tế hoặc hội đồng.
>
> - Huy soạn 2026-10-21; phần thiết bị theo
>   [V1-module](../../configs/hardware/custom_board_proposal.md), phần nghiệm pháp theo
>   [protocol v0.3 mục 6.4](../protocol/protocol_outline_v0.2.md).
> - 2026-10-29 (đề xuất của nhóm, chờ thầy/bác sĩ/hội đồng): ngưỡng huyết áp ở mục 6, phương
>   pháp đo dòng rò ở mục 9, hỏi lại triệu chứng sau 5 phút và trước khi ra về. Trần mã LED
>   `0x7F` chốt 2026-10-29 (Packet Schema V0.2 mục 13). Không còn quy tắc dừng cho M3, M4 (đã bỏ).
> - 2026-10-30: thứ tự ưu tiên giữa dừng buổi và dừng nghiệm pháp.
> - 2026-10-31, sau rà soát cuối (đề xuất, chờ thầy/đầu mối y tế): thêm mục 1 (người trực, ít nhất
>   hai thành viên), mục 3 (theo dõi trong buổi đo, hướng dẫn thở), mục 7 (trước khi ra về) và mục
>   8 (triệu chứng nặng, cấp cứu); thử nhiệt loại một lần 120 phút ở trần LED thay cho chỉ kiểm
>   "không nóng sau 5 phút"; máy đo huyết áp chỉ nối với người tham gia qua ống hơi; viết lại câu
>   về laptop cho rõ; người ký biên bản ghi theo vai trò.
> - 2026-10-31, sau vòng phản biện thứ hai của Codex: mục 8 tách trường hợp ngất nhưng thở bình
>   thường với trường hợp không tỉnh hoặc không thở bình thường (gọi 115, ép tim theo hướng dẫn của
>   tổng đài); mục 7 thêm đứng dậy từ từ; mục 10 nói rõ việc hỏi thăm sau sự cố chỉ khi người tham
>   gia đồng ý ở mục 9 của phiếu đồng thuận, giữ liên lạc tối đa 30 ngày. Không thêm ngưỡng huyết
>   áp thấp bằng số: chưa có nguồn, và người trẻ khỏe có thể có huyết áp tâm thu dưới 100 mmHg mà
>   không có triệu chứng; quy tắc dừng dựa trên triệu chứng vẫn giữ.
> - 2026-11-07, sau review Tuần 6 (đề xuất của nhóm, chờ đầu mối y tế duyệt): mục 8 ý 3 tách ba
>   nhánh theo hướng dẫn hồi sinh cơ bản cho người lớn (Resuscitation Council UK 2025): tỉnh lại
>   nhanh; không tỉnh nhưng thở bình thường (nằm nghiêng an toàn, theo dõi nhịp thở, không ép tim);
>   không đáp ứng và không thở bình thường (ép tim). Bản trước cho ép tim cả khi người tham gia
>   chưa tỉnh nhưng vẫn thở bình thường. Mục 6 thêm ý (d)–(f): số đo ≥ 180/110 kèm triệu chứng thì
>   gọi 115; không triệu chứng thì gọi đầu mối y tế trong buổi; ≥ 140/90 thì khuyên đi khám. Danh
>   sách triệu chứng ở ý (d) là đề xuất, chưa có nguồn; ESC 2024 yêu cầu đánh giá khả năng cấp cứu
>   tăng huyết áp khi BP ≥ 180/110 [số trang]. Bộ Word ngày 2026-10-31 phải dựng lại theo file này.
> - Nguồn của hai ngưỡng huyết áp **chưa đọc nguyên văn**: phải đọc và ghi số trang trước khi
>   nộp. Europe PMC không có toàn văn; theo OpenAlex (tra 2026-10-29), hướng dẫn ESH 2023
>   ([10.1097/HJH.0000000000003480](https://doi.org/10.1097/HJH.0000000000003480)) có bản ở kho
>   của Maastricht University và Erasmus University Rotterdam, hướng dẫn ESC 2024
>   ([10.1093/eurheartj/ehae178](https://doi.org/10.1093/eurheartj/ehae178)) có bản nộp trên
>   figshare.

---

Quy trình này áp dụng cho mọi buổi đo trên người tham gia. Nhóm nghiên cứu **không chẩn đoán và
không tư vấn y khoa**; các quyết định dưới đây là quy tắc an toàn của nghiên cứu.

## 1. Người trực và trách nhiệm

- Mỗi buổi đo có ít nhất hai thành viên nhóm đã được huấn luyện theo quy trình này: một người vận
  hành thiết bị và máy đo huyết áp, một người theo dõi người tham gia và ghi chép.
- Ít nhất một người có mặt đã học sơ cứu cơ bản: [họ tên, chứng nhận sơ cứu].
- Danh sách người được phép vận hành buổi đo: [danh sách người trực].
- Đầu mối y tế: [cơ sở y tế/đầu mối y tế, điện thoại].

## 2. Kiểm tra trước khi gắn thiết bị lên người

Một người đọc, một người kiểm tra; kết quả ghi vào phiếu ghi buổi đo (chỉ ghi mã, không ghi tên).

- [ ] Có văn bản chấp thuận đạo đức còn hiệu lực cho đúng phiên bản đề cương đang dùng.
- [ ] Đã có biên bản đo dòng rò và biên bản thử nhiệt trên chính bộ thiết bị này (mục 9), kết quả
      đạt, có chữ ký của người phụ trách phần cứng.
- [ ] Laptop chạy bằng pin và đã rút sạc. Laptop không nối với thiết bị nào khác cắm điện lưới
      (màn hình ngoài, ổ cứng hay hub USB có nguồn riêng) và không cắm cáp mạng.
- [ ] Bo MCU chỉ nối với laptop qua một cáp USB-C; không có nguồn nào khác cấp vào bo đế.
- [ ] Máy đo huyết áp chỉ nối với người tham gia qua ống hơi và vòng bít, không có dây điện nào nối
      với thiết bị nghiên cứu. [Máy chạy pin trong lúc đo nếu model cho phép.]
- [ ] Bo cổ tay không có cạnh sắc; đầu nối Qwiic đã được tháo hoặc có giá đỡ để không chạm da; tấm
      che cửa sổ quang còn nguyên vẹn; cáp dẹt không đứt và được cắm đúng chiều.
- [ ] Sau 5 phút chạy, bo cổ tay không ấm bất thường khi chạm (kiểm tra nhanh; giới hạn nhiệt độ
      được kiểm bằng phép thử ở mục 9).
- [ ] Dòng LED của bo cảm biến không vượt trần của nghiên cứu: mã `0x7F` cho mỗi màu, tức khoảng
      25,4 mA cho mỗi nhánh LED. Phần mềm trên máy tính và firmware đều từ chối mức cao hơn. Trần
      này chỉ có thể được hạ thấp hơn.
- [ ] Điện cực Ag/AgCl còn hạn dùng, bao bì còn nguyên; mỗi buổi dùng điện cực mới.
- [ ] Máy đo huyết áp đúng model đã chọn, vòng bít đúng cỡ, máy hoạt động bình thường.
- [ ] Phiếu sàng lọc của buổi này cho kết quả đủ điều kiện.
- [ ] Điện thoại, số cấp cứu 115 và số của đầu mối y tế có sẵn ở phòng đo.

## 3. Trong buổi đo

- Người theo dõi quan sát người tham gia suốt buổi đo, nhất là trong hai nghiệm pháp, và hỏi người
  tham gia có thấy khó chịu không sau mỗi nghiệm pháp.
- Trước khi thở chậm, người tham gia được dặn thở nhẹ nhàng ở độ sâu thoải mái, không cố hít thật
  sâu và không nín thở.
- Giữa thở chậm và tính nhẩm có ít nhất 5 phút nghỉ. Chỉ bắt đầu tính nhẩm khi người tham gia không
  còn chóng mặt hay tê đầu ngón tay.
- Giữa hai lần bơm vòng bít có ít nhất 2 phút nghỉ. Số lần bơm không vượt trần ghi trong đề cương
  (mục 6.3 của đề cương).

## 4. Dừng ngay buổi đo

Dừng ngay buổi đo, tháo vòng bít, dừng nghiệm pháp, tháo điện cực và bo cổ tay trong các trường hợp
sau:

1. Người tham gia yêu cầu dừng, không cần nêu lý do.
2. Người tham gia báo hoặc có biểu hiện một trong các triệu chứng: chóng mặt, choáng, buồn nôn, đau
   ngực, hồi hộp, khó thở, lo âu rõ, tê hoặc đau tay kéo dài sau khi vòng bít đã xả.
3. Da tại vị trí dán điện cực hoặc đeo bo cổ tay bị đỏ, ngứa, rát hoặc phồng.
4. Thiết bị nóng bất thường, có mùi khét, bốc khói hoặc hở dây; hoặc laptop bị cắm sạc hay bị nối
   với thiết bị dùng điện lưới trong khi người tham gia đang đeo.
5. Máy đo huyết áp bơm mà không xả, bơm quá mức hoặc báo lỗi phần cứng. Nếu máy xả bình thường
   nhưng không ra kết quả (lỗi đọc) thì đó không phải lý do dừng: được đo lại, miễn là vẫn trong
   trần số lần bơm.
6. Số đo huyết áp bằng hoặc cao hơn ngưỡng dừng ở mục 6.

## 5. Dừng một nghiệm pháp

Dừng một **nghiệm pháp** (không nhất thiết dừng cả buổi) khi:

- Người tham gia muốn dừng nghiệm pháp đó và không có triệu chứng nào ở mục 4, ý 2.
- Thở chậm: người tham gia bị tê đầu ngón tay hoặc khó chịu khi thở. Khi đó người tham gia trở lại
  thở bình thường và ngồi nghỉ.
- Tính nhẩm: người tham gia muốn dừng, hoặc căng thẳng rõ nhưng không có triệu chứng nào ở mục 4,
  ý 2.

Thứ tự ưu tiên:

- Nếu có bất kỳ triệu chứng nào ở mục 4, ý 2 (kể cả chóng mặt và lo âu rõ) thì dừng cả buổi, kể cả
  khi đang làm nghiệm pháp. Quy tắc dừng nghiệm pháp chỉ áp dụng khi không có các triệu chứng đó.
- Nếu tê đầu ngón tay hay khó chịu khi thở không hết sau 5 phút nghỉ thì cũng dừng cả buổi.

## 6. Ngưỡng huyết áp

<!-- cols: 55,45 -->
| Tình huống | Xử lý |
| --- | --- |
| (a) Bất kỳ lần đo nào, kể cả hai lần đo hai tay ở buổi 1, có huyết áp tâm thu ≥ 180 mmHg hoặc tâm trương ≥ 110 mmHg | Dừng buổi đo (mục 4, ý 6) |
| (b) Trung bình các lần đo lúc nghỉ (M0) của buổi có huyết áp tâm thu ≥ 140 mmHg hoặc tâm trương ≥ 90 mmHg | Không làm hai nghiệm pháp trong buổi đó; chỉ đo lúc nghỉ |
| (c) Số đo rơi vào (a) hoặc (b) | Báo số đo cho người tham gia, kèm câu "đây là số đo trong nghiên cứu, không phải chẩn đoán", và khuyên người tham gia đi khám |
| (d) Số đo rơi vào (a) và người tham gia có đau ngực, khó thở, đau đầu dữ dội, nhìn mờ, yếu hoặc tê nửa người, nói khó, hay lú lẫn | Xử trí như triệu chứng nặng (mục 8): gọi 115 ngay |
| (e) Số đo rơi vào (a), không có triệu chứng ở ý (d) | Ngồi nghỉ, hỏi lại triệu chứng sau 5 phút (mục 7); gọi đầu mối y tế ngay trong buổi và làm theo hướng dẫn của đầu mối; khuyên người tham gia đi khám trong ngày. [thời hạn đi khám và nơi chuyển: chờ đầu mối y tế duyệt] |
| (f) Số đo rơi vào (b) | Khuyên người tham gia đi khám để được đo lại theo đúng quy trình chẩn đoán. Buổi sau vẫn làm theo quy tắc của bảng này |
| (g) Đầu mối y tế | [cơ sở y tế/đầu mối y tế, điện thoại] |

- Hai mức này theo phân độ tăng huyết áp của hướng dẫn ESH 2023 [số trang] và ESC 2024 [số trang]:
  180/110 mmHg là ngưỡng tăng huyết áp độ 3, còn 140/90 mmHg là ngưỡng tăng huyết áp khi đo tại cơ
  sở y tế.
- Ngưỡng được tính trên số do máy đo huyết áp hiển thị, không tính trên ước lượng của thiết bị
  nghiên cứu.
- Ngưỡng chỉ dùng cho an toàn, **không dùng để loại dữ liệu khỏi phân tích**.

## 7. Sau khi dừng và trước khi người tham gia ra về

- Sau khi dừng buổi đo, người tham gia ngồi nghỉ. Nhóm hỏi lại về triệu chứng sau 5 phút và hỏi
  thêm một lần nữa trước khi người tham gia ra về. Hỏi lại như vậy cả ở những buổi kết thúc bình
  thường.
- Khi kết thúc, người tham gia ngồi dậy và đứng lên từ từ; nếu thấy chóng mặt khi đứng thì ngồi lại
  nghỉ, và nhóm hỏi lại triệu chứng sau 5 phút.
- Người tham gia chỉ ra về khi không còn triệu chứng. Khi triệu chứng không hết hoặc số đo bằng hoặc
  cao hơn ngưỡng ở mục 6, nhóm hướng dẫn người tham gia tới đầu mối y tế (mục 6, ý g).
- Trước khi ra về, người tham gia được dặn liên hệ nhóm nếu da bị đỏ hay ngứa quá 2 ngày, bị phồng
  rộp, hoặc có bất kỳ khó chịu nào sau buổi đo.

## 8. Triệu chứng nặng và cấp cứu

Các dấu hiệu sau được coi là nặng: đau ngực, khó thở nặng, ngất hoặc lơ mơ, co giật, phản ứng dị ứng
lan rộng. Khi đó [quy trình chờ đầu mối y tế duyệt]:

1. Dừng mọi việc; tháo vòng bít, điện cực và bo cổ tay.
2. Một người gọi ngay cấp cứu 115 và [trạm y tế/đầu mối y tế]; người đã học sơ cứu ở cạnh người
   tham gia.
3. Xử trí theo việc người tham gia có đáp ứng và có thở bình thường hay không:
   - Choáng hoặc ngất, tỉnh lại nhanh và thở bình thường: đặt nằm ngửa ở nơi an toàn, kê cao chân
     nếu không có chấn thương, và theo dõi tới khi tỉnh hẳn.
   - Không tỉnh lại nhanh nhưng vẫn thở bình thường: đặt nằm nghiêng an toàn, gọi 115 nếu chưa gọi,
     và người đã học sơ cứu theo dõi nhịp thở liên tục cho tới khi nhân viên cấp cứu tới. Nếu người
     tham gia ngừng thở hoặc thở không bình thường thì làm như ý dưới.
   - Không đáp ứng và không thở hoặc thở không bình thường (kể cả chỉ thở ngáp từng cơn): gọi 115
     ngay nếu chưa gọi, và người đã học sơ cứu bắt đầu hồi sinh tim phổi (ép tim) theo hướng dẫn của
     tổng đài 115 cho tới khi nhân viên cấp cứu tới.

   Nhóm không cho người tham gia dùng thuốc.
4. Ghi lại thời điểm, diễn biến và việc đã làm.
5. Báo ngay giảng viên hướng dẫn, rồi báo hội đồng đạo đức theo mục 10.

Thông tin dán sẵn ở phòng đo: địa chỉ phòng đo [địa chỉ, tầng, phòng], số cấp cứu 115, số của đầu
mối y tế, và lối đưa người bệnh ra xe cấp cứu [mô tả].

## 9. Thử an toàn điện và nhiệt trước khi dùng trên người

**Đo dòng rò:**

- Đo dòng rò qua người tham gia (dòng rò bệnh nhân) ở từng điện cực ECG và ở bo cổ tay.
- Ưu tiên mượn máy phân tích an toàn điện y tế từ đơn vị vật tư thiết bị y tế hoặc bệnh viện. Nếu
  không mượn được thì dựng mạch đo theo IEC 60601-1, đo bằng đồng hồ vạn năng và ghi rõ giới hạn đo
  cùng độ bất định.
- Đo trên đúng cấu hình dùng trong buổi đo: bo mạch nghiên cứu, bo MCU, cáp USB và laptop chạy pin.
- Loại bộ phận ứng dụng dự kiến là BF (điện cực dán ngoài da) [cần xác nhận]. Giới hạn dùng để so
  sánh được trích từ bản tiêu chuẩn khi viết biên bản.
- Biên bản ghi phạm vi phép đo: dòng rò bệnh nhân và dòng phụ giữa các điện cực, ở điều kiện bình
  thường và điều kiện lỗi đơn, cả thành phần AC lẫn DC. Phần nào dụng cụ không đo được thì ghi rõ
  là chưa đo, và thiết bị chỉ được dùng trên người khi người có chuyên môn [người duyệt biên bản]
  xác nhận phần đã đo là đủ.

**Thử nhiệt:** cho thiết bị chạy liên tục 120 phút (bằng buổi đo dài nhất) với dòng LED ở trần của
nghiên cứu, ở nhiệt độ phòng đo; đo nhiệt độ bề mặt bo cổ tay ở mặt tiếp xúc da. Nhiệt độ cao nhất
không được vượt [giới hạn cho bộ phận tiếp xúc da của IEC 60601-1, trích khi viết biên bản].

## 10. Ghi nhận và báo cáo sự cố

Mỗi lần dừng buổi đo hay dừng nghiệm pháp, nhóm ghi một dòng vào nhật ký sự cố (chỉ ghi mã):

<!-- cols: 38,62 -->
| Trường | Ghi chú |
| --- | --- |
| Mã người tham gia, mã buổi, mã lượt đo | Mã nghiên cứu |
| Thời điểm, nghiệm pháp đang làm | |
| Lý do dừng (số thứ tự ở mục 4 hoặc 5) | |
| Triệu chứng, xử trí, thời gian hồi phục | Mô tả ngắn, không chẩn đoán |
| Người ghi (mã nhóm) | |
| Ngày báo giảng viên hướng dẫn và hội đồng | Theo quy định báo cáo của hội đồng: [thời hạn và kênh báo] |

- Sự cố nặng (mục 8) được báo cho giảng viên hướng dẫn ngay trong ngày và báo hội đồng đạo đức theo
  thời hạn của hội đồng [thời hạn].
- Nếu khi ra về người tham gia còn triệu chứng và đã đồng ý ở mục 9 của phiếu đồng thuận, nhóm hỏi
  thăm cho tới khi hết triệu chứng, giữ thông tin liên lạc tối đa 30 ngày cho việc này rồi xóa. Nếu
  người tham gia không đồng ý, nhóm dặn người tham gia tự liên hệ nhóm hoặc đầu mối y tế khi cần.
- Lượt đo bị dừng vẫn được giữ trong dữ liệu gốc và được gắn cờ; nhóm không xóa lượt đo để "làm
  sạch" kết quả. Lượt đã có số đo huyết áp đầy đủ thì được giữ trong phân tích, kể cả khi buổi đo
  dừng sau đó. Số lượt bị dừng được báo cáo theo nghiệm pháp và theo người, kèm phân tích độ nhạy
  loại các lượt mang cờ dừng.
