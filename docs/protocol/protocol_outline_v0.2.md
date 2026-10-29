# Khung protocol nghiên cứu thực nghiệm (Protocol Outline), phiên bản v0.3

> **Phiên bản:** v0.3, thay cho v0.2 (bản trước nữa: [v0.1](protocol_outline_v0.1.md)). Tên file vẫn giữ `v0.2` để không làm gãy liên kết.
> **Người biên soạn:** Nguyễn Đức Huy
> **Vai trò:** Xử lý tín hiệu, PAT, thống kê, xây dựng protocol nghiên cứu
> **Ngày lập:** 2026-09-22. **Cập nhật:** 2026-10-14 (v0.1: đồng bộ với RQ v0.2, với yêu cầu phần cứng V0 và với nguồn bổ sung); 2026-10-21 (v0.2); 2026-10-22 (sửa theo review); 2026-10-29 (v0.3); 2026-10-30 (dẫn N7 cho dạng bài của M2; ngưỡng P2/R3 dùng các kịch bản δ khai báo trước).
> **Lưu ý:** Chưa thu dữ liệu trên người, và chỉ thu sau khi có phê duyệt đạo đức. Phân bổ tay và điện cực ở mục 5.1–5.2 đã được xác nhận về phần cứng ngày 2026-10-23. Các nghiệm pháp ở 6.4–6.5 chưa được hội đồng đạo đức duyệt. Những mục ghi "đề xuất của nhóm, chờ thầy/hội đồng" trong v0.3 là phương án mặc định mang đi xin ý kiến, chưa phải quyết định cuối cùng.

**Changelog v0.3 (2026-10-29):** chốt các mục thiết kế nghiên cứu còn mở để chuẩn bị hồ sơ đạo đức.

- Mục 3: mục tiêu 3 phiên, tối thiểu 2; khoảng cách và cửa sổ tối đa giữa các phiên; phiên nào cũng theo cùng một trình tự (M0, rồi M1–M4 nếu được duyệt).
- Mục 4: trần tuyển 25 người; tiêu chí chọn/loại chỉ còn một nguồn là phiếu sàng lọc, bỏ tiêu chí "nhịp xoang"; đo hai tay một lần khi sàng lọc.
- Mục 5.1: chỉ dùng điện cực Ag/AgCl trên người; tiêu chí chọn máy cuff; đổi tên bo MCU thành tên chung.
- Mục 6.4: endpoint chính của RQ1 tính trên mọi lần cuff hợp lệ ở phiên ≥ 2; trục thời gian của M2, M3, M4.
- Mục 6.5: P2 và R3 dùng cùng một thống kê (median |ΔSBP|), nhưng mỗi chỉ số có mốc so sánh riêng.
- Mục 9.1: LOSO lồng. Mục 10: quy tắc cho lượt đo bị dừng vì an toàn.
- Bổ sung cùng ngày theo RQ v0.4 (đề xuất, chờ thầy): mục 9.1 thêm dự đoán vòng ngoài cho các lần cuff nghiệm pháp ở phiên 1, chỉ dùng cho RQ2b; mục 9.2 dẫn về RQ mục 4.E cho tiêu chí kết luận, đa kiểm định và δ.
- Bổ sung cùng ngày: bỏ M3 (ngâm chân nước lạnh) và M4 (đạp xe tư thế ngồi) vì khó thực hiện ở phòng thí nghiệm của nhóm. Bộ nghiệm pháp còn M0–M2 và không thay bằng nghiệm pháp mới trong hồ sơ lần này (6.4, mục "Dự phòng"). Các mục sửa theo: 3; 4.2–4.3 (bỏ L9 cũ, L10 đổi thành L9); 5.2–5.4; 6.4 (nhịp thở của M1; dạng bài, thời lượng và cách kiểm mức tham gia của M2; thứ tự và thời gian nghỉ; số lần cuff; thời lượng buổi; quy tắc nếu xin sửa đổi để thêm nghiệm pháp); 6.5 (phải đặt lại ngưỡng P2/R3, đề xuất suy ngưỡng từ mô phỏng độ nhạy); 7.3; 9.1; 10–12.

**Changelog v0.2 (2026-10-21, Huy):**

- Mục 5 viết lại theo thiết bị V1-module (Phần A của `custom_board_proposal.md`): bo cổ tay MAX30101/BMI270, bo đế ESP32-S3 + MAX30001, USB nối tới laptop chạy pin, điện cực dán Ag/AgCl đạo trình I giữa hai cổ tay (chốt 2026-10-23; bản nháp đầu của v0.2 ghi cổ tay–ngón tay). Bỏ cấu hình ngón tay chạm điện cực mặt trên của v0.1.
- Thêm bảng phân bổ tay/điện cực (5.2), phần chi dùng cho từng nghiệm pháp, và phần kiểm tra xung đột có kết quả (5.4).
- 6.2: thêm nút `t0`. 6.3: cập nhật AFE của V1-module và độ lệch có hệ thống giữa các phương án foot.
- Thêm 6.4 về nghiệm pháp tạo ΔBP (có nguồn cho hướng thay đổi) và 6.5 về tiêu chí biên độ ΔBP cho pilot (đề xuất, khóa trước pilot).
- Mục 3, 11, 12 sửa theo các thay đổi trên. Mục 1 chỉ bỏ chữ "trong Tuần 1" ở tuyên bố không thu dữ liệu. Mục 2, 4, 7–10 giữ nguyên như v0.1.

**Changelog 2026-10-22 (Huy, sửa theo review độc lập Tuần 5):**

- 5.1: MAX30101 là module PPG nhóm đã chọn. Số điện cực và việc dùng điện cực khô trên người được ghi là chờ quyết định. Khôi phục hai ý của v0.1 bị mất khi viết lại mục 5: ghi chú Cohen 2025 về sai số cuff truyền vào hiệu chuẩn, và yêu cầu chốt quy trình đo hai tay trước khi thu chính.
- 5.3, 6.4: ghi rõ mâu thuẫn chưa giải quyết về thời điểm nói ở M2 và về thời điểm của cửa sổ tín hiệu ở M4.
- 5.4: đổi tên quy tắc R1–R6 thành K1–K6 để không trùng với dấu hiệu R2/R3/R5 của kế hoạch 28 tuần; K3 thêm M1, M2, M4 (chưa đánh giá); K4 ghi rằng tay đeo cuff luôn mang một điện cực; K6 tách M3/M4; viết lại kết luận cho đúng trạng thái.
- 6.4: M3 thêm yếu tố nhiễu là co mạch ngoại vi; M4 ghi rằng hướng thay đổi ở pha hồi phục chưa chắc; đổi tên "ESH 2023" thành Stergiou 2023; ghi rằng Carroll 2012 và Jern 1991 chỉ ủng hộ gián tiếp; bỏ Fu 2002 (nguồn yếu, M5 đã bị loại).
- 6.5: ghi rằng định nghĩa P2 phải trùng với kịch bản bài báo.

---

## 1. Tuyên bố phạm vi và tính chất nghiên cứu

> [!IMPORTANT]
> **Tuyên bố pháp lý và y đức:**
> 1. Thiết bị đang phát triển trong dự án này là **nguyên mẫu nghiên cứu học thuật (exploratory research prototype)**, hoàn toàn **không phải thiết bị y tế**, và không được dùng cho bất kỳ mục đích chẩn đoán lâm sàng, sàng lọc hay can thiệp điều trị y tế nào.
> 2. Tài liệu này là **khung phác thảo phương pháp luận (protocol outline)**, phục vụ thiết kế kỹ thuật. **Không tuyển tình nguyện viên hoặc thu thập dữ liệu trên người trước khi có phê duyệt.** Chỉ được thu thập dữ liệu sau khi đề cương đạo đức hoàn chỉnh được phê duyệt chính thức.

---

## 2. Mục tiêu nghiên cứu (Research Objectives)

1. **Mục tiêu kỹ thuật:** Thiết lập quy trình chuẩn hóa để thu đồng thời tín hiệu ECG và PPG tại cổ tay với đồng bộ thời gian chính xác, kèm đo huyết áp đối chứng bằng máy đo bắp tay đạt chuẩn lâm sàng.
2. **Mục tiêu khoa học:**
   - Đánh giá khả năng ước lượng biến thiên huyết áp ($\Delta\text{SBP}$, $\Delta\text{DBP}$) ở các phiên đo độc lập (cross-session), sau khi đã hiệu chuẩn ban đầu cho từng người.
   - So sánh định lượng phần đóng góp khi bổ sung ECG/PAT với khi chỉ dùng đặc trưng hình thái PPG.
   - Kiểm chứng bằng thực nghiệm độ bền vững của mô hình khi chia dữ liệu theo các cách nghiêm ngặt, chống rò rỉ dữ liệu.

---

## 3. Thiết kế nghiên cứu (Study Design)

- **Hình thức:** nghiên cứu thực nghiệm quan sát (observational prospective study), đo lặp lại theo thời gian (repeated-measures longitudinal design).
- **Cấu trúc phiên đo (chốt 2026-10-29; cửa sổ tối đa là đề xuất của nhóm, chờ thầy/hội đồng):** mục tiêu là 3 phiên độc lập (`session_id`) cho mỗi người, tối thiểu 2. Người có ≥ 2 phiên hợp lệ vẫn được đưa vào phân tích RQ1. Phiên 2 cách phiên 1 ít nhất 1 ngày, và mọi phiên nằm trong 4 tuần kể từ phiên 1. Con số 4 tuần chưa có nguồn; nhóm chọn theo lịch thu Tuần 12–18. Không có hai phiên nào cùng ngày. Giờ bắt đầu phiên được ghi vào metadata; các phiên không bắt buộc cùng khung giờ.
  - **Phiên 1 (Calibration Session):** mốc hiệu chuẩn $\text{BP}_0$ là trung bình các lần cuff M0 hợp lệ của phiên 1. $\text{PAT}_0$ và đặc trưng nền lấy từ cửa sổ của chính các lần cuff M0 đó.
  - **Phiên 2 trở đi (Evaluation Sessions):** dùng để đánh giá khả năng theo dõi $\Delta\text{BP}$ ở các phiên sau (endpoint ở mục 6.4).
  - Phiên nào cũng theo cùng một trình tự: nghỉ ổn định (6.1), M0, rồi M1, M2 (6.4) nếu hội đồng đã duyệt và người tham gia đồng ý với từng nghiệm pháp.
- **Hệ quả cần lưu ý:** Ở người trẻ khỏe mạnh đo lúc nghỉ, $\Delta\text{BP}$ giữa các phiên có thể nhỏ. Khi đó baseline zero-change (dự đoán $\Delta\text{BP} = 0$) đã có sai số thấp, và mô hình khó cho thấy khác biệt. Mukkamala et al. (2021, [10.1161/HYPERTENSIONAHA.121.17747](https://doi.org/10.1161/HYPERTENSIONAHA.121.17747)) chỉ ra rằng thiết bị có hiệu chuẩn có thể trông chính xác chỉ vì BP ít thay đổi. Vì vậy, cùng với sai số của mô hình, phải báo cáo sai số của baseline chỉ dùng BP hiệu chuẩn và độ lệch chuẩn của $\Delta\text{BP}$ tham chiếu.

---

## 4. Đối tượng tham gia dự kiến và tiêu chí lựa chọn

### 4.1. Cỡ mẫu dự kiến
- Mục tiêu là **≥ 15 người đạt chuẩn** (định nghĩa ở [kịch bản bài báo](../paper_scenarios_v0.1.md)). Tuyển tối đa **25** tình nguyện viên khỏe mạnh (sinh viên hoặc cán bộ tại trường, 18–35 tuổi) để bù cho người bỏ cuộc hoặc mất ECG. Trần 25 là đề xuất của nhóm (2026-10-29), chưa có nguồn, chờ thầy/hội đồng. Trần tuyển được ghi trong hồ sơ, nên muốn tăng về sau thì phải xin sửa đổi. Trần 25 tính mọi người tham gia, kể cả người làm pilot. Mục tiêu ≥ 15 người đạt chuẩn chỉ tính người ngoài pilot, vì người có dữ liệu đã dùng để khóa các lựa chọn thì không vào vòng đánh giá (mục 9.1).
- Đây là cỡ mẫu khả thi cho giai đoạn thử nghiệm nguyên mẫu (feasibility), chưa dựa trên phân tích power. Với 2–3 phiên mỗi người và ít nhất 2 lần cuff hợp lệ mỗi phiên ([RQ](../research_questions_v0.1.md), mục 4.G), 15 người cho tối thiểu $15 \times 2 \times 2 = 60$ lần cuff hợp lệ, chưa kể cuff nghiệm pháp. Các lần đo này lặp lại trên cùng một người nên **không phải quan sát độc lập**. Đơn vị cho kiểm định cặp là người. Cỡ mẫu chính thức cần được tính lại từ dữ liệu pilot.

Tiêu chí chọn và loại (chốt 2026-10-29) chỉ có một nguồn là
[eligibility_screening_v0.1.md](../ethics/eligibility_screening_v0.1.md): tiêu chí chọn ở
mục 1, tiêu chí loại L1–L9, người tham gia tự khai. Mục 4.2–4.3 chỉ tóm tắt; nếu có chỗ khác
nhau thì theo phiếu sàng lọc. Bỏ tiêu chí "nhịp tim xoang bình thường" của v0.1–v0.2, vì tự
khai thì không kiểm được và nhóm không có người đánh giá ECG lâm sàng. Độ tuổi, L7, L8 và
ngưỡng chênh hai tay là đề xuất của nhóm, cần thầy/bác sĩ xác nhận.

### 4.2. Tiêu chí lựa chọn (Inclusion Criteria)
- 18–35 tuổi, đủ năng lực tự quyết định việc tham gia. Giới hạn tuổi là đề xuất của nhóm, chưa có nguồn, nhằm giữ quần thể đồng nhất và giảm rủi ro chung khi làm nghiệm pháp.
- Tự nguyện ký phiếu đồng thuận, sau khi đã nhận phiếu thông tin ít nhất 24 giờ.
- Tự khai không có bệnh tim mạch đã được chẩn đoán.
- Ngồi yên được suốt buổi đo và tham gia được ít nhất 2 buổi (tiêu chí 4 của phiếu sàng lọc).

### 4.3. Tiêu chí loại trừ (Exclusion Criteria)
Tiêu chí loại trừ là L1–L9 của phiếu sàng lọc:

- L1: bệnh tim mạch, hoặc tăng/hạ huyết áp đã được chẩn đoán;
- L2: thuốc tim mạch hoặc thuốc thần kinh giao cảm;
- L3: máy tạo nhịp hoặc thiết bị cấy ghép;
- L4: mang thai;
- L5: tổn thương da ở vị trí đeo thiết bị, dán điện cực hoặc quấn cuff;
- L6: dị ứng băng dán, gel hoặc kim loại;
- L7: không đo được huyết áp ở tay phải;
- L8: ngất, động kinh, khó thở khi gắng sức;
- L9: cà phê, trà, thuốc lá hoặc vận động mạnh trong 2 giờ trước buổi đo (hoãn buổi).

L9 cũ (Raynaud, bệnh bàn chân; chỉ cần cho M3) đã bỏ ngày 2026-10-29 cùng với M3. L10 cũ
đổi số thành L9.

**Đo hai tay (chốt 2026-10-29; ngưỡng là đề xuất, chờ thầy/bác sĩ):** ở buổi 1, trước khi gắn
thiết bị, đo huyết áp mỗi tay một lần bằng máy cuff của nghiên cứu. Hai lần đo này chỉ để sàng
lọc; ngoài hai lần này, mọi lần đo cuff đều ở tay phải (K1, mục 5.4) và không đổi bên. Nếu SBP hai tay chênh nhau ≥ 10 mmHg thì vẫn đo ở tay phải,
gắn cờ `interarm_diff` trong metadata, báo số người có cờ và làm phân tích độ nhạy loại những
người này. Ngưỡng 10 mmHg chưa có nguồn. Hai lần đo này không phải nhãn.

---

## 5. Bố trí thiết bị, điện cực và tư thế đo

> [!IMPORTANT]
> **Mục 5 và mục 6.4–6.5: đề xuất ngày 2026-10-21.** Phân bổ tay, số lượng và vị trí điện
> cực, cực tính (5.1, 5.2) đã được chốt về phần cứng ngày 2026-10-23. Các nghiệm pháp ở 6.4
> chưa được hội đồng đạo đức duyệt. Chưa đo trên người nào, kể cả thành viên nhóm. Kiểm tra
> xung đột ở 5.4 mới là kiểm tra trên giấy; các dòng "chưa kiểm chứng" cần bản ghi bring-up/G2.

### 5.1. Thiết bị V1-module

Theo [custom_board_proposal.md, Phần A](../../configs/hardware/custom_board_proposal.md):

- **Bo cảm biến cổ tay** kích thước 40,4 × 31,5 mm, gắn dây velcro 20 mm. Bo gồm PPG
  SparkFun MAX30101 (SEN-16474, ba kênh xanh lá, đỏ, IR; **đã chọn** 2026-10-22) và IMU
  BMI270. V1 không dùng FSR (chốt 2026-10-23). Bo nối với bo đế bằng cáp dẹt 16 dây, dài dự
  kiến 20–30 cm. Pin map chuẩn là KiCad V1-module (`configs/hardware/custom_board_proposal.md`
  A.7, chốt 2026-10-23); danh sách mua ở `hardware/bom/purchase_list_v1_module.md`.
- **Bo đế đặt trên bàn:** gồm bo MCU ESP32-S3 (loại bo cụ thể ở
  [custom_board_proposal.md](../../configs/hardware/custom_board_proposal.md) A.2), breakout
  ProtoCentral MAX30001 (ECG) và nút `t0`. Nút này đánh dấu lúc bắt đầu bơm cuff, trên cùng
  đồng hồ `esp_timer`.
- **Nguồn và dữ liệu:** bo MCU nối với laptop bằng một cáp USB; laptop **chạy pin, rút sạc**.
  Khi người tham gia đang đeo thiết bị, không thiết bị nào được nối điện lưới
  ([quy tắc an toàn](../ethics/session_safety_stopping_v0.1.md)).
- **ECG:** dùng **ba** điện cực dán Ag/AgCl có gel, loại dùng một lần (LA, RA và RL tham
  chiếu), nối qua cáp 3 điện cực đi kèm kit và jack 3,5 mm của breakout. Đạo trình I lấy giữa
  **hai cổ tay** (chốt 2026-10-23, vị trí ở 5.2). **Trên người chỉ dùng cấu hình này**
  (chốt 2026-10-29). Điện cực khô
  ([Hai_phuong_an_dien_cuc_ECG.md](../../hardware/Hai_phuong_an_dien_cuc_ECG.md)) và cấu hình
  hai điện cực (bỏ RL, bật lead bias nội) không thuộc hồ sơ đạo đức lần này. Hai phương án này
  chỉ được thử trên bàn, không có người, hoặc đưa vào sau pilot bằng sửa đổi đạo đức; khi đó
  phải thêm chúng vào phiếu thông tin, phiếu đồng thuận và L6.
- **Cuff (tiêu chí chốt 2026-10-29, đề xuất của nhóm, chờ thầy):** nhãn chính lấy từ máy đo
  bắp tay tự động (dao động ký) có kết quả validation đã công bố cho đúng model đó. Nếu mượn
  được thiết bị đo huyết áp liên tục thì thiết bị này chỉ làm tham chiếu phụ, không thay nhãn
  cuff (mục 7.1). Model chưa được chọn (mục 12). Phải chọn trước khi nộp hồ sơ, vì dải cỡ vòng
  bít quyết định tiêu chí loại theo chu vi bắp tay. Không coi "cùng hãng" là đã validate. Sai
  số của máy cuff truyền thẳng vào nhãn và vào mốc hiệu chuẩn $\text{BP}_0$. AHA scientific
  statement về thiết bị cuffless (Cohen et al., 2025,
  [10.1161/HYP.0000000000000254](https://doi.org/10.1161/HYP.0000000000000254)) nhấn mạnh
  rằng độ chính xác của thiết bị cuffless phụ thuộc mạnh vào cuff dùng để hiệu chuẩn. Quy
  trình đo hai tay ở mục 4 (chốt 2026-10-29). Ngoài hai lần đo sàng lọc đó, cuff luôn ở tay
  phải, không đổi bên giữa các lượt đo.

So với v0.1, bản này bỏ cấu hình "điện cực mặt đáy vòng + ngón tay chạm điện cực mặt
trên". Điện cực dán không cần người tham gia chủ động chạm, nên ECG không phụ thuộc vào việc
giữ ngón tay trong lúc cuff bơm.

### 5.2. Bảng phân bổ (phương án A, đề xuất chính)

| Thành phần | Vị trí | Lý do / ghi chú |
| --- | --- | --- |
| Bo PPG cổ tay | Mặt lưng cổ tay **trái**, cách mỏm trâm trụ khoảng 1,5–2,0 cm (như v0.1); vị trí cố định cho mọi người, tay thuận ghi vào metadata | Không đổi bên giữa những người tham gia hay giữa các lượt đo, để tránh thêm biến số |
| Cuff đối chứng | Bắp tay **phải**, ngang tim, vòng bít đúng cỡ | Khác tay với PPG (5.4, K1) |
| Điện cực LA (ECGP) | Cổ tay **trái**, mặt lòng, không nằm dưới dây đeo hay bo PPG | Phía tay trái của đạo trình I |
| Điện cực RA (ECGN) | Cổ tay **phải**, mặt lòng | Phía tay phải, nằm xa cuff ở bắp tay. Điện cực 4 × 3,3 cm dán vừa, không cần loại nhỏ dành cho ngón tay |
| Điện cực RL (tham chiếu, VCM) | Cẳng tay **trái**, mặt lòng, cách LA khoảng 5 cm về phía khuỷu | Mặt lòng cổ tay không đủ chỗ cho hai miếng dán; tay đeo cuff chỉ mang một dây điện cực |
| Cực tính | Tay trái là cực dương của đạo trình I: LA → ECGP (vòng giữa, ring của jack), RA → ECGN (đầu, tip), RL → sleeve → VCM qua R3 (theo schematic `pc_max30001_brk_v1.0`); tắt lead bias nội (`custom_board_proposal.md` A.2) | `ecg_polarity = 1`. Màu nắp đầu bấm khác nhau tùy lô cáp, nên phải đo thông mạch giữa đầu bấm và tip/ring/sleeve trước buổi đo đầu tiên |
| Cáp | Cáp dẹt PPG và dây điện cực đi dọc cẳng tay, cố định bằng băng dính y tế, không kéo căng bo PPG | Giảm nhiễu do cáp lay động |
| Tư thế | Như mục 5.3 | |

**Phương án B cũ** (điện cực ở cổ tay phải và ngón tay trái) không còn dùng. Phương án A đã
dời RA từ ngón trỏ sang cổ tay phải, nên không còn vướng việc dán điện cực lên ngón tay. Chiều
dài dây, và việc dây không kéo bo PPG, sẽ được kiểm trên thành viên nhóm ở G2 (K5).

**Chi dùng cho từng nghiệm pháp** (chi tiết ở 6.4):

| Nghiệm pháp | Chi hoạt động | Tay trái (PPG + LA + RL) | Tay phải (cuff + RA) |
| --- | --- | --- | --- |
| M0 Nghỉ ngồi | Không | Yên trên bàn | Yên trên bàn |
| M1 Thở chậm có hướng dẫn | Hô hấp | Yên | Yên |
| M2 Tính nhẩm | Không (nhẩm im lặng; chỉ nói đáp án ngoài khoảng im lặng ở 6.4) | Yên | Yên |
| ~~M3 Ngâm bàn chân vào nước lạnh~~ | Một bàn chân | Bỏ 2026-10-29 (6.4) | Bỏ |
| ~~M4 Đạp xe nhẹ tư thế ngồi~~ | Hai chân | Bỏ 2026-10-29 (6.4) | Bỏ |
| ~~M5 Bóp tay tĩnh~~ | Một tay | Loại (5.4) | Loại (5.4) |

### 5.3. Tư thế người tham gia
- Trong mọi nghiệm pháp, người tham gia ngồi tựa lưng thoải mái trên ghế có tựa, hai bàn chân đặt phẳng trên sàn, hai chân không bắt chéo.
- Hai cẳng tay đặt thả lỏng trên mặt bàn có đệm êm, sao cho cổ tay đeo thiết bị và vùng đo ở bắp tay nằm **ngang mức tim**.
- Không nói chuyện, không cử động ngón tay và không đổi tư thế trong suốt lúc ghi tín hiệu và lúc cuff bơm, xả.
- M2 không vi phạm quy tắc trên, vì người tham gia nhẩm im lặng và chỉ nói đáp án ngoài
  khoảng im lặng (trục thời gian ở 6.4, chốt 2026-10-29). Mâu thuẫn ghi nhận ngày 2026-10-22
  đã được đóng.

### 5.4. Kiểm tra xung đột (2026-10-21, trên giấy; sửa 2026-10-22)

Các quy tắc mang mã K1–K6 (trước đây là R1–R6) để không trùng với các dấu hiệu R2/R3/R5 của
kế hoạch 28 tuần.

| # | Quy tắc | Kết quả với phương án A | Còn phải làm |
| --- | --- | --- | --- |
| K1 | Cuff không cùng tay đeo PPG | **Đạt:** cuff ở tay phải, PPG ở tay trái; lần đo tay trái lúc sàng lọc diễn ra trước khi gắn thiết bị | — |
| K2 | Không nghiệm pháp nào làm chuyển động tay đeo PPG | **Đạt trên giấy** cho M0–M2. **Không đạt** cho M5 nếu bóp bằng tay trái. M3, M4 đã bỏ (2026-10-29), không còn phải xét | Dùng IMU BMI270 để kiểm chuyển động thực tế |
| K3 | Tránh nhiễu cơ trên chi gắn điện cực ECG | Đạo trình I cần điện cực ở **cả hai tay**, nên mọi hoạt động cơ ở tay đều gây nhiễu. **Không đạt** cho M5 dù bóp bằng tay nào, nên loại M5. **Chưa kiểm chứng** cho lúc cuff bơm (cơ tay phải bị căng). **Chưa đánh giá:** M1 (thở sâu làm trôi đường nền, nên trong phân tích phụ có lọc SQI ở mục 7.3, cửa sổ M1 có thể bị loại có hệ thống; phân tích chính không lọc theo SQI) và M2 (nói, cơ hô hấp) | Xem ECG trong M1, M2 và lúc cuff bơm ở G2 |
| K4 | ECG có tín hiệu tại thời điểm đo cuff | **Đạt về thiết kế:** điện cực dán, không cần chạm chủ động. Với đạo trình I, tay đeo cuff **luôn** mang một điện cực (RA ở cổ tay phải), và đổi vị trí điện cực cũng không khắc phục được điều này. Pha cuff bơm được loại khỏi phân tích chính (6.2, giai đoạn 2). **Chưa kiểm chứng** ảnh hưởng của cuff bơm lên ECG | Bản ghi có cuff bơm ở G2, sau khi được phép |
| K5 | Dây điện cực và cáp không đè hay kéo bo PPG | Chưa kiểm (chưa có module). Tay trái mang cáp dẹt PPG và hai dây LA, RL | Kiểm trên thành viên nhóm ở lần đeo đầu tiên (G2), trước buổi pilot đầu tiên; không dùng tay giả (chốt 2026-10-29) |
| K6 | Chân dùng cho nghiệm pháp không ảnh hưởng tay | **Không còn áp dụng:** sau khi bỏ M3, M4 (2026-10-29), không còn nghiệm pháp nào dùng chân. Nếu sau này xin sửa đổi để thêm nghiệm pháp dùng chân (6.4, "Dự phòng") thì xét lại | — |

Kết luận (trên giấy, 2026-10-22; sửa 2026-10-29 khi bỏ M3, M4):

- K1 đạt. M5 bị loại. M3, M4 bị bỏ vì khó thực hiện ở phòng thí nghiệm (6.4).
- K2 đạt trên giấy cho M0–M2.
- K3, K4, K5 chưa kiểm chứng; riêng K3 còn chưa đánh giá M1, M2.
- Vì vậy **chưa thể nói** phương án A không còn xung đột với M0–M2; cần có bản ghi G2. Trục
  thời gian M2 đã có ở 6.4 (2026-10-29).

---

## 6. Quy trình thu thập dữ liệu và đồng bộ tín hiệu

### 6.1. Quy trình nghỉ ổn định trước khi đo
1. Người tham gia đến phòng đo và ngồi nghỉ yên tĩnh ít nhất **10 phút**, trong phòng có nhiệt độ ổn định ($24 - 26^\circ\text{C}$, đề xuất, chưa có nguồn).
2. Giải thích lại quy trình thao tác và kiểm tra độ vừa vặn của thiết bị.
3. Không uống cà phê, trà, không hút thuốc và không vận động mạnh trong vòng 2 giờ trước phiên đo (đề xuất, chưa có nguồn).
4. **Dòng LED PPG theo người** (chốt 2026-10-25). Ở buổi đầu của mỗi người, sau khi đeo bo cổ
   tay, chỉnh dòng LED của từng màu (xanh, đỏ, IR) để mức DC nằm trong khoảng 30–70% thang đo
   ADC (16 384 nA), không bão hòa và không tràn phần khử ánh sáng môi trường. Giá trị này được
   khóa cho người đó ở **mọi buổi sau**, để biên độ PPG giữa các buổi của cùng một người còn so
   sánh được (ΔBP cross-session). Firmware không tự chỉnh trong lúc ghi. Giá trị đang dùng được
   ghi vào trường `ppg_led_lock` của metadata phiên, và logger báo khi `0xD2` khác mã đã khóa.

   Lệnh chỉnh gửi từ PC (2026-10-25; Packet Schema V0.2 mục 13) là
   `scripts/device_command.py set-ppg-led`, chạy trong lúc `record --commands`. Mã tính theo
   bước 0,2 mA (với màu xanh là mã của mỗi nhánh), tối đa 127 (giới hạn tạm của firmware). Mỗi
   lệnh cấu hình lại chip, nên tạo một ranh giới chuỗi trong dữ liệu; dòng thật đang dùng nằm
   trong packet `0xD2` của luồng raw. Đoạn hiệu chuẩn và đoạn chạy với dòng mặc định ngay sau
   khởi động **không** thuộc cửa sổ đo: chỉ bắt đầu lượt đo sau khi `0xD3` báo xong với dòng
   đã khóa. Ở các buổi sau, PC gửi lại đúng các mã đã khóa ngay đầu phiên, vì firmware không
   lưu giá trị qua các lần khởi động. PC cũng gửi lại mỗi khi `SESSION_ID` đổi (MCU khởi động
   lại giữa buổi). Khoảng 30–70% là đề xuất kỹ thuật, **chưa có nguồn**.

   **Quy trình chỉnh ở buổi đầu (chốt 2026-10-29):** chỉnh tay bằng
   `device_command.py set-ppg-led`; mỗi lệnh tự được ghi vào nhật ký lệnh của `record`.
   1. Bắt đầu từ mã mặc định của bring-up: đỏ và IR là `0x24`, xanh là `0x12` mỗi nhánh
      (7,2 mA mỗi màu).
   2. Người tham gia ngồi yên. Ghi 10 s rồi đọc mức DC trung bình của từng màu, tính theo
      phần trăm thang đo.
   3. Với từng màu: nếu DC < 30% thì tăng một bước; nếu DC > 70% hoặc có mẫu bão hòa thì giảm
      một bước. Bước cố định là `0x08` cho đỏ và IR, `0x04` mỗi nhánh cho xanh (đều bằng
      1,6 mA mỗi màu). Không vượt trần hiện hành: `0x7F` theo Packet Schema V0.2 mục 13, hoặc
      trần thấp hơn sau bring-up; PC từ chối mọi mã vượt `0x7F`. Không xuống dưới mã nhỏ nhất:
      `0x04` cho đỏ và IR, `0x02` mỗi nhánh cho xanh (0,8 mA mỗi màu).
   4. Lặp tối đa 6 vòng. Màu nào đã chạm trần hoặc mã nhỏ nhất mà vẫn cần chỉnh tiếp thì dừng
      ở đó. Nếu vẫn chưa vào khoảng, dùng mã cuối cùng không bão hòa; nếu không có mã nào
      không bão hòa thì dùng mã nhỏ nhất. Cả hai trường hợp đều ghi "ngoài khoảng" vào metadata
      (`outside_dc_range`).
   5. Khóa mã của từng màu và ghi vào metadata phiên.

   **Buổi sau lệch thang (chốt 2026-10-29):** giữ nguyên mã đã khóa. Chỉ khi cửa sổ M0 đầu
   tiên có mẫu chạm trần ADC quá 5% thời gian thì mới chỉnh lại **một lần** theo quy trình
   trên. Lần chỉnh này được ghi là sai lệch protocol, và phiên đó mang cờ `led_readjusted`. Biên
   độ PPG của phiên đó không còn so được với phiên hiệu chuẩn, nên các lần cuff của phiên đó
   không vào phân tích chính; phân tích độ nhạy thì đưa chúng vào với đủ đặc trưng. Báo số
   phiên có cờ theo từng người. Nếu DC lệch khỏi khoảng mà không bão hòa thì không chỉnh.

### 6.2. Trình tự một lượt đo (Measurement Event)
Mỗi lượt đo (`event_id`) kéo dài khoảng $2.5 - 3\text{ phút}$ và gồm 3 giai đoạn:
1. **Giai đoạn 1: ghi tín hiệu trước khi đo cuff (Baseline Signal Window, $60\text{s}$):**
   - Thiết bị thu PPG và ECG đồng bộ, liên tục trong 60 giây trước khi bắt đầu bơm cuff. Toàn bộ 60 giây này được lưu để kiểm soát chất lượng và phân tích độ nhạy.
   - Đây là **cửa sổ tín hiệu ứng viên trước cuff**, không phải phép đo huyết áp đồng thời. Cửa sổ phân tích chính dự kiến là 20–30 giây ngay trước lúc bơm cuff. SQI, độ ổn định của nhịp tim/nhịp mạch và cờ chuyển động của cửa sổ đều được tính và lưu, nhưng phân tích chính không loại cửa sổ theo các chỉ số này; lọc theo SQI là phân tích phụ (7.3, sửa 2026-10-29). Phải lưu độ lệch thời gian giữa cuối cửa sổ tín hiệu và lúc máy cuff trả kết quả.
2. **Giai đoạn 2: bơm cuff đo huyết áp đối chứng ($45 - 60\text{s}$):**
   - **Bấm nút `t0` trên bo đế trước, rồi mới bấm máy đo bắp tay** (chốt 2026-10-29), để cửa sổ `[t0 − L, t0)` không dính phần đầu của pha bơm. Nút ghi sự kiện trên cùng đồng hồ `esp_timer` với ECG/PPG. Khi cuff xả xong, người vận hành ghi lúc kết thúc xả bằng lệnh đánh dấu sự kiện mã 2 (`CUFF_END`) gửi từ PC (`device_command.py`, Packet Schema V0.2 mục 13; chốt 2026-10-29). Mốc này là lúc thiết bị nhận được lệnh. Độ trễ từ PC tới thiết bị chưa được đo, nhưng mốc này vẫn đủ dùng ở mức giây; mốc cần chính xác tới ms vẫn là `t0`.
   - Tín hiệu thu trong giai đoạn này được gắn cờ cuff_inflating = True và không dùng làm đầu vào chính cho mô hình. ECG vẫn được ghi (nhờ điện cực dán) để kiểm K4 ở mục 5.4.
3. **Giai đoạn 3: ghi nhãn và nghỉ hồi phục ($30\text{s}$):**
   - Chép kết quả SBP, DBP và Pulse Rate từ màn hình máy đo đối chứng vào biểu mẫu nghiên cứu.
   - Nghỉ ít nhất 2 phút rồi mới làm lượt đo tiếp theo.

- **Phân tích độ nhạy ghép nhãn:** so sánh kết quả khi dùng cửa sổ 10, 20, 30 và 60 giây trước cuff, đồng thời làm riêng một phân tích loại các lượt không đạt tiêu chí plateau. Nếu kết quả thay đổi đáng kể theo cửa sổ thì phải báo cáo đó là bất định do nhãn không đồng thời. Không được chọn cửa sổ hậu nghiệm để có kết quả đẹp nhất.

### 6.3. Đồng bộ thời gian phần cứng giữa ECG và PPG
- ECG và PPG cần dùng chung một quy chiếu thời gian, hoặc có ánh xạ clock đã được kiểm chứng. Không mặc định rằng hai AFE lấy mẫu đồng thời chỉ vì chúng dùng chung MCU.
- V1-module dùng MAX30001 (ECG) và MAX30101 (PPG). ECG chốt ở 512 sps (`custom_board_proposal.md` Phần A.2, 2026-10-23). PPG chốt chế độ multi-LED ba khe, 200 sps mỗi khe, `SMP_AVE = 1` (A.6 mục 3, 2026-10-24). Độ rộng xung còn mở. Bảng các tốc độ cấu hình được nằm ở [interface_power_sampling_v0.md, mục 4](../../configs/hardware/interface_power_sampling_v0.md). Tần số cuối cùng phải là giá trị mà từng AFE hỗ trợ theo datasheet, và phải được đo lại trên thiết bị.
- Về độ phân giải thời gian: mỗi mẫu ECG ở 512 sps dài khoảng 1,95 ms, mỗi mẫu PPG ở 200 sps dài 5 ms. Sai số định vị R peak và PPG foot, cộng với sai số đồng bộ giữa hai kênh, đi thẳng vào PAT. Vì vậy cần đo jitter/offset thực tế ([kế hoạch đo 10 phút](../../hardware/test_reports/sync_10min_test_plan.md)) trước khi diễn giải các thay đổi PAT cỡ vài ms. Các phương pháp foot khác nhau lệch nhau có hệ thống hàng chục ms trên cùng một xung ([Tuần 5](week05_fiducials_pat_validity.md)), nên không trộn phương pháp trong một phân tích.
- Phải phân biệt timestamp **lấy mẫu**, timestamp **đọc FIFO** và thời điểm **nhận gói tại PC**. Counter của MCU không tự loại bỏ được độ trễ của sensor/FIFO, sai lệch clock hay jitter. Cần ghi lại clock, đơn vị, tần số của từng kênh, các lần mất mẫu, và cách suy ra thời điểm của từng mẫu từ timestamp của mẫu đầu gói.
- Marker bắt đầu bơm cuff (`t0`) phải dùng cùng clock, hoặc có ánh xạ kiểm tra được. Không dịch PPG cho trùng với đỉnh R, vì làm vậy sẽ mất chính độ trễ cần để tính PAT.

### 6.4. Nghiệm pháp tạo ΔBP (đề xuất, chưa được hội đồng đạo đức duyệt)

Mục đích chung là mở rộng dải ΔBP so với mốc hiệu chuẩn. Đo lúc nghỉ ở người trẻ cho ΔBP
nhỏ, nên baseline zero-change khó bị vượt (mục 3). Mukkamala et al. 2021
([10.1161/HYPERTENSIONAHA.121.17747](https://doi.org/10.1161/HYPERTENSIONAHA.121.17747),
toàn văn, [tổng quan bổ sung S2](../literature/literature_update_2026-10-14.md)) đề xuất
đánh giá thiết bị có hiệu chuẩn bằng ít nhất ba can thiệp làm BP thay đổi.

**Bộ nghiệm pháp từ 2026-10-29: M0, M1, M2.** M3 (ngâm chân nước lạnh) và M4 (đạp xe tư thế
ngồi) bị bỏ vì khó thực hiện ở phòng thí nghiệm của nhóm. Bộ còn lại chỉ có hai can thiệp: M1
làm BP giảm nhẹ, M2 làm BP tăng. Kể cả khi cộng thêm biến thiên tự nhiên giữa các ngày, bộ này
vẫn chưa đạt mức ít nhất ba can thiệp mà Mukkamala 2021 đề xuất. Đây là giới hạn phải nêu trong
bài báo. Dải ΔBP dự kiến sẽ hẹp hơn, nên RQ1 kém nhạy hơn và khả năng kết quả rơi vào "chưa kết
luận" tăng lên ([RQ](../research_questions_v0.1.md) mục 4.E–4.F). Hồ sơ lần này không thay
bằng nghiệm pháp mới; hướng bổ sung nằm ở mục "Dự phòng" bên dưới.

**Endpoint chính của RQ1 (đề xuất của nhóm 2026-10-29, chờ thầy xác nhận):**

- Tập đánh giá gồm mọi lần cuff hợp lệ ở phiên ≥ 2, cả M0, M1 lẫn M2.
- Với mỗi lần cuff, $\Delta\text{BP}$ = giá trị cuff − $\text{BP}_0$, trong đó
  $\text{BP}_0$ là trung bình các lần cuff M0 hợp lệ của phiên 1 (mục 3).
- Nghiệm pháp là biến phân tầng: sai số được báo cả gộp chung lẫn theo từng nghiệm pháp.
- Phân tích phụ định trước: chỉ dùng các lần cuff M0 ở phiên ≥ 2, tức ΔBP giữa các phiên lúc
  nghỉ.
- Với người được đánh giá, phiên 1 chỉ cung cấp $\text{BP}_0$, $\text{PAT}_0$ và đặc trưng
  nền, đều lấy từ M0. Các lần cuff nghiệm pháp của phiên 1 không dùng để fit hệ số riêng cho
  người đó và không vào tập đánh giá.

Nghiệm pháp được thêm vào để RQ1 đủ nhạy. Một endpoint chỉ dùng M0 sẽ làm mất tác dụng đó, nên
cách này chỉ được giữ làm phân tích phụ.

"Mức đã đọc" của các nguồn: tất cả là **abstract** (Europe PMC, đọc ngày 2026-10-21), trừ khi
có ghi khác. Không nguồn nào ở đây cho biết biên độ ΔBP ở đúng quần thể và protocol của nhóm.

| Mã | Nghiệm pháp | Mục đích | Hướng BP dự kiến và nguồn | Thời lượng | Rủi ro | Dừng khi |
| --- | --- | --- | --- | --- | --- | --- |
| M0 | Nghỉ ngồi | Mốc hiệu chuẩn, so sánh | Ổn định (mục 6.1) | ≥ 10 phút nghỉ, rồi ≥ 2 lượt cuff | Tối thiểu | Quy tắc chung |
| M1 | Thở chậm có hướng dẫn | ΔBP âm | **Giảm.** Adler 2019 ([10.1152/japplphysiol.00442.2019](https://doi.org/10.1152/japplphysiol.00442.2019)): 22 người trẻ có huyết áp bình thường thở chậm 15 phút theo hướng dẫn của thiết bị RESPeRATE; SBP giảm 3,2 ± 0,8 mmHg (đo ở 5 phút cuối). Biên độ nhỏ, có thể không vượt sai số cuff | 15 phút theo nguồn; nhịp 6 lần mỗi phút là đề xuất của nhóm 2026-10-29, **chưa có nguồn** (abstract không nêu nhịp) | Chóng mặt, tê đầu ngón | Chóng mặt, tê, khó chịu khi thở |
| M2 | Tính nhẩm im lặng: trừ liên tiếp 13 từ một số có bốn chữ số do người vận hành đọc, cuối cùng nói ra số đạt được. Dạng bài theo Hove et al. 2024 ([10.3389/fmedt.2024.1464473](https://doi.org/10.3389/fmedt.2024.1464473), N7, đọc đoạn Methods ngày 2026-10-30): trừ liên tiếp 13 từ 1.079 trong 5 phút, có báo lỗi và metronome 2 Hz để tạo căng thẳng. Nhóm làm bản im lặng và không báo lỗi trong lúc đo, nên đáp ứng BP có thể yếu hơn; bản im lặng chưa có nguồn | ΔBP dương do stress tâm lý | **Tăng** (nguồn chỉ **ủng hộ gián tiếp**). Carroll 2012 ([10.1111/j.1469-8986.2012.01463.x](https://doi.org/10.1111/j.1469-8986.2012.01463.x)) đo phản ứng SBP/DBP với tính nhẩm (431 người, 63 tuổi; câu hỏi nghiên cứu về tiên lượng). Jern 1991 ([10.1042/cs0810593](https://doi.org/10.1042/cs0810593)): phản ứng HR/BP lặp lại tốt ở 14 nam giới trẻ. Abstract không nêu chiều hay biên độ thay đổi ở người trẻ, nên cần nguồn trực tiếp. Stress cũng làm đổi PEP, nên PAT có thể đổi trong khi BP không đổi ([RQ](../research_questions_v0.1.md), mục F) | Khoảng 3 phút (đề xuất của nhóm 2026-10-29, suy từ trục thời gian bên dưới; **chưa có nguồn**) | Căng thẳng, lo âu | Người tham gia muốn dừng, hoặc căng thẳng rõ |
| ~~M3~~ | ~~Ngâm một bàn chân vào nước lạnh~~ | — | Tăng SBP và DBP (Korhonen 2006, [10.3402/ijch.v65i2.18090](https://doi.org/10.3402/ijch.v65i2.18090): cold pressor ở tay và ở chân; Velasco 1997, [10.1097/00045391-199701000-00008](https://doi.org/10.1097/00045391-199701000-00008)). Co mạch ngoại vi do lạnh có thể làm đổi PPG và PAT độc lập với BP | — | — | **Bỏ 2026-10-29:** khó thực hiện ở phòng thí nghiệm của nhóm; trần thời lượng ngâm và nhiệt độ nước cũng chưa có nguồn |
| ~~M4~~ | ~~Đạp xe nhẹ tư thế ngồi, đo trong pha hồi phục~~ | — | Tăng khi gắng sức; ở pha hồi phục thì chưa chắc (Stergiou 2023, [10.1097/HJH.0000000000003483](https://doi.org/10.1097/HJH.0000000000003483); Mukkamala 2021 ghi rằng BP sau gắng sức có thể thấp hơn trước gắng sức) | — | — | **Bỏ 2026-10-29:** khó thực hiện ở phòng thí nghiệm của nhóm; cường độ và thời lượng cũng chưa có nguồn |
| ~~M5~~ | ~~Bóp tay tĩnh~~ | — | Tăng (Mark 1985, [10.1161/01.res.57.3.461](https://doi.org/10.1161/01.res.57.3.461): HR và BP tăng ở phút 1–2 khi bóp 30% lực tối đa) | — | — | **Loại**: không đạt K2/K3 ở 5.4 |

Không đưa vào: đổi tư thế ngồi–đứng, vì tay đeo PPG di chuyển và đổi độ cao so với tim, vi
phạm K2. M3, M4 đã bỏ ngày 2026-10-29 (xem đầu mục). Muốn thêm nghiệm pháp thay thế thì phải
qua sửa đổi đạo đức (mục "Dự phòng").

Thứ tự trong một buổi (đề xuất của nhóm 2026-10-29, chưa có nguồn): M0 → M1 → nghỉ ít nhất
5 phút → M2 → nghỉ. Thứ tự này cố định: thở chậm làm trước, để căng thẳng do tính nhẩm không
kéo sang lúc thở chậm. Nếu trung bình M0 của buổi có SBP ≥ 140 mmHg hoặc DBP ≥ 90 mmHg thì
không làm M1, M2. Nếu có lần cuff nào có SBP ≥ 180 mmHg hoặc DBP ≥ 110 mmHg thì dừng buổi
([an toàn buổi đo](../ethics/session_safety_stopping_v0.1.md) mục 3, đề xuất 2026-10-29,
chờ thầy). Tiêu chí "BP đã về gần nền" trước M2: **chưa khóa, chưa có nguồn**. Mỗi lần đo
cuff vẫn chỉ là một nhãn; nhiều cửa sổ trong cùng một nghiệm pháp không thành nhiều nhãn.

**Trục thời gian đo cuff** (chốt 2026-10-29, đóng hai mâu thuẫn ghi nhận ngày 2026-10-22; các
khoảng chờ là đề xuất của nhóm, chưa có nguồn, chờ thầy). Ký hiệu như ở 6.2: `t0` là lúc bấm
cuff, cửa sổ tín hiệu là `[t0 − L, t0)`.

- **M1:** người vận hành ghi lúc bắt đầu thở chậm bằng sự kiện mã 4 (`OPERATOR_MARK`) gửi từ
  PC. Người tham gia thở 6 lần mỗi phút (hít vào 4 s, thở ra 6 s) theo âm thanh hướng dẫn phát
  từ laptop; nhịp này là đề xuất của nhóm 2026-10-29, chưa có nguồn. Cuff đo ở phút cuối của
  15 phút thở chậm, và cửa sổ nằm trọn trong lúc thở chậm.
- **M2:** trình tự như sau.
  - Người vận hành đọc số bắt đầu và ghi sự kiện mã 4.
  - Người tham gia nhẩm im lặng.
  - Sau 90 s nhẩm thì bấm cuff (`t0`), nên cửa sổ `[t0 − 60 s, t0)` nằm trọn trong lúc nhẩm.
  - Người tham gia nhẩm tiếp tới khi cuff xả xong.
  - Người tham gia nói số đạt được.

  Tổng thời gian khoảng 3 phút; mốc 90 s và tổng 3 phút là đề xuất của nhóm 2026-10-29,
  chưa có nguồn. Trong khoảng im lặng `[t0 − 60 s, lúc cuff xả xong]`, người tham gia vẫn
  nhẩm nhưng không nói; đáp án chỉ được nói sau khoảng đó. Cuff đo khi người tham gia đang
  nhẩm, nên không trái quy tắc không nói ở 5.3. Độ trễ của `t0` so với sự kiện mã 4 được lưu
  cùng lượt đo, để kiểm cửa sổ có nằm trọn trong lúc nhẩm hay không. Người vận hành ghi lại số
  bắt đầu và số mà người tham gia nói ra. Hai số này cho biết người tham gia có nhẩm suốt thời
  gian đo hay không, nên được dùng để kiểm mức tham gia, nhưng không dùng để loại lượt đo khỏi
  phân tích chính.

**Dự phòng (chốt 2026-10-29; sửa cùng ngày khi bỏ M3, M4):**

- Nếu thầy chưa duyệt trục thời gian M2 trong Tuần 6 thì hồ sơ lần này chỉ có M0 và M1; M2
  được bổ sung bằng sửa đổi đạo đức.
- Nếu P2 ở pilot (6.5) cho thấy dải ΔBP quá hẹp thì báo thầy và rà lại protocol trước khi thu
  chính. Một hướng là xin sửa đổi đạo đức để thêm một nghiệm pháp làm tăng BP mà không dùng
  tay. Ứng viên mà nhóm thấy hợp nhất là duỗi gối tĩnh ở tư thế ngồi. Koba et al. 2004
  ([10.2170/jjphysiol.54.471](https://doi.org/10.2170/jjphysiol.54.471), abstract): 9 người
  giữ duỗi gối 2 phút ở 20% lực tối đa, MAP tăng 24 ± 3 mmHg (trung bình ± SE); abstract không
  nêu tư thế. Muốn dùng nghiệm pháp này thì phải thiết kế xong rồi mới nộp sửa đổi. Thiết kế
  gồm:
  - ghế có tựa;
  - lực cản cố định có phản hồi lực;
  - mức lực và thời lượng cố định;
  - thở bình thường (không nín thở);
  - quy tắc dừng khi gắng sức;
  - kiểm K2, K3, K6 (không gồng tay, không tì tay) trên thành viên nhóm.

  Đã cân nhắc nhưng không chọn: kẹp bóng giữa hai gối (khó chuẩn hóa lực); chườm lạnh mặt
  (đáp ứng BP không chắc); Stroop (trả lời bằng tay vi phạm K2/K3).
- Sửa đổi chỉ áp dụng sau pilot và trước khi bắt đầu thu chính; người làm pilot không vào vòng
  đánh giá (9.1). Nếu sửa đổi được duyệt khi thu chính đã bắt đầu, nghiệm pháp mới chỉ vào
  phân tích phụ, còn endpoint chính và δ của RQ1 vẫn tính trên M0–M2. Phiên bản protocol dùng
  ở từng buổi được ghi vào nhật ký buổi.
- Không tăng cường độ hay thời lượng của M1, M2 vượt quá bản đã duyệt để đạt P2 (P4 ở 6.5).

**Số lần bơm cuff và thời lượng buổi đo (chốt 2026-10-29, sửa cùng ngày khi bỏ M3, M4; ghi vào phiếu thông tin và tiêu chí chọn số 4):**

- Theo kế hoạch, M0 đo hai lần, M1 và M2 mỗi nghiệm pháp một lần, tổng cộng 4 lần mỗi buổi.
  Trần là 6 lần mỗi buổi, trong đó có tối đa 2 lần đo lại, dùng khi máy xả bình thường nhưng
  không ra kết quả, hoặc khi lượt đo bị cử động. Nếu máy gặp lỗi bơm không xả, bơm quá mức hoặc
  lỗi phần cứng thì dừng buổi theo
  [an toàn buổi đo](../ethics/session_safety_stopping_v0.1.md) mục 2 và không đo lại. Buổi
  chỉ có M0 thì tối đa 4 lần.
- Buổi 1 có thêm 2 lần đo hai tay khi sàng lọc (mục 4). Vì vậy tổng của buổi 1 theo kế hoạch
  là 6 lần, trần 8 lần; nếu buổi 1 chỉ có M0 thì trần là 6 lần.
- Giữa hai lần bơm, nghỉ ít nhất 2 phút (6.2).
- Trần thời lượng là 120 phút mỗi buổi, giữ nguyên khi bỏ M3, M4. Ước tính thô cho một buổi đủ
  M0–M2 là khoảng 60–80 phút; buổi 1 dài hơn vì có thêm bước đo chu vi bắp tay, đo hai tay
  và chỉnh LED. Ước tính
  này chưa có nguồn. Sau buổi diễn tập, trần này chỉ được giảm.
- Mỗi người tối đa 3 buổi, trong cửa sổ 4 tuần (mục 3).

### 6.5. Tiêu chí biên độ ΔBP kiểm ở pilot — **ĐỀ XUẤT, KHÓA TRƯỚC PILOT**

Định nghĩa trong pilot: ΔBP của một lần cuff trong nghiệm pháp bằng giá trị cuff đó trừ
trung bình các lần cuff M0 cùng buổi, tính riêng cho SBP và DBP.

**Thống kê chung cho P2 và R3 (chốt 2026-10-29):** với mỗi người $s$, tính
$m_s$ là median của $|\Delta\text{SBP}|$ trên các lần cuff không dùng để hiệu chuẩn. Chỉ số
là median của $m_s$ qua các người. Hai chỉ số dùng cùng thống kê này, nhưng mỗi chỉ số có mốc
so sánh riêng:

- **P2 (pilot, một buổi):** các lần cuff M1, M2, so với trung bình M0 cùng buổi.
- **R3 (cổng G4, [kịch bản bài báo](../paper_scenarios_v0.1.md)):** mọi lần cuff
  hợp lệ ở phiên ≥ 2, so với $\text{BP}_0$ của phiên 1. Đây chính là nhãn của RQ1
  (6.4), nên R3 đo được độ nhạy của RQ1.

So với max (định nghĩa ở v0.2 dùng max), median ít bị sai số cuff kéo lên hơn. Nhưng median
cũng chặt hơn max nhiều, vì các lần M0 ở phiên sau và các lần M1 thường có $|\Delta\text{SBP}|$
nhỏ. Ngưỡng 15 mmHg vốn được đặt theo câu chữ cũ, nên phải cùng thầy xem lại ngưỡng trước khi
khóa ở pilot.

Từ 2026-10-29, bộ nghiệm pháp chỉ còn M1, M2 (6.4), nên việc xem lại ngưỡng không còn là tùy
chọn. Dưới đây là suy luận của nhóm, chưa có số liệu:
- Ở pilot, $m_s$ chỉ là trung bình $|\Delta\text{SBP}|$ của hai lần cuff M1 và M2, trong khi
  M1 chỉ làm SBP giảm khoảng 3 mmHg (Adler 2019). Muốn P2 đạt 15 mmHg thì M2 phải làm SBP
  tăng gần 27 mmHg ở người đứng giữa.
- R3 tính thêm cả các lần M0 ở các phiên sau, nên còn khó đạt hơn P2.

Ngưỡng mới, và nhánh "≥ 15 người đạt chuẩn nhưng R3 dưới ngưỡng" ở
[kịch bản bài báo](../paper_scenarios_v0.1.md), phải được chốt cùng thầy trước pilot, kèm lý
do. Đề xuất của nhóm là suy ngưỡng từ mô phỏng độ nhạy ở
[RQ](../research_questions_v0.1.md) mục 4.E, tức là dải ΔBP cần có để CI của $d_s$ phân
biệt được với $\pm\delta$, làm riêng cho SBP và DBP. Không chọn một con số theo cảm tính, và không
chọn ngưỡng sau khi xem dữ liệu pilot. δ chính thức chỉ được chốt sau pilot, dựa trên độ lặp
lại của các lần cuff M0 (RQ mục 4.E). Vì vậy, mô phỏng để đặt ngưỡng P2/R3 dùng vài kịch bản δ
khai báo trước; mỗi kịch bản ghi rõ giá trị giả định và lý do. Ngưỡng P2/R3 không bị đổi lại
sau khi δ chính thức được chốt.

| # | Tiêu chí | Nguồn của ngưỡng |
| --- | --- | --- |
| P1 | Báo cáo theo người và theo nghiệm pháp: median, IQR của ΔSBP/ΔDBP và tỷ lệ lần cuff có hướng thay đổi đúng như 6.4 | Hướng thay đổi: nguồn ở 6.4. Không có ngưỡng đạt/không đạt cho tỷ lệ (**chưa có nguồn**) |
| P2 | Median qua người của $m_s$ (median \|ΔSBP\| của các lần cuff M1, M2 so với M0 cùng buổi) **≥ 15 mmHg** (phải đặt lại trước pilot, xem ở trên); nếu thấp hơn thì báo thầy và rà lại protocol trước khi thu chính | Lấy từ dấu hiệu R3 của kế hoạch 28 tuần (tài liệu nội bộ ngoài repo, áp dụng ở thu chính) — **ngưỡng nội bộ, không có nguồn khoa học**. Dùng chung thống kê với R3 nhưng mốc so sánh khác (chốt 2026-10-29, xem ở trên). Ngưỡng cần xem lại vì median chặt hơn max |
| P3 | Báo SD của ΔBP tham chiếu và tỷ lệ \|ΔBP\| > 5 mmHg | [RQ, mục 4](../research_questions_v0.1.md) (quy ước nội bộ) |
| P4 | Không tăng cường độ hay thời lượng nghiệm pháp ngoài bản đã duyệt để đạt P2 | Kế hoạch 28 tuần (nội bộ) |

Các ngưỡng trên sẽ được khóa bằng commit trước buổi pilot đầu tiên và không chỉnh sau khi
xem dữ liệu. Pilot chỉ chạy khi đã có phê duyệt phù hợp.

---

## 7. Quy tắc phân đoạn, gán nhãn và kiểm soát chất lượng (SQI)

### 7.1. Định nghĩa mẫu độc lập (Independent Sample)
> [!CAUTION]
> **Nguyên tắc cốt lõi chống thổi phồng dữ liệu:**
> - **Mỗi lần đo bằng cuff đối chứng chỉ tạo ra DUY NHẤT 1 nhãn huyết áp độc lập ($\text{SBP}_i, \text{DBP}_i$).**
> - Tuyệt đối **KHÔNG** được cắt đoạn tín hiệu 60 giây trước cuff thành 12 cửa sổ nhỏ (mỗi cửa sổ 5 giây), rồi gán cùng giá trị $(\text{SBP}_i, \text{DBP}_i)$ cho cả 12 cửa sổ và coi đó là 12 mẫu độc lập. Cách làm sai này gây rò rỉ dữ liệu nghiêm trọng và thổi phồng cỡ mẫu một cách sai lệch.
> - Đề xuất tổng hợp đặc trưng bằng trung vị trong cửa sổ chính, dự kiến dài 20–30 giây trước cuff; độ dài và quy tắc tổng hợp đều chưa khóa. Các cửa sổ ứng viên cho phân tích độ nhạy dài 10/20/30/60 giây, lấy trên `[t0 - L, t0)`, và phải được chọn/khóa trên pilot/validation trước khi xem test. Mỗi `event_id` vẫn chỉ đóng góp tối đa một cặp nhãn cuff độc lập.

### 7.2. Định danh cấu trúc dữ liệu phân cấp
Mỗi bản ghi phải có khóa định danh duy nhất theo cấu trúc phân cấp dưới đây (định dạng ID theo [quy ước dữ liệu](../quy_uoc_du_lieu.md)):
- `subject_id`: mã người tham gia (ví dụ `SUB001`, `SUB002`), không chứa thông tin định danh cá nhân.
- `session_id`: mã phiên đo theo ngày/thời điểm (ví dụ `S001`, `S002`).
- `event_id`: mã lượt đo trong phiên (ví dụ `E01`, `E02`).
- `window_id`: mã của từng cửa sổ tín hiệu bên trong một event.

### 7.3. Tiêu chí kiểm tra chất lượng tín hiệu (SQI) và loại bỏ cửa sổ

**Chốt 2026-10-29:**

- **Phân tích chính không loại lượt đo theo SQI.** Phân tích chính dùng mọi lần
  cuff hợp lệ tính được đặc trưng. Riêng lượt mất ECG hoặc mất PPG thì xử lý theo quy tắc ở
  mục 10.
- Lọc theo SQI là **phân tích phụ đăng ký trước**; coverage được báo trên toàn bộ lượt đo,
  như ở RQ3.
- Bộ cờ chính thức gồm các cờ của `features-sqi-v2`
  ([week04.py](../../software/feature_extraction/week04.py)) cho ECG/PPG, và
  `motion-sqi-v0` (ý 5 bên dưới) cho IMU.
- Ngưỡng của cả hai bộ sẽ được khóa trên bản ghi G2 (ghi ngày và commit) trước khi thu
  chính. Các con số còn chờ G2.

Bốn tiêu chí 1–4 dưới đây là ứng viên từ v0.1–v0.2, được giữ để tham khảo, **không phải quy tắc**. Mọi con số đều là đề xuất chưa khóa, và không tuning theo test:
1. **Nhiễu bão hòa quang học (Clipping/Saturation):** tín hiệu PPG chạm giới hạn của ADC ($V_{\text{max}}$ hoặc $V_{\text{min}}$) quá 5% thời gian cửa sổ.
2. **Chỉ số Skewness SQI ($s\text{SQI}$):** ứng viên là $s\text{SQI} < 0$. Dấu của chỉ số phụ thuộc vào cực tính và cách xử lý tín hiệu, nên không mặc định mọi PPG hợp lệ đều có độ lệch dương.
3. **Mất tín hiệu ECG:** không phát hiện được phức bộ QRS rõ ràng, hoặc biên độ đỉnh R nhỏ hơn $3\times$ độ lệch chuẩn của đường nền.
4. **Biến thiên nhịp tim bất thường:** khoảng cách giữa các đỉnh R liên tiếp dao động $> 30\%$ trong cửa sổ tĩnh (trừ hiện tượng loạn nhịp sinh lý theo hô hấp khi hô hấp đã được kiểm soát).
5. **Cử động mạnh (`motion-sqi-v0`, định nghĩa chốt 2026-10-24, ngưỡng chưa khóa):**
   dùng IMU BMI270 ở cổ tay đeo PPG, gia tốc và gyro 100 Hz (Packet Schema V0.2). Mã nguồn:
   [motion_sqi.py](../../software/feature_extraction/motion_sqi.py).
   - Gia tốc: lọc từng trục bằng bộ lọc thông cao 0,5 Hz rồi thông thấp 10 Hz (Butterworth bậc
     2, pha không đổi), sau đó lấy độ lớn vector $d(t)$. Gyro: trừ bias rồi lọc thông thấp
     10 Hz, sau đó lấy độ lớn $s(t)$. Đoạn đưa vào lọc rộng hơn cửa sổ nhưng không vượt qua
     $t_0$ (lúc bơm cuff).
   - Bias gyro lấy từ 30 s nghỉ **đã xác nhận yên** ở M0. Nếu đoạn này có mất mẫu, bão hòa hay
     chuyển động thì coi như không có bias (ghi lý do); không đi tìm đoạn "yên nhất".
   - Chỉ số burst: tính phân vị 95 trên cửa sổ trượt 1 s, bước 0,1 s, rồi lấy giá trị lớn nhất
     trong cửa sổ phân tích. Lý do: P95 tính trên cả 10 s sẽ bỏ sót cú giật < 0,5 s. Xuất kèm
     P95 của toàn cửa sổ, tỉ lệ mẫu vượt ngưỡng và giá trị lớn nhất.
   - Cửa sổ là `motion` khi một nhánh hợp lệ vượt ngưỡng (gia tốc 0,15 g hoặc gyro 20 °/s).
     Cửa sổ chỉ là `no_motion_detected` khi **cả hai** nhánh đều hợp lệ và dưới ngưỡng. Các
     trường hợp còn lại là `not_evaluable`: mất mẫu (không nội suy), bão hòa, thiếu bias, hoặc
     cửa sổ ngắn hơn 1 s. Chỉ riêng gia tốc dưới ngưỡng thì chưa đủ để coi cửa sổ là yên.
   - Hai ngưỡng này là `ENGINEERING_DRAFT_NOT_TEST_TUNED`, **không có nguồn**. Chúng sẽ được
     khóa trên bản ghi G2 của thành viên nhóm (lúc nghỉ so với lúc cử động theo hướng dẫn, có nhãn
     chuyển động độc lập), ghi ngày và commit, trước khi thu chính.
   - Giới hạn: cờ này không chứng nhận tín hiệu sạch. Bóp hay gồng tay có thể làm hỏng PPG mà
     gần như không tạo ra gia tốc hay chuyển động xoay. Cử động chậm (nâng tay, lắc thân) bị
     bộ lọc 0,5 Hz làm yếu đi. IMU ở tay trái không phản ánh nhiễu cơ ở tay phải (RA).
   - Phân tích chính không loại và không giảm trọng số cuff event theo cờ này
     (chốt 2026-10-29, xem đầu mục). Với RQ3, mọi chiến lược được so trên cùng một tập cuff
     event, và coverage được báo trên toàn bộ event; không coi phần còn lại sau khi lọc chuyển
     động là coverage 100 %.

---

## 8. Phương pháp tính PAT và cảnh báo vật lý

### 8.1. Công thức xác định PAT
$$\mathrm{PAT} = t_{\mathrm{PPG,foot}} - t_{\mathrm{ECG,Rpeak}}$$
- $t_{\mathrm{ECG,Rpeak}}$: thời điểm đỉnh sóng R của phức bộ QRS. Pan–Tompkins có hiệu chỉnh là một thuật toán ứng viên. Phương pháp phát hiện R peak, cấu hình lọc và quy tắc xử lý đỉnh giả hay đỉnh bị bỏ sót phải được kiểm tra trên pilot/validation trước khi khóa.
- $t_{\mathrm{PPG,foot}}$: thời điểm chân sóng (foot) của nhịp PPG tương ứng. Các phương pháp ứng viên gồm:
  - tiếp tuyến giao cắt (intersecting tangent method);
  - đạo hàm bậc hai cực đại ($d^2\text{PPG}/dt^2$);
  - cực tiểu trước sườn lên (`valley_min`; thêm 2026-10-29, [Tuần 5](week05_fiducials_pat_validity.md)).

  Mốc đánh dấu tay ở Tuần 5 là cực tiểu trước sườn lên, nên phương pháp tiếp tuyến gần như không thể đạt khi so với mốc tay. Khoảng PAT hợp lệ 80–400 ms chỉ dùng cho dữ liệu thiết bị; PulseDB dùng chế độ ghép riêng `pat-validity-pulsedb-v0` (Tuần 5 mục 3.1, chốt 2026-10-29). Phương pháp foot và quy tắc ghép nhịp vẫn chưa khóa. Chúng phải được khóa trên pilot/validation, không điều chỉnh theo test.

### 8.2. Cảnh báo phương pháp luận: $\text{PAT} \neq \text{PTT}$
- Nhóm nghiên cứu ghi nhận rõ:
  $$\text{PAT} = \text{PEP} + \text{PTT}$$
  Đây là cách viết gọn. PEP thường tính từ Q/QRS, không phải từ R peak, nên khoảng từ R đến lúc tống máu có thể khác PEP. Cần khai báo rõ các mốc. Với ECG + PPG, dự kiến chỉ đo được PAT, không đo riêng được PEP hay PTT. Xem [glossary Tuần 2](week_02_sample_label_glossary.md).
- **Quy tắc bắt buộc:**
  - Không được áp dụng trực tiếp cho PAT các phương trình vật lý thuần túy về sóng mạch vốn dành cho PTT (như Bramwell-Hill hay Hughes) mà bỏ qua PEP.
  - Đề xuất kiểm tra HR và hình thái PPG trong ablation. Trong dự án này chưa có bằng chứng rằng các đặc trưng đó bù được biến thiên của PEP.

---

## 9. Kế hoạch chia dữ liệu và đánh giá thống kê

### 9.1. Chiến lược phân chia (Data Splitting)
1. **LOSO lồng (nested Leave-One-Subject-Out, chốt 2026-10-29):**
   - **Vòng ngoài** chỉ dùng cho ước lượng cuối cùng. Mỗi lượt để riêng toàn bộ dữ liệu của
     người $k$ làm test và huấn luyện trên $N-1$ người còn lại; lặp lại cho cả $N$ người.
     Vòng ngoài chạy **đúng một lần**, sau commit khóa mọi lựa chọn. "Test khóa tới G5" nghĩa
     là dự đoán của vòng ngoài chỉ được sinh một lần, sau commit đó.
   - **Vòng trong** dùng để chọn siêu tham số. Với mỗi lượt ngoài, chạy LOSO (hoặc k-fold
     theo người) trên $N-1$ người huấn luyện; người test của lượt ngoài không tham gia. Ưu tiên
     mô hình có ít siêu tham số và cố định chúng từ trước (ví dụ Ridge với $\alpha$ cố định);
     khi đó có thể bỏ vòng trong.
   - Cửa sổ, phương pháp mốc R/foot, ngưỡng SQI, bộ đặc trưng và cách dùng dữ liệu của người
     huấn luyện (kể cả các lần cuff nghiệm pháp ở phiên 1 của họ) được khóa trên pilot trước
     khi chạy vòng ngoài, không chọn bằng sai số LOSO. Người có dữ liệu đã dùng để khóa các
     lựa chọn này không thuộc vòng ngoài.
2. **Temporal Cross-Session Split (Đánh giá hiệu chuẩn cá nhân):**
   - Với người test của mỗi lượt ngoài:
     - `Session 1`: chỉ dùng làm mốc hiệu chuẩn ($\text{BP}_0$, $\text{PAT}_0$, $\text{Features}_0$, lấy từ M0; mục 3).
     - Phiên 2 trở đi: mọi lần cuff hợp lệ dùng để kiểm tra dự đoán $\Delta\text{SBP}$ và $\Delta\text{DBP}$ (endpoint ở 6.4).
     - Các lần cuff nghiệm pháp M1, M2 ở phiên 1 (đề xuất 2026-10-29, chờ thầy): vòng ngoài sinh dự đoán cho các lần này trong cùng lần chạy. Các dự đoán này chỉ dùng cho RQ2b (cùng phiên so với khác phiên, [RQ](../research_questions_v0.1.md) mục 5.B), không dùng để hiệu chuẩn và không vào endpoint của RQ1.
   - Tuyệt đối không xáo trộn ngẫu nhiên dữ liệu giữa các phiên đo.

### 9.2. Kế hoạch thống kê và kiểm định giả thuyết
- **Chỉ số sai số:** $\text{MAE}$, $\text{RMSE}$, $\text{ME} \pm \text{STD}$, tính riêng cho SBP và DBP.
- **Bootstrap theo đối tượng (Subject-level Bootstrapping):**
  - Khi ước lượng khoảng tin cậy 95% (95% CI) cho MAE, phải lấy mẫu lại có hoàn lại **theo từng người tham gia (`subject_id`)**, sau đó tính sai số trên toàn bộ các mẫu của mỗi người được rút.
  - Tuyệt đối **KHÔNG bootstrap theo từng cửa sổ đo riêng rẽ**, vì làm vậy vi phạm giả định các quan sát độc lập (i.i.d).
- **Kiểm định giả thuyết (chưa khóa):**
  - Phép so sánh chính của RQ1 là giữa mô hình PPG-only và mô hình PPG + PAT, dùng cùng thuật toán, trên **cùng tập lần đo** tính được cả PAT lẫn đặc trưng PPG (xem [RQ](../research_questions_v0.1.md), mục 4.C). Tập này lấy từ endpoint ở 6.4 và không lọc thêm theo ngưỡng SQI (7.3). Sai số được báo cả gộp chung lẫn theo từng nghiệm pháp; phân tích chỉ dùng M0 là phân tích phụ định trước.
  - Hiệu ứng chính là chênh lệch MAE tính theo từng người; báo cáo trung bình và CI 95% bootstrap theo người. Kiểm định Wilcoxon signed-rank ghép cặp theo người ($\alpha = 0.05$) là phân tích hỗ trợ.
  - Tiêu chí kết luận theo [RQ v0.4](../research_questions_v0.1.md) mục 4.E (đề xuất 2026-10-29, chờ thầy): so sánh với zero-change cũng phải có CI theo người, như so sánh với PPG-only; trước khi chạy vòng ngoài phải chọn xong phương án đa kiểm định (A: giao–hợp cho từng đầu ra, Holm giữa SBP và DBP; B: Holm trên bốn so sánh) và mức hiệu ứng nhỏ nhất đáng quan tâm δ.
  - Luôn báo cáo kèm baseline zero-change và SD của $\Delta\text{BP}$ tham chiếu.

---

## 10. Quản lý dữ liệu thiếu và dữ liệu suy hao

- Nếu một lượt đo bị mất nhãn cuff (do lỗi máy đo bắp tay) thì toàn bộ lượt đo đó bị hủy, không đưa vào tập huấn luyện hay kiểm thử.
- Nếu ECG nhiễu tới mức không bắt được đỉnh R nhưng PPG đạt chuẩn, lượt đo bị loại khỏi phép so sánh chính PPG-only với PPG + PAT, để hai mô hình được đánh giá trên cùng một tập. Lượt đo đó vẫn được giữ cho phân tích phụ PPG-only trên toàn bộ lượt đo. Ghi rõ tỷ lệ lượt đo mất ECG theo từng người, vì nếu ECG mất không ngẫu nhiên thì kết quả có thể bị lệch.
- Lượt đo bị dừng vì an toàn (chốt 2026-10-29): lượt đã có nhãn cuff đầy đủ thì được giữ trong phân tích, kể cả khi buổi đo dừng sau đó. Lượt không có nhãn thì xử lý theo quy tắc mất nhãn cuff ở trên. Báo số lượt bị dừng theo nghiệm pháp và theo người, và làm phân tích độ nhạy loại các lượt mang cờ dừng. Các lượt bị dừng thường rơi vào lúc làm nghiệm pháp, đúng chỗ ΔBP lớn, nên nếu loại hết thì dải ΔBP sẽ bị lệch.
- Không tự điền nhãn huyết áp của biến đầu ra bằng giá trị trung bình (imputation).

---

## 11. Rủi ro thực nghiệm và phương án dự phòng

| Rủi ro kỹ thuật | Khả năng | Mức độ | Biện pháp phòng ngừa và xử lý |
|---|---|---|---|
| ECG đạo trình I nhiễu, SNR thấp | Cao | Cao | Dùng điện cực dán Ag/AgCl cho đạo trình I qua hai tay (LA ở mặt lòng cổ tay trái, RA ở mặt lòng cổ tay phải, RL ở cẳng tay trái; mục 5.2). Thiết kế lọc dải thông khoảng $0.5 - 40\text{ Hz}$ và khuếch đại vi sai có CMRR cao (thông số cụ thể theo AFE được chọn). Thiết bị theo [custom_board_proposal.md, Phần A](../../configs/hardware/custom_board_proposal.md). Trên người chỉ dùng Ag/AgCl có gel; điện cực khô không thuộc hồ sơ lần này (mục 5.1). |
| Nhiễu trôi đường nền PPG do dây đeo lỏng | Trung bình | Trung bình | Thêm phần hiển thị SQI trực quan trên giao diện thu thập; hướng dẫn kỹ thuật viên siết vòng vừa đủ chặt trước khi bắt đầu đếm ngược 60 giây. |
| Biên độ biến thiên huyết áp tự nhiên giữa các phiên quá nhỏ ($< 5\text{ mmHg}$) | Cao (từ 2026-10-29, khi chỉ còn M1, M2) | Cao | Dùng nghiệm pháp M1, M2 ở mục 6.4 và tiêu chí kiểm ở pilot (6.5), chỉ khi đã được duyệt đạo đức. Báo SD của ΔBP tham chiếu và sai số của baseline zero-change (mục 3). Nếu P2 thấp thì cùng thầy rà lại protocol, có thể xin sửa đổi để thêm nghiệm pháp (6.4, "Dự phòng"). |
| Người tham gia cử động tay trong khi đo | Cao | Trung bình | Hiển thị SQI và cờ cử động (`motion-sqi-v0`) cho người vận hành. Khi có cử động trong cửa sổ trước cuff, người vận hành đánh dấu (sự kiện mã 4) và có thể đo lại sau thời gian nghỉ theo quy tắc an toàn. Mọi lượt, kể cả lượt có cử động, vẫn được giữ trong raw kèm cờ. Phân tích chính không loại theo SQI; lọc SQI là phân tích phụ đăng ký trước (7.3, chốt 2026-10-29), không quyết định ngay lúc đang đo, để RQ3 có dữ liệu SQI kém (sửa 2026-10-26; bản trước ghi là tự động hủy lượt đo). Việc đánh dấu dùng lệnh sự kiện mã 4 gửi từ PC. |

---

## 12. Việc còn mở trước protocol v1.0

> [!IMPORTANT]
> **Checklist trước khi hoàn thiện protocol v1.0:**
> 1. [x] Phân bổ tay/điện cực (mục 5.2): phương án A, ba điện cực gồm LA ở cổ tay trái, RA ở cổ tay phải, RL ở cẳng tay trái; cực tính LA → ECGP (chốt 2026-10-23). Còn phải kiểm K3–K5 ở mục 5.4 trên thành viên nhóm ở G2.
> 2. [ ] Định danh trong dữ liệu: `SESSION_ID`, timestamp vi giây và sự kiện cuff (packet `0xC1`; SBP/DBP nhập ở PC theo `event_id`) đã có trong Packet Schema V0.1/V0.2. `subject_id`, `session_id` của buổi nghiên cứu và mã LED đã khóa nằm trong metadata phiên `packet-session-metadata-v1` của logger `packet-logger-v3` (chốt 2026-10-29).
> 3. [ ] Chọn nhãn hiệu và model máy đo huyết áp bắp tay đối chứng (tiêu chí ở 5.1, 2026-10-29). Phải chọn trước khi nộp hồ sơ.
> 4. [ ] Làm rõ quy trình nộp hồ sơ cho hội đồng đạo đức trước khi tuyển tình nguyện viên. Trước khi nộp, mang các mục ghi "đề xuất của nhóm, chờ thầy" trong v0.3 tới buổi gặp thầy ở Tuần 6: endpoint RQ1, bộ nghiệm pháp thu gọn M0–M2 và trục thời gian M2, trần tuyển, tiêu chí chọn/loại và đo hai tay, máy cuff, cùng các mục của hồ sơ đạo đức. Thầy xác nhận xong thì mới nộp.
> 5. [x] Đối chiếu với packet schema các khác biệt về sampling, timestamp lấy mẫu/FIFO/nhận gói, clock và marker cuff: đã chốt trong Packet Schema V0.1 mục 5 và V0.2 mục 7 (2026-10-23/24).
> 6. [ ] Kiểm tra căn cứ của cỡ mẫu, cửa sổ, SQI, kiểm định và mọi tiêu chí an toàn/vận động đang ở dạng dự thảo. Không dùng outline này để tự triển khai đo trên người.
> 7. [ ] Tìm nguồn cho bản tính nhẩm im lặng và thời lượng khoảng 3 phút của M2 (dạng bài trừ 13 liên tiếp đã có tiền lệ N7, mục 6.4), và cho thời gian nghỉ giữa các nghiệm pháp (M3, M4 đã bỏ ngày 2026-10-29 nên không cần nguồn nữa). Đặt lại ngưỡng 15 mmHg của P2/R3 trước pilot, vì với bộ M0–M2 ngưỡng này rất khó đạt (6.5).
