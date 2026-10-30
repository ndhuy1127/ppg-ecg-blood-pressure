# Câu hỏi nghiên cứu (Research Questions) — v0.4

> **Người thực hiện:** Nguyễn Đức Huy
>
> **Vai trò:** Xử lý tín hiệu, PAT, thống kê, protocol, tổng quan tài liệu và điều phối bài báo
>
> **Ngày lập:** 2026-09-22; **cập nhật:** 2026-10-14 (v0.2: thêm phần vấn đề nghiên cứu, làm rõ phép so sánh chính của RQ1, tính khả thi của RQ2/RQ3 và đối chiếu tên baseline với code), 2026-10-29 (v0.3: endpoint của RQ1 và mốc hiệu chuẩn khi có nghiệm pháp M0–M4, LOSO lồng, số phiên và cỡ mẫu theo [protocol v0.3](protocol/protocol_outline_v0.2.md); cập nhật bảng baseline), 2026-10-29 (v0.4: dẫn các nghiên cứu gần nhất; estimand của RQ1; tiêu chí kết luận dùng CI cho cả phép so sánh với zero-change; mức hiệu ứng nhỏ nhất đáng quan tâm δ; rủi ro áp lực tiếp xúc; RQ2a chuyển thành kiểm tra rò rỉ ở phụ lục, RQ2b đổi thành đánh giá cùng phiên so với khác phiên; RQ3 chuyển thành phân tích thăm dò; cùng ngày bỏ nghiệm pháp M3, M4 theo protocol 6.4, nên endpoint và RQ2b chỉ còn M0–M2, và thêm rủi ro dải ΔBP hẹp ở mục 4.F), 2026-10-30 (sửa mục 1 và 4.F–4.G theo lần tra có hệ thống: N18 đã đánh giá qua nhiều phiên với baseline chỉ hiệu chuẩn, nên khoảng trống hẹp lại; thêm nguồn về PEP và con số 31 người của N18), 2026-10-30 lần 2 (mục 1: thêm kết quả đọc toàn văn N6)
>
> Các thay đổi của v0.4 là **đề xuất của nhóm ngày 2026-10-29, chờ thầy xác nhận**. Các thay đổi này phải được khóa trước khi chạy vòng ngoài của LOSO lồng.
>
> Tên file vẫn giữ `v0.1` để các liên kết cũ không bị gãy.

---

## 1. Vấn đề nghiên cứu

Thiết bị đo huyết áp không vòng bít (cuffless) dựa trên PPG ở cổ tay thường cần được hiệu chuẩn bằng một lần đo cuff, rồi theo dõi thay đổi so với mốc này. Ba vấn đề sau làm cho việc đánh giá các thiết bị này trở nên khó:

1. **Mốc hiệu chuẩn tự nó đã là một dự đoán tốt.** Nếu BP ít thay đổi sau hiệu chuẩn, chỉ cần giữ nguyên giá trị cuff ban đầu là đã có sai số nhỏ. Mukkamala et al. (2021) chỉ ra điểm này bằng mô phỏng. Dự án Aurora (1.125 người) cũng không tìm thấy mô hình dạng sóng nào dự đoán BP ngày hôm sau tốt hơn rõ rệt so với baseline chỉ dùng BP hiệu chuẩn (Mukkamala et al., 2023). Xem [tổng quan bổ sung](literature/literature_update_2026-10-14.md), S2–S3. Tổng quan gần nhất của cùng nhóm tác giả (Mukkamala et al., 2025; đọc toàn văn ngày 2026-10-29) cho rằng đến nay chưa có bằng chứng thuyết phục rằng phân tích dạng sóng hay PAT thêm được giá trị đáng kể ngoài cuff hiệu chuẩn hoặc dữ liệu nhân khẩu học ([N8](literature/literature_update_2026-10-29.md)).
2. **PAT không phải PTT.** Có ECG thì đo được PAT, tức khoảng từ R-peak đến chân sóng PPG. Nhưng PAT chứa cả thời gian tiền tống máu (PEP), vốn thay đổi theo trạng thái giao cảm. Payne et al. (2006) cho thấy PEP chiếm 12–35% khoảng từ đỉnh R đến xung ở ngón tay. Vì vậy, thêm ECG có giúp ích hơn so với chỉ dùng PPG hay không là câu hỏi thực nghiệm, không suy ra được từ lý thuyết PTT.
3. **Cách chia dữ liệu làm kết quả đẹp giả tạo.** Khi các cửa sổ của cùng một người nằm ở cả tập huấn luyện lẫn tập kiểm tra, sai số thấp hơn đáng kể so với khi chia theo người (Yoshizawa et al., 2023; Mehta et al., 2024).

**Các nghiên cứu gần nhất (v0.4; sửa 2026-10-30 theo lần tra có hệ thống ngày 2026-10-29).** Đã có nghiên cứu đánh giá mô hình dựa trên PPG và mô hình dựa trên PAT so với baseline zero-change hoặc baseline chỉ hiệu chuẩn, đánh giá theo người, kể cả qua nhiều phiên. Tuy vậy, chưa thấy phép so sánh ghép cặp PPG-only với PPG + PAT cho cùng một đầu ra qua nhiều phiên. Các nguồn dưới đây đều có trong [tổng quan 2026-10-29](literature/literature_update_2026-10-29.md):

- **Trong một buổi đo** (PPG ở ngón tay, ngón chân hoặc tai):
  - Finnegan et al. (2023, N1) so sánh các bộ đặc trưng PPG, ECG và PAT khi truyền phenylephrine, nhưng không có mô hình PPG + PAT.
  - Natarajan et al. (2021, N2) đánh giá đặc trưng PPG cộng PAT trong các nghiệm pháp.
- **Qua nhiều phiên:** Yavarimanesh et al. (2022, N18, đọc toàn văn).
  - Thiết kế: các mô hình tuyến tính dựa trên PAT hoặc trên đặc trưng dạng sóng PPG (tai, ngón tay, ngón chân) được đánh giá ở các phiên cách nhau khoảng một năm, so với baseline chỉ dùng trung bình các lần cuff ban đầu. Các nghiệm pháp gồm thở chậm, tính nhẩm, cold pressor ở chân và nitroglycerin.
  - Đối tượng: 10 người, 57 ± 18 tuổi. Hệ số riêng của từng người được lập từ một phiên.
  - Các mô hình có PAT dự đoán SBP, còn mô hình chỉ dùng PPG dự đoán DBP. Mỗi mô hình được so riêng với baseline, nên đây không phải so sánh ghép cặp cho cùng một đầu ra.
  - Kết quả: sau một năm, chỉ còn mô hình PAT ngón chân cho SBP là hữu ích.
- **Trên dữ liệu cổ tay Aurora-BP (đo lưu động):** Cisnal et al. (2025, N19, mới đọc abstract) báo rằng baseline tốt hơn mô hình dựa trên PAT tốt nhất ở SBP và tương đương ở DBP.
- **Nghiên cứu nhiều ngày, quy mô lớn:**
  - Mieloszyk et al. (2022, [S4](literature/literature_update_2026-10-14.md)), trên thiết bị cổ tay: phần nhóm đã đọc (abstract) chưa cho thấy phép so sánh ghép cặp PPG-only với PPG + PAT, đối chiếu với baseline chỉ hiệu chuẩn.
  - Liu et al. (2023, N6, đọc toàn văn ngày 2026-10-30, chờ thầy xem): 3.077 người, không có nghiệm pháp; hiệu chuẩn ở ngày D rồi đánh giá ở D+7, D+14, D+21. Baseline có hiệu chuẩn là mô hình AdaBoost học từ BP ban đầu + nhân khẩu học, không phải zero-change. Ba mô hình "PTT" theo cách gọi của bài (PAT theo quy ước dự án), hiệu chuẩn theo từng người, có MAE cao hơn baseline này ở cả SBP và DBP (SBP 9,20–9,26 so với 8,46; DBP 6,59–6,78 so với 5,78 mmHg). Bài chỉ so PPG với ECG + PPG ở mô hình không hiệu chuẩn, chỉ cho SBP, và không kiểm định cặp này. PPG đo ở ngón tay ấn lên đồng hồ và ECG cần ngón cái tay kia, nên thiết bị không thuần cổ tay.

Vì vậy, các yếu tố sau, dù đứng riêng hay gộp một phần, đều không phải điểm mới:

- nhiều phiên;
- baseline chỉ hiệu chuẩn;
- nghiệm pháp;
- đánh giá mô hình PAT và mô hình PPG so với baseline.

Phần có thể vẫn là đóng góp thì hẹp hơn ([tổng quan](literature/literature_update_2026-10-29.md) mục 5.1): một phép so sánh ghép cặp, đăng ký trước, giữa PPG-only và PPG + PAT, với các điều kiện sau:

- thiết bị chỉ đặt ở cổ tay;
- các phiên cách nhau vài ngày đến 4 tuần;
- hiệu chuẩn bằng offset từ M0 của phiên 1, còn hệ số chung cho mọi người được học bằng LOSO lồng (khác với N18);
- luôn so với zero-change.

Giới hạn của nhận định này:

- Nhận định chỉ dựa trên phạm vi đã tra: PubMed, Europe PMC, OpenAlex, giai đoạn 2022–2026. Chưa tra IEEE Xplore và Scopus.
- Đã đối chiếu với toàn văn N6 ngày 2026-10-30 (chờ thầy xem): N6 chỉ thỏa một phần điều kiện về khoảng cách giữa các phiên, không thỏa các điều kiện còn lại ([tổng quan](literature/literature_update_2026-10-29.md) mục 5.1).
- S4 chỉ dùng abstract. Ngày 2026-10-29 đã quyết định không lấy toàn văn qua thư viện, nên nhận định chưa được kiểm với toàn văn S4, và bài báo phải nêu rõ giới hạn này.
- Không được viết thành "chưa có nghiên cứu nào".

**Mục tiêu nghiên cứu:** xây dựng nguyên mẫu đo ở cổ tay thu đồng bộ ECG và PPG, rồi dùng nó để kiểm tra trên một nhóm nhỏ người khỏe mạnh xem PAT có làm giảm sai số dự đoán ΔSBP/ΔDBP ở các phiên đo sau hiệu chuẩn so với chỉ dùng PPG hay không. Nguyên mẫu nối USB với máy tính và dùng điện cực ECG dán ở hai cổ tay. Phần đánh giá phải có baseline zero-change, chia dữ liệu theo người và theo thời gian, và có khoảng tin cậy theo người.

Các mục tiêu triển khai (chế tạo prototype, firmware, pipeline) là điều kiện để trả lời câu hỏi, không phải là câu hỏi nghiên cứu.

---

## 2. Nguyên tắc phương pháp chung

1. **Đánh giá riêng SBP và DBP.** Hai đại lượng này chịu ảnh hưởng của những yếu tố sinh lý khác nhau một phần: SBP gắn nhiều hơn với tống máu và độ cứng của động mạch lớn, còn DBP gắn với kháng lực ngoại vi. Không gộp chúng thành một chỉ số sai số chung.
2. **Gọi đúng PAT.** Khoảng từ đỉnh R của ECG đến chân sóng PPG là PAT, với `PAT = PEP + PTT`. Đây là cách viết gọn: mốc R không trùng với mốc Q/QRS mà PEP thường dùng. Không áp trực tiếp phương trình của PTT lên PAT.
3. **Chống rò rỉ dữ liệu.** Dữ liệu được chia theo người. Khi cá nhân hóa, dữ liệu hiệu chuẩn có trước dữ liệu kiểm tra. Một lần đo cuff là một nhãn; nhiều cửa sổ của cùng một lần đo không phải là nhiều mẫu độc lập. Bootstrap lấy mẫu lại theo người. Các biện pháp này làm giảm nguy cơ mô hình nhận dạng người thay vì học quan hệ với BP, nhưng không loại trừ hoàn toàn mọi dạng rò rỉ.
4. **Không chọn gì trên tập test.** Đặc trưng, cửa sổ, ngưỡng SQI, siêu tham số và mức vận hành đều được chọn trên train/validation; test chỉ dùng một lần, sau khi các lựa chọn đã khóa. Với dữ liệu prototype, nguyên tắc này được thực hiện bằng LOSO lồng ([protocol v0.3](protocol/protocol_outline_v0.2.md) mục 9.1, chốt 2026-10-29):
   - siêu tham số được chọn ở vòng trong;
   - cửa sổ, mốc và SQI được khóa trên pilot;
   - vòng ngoài chỉ chạy một lần.

---

## 3. Tóm tắt ba câu hỏi nghiên cứu

| | Yếu tố khảo sát | So sánh với | Chỉ số chính | Dữ liệu cần | Làm được khi nào |
|---|---|---|---|---|---|
| **RQ1** (chính, xác nhận) | Thêm PAT (từ ECG) vào mô hình PPG | Cùng mô hình nhưng chỉ dùng PPG; zero-change | Trung bình theo người của chênh lệch MAE cho ΔSBP và ΔDBP, kèm CI 95% bootstrap theo người, đọc theo mức δ khóa trước (mục 4.E) | Prototype, ≥ 15 người đạt chuẩn, ≥ 2 phiên/người, nhãn cuff | Sau khi có phần cứng, có phê duyệt đạo đức và đã thu dữ liệu |
| **RQ2** (phụ) | (a) Cách chia dữ liệu; (b) đánh giá cùng phiên so với khác phiên | (a) Chia ngẫu nhiên theo cửa sổ so với chia theo người; (b) cuff nghiệm pháp ở phiên 1 so với ở phiên ≥ 2 | Chênh lệch MAE, CI theo người | (a) PulseDB train ∪ val; (b) prototype, cùng dữ liệu với RQ1 | (a) làm được ngay, báo ở phụ lục; (b) cần dữ liệu prototype |
| **RQ3** (thăm dò) | Từ chối dự đoán theo SQI và độ bất định | Không từ chối; từ chối ngẫu nhiên ở cùng coverage; chỉ SQI; chỉ độ bất định | Đường cong risk–coverage, MAE tại mức coverage chọn ở vòng trong | Dữ liệu có nhãn, có cả đoạn tốt lẫn đoạn nhiễu tự nhiên | Tùy nguồn dữ liệu (xem 6.G) |

---

## 4. RQ1: Giá trị gia tăng của PAT sau hiệu chuẩn cá nhân

> **Câu hỏi:** Ở người khỏe mạnh 18–35 tuổi không có trong dữ liệu huấn luyện, sau khi hiệu chuẩn bằng trung bình các lần cuff M0 ở phiên 1, nếu thêm PAT (tính từ ECG) vào mô hình đặc trưng PPG thì sai số dự đoán $`\Delta\text{SBP}`$ và $`\Delta\text{DBP}`$ ở các phiên đo sau (phiên 2–3) có giảm so với cùng mô hình chỉ dùng PPG hay không, và giảm bao nhiêu?

### A. Giả thuyết

- **$H_{0,\text{RQ1}}$:** Với mỗi đầu ra (SBP, DBP), MAE theo người của mô hình PPG + PAT không thấp hơn MAE của mô hình PPG-only trên các phiên sau.
- **$H_{1,\text{RQ1}}$:** MAE theo người của mô hình PPG + PAT thấp hơn MAE của mô hình PPG-only.
- **So với zero-change (v0.4):** $H^{\text{ZC}}_{0,\text{RQ1}}$: MAE theo người của PPG + PAT không thấp hơn MAE của zero-change; $H^{\text{ZC}}_{1,\text{RQ1}}$: MAE này thấp hơn. Kết luận chính đòi hỏi bác bỏ cả $H_{0,\text{RQ1}}$ lẫn $H^{\text{ZC}}_{0,\text{RQ1}}$ (mục E).

SBP và DBP được kiểm định riêng. Bằng chứng hiện có cho thấy việc không bác bỏ được $H_0$ là một khả năng thực tế. Theo Payne 2006, PAT gần như không giải thích được DBP khi chưa trừ PEP; ở Aurora, mô hình dạng sóng không vượt baseline hiệu chuẩn. Kết quả như vậy vẫn được báo cáo đầy đủ.

**Estimand (v0.4, đề xuất 2026-10-29, chờ thầy):** $`\theta = \mathbb{E}_s[d_s]`$, tức trung bình theo người của $`d_s = \text{MAE}_s(\text{PPG+PAT}) - \text{MAE}_s(\text{PPG})`$, tính riêng cho ΔSBP và ΔDBP.

- **Quần thể:** người khỏe mạnh 18–35 tuổi thuộc vòng ngoài của LOSO lồng, tức là không có trong dữ liệu huấn luyện của lượt đó và không phải người tham gia pilot.
- **Điều kiện:** hiệu chuẩn bằng $`\text{BP}_0`$ của phiên 1 và đánh giá trên endpoint; cả hai được định nghĩa ở mục B.
- **Trọng số:** trong một người, các lần cuff có trọng số như nhau. Khi tính $\theta$, mỗi người cũng có trọng số như nhau, nên người có nhiều lần cuff không chi phối kết quả.
- **Phạm vi kết luận:** chỉ cho các lần đo tính được PAT (mục C). Tỷ lệ lần đo mất ECG được báo kèm.
- **Ý nghĩa:** endpoint gộp M0–M2, nên $\theta$ đo khả năng theo dõi cả đáp ứng với nghiệm pháp lẫn biến thiên lúc nghỉ ở các phiên sau. M3 và M4 đã bỏ ngày 2026-10-29 (protocol 6.4). Phân tích phụ chỉ trên M0 cho biết riêng phần biến thiên lúc nghỉ. Theo kế hoạch, M0 chiếm hai trên bốn lần cuff mỗi phiên (trước khi bỏ M3, M4 là hai trên sáu), nên $\theta$ nghiêng về biến thiên lúc nghỉ. Kết luận chỉ áp dụng cho các nghiệm pháp đã làm, không suy ra cho tình huống lạnh hay gắng sức.

### B. Biến nghiên cứu

- **Đặc trưng PPG:** thời gian lên (rise time), độ rộng xung tại 50% biên độ, biên độ xung và HR tính từ PPG. Ứng viên mở rộng là tỷ số diện tích tâm thu/tâm trương và PIR (Ding et al., 2016). Bộ đặc trưng v0 đã có trong code Tuần 4 (`software/feature_extraction/week04.py`) nhưng chưa được khóa.
- **Đặc trưng từ ECG:** PAT và $`\Delta\text{PAT} = \text{PAT}_{\text{hiện tại}} - \text{PAT}_{\text{hiệu chuẩn}}`$. PAT đo từ R-peak đến chân sóng PPG (PPG foot) của cùng nhịp, lấy trung vị trong cửa sổ. HR và HRV ngắn hạn từ ECG là đặc trưng phụ cho phân tích ablation.
- **Mốc hiệu chuẩn (chốt 2026-10-29):** $`\text{SBP}_0`$ và $`\text{DBP}_0`$ là trung bình các lần cuff M0 (nghỉ ở tư thế ngồi) hợp lệ ở phiên 1. $`\text{PAT}_{\text{hiệu chuẩn}}`$ và các đặc trưng nền được lấy từ cửa sổ của chính các lần cuff đó.
- **Đầu ra:** $`\Delta\text{SBP} = \text{SBP}_{\text{target}} - \text{SBP}_0`$ và $`\Delta\text{DBP} = \text{DBP}_{\text{target}} - \text{DBP}_0`$ (mmHg). BP ước lượng cuối cùng là $`\widehat{\text{BP}} = \text{BP}_0 + \Delta\widehat{\text{BP}}`$.
- **Tập đánh giá (endpoint chính; đề xuất của nhóm 2026-10-29, chờ thầy xác nhận):** mọi lần cuff hợp lệ ở phiên ≥ 2, gồm M0 và các nghiệm pháp M1, M2 ([protocol v0.3](protocol/protocol_outline_v0.2.md) mục 6.4). M3 và M4 đã bỏ ngày 2026-10-29. Nghiệm pháp là biến phân tầng. Phân tích phụ định trước chỉ dùng các lần cuff M0 ở phiên ≥ 2. Cuff nghiệm pháp ở phiên 1 của người được đánh giá không dùng để hiệu chuẩn và không vào tập đánh giá.

### C. Các mô hình so sánh

| Mô hình | Đầu vào | Vai trò |
|---|---|---|
| **Zero-change** | Không có đặc trưng; $`\Delta\widehat{\text{BP}} = 0`$, tức $`\widehat{\text{BP}} = \text{BP}_0`$ | Baseline bắt buộc. Mô hình nào không vượt baseline này thì không có giá trị gia tăng so với chỉ dùng mốc hiệu chuẩn |
| **PAT-only** | $`\Delta(1/\text{PAT}^2)`$ hoặc $`\Delta\text{PAT}`$ | Kiểm tra lượng thông tin của riêng PAT. Hệ số được học ở mức quần thể trên những người thuộc tập train, vì người được đánh giá chỉ đóng góp $`\text{BP}_0`$ (trung bình M0 phiên 1) cho hiệu chuẩn; cuff nghiệm pháp ở phiên 1 của họ không dùng để fit hệ số riêng. Đây là hồi quy thực nghiệm, không phải áp phương trình Moens–Korteweg lên PAT |
| **PPG-only** | Đặc trưng PPG + HR từ PPG | Đối chứng chính của RQ1 |
| **PPG + PAT** | Như PPG-only, có thêm PAT/ΔPAT | Mô hình chính của RQ1 |
| **PPG + PAT + ECG-HRV** | Thêm HR/HRV từ ECG | Ablation phụ, tách phần đóng góp của PAT khỏi phần của các đặc trưng ECG khác |

**Phép so sánh chính là PPG-only với PPG + PAT**. Hai mô hình dùng cùng thuật toán (ví dụ Ridge), cùng ngân sách chọn siêu tham số ở vòng trong của LOSO lồng (protocol mục 9.1) và **cùng tập lần đo đánh giá**, tức những lần đo tính được cả PAT lẫn đặc trưng PPG. Phân tích chính không lọc thêm theo ngưỡng SQI; lọc SQI là phân tích phụ đăng ký trước (protocol mục 7.3, chốt 2026-10-29). Nếu PPG-only được đánh giá trên nhiều lần đo hơn, kể cả những lần ECG hỏng, thì hai mô hình sẽ bị so trên hai tập khác nhau. Kết quả PPG-only trên toàn bộ lần đo và tỷ lệ lần đo mất ECG được báo cáo riêng như phân tích phụ.

### D. Chỉ số đánh giá

Tính riêng cho ΔSBP và ΔDBP:

- MAE và ME ± SD của sai số (sai số = dự đoán − tham chiếu), tổng hợp đều theo người (như `evaluate_bp`).
- **Hiệu ứng chính:** $`d_s = \text{MAE}_s(\text{PPG+PAT}) - \text{MAE}_s(\text{PPG})`$ cho từng người $s$. Báo cáo trung bình của $d_s$ và CI 95% bootstrap theo người (`software/evaluation/subject_bootstrap.py`). Kiểm định Wilcoxon signed-rank trên $d_s$ là phân tích hỗ trợ.
- **So với zero-change (v0.4):** $`d^{0}_s = \text{MAE}_s(\text{PPG+PAT}) - \text{MAE}_s(\text{zero-change})`$. Báo trung bình và CI 95% bootstrap theo người giống như với $d_s$, dùng chung các lượt bootstrap.
- Hệ số Pearson $r$ giữa ΔBP tham chiếu và ΔBP dự đoán. Hệ số này không xác định cho zero-change vì dự đoán là hằng số.
- Tỷ lệ lần đo có $|e| \le 5$ và $\le 10$ mmHg, chỉ để mô tả, không phải tiêu chí AAMI/ISO.
- **Bắt buộc báo cáo kèm:** SD của ΔBP tham chiếu và tỷ lệ lần đo có $|\Delta\text{BP}| > 5$ mmHg. Nếu ΔBP tham chiếu có dải rất hẹp thì mọi so sánh MAE đều kém nhạy, và người đọc cần biết điều đó.
- Các chỉ số trên được báo cả cho toàn bộ lẫn cho từng nghiệm pháp (M0–M2), và cho cả phân tích phụ chỉ trên M0.

### E. Tiêu chí kết luận

Mục này được viết lại ở v0.4 (đề xuất 2026-10-29, chờ thầy) và phải khóa trước khi chạy vòng ngoài. Bản v0.3 chỉ đòi "MAE thấp hơn zero-change" mà không cần CI, trong khi phép so với PPG-only lại đòi CI, nên hai chuẩn bằng chứng lệch nhau.

- **Kết luận chính, riêng cho từng đầu ra (SBP, DBP):** chỉ kết luận "thêm PAT làm giảm sai số so với PPG-only và vượt zero-change" khi **cả hai** điều kiện sau cùng đạt:
  1. CI 95% bootstrap theo người của trung bình $d^{0}_s$ (PPG + PAT so với zero-change) nằm hoàn toàn dưới 0;
  2. CI 95% bootstrap theo người của trung bình $d_s$ (PPG + PAT so với PPG-only) nằm hoàn toàn dưới 0.

  Mức 95% ở đây là mức trước hiệu chỉnh; mức thực dùng theo phương án đa kiểm định bên dưới. Mức độ lợi ích được đọc theo δ ở dưới, và chỉ gọi là lợi ích đáng quan tâm khi $U < -\delta$.
- **Đa kiểm định, chọn một phương án trước khi chạy vòng ngoài:**
  - **Phương án A (đề xuất):** với mỗi đầu ra, kết luận chính là giao của hai điều kiện trên (kiểm định giao–hợp, intersection–union). Mỗi điều kiện được xét bằng CI hai phía ở cùng một mức, không hiệu chỉnh thêm trong cùng một đầu ra, vì kết luận chỉ đúng khi cả hai cùng đạt. Giữa SBP và DBP dùng Holm, nên mức CI của từng đầu ra theo thứ tự Holm. Các kết luận riêng lẻ khác (ví dụ chỉ vượt PPG-only) là phân tích phụ, không dùng để tuyên bố.
  - **Phương án B:** Holm trên bốn phép so sánh (2 đầu ra × 2 đối chứng).
  - Dù chọn phương án nào cũng báo CI ứng với mức hiệu chỉnh đã chọn.
- **Mức hiệu ứng nhỏ nhất đáng quan tâm δ** ($`\delta_{\text{SBP}}`$, $`\delta_{\text{DBP}}`$, mmHg) được khóa trước vòng ngoài, căn cứ vào độ lặp lại của cuff tham chiếu và vào lý do ứng dụng. Độ lặp lại ở đây là chênh lệch giữa các lần cuff M0 liền nhau ở pilot. Không dùng lại 1,5/1,0 mmHg của bản v0.1 vì con số đó chưa có căn cứ. CI của trung bình $d_s$, ở cùng mức với kết luận chính, được ký hiệu là $[L; U]$ và đọc như sau:
  - $U < -\delta$: thêm PAT giảm sai số ít nhất δ.
  - $U < 0$ và $L < -\delta \le U$: thêm PAT có lợi, nhưng chưa chắc đạt δ.
  - $-\delta \le L$ và $U \le \delta$: PPG-only và PPG + PAT tương đương trong phạm vi δ; đây là kết quả âm tính có thông tin. Nếu đồng thời $U < 0$ thì có lợi nhưng nhỏ hơn mức đáng quan tâm; nếu $L > 0$ thì sai số tăng nhưng nhỏ hơn δ. Cách đọc này dùng CI hai phía ở mức trên, nên thận trọng hơn kiểm định TOST thông thường (TOST ở mức 5% tương ứng CI 90%).
  - $L > 0$ và $U > \delta$: thêm PAT làm sai số tăng; báo như một kết quả.
  - Các trường hợp còn lại (CI chứa 0 và vượt ra ngoài $[-\delta; \delta]$): **chưa kết luận**, phép so sánh thiếu độ nhạy; không viết là "PAT không giúp".
- **Độ nhạy dự kiến:** trước đợt thu dữ liệu chính, ước lượng độ rộng CI kỳ vọng bằng mô phỏng với nhiều mức phương sai của $d_s$ (dùng số liệu pilot nếu có), để biết với ≥ 15 người thì có loại trừ được δ hay không.
- Nếu hai điều kiện không cùng đạt thì không tuyên bố kết luận chính và không khẳng định PAT có lợi. Trạng thái của từng phép so sánh (so với PPG-only, so với zero-change) vẫn được báo như phân tích phụ, kèm ước lượng và CI theo cách đọc ở trên. Một phép so sánh đạt riêng lẻ không đủ để tuyên bố.

### F. Rủi ro phương pháp

- **PEP thay đổi giữa các phiên** do căng thẳng, tư thế hay nhiệt độ, làm PAT thay đổi trong khi BP không đổi. Các nguồn bổ sung ngày 2026-10-30, đều mới đọc abstract ([tổng quan 2026-10-29](literature/literature_update_2026-10-29.md)):
  - stress tinh thần làm PEP giảm (N11);
  - phản ứng PEP mạnh hơn khi nhiệm vụ khó hơn (N30);
  - với nhiệm vụ tinh thần, tương quan giữa thay đổi PAT và thay đổi SBP không có ý nghĩa thống kê trong nghiên cứu đó (N25, r = −0,12);
  - khi đau do lạnh, PTT giảm còn PEP không đổi (N29).
- **PAT ở cổ tay chịu ảnh hưởng của sự co cơ trơn ở mạch ngoại vi**, độc lập với mức BP (Mukkamala et al., 2023).
- **ΔBP giữa các phiên nhỏ** ở người trẻ, khỏe mạnh, đo lúc nghỉ. Điều này làm zero-change khó bị vượt và làm giảm độ nhạy của phép so sánh.
- **Áp lực tiếp xúc và cách đeo thay đổi giữa các phiên (v0.4).** Natarajan et al. (2021, [N2](literature/literature_update_2026-10-29.md)) ghi nhận rằng dạng sóng PPG chịu ảnh hưởng của áp lực tiếp xúc nhiều hơn PAT. Nếu độ chặt của dây hay vị trí đeo ở các phiên sau khác với phiên 1, PPG-only có thể kém đi vì lý do kỹ thuật, khiến PAT trông như có lợi dù không phải do sinh lý. Rủi ro này được giảm bằng cách chuẩn hóa cách đeo trong protocol (vị trí, nấc dây) và ghi lại ở mỗi phiên. Khi diễn giải $d_s$ phải nêu rủi ro này.
- **Dải ΔBP hẹp khi chỉ còn M0–M2 (2026-10-29).** M3 (ngâm chân nước lạnh) và M4 (đạp xe) đã bị bỏ vì khó thực hiện ở phòng thí nghiệm ([protocol](protocol/protocol_outline_v0.2.md) mục 6.4). M2 (tính nhẩm im lặng) là nghiệm pháp duy nhất dự kiến làm BP tăng, mà stress tâm lý lại làm PEP đổi, nên PAT có thể đổi trong khi BP không đổi (rủi ro đã nêu ở trên). Theo abstract của N25, SBP thậm chí còn giảm trong nhiệm vụ tinh thần của nghiên cứu đó, nên chưa chắc M2 làm SBP tăng. Dải ΔBP hẹp làm baseline zero-change khó bị vượt, và CI của $d_s$ dễ nằm trong $[-\delta; \delta]$ hoặc rơi vào "chưa kết luận". Mô phỏng độ nhạy ở mục E phải dùng dải ΔBP dự kiến của bộ M0–M2, làm riêng cho SBP và DBP. Khi viết bài phải báo SD của ΔBP tham chiếu theo từng nghiệm pháp, và không suy kết quả ra các tình huống làm BP đổi mạnh (lạnh, gắng sức).
- **ECG đạo trình I giữa hai cổ tay (điện cực dán, chốt 2026-10-23) có biên độ nhỏ hơn ECG ngực và dễ nhiễu khi một trong hai tay cử động**, gây sai lệch R-peak. Nếu việc mất ECG ở các lần đo không xảy ra ngẫu nhiên, tập đánh giá có thể bị lệch; vì vậy phải so trên cùng một tập (mục C).
- **Độ phân giải thời gian:** ECG 512 sps (khoảng 1,95 ms mỗi mẫu) và PPG 200 sps mỗi khe (5 ms mỗi mẫu; chốt 2026-10-24). Sai số định vị mốc, nhất là chân sóng PPG, và sai số đồng bộ hai kênh đều cộng trực tiếp vào PAT.

### G. Dữ liệu tối thiểu và tính khả thi

- Mục tiêu là ≥ 15 người đạt chuẩn, tuyển tối đa 25 người; mức trần này là đề xuất của nhóm, chờ thầy. Mỗi người cần tối thiểu 2 phiên (1 phiên hiệu chuẩn + ≥ 1 phiên đánh giá), mục tiêu là 3 phiên, và mọi phiên nằm trong 4 tuần kể từ phiên 1 (protocol v0.3 mục 3, chốt 2026-10-29). Mỗi phiên có ít nhất 2 lần cuff hợp lệ. Đơn vị phân tích cho kiểm định là người.
- Các con số này là đề xuất dựa trên tính khả thi, chưa dựa trên phân tích power, và cần được tính lại từ pilot và mô phỏng độ nhạy ở mục E.
- Yavarimanesh et al. (2022, N18, đọc toàn văn) ước tính cần 31 người cho một phép so sánh tương tự: mô hình PAT/đặc trưng PPG ngón tay so với baseline sau một năm, kiểm định t ghép cặp, mức 0,05, power 0,8. Vì vậy ≥ 15 người có thể không đủ nhạy, và con số này phải được đưa vào mô phỏng độ nhạy (bổ sung 2026-10-30).
- **Hiện trạng:** chưa có prototype, chưa có phê duyệt đạo đức và chưa có dữ liệu cuff. PulseDB **không** trả lời được RQ1, vì nhãn là ABP xâm lấn chứ không phải cuff, và dữ liệu không có cấu trúc phiên theo thời gian. PulseDB chỉ dùng để phát triển và kiểm tra đặc trưng.

---

## 5. RQ2 (phụ): Cách chia dữ liệu và đánh giá cùng phiên so với khác phiên

> **Câu hỏi:** (a) Trên PulseDB, sai số ước lượng BP tăng bao nhiêu khi chuyển từ chia ngẫu nhiên theo cửa sổ sang chia theo người? (b) Trên dữ liệu prototype, đánh giá ngay trong phiên hiệu chuẩn cho sai số lạc quan hơn bao nhiêu so với đánh giá ở các phiên khác ngày?

**Thay đổi ở v0.4 (đề xuất 2026-10-29, chờ thầy):** RQ2a là phép kiểm tra rò rỉ, báo ở phụ lục của bài. RQ2b đổi từ "chia theo phiên", vốn trùng với thiết kế của RQ1, thành so sánh cùng phiên với khác phiên. Một số nghiên cứu gần nhất chỉ đánh giá trong một buổi (N1, N2), còn N7 chỉ đo lại vào ngày hôm sau ở 11 người ([tổng quan 2026-10-29](literature/literature_update_2026-10-29.md)), nên RQ2b đo được cách đánh giá trong một buổi lạc quan đến mức nào trên dữ liệu của nhóm.

### A. Giả thuyết

- **$H_{0,\text{RQ2a}}$:** MAE không khác nhau giữa chia ngẫu nhiên theo cửa sổ và chia theo người.
- **$H_{1,\text{RQ2a}}$:** MAE khi chia theo người cao hơn khi chia ngẫu nhiên theo cửa sổ.
- **$H_{0,\text{RQ2b}}$:** MAE trên cuff nghiệm pháp ở phiên ≥ 2 không cao hơn MAE trên cuff nghiệm pháp ở phiên 1.
- **$H_{1,\text{RQ2b}}$:** MAE ở phiên ≥ 2 cao hơn.

Hiệu ứng mà RQ2a khảo sát đã được ghi nhận trong y văn (Yoshizawa 2023, Mehta 2024, Moulaeifard 2025). RQ2a là bước **kiểm chứng lại và lượng hóa** hiệu ứng này trong pipeline của nhóm, không phải phát hiện mới. Chênh lệch sai số giữa các cách chia tự nó không chứng minh rằng nguyên nhân duy nhất là mô hình nhận dạng người.

### B. Các cách chia

1. **A — Ngẫu nhiên theo cửa sổ (đối chứng có rò rỉ):** chia ngẫu nhiên các cửa sổ/đoạn, nên cùng một người có thể nằm ở nhiều tập. Cách chia này chỉ dùng để minh họa rò rỉ, không dùng để chọn mô hình hay báo cáo hiệu năng chính.
2. **B — Theo người:** mỗi người chỉ nằm trong một tập (train/validation/test cố định theo `subject_id`, hoặc k-fold/LOSO theo người).
3. **C — Cùng phiên so với khác phiên (RQ2b, chỉ với dữ liệu prototype; thay cho cách chia "theo phiên" của v0.3):**
   - Dùng chính dự đoán vòng ngoài của LOSO lồng ở RQ1, không huấn luyện hay tuning thêm. Dự đoán cho cuff nghiệm pháp ở phiên 1 của người test phải được sinh trong cùng lần chạy vòng ngoài và được khai báo trong commit khóa.
   - Với mỗi người $s$, **tập cùng phiên** gồm các lần cuff nghiệm pháp M1, M2 ở phiên 1, còn **tập khác phiên** gồm các lần cuff M1, M2 ở phiên ≥ 2. Cả hai tập đều so với cùng một $`\text{BP}_0`$ (trung bình M0 phiên 1). Chỉ so cuff nghiệm pháp, và báo kèm phân bố nghiệm pháp của từng tập.
   - **Chuẩn hóa theo nghiệm pháp:** với mỗi người, MAE của mỗi tập được tính riêng cho từng nghiệm pháp, rồi lấy trung bình đều trên các nghiệm pháp có mặt ở **cả hai** tập của người đó; các phiên ≥ 2 được gộp chung. Người không có nghiệm pháp chung nào thì không được tính. Nhờ vậy, $e_s$ không tăng chỉ vì nghiệm pháp khó chiếm tỷ trọng lớn hơn ở phiên sau. Bản thô (gộp theo số cuff thực có) được báo kèm như phân tích phụ, ghi rõ là gồm cả phần do thay đổi cơ cấu nghiệm pháp. Với bộ M1, M2, theo kế hoạch mỗi người có hai cuff nghiệm pháp ở tập cùng phiên và hai đến bốn cuff ở tập khác phiên (một hay hai phiên sau), chưa kể lần đo thiếu hay đo lại. Người thiếu M2 thì chỉ còn so được M1. Vì vậy có thêm phân tích độ nhạy chỉ trên những người có cả M1 và M2 ở cả hai tập, và báo số cuff theo nghiệm pháp ở từng tập.
   - Tập cùng phiên **không** làm thay đổi endpoint của RQ1: cuff nghiệm pháp ở phiên 1 vẫn không dùng để hiệu chuẩn và không vào tập đánh giá của RQ1.
   - Chênh lệch giữa hai tập không chỉ do hiệu chuẩn trôi theo thời gian, mà còn do đeo lại thiết bị, BP nền khác nhau giữa các ngày, PEP, và việc người tham gia quen dần với nghiệm pháp ở phiên sau (nhất là tính nhẩm M2). Không quy toàn bộ chênh lệch cho một nguyên nhân.

Với RQ2a, cách tạo cửa sổ, đặc trưng và thuật toán được giữ nguyên giữa các cách chia; chỉ cách chia thay đổi.

### C. Mô hình so sánh

- **RQ2a:** dùng cùng một mô hình cho cách chia A và B, là B3 XGBoost (đã có trong code, xem mục 7) hoặc Ridge. Chạy thêm B0 (trung bình train) trên từng cách chia để biết mức sai số khi không dùng tín hiệu.
- **RQ2b:** các mô hình của RQ1 (zero-change, PPG-only, PPG + PAT), dùng cùng dự đoán vòng ngoài.

### D. Chỉ số

- **RQ2a:** MAE, RMSE và ME ± SD cho SBP và DBP; $`\Delta\text{MAE} = \text{MAE}_{\text{B}} - \text{MAE}_{\text{A}}`$ và tỷ lệ suy giảm $`(\text{MAE}_{\text{nghiêm}} - \text{MAE}_{\text{ngẫu nhiên}}) / \text{MAE}_{\text{ngẫu nhiên}} \times 100\%`$.
- **RQ2b:** $`e_s = \text{MAE}_s(\text{khác phiên}) - \text{MAE}_s(\text{cùng phiên})`$ cho từng mô hình, với MAE chuẩn hóa theo nghiệm pháp (mục B). Báo trung bình và CI 95% bootstrap theo người, riêng cho SBP, DBP và theo từng nghiệm pháp.
- CI bootstrap theo người cho từng MAE.
- Bland–Altman: độ lệch trung bình và **giới hạn đồng thuận 95%** (LoA); không gọi LoA là khoảng tin cậy. Với dữ liệu đo lặp, cần phương pháp LoA dành cho đo lặp (chưa khóa).

### E. Tiêu chí kết luận

Báo cáo ΔMAE (RQ2a) và $e_s$ (RQ2b) kèm CI theo người, riêng cho SBP và DBP; không đặt ngưỡng đạt/không đạt. RQ2a được báo ở phụ lục như một phép kiểm tra rò rỉ. Mức suy giảm 40% và ngưỡng $p < 0{,}001$ trong bản v0.1 là đề xuất chưa có căn cứ và **không** được dùng làm tiêu chí. Kế hoạch kiểm định phải được duyệt trước khi mở test.

### F. Rủi ro

- Nếu dải BP hẹp, mọi mô hình đều tiến gần B0/zero-change và chênh lệch giữa các cách chia khó đo được.
- Với PulseDB, mỗi người có rất nhiều đoạn 10 giây gần nhau về thời gian. Chia ngẫu nhiên theo đoạn gần như chắc chắn gây rò rỉ, nên chênh lệch trên PulseDB có thể lớn hơn so với trên dữ liệu prototype.

### G. Dữ liệu và tính khả thi

- **Phần (a), làm được ngay:** dùng PulseDB (phần VitalDB trên Kaggle). Reader, inventory và split theo người `pulsedb-split-v2` đã có, cùng với pipeline B0/B3 trên split này (mục 7). Pipeline đã chạy trên raw PulseDB VitalDB Train 400 người ngày 2026-10-25, chỉ chấm val ([báo cáo](../reports/weekly/week_05/pulsedb_b3_v1/README.md)). Còn cần thêm một hàm chia ngẫu nhiên theo đoạn, chỉ dùng cho đối chứng A.
- **Rào chắn cho phần (a), chốt 2026-10-29:**
  - RQ2(a) chỉ chạy trên những người thuộc train ∪ val của split v2, so sánh chia theo đoạn với chia theo người (k-fold theo người) trên cùng pool đó.
  - 40 người test của split v2 và tập CalFree không tham gia.
  - Hàm chia ngẫu nhiên theo đoạn phải từ chối mọi dòng có `split = test`. Test cho điều này phải được viết trước, rồi mới viết hàm.
  - Không dùng CalBased Test, vì tập này có cùng người với Train; tập này đã bị loại trong quyết định về pool ngày 2026-10-24 ([provenance](pulsedb_provenance.md)).
  - Theo Bảng 4 của bài báo PulseDB (Wang et al., 2023), phần VitalDB có 1.293 người ở cả Train lẫn CalBased Test và 144 người ở CalFree Test. Các con số 2.506 và 279 là tổng của MIMIC-III + VitalDB.
- **Phần (b):** dùng đúng dữ liệu của RQ1 (cấu trúc `subject_id → session_id → event_id → window_id`), không cần thêm phiên. Chỉ tính trên những người có cuff nghiệm pháp ở cả phiên 1 và phiên ≥ 2. Nếu hội đồng không duyệt nghiệm pháp M1, M2 thì không làm được RQ2b theo định nghĩa trên.

---

## 6. RQ3 (thăm dò): Từ chối dự đoán theo SQI và độ bất định

**Thay đổi ở v0.4 (đề xuất 2026-10-29, chờ thầy):** RQ3 là phân tích thăm dò, không phải câu hỏi xác nhận. Protocol yêu cầu ngồi yên lúc đo, nên có thể có ít đoạn nhiễu tự nhiên (mục G). Nếu không đủ dữ liệu thì không dùng RQ3 để đưa ra tuyên bố trong bài.

> **Câu hỏi:** Ở cùng tỷ lệ giữ lại (coverage), nếu từ chối dự đoán dựa trên SQI của tín hiệu đầu vào kết hợp với độ bất định của mô hình thì sai số trên phần được giữ lại có thấp hơn so với từ chối ngẫu nhiên và so với chỉ dùng SQI hay không?

### A. Giả thuyết

- **$H_{0,\text{RQ3}}$:** Ở cùng coverage, MAE trên phần được giữ của chiến lược SQI + độ bất định không thấp hơn MAE của từ chối ngẫu nhiên.
- **$H_{1,\text{RQ3}}$:** Chiến lược SQI + độ bất định cho đường cong risk–coverage tốt hơn từ chối ngẫu nhiên và tốt hơn SQI đơn lẻ; điểm số từ chối tương quan dương với độ lớn sai số $|e|$.

Mức từ chối 15–20% và mức giảm MAE 20% trong bản v0.1 là đề xuất chưa có căn cứ và **không** được dùng làm tiêu chí.

### B. Biến nghiên cứu

- **Đơn vị từ chối:** một quan sát của phân tích BP, tức một lần đo cuff (prototype) hoặc một đoạn (PulseDB). SQI được tính trên từng cửa sổ, rồi tổng hợp lên mức quan sát theo quy tắc khóa trước.
- **SQI của PPG:** skewness (Elgendi, 2016), độ nhất quán hình dạng nhịp so với template trong cửa sổ (đã có trong SQI v0) và tỷ lệ ghép nhịp R–foot. Perfusion index cần thành phần DC và đơn vị vật lý, hiện chưa có.
- **SQI của ECG:** biên độ R so với nhiễu nền, độ đều của RR và độ trôi đường nền.
- **Độ bất định:** chọn phương pháp hợp với mô hình đang dùng (Ridge/Random Forest/XGBoost): phương sai giữa các mô hình trong ensemble, độ rộng khoảng của quantile regression, hoặc khoảng conformal (Shen et al., 2025). MC Dropout hay evidential regression chỉ áp dụng khi dùng mạng nơ-ron.
- **Biến điều khiển:** coverage từ 100% xuống khoảng 70% (tỷ lệ từ chối 0–30%).
- **Đầu ra:** MAE trên phần được giữ ở từng mức coverage, riêng cho SBP và DBP.

### C. Chiến lược so sánh

1. **Không từ chối** (coverage = 100%).
2. **Từ chối ngẫu nhiên** ở cùng coverage, lặp nhiều lần để lấy phân phối.
3. **Chỉ SQI.**
4. **Chỉ độ bất định.**
5. **SQI + độ bất định** (chiến lược đề xuất).

### D. Chỉ số

- Đường cong risk–coverage (risk = MAE trên phần được giữ) và diện tích dưới đường cong (AURC, càng nhỏ càng tốt).
- MAE tại một mức coverage chọn trên validation, đánh giá một lần trên test.
- Tương quan hạng Spearman giữa điểm số từ chối và $|e|$.
- Tỷ lệ phát hiện các quan sát có $|e| > 10$ mmHg, chỉ để mô tả.
- Báo cáo coverage theo từng người: một chiến lược có thể đạt coverage tổng 80% nhưng từ chối gần hết dữ liệu của vài người.
- **Phân bố |ΔBP| tham chiếu của các lần cuff bị từ chối so với các lần được giữ (v0.4):** nếu chiến lược chủ yếu loại những lần BP thay đổi lớn thì việc MAE giảm không chứng minh được rằng nó phát hiện tín hiệu kém.

Lưu ý: "coverage" ở đây là **tỷ lệ quan sát được giữ lại**, khác với coverage của khoảng dự đoán trong conformal prediction.

### E. Tiêu chí kết luận

Kết quả ủng hộ $H_1$ khi đường cong của chiến lược đề xuất nằm dưới đường cong của từ chối ngẫu nhiên và của SQI đơn lẻ trên phần lớn dải coverage, và CI bootstrap theo người của chênh lệch MAE tại mức coverage đã chọn trên validation nằm dưới 0. Mức vận hành chỉ được chọn trên validation; với dữ liệu prototype, validation là vòng trong của LOSO lồng. Vì RQ3 là phân tích thăm dò (v0.4), kết quả chỉ được báo như kết quả thăm dò, không đưa vào kết luận chính.

### F. Rủi ro

- Ngưỡng quá chặt sẽ từ chối quá nhiều, làm giảm tính hữu dụng của thiết bị.
- SQI và độ bất định có thể tương quan mạnh với nhau, khiến việc kết hợp không thêm thông tin.
- Từ chối không đều giữa những người tham gia làm MAE "tốt lên" chỉ vì đã loại bỏ những người khó.

### G. Dữ liệu và tính khả thi

- Cần dữ liệu có nhãn BP, gồm cả đoạn tốt lẫn đoạn kém chất lượng xảy ra tự nhiên. Protocol của prototype yêu cầu ngồi yên lúc đo, nên số đoạn kém có thể ít. PulseDB là dữ liệu đã làm sạch, nên dải chất lượng hẹp.
- Các lựa chọn cần nhóm quyết định:
  - (a) trong protocol, ghi nhận các lần đo kém xảy ra tự nhiên thay vì đo lại ngay;
  - (b) xin truy cập dataset có nhãn chất lượng như CardioWave-Portable (cần credentialed access và DUA);
  - (c) giới hạn RQ3 thành phân tích thăm dò (đã chọn ở v0.4, chờ thầy xác nhận).

  Ngoài (c), vẫn có thể làm thêm (a) và (b).

---

## 7. Bảng tổng hợp baseline và đối chiếu với code

| Tên trong RQ | Tên trong code / kế hoạch | Bài toán | Trạng thái |
|---|---|---|---|
| — | **B0** `PopulationMeanBaseline` (trung bình nhãn train; trong b3-pipeline-v1 là trung bình của các trung bình theo người) | BP tuyệt đối cho người mới; dùng cho RQ2a | Đã cài; đã chạy sơ bộ trên CSV PulseDB (Tuần 3, nay chỉ còn là lịch sử), rồi chạy cùng B3 trên raw PulseDB VitalDB Train 400 người ngày 2026-10-25, chỉ chấm val |
| **Zero-change** | **B1** `PersonalMeanBaseline`, khi $`\text{BP}_0`$ là trung bình các lần cuff hiệu chuẩn | $`\widehat{\text{BP}} = \text{BP}_0`$, tương đương $`\Delta\widehat{\text{BP}} = 0`$; RQ1 | Đã cài, mới kiểm tra bằng dữ liệu giả lập |
| — | **B3** `XGBoostBaseline` (`software/models/xgboost_baseline.py`), đặc trưng `pulsedb-simple-stats-v0`; pipeline `software/pulsedb/pipeline.py`, runner `scripts/run_b3_pulsedb.py` | BP tuyệt đối (không phải ΔBP) trên PulseDB; RQ2a | Đã cài: fit trên train, chỉ đánh giá trên val (không trích đặc trưng của tập test); đã chạy trên raw PulseDB ngày 2026-10-25 (val 40 người), chưa chấm test |
| — | **B2** nhân khẩu học + HR từ ECG (`software/pulsedb/pipeline_b2.py`, `features_b2.py`; runner `scripts/run_b2_pulsedb.py`; định nghĩa [b2_pulsedb_definition.md](protocol/b2_pulsedb_definition.md)) | BP tuyệt đối trên PulseDB | Có code và test SYNTHETIC; định nghĩa chưa được duyệt, runner từ chối chạy, chưa có kết quả |
| PAT-only, PPG-only, PPG + PAT | Chưa có | ΔBP; RQ1 | Chưa triển khai, cần dữ liệu prototype |
| Không từ chối / ngẫu nhiên / SQI / SQI + độ bất định | Cờ SQI `features-sqi-v1`/`v2` trong `week04.py`, cờ cử động `motion-sqi-v0` (`motion_sqi.py`); chưa có cơ chế từ chối | RQ3 | Mới có cờ SQI, chưa có ngưỡng được khóa |

Tên B0/B1/B3 trong code không khớp với số thứ tự "Baseline 1/2/3" của bản v0.1; bảng này thay cho cách đánh số cũ.

---

## 8. Các điểm cần nhóm và giảng viên xác nhận

> [!IMPORTANT]
> - [ ] **Đại lượng dự đoán:** xác nhận rằng RQ1 dự đoán ΔSBP/ΔDBP có hiệu chuẩn cá nhân, không làm BP tuyệt đối không hiệu chuẩn.
> - [ ] **Phép so sánh chính của RQ1:** PPG-only so với PPG + PAT trên cùng tập lần đo, cùng thuật toán.
> - [ ] **Endpoint RQ1 khi có nghiệm pháp M0–M2** (đề xuất của nhóm 2026-10-29, mục 4.B): mọi lần cuff hợp lệ ở phiên ≥ 2, so với $`\text{BP}_0`$ = trung bình M0 phiên 1; nghiệm pháp là biến phân tầng; phân tích chỉ trên M0 là phân tích phụ.
> - [ ] **Cỡ mẫu và kiểm định:** trần tuyển 25 người và số phiên (mục 4.G, đề xuất 2026-10-29). Tất cả được khóa trước khi mở test, dựa trên pilot.
> - [ ] **Tiêu chí kết luận RQ1 v0.4** (mục 4.E, đề xuất 2026-10-29):
>   - cùng chuẩn CI cho so sánh với zero-change và với PPG-only;
>   - chọn phương án đa kiểm định A (giao–hợp, Holm giữa SBP/DBP) hay B (Holm trên bốn so sánh);
>   - giá trị δ và cách lấy δ từ độ lặp lại của cuff ở pilot;
>   - estimand (mục 4.A).
> - [x] **RQ2:** phần (a) dùng train ∪ val của split v2, không dùng test, CalFree hay CalBased (chốt 2026-10-29, mục 5.G); random split chỉ là đối chứng để minh họa.
> - [ ] **RQ2 v0.4** (đề xuất 2026-10-29): RQ2a báo ở phụ lục; RQ2b đổi thành so sánh cùng phiên với khác phiên (mục 5.B), và cần sinh dự đoán cho cuff nghiệm pháp phiên 1 trong cùng lần chạy vòng ngoài.
> - [ ] **RQ3:**
>   - là phân tích thăm dò (v0.4, đề xuất 2026-10-29);
>   - nguồn dữ liệu có đoạn nhiễu tự nhiên (mục 6.G);
>   - phương pháp đo độ bất định;
>   - mức coverage chọn ở vòng trong.
> - [ ] **Rủi ro áp lực tiếp xúc** (mục 4.F): cách chuẩn hóa vị trí và nấc dây đeo trong protocol.
> - [ ] **Mốc PEP:** PEP thường tính từ Q/QRS, còn PAT của dự án tính từ R; không đồng nhất hai mốc khi diễn giải.
