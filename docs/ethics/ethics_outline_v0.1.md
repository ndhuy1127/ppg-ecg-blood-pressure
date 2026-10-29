# Khung Đạo đức Nghiên cứu (Ethics Outline) - Phiên bản v0.1

> **Phiên bản:** v0.1
> **Người biên soạn:** Nguyễn Đức Huy
> **Vai trò:** Xử lý tín hiệu, PAT, thống kê, xây dựng protocol và hồ sơ đạo đức
> **Ngày cập nhật:** 2026-09-22
> **Lưu ý:** CHƯA PHẢI HỒ SƠ ĐẠO ĐỨC ĐÃ ĐƯỢC PHÊ DUYỆT CHÍNH THỨC.

> [!NOTE]
> **Cập nhật 2026-10-22 (Huy):** nội dung để nộp nằm trong 5 file bản nháp v0.1:
> [phiếu thông tin](participant_information_sheet_v0.1.md),
> [phiếu đồng thuận](consent_form_v0.1.md),
> [chọn/loại](eligibility_screening_v0.1.md),
> [an toàn và quy tắc dừng](session_safety_stopping_v0.1.md),
> [quản lý dữ liệu](data_management_plan_v0.1.md).
> Outline này giữ làm lịch sử; khi khác nhau thì theo 5 file đó. Các chỗ dưới đây
> đã cũ hoặc mâu thuẫn, **không dùng khi nộp**:
>
> | Mục trong outline | Nội dung đã cũ | Theo bản mới |
> | --- | --- | --- |
> | 3, bước 1 | "chạm ngón tay vào điện cực ECG" | V1 dùng điện cực dán, không cần chạm chủ động (protocol v0.2 mục 5.1) |
> | 3, bước 1 | Mỗi phiên khoảng 20–30 phút | Phiếu thông tin: tối đa 120 phút mỗi buổi, tối đa 3 buổi (2026-10-29) |
> | 3, bước 4 | Rút lui thì xóa vĩnh viễn **toàn bộ** dữ liệu | Người rút lui chọn xóa hay giữ; xóa được nếu yêu cầu trước mốc khóa dữ liệu ở G4 (phiếu thông tin mục 6, kế hoạch quản lý dữ liệu mục 4; 2026-10-29) |
> | 4, đoạn đầu | Tự phân loại "rủi ro tối thiểu (minimal risk)" | Phân loại rủi ro do hội đồng quyết định; câu trong outline chỉ là nhận định ban đầu của nhóm |
> | 4.1 | Quy tắc pin, cấm nối máy tính | V1: USB tới laptop chạy pin, rút sạc (ghi chú trong 4.1) |
> | 4.2 | Vỏ in 3D; vật liệu điện cực chưa chốt | V1: bo cổ tay gắn velcro, không có vỏ in 3D; điện cực Ag/AgCl dán là phương án chính |
> | 4.2 | LED < 15 mW | Chưa có nguồn (ghi chú trong 4.2) |
> | 4.3 | Nghỉ 2–3 phút giữa hai lần cuff | Phiếu thông tin và protocol: ít nhất 2 phút |
> | 4.4, ý 4 | Ngưỡng SBP > 180 / DBP > 110 mmHg | Đề xuất ≥ 180/110 dừng buổi, M0 ≥ 140/90 không làm nghiệm pháp; chờ thầy/hội đồng ([quy tắc dừng](session_safety_stopping_v0.1.md) mục 3) |
> | 5, thời hạn lưu | Tối đa 03 năm sau khi công bố | Theo quy định của trường; không có thì 03 năm kể từ mốc muộn hơn giữa kết thúc đề tài và công bố ([kế hoạch quản lý dữ liệu](data_management_plan_v0.1.md) mục 5) |

---

## 1. Tuyên bố bản chất văn bản và Cảnh báo quan trọng

> [!WARNING]
> **Tuyên bố quan trọng về phê duyệt đạo đức y sinh:**
> 1. Tài liệu này là **khung phác thảo sơ bộ (outline)** các nguyên tắc bảo vệ quyền lợi con người và an toàn dữ liệu, phục vụ công tác chuẩn bị hồ sơ xin cấp phép của nhóm nghiên cứu. Đây **hoàn toàn chưa phải là Giấy chứng nhận chấp thuận đạo đức (IRB/Ethics Approval)** được cấp bởi Hội đồng Đạo đức trong nghiên cứu y sinh học có thẩm quyền.
> 2. **Tuyệt đối không được phép tiến hành tuyển tình nguyện viên hoặc thu thập dữ liệu sinh học trên người trong Tuần 1.** Bất kỳ hoạt động đo đạc thực nghiệm nào trên con người chỉ được thực hiện sau khi hồ sơ đạo đức chính thức được hoàn thiện, thẩm định và phê duyệt bằng văn bản.
> 3. Tài liệu phải được đối chiếu với [chính sách dữ liệu và bảo mật](../DATA_POLICY.md) trước khi nộp duyệt; outline không phải bằng chứng đã triển khai các biện pháp bảo vệ.

---

## 2. Mục đích nghiên cứu và Phạm vi áp dụng

- **Mục đích khoa học:** Dự án là nghiên cứu học thuật thuần túy trong lĩnh vực kỹ thuật y sinh, nhằm phát triển và đánh giá tính khả thi kỹ thuật của một nguyên mẫu vòng đeo tay thu nhận đồng bộ tín hiệu quang học (PPG) và điện sinh lý tim (ECG) để ước lượng biến thiên huyết áp.
- **Phạm vi phi y tế:** Thiết bị nguyên mẫu, thuật toán và toàn bộ dữ liệu tạo ra trong khuôn khổ dự án **chỉ phục vụ mục đích nghiên cứu công nghệ**. Thiết bị này:
  - **KHÔNG PHẢI LÀ THIẾT BỊ Y TẾ.**
  - **KHÔNG ĐƯỢC PHÉP SỬ DỤNG** để chẩn đoán, phát hiện sớm, theo dõi bệnh lý tim mạch hay đưa ra bất kỳ chỉ định điều trị y khoa nào.
  - Người thực hiện nghiên cứu không được phép đưa ra bất kỳ kết luận hay tư vấn y khoa nào cho người tham gia dựa trên các chỉ số hiển thị của nguyên mẫu.

---

## 3. Quy trình giải thích và Lấy phiếu đồng thuận (Informed Consent)

Trước khi tham gia bất kỳ phiên đo thử nghiệm nào (khi được phép ở các giai đoạn sau), mỗi tình nguyện viên phải trải qua quy trình lấy đồng thuận minh bạch gồm các bước:

1. **Cung cấp bản thông tin nghiên cứu (Participant Information Sheet):**
   - Giải thích rõ ràng bằng ngôn ngữ phổ thông, dễ hiểu về mục đích của đề tài.
   - Mô tả chi tiết các bước mà người tham gia sẽ thực hiện: ngồi nghỉ, đeo thiết bị ở cổ tay, chạm ngón tay vào điện cực ECG, đo huyết áp đối chứng bằng vòng bít bắp tay.
   - Nêu rõ thời lượng dự kiến của mỗi phiên đo (khoảng 20–30 phút).
2. **Thời gian cân nhắc và giải đáp thắc mắc:**
   - Người tham gia có ít nhất 24 giờ để đọc tài liệu, thảo luận với người thân và đặt câu hỏi cho nhóm nghiên cứu trước khi quyết định ký phiếu đồng thuận.
3. **Ký phiếu đồng thuận tự nguyện (Informed Consent Form):**
   - Phiếu đồng thuận được lập thành 02 bản có chữ ký của người tham gia và nghiên cứu viên chính (mỗi bên giữ 01 bản).
   - Bản cứng phiếu đồng thuận có chữ ký được lưu trữ an toàn trong tủ hồ sơ có khóa của phòng thí nghiệm, tách biệt hoàn toàn khỏi dữ liệu số hóa.
4. **Quyền từ chối và rút lui vô điều kiện:**
   - Việc tham gia là hoàn toàn tự nguyện. Người tham gia có quyền từ chối tham gia hoặc **rút lui khỏi nghiên cứu tại bất kỳ thời điểm nào** trong quá trình đo mà không cần nêu lý do.
   - Việc rút lui hoàn toàn không gây ra bất kỳ ảnh hưởng, thiệt thòi hay phân biệt đối xử nào (đặc biệt đối với đối tượng là sinh viên).
   - Khi người tham gia yêu cầu rút lui, toàn bộ dữ liệu tín hiệu đã ghi nhận của người đó sẽ bị xóa bỏ vĩnh viễn khỏi hệ thống nghiên cứu theo nguyện vọng.

---

## 4. Đánh giá nguy cơ và Tiêu chí đảm bảo an toàn

*(Ghi chú 2026-10-22: phân loại rủi ro do hội đồng quyết định; câu sau là nhận định ban đầu của nhóm, chưa được xác nhận.)* Nghiên cứu này được phân loại là **nghiên cứu có rủi ro tối thiểu (minimal risk)**, tương đương với các hoạt động sinh hoạt hàng ngày kết hợp đo sức khỏe định kỳ. Tuy nhiên, nhóm nghiên cứu xác định rõ các nguy cơ tiềm ẩn và biện pháp ngăn ngừa:

### 4.1. An toàn điện và Thiết kế phần cứng
- **QUY TẮC AN TOÀN TUYỆT ĐỐI:**
  > [!NOTE]
  > **Cập nhật 2026-10-21 (V1-module):** V1 không có pin (LiPo thuộc Phần B của
  > [custom_board_proposal.md](../../configs/hardware/custom_board_proposal.md)).
  > ESP32-S3 DevKitC lấy nguồn và truyền dữ liệu qua USB từ một laptop **chạy
  > pin, rút sạc**, không nối thiết bị dùng điện lưới nào khi đang đeo. Với V1,
  > quy tắc dưới đây đọc là: không có đường nào nối người tham gia với điện lưới.
  > Quy tắc chi tiết: [session_safety_stopping_v0.1.md](session_safety_stopping_v0.1.md).
  > Đoạn gốc giữ nguyên bên dưới cho thiết bị đeo dùng pin (Phần B).

  > [!CAUTION]
  > **NGHIÊM CẤM SẠC THIẾT BỊ KHI ĐANG ĐEO TRÊN NGƯỜI:**
  > - Thiết bị nguyên mẫu chỉ được phép hoạt động bằng **nguồn pin sạc Li-ion điện áp thấp nội bộ ($3.7\text{V} - 4.2\text{V}$)** khi đang tiếp xúc với cơ thể người tham gia.
  > - Tuyệt đối không cắm cáp sạc USB, không nối thiết bị với nguồn điện lưới ($220\text{V}/\text{AC}$) hoặc máy tính khi vòng đeo đang tiếp xúc với da người tham gia.
  > - Pin sử dụng phải có mạch bảo vệ ngắt quá áp, quá dòng và chống quá nhiệt (PCM module).
- **Cách ly tín hiệu và tiếp xúc điện cực:**
  - Mạch đo ECG dùng tầng khuếch đại có trở kháng đầu vào cao và có điện trở hạn dòng/bảo vệ ở đầu vào điện cực. Trở kháng đầu vào cao **không tự bảo đảm** dòng rò an toàn: dòng rò qua người phải được đo trên bo mạch thực tế và so với giới hạn của IEC 60601-1 cho loại bộ phận ứng dụng tương ứng, trước khi đo trên người (checklist mục 7).

### 4.2. An toàn da liễu và Tiếp xúc quang học
- **Vật liệu vỏ hộp và điện cực:**
  - Vỏ thiết bị in 3D bằng vật liệu nhựa sinh học an toàn (PLA/PETG) hoặc silicone y tế không độc hại, không có gờ sắc nhọn.
  - Điện cực kim loại tiếp xúc da: vật liệu chưa chốt (thép không gỉ, mạ vàng hoặc Ag/AgCl dùng gel theo [yêu cầu phần cứng V0](../../configs/hardware/hardware_requirements_for_V0.md)). Thép không gỉ 316L có chứa niken, và lớp mạ vàng có thể nằm trên lớp lót niken; vì vậy phải hỏi tiền sử dị ứng kim loại và loại trừ người dị ứng niken nếu điện cực có niken.
- **Cảm biến quang học PPG:**
  - Sử dụng chùm sáng LED xanh lá/đỏ/hồng ngoại với công suất phát quang cực thấp ($< 15\text{mW}$), không tạo nhiệt lượng gây bỏng rát hay tổn thương nhiệt biểu bì da khi đo liên tục.
  - *Ghi chú 2026-10-21:* con số $< 15\text{ mW}$ **chưa có nguồn** và chưa đo; công suất phụ thuộc dòng LED cấu hình trên MAX30101. Không dùng con số này trong hồ sơ nộp cho tới khi có datasheet/đo kiểm.

### 4.3. Sự khó chịu do Vòng bít đo đối chứng (Reference Cuff)
- Vòng bít bắp tay tự động bơm căng có thể gây cảm giác tức ép nhẹ tại bắp tay trong thời gian bơm và xả (protocol dự kiến khoảng $45 - 60\text{ giây}$ mỗi lần đo).
- Giữa hai lần bơm bắp tay liên tiếp phải có khoảng nghỉ tối thiểu 2–3 phút để mạch máu tái tưới máu hoàn toàn, tránh ứ trệ tĩnh mạch cục bộ.

### 4.4. Tiêu chí dừng phiên đo ngay lập tức (Stopping Criteria)
Phiên đo phải được dừng ngay lập tức khi xảy ra một trong các tình huống sau:
1. Người tham gia yêu cầu dừng đo hoặc có biểu hiện khó chịu, đau nhức, chóng mặt hay lo âu.
2. Xuất hiện dấu hiệu đỏ da, ngứa hoặc dị ứng tại vị trí tiếp xúc của cảm biến.
3. Thiết bị nguyên mẫu có biểu hiện nóng lên bất thường hoặc phần mềm ghi nhận lỗi mất kiểm soát nguồn.
4. Máy đo huyết áp đối chứng báo lỗi bơm ép quá mức hoặc chỉ số huyết áp hiển thị đột biến ngoài ngưỡng an toàn sinh lý học (ví dụ $\text{SBP} > 180\text{ mmHg}$ hoặc $\text{DBP} > 110\text{ mmHg}$); khi đó nghiên cứu viên bình tĩnh đề nghị người tham gia nghỉ ngơi và hướng dẫn đến cơ sở y tế nếu cần thiết.

---

## 5. Chính sách bảo mật dữ liệu và giả danh hóa (Data Governance)

Chính sách bảo mật tuân thủ nghiêm ngặt các điều khoản trong `docs/DATA_POLICY.md`:

### 5.1. Cơ chế mã hóa và giả danh hóa danh tính (Pseudonymization)
- Khi còn bảng liên kết danh tính với `subject_id`, dữ liệu là **giả danh hóa**, không phải ẩn danh không thể truy ngược. Mã giả danh không tự loại bỏ mọi nguy cơ tái nhận diện từ metadata hoặc waveform.
- Mỗi người tham gia được gán một mã định danh nghiên cứu duy nhất ngẫu nhiên: `subject_id` (ví dụ: `SUB001`, `SUB002`...; định dạng theo [quy ước dữ liệu](../quy_uoc_du_lieu.md)).
- **Quy tắc tuyệt đối:**
  - Không sử dụng Họ tên, Số điện thoại, Email, Mã số sinh viên, Số căn cước công dân hoặc Ngày sinh làm mã định danh trong dữ liệu.
  - Tệp tín hiệu thô, tệp trích xuất đặc trưng và toàn bộ mã nguồn chỉ được chứa `subject_id`, `session_id`, `event_id`.
  - Tệp bảng mã liên kết giữa thông tin cá nhân và `subject_id` (Identity Key File) là tài liệu mật duy nhất, được mã hóa bằng mật khẩu mạnh (AES-256), lưu trữ độc lập trên ổ cứng rời có mã hóa phần cứng và chỉ do Người chịu trách nhiệm dữ liệu (Huy/Linh) quản lý.

### 5.2. Phân quyền và Kiểm soát truy cập dữ liệu
- **Dữ liệu trên GitHub Repository:**
  - Nghiêm cấm commit dữ liệu thật của người tham gia, dữ liệu nhạy cảm hay dữ liệu dung lượng lớn lên bất kỳ nhánh nào của GitHub.
  - Chỉ các tệp mẫu mô phỏng nhỏ đã được làm sạch và hoàn toàn vô danh tính mới được phép đặt trong `data/sample/`.
- **Dữ liệu lưu trữ nội bộ (Local Storage):**
  - Dữ liệu thực nghiệm đầy đủ chỉ được lưu trữ trên ổ đĩa nghiên cứu được chỉ định tại phòng thí nghiệm hoặc máy trạm có kiểm soát mật khẩu truy cập của các thành viên trong nhóm.

### 5.3. Thời gian lưu trữ và Tiêu hủy dữ liệu
- Dữ liệu nghiên cứu dạng mã hóa được lưu giữ trong suốt quá trình thực hiện đề tài và phục vụ công tác đối soát khoa học tối đa **03 năm** sau khi công bố bài báo.
- Sau thời hạn trên, dữ liệu sẽ được tiêu hủy an toàn (xóa vĩnh viễn theo chuẩn bảo mật ghi đè số học).

### 5.4. Quy trình ứng phó sự cố rò rỉ dữ liệu (Data Breach Protocol)
Nếu phát hiện bất kỳ sự cố rò rỉ dữ liệu hoặc commit nhầm thông tin nhạy cảm:
1. **Dừng khẩn cấp:** Người phát hiện thông báo ngay lập tức cho toàn bộ nhóm nghiên cứu và dừng mọi hoạt động đẩy commit mới.
2. **Cách ly và Thu hồi:** Thu hồi quyền truy cập, xóa commit vi phạm khỏi lịch sử Git theo quy trình BFG Repo-Cleaner/git filter-repo (không chỉ đơn thuần là tạo commit xóa file).
3. **Đánh giá tác động:** Xác định chính xác phạm vi dữ liệu bị ảnh hưởng. Nếu có nguy cơ lộ danh tính, thông báo ngay cho người tham gia và giảng viên hướng dẫn để có biện pháp hỗ trợ kịp thời.

---

## 6. Trách nhiệm của các thành viên trong nhóm nghiên cứu

- **Huy (Điều phối protocol & đạo đức):** Chịu trách nhiệm soạn thảo biểu mẫu đồng thuận, giám sát việc thực hiện đúng protocol và quy trình bảo vệ thông tin người tham gia.
- **Linh (Phần mềm & Dữ liệu):** Chịu trách nhiệm xây dựng hệ thống tự động kiểm tra, đảm bảo công cụ ghi log và pipeline không bao giờ lưu trữ các trường dữ liệu định danh cá nhân (PII).
- **Đức Anh (Phần cứng & Firmware):** Chịu trách nhiệm đảm bảo các tiêu chuẩn an toàn điện, an toàn cơ khí và thử nghiệm nhiệt độ hoạt động của thiết bị nguyên mẫu trước khi đưa vào thử nghiệm.

---

## 7. Các mục cần hoàn thiện trước khi nộp hồ sơ phê duyệt chính thức

> [!IMPORTANT]
> **Checklist chuẩn bị hồ sơ đạo đức chính thức (Sau Tuần 1):**
> 1. [ ] Hoàn thiện Biểu mẫu Phiếu đồng thuận tham gia nghiên cứu (Informed Consent Form template).
> 2. [ ] Hoàn thiện Bản thông tin nghiên cứu dành cho tình nguyện viên (Participant Information Sheet).
> 3. [ ] Hoàn thiện biên bản kiểm định an toàn điện và dòng rò của bo mạch nguyên mẫu.
> 4. [ ] Trình giảng viên hướng dẫn rà soát và ký duyệt trước khi gửi Hội đồng Đạo đức.
> 5. [ ] Xác nhận căn cứ và quy trình ứng phó cho tiêu chí dừng/ngưỡng BP tại mục 4; không coi outline là hướng dẫn xử trí y khoa đã được duyệt.
> 6. [ ] Xác nhận người quản lý bảng liên kết, biện pháp mã hóa, phân quyền, thời gian lưu giữ 03 năm và cách tiêu hủy phù hợp loại thiết bị lưu trữ. Đây là đề xuất, chưa có bằng chứng triển khai/phê duyệt.
