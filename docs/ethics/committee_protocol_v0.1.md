# Đề cương nghiên cứu nộp hội đồng đạo đức — bản nháp v0.1

> **Ghi chú nội bộ (không đưa vào bản nộp).** Bản tóm tắt cho hội đồng của
> [protocol v0.3](../protocol/protocol_outline_v0.2.md), viết ngày 2026-10-31 sau rà soát cuối hồ
> sơ. Hội đồng chỉ nhận bản này (kèm các phụ lục), không nhận protocol kỹ thuật, nên bản này phải
> tự đứng được và không dùng ký hiệu nội bộ (K1–K6, G2, G4, R3, mã packet). **Khi protocol v0.3 đổi
> thì phải sửa file này**; chỗ nào khác nhau thì protocol là nguồn, trừ tiêu chí chọn/loại (nguồn là
> [phiếu sàng lọc](eligibility_screening_v0.1.md)). Phần dưới đường kẻ là đúng nội dung bản nộp; bản
> Word được dựng từ file này. Ô `[...]` chờ thầy, đơn vị hoặc hội đồng.
>
> - Các mục là **đề xuất của nhóm, chờ thầy/hội đồng** giống protocol v0.3 (danh sách ở
>   [README](README.md)). Mục mới so với protocol, cũng là đề xuất: cách tuyển và lấy đồng thuận
>   (4.5–4.6), người trực (9.7), thử nhiệt (5.1), nghỉ 5 phút trước khi đo hai tay và thứ tự đo
>   (6.2), giới tính (mục 7), mô tả thiết kế là "thực nghiệm có nghiệm pháp sinh lý" thay vì
>   "quan sát".
> - Sửa cùng ngày sau vòng thảo luận thứ hai: PAT được định nghĩa là khoảng từ đỉnh R tới
>   chân sóng PPG, không gọi là "thời gian truyền mạch"; thiết bị ghi là "chưa được cấp phép như thiết
>   bị y tế" và câu hỏi gửi hội đồng ở 9.8 hỏi phạm vi pháp luật áp dụng thay vì xin xác nhận một kết
>   luận có sẵn (Điều 24 của Nghị định 98/2021/NĐ-CP miễn đăng ký cho *thiết bị y tế* dùng cho nghiên
>   cứu, nên không tự chứng minh thiết bị không phải thiết bị y tế); thêm tiêu chí kết luận phải vượt
>   cả PPG-only lẫn zero-change (RQ v0.4 mục 4.E, đề xuất chờ thầy) và chi tiết RQ2b, RQ3; người đo
>   thử tham gia 2–3 buổi như người khác (đề xuất mới, protocol 6.5 chỉ định P2 trong một buổi chứ
>   không nói số buổi của pilot) và việc phải làm khi dải ΔBP ở pilot quá hẹp (protocol 6.4,
>   "Dự phòng").
> - Sửa 2026-11-21 theo các thay đổi của dự án từ 2026-11-01:
>   - **Lịch và số buổi (chốt 2026-11-19):** mỗi người 2 buổi, buổi 2 cách buổi 1 ít nhất 7 ngày
>     và trong 4 tuần; không có buổi 3. Đề tài kết thúc đầu tháng 7/2027: buổi 1 cuối cùng
>     29/04/2027, buổi đo cuối 14/05/2027, khóa dữ liệu 21/05/2027 (mục 3, 4.2, 4.4, 6.5, 8.1,
>     9.3, 10, 12). Thay cho "3 buổi, tối thiểu 2, buổi 2 cách buổi 1 ít nhất 1 ngày" của protocol
>     v0.3 mục 3; protocol mục 3, 4.1, 6.4, 6.5, 9.1 và SAP sửa theo cùng ngày.
>   - **Thêm người trực (chốt 2026-11-19):** nhóm huấn luyện thêm 2 người trực; công suất 7–10
>     buổi mỗi tuần tùy số người trực (mục 4.4, 9.7, 11).
>   - **Chia sẻ dữ liệu tùy chọn (chốt 2026-11-19):** mục 7, 9.4; chi tiết ở phiếu đồng thuận mục 11
>     và quản lý dữ liệu mục 9.
>   - **Phân tích (SAP v1, chốt 2026-11-12 và 2026-11-19):** kiểu khoảng tin cậy, Holm giữa tâm thu
>     và tâm trương, quy tắc và trần của mức hiệu ứng nhỏ nhất, hai cách dự đoán không dùng tín
>     hiệu (mục 8.2, 8.4); tiêu chí dải thay đổi huyết áp ở đo thử (P2: trung vị thay đổi tâm thu
>     có dấu ở tính nhẩm ≥ 10 mmHg, mức báo động; mục 6.5).
>   - **Thiết bị (chốt 2026-11-19, không sửa module):** đầu chuyển có điện trở giới hạn dòng cho cáp
>     điện cực, nằm trong hộp khóa; giá đỡ che đầu nối và đèn báo ở bo cổ tay; thử nhiệt làm với giá
>     đỡ thật (mục 5.1, 9.1). Phần cứng V1 đã về, bring-up bắt đầu 2026-11-20 chỉ với tín hiệu nhân
>     tạo; chưa đo dòng rò.
> - Vẫn chưa đưa vào: nghiệm pháp duỗi gối tĩnh (M6; chỉ vào lần nộp đầu nếu tới 2026-12-04 đạt
>   tiêu chí của [đề xuất Tuần 7](../meetings/week_07_de_xuat_sua_protocol_va_ho_so.md) mục 2.5),
>   thêm lần cuff hay đo lặp cuff (quyết cùng ngày), pilot nội bộ. Nếu đưa vào thì sửa protocol,
>   file này và các phụ lục cùng lúc.

---

- **Tên nghiên cứu:** Nguyên mẫu đeo cổ tay thu đồng thời tín hiệu quang học (PPG) và điện tim
  (ECG) để ước lượng thay đổi huyết áp sau hiệu chuẩn cá nhân.
- **Chủ nhiệm đề tài:** [họ tên, học hàm, học vị, đơn vị]
- **Giảng viên hướng dẫn:** [họ tên, học hàm, học vị, đơn vị]
- **Đơn vị chủ trì:** [tên trường, khoa/viện]
- **Địa điểm nghiên cứu:** [phòng thí nghiệm, địa chỉ]
- **Thời gian thực hiện:** từ [tháng/năm] đến tháng 7/2027; chỉ đo trên người sau khi có văn bản
  chấp thuận của hội đồng đạo đức.
- **Kinh phí:** [nguồn kinh phí]

## Tóm tắt nghiên cứu

<!-- cols: 24,76 -->
| Mục | Nội dung |
| --- | --- |
| Mục tiêu chính | Đánh giá xem thêm PAT (khoảng thời gian từ đỉnh R của điện tim đến chân sóng PPG ở cổ tay) vào mô hình chỉ dùng tín hiệu PPG cổ tay có làm giảm sai số ước lượng thay đổi huyết áp ở các buổi đo sau buổi hiệu chuẩn hay không |
| Thiết kế | Nghiên cứu thực nghiệm tiến cứu trên người tình nguyện khỏe mạnh, đo lặp lại 2 buổi cách nhau ít nhất 7 ngày; không dùng thuốc, không can thiệp điều trị, không lấy mẫu sinh học; có hai nghiệm pháp sinh lý (thở chậm, tính nhẩm) |
| Người tham gia | Người trưởng thành khỏe mạnh 18–35 tuổi; tối đa 35 người, kể cả 2–3 người đo thử |
| Thiết bị | Thiết bị nguyên mẫu chỉ dùng cho nghiên cứu, chưa được cấp phép như thiết bị y tế: bo cảm biến quang và chuyển động ở cổ tay trái, ba điện cực dán Ag/AgCl nối qua đầu chuyển có điện trở giới hạn dòng, cấp nguồn qua USB từ máy tính xách tay chạy pin; máy đo huyết áp bắp tay tự động làm đối chứng |
| Thời gian tham gia | 2 buổi, buổi 2 cách buổi 1 từ 7 ngày tới 4 tuần, mỗi buổi tối đa 120 phút |
| Kết cục chính | Sai số tuyệt đối trung bình theo người khi ước lượng thay đổi huyết áp tâm thu và tâm trương ở buổi đo sau buổi hiệu chuẩn, so giữa mô hình có PAT và mô hình chỉ dùng PPG |
| Rủi ro chính | Khó chịu do vòng bít, kích ứng da do điện cực, căng thẳng hoặc chóng mặt nhẹ khi làm nghiệm pháp, rủi ro về riêng tư; nhóm đánh giá ban đầu là rủi ro thấp, phân loại cuối cùng do hội đồng quyết định |

## 1. Đặt vấn đề

Thiết bị đeo đo huyết áp không dùng vòng bít thường ước lượng huyết áp từ dạng sóng quang thể tích
(PPG) và từ thời gian truyền mạch. Khi có thêm điện tim, có thể đo khoảng từ đỉnh R của điện tim tới
chân sóng PPG ở cổ tay, gọi là PAT (pulse arrival time). PAT gồm thời kỳ tiền tống máu (PEP) cộng
thời gian truyền mạch (PTT), nên không đồng nhất với PTT, và các quan hệ vật lý dành cho PTT không
được áp trực tiếp lên PAT (Mukkamala và cộng sự, 2015; Payne và cộng sự, 2006).

Các thiết bị này thường cần hiệu chuẩn bằng máy đo có vòng bít cho từng người. Mukkamala và cộng sự
(2021) chỉ ra rằng thiết bị có hiệu chuẩn có thể trông chính xác chỉ vì huyết áp ít thay đổi giữa
các lần đo, nên đề xuất đánh giá thiết bị bằng các can thiệp làm huyết áp thay đổi và luôn so với
cách dự đoán "không đổi so với lúc hiệu chuẩn". Tuyên bố khoa học của Hội Tim mạch Hoa Kỳ (Cohen và
cộng sự, 2025) cũng nhấn mạnh rằng độ chính xác của thiết bị không vòng bít phụ thuộc mạnh vào máy đo
dùng để hiệu chuẩn.

Câu hỏi của nghiên cứu này là: ở người trẻ khỏe mạnh, sau khi hiệu chuẩn bằng các lần đo lúc nghỉ ở
buổi đầu, việc thêm PAT vào mô hình dùng đặc trưng PPG cổ tay có làm giảm sai số ước lượng thay đổi
huyết áp ở buổi đo sau đó ít nhất một tuần hay không. Kết quả âm tính (không giảm, hoặc tương đương
trong một ngưỡng định trước) cũng được báo cáo đầy đủ.

## 2. Mục tiêu nghiên cứu

1. Xây dựng quy trình thu đồng thời tín hiệu PPG cổ tay và điện tim, đồng bộ thời gian, kèm số đo
   huyết áp đối chứng bằng máy đo bắp tay.
2. **Mục tiêu chính:** so sánh sai số ước lượng thay đổi huyết áp tâm thu và tâm trương ở buổi
   sau buổi hiệu chuẩn giữa mô hình chỉ dùng PPG và mô hình PPG có thêm PAT, cùng thuật toán, trên
   cùng tập lần đo, và so với cách dự đoán "không đổi".
3. **Mục tiêu phụ:** so sánh sai số khi đánh giá trong cùng buổi (các lần đo nghiệm pháp ở buổi 1)
   với khi đánh giá ở buổi sau, có chuẩn hóa theo nghiệm pháp, dùng chính các dự đoán của phân
   tích chính; và (thăm dò) dùng chỉ số chất lượng tín hiệu kết hợp độ bất định của mô hình để từ
   chối các lần ước lượng kém tin cậy, so với từ chối ngẫu nhiên ở cùng tỷ lệ giữ lại.

## 3. Thiết kế nghiên cứu

Nghiên cứu thực nghiệm tiến cứu trên người tình nguyện khỏe mạnh, đo lặp lại theo thời gian. Mỗi
người tham gia 2 buổi đo. Buổi 2 cách buổi 1 ít nhất 7 ngày và nằm trong 4 tuần kể từ buổi 1. Giờ
bắt đầu mỗi buổi được ghi lại; hai buổi không bắt buộc cùng khung giờ. Khi hẹn buổi 1, nhóm hẹn
luôn buổi 2.

- **Buổi 1 (hiệu chuẩn):** mốc hiệu chuẩn huyết áp BP₀ là trung bình các lần đo hợp lệ lúc
  nghỉ (M0) của buổi 1; PAT và đặc trưng nền lấy từ tín hiệu của chính các lần đo đó.
- **Buổi 2 (đánh giá):** dùng để đánh giá khả năng theo dõi thay đổi huyết áp sau ít nhất một
  tuần.
- Buổi nào cũng theo cùng một trình tự: nghỉ ổn định, đo lúc nghỉ (M0), rồi thở chậm (M1) và tính
  nhẩm (M2) nếu người tham gia đồng ý với từng nghiệm pháp.

Ở người trẻ khỏe mạnh đo lúc nghỉ, thay đổi huyết áp giữa các buổi thường nhỏ. Vì vậy nghiên cứu dùng
hai nghiệm pháp để mở rộng dải thay đổi, và luôn báo cáo kèm sai số của cách dự đoán "không đổi" cùng
độ lệch chuẩn của thay đổi huyết áp đối chứng.

## 4. Đối tượng nghiên cứu

### 4.1. Quần thể và địa điểm

Người trưởng thành khỏe mạnh 18–35 tuổi, là sinh viên hoặc cán bộ của [tên trường], tự nguyện tham
gia. Mọi buổi đo diễn ra tại [phòng thí nghiệm, địa chỉ].

### 4.2. Tiêu chuẩn lựa chọn

1. Từ 18 đến 35 tuổi, đủ năng lực tự quyết định việc tham gia.
2. Tự nguyện ký phiếu đồng thuận sau khi đã nhận bản thông tin được ít nhất 24 giờ.
3. Tự khai không có bệnh tim mạch đã được chẩn đoán.
4. Có thể ngồi yên trong buổi đo dài tối đa 120 phút, và tham gia 2 buổi đo, buổi 2 cách buổi 1
   từ 7 ngày tới 4 tuần.

### 4.3. Tiêu chuẩn loại trừ

Người tham gia tự khai; nhóm không khám. Chi tiết và phiếu sàng lọc ở Phụ lục 3.

- L1: tăng huyết áp, hạ huyết áp tư thế, loạn nhịp tim hoặc bệnh tim mạch đã được chẩn đoán;
- L2: đang dùng thuốc tác động lên tim mạch hoặc thần kinh giao cảm;
- L3: mang máy tạo nhịp hoặc thiết bị điện tử cấy ghép;
- L4: đang mang thai hoặc nghi có thai;
- L5: vết thương hở, viêm da hoặc kích ứng da ở vị trí đeo thiết bị, dán điện cực hoặc quấn vòng bít
  (hoãn buổi tới khi da lành);
- L6: dị ứng với băng dán, keo y tế, gel điện cực hoặc kim loại (niken);
- L7: không được đo huyết áp ở tay phải;
- L8: có tiền sử ngất, động kinh hoặc khó thở khi gắng sức;
- L9: uống cà phê hoặc trà, hút thuốc hoặc vận động mạnh trong 2 giờ trước buổi đo (hoãn buổi).

Người có chu vi bắp tay phải nằm ngoài các cỡ vòng bít của máy đo thì không đủ điều kiện về kỹ thuật.

### 4.4. Cỡ mẫu

- Đây là cỡ mẫu khả thi cho giai đoạn thử nghiệm nguyên mẫu, chưa dựa trên phân tích lực mẫu. Mức
  tối thiểu là 15 người đạt chuẩn, mục tiêu là ít nhất 25 người đạt chuẩn, và tuyển tối đa 35 người,
  kể cả 2–3 người đo thử. Một người đạt chuẩn khi đã qua sàng lọc, có buổi 1 đạt và buổi 2 đạt;
  một buổi đạt khi có ít nhất 2 lần đo huyết áp hợp lệ tính được cả PAT lẫn đặc trưng PPG. Buổi 2
  phải chỉnh lại dòng LED (mục 6.2 bước 4) không vào phân tích chính nên không được tính là buổi
  đạt.
- Yavarimanesh và cộng sự (2022) ước tính cần 31 người cho một phép so sánh tương tự; với trần 25 người,
  sau khi trừ người đo thử và người bỏ cuộc, nhóm ước tính chỉ còn khoảng 20 người phân tích được. Vì
  vậy trần tuyển là 35 người.
- Số người cần tuyển được chốt sau đợt đo thử, bằng mô phỏng độ nhạy, rồi ghi vào kế hoạch phân tích
  thống kê trước khi thu dữ liệu chính, trong trần 35 người và với ít nhất 15 người đạt chuẩn. Nhóm
  ngừng tuyển khi đủ số người có buổi 1 đạt, hoặc khi hết thời gian thu dữ liệu đã lên lịch (buổi 1
  cuối cùng ngày 29/04/2027), tùy điều nào đến trước. Quyết định dừng hay tuyển tiếp không dựa trên
  kết quả của mô hình.
- Nhóm có một bộ thiết bị và mỗi lúc đo một người: khoảng 7 buổi mỗi tuần, tới 10 buổi mỗi tuần khi
  đủ người trực đã được huấn luyện (mục 9.7).

### 4.5. Tuyển chọn

- Nhóm đăng thông báo tuyển (Phụ lục 7) trên [bảng tin, trang hoặc nhóm thông tin của trường]. Người
  quan tâm tự liên hệ với nhóm; nhóm không mời trực tiếp từng người.
- Giảng viên đang dạy hoặc đánh giá một sinh viên không mời, không tuyển và không lấy đồng thuận của
  sinh viên đó. Việc một người tham gia, từ chối hay rút lui không được báo cho giảng viên hay người
  quản lý của họ.
- Nhóm gửi bản thông tin (Phụ lục 1) cho người quan tâm ít nhất 24 giờ trước buổi 1.
- Buổi 1 cuối cùng là ngày 29/04/2027 và buổi đo cuối cùng là ngày 14/05/2027, để mọi buổi 2 nằm
  trước ngày khóa dữ liệu.

### 4.6. Quy trình lấy đồng thuận

- Ở đầu buổi 1, trước mọi bước đo và trước phiếu sàng lọc, một thành viên nhóm đã được huấn luyện
  [danh sách người lấy đồng thuận] đọc lại thông tin với người tham gia, trả lời câu hỏi và kiểm tra
  người tham gia đã hiểu các điểm chính.
- Người tham gia tự đánh dấu từng mục của phiếu đồng thuận (Phụ lục 2) và ký. Phiếu lập thành hai
  bản; người tham gia giữ một bản cùng bản thông tin. Các nghiệm pháp, việc liên hệ nhắc lịch, việc
  dùng dữ liệu cho nghiên cứu sau và việc chia sẻ dữ liệu đã giả danh hóa qua kho dữ liệu có kiểm
  soát truy cập là các mục tùy chọn.
- Nếu người tham gia không tự đọc được phiếu thì cần một người làm chứng không thuộc nhóm nghiên cứu.
- Ở buổi 2, nhóm hỏi lại người tham gia có muốn tiếp tục không. Nếu có thông tin mới ảnh hưởng
  tới quyết định tham gia, nhóm báo cho người tham gia và hỏi lại sự đồng ý bằng văn bản khi cần.

## 5. Thiết bị nghiên cứu

### 5.1. Thiết bị nguyên mẫu

Thiết bị là nguyên mẫu nghiên cứu học thuật, chỉ dùng cho nghiên cứu, **chưa được cấp phép hay đăng
ký lưu hành như thiết bị y tế**; kết quả của thiết bị không được dùng để chẩn đoán, sàng lọc hay
điều trị, và không được báo cho người tham gia như kết quả sức khỏe. Phạm vi pháp luật áp dụng cho
thiết bị là câu hỏi nhóm gửi hội đồng (mục 9.8).

Thiết bị được lắp từ các module thương mại cắm lên hai bo mạch của nhóm; nhóm không sửa linh kiện
trên các module.

- **Bo cảm biến cổ tay** (40,4 × 31,5 mm, gắn dây velcro): cảm biến quang MAX30101 với đèn LED xanh
  lá, đỏ, hồng ngoại và bộ thu quang; cảm biến chuyển động BMI270. Một giá đỡ cách điện, màu đen,
  che kín các đầu nối và đèn báo nguồn của module cảm biến để chúng không chạm da; chỉ để hở cửa sổ
  quang. Bo nối với bo đế bằng cáp dẹt dài khoảng 20–30 cm.
- **Bo đế đặt trên bàn:** bo vi điều khiển ESP32-S3, mạch đo điện tim MAX30001 với ba điện cực dán
  Ag/AgCl có gel, loại dùng một lần, và một nút bấm đánh dấu thời điểm bắt đầu đo huyết áp.
- **Đầu chuyển cho cáp điện cực:** cáp điện cực cắm vào mạch đo điện tim qua một đầu chuyển có điện
  trở nối tiếp trên từng dây để giới hạn dòng qua người khi có lỗi: dây tham chiếu có ít nhất
  200 kΩ, gồm hai điện trở nối tiếp để một điện trở bị chập vẫn còn đủ giới hạn; giá trị trên hai
  dây đo được chọn sao cho dòng một chiều qua mỗi điện cực ở điều kiện lỗi đơn không quá 50 µA
  [giá trị chốt sau khi người có chuyên môn duyệt bảng phân tích lỗi đơn]. Đầu chuyển nằm trong
  hộp khóa cố định phía mạch đo, nên không thể cắm thẳng cáp điện cực vào mạch. Điện trở từng dây
  được đo trước mỗi buổi và phải nằm trong ngưỡng trên, ngưỡng dưới đã ghi (Phụ lục 5, mục 2).
- **Nguồn điện:** bo đế nối với máy tính xách tay bằng một cáp USB (điện một chiều 5 V). Trong lúc
  người tham gia đeo thiết bị, máy tính chạy bằng pin, đã rút sạc, và không nối với thiết bị nào cắm
  điện lưới; không có đường điện nào nối người tham gia với điện lưới.
- **Ánh sáng LED:** dòng LED được chỉnh cho từng người ở buổi 1 rồi giữ cố định ở buổi 2; dòng
  tối đa là khoảng 25,4 mA cho mỗi nhánh LED, và phần mềm cùng firmware đều từ chối mức cao hơn.
- **An toàn điện và nhiệt:** trước khi dùng trên người, nhóm đo dòng rò trên chính bộ thiết bị dùng
  trong nghiên cứu, kể cả đầu chuyển và cáp điện cực, và so với giới hạn của IEC 60601-1; lập bảng
  phân tích lỗi đơn cho đầu chuyển; và thử nhiệt độ bề mặt bo cổ tay, có lắp giá đỡ, khi chạy liên
  tục 120 phút ở dòng LED tối đa (Phụ lục 5, mục 9). Người có chuyên môn duyệt phương pháp, giới hạn
  và biên bản trước khi thiết bị được dùng trên bất kỳ ai. Biên bản: [số, ngày; Phụ lục 8].

### 5.2. Máy đo huyết áp đối chứng

Số đo huyết áp đối chứng lấy từ máy đo bắp tay tự động (phương pháp dao động) có kết quả thẩm định
độ chính xác đã công bố cho đúng model đó; giữa các model đạt điều kiện này, nhóm ưu tiên model có
độ lặp lại tốt. Model: [tên model, kết quả thẩm định, dải cỡ vòng bít; Phụ lục 10]. Không coi máy
"cùng hãng" là đã được thẩm định. Mọi lần đo của nghiên cứu ở bắp tay phải,
trừ một lần đo tay trái để sàng lọc ở buổi 1.

### 5.3. Bố trí trên người tham gia

<!-- cols: 30,70 -->
| Thành phần | Vị trí |
| --- | --- |
| Bo cảm biến cổ tay | Mặt lưng cổ tay trái, cách mỏm trâm trụ khoảng 1,5–2 cm; vị trí cố định cho mọi người |
| Điện cực 1 (cực dương) | Mặt trong cổ tay trái, không nằm dưới dây đeo |
| Điện cực 2 (cực âm) | Mặt trong cổ tay phải |
| Điện cực 3 (tham chiếu) | Mặt trong cẳng tay trái, cách điện cực 1 khoảng 5 cm về phía khuỷu |
| Vòng bít | Bắp tay phải, ngang tim, đúng cỡ |
| Tư thế | Ngồi tựa lưng, hai bàn chân đặt trên sàn, hai cẳng tay đặt trên bàn có đệm, cổ tay và bắp tay ngang tim |

Vòng bít và bo cảm biến ở hai tay khác nhau, để lúc vòng bít bơm không làm thay đổi tín hiệu PPG.

## 6. Quy trình nghiên cứu

### 6.1. Chuẩn bị

- Người tham gia được dặn không uống cà phê hay trà, không hút thuốc và không vận động mạnh trong 2
  giờ trước buổi đo; nếu chưa kiêng đủ thì buổi đo được hẹn lại.
- Phòng đo yên tĩnh, nhiệt độ ổn định trong khoảng 24–26 °C.
- Trước khi gắn thiết bị, nhóm làm bảng kiểm an toàn (Phụ lục 5, mục 2).

### 6.2. Trình tự một buổi đo

1. *Buổi 1:* lấy đồng thuận (mục 4.6).
2. Phiếu sàng lọc (Phụ lục 3); không đủ điều kiện thì dừng, L5 hoặc L9 thì hẹn lại.
3. *Buổi 1:* ngồi nghỉ ít nhất 5 phút; đo chu vi bắp tay phải để chọn cỡ vòng bít; đo huyết áp tay
   phải rồi tay trái, cách nhau ít nhất 2 phút. Hai lần đo này chỉ để sàng lọc, không phải dữ liệu
   phân tích. Nếu huyết áp tâm thu hai tay chênh nhau từ 10 mmHg trở lên thì không loại, vẫn đo ở tay
   phải, gắn cờ trong dữ liệu và báo số đo cho người tham gia.
4. Gắn thiết bị và kiểm tra tín hiệu. *Buổi 1:* chỉnh dòng LED từng màu để mức tín hiệu nằm trong
   khoảng 30–70% thang đo, tối đa 6 vòng chỉnh, rồi khóa mức đó cho buổi 2. Ở buổi 2, chỉ chỉnh
   lại một lần nếu tín hiệu bị bão hòa quá 5% thời gian; buổi đó được ghi là sai lệch đề cương và
   không vào phân tích chính.
5. Ngồi nghỉ ít nhất 10 phút, rồi đo M0 (hai lần đo lúc nghỉ).
6. M1 (thở chậm), nghỉ ít nhất 5 phút, rồi M2 (tính nhẩm), nếu người tham gia đồng ý và trung bình M0
   của buổi dưới 140/90 mmHg.
7. Tháo thiết bị; người tham gia nghỉ; hỏi lại triệu chứng trước khi ra về (Phụ lục 5, mục 7).

Trong lúc ghi tín hiệu và lúc vòng bít bơm, người tham gia ngồi yên, không nói chuyện và không cử động
tay. Nhóm không chụp ảnh, quay video hay ghi âm. Mọi số liệu ghi vào phiếu ghi buổi đo (Phụ lục 4),
chỉ mang mã nghiên cứu.

### 6.3. Một lượt đo huyết áp và số lần bơm vòng bít

- Mỗi lượt đo gồm: 60 giây ghi tín hiệu trước khi bơm; bấm nút đánh dấu trên bo đế rồi bấm máy đo
  huyết áp (45–60 giây bơm và xả); chép số đo tâm thu, tâm trương và mạch vào phiếu; nghỉ ít nhất 2
  phút trước lượt tiếp theo. Tín hiệu trong lúc vòng bít bơm được gắn cờ và không dùng làm đầu vào
  chính.
- Mỗi lần đo huyết áp chỉ tạo **một** nhãn huyết áp; nhiều đoạn tín hiệu của cùng một lần đo không
  được tính như nhiều nhãn độc lập.
- Theo kế hoạch, M0 đo hai lần, M1 và M2 mỗi nghiệm pháp một lần: 4 lần mỗi buổi. Trần là 6 lần mỗi
  buổi, trong đó tối đa 2 lần đo lại khi máy xả bình thường nhưng không ra kết quả hoặc khi lượt đo bị
  cử động. Buổi chỉ có M0 thì tối đa 4 lần. Buổi 1 có thêm 2 lần đo hai tay khi sàng lọc: theo kế
  hoạch 6 lần, trần 8 lần (6 lần nếu chỉ có M0). Nếu máy bơm không xả, bơm quá mức hoặc báo lỗi phần
  cứng thì dừng buổi đo, không đo lại.
- Trần thời lượng là 120 phút mỗi buổi; ước tính một buổi đủ các bước khoảng 60–80 phút.

### 6.4. Các nghiệm pháp

<!-- cols: 12,44,44 -->
| Mã | Cách làm | Căn cứ và rủi ro |
| --- | --- | --- |
| M0 – Nghỉ | Ngồi nghỉ ít nhất 10 phút, rồi đo huyết áp hai lần, cách nhau ít nhất 2 phút | Mốc hiệu chuẩn và so sánh. Rủi ro tối thiểu |
| M1 – Thở chậm | 15 phút thở theo âm thanh hướng dẫn từ máy tính, 6 nhịp mỗi phút (hít vào 4 giây, thở ra 6 giây), độ sâu thoải mái, không nín thở; đo huyết áp một lần ở phút cuối | Thở chậm có hướng dẫn 15 phút làm huyết áp tâm thu giảm khoảng 3 mmHg ở người trẻ có huyết áp bình thường (Adler và cộng sự, 2019). Rủi ro: chóng mặt nhẹ, tê đầu ngón tay |
| M2 – Tính nhẩm | Người vận hành đọc một số có bốn chữ số; người tham gia trừ liên tiếp 13 trong đầu, không nói; sau 90 giây thì đo huyết áp; người tham gia nhẩm tiếp tới khi vòng bít xả xong rồi nói số cuối cùng; tổng khoảng 3 phút; không chấm điểm, không báo đúng sai | Dạng bài trừ liên tiếp 13 theo Hove và cộng sự (2024); phản ứng huyết áp với tính nhẩm đã được ghi nhận (Carroll và cộng sự, 2012; Jern và cộng sự, 1991). Rủi ro: căng thẳng, lo âu |

- Thứ tự cố định: M0 → M1 → nghỉ ít nhất 5 phút → M2 → nghỉ. Thở chậm làm trước để căng thẳng do
  tính nhẩm không kéo sang lúc thở chậm.
- Nếu trung bình M0 của buổi có huyết áp tâm thu từ 140 mmHg hoặc tâm trương từ 90 mmHg trở lên thì
  không làm M1, M2. Nếu có lần đo nào từ 180/110 mmHg trở lên thì dừng buổi (Phụ lục 5, mục 6).
- Người tham gia có thể từ chối riêng từng nghiệm pháp. Nhóm không tăng cường độ hay thời lượng của
  nghiệm pháp vượt quá bản được hội đồng chấp thuận.
- Số bắt đầu và số người tham gia nói ra ở M2 được ghi lại để kiểm mức tham gia, không dùng để loại
  lượt đo.

### 6.5. Đo thử

Sau khi có chấp thuận, 2–3 người đầu tiên tham gia đợt đo thử theo đúng quy trình này, cũng 2 buổi
cách nhau ít nhất 7 ngày như người tham gia khác, và nhận cùng bản thông tin. Dữ liệu đo thử dùng để
kiểm tra quy trình, chốt các lựa chọn xử lý tín hiệu, đo độ lặp lại của máy đo huyết áp và kiểm tra
dải thay đổi huyết áp mà hai nghiệm pháp tạo ra. Tiêu chí kiểm tra dải thay đổi đã được chốt trước:
trung vị qua người của thay đổi huyết áp tâm thu (có dấu) ở lần đo tính nhẩm so với trung bình lúc
nghỉ cùng buổi đạt ít nhất 10 mmHg. Đây là mức báo động nội bộ, chọn từ mô phỏng độ nhạy, không phải
tiêu chí an toàn. Nếu thấp hơn mức này, nhóm báo giảng viên hướng dẫn và rà lại đề cương trước khi
thu dữ liệu chính; mọi thay đổi (ví dụ thêm nghiệm pháp) chỉ áp dụng sau khi hội đồng chấp thuận sửa
đổi, và nhóm không tăng cường độ hay thời lượng nghiệm pháp để đạt tiêu chí. Người đo thử được tính
vào trần 35 người nhưng không vào phân tích kết cục chính.

## 7. Dữ liệu thu thập

<!-- cols: 30,70 -->
| Nhóm | Dữ liệu |
| --- | --- |
| Nhân khẩu học | Tuổi (năm), giới tính, tay thuận, chu vi bắp tay phải |
| Sàng lọc | Câu trả lời có/không cho L1–L9; huyết áp hai tay ở buổi 1 |
| Tín hiệu | PPG ba bước sóng và chuyển động ở cổ tay trái; điện tim một đạo trình (giữa hai cổ tay); mốc thời gian của thiết bị |
| Đối chứng | Huyết áp tâm thu, tâm trương và mạch của máy đo bắp tay; thời điểm và nghiệm pháp của từng lần đo |
| Kỹ thuật | Cấu hình thiết bị, mức dòng LED đã khóa, vị trí và nấc dây đeo, nhiệt độ phòng, giờ bắt đầu buổi |
| An toàn | Nhật ký sự cố và lý do dừng; nhật ký rút lui (chỉ mã); điện trở từng dây của đầu chuyển điện cực đo trước buổi |

Nhóm không thu họ tên vào dữ liệu nghiên cứu, không thu mã sinh viên, số căn cước, ngày sinh, ảnh,
video hay ghi âm. Quản lý dữ liệu theo Phụ lục 6. Chỉ dữ liệu của người đồng ý ở mục 11 của phiếu
đồng thuận mới có thể được chia sẻ, ở dạng đã giả danh hóa và rút gọn, qua kho dữ liệu có kiểm soát
truy cập (Phụ lục 6, mục 9).

## 8. Phân tích số liệu

### 8.1. Kết cục chính

- Với mỗi lần đo huyết áp hợp lệ ở buổi 2 (cả M0, M1 và M2), thay đổi huyết áp đối chứng
  ΔBP = BP − BP₀, tính riêng cho huyết áp tâm thu và tâm trương.
- Các lần đo nghiệm pháp ở buổi 1 không dùng để hiệu chuẩn và không vào tập đánh giá kết cục chính.
- Sai số được báo gộp và theo từng nghiệm pháp. Phân tích phụ định trước chỉ dùng các lần đo lúc nghỉ
  ở buổi 2.

### 8.2. Mô hình so sánh

Cách dự đoán "không đổi" (dự đoán thay đổi bằng 0); hai cách dự đoán không dùng tín hiệu, chỉ dựa
vào nghiệm pháp đang làm (trung bình thay đổi của từng nghiệm pháp, và một độ lệch hằng số), để biết
mô hình có theo được thay đổi của từng người hay chỉ nhận ra nghiệm pháp; mô hình chỉ dùng đặc trưng
PPG; mô hình PPG có thêm PAT (mô hình chính); mô hình chỉ dùng PAT; mô hình có thêm nhịp tim và biến
thiên nhịp tim từ điện tim (phân tích phụ). Hai mô hình của phép so sánh chính dùng cùng thuật toán và được đánh giá trên cùng
tập lần đo tính được cả PAT lẫn đặc trưng PPG. PAT được tính từ đỉnh R tới chân sóng PPG của cùng nhịp.

### 8.3. Chia dữ liệu

- Đánh giá chéo bỏ từng người, có vòng lặp lồng: mỗi lượt để riêng toàn bộ dữ liệu của một người làm
  dữ liệu kiểm tra và huấn luyện trên những người còn lại; siêu tham số, nếu có, được chọn ở vòng trong
  chỉ trên những người huấn luyện.
- Cửa sổ tín hiệu, cách xác định đỉnh R và chân sóng PPG, ngưỡng chất lượng tín hiệu và bộ đặc trưng
  được chốt trên dữ liệu đo thử trước khi chạy đánh giá cuối, không chọn theo sai số. Đánh giá cuối
  chạy đúng một lần, sau khi các lựa chọn đã được khóa.
- Không trộn ngẫu nhiên dữ liệu giữa các buổi hay giữa các người.

### 8.4. Chỉ số và thống kê

- Sai số tuyệt đối trung bình (MAE), sai số trung bình và độ lệch chuẩn, tính riêng cho huyết áp tâm
  thu và tâm trương, tổng hợp đều theo người.
- Hiệu ứng chính: chênh lệch MAE theo từng người giữa mô hình PPG có PAT và mô hình chỉ dùng PPG, báo
  trung bình và khoảng tin cậy theo người (không theo lần đo hay đoạn tín hiệu). Khoảng tin cậy chính
  lấy cận rộng hơn ở mỗi phía của hai khoảng: bootstrap-t lấy mẫu lại theo người (10 000 lượt, số
  khởi tạo cố định) và khoảng Student t; các kiểu khoảng khác được báo làm phân tích độ nhạy. Kiểm
  định Wilcoxon cặp theo người là phân tích hỗ trợ. So sánh với cách dự đoán "không đổi" dùng cùng
  cách tính.
- Chỉ kết luận "thêm PAT làm giảm sai số" cho một đầu ra (tâm thu hoặc tâm trương) khi khoảng tin
  cậy của chênh lệch MAE so với **cả** mô hình chỉ dùng PPG **lẫn** cách dự đoán "không đổi" đều nằm
  hoàn toàn dưới 0. Đa kiểm định giữa tâm thu và tâm trương theo thủ tục Holm: xét cả hai đầu ra với
  khoảng tin cậy 97,5%; nếu chỉ một đầu ra đạt thì xét đầu ra còn lại với khoảng 95%. Kết quả không
  đạt được báo là tương đương trong phạm vi mức hiệu ứng định trước, hoặc chưa kết luận, không viết
  là "PAT không giúp".
- Mức hiệu ứng nhỏ nhất đáng quan tâm bằng một nửa độ lệch chuẩn lặp lại của máy đo huyết áp, ước
  lượng từ hai lần đo lúc nghỉ liền nhau ở đợt đo thử, không nhỏ hơn 1 mmHg và không lớn hơn 2 mmHg
  (tâm thu) hoặc 1,5 mmHg (tâm trương). Giá trị được tính sau đợt đo thử theo quy tắc này và ghi vào
  kế hoạch phân tích trước buổi thu dữ liệu chính đầu tiên.
- Kế hoạch phân tích thống kê được khóa bằng một bản có ghi ngày trước buổi đo thử đầu tiên; sau đo
  thử chỉ điền các giá trị đã định là "chốt sau đo thử" (mức hiệu ứng, số người) theo quy tắc đã
  khóa.
- Luôn báo cáo kèm độ lệch chuẩn của thay đổi huyết áp đối chứng và tỷ lệ lần đo có thay đổi trên 5
  mmHg.

### 8.5. Dữ liệu thiếu và lượt đo bị dừng

- Lượt đo không có số đo huyết áp thì bị loại; không điền giá trị huyết áp thay thế.
- Lượt mất điện tim nhưng PPG đạt bị loại khỏi phép so sánh chính để hai mô hình được đánh giá trên
  cùng tập, và vẫn dùng cho phân tích phụ chỉ có PPG; tỷ lệ mất điện tim được báo theo người.
- Người chỉ có buổi 1 không đạt chuẩn và không vào phân tích kết cục chính; số người và lý do được
  báo cáo. Không điền dữ liệu thiếu bằng mô hình.
- Lượt đã có số đo huyết áp đầy đủ được giữ, kể cả khi buổi đo bị dừng sau đó vì an toàn; số lượt bị
  dừng được báo cáo, kèm phân tích độ nhạy loại các lượt này.
- Phân tích chính không loại lượt đo theo chỉ số chất lượng tín hiệu; lọc theo chất lượng tín hiệu là
  phân tích phụ đăng ký trước.

## 9. Đạo đức trong nghiên cứu

Nghiên cứu được thực hiện theo các nguyên tắc của Tuyên bố Helsinki và hướng dẫn CIOMS 2016, theo
Thông tư 43/2024/TT-BYT về hội đồng đạo đức trong nghiên cứu y sinh học, và theo Luật Bảo vệ dữ liệu
cá nhân số 91/2025/QH15 cùng Nghị định 356/2025/NĐ-CP. Chỉ bắt đầu tuyển và đo trên người sau khi có
văn bản chấp thuận của hội đồng.

### 9.1. Nguy cơ và biện pháp giảm thiểu

<!-- cols: 30,70 -->
| Nguy cơ | Biện pháp |
| --- | --- |
| Khó chịu khi vòng bít bơm | Trần số lần bơm mỗi buổi, nghỉ ít nhất 2 phút giữa hai lần, vòng bít đúng cỡ |
| Kích ứng da do điện cực | Loại người dị ứng băng dán, gel hoặc kim loại; điện cực mới mỗi buổi; dừng khi da đỏ, ngứa, rát; dặn liên hệ nếu phản ứng kéo dài |
| Điện giật, dòng rò | Nguồn một chiều 5 V từ máy tính chạy pin, không nối điện lưới; điện trở giới hạn dòng trên từng dây điện cực, đầu chuyển trong hộp khóa; đo dòng rò theo IEC 60601-1 và phân tích lỗi đơn trước khi dùng, có người có chuyên môn duyệt; bảng kiểm và đo điện trở đầu chuyển trước mỗi buổi |
| Nóng ở bo cổ tay | Trần dòng LED; thử nhiệt 120 phút với giá đỡ thật trước khi dùng; dừng khi bo nóng bất thường |
| Đầu nối hay linh kiện chạm da | Giá đỡ cách điện che kín đầu nối và đèn báo của module cảm biến; kiểm giá đỡ trước mỗi buổi |
| Chóng mặt, tê tay khi thở chậm; căng thẳng khi tính nhẩm | Hướng dẫn thở nhẹ nhàng, không nín thở; người theo dõi suốt nghiệm pháp; quy tắc dừng nghiệm pháp và dừng buổi; nghỉ ít nhất 5 phút giữa hai nghiệm pháp |
| Huyết áp cao phát hiện trong buổi đo | Ngưỡng 140/90 (không làm nghiệm pháp) và 180/110 mmHg (dừng buổi); báo số đo, khuyên đi khám; từ 180/110 kèm triệu chứng thì gọi 115, không triệu chứng thì gọi đầu mối y tế ngay trong buổi (Phụ lục 5, mục 6) |
| Lộ thông tin cá nhân | Giả danh hóa, tách phiếu có họ tên khỏi dữ liệu, mã hóa thiết bị lưu trữ, giới hạn người truy cập (Phụ lục 6) |
| Áp lực phải tham gia với sinh viên | Tuyển qua thông báo; giảng viên không tuyển sinh viên mình dạy; quyết định của người tham gia không được báo cho giảng viên (mục 4.5) |

Nhóm đánh giá ban đầu đây là nghiên cứu có rủi ro thấp; phân loại rủi ro và hình thức xét duyệt do
hội đồng quyết định. Quy trình an toàn và quy tắc dừng chi tiết ở Phụ lục 5.

### 9.2. Lợi ích

Người tham gia không có lợi ích sức khỏe trực tiếp. Nghiên cứu cung cấp hiểu biết về khả năng theo
dõi thay đổi huyết áp bằng thiết bị đeo ở cổ tay.

### 9.3. Tự nguyện và rút lui

Người tham gia có thể từ chối, dừng một nghiệm pháp, dừng buổi đo hoặc rút lui bất cứ lúc nào mà không
cần nêu lý do. Khi rút lui, người tham gia chọn xóa hay giữ dữ liệu đã thu. Yêu cầu xóa đưa ra trước
ngày khóa dữ liệu 21/05/2027 được thực hiện trong 20 ngày; ngày này được ghi trong bản thông tin từ
khi tuyển. Dữ liệu đã được chia sẻ qua kho dữ liệu (chỉ với người đồng ý ở mục 11 của phiếu đồng
thuận) thì không thu hồi được; việc chia sẻ chỉ làm sau khi đề tài kết thúc. Sau ngày khóa, nhóm đề nghị giữ dữ liệu chỉ cho các phân tích đã định trước nếu đơn
vị chủ trì xác nhận có căn cứ; nếu không có căn cứ thì nhóm xóa và chạy lại các phân tích không có dữ
liệu của người đó (Phụ lục 6, mục 6). Các trường hợp nhóm dừng sự tham gia của một người được nêu ở
mục 9 của bản thông tin.

### 9.4. Bảo mật dữ liệu

Dữ liệu nghiên cứu chỉ mang mã; bảng liên kết danh tính được mã hóa và do người quản lý dữ liệu giữ;
phiếu đồng thuận và phiếu sàng lọc cất riêng trong tủ có khóa; chỉ công bố số liệu tổng hợp. Thời hạn
lưu theo quy định của trường, nếu không có thì 03 năm. Với người đồng ý ở mục 11 của phiếu đồng
thuận, một bản rút gọn đã giả danh hóa (mã mới, tuổi theo nhóm 5 năm, không có ngày giờ thật hay ghi
chú tự do) có thể được đưa lên [kho dữ liệu có kiểm soát truy cập]; người nhận phải ký thỏa thuận
sử dụng dữ liệu, cam kết không tìm cách nhận diện người tham gia và không chia sẻ tiếp. Chi tiết ở
Phụ lục 6.

### 9.5. Phát hiện ngoài ý muốn

Nhóm không chẩn đoán và không tư vấn y khoa. Số đo huyết áp vượt ngưỡng an toàn và chênh lệch huyết áp
hai tay từ 10 mmHg được báo cho người tham gia kèm lời khuyên đi khám tại [cơ sở y tế/đầu mối y tế].
Tín hiệu điện tim không được bác sĩ đọc để chẩn đoán, và điều này được nói rõ trong bản thông tin.

### 9.6. Chi phí, bồi dưỡng và xử trí khi có tổn hại

Người tham gia không phải trả chi phí nào. Bồi dưỡng: [mức, cách tính theo số buổi đã tham gia]. Khi
có tổn hại do nghiên cứu, nhóm sơ cứu ban đầu và đưa hoặc hướng dẫn người tham gia tới
[cơ sở y tế/đầu mối y tế]; chi phí do [đơn vị chi trả] chịu. Bảo hiểm: [có hoặc không].

### 9.7. Người trực và báo cáo sự cố

Mỗi buổi đo có ít nhất hai thành viên nhóm đã được huấn luyện, trong đó ít nhất một người đã học sơ cứu
cơ bản. Ngoài các thành viên nhóm, nhóm tuyển và huấn luyện thêm 2 người trực theo quy trình này; chỉ
người có tên trong danh sách người trực [danh sách] mới được vận hành buổi đo, và quyền truy cập dữ
liệu của họ theo Phụ lục 6. Sự cố được ghi vào nhật ký và báo cho giảng viên hướng dẫn và hội đồng theo quy định
[thời hạn báo cáo của hội đồng]. Mọi thay đổi đề cương, bản thông tin hay phiếu đồng thuận chỉ áp dụng
sau khi hội đồng chấp thuận sửa đổi.

### 9.8. Đề nghị hội đồng cho ý kiến

1. **Phạm vi pháp luật áp dụng cho thiết bị.** Thiết bị là nguyên mẫu chỉ dùng cho nghiên cứu,
   không đăng ký lưu hành, không được dùng để chẩn đoán, theo dõi bệnh hay điều trị, và kết quả của
   thiết bị không được báo cho người tham gia. Nhóm đề nghị hội đồng xác định phạm vi pháp luật áp
   dụng, trong đó có việc nghiên cứu này có thuộc diện thử nghiệm lâm sàng trang thiết bị y tế hay
   không, và các thủ tục nhóm cần thực hiện; nếu việc này ngoài thẩm quyền của hội đồng, xin hội
   đồng hướng dẫn cơ quan có thẩm quyền.
2. [Mục tùy chọn, nhóm quyết trước khi nộp có đưa vào không.] Trước đợt đo thử, nhóm muốn thử kỹ thuật
   thiết bị trên chính thành viên nhóm (đeo thiết bị, đo huyết áp, thử hai nghiệm pháp) để kiểm tra
   dây đeo, cáp, điện cực và trình tự buổi đo. Số liệu thử không dùng cho bất kỳ phân tích hay công
   bố nào, và chỉ làm sau khi đo dòng rò đạt. Nhóm đề nghị hội đồng cho biết hoạt động này có cần
   chấp thuận riêng hay không.

## 10. Kế hoạch thực hiện

<!-- cols: 45,55 -->
| Công việc | Thời gian dự kiến |
| --- | --- |
| Nộp hồ sơ và chờ chấp thuận | Nộp [ngày nộp]; chờ chấp thuận [thời gian xét của hội đồng] |
| Đo dòng rò, phân tích lỗi đơn của đầu chuyển, thử nhiệt, chọn máy đo huyết áp | Trước khi nộp hoặc trước buổi đo đầu tiên [theo yêu cầu của hội đồng] |
| Khóa kế hoạch phân tích thống kê | Trước buổi đo thử đầu tiên |
| Đo thử (2–3 người, mỗi người 2 buổi) | Khoảng 2 tuần sau khi có chấp thuận; buổi 2 của người đo thử có thể chạy song song tuần thu dữ liệu chính đầu tiên |
| Chốt mức hiệu ứng nhỏ nhất và số người cần tuyển | Sau đo thử, trước buổi thu dữ liệu chính đầu tiên |
| Thu dữ liệu chính | Sau đo thử đến 14/05/2027; buổi 1 cuối cùng ngày 29/04/2027 |
| Khóa dữ liệu | 21/05/2027 |
| Phân tích, viết báo cáo và bài báo | 22/05/2027 đến hết tháng 7/2027 |

## 11. Nhóm nghiên cứu

<!-- cols: 32,68 -->
| Thành viên | Vai trò |
| --- | --- |
| [Chủ nhiệm đề tài] | Chịu trách nhiệm chung |
| [Giảng viên hướng dẫn] | Hướng dẫn khoa học, giám sát tuân thủ đề cương |
| Nguyễn Đức Huy | Đề cương, hồ sơ đạo đức, xử lý tín hiệu, PAT, thống kê; người quản lý dữ liệu [chờ xác nhận] |
| [Họ tên] | Phần mềm, quy trình dữ liệu, mô hình; người quản lý dữ liệu dự phòng [chờ xác nhận] |
| [Họ tên] | Phần cứng, firmware, an toàn thiết bị (đo dòng rò, thử nhiệt) |
| [Người trực, người lấy đồng thuận, gồm 2 người trực được tuyển thêm] | Vận hành buổi đo, lấy đồng thuận, ghi phiếu |

## 12. Hạn chế của nghiên cứu

- Chỉ có hai nghiệm pháp làm huyết áp thay đổi, ít hơn mức ít nhất ba can thiệp mà Mukkamala và cộng
  sự (2021) đề xuất; dải thay đổi huyết áp có thể hẹp, làm phép so sánh kém nhạy.
- PAT gồm cả PEP, nên căng thẳng khi tính nhẩm có thể làm PAT thay đổi mà huyết áp không đổi.
- Điện tim một đạo trình giữa hai cổ tay có biên độ nhỏ và dễ nhiễu khi tay cử động.
- Số đo huyết áp đối chứng không đồng thời với tín hiệu (tín hiệu lấy ngay trước khi vòng bít bơm), và
  sai số của máy đo truyền vào cả nhãn lẫn mốc hiệu chuẩn.
- Mỗi người chỉ có một buổi đánh giá, cách buổi hiệu chuẩn từ 7 ngày tới 4 tuần; kết quả chỉ nói về
  sai số ở khoảng cách này, không suy ra thời hạn của hiệu chuẩn.
- Cỡ mẫu nhỏ, người trẻ khỏe mạnh; kết quả không suy ra cho người lớn tuổi, người bệnh hay các tình
  huống làm huyết áp thay đổi mạnh.

## 13. Tài liệu tham khảo

1. Mukkamala R, et al. Toward ubiquitous blood pressure monitoring via pulse transit time: theory and
   practice. IEEE Trans Biomed Eng. 2015;62(8):1879–1901. doi:10.1109/TBME.2015.2441951
2. Payne RA, et al. Pulse transit time measured from the ECG: an unreliable marker of beat-to-beat
   blood pressure. J Appl Physiol. 2006;100(1):136–141. doi:10.1152/japplphysiol.00657.2005
3. Mukkamala R, et al. Evaluation of the accuracy of cuffless blood pressure measurement devices:
   challenges and proposals. Hypertension. 2021. doi:10.1161/HYPERTENSIONAHA.121.17747
4. Cohen JB, et al. Cuffless devices for the measurement of blood pressure: a scientific statement
   from the American Heart Association. Hypertension. 2025. doi:10.1161/HYP.0000000000000254
5. Yavarimanesh M, et al. Assessment of calibration models for cuff-less blood pressure measurement
   after one year of aging. IEEE Trans Biomed Eng. 2022;69(6):2087–2093.
   doi:10.1109/TBME.2021.3136492
6. Adler TE, et al. Device-guided slow breathing reduces blood pressure and sympathetic activity in
   young normotensive individuals of both sexes. J Appl Physiol. 2019.
   doi:10.1152/japplphysiol.00442.2019
7. Hove C, et al. A prototype photoplethysmography-based cuffless device shows promising results in
   tracking changes in blood pressure. Front Med Technol. 2024. doi:10.3389/fmedt.2024.1464473
8. Carroll D, et al. Increased blood pressure reactions to acute mental stress are associated with
   16-year cardiovascular disease mortality. Psychophysiology. 2012.
   doi:10.1111/j.1469-8986.2012.01463.x
9. Jern S, et al. Short-term reproducibility of a mental arithmetic stress test. Clin Sci. 1991.
   doi:10.1042/cs0810593
10. Mancia G, et al. 2023 ESH Guidelines for the management of arterial hypertension. J Hypertens.
    2023. doi:10.1097/HJH.0000000000003480
11. McEvoy JW, et al. 2024 ESC Guidelines for the management of elevated blood pressure and
    hypertension. Eur Heart J. 2024. doi:10.1093/eurheartj/ehae178
12. IEC 60601-1: Medical electrical equipment – Part 1: General requirements for basic safety and
    essential performance.
13. World Medical Association. Declaration of Helsinki: Ethical principles for medical research
    involving human participants. 2024.
14. CIOMS. International ethical guidelines for health-related research involving humans. Geneva;
    2016.
15. Bộ Y tế. Thông tư 43/2024/TT-BYT quy định việc thành lập, tổ chức và hoạt động của hội đồng đạo
    đức trong nghiên cứu y sinh học. Ngày 12/12/2024.
16. Quốc hội. Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15. Ngày 26/06/2025.
17. Chính phủ. Nghị định 356/2025/NĐ-CP quy định chi tiết Luật Bảo vệ dữ liệu cá nhân. Ngày
    31/12/2025.

## Phụ lục

1. Bản thông tin dành cho người tham gia.
2. Phiếu đồng thuận tham gia nghiên cứu.
3. Tiêu chuẩn lựa chọn, loại trừ và phiếu sàng lọc.
4. Phiếu ghi buổi đo.
5. Quy trình an toàn buổi đo và quy tắc dừng.
6. Kế hoạch quản lý dữ liệu và bảo vệ dữ liệu cá nhân.
7. Thông báo tuyển người tham gia.
8. Biên bản đo dòng rò, phân tích lỗi đơn của đầu chuyển điện cực và thử nhiệt [chờ đo].
9. Lý lịch khoa học và chứng nhận đào tạo đạo đức nghiên cứu của nghiên cứu viên [chờ].
10. Tài liệu của máy đo huyết áp đối chứng (kết quả thẩm định độ chính xác) [chờ chọn model].
