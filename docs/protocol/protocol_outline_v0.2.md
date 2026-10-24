# Khung Protocol Nghiên cứu Thực nghiệm (Protocol Outline) - Phiên bản v0.2

> **Phiên bản:** v0.2 (thay [v0.1](protocol_outline_v0.1.md))
> **Người biên soạn:** Nguyễn Đức Huy
> **Vai trò:** Xử lý tín hiệu, PAT, thống kê, xây dựng protocol nghiên cứu
> **Ngày lập:** 2026-09-22; **cập nhật:** 2026-10-14 (v0.1: đồng bộ với RQ v0.2, yêu cầu phần cứng V0 và nguồn bổ sung), 2026-10-21 (v0.2), 2026-10-22 (sửa theo review).
> **Lưu ý:** chưa thu dữ liệu trên người; chỉ thu sau khi có phê duyệt đạo đức. Phân bổ tay và điện cực ở mục 5.1–5.2 đã xác nhận về phần cứng ngày 2026-10-23; nghiệm pháp ở 6.4–6.5 chưa được hội đồng đạo đức duyệt.

**Changelog v0.2 (2026-10-21, Huy):**

- Mục 5 viết lại theo thiết bị V1-module (Phần A của `custom_board_proposal.md`): bo cổ tay MAX30101/BMI270, bo đế ESP32-S3 + MAX30001, USB tới laptop chạy pin, điện cực dán Ag/AgCl đạo trình I cổ tay–ngón tay. Bỏ cấu hình ngón tay chạm điện cực mặt trên của v0.1.
- Thêm bảng phân bổ tay/điện cực (5.2), chi dùng cho từng nghiệm pháp và kiểm tra xung đột có kết quả (5.4).
- 6.2: thêm nút `t0`. 6.3: cập nhật AFE V1-module và lệch có hệ thống giữa các phương án foot.
- Thêm 6.4 nghiệm pháp tạo ΔBP (có nguồn hướng thay đổi) và 6.5 tiêu chí biên độ ΔBP cho pilot (đề xuất, khóa trước pilot).
- Mục 3, 11, 12 sửa theo các thay đổi trên. Mục 1 chỉ bỏ chữ "trong Tuần 1" ở tuyên bố không thu dữ liệu. Mục 2, 4, 7–10 giữ nguyên từ v0.1.

**Changelog 2026-10-22 (Huy, sửa theo review độc lập Tuần 5):**

- 5.1: MAX30101 là module PPG nhóm đã chọn (Huy xác nhận 2026-10-22). Số điện cực và việc dùng điện cực khô trên người ghi là chờ quyết định. Khôi phục hai ý của v0.1 bị mất khi viết lại mục 5: ghi chú Cohen 2025 về sai số cuff truyền vào hiệu chuẩn, và yêu cầu chốt quy trình đo hai tay trước thu chính.
- 5.3, 6.4: ghi rõ mâu thuẫn chưa giải quyết về thời điểm nói ở M2 và thời điểm cửa sổ tín hiệu ở M4.
- 5.4: đổi tên quy tắc R1–R6 thành K1–K6 để không trùng với dấu hiệu R2/R3/R5 của kế hoạch 28 tuần; K3 thêm M1, M2, M4 (chưa đánh giá); K4 ghi tay đeo cuff luôn mang một điện cực; K6 tách M3/M4; viết lại kết luận cho đúng trạng thái.
- 6.4: M3 thêm yếu tố nhiễu co mạch ngoại vi; M4 ghi hướng ở pha hồi phục chưa chắc; đổi tên "ESH 2023" thành Stergiou 2023; ghi Carroll 2012, Jern 1991 chỉ ủng hộ gián tiếp; bỏ Fu 2002 (nguồn yếu, M5 đã loại).
- 6.5: ghi định nghĩa P2 phải trùng với kịch bản bài báo.

---

## 1. Tuyên bố phạm vi và tính chất nghiên cứu

> [!IMPORTANT]
> **Tuyên bố pháp lý và y đức:**
> 1. Thiết bị đang phát triển trong dự án này là **nguyên mẫu nghiên cứu học thuật (exploratory research prototype)**, hoàn toàn **không phải thiết bị y tế** và không được sử dụng cho bất kỳ mục đích chẩn đoán lâm sàng, sàng lọc hay can thiệp điều trị y tế nào.
> 2. Tài liệu này là **khung phác thảo phương pháp luận (protocol outline)** phục vụ thiết kế kỹ thuật. **Không tuyển tình nguyện viên hoặc thu thập dữ liệu trên người trước khi có phê duyệt.** Hoạt động thu thập dữ liệu chỉ được phép triển khai sau khi đề cương đạo đức hoàn chỉnh được phê duyệt chính thức.

---

## 2. Mục tiêu nghiên cứu (Research Objectives)

1. **Mục tiêu kỹ thuật:** Thiết lập quy trình chuẩn hóa nhằm thu nhận đồng thời tín hiệu ECG và PPG tại cổ tay có đồng bộ thời gian chính xác, kết hợp đo huyết áp đối chứng bằng máy đo bắp tay đạt chuẩn lâm sàng.
2. **Mục tiêu khoa học:**
   - Đánh giá khả năng ước lượng biến thiên huyết áp ($\Delta\text{SBP}$, $\Delta\text{DBP}$) qua các phiên đo độc lập (cross-session) sau khi đã hiệu chuẩn cá nhân ban đầu.
   - So sánh định lượng giá trị đóng góp của việc bổ sung ECG/PAT so với việc chỉ sử dụng đặc trưng hình thái PPG.
   - Kiểm chứng thực nghiệm tính bền vững của mô hình dưới các phương pháp phân chia dữ liệu nghiêm ngặt (chống rò rỉ dữ liệu).

---

## 3. Thiết kế nghiên cứu (Study Design)

- **Hình thức:** Nghiên cứu thực nghiệm quan sát (observational prospective study), đo lặp lại theo chuỗi thời gian (repeated-measures longitudinal design).
- **Cấu trúc phiên đo:** Mỗi người tham gia sẽ thực hiện ít nhất 3 phiên đo độc lập (`session_id`), phân bố qua tối thiểu 2–3 ngày khác nhau:
  - **Phiên 1 (Calibration Session):** Thu nhận mốc huyết áp chuẩn ban đầu ($\text{BP}_0$) và tín hiệu nền để thiết lập tham số hiệu chuẩn cá nhân.
  - **Phiên 2 & Phiên 3 (Evaluation Sessions):** Thu nhận tín hiệu và huyết áp ở các thời điểm khác nhau (ví dụ: sáng/chiều, khác ngày) theo cùng quy trình nghỉ ổn định ở mục 6.1 để đánh giá khả năng theo dõi $\Delta\text{BP}$ ở phiên sau. Các nghiệm pháp làm thay đổi huyết áp trong buổi đo được đề xuất ở mục 6.4; chỉ áp dụng khi đã được duyệt đạo đức.
- **Hệ quả cần lưu ý:** Ở người trẻ khỏe mạnh đo lúc nghỉ, $\Delta\text{BP}$ giữa các phiên có thể nhỏ. Khi đó baseline zero-change (dự đoán $\Delta\text{BP} = 0$) đã có sai số thấp, và mô hình khó thể hiện khác biệt. Mukkamala et al. (2021, [10.1161/HYPERTENSIONAHA.121.17747](https://doi.org/10.1161/HYPERTENSIONAHA.121.17747)) chỉ ra rằng thiết bị có hiệu chuẩn có thể trông chính xác chỉ vì BP ít thay đổi, nên phải báo cáo sai số của baseline chỉ dùng BP hiệu chuẩn và độ lệch chuẩn của $\Delta\text{BP}$ tham chiếu cùng với sai số mô hình.

---

## 4. Đối tượng tham gia dự kiến và Tiêu chí lựa chọn

### 4.1. Cỡ mẫu dự kiến
- Dự kiến $N = 15 - 20$ tình nguyện viên khỏe mạnh (sinh viên/cán bộ tại trường, độ tuổi 18–35).
- Đây là cỡ mẫu khả thi cho giai đoạn thử nghiệm nguyên mẫu (feasibility), chưa dựa trên phân tích power. Với 3 phiên mỗi người và ít nhất 2 lần cuff hợp lệ mỗi phiên ([RQ v0.2](../research_questions_v0.1.md), mục 4.G), dự kiến có tối thiểu $15 \times 3 \times 2 = 90$ đến $20 \times 3 \times 2 = 120$ lần đo cuff hợp lệ, với giả định mọi người hoàn thành đủ 3 phiên; các lần đo này lặp trong cùng người nên **không phải 90–120 quan sát độc lập**. Đơn vị cho kiểm định cặp là người ($n = 15 - 20$). Cỡ mẫu chính thức cần được tính lại từ dữ liệu pilot.

> **Ghi chú 2026-10-22:** mục 4.2–4.3 giữ nguyên từ v0.1. Tiêu chí dùng khi sàng
> lọc nằm ở [eligibility_screening_v0.1.md](../ethics/eligibility_screening_v0.1.md)
> (L1–L10, tự khai). Hai bản còn khác nhau:
>
> - 4.2 ghi "nhịp tim xoang bình thường", điều không xác nhận được bằng tự khai;
>   bản sàng lọc chỉ ghi "tự khai không có bệnh tim mạch đã được chẩn đoán".
> - 4.3 chưa có L5 (cổ tay, cẳng tay trái, bắp tay phải), L7 (không đo được BP tay
>   phải), L8 và L9.
>
> Cần thống nhất trước khi nộp hồ sơ (**chờ quyết định**, cần chuyên môn y tế).
> Độ tuổi 18–35 là đề xuất của nhóm, chưa có nguồn.

### 4.2. Tiêu chí lựa chọn (Inclusion Criteria)
- Độ tuổi từ 18 đến 35 tuổi, có đầy đủ năng lực hành vi dân sự.
- Tự nguyện ký vào phiếu đồng thuận tham gia nghiên cứu (Informed Consent).
- Nhịp tim xoang bình thường, không có tiền sử bệnh lý tim mạch đã được chẩn đoán.

### 4.3. Tiêu chí loại trừ (Exclusion Criteria)
- Người có tiền sử tăng huyết áp bệnh lý, hạ huyết áp tư thế, loạn nhịp tim (rung nhĩ, ngoại tâm thu dày) hoặc đang sử dụng thuốc tác động đến hệ tim mạch/hệ thần kinh giao cảm (thuốc chẹn beta, giãn mạch, an thần).
- Người có vết thương hở, viêm da, dị ứng hoặc kích ứng tiếp xúc tại vùng cổ tay đeo thiết bị; người có tiền sử dị ứng kim loại (niken) nếu điện cực được chọn có chứa niken.
- Người mang máy tạo nhịp tim hoặc thiết bị cấy ghép điện tử trong cơ thể.
- Phụ nữ đang mang thai hoặc nghi ngờ có thai.

---

## 5. Bố trí thiết bị, điện cực và tư thế đo

> [!IMPORTANT]
> **Mục 5 và mục 6.4–6.5: đề xuất của Huy (2026-10-21).** Phân bổ tay, số và vị
> trí điện cực, cực tính (5.1, 5.2) đã xác nhận về phần cứng ngày 2026-10-23. Các
> nghiệm pháp ở 6.4 còn chờ thầy và hội đồng đạo đức chấp thuận. Chưa đo trên
> người, kể cả thành viên nhóm. Kiểm tra xung đột ở 5.4 là kiểm tra trên giấy;
> dòng "chưa kiểm chứng" cần bản ghi bench/G2.

### 5.1. Thiết bị V1-module

Theo [custom_board_proposal.md, Phần A](../../configs/hardware/custom_board_proposal.md):

- **Bo cảm biến cổ tay** 40,4 × 31,5 mm, gắn dây velcro 20 mm: PPG SparkFun
  MAX30101 (SEN-16474, ba kênh xanh lá, đỏ, IR; **nhóm đã chọn**, Huy xác nhận
  2026-10-22), IMU BMI270; V1 không dùng FSR (chốt 2026-10-23). Nối bo đế bằng cáp
  dẹt 16 dây dài dự kiến 20–30 cm. Pin map chuẩn: KiCad V1-module
  (`configs/hardware/custom_board_proposal.md` A.7, chốt 2026-10-23); danh sách
  mua: `hardware/bom/purchase_list_v1_module.md`.
- **Bo đế đặt trên bàn:** ESP32-S3-DevKitC-1-N8R8 chính hãng, breakout ProtoCentral
  MAX30001 (ECG), nút `t0` đánh dấu bắt đầu bơm cuff trên cùng đồng hồ
  `esp_timer`.
- **Nguồn và dữ liệu:** DevKitC nối USB với laptop **chạy pin, rút sạc**; không
  thiết bị nào nối điện lưới khi người tham gia đang đeo
  ([quy tắc an toàn](../ethics/session_safety_stopping_v0.1.md)).
- **ECG:** **ba** điện cực dán Ag/AgCl có gel, dùng một lần (LA, RA và RL tham
  chiếu), qua cáp 3 điện cực kèm kit và jack 3,5 mm của breakout; đạo trình I
  giữa **hai cổ tay** (chốt 2026-10-23, vị trí ở 5.2). Ag/AgCl là phương án chính,
  điện cực khô chỉ để so sánh
  ([Hai_phuong_an_dien_cuc_ECG.pdf](../../hardware/Hai_phuong_an_dien_cuc_ECG.pdf)).
  Cấu hình hai điện cực (bỏ RL, bật lead bias nội) chỉ so sánh trên bench.
  **Chờ quyết định:** điện cực khô dùng trên người hay chỉ trên bench. Nếu dùng
  trên người thì phải thêm vào phiếu thông tin, phiếu đồng thuận và tiêu chí
  loại L6.
- **Cuff:** máy đo bắp tay tự động có kết quả validation đã công bố cho đúng
  model; model chưa chốt (mục 12). Không coi "cùng hãng" là đã validate. Sai số
  của máy cuff truyền thẳng vào nhãn và vào mốc hiệu chuẩn $\text{BP}_0$: AHA
  scientific statement về thiết bị cuffless (Cohen et al., 2025,
  [10.1161/HYP.0000000000000254](https://doi.org/10.1161/HYP.0000000000000254))
  nhấn mạnh độ chính xác của thiết bị cuffless phụ thuộc mạnh vào cuff dùng để
  hiệu chuẩn. Quy trình đo hai tay và tiêu chí chọn bên/loại trừ phải chốt trước
  khi thu dữ liệu chính (như v0.1); sau khi khóa protocol, không đổi bên tùy
  từng lượt đo.

So với v0.1: bỏ cấu hình "điện cực mặt đáy vòng + ngón tay chạm điện cực mặt
trên". Điện cực dán không cần người tham gia chủ động chạm, nên ECG không phụ
thuộc vào việc giữ ngón tay trong lúc cuff bơm.

### 5.2. Bảng phân bổ (phương án A, đề xuất chính)

| Thành phần | Vị trí | Lý do / ghi chú |
| --- | --- | --- |
| Bo PPG cổ tay | Mặt lưng cổ tay **trái**, cách mỏm trâm trụ khoảng 1,5–2,0 cm (như v0.1); cố định cho mọi người, ghi tay thuận vào metadata | Không đổi bên giữa người/lượt để tránh thêm biến số |
| Cuff đối chứng | Bắp tay **phải**, ngang tim, đúng cỡ vòng bít | Khác tay với PPG (5.4, K1) |
| Điện cực LA (ECGP) | Cổ tay **trái**, mặt lòng, không nằm dưới dây đeo hay bo PPG | Phía tay trái của đạo trình I |
| Điện cực RA (ECGN) | Cổ tay **phải**, mặt lòng | Phía tay phải; nằm xa cuff ở bắp tay. Điện cực 4 × 3,3 cm dán vừa, không cần loại nhỏ cho ngón tay |
| Điện cực RL (tham chiếu, VCM) | Cẳng tay **trái**, mặt lòng, cách LA khoảng 5 cm về phía khuỷu | Mặt lòng cổ tay không đủ chỗ cho hai miếng; tay đeo cuff chỉ mang một dây điện cực |
| Cực tính | Tay trái là cực dương của đạo trình I: LA → ECGP (vòng giữa, ring của jack), RA → ECGN (đầu, tip), RL → sleeve → VCM qua R3 (theo schematic `pc_max30001_brk_v1.0`); tắt lead bias nội (`custom_board_proposal.md` A.2) | `ecg_polarity = 1`. Màu nắp đầu bấm khác nhau tùy lô cáp: đo thông mạch đầu bấm ↔ tip/ring/sleeve trước buổi đo đầu tiên |
| Cáp | Cáp dẹt PPG và dây điện cực đi dọc cẳng tay, cố định bằng băng dính y tế, không kéo căng bo PPG | Giảm nhiễu do cáp lay |
| Tư thế | Như 5.3 | |

**Phương án B cũ** (điện cực ở cổ tay phải và ngón tay trái) không dùng nữa: phương
án A đã dời RA từ ngón trỏ sang cổ tay phải, nên không còn vướng việc dán điện cực
lên ngón tay. Chiều dài dây và việc dây không kéo bo PPG kiểm khi có module (K5).

**Chi dùng cho từng nghiệm pháp** (chi tiết ở 6.4):

| Nghiệm pháp | Chi hoạt động | Tay trái (PPG + LA + RL) | Tay phải (cuff + RA) |
| --- | --- | --- | --- |
| M0 Nghỉ ngồi | Không | Yên trên bàn | Yên trên bàn |
| M1 Thở chậm có hướng dẫn | Hô hấp | Yên | Yên |
| M2 Tính nhẩm | Không (trả lời bằng lời ngoài cửa sổ ghi) | Yên | Yên |
| M3 Ngâm bàn chân vào nước lạnh | Một bàn chân (bên chưa chốt) | Yên | Yên |
| M4 Đạp xe nhẹ tư thế ngồi, đo khi hồi phục | Hai chân | Yên trên bàn | Yên trên bàn |
| ~~M5 Bóp tay tĩnh~~ | Một tay | Loại (5.4) | Loại (5.4) |

### 5.3. Tư thế người tham gia
- Ngồi tựa lưng thoải mái trên ghế có tựa, hai bàn chân đặt phẳng trên sàn, hai chân không bắt chéo (trừ khi làm M3/M4).
- Cả hai cẳng tay đặt thả lỏng trên mặt bàn có đệm êm, giữ cho cổ tay đeo thiết bị và vùng đo bắp tay nằm **ngang mức tim**.
- Không nói chuyện, không cử động ngón tay hay thay đổi tư thế trong suốt quá trình ghi tín hiệu và bơm xả cuff.
- **Mâu thuẫn chưa giải quyết (review 2026-10-22):** M2 cần người tham gia trả lời
  bằng lời, và 6.4 đo cuff "khi đang làm" M2. Cách trả lời (nói, hay cách khác
  không dùng tay), thời điểm được nói và việc có đo cuff khi đang nói hay không:
  **chờ quyết định**. Cần vẽ trục thời gian M2 trước khi nộp hồ sơ.

### 5.4. Kiểm tra xung đột (2026-10-21, trên giấy; sửa 2026-10-22)

Mã quy tắc K1–K6 (trước đây R1–R6) để không trùng với dấu hiệu R2/R3/R5 của kế
hoạch 28 tuần.

| # | Quy tắc | Kết quả với phương án A | Còn phải làm |
| --- | --- | --- | --- |
| K1 | Cuff không cùng tay đeo PPG | **Đạt:** cuff tay phải, PPG tay trái | — |
| K2 | Không nghiệm pháp nào làm chuyển động tay đeo PPG | **Đạt trên giấy** cho M0–M2. **Chưa kiểm chứng** cho M3: thao tác đưa và rút chân, đau do lạnh có thể làm người tham gia cử động thân hoặc bám tay vào bàn. **Đạt có điều kiện** cho M4: thân người chuyển động khi đạp, nên chỉ lấy cửa sổ tín hiệu và đo cuff sau khi dừng đạp, tay vẫn đặt trên bàn (thời điểm cửa sổ còn mâu thuẫn, 6.4). **Không đạt** cho M5 nếu bóp bằng tay trái | IMU BMI270 kiểm chuyển động thực tế |
| K3 | Tránh nhiễu cơ trên chi gắn điện cực ECG | Đạo trình I cần điện cực ở **cả hai tay**, nên mọi hoạt động cơ tay đều gây nhiễu. **Không đạt** cho M5 với bất kỳ tay nào → loại M5. **Chưa kiểm chứng** cho M3 (đau do lạnh có thể làm người tham gia gồng cả người) và cho lúc cuff bơm (căng cơ tay phải). **Chưa đánh giá:** M1 (thở sâu làm trôi nền, có thể làm cửa sổ bị loại có hệ thống theo quy tắc SQI ở mục 7), M2 (nói, cơ hô hấp), M4 (tì tay, mồ hôi, thở mạnh sau đạp) | Xem ECG trong M1–M4 và lúc cuff bơm ở G2 |
| K4 | ECG có tín hiệu tại thời điểm đo cuff | **Đạt về thiết kế:** điện cực dán, không cần chạm chủ động. Với đạo trình I, tay đeo cuff **luôn** mang một điện cực (RA ở cổ tay phải); đổi vị trí điện cực không xử lý được. Pha cuff bơm được loại khỏi phân tích chính (6.2, giai đoạn 2). **Chưa kiểm chứng** ảnh hưởng của cuff bơm lên ECG | Bản ghi có cuff bơm trên bench/G2, sau khi được phép |
| K5 | Dây điện cực và cáp không đè hay kéo bo PPG | Chưa kiểm (chưa có module). Tay trái mang cáp dẹt PPG và hai dây LA, RL | Thử khi có module |
| K6 | Chân dùng cho M3/M4 không ảnh hưởng tay | **Đạt trên giấy** cho M3 (xem K2). **Có điều kiện** cho M4: đạp làm thân người chuyển động (K2) | IMU kiểm ở G2 |

Kết luận (trên giấy, 2026-10-22):

- K1 đạt; M5 bị loại.
- K2 đạt trên giấy cho M0–M2, chưa kiểm chứng cho M3, có điều kiện cho M4.
- K3, K4, K5 chưa kiểm chứng; K3 chưa đánh giá M1, M2, M4.
- Vì vậy **chưa thể nói** phương án A không còn xung đột với M0–M4. Cần bản ghi
  bench/G2 và trục thời gian M2/M4 (5.3, 6.4).

---

## 6. Quy trình thu thập dữ liệu và Đồng bộ tín hiệu

### 6.1. Quy trình nghỉ ổn định trước khi đo
1. Người tham gia đến phòng đo, ngồi nghỉ ngơi yên tĩnh trong môi trường nhiệt độ phòng ổn định ($24 - 26^\circ\text{C}$, đề xuất, chưa có nguồn) trong tối thiểu **10 phút**.
2. Giải thích lại quy trình thao tác và kiểm tra độ vừa vặn của thiết bị.
3. Không uống cà phê, trà, hút thuốc hoặc vận động mạnh trong vòng 2 giờ trước phiên đo (đề xuất, chưa có nguồn).

### 6.2. Trình tự một lượt đo (Measurement Event)
Mỗi sự kiện đo (`event_id`) kéo dài khoảng $2.5 - 3\text{ phút}$, gồm 3 giai đoạn:
1. **Giai đoạn 1 - Ghi tín hiệu trước đo cuff (Baseline Signal Window - $60\text{s}$):**
   - Thiết bị thu nhận tín hiệu PPG và ECG đồng bộ liên tục trong 60 giây trước khi bắt đầu bơm cuff. Toàn bộ 60 giây được lưu để kiểm soát chất lượng và phân tích độ nhạy.
   - Đây là **cửa sổ tín hiệu ứng viên trước cuff**, không phải phép đo huyết áp đồng thời. Cửa sổ phân tích chính dự kiến là 20–30 giây ngay trước thời điểm bơm cuff và chỉ được chấp nhận khi SQI đạt yêu cầu, nhịp tim/xung tương đối ổn định và không có chuyển động. Phải lưu độ lệch thời gian giữa cuối cửa sổ tín hiệu và thời điểm máy cuff trả kết quả.
2. **Giai đoạn 2 - Bơm đo huyết áp đối chứng bằng Cuff ($45 - 60\text{s}$):**
   - Kích hoạt máy đo bắp tay và **bấm nút `t0` trên bo đế cùng lúc**; nút ghi sự kiện trên cùng đồng hồ `esp_timer` với ECG/PPG. Ghi nhận thời điểm kết thúc xả.
   - Tín hiệu thu được trong giai đoạn này được gắn cờ cuff_inflating = True; không dùng làm đầu vào chính cho mô hình. ECG vẫn được ghi (điện cực dán) để kiểm K4 ở mục 5.4.
3. **Giai đoạn 3 - Ghi nhãn và nghỉ hồi phục ($30\text{s}$):**
   - Ghi nhận kết quả SBP, DBP và Pulse Rate từ màn hình máy đo đối chứng vào biểu mẫu nghiên cứu.
   - Nghỉ tối thiểu 2 phút trước khi lặp lại lượt đo tiếp theo.

- **Phân tích độ nhạy ghép nhãn:** So sánh kết quả khi dùng cửa sổ 10, 20, 30 và 60 giây trước cuff, đồng thời loại riêng các lượt không đạt tiêu chí plateau. Nếu kết quả thay đổi đáng kể theo cửa sổ, phải báo cáo đây là bất định do nhãn không đồng thời, không được chọn hậu nghiệm cửa sổ cho kết quả đẹp nhất.

### 6.3. Đồng bộ thời gian phần cứng giữa ECG và PPG
- ECG và PPG cần cùng quy chiếu thời gian hoặc ánh xạ clock được kiểm chứng; không mặc định hai AFE lấy mẫu đồng thời chỉ vì dùng cùng MCU.
- V1-module dùng MAX30001 (ECG) và MAX30101 (PPG). ECG chốt 512 sps (`custom_board_proposal.md` Phần A.2, 2026-10-23). PPG chốt multi-LED ba khe ở 200 sps mỗi khe, `SMP_AVE = 1` (A.6 mục 3, 2026-10-24); độ rộng xung còn mở; bảng tốc độ cấu hình được ở [interface_power_sampling_v0.md, mục 4](../../configs/hardware/interface_power_sampling_v0.md). Tần số cuối cùng phải là giá trị mà từng AFE hỗ trợ theo datasheet và phải được đo lại trên thiết bị.
- Với độ phân giải thời gian, mỗi mẫu ECG ở 512 sps là khoảng 1,95 ms và mỗi mẫu PPG ở 200 sps là 5 ms; sai số định vị R peak và PPG foot cộng với sai số đồng bộ hai kênh đi thẳng vào PAT, nên cần đo jitter/offset thực tế ([kế hoạch đo 10 phút](../../hardware/test_reports/sync_10min_test_plan.md)) trước khi diễn giải các thay đổi PAT cỡ vài ms. Phương pháp foot khác nhau lệch nhau có hệ thống hàng chục ms trên cùng xung ([Tuần 5](week05_fiducials_pat_validity.md)); không trộn phương pháp trong một phân tích.
- Phải phân biệt timestamp **lấy mẫu**, timestamp **đọc FIFO** và thời điểm **nhận gói tại PC**. Counter MCU không tự loại bỏ độ trễ sensor/FIFO, sai lệch clock hoặc jitter. Cần ghi clock, đơn vị, tần số theo kênh, mất mẫu và cách suy ra thời điểm từng mẫu từ timestamp mẫu đầu gói.
- Marker bắt đầu bơm cuff (`t0`) phải cùng clock hoặc có ánh xạ có thể kiểm tra. Không dịch PPG để trùng đỉnh R vì sẽ mất độ trễ cần tính PAT.

### 6.4. Nghiệm pháp tạo ΔBP (đề xuất, chờ thầy/hội đồng chấp thuận)

Mục đích chung: mở rộng dải ΔBP so với mốc hiệu chuẩn, vì đo lúc nghỉ ở người
trẻ cho ΔBP nhỏ và baseline zero-change khó bị vượt (mục 3). Mukkamala et al.
2021 ([10.1161/HYPERTENSIONAHA.121.17747](https://doi.org/10.1161/HYPERTENSIONAHA.121.17747),
toàn văn, [tổng quan bổ sung S2](../literature/literature_update_2026-10-14.md))
đề xuất đánh giá thiết bị có hiệu chuẩn với ít nhất ba can thiệp làm BP thay đổi.
Nghiệm pháp trong một buổi tạo ΔBP **trong phiên**; phép so sánh chính của RQ1
vẫn là ΔBP **giữa các phiên**, phân tích phải gắn nhãn nghiệm pháp và không gộp
hai loại.

"Mức đã đọc" của nguồn: tất cả là **abstract** (Europe PMC, đọc 2026-10-21) trừ
khi ghi khác. Không có nguồn nào ở đây cho biên độ ΔBP ở đúng quần thể và
protocol của nhóm.

| Mã | Nghiệm pháp | Mục đích | Hướng BP dự kiến và nguồn | Thời lượng | Rủi ro | Dừng khi |
| --- | --- | --- | --- | --- | --- | --- |
| M0 | Nghỉ ngồi | Mốc hiệu chuẩn, so sánh | Ổn định (mục 6.1) | ≥ 10 phút nghỉ, rồi ≥ 2 lượt cuff | Tối thiểu | Quy tắc chung |
| M1 | Thở chậm có hướng dẫn | ΔBP âm | **Giảm.** Adler 2019 ([10.1152/japplphysiol.00442.2019](https://doi.org/10.1152/japplphysiol.00442.2019)): 22 người trẻ huyết áp bình thường, 15 phút thở chậm do thiết bị RESPeRATE hướng dẫn, SBP giảm 3,2 ± 0,8 mmHg (đo 5 phút cuối). Biên độ nhỏ, có thể không vượt sai số cuff | 15 phút theo nguồn; nhịp thở cụ thể **chưa có nguồn** (abstract không nêu) | Chóng mặt, tê đầu ngón | Chóng mặt, tê, khó chịu khi thở |
| M2 | Tính nhẩm | ΔBP dương do stress tâm lý | **Tăng** (nguồn chỉ **ủng hộ gián tiếp**). Carroll 2012 ([10.1111/j.1469-8986.2012.01463.x](https://doi.org/10.1111/j.1469-8986.2012.01463.x)) đo phản ứng SBP/DBP với tính nhẩm (431 người, 63 tuổi; câu hỏi về tiên lượng); Jern 1991 ([10.1042/cs0810593](https://doi.org/10.1042/cs0810593)): phản ứng HR/BP lặp lại tốt ở 14 nam trẻ. Abstract không nêu chiều hay biên độ ở người trẻ; cần nguồn trực tiếp. Stress cũng làm đổi PEP, nên PAT có thể đổi mà BP không đổi ([RQ](../research_questions_v0.1.md), mục F) | **Chưa có nguồn** | Căng thẳng, lo âu | Người tham gia muốn dừng, căng thẳng rõ |
| M3 | Ngâm một bàn chân vào nước lạnh | ΔBP dương do kích thích lạnh | **Tăng SBP và DBP.** Korhonen 2006 ([10.3402/ijch.v65i2.18090](https://doi.org/10.3402/ijch.v65i2.18090)): 20 nam khỏe, cold pressor ở tay và **ở chân** đều làm tăng SBP, DBP. Velasco 1997 ([10.1097/00045391-199701000-00008](https://doi.org/10.1097/00045391-199701000-00008), tổng quan): giải phóng norepinephrine gây co tiểu động mạch, tăng BP. Dùng chân để hai tay (PPG, cuff, ECG) không tham gia. **Yếu tố nhiễu:** co mạch ngoại vi do lạnh có thể làm đổi PPG và PAT ở cổ tay độc lập với BP (Velasco 1997; [RQ](../research_questions_v0.1.md), mục F), nên sai số phải báo theo từng nghiệm pháp, không gộp, và dự kiến SQI có thể giảm trong M3 | Nhiệt độ nước và thời lượng **chưa có nguồn** | Đau buốt, gồng người (K3), phản ứng giao cảm | Đau không chịu được, yêu cầu; rút chân ngay |
| M4 | Đạp xe nhẹ tư thế ngồi, đo trong pha hồi phục | ΔBP dương do vận động | Tăng khi gắng sức; **ở pha hồi phục chưa chắc**. Stergiou 2023 (khuyến cáo ESH về validation thiết bị không cuff, [10.1097/HJH.0000000000003483](https://doi.org/10.1097/HJH.0000000000003483), S1) có phép thử vận động là phép thử BP tăng, nhưng không nói đo lúc nào. Mukkamala 2021 (toàn văn PMC8516718, đọc 2026-10-22) ghi BP sau gắng sức có thể **thấp hơn** trước gắng sức, và thay đổi BP do gắng sức có thể tương đối dễ phát hiện vì HR và biên độ mạch tăng rõ, nên mô hình có thể chỉ bám HR. Esmaili 2017 (ma trận #6, toàn văn) ghi tín hiệu trong hồi phục sau gắng sức; Zhang 2017 (#8) dùng đạp xe nằm | Cường độ, thời lượng **chưa có nguồn** | Mệt, khó thở; chuyển động thân (K2) | Mệt, khó thở, đau; hết thời lượng duyệt |
| ~~M5~~ | ~~Bóp tay tĩnh~~ | — | Tăng (Mark 1985, [10.1161/01.res.57.3.461](https://doi.org/10.1161/01.res.57.3.461): HR và BP tăng ở phút 1–2 khi bóp 30% lực tối đa) | — | — | **Loại**: không đạt K2/K3 ở 5.4 |

Không đưa vào: đổi tư thế ngồi–đứng (tay đeo PPG di chuyển và đổi độ cao so với
tim, vi phạm K2).

Thứ tự đề xuất trong một buổi: M0 → M1 → nghỉ → M2 → nghỉ → M3 → nghỉ → M4 → nghỉ.
Thứ tự cố định hay đổi chéo, thời gian nghỉ giữa nghiệm pháp và tiêu chí "BP đã
về gần nền": **chưa khóa, chưa có nguồn**. Đo cuff: trong M1 (phút cuối), M2 và
M3 (khi đang làm, tay phải không tham gia), M4 (ngay sau khi dừng đạp). Mỗi lần
đo cuff vẫn là một nhãn; nhiều cửa sổ trong cùng nghiệm pháp không thành nhiều nhãn.

**Mâu thuẫn chưa giải quyết (review 2026-10-22), chờ quyết định trước khi nộp hồ sơ:**

- **M4:** cửa sổ tín hiệu là 60 s ngay trước khi bơm cuff (6.2). Nếu cuff bơm
  "ngay sau khi dừng đạp", cửa sổ đó rơi vào lúc **đang đạp**, trái với K2. Cần
  trục thời gian `t_dừng` → cửa sổ tín hiệu → cuff, ghi rõ độ trễ giữa nhãn và
  cửa sổ. BP hồi phục thay đổi nhanh, nên độ trễ này đi thẳng vào sai số nhãn.
- **M2:** đo cuff "khi đang làm" mâu thuẫn với quy tắc không nói ở 5.3.

### 6.5. Tiêu chí biên độ ΔBP kiểm ở pilot — **ĐỀ XUẤT, KHÓA TRƯỚC PILOT**

Định nghĩa trong pilot: ΔBP của một lần cuff trong nghiệm pháp = giá trị đó trừ
trung bình các lần cuff M0 cùng buổi; SBP và DBP riêng.

| # | Tiêu chí | Nguồn của ngưỡng |
| --- | --- | --- |
| P1 | Báo cáo theo người và theo nghiệm pháp: median, IQR của ΔSBP/ΔDBP và tỷ lệ lần cuff có hướng thay đổi đúng như 6.4 | Hướng: nguồn ở 6.4. Không có ngưỡng đạt/không đạt cho tỷ lệ (**chưa có nguồn**) |
| P2 | Median theo người của max \|ΔSBP\| qua các nghiệm pháp **≥ 15 mmHg**; thấp hơn thì báo giảng viên và rà protocol trước thu chính | Lấy từ dấu hiệu R3 của kế hoạch 28 tuần (tài liệu nội bộ ngoài repo, áp dụng ở thu chính) — **ngưỡng nội bộ, không có nguồn khoa học**. Định nghĩa ở đây (max, trong phiên, so với M0) **khác** câu "median ΔSBP theo người" ở [kịch bản bài báo](../paper_scenarios_v0.1.md): phải chọn **một** định nghĩa và khóa cùng lúc (**chờ quyết định**). Lấy max bị kéo lên bởi sai số đo cuff |
| P3 | Báo SD của ΔBP tham chiếu và tỷ lệ \|ΔBP\| > 5 mmHg | [RQ v0.2, mục 4](../research_questions_v0.1.md) (quy ước nội bộ) |
| P4 | Không tăng cường độ hay thời lượng nghiệm pháp ngoài bản đã duyệt để đạt P2 | Kế hoạch 28 tuần (nội bộ) |

Ngưỡng trên khóa bằng commit trước buổi pilot đầu tiên; không chỉnh sau khi xem
dữ liệu. Pilot chỉ chạy khi có phê duyệt phù hợp.

---

## 7. Quy tắc phân đoạn, Gán nhãn và Kiểm soát chất lượng (SQI)

### 7.1. Định nghĩa mẫu độc lập (Independent Sample)
> [!CAUTION]
> **Nguyên tắc cốt lõi chống thổi phồng dữ liệu:**
> - **Mỗi lần đo bằng cuff đối chứng chỉ tạo ra DUY NHẤT 1 nhãn huyết áp độc lập ($\text{SBP}_i, \text{DBP}_i$).**
> - Tuyệt đối **KHÔNG** được cắt đoạn tín hiệu 60 giây trước đó thành 12 cửa sổ nhỏ (mỗi cửa sổ 5 giây) rồi gán cùng giá trị $(\text{SBP}_i, \text{DBP}_i)$ cho cả 12 cửa sổ và coi đó là 12 mẫu độc lập. Cách làm sai lầm này sẽ gây rò rỉ dữ liệu nghiêm trọng và thổi phồng sai lệch kích thước mẫu.
> - Đề xuất tổng hợp đặc trưng bằng trung vị trong cửa sổ chính dự kiến 20–30 giây trước cuff; chưa khóa độ dài hoặc quy tắc tổng hợp. Các ứng viên độ nhạy 10/20/30/60 giây lấy `[t0 - L, t0)`, phải chọn/khóa trên pilot/validation trước khi xem test. Mỗi `event_id` vẫn chỉ đóng góp tối đa một cặp nhãn cuff độc lập.

### 7.2. Định danh cấu trúc dữ liệu phân cấp
Mỗi bản ghi phải chứa khóa định danh duy nhất theo cấu trúc (định dạng ID theo [quy ước dữ liệu](../quy_uoc_du_lieu.md)):
- `subject_id`: Mã người tham gia (ví dụ: `SUB001`, `SUB002`), không chứa thông tin định danh cá nhân.
- `session_id`: Mã phiên đo theo ngày/thời điểm (ví dụ: `S001`, `S002`).
- `event_id`: Mã lượt đo trong phiên (ví dụ: `E01`, `E02`).
- `window_id`: Mã cửa sổ tín hiệu thành phần bên trong một event.

### 7.3. Tiêu chí kiểm tra chất lượng tín hiệu (SQI) và Loại bỏ cửa sổ
Các tiêu chí và con số dưới đây là **đề xuất chưa khóa**, không phải ngưỡng đã kiểm chứng hay quy tắc đang triển khai. Phải kiểm tra căn cứ, cực tính/lọc tín hiệu và kiểm tra trên pilot/validation trước khi áp dụng; không tuning theo test. Dự kiến gắn `flag_reject = True` khi vi phạm tiêu chí đã khóa:
1. **Nhiễu bão hòa quang học (Clipping/Saturation):** Tín hiệu PPG chạm ngưỡng kịch trần ADC ($V_{\text{max}}$ hoặc $V_{\text{min}}$) quá 5% thời gian cửa sổ.
2. **Chỉ số Skewness SQI ($s\text{SQI}$):** Ứng viên $s\text{SQI} < 0$; dấu phụ thuộc cực tính và xử lý tín hiệu, không mặc định mọi PPG hợp lệ đều có độ lệch dương.
3. **Mất tín hiệu ECG:** Không phát hiện được phức bộ QRS rõ ràng hoặc biên độ đỉnh R nhỏ hơn $3\times$ độ lệch chuẩn đường nền.
4. **Biến thiên nhịp tim bất thường:** Khoảng cách giữa các đỉnh R liên tiếp biến động $> 30\%$ trong cửa sổ tĩnh (ngoại trừ hiện tượng loạn nhịp sinh lý khi hô hấp đã kiểm soát).
5. **Cử động mạnh (`motion-sqi-v0`, định nghĩa chốt 2026-10-24, ngưỡng chưa khóa):**
   IMU BMI270 ở cổ tay đeo PPG, gia tốc và gyro 100 Hz (Packet Schema V0.2). Mã:
   [motion_sqi.py](../../software/feature_extraction/motion_sqi.py).
   - Gia tốc: lọc từng trục thông cao 0,5 Hz rồi thông thấp 10 Hz (Butterworth bậc 2,
     pha không đổi), lấy độ lớn vector $d(t)$. Gyro: trừ bias rồi thông thấp 10 Hz,
     lấy độ lớn $s(t)$. Đoạn lọc rộng hơn cửa sổ nhưng không vượt qua $t_0$ (bơm cuff).
   - Bias gyro lấy từ 30 s nghỉ **đã xác nhận yên** ở M0; đoạn này có mất mẫu, bão
     hòa hay chuyển động thì không có bias (ghi lý do), không tìm đoạn "yên nhất".
   - Chỉ số burst: phân vị 95 trên cửa sổ trượt 1 s, bước 0,1 s, lấy giá trị lớn
     nhất trong cửa sổ phân tích (P95 trên cả 10 s bỏ sót cú giật < 0,5 s). Xuất kèm
     P95 toàn cửa sổ, tỉ lệ mẫu vượt ngưỡng và giá trị lớn nhất.
   - `motion` khi một nhánh hợp lệ vượt ngưỡng (gia tốc 0,15 g hoặc gyro 20 °/s);
     `no_motion_detected` chỉ khi **cả hai** nhánh hợp lệ và dưới ngưỡng; còn lại
     `not_evaluable` (mất mẫu, không nội suy; bão hòa; thiếu bias; cửa sổ ngắn hơn
     1 s). Gia tốc dưới ngưỡng không đủ để coi cửa sổ là yên.
   - Hai ngưỡng là `ENGINEERING_DRAFT_NOT_TEST_TUNED`, **không có nguồn**; khóa trên
     bản ghi G2 của thành viên nhóm (nghỉ so với cử động theo hướng dẫn, có nhãn
     chuyển động độc lập), ghi ngày và commit, trước khi thu chính.
   - Giới hạn: không chứng nhận tín hiệu sạch. Bóp hay gồng tay có thể làm hỏng PPG
     mà gần như không tạo gia tốc hay xoay; cử động chậm (nâng tay, lắc thân khi đạp
     M4) bị lọc 0,5 Hz làm yếu; IMU tay trái không phản ánh nhiễu cơ ở tay phải (RA).
   - Chính sách loại hoặc giảm trọng số ở cấp cuff event **chưa định nghĩa**; phải
     khóa riêng trước thu chính. Với RQ3, so mọi chiến lược trên cùng tập cuff event,
     báo coverage trên toàn bộ event, không coi phần còn lại sau lọc chuyển động là
     coverage 100 %.

---

## 8. Phương pháp tính toán đại lượng PAT và Cảnh báo vật lý

### 8.1. Công thức xác định PAT
$$\mathrm{PAT} = t_{\mathrm{PPG,foot}} - t_{\mathrm{ECG,Rpeak}}$$
- $t_{\mathrm{ECG,Rpeak}}$: Thời điểm đỉnh sóng R của phức bộ QRS. Pan–Tompkins hiệu chỉnh là một thuật toán ứng viên; phương pháp phát hiện R peak, cấu hình lọc và quy tắc xử lý đỉnh giả/bỏ sót phải được kiểm tra trên pilot/validation trước khi khóa.
- $t_{\mathrm{PPG,foot}}$: Thời điểm chân sóng (foot) của nhịp PPG tương ứng. Tiếp tuyến giao cắt (intersecting tangent method) và đạo hàm bậc hai cực đại ($d^2\text{PPG}/dt^2$) là các phương pháp ứng viên; phương pháp foot và quy tắc ghép nhịp vẫn chưa khóa, phải khóa trên pilot/validation, không điều chỉnh theo test.

### 8.2. Cảnh báo phương pháp luận: $\text{PAT} \neq \text{PTT}$
- Nhóm nghiên cứu ghi nhận rõ ràng:
  $$\text{PAT} = \text{PEP} + \text{PTT}$$
  Đây là cách viết gọn. PEP thường bắt đầu ở Q/QRS, không phải R peak; khoảng R đến lúc tống máu có thể khác PEP. Cần khai báo các mốc; ECG + PPG dự kiến chỉ đo PAT, không đo riêng PEP/PTT. Xem [glossary Tuần 2](week_02_sample_label_glossary.md).
- **Quy tắc bắt buộc:**
  - Không được áp dụng trực tiếp các phương trình vật lý sóng mạch thuần túy của PTT (như Bramwell-Hill hay Hughes) cho PAT mà bỏ qua PEP.
  - Đề xuất kiểm tra HR và hình thái PPG trong ablation; chưa có bằng chứng các đặc trưng đó bù trừ được biến thiên PEP trong dự án.

---

## 9. Kế hoạch phân chia dữ liệu và Đánh giá thống kê

### 9.1. Chiến lược phân chia (Data Splitting)
1. **Subject-independent Split (Leave-One-Subject-Out Cross-Validation - LOSO):**
   - Toàn bộ dữ liệu của đối tượng $k$ được dành riêng cho tập Test.
   - Mô hình được huấn luyện trên $N-1$ đối tượng còn lại.
   - Lặp lại cho tất cả $N$ đối tượng để thu được phân phối sai số khách quan trên người chưa từng gặp.
2. **Temporal Cross-Session Split (Đánh giá hiệu chuẩn cá nhân):**
   - Với mỗi người trong tập Test:
     - `Session 1`: Dùng làm mốc hiệu chuẩn cá nhân ($\text{BP}_0, \text{PAT}_0, \text{Features}_0$).
     - `Session 2 & Session 3`: Dùng để kiểm tra dự đoán $\Delta\text{SBP}$ và $\Delta\text{DBP}$.
   - Tuyệt đối không xáo trộn ngẫu nhiên dữ liệu giữa các phiên đo.

### 9.2. Kế hoạch thống kê và Kiểm định giả thuyết
- **Chỉ số sai số:** $\text{MAE}$, $\text{RMSE}$, $\text{ME} \pm \text{STD}$ (tính riêng biệt cho SBP và DBP).
- **Bootstrap theo đối tượng (Subject-level Bootstrapping):**
  - Khi ước lượng khoảng tin cậy 95% (95% CI) cho MAE, phải tiến hành lấy mẫu lại có hoàn lại **theo từng người tham gia (`subject_id`)**, sau đó tính sai số trên toàn bộ các mẫu của người đó.
  - Tuyệt đối **KHÔNG bootstrap theo từng cửa sổ đo riêng rẽ**, vì điều đó vi phạm giả định độc lập quan sát (i.i.d).
- **Kiểm định giả thuyết (chưa khóa):**
  - Phép so sánh chính của RQ1 là mô hình PPG-only với mô hình PPG + PAT, cùng thuật toán và trên **cùng tập lần đo** có cả ECG và PPG đạt chất lượng (xem [RQ v0.2](../research_questions_v0.1.md), mục 4.C).
  - Hiệu ứng chính là chênh lệch MAE theo từng người; báo cáo trung bình và CI 95% bootstrap theo người. Wilcoxon signed-rank cặp theo người ($\alpha = 0.05$) là phân tích hỗ trợ.
  - SBP và DBP là hai phép kiểm định; cách hiệu chỉnh đa kiểm định (ví dụ Holm) phải chọn trước khi mở test.
  - Luôn báo cáo kèm baseline zero-change và SD của $\Delta\text{BP}$ tham chiếu.

---

## 10. Quản lý dữ liệu thiếu và Dữ liệu suy hao

- Trường hợp một lượt đo bị mất nhãn cuff (do lỗi máy đo bắp tay): Toàn bộ lượt đo đó bị hủy, không đưa vào tập huấn luyện hay kiểm thử.
- Trường hợp tín hiệu ECG bị nhiễu không bắt được đỉnh R nhưng PPG đạt chuẩn: lượt đo bị loại khỏi phép so sánh chính PPG-only vs PPG + PAT (để hai mô hình được đánh giá trên cùng tập), nhưng được giữ cho phân tích phụ PPG-only trên toàn bộ lượt đo. Ghi rõ tỷ lệ lượt đo mất ECG theo từng người, vì mất ECG không ngẫu nhiên có thể làm lệch kết quả.
- Không áp dụng phương pháp tự điền nhãn huyết áp bằng trung bình (imputation) cho biến đầu ra.

---

## 11. Rủi ro thực nghiệm và Phương án dự phòng

| Rủi ro kỹ thuật | Khả năng | Mức độ | Biện pháp phòng ngừa và xử lý |
|---|---|---|---|
| ECG đạo trình I nhiễu, SNR thấp | Cao | Cao | Điện cực dán Ag/AgCl đạo trình I qua hai tay (LA mặt lòng cổ tay trái, RA mặt lòng cổ tay phải, RL cẳng tay trái; mục 5.2); thiết kế lọc dải thông khoảng $0.5 - 40\text{ Hz}$ và khuếch đại vi sai có CMRR cao (thông số cụ thể theo AFE được chọn); so sánh điện cực khô với Ag/AgCl dùng gel theo [yêu cầu phần cứng V0](../../configs/hardware/hardware_requirements_for_V0.md). |
| Nhiễu trôi đường nền PPG do lỏng dây đeo | Trung bình | Trung bình | Bổ sung cơ chế hiển thị SQI trực quan trên giao diện thu thập; hướng dẫn kỹ thuật viên siết chặt vòng vừa đủ trước khi bắt đầu đếm ngược 60 giây. |
| Biên độ biến thiên huyết áp tự nhiên giữa các phiên quá nhỏ ($< 5\text{ mmHg}$) | Trung bình | Cao | Nghiệm pháp ở mục 6.4 và tiêu chí kiểm ở pilot (6.5), chỉ khi đã được duyệt đạo đức. |
| Người tham gia cử động tay trong khi đo | Cao | Trung bình | Tích hợp thuật toán tự động hủy lượt đo và yêu cầu đo lại nếu SQI tụt dưới ngưỡng cho phép. |

---

## 12. Danh mục việc cần nhóm và giảng viên xác nhận

> [!IMPORTANT]
> **Checklist trước khi hoàn thiện protocol v1.0:**
> 1. [x] Phân bổ tay/điện cực (mục 5.2): phương án A, ba điện cực LA cổ tay trái, RA cổ tay phải, RL cẳng tay trái; cực tính LA → ECGP (xác nhận 2026-10-23). Còn kiểm K3–K5 ở mục 5.4 khi có module.
> 2. [ ] Linh xác nhận cấu trúc gói dữ liệu nhị phân/JSON truyền từ thiết bị vào máy tính có trường lưu `subject_id`, `session_id`, `event_id` và timestamp vi giây.
> 3. [ ] Thống nhất nhãn hiệu và model máy đo huyết áp bắp tay đối chứng dùng trong phòng thí nghiệm.
> 4. [ ] Xin ý kiến giảng viên hướng dẫn về quy trình làm việc với hội đồng đạo đức trước khi tuyển tình nguyện viên.
> 5. [ ] Đối chiếu khác biệt sampling, timestamp lấy mẫu/FIFO/nhận gói, clock và marker cuff với packet schema; ghi commit và quyết định trước khi khóa giao diện.
> 6. [ ] Kiểm tra căn cứ cỡ mẫu, cửa sổ, SQI, kiểm định và mọi tiêu chí an toàn/vận động dự thảo; không dùng outline để tự triển khai đo trên người.
