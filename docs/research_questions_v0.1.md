# Câu hỏi nghiên cứu (Research Questions) — v0.4

> **Người thực hiện:** Nguyễn Đức Huy
>
> **Vai trò:** Xử lý tín hiệu, PAT, thống kê, protocol, tổng quan tài liệu và điều phối bài báo
>
> **Ngày lập:** 2026-09-22; **cập nhật:** 2026-10-14 (v0.2: thêm phần vấn đề nghiên cứu, làm rõ phép so sánh chính của RQ1, tính khả thi của RQ2/RQ3 và đối chiếu tên baseline với code), 2026-10-29 (v0.3: endpoint RQ1 và mốc hiệu chuẩn khi có nghiệm pháp M0–M4, LOSO lồng, số phiên và cỡ mẫu theo [protocol v0.3](protocol/protocol_outline_v0.2.md); cập nhật bảng baseline), 2026-10-29 (v0.4: dẫn các nghiên cứu gần nhất; estimand RQ1; tiêu chí kết luận dùng CI cho cả so sánh với zero-change; mức hiệu ứng nhỏ nhất đáng quan tâm δ; rủi ro áp lực tiếp xúc; RQ2a chuyển thành kiểm tra rò rỉ ở phụ lục, RQ2b đổi thành đánh giá cùng phiên so với khác phiên; RQ3 thành phân tích thăm dò; cùng ngày bỏ nghiệm pháp M3, M4 theo protocol 6.4, endpoint và RQ2b còn M0–M2, thêm rủi ro dải ΔBP hẹp ở mục 4.F), 2026-10-30 (mục 1 và 4.F–4.G sửa theo lần tra có hệ thống: N18 đã đánh giá qua nhiều phiên với baseline chỉ hiệu chuẩn, nên khoảng trống hẹp lại; thêm nguồn về PEP và con số 31 người của N18)
>
> Các thay đổi của v0.4 là **đề xuất của nhóm ngày 2026-10-29, chờ thầy xác nhận**; phải khóa trước khi chạy vòng ngoài của LOSO lồng.
>
> Tên file giữ `v0.1` để không làm gãy liên kết.

---

## 1. Vấn đề nghiên cứu

Thiết bị đo huyết áp không vòng bít (cuffless) dựa trên PPG ở cổ tay thường cần hiệu chuẩn bằng một lần đo cuff, sau đó theo dõi thay đổi so với mốc này. Có ba vấn đề làm cho việc đánh giá các thiết bị này khó:

1. **Mốc hiệu chuẩn tự nó đã là một dự đoán tốt.** Nếu BP ít thay đổi sau hiệu chuẩn, chỉ cần giữ nguyên giá trị cuff ban đầu cũng cho sai số nhỏ. Mukkamala et al. (2021) chỉ ra điểm này bằng mô phỏng, và dự án Aurora (1.125 người) không tìm thấy mô hình dạng sóng nào dự đoán BP ngày hôm sau tốt hơn rõ rệt so với baseline chỉ dùng BP hiệu chuẩn (Mukkamala et al., 2023). Xem [tổng quan bổ sung](literature/literature_update_2026-10-14.md), S2–S3. Tổng quan gần nhất của cùng nhóm tác giả (Mukkamala et al., 2025; đọc toàn văn ngày 2026-10-29) cho rằng đến nay chưa có bằng chứng thuyết phục là phân tích dạng sóng hay PAT thêm được giá trị đáng kể ngoài cuff hiệu chuẩn hoặc dữ liệu nhân khẩu học ([N8](literature/literature_update_2026-10-29.md)).
2. **PAT không phải PTT.** ECG cho phép đo PAT (R-peak → chân sóng PPG), nhưng PAT chứa thời gian tiền tống máu (PEP), vốn thay đổi theo trạng thái giao cảm. Payne et al. (2006) cho thấy PEP chiếm 12–35% khoảng R → xung ngón tay. Vì vậy, việc thêm ECG có giúp hơn PPG đơn lẻ hay không là câu hỏi thực nghiệm, không suy ra được từ lý thuyết PTT.
3. **Cách chia dữ liệu làm kết quả đẹp giả.** Khi cửa sổ của cùng một người nằm ở cả tập huấn luyện và tập kiểm tra, sai số giảm đáng kể so với khi chia theo người (Yoshizawa et al., 2023; Mehta et al., 2024).

**Các nghiên cứu gần nhất (v0.4; sửa 2026-10-30 theo lần tra có hệ thống ngày 2026-10-29).** Đã có nghiên cứu đánh giá mô hình dựa trên PPG và mô hình dựa trên PAT so với baseline zero-change hoặc chỉ hiệu chuẩn, đánh giá theo người, kể cả qua nhiều phiên. Tuy vậy, chưa thấy so sánh ghép cặp PPG-only với PPG + PAT cho cùng một đầu ra qua nhiều phiên. Các nguồn dưới đây đều ở [tổng quan 2026-10-29](literature/literature_update_2026-10-29.md):

- **Trong một buổi đo** (PPG ở ngón tay, ngón chân hoặc tai):
  - Finnegan et al. (2023, N1) so các bộ đặc trưng PPG, ECG và PAT khi truyền phenylephrine; không có mô hình PPG + PAT.
  - Natarajan et al. (2021, N2) đánh giá đặc trưng PPG cộng PAT dưới các nghiệm pháp.
- **Qua nhiều phiên:** Yavarimanesh et al. (2022, N18, đọc toàn văn).
  - Thiết kế: đánh giá các mô hình tuyến tính dựa trên PAT hoặc đặc trưng dạng sóng PPG (tai, ngón tay, ngón chân) ở phiên cách khoảng một năm, so với baseline chỉ dùng trung bình cuff ban đầu. Nghiệm pháp gồm thở chậm, tính nhẩm, cold pressor ở chân và nitroglycerin.
  - Đối tượng: 10 người, 57 ± 18 tuổi; hệ số riêng từng người lập từ một phiên.
  - Các mô hình có PAT dự đoán SBP, còn mô hình chỉ PPG dự đoán DBP. Mỗi mô hình được so riêng với baseline, nên đây không phải so sánh ghép cặp cho cùng một đầu ra.
  - Kết quả: chỉ mô hình PAT ngón chân–SBP còn hữu ích sau một năm.
- **Trên dữ liệu cổ tay Aurora-BP (đo lưu động):** Cisnal et al. (2025, N19, mới đọc abstract) báo baseline tốt hơn mô hình dựa trên PAT tốt nhất ở SBP và tương đương ở DBP.
- **Nghiên cứu nhiều ngày, quy mô lớn trên thiết bị cổ tay:** Mieloszyk et al. (2022, [S4](literature/literature_update_2026-10-14.md)) và Liu et al. (2023, N6). Phần nhóm đã đọc (abstract) chưa cho thấy phép so sánh ghép cặp PPG-only với PPG + PAT so với baseline chỉ hiệu chuẩn.

Vì vậy, các yếu tố sau, đứng riêng hay gộp một phần, đều không phải điểm mới: nhiều phiên, baseline chỉ hiệu chuẩn, nghiệm pháp, đánh giá mô hình PAT và mô hình PPG so với baseline.

Phần có thể còn là đóng góp hẹp hơn ([tổng quan](literature/literature_update_2026-10-29.md) mục 5.1): so sánh ghép cặp, đăng ký trước, giữa PPG-only và PPG + PAT, với các điều kiện:

- thiết bị chỉ đặt ở cổ tay;
- các phiên cách nhau vài ngày đến 4 tuần;
- hiệu chuẩn bằng offset từ M0 phiên 1, hệ số chung cho mọi người học bằng LOSO lồng (khác N18);
- luôn so với zero-change.

Giới hạn của nhận định này:

- Chỉ trong phạm vi đã tra: PubMed, Europe PMC, OpenAlex, giai đoạn 2022–2026; chưa tra IEEE Xplore, Scopus.
- Phải kiểm lại sau khi đọc toàn văn N6: bài truy cập mở, nhưng tải tự động bị chặn.
- S4 chỉ dùng abstract: ngày 2026-10-29 đã quyết định không lấy toàn văn qua thư viện, nên nhận định chưa được kiểm với toàn văn S4, và bài báo phải nêu rõ giới hạn này.
- Không được viết thành "chưa có nghiên cứu nào".

**Mục tiêu nghiên cứu:** xây dựng nguyên mẫu đo ở cổ tay (nối USB với máy tính, điện cực ECG dán ở hai cổ tay) thu đồng bộ ECG và PPG, và dùng nó để kiểm tra, trên một nhóm nhỏ người khỏe mạnh, liệu PAT có làm giảm sai số dự đoán ΔSBP/ΔDBP ở các phiên đo sau hiệu chuẩn so với chỉ dùng PPG hay không. Đánh giá phải có baseline zero-change, chia dữ liệu theo người và theo thời gian, và khoảng tin cậy theo người.

Mục tiêu triển khai (chế tạo prototype, firmware, pipeline) là điều kiện để trả lời câu hỏi, không phải câu hỏi nghiên cứu.

---

## 2. Nguyên tắc phương pháp chung

1. **Đánh giá SBP và DBP riêng.** Hai đại lượng chịu ảnh hưởng của các yếu tố sinh lý khác nhau một phần (SBP gắn nhiều hơn với tống máu và độ cứng động mạch lớn, DBP với kháng lực ngoại vi). Không gộp thành một chỉ số sai số chung.
2. **Gọi đúng PAT.** Khoảng từ đỉnh R của ECG đến chân sóng PPG là PAT, `PAT = PEP + PTT` (cách viết gọn; mốc R không trùng mốc Q/QRS mà PEP thường dùng). Không áp trực tiếp phương trình của PTT lên PAT.
3. **Chống rò rỉ dữ liệu.** Chia theo người; với cá nhân hóa, dữ liệu hiệu chuẩn có trước dữ liệu kiểm tra. Một lần đo cuff là một nhãn; nhiều cửa sổ cùng lần đo không phải nhiều mẫu độc lập. Bootstrap lấy mẫu lại theo người. Các biện pháp này giảm nguy cơ mô hình nhận dạng người thay vì học quan hệ với BP, nhưng không loại trừ hoàn toàn mọi dạng rò rỉ.
4. **Không chọn gì trên tập test.** Đặc trưng, cửa sổ, ngưỡng SQI, siêu tham số và mức vận hành đều chọn trên train/validation; test chỉ dùng một lần sau khi đã khóa. Với dữ liệu prototype, việc này thực hiện bằng LOSO lồng ([protocol v0.3](protocol/protocol_outline_v0.2.md) mục 9.1, chốt 2026-10-29): siêu tham số chọn ở vòng trong; cửa sổ, mốc, SQI khóa trên pilot; vòng ngoài chạy một lần.

---

## 3. Tóm tắt ba câu hỏi nghiên cứu

| | Yếu tố khảo sát | So sánh với | Chỉ số chính | Dữ liệu cần | Làm được khi nào |
|---|---|---|---|---|---|
| **RQ1** (chính, xác nhận) | Thêm PAT (từ ECG) vào mô hình PPG | Cùng mô hình chỉ dùng PPG; zero-change | Trung bình theo người của chênh lệch MAE cho ΔSBP, ΔDBP, kèm CI 95% bootstrap theo người, đọc theo mức δ khóa trước (mục 4.E) | Prototype, ≥ 15 người đạt chuẩn, ≥ 2 phiên/người, nhãn cuff | Sau khi có phần cứng, phê duyệt đạo đức và thu dữ liệu |
| **RQ2** (phụ) | (a) Cách chia dữ liệu; (b) đánh giá cùng phiên so với khác phiên | (a) Chia ngẫu nhiên theo cửa sổ vs theo người; (b) cuff nghiệm pháp phiên 1 vs phiên ≥ 2 | Chênh lệch MAE, CI theo người | (a) PulseDB train ∪ val; (b) prototype, cùng dữ liệu RQ1 | (a) làm được ngay, báo ở phụ lục; (b) cần dữ liệu prototype |
| **RQ3** (thăm dò) | Từ chối dự đoán theo SQI và độ bất định | Không từ chối; từ chối ngẫu nhiên cùng coverage; SQI đơn lẻ; độ bất định đơn lẻ | Đường cong risk–coverage, MAE tại coverage chọn ở vòng trong | Dữ liệu có cả đoạn tốt và đoạn nhiễu tự nhiên, có nhãn | Phụ thuộc nguồn dữ liệu (xem 6.G) |

---

## 4. RQ1: Giá trị gia tăng của PAT sau hiệu chuẩn cá nhân

> **Câu hỏi:** Ở người khỏe mạnh 18–35 tuổi không có trong dữ liệu huấn luyện, sau khi hiệu chuẩn bằng trung bình các lần cuff M0 ở phiên 1, việc thêm PAT (tính từ ECG) vào mô hình đặc trưng PPG có làm giảm sai số dự đoán $`\Delta\text{SBP}`$ và $`\Delta\text{DBP}`$ ở các phiên đo sau (phiên 2–3) so với cùng mô hình chỉ dùng PPG, và giảm bao nhiêu?

### A. Giả thuyết

- **$H_{0,\text{RQ1}}$:** Với mỗi đầu ra (SBP, DBP), MAE theo người của mô hình PPG + PAT không thấp hơn MAE của mô hình PPG-only trên các phiên sau.
- **$H_{1,\text{RQ1}}$:** MAE theo người của mô hình PPG + PAT thấp hơn mô hình PPG-only.
- **So với zero-change (v0.4):** $H^{\text{ZC}}_{0,\text{RQ1}}$: MAE theo người của PPG + PAT không thấp hơn zero-change; $H^{\text{ZC}}_{1,\text{RQ1}}$: thấp hơn. Kết luận chính cần bác bỏ cả $H_{0,\text{RQ1}}$ lẫn $H^{\text{ZC}}_{0,\text{RQ1}}$ (mục E).

SBP và DBP được kiểm định riêng. Bằng chứng hiện có (Payne 2006: PAT gần như không giải thích DBP khi chưa trừ PEP; Aurora: mô hình dạng sóng không vượt baseline hiệu chuẩn) cho thấy không bác bỏ được $H_0$ là một khả năng thực tế. Kết quả đó vẫn được báo cáo đầy đủ.

**Estimand (v0.4, đề xuất 2026-10-29, chờ thầy):** $`\theta = \mathbb{E}_s[d_s]`$, trung bình qua người của $`d_s = \text{MAE}_s(\text{PPG+PAT}) - \text{MAE}_s(\text{PPG})`$, tính riêng cho ΔSBP và ΔDBP.

- **Quần thể:** người khỏe mạnh 18–35 tuổi thuộc vòng ngoài của LOSO lồng, tức không có trong dữ liệu huấn luyện của lượt đó và không phải người pilot.
- **Điều kiện:** hiệu chuẩn bằng $`\text{BP}_0`$ của phiên 1 (mục B), đánh giá trên endpoint ở mục B.
- **Trọng số:** trong một người, mỗi lần cuff có trọng số như nhau; khi tính $\theta$, mỗi người có trọng số như nhau, người nhiều lần cuff không chi phối kết quả.
- **Phạm vi kết luận:** chỉ cho các lần đo tính được PAT (mục C); tỷ lệ lần đo mất ECG báo kèm.
- **Ý nghĩa:** vì endpoint gộp M0–M2 (M3, M4 bỏ ngày 2026-10-29, protocol 6.4), $\theta$ đo khả năng theo dõi cả đáp ứng nghiệm pháp lẫn biến thiên lúc nghỉ ở phiên sau. Phân tích phụ chỉ M0 cho biết riêng phần biến thiên lúc nghỉ. Theo kế hoạch M0 chiếm hai trên bốn lần cuff mỗi phiên (trước khi bỏ M3, M4 là hai trên sáu), nên $\theta$ nghiêng về biến thiên lúc nghỉ. Kết luận chỉ áp dụng cho các nghiệm pháp đã làm, không suy ra tình huống lạnh hay gắng sức.

### B. Biến nghiên cứu

- **Đặc trưng PPG:** thời gian lên (rise time), độ rộng xung tại 50% biên độ, biên độ xung, HR tính từ PPG; ứng viên mở rộng là tỷ số diện tích tâm thu/tâm trương và PIR (Ding et al., 2016). Bộ đặc trưng v0 đã có trong code Tuần 4 (`software/feature_extraction/week04.py`), chưa được khóa.
- **Đặc trưng từ ECG:** PAT (R-peak → PPG foot cùng nhịp, trung vị trong cửa sổ) và $`\Delta\text{PAT} = \text{PAT}_{\text{hiện tại}} - \text{PAT}_{\text{hiệu chuẩn}}`$. HR và HRV ngắn hạn từ ECG là đặc trưng phụ cho phân tích ablation.
- **Mốc hiệu chuẩn (chốt 2026-10-29):** $`\text{SBP}_0`$, $`\text{DBP}_0`$ là trung bình các lần cuff M0 (nghỉ ngồi) hợp lệ ở phiên 1; $`\text{PAT}_{\text{hiệu chuẩn}}`$ và đặc trưng nền lấy từ cửa sổ của các lần cuff đó.
- **Đầu ra:** $`\Delta\text{SBP} = \text{SBP}_{\text{target}} - \text{SBP}_0`$, $`\Delta\text{DBP} = \text{DBP}_{\text{target}} - \text{DBP}_0`$ (mmHg). Ước lượng BP cuối: $`\widehat{\text{BP}} = \text{BP}_0 + \Delta\widehat{\text{BP}}`$.
- **Tập đánh giá (endpoint chính; đề xuất của nhóm 2026-10-29, chờ thầy xác nhận):** mọi lần cuff hợp lệ ở phiên ≥ 2, gồm M0 và các nghiệm pháp M1, M2 ([protocol v0.3](protocol/protocol_outline_v0.2.md) mục 6.4; M3, M4 bỏ ngày 2026-10-29). Nghiệm pháp là biến phân tầng. Phân tích phụ định trước: chỉ các lần cuff M0 ở phiên ≥ 2. Cuff nghiệm pháp ở phiên 1 của người được đánh giá không dùng để hiệu chuẩn và không vào tập đánh giá.

### C. Các mô hình so sánh

| Mô hình | Đầu vào | Vai trò |
|---|---|---|
| **Zero-change** | Không có đặc trưng; $`\Delta\widehat{\text{BP}} = 0`$, tức $`\widehat{\text{BP}} = \text{BP}_0`$ | Baseline bắt buộc. Mô hình không vượt baseline này thì không có giá trị gia tăng so với chỉ dùng mốc hiệu chuẩn |
| **PAT-only** | $`\Delta(1/\text{PAT}^2)`$ hoặc $`\Delta\text{PAT}`$ | Kiểm tra lượng thông tin của riêng PAT. Hệ số học ở mức quần thể trên người thuộc tập train, vì người được đánh giá chỉ đóng góp $`\text{BP}_0`$ (trung bình M0 phiên 1) cho hiệu chuẩn; cuff nghiệm pháp phiên 1 của họ không dùng để fit hệ số riêng. Đây là hồi quy thực nghiệm, không phải áp Moens–Korteweg lên PAT |
| **PPG-only** | Đặc trưng PPG + HR từ PPG | Đối chứng chính của RQ1 |
| **PPG + PAT** | Như PPG-only, thêm PAT/ΔPAT | Mô hình chính của RQ1 |
| **PPG + PAT + ECG-HRV** | Thêm HR/HRV từ ECG | Ablation phụ, tách phần đóng góp của PAT với phần của các đặc trưng ECG khác |

**Phép so sánh chính là PPG-only với PPG + PAT**, dùng cùng thuật toán (ví dụ Ridge), cùng ngân sách chọn siêu tham số ở vòng trong của LOSO lồng (protocol mục 9.1) và **cùng tập lần đo đánh giá** (những lần đo tính được cả PAT và đặc trưng PPG; phân tích chính không lọc thêm theo ngưỡng SQI, lọc SQI là phân tích phụ đăng ký trước: protocol mục 7.3, chốt 2026-10-29). Nếu PPG-only được đánh giá trên nhiều lần đo hơn (gồm cả lần ECG hỏng), hai mô hình sẽ bị so trên hai tập khác nhau. Kết quả PPG-only trên toàn bộ lần đo và tỷ lệ lần đo mất ECG được báo cáo riêng như phân tích phụ.

### D. Chỉ số đánh giá

Tính riêng cho ΔSBP và ΔDBP:

- MAE, ME ± SD của sai số (sai số = dự đoán − tham chiếu), tổng hợp đều theo người (như `evaluate_bp`).
- **Hiệu ứng chính:** $`d_s = \text{MAE}_s(\text{PPG+PAT}) - \text{MAE}_s(\text{PPG})`$ cho từng người $s$; báo cáo trung bình của $d_s$ và CI 95% bootstrap theo người (`software/evaluation/subject_bootstrap.py`). Wilcoxon signed-rank trên $d_s$ là phân tích hỗ trợ.
- **So với zero-change (v0.4):** $`d^{0}_s = \text{MAE}_s(\text{PPG+PAT}) - \text{MAE}_s(\text{zero-change})`$; báo trung bình và CI 95% bootstrap theo người như $d_s$, dùng cùng các lượt bootstrap.
- Pearson $r$ giữa ΔBP tham chiếu và ΔBP dự đoán (không xác định cho zero-change vì dự đoán là hằng).
- Tỷ lệ lần đo có $|e| \le 5$ và $\le 10$ mmHg, chỉ để mô tả; không phải tiêu chí AAMI/ISO.
- **Bắt buộc báo cáo kèm:** SD của ΔBP tham chiếu và tỷ lệ lần đo có $|\Delta\text{BP}| > 5$ mmHg. Nếu ΔBP tham chiếu rất hẹp, mọi so sánh MAE đều kém nhạy, và người đọc cần biết điều đó.
- Các chỉ số trên báo cả tổng và theo từng nghiệm pháp (M0–M2), và cho phân tích phụ chỉ M0.

### E. Tiêu chí kết luận

Viết lại ở v0.4 (đề xuất 2026-10-29, chờ thầy; khóa trước khi chạy vòng ngoài). Bản v0.3 chỉ đòi "MAE thấp hơn zero-change" mà không có CI, trong khi so với PPG-only lại đòi CI: hai chuẩn bằng chứng lệch nhau.

- **Kết luận chính, riêng cho từng đầu ra (SBP, DBP):** "thêm PAT làm giảm sai số so với PPG-only và vượt zero-change" chỉ khi **cả hai** điều kiện đạt (mức độ lợi ích đọc theo δ ở dưới; chỉ gọi là lợi ích đáng quan tâm khi $U < -\delta$):
  1. CI 95% bootstrap theo người của trung bình $d^{0}_s$ (PPG + PAT so với zero-change) nằm hoàn toàn dưới 0;
  2. CI 95% bootstrap theo người của trung bình $d_s$ (PPG + PAT so với PPG-only) nằm hoàn toàn dưới 0.

  Mức 95% ở đây là trước hiệu chỉnh; mức thực dùng theo phương án đa kiểm định bên dưới.
- **Đa kiểm định, chọn một phương án trước khi chạy vòng ngoài:**
  - **Phương án A (đề xuất):** với mỗi đầu ra, kết luận chính là giao của hai điều kiện trên (kiểm định giao–hợp, intersection–union): mỗi điều kiện xét bằng CI hai phía ở cùng một mức, không hiệu chỉnh thêm trong cùng đầu ra, vì kết luận chỉ đúng khi cả hai cùng đạt; giữa SBP và DBP dùng Holm, nên mức CI của từng đầu ra theo thứ tự Holm. Kết luận riêng lẻ khác (ví dụ chỉ vượt PPG-only) là phân tích phụ, không dùng để tuyên bố.
  - **Phương án B:** Holm trên bốn phép so sánh (2 đầu ra × 2 đối chứng).
  - Phương án nào cũng báo CI tương ứng với mức hiệu chỉnh đã chọn.
- **Mức hiệu ứng nhỏ nhất đáng quan tâm δ** ($`\delta_{\text{SBP}}`$, $`\delta_{\text{DBP}}`$, mmHg): khóa trước vòng ngoài, căn cứ vào độ lặp lại của cuff tham chiếu (chênh lệch giữa các lần cuff M0 liền nhau ở pilot) và lý do ứng dụng. Không dùng lại 1,5/1,0 mmHg của bản v0.1 vì con số đó chưa có căn cứ. Đọc CI của trung bình $d_s$ (cùng mức với kết luận chính), ký hiệu $[L; U]$:
  - $U < -\delta$: thêm PAT giảm sai số ít nhất δ.
  - $U < 0$ và $L < -\delta \le U$: thêm PAT có lợi, nhưng chưa chắc đạt δ.
  - $-\delta \le L$ và $U \le \delta$: PPG-only và PPG + PAT tương đương trong phạm vi δ; đây là kết quả âm tính có thông tin. Nếu đồng thời $U < 0$ thì có lợi nhưng nhỏ hơn mức đáng quan tâm; nếu $L > 0$ thì sai số tăng nhưng nhỏ hơn δ. Cách đọc này dùng CI hai phía ở mức trên, nên thận trọng hơn kiểm định TOST thông thường (TOST ở mức 5% tương ứng CI 90%).
  - $L > 0$ và $U > \delta$: thêm PAT làm sai số tăng; báo như một kết quả.
  - Các trường hợp còn lại (CI chứa 0 và vượt ra ngoài $[-\delta; \delta]$): **chưa kết luận**, phép so sánh thiếu độ nhạy; không viết là "PAT không giúp".
- **Độ nhạy dự kiến:** trước khi thu chính, ước lượng độ rộng CI kỳ vọng bằng mô phỏng theo nhiều mức phương sai của $d_s$ (dùng số liệu pilot nếu có), để biết với ≥ 15 người có loại trừ được δ hay không.
- Nếu không đạt đồng thời hai điều kiện: không tuyên bố kết luận chính và không khẳng định PAT có lợi. Vẫn báo trạng thái từng phép so sánh (so với PPG-only, so với zero-change) như phân tích phụ, kèm ước lượng và CI theo cách đọc ở trên; một phép so sánh đạt riêng lẻ không đủ để tuyên bố.

### F. Rủi ro phương pháp

- **PEP thay đổi giữa các phiên** (căng thẳng, tư thế, nhiệt độ) làm PAT thay đổi mà BP không đổi. Nguồn bổ sung 2026-10-30 (đều mới đọc abstract, [tổng quan 2026-10-29](literature/literature_update_2026-10-29.md)):
  - stress tinh thần làm PEP giảm (N11);
  - phản ứng PEP mạnh hơn khi nhiệm vụ khó hơn (N30);
  - với nhiệm vụ tinh thần, tương quan giữa thay đổi PAT và thay đổi SBP không có ý nghĩa thống kê trong nghiên cứu đó (N25, r = −0,12);
  - khi đau do lạnh, PTT giảm còn PEP không đổi (N29).
- **PAT ở cổ tay chịu ảnh hưởng của co cơ trơn mạch ngoại vi**, độc lập với mức BP (Mukkamala et al., 2023).
- **ΔBP giữa các phiên nhỏ** ở người trẻ khỏe mạnh đo lúc nghỉ, làm zero-change khó bị vượt và giảm độ nhạy của so sánh.
- **Áp lực tiếp xúc và cách đeo thay đổi giữa các phiên (v0.4).** Natarajan et al. (2021, [N2](literature/literature_update_2026-10-29.md)) ghi nhận dạng sóng PPG chịu ảnh hưởng của áp lực tiếp xúc nhiều hơn PAT. Nếu độ chặt dây hay vị trí đeo ở các phiên sau khác phiên 1, PPG-only có thể kém đi vì lý do kỹ thuật, làm PAT trông có lợi mà không do sinh lý. Giảm rủi ro bằng cách chuẩn hóa cách đeo trong protocol (vị trí, nấc dây) và ghi lại ở mỗi phiên; khi diễn giải $d_s$ phải nêu rủi ro này.
- **Dải ΔBP hẹp khi chỉ còn M0–M2 (2026-10-29).** Bỏ M3 (ngâm chân nước lạnh) và M4 (đạp xe) vì khó thực hiện ở phòng thí nghiệm ([protocol](protocol/protocol_outline_v0.2.md) mục 6.4). M2 (tính nhẩm im lặng) là nghiệm pháp duy nhất dự kiến làm BP tăng, và stress tâm lý làm PEP đổi nên PAT có thể đổi mà BP không đổi (rủi ro ở trên). Theo abstract của N25, SBP còn giảm trong nhiệm vụ tinh thần của nghiên cứu đó, nên M2 không chắc làm SBP tăng. Dải ΔBP hẹp làm baseline zero-change khó bị vượt, CI của $d_s$ dễ nằm trong $[-\delta; \delta]$ hoặc rơi vào "chưa kết luận". Mô phỏng độ nhạy ở mục E phải dùng dải ΔBP dự kiến của bộ M0–M2, làm riêng cho SBP và DBP. Khi viết bài phải báo SD của ΔBP tham chiếu theo nghiệm pháp, và không suy kết quả ra các tình huống làm BP đổi mạnh (lạnh, gắng sức).
- **ECG đạo trình I giữa hai cổ tay (điện cực dán, chốt 2026-10-23) có biên độ nhỏ hơn ECG ngực và dễ nhiễu khi một trong hai tay cử động**, gây sai lệch R-peak. Lần đo mất ECG không ngẫu nhiên có thể làm lệch tập đánh giá; vì vậy phải so trên cùng tập (mục C).
- **Độ phân giải thời gian:** ECG 512 sps (khoảng 1,95 ms mỗi mẫu) và PPG 200 sps mỗi khe (5 ms mỗi mẫu; chốt 2026-10-24); sai số định vị mốc, nhất là chân sóng PPG, và đồng bộ hai kênh cộng trực tiếp vào PAT.

### G. Dữ liệu tối thiểu và tính khả thi

- Mục tiêu ≥ 15 người đạt chuẩn, tuyển tối đa 25 người (trần đề xuất của nhóm, chờ thầy). Mục tiêu 3 phiên mỗi người, tối thiểu 2 (1 phiên hiệu chuẩn + ≥ 1 phiên đánh giá), mọi phiên trong 4 tuần kể từ phiên 1 (protocol v0.3 mục 3, chốt 2026-10-29). Mỗi phiên có ít nhất 2 lần cuff hợp lệ. Đơn vị phân tích cho kiểm định là người.
- Các con số này là đề xuất khả thi, chưa dựa trên phân tích power; cần tính lại từ pilot và mô phỏng độ nhạy ở mục E.
- Yavarimanesh et al. (2022, N18, đọc toàn văn) ước tính cần 31 người cho một so sánh tương tự. So sánh đó là mô hình PAT/đặc trưng PPG ngón tay với baseline sau một năm, kiểm định t ghép cặp, mức 0,05, power 0,8. Vì vậy ≥ 15 người có thể không đủ nhạy, và con số này phải đưa vào mô phỏng độ nhạy (bổ sung 2026-10-30).
- **Hiện trạng:** chưa có prototype, phê duyệt đạo đức hay dữ liệu cuff. PulseDB **không** trả lời được RQ1: nhãn là ABP xâm lấn chứ không phải cuff, và không có cấu trúc phiên theo thời gian. PulseDB chỉ dùng để phát triển và kiểm tra đặc trưng.

---

## 5. RQ2 (phụ): Cách chia dữ liệu và đánh giá cùng phiên so với khác phiên

> **Câu hỏi:** (a) Trên PulseDB, sai số ước lượng BP tăng bao nhiêu khi chuyển từ chia ngẫu nhiên theo cửa sổ sang chia theo người? (b) Trên dữ liệu prototype, đánh giá ở cùng phiên hiệu chuẩn cho sai số lạc quan hơn bao nhiêu so với đánh giá ở các phiên khác ngày?

**Thay đổi ở v0.4 (đề xuất 2026-10-29, chờ thầy):** RQ2a là kiểm tra rò rỉ, báo ở phụ lục của bài. RQ2b đổi từ "chia theo phiên" (trùng với thiết kế của RQ1) thành so sánh cùng phiên với khác phiên. Phần lớn các nghiên cứu gần nhất chỉ đánh giá trong một buổi (N1, N2, N7 ở [tổng quan 2026-10-29](literature/literature_update_2026-10-29.md)), nên RQ2b đo được mức lạc quan của cách đánh giá đó trên dữ liệu của nhóm.

### A. Giả thuyết

- **$H_{0,\text{RQ2a}}$:** MAE không khác nhau giữa chia ngẫu nhiên theo cửa sổ và chia theo người.
- **$H_{1,\text{RQ2a}}$:** MAE khi chia theo người cao hơn khi chia ngẫu nhiên theo cửa sổ.
- **$H_{0,\text{RQ2b}}$:** MAE trên cuff nghiệm pháp ở phiên ≥ 2 không cao hơn MAE trên cuff nghiệm pháp ở phiên 1.
- **$H_{1,\text{RQ2b}}$:** MAE ở phiên ≥ 2 cao hơn.

Hiệu ứng của RQ2a đã được ghi nhận trong y văn (Yoshizawa 2023, Mehta 2024, Moulaeifard 2025). RQ2a là **kiểm chứng lại và lượng hóa** hiệu ứng trong pipeline của nhóm, không phải phát hiện mới. Chênh lệch sai số giữa các cách chia không tự chứng minh nguyên nhân duy nhất là mô hình nhận dạng người.

### B. Các cách chia

1. **A — Ngẫu nhiên theo cửa sổ (đối chứng có rò rỉ):** chia ngẫu nhiên các cửa sổ/đoạn, cùng người có thể nằm ở nhiều tập. Chỉ dùng để minh họa rò rỉ, không dùng để chọn mô hình hay báo cáo hiệu năng chính.
2. **B — Theo người:** mỗi người chỉ nằm trong một tập (train/validation/test cố định theo `subject_id`, hoặc k-fold/LOSO theo người).
3. **C — Cùng phiên so với khác phiên (RQ2b, chỉ với dữ liệu prototype; thay cách chia "theo phiên" của v0.3):**
   - Dùng chính dự đoán vòng ngoài của LOSO lồng ở RQ1, không huấn luyện hay tuning thêm. Dự đoán cho cuff nghiệm pháp phiên 1 của người test phải được sinh trong cùng lần chạy vòng ngoài và khai báo trong commit khóa.
   - Với mỗi người $s$: **tập cùng phiên** là các lần cuff nghiệm pháp M1, M2 ở phiên 1; **tập khác phiên** là các lần cuff M1, M2 ở phiên ≥ 2. Cả hai so với cùng $`\text{BP}_0`$ (trung bình M0 phiên 1). Chỉ so cuff nghiệm pháp; báo kèm phân bố nghiệm pháp của từng tập.
   - **Chuẩn hóa theo nghiệm pháp:** với mỗi người, MAE của mỗi tập tính riêng cho từng nghiệm pháp rồi lấy trung bình đều trên các nghiệm pháp có mặt ở **cả hai** tập của người đó; các phiên ≥ 2 gộp chung. Người không có nghiệm pháp chung nào thì không tính. Như vậy $e_s$ không tăng chỉ vì nghiệm pháp khó chiếm tỷ trọng lớn hơn ở phiên sau. Bản thô (gộp theo số cuff thực có) báo kèm như phân tích phụ, ghi rõ là gồm cả thay đổi cơ cấu nghiệm pháp. Với bộ M1, M2, theo kế hoạch mỗi người có hai cuff nghiệm pháp ở tập cùng phiên và hai đến bốn ở tập khác phiên (một hay hai phiên sau), chưa kể lần đo thiếu hay đo lại; người thiếu M2 chỉ còn so được M1. Vì vậy thêm phân tích độ nhạy chỉ trên người có cả M1 và M2 ở cả hai tập, và báo số cuff theo nghiệm pháp ở từng tập.
   - Tập cùng phiên **không** thay đổi endpoint của RQ1: cuff nghiệm pháp phiên 1 vẫn không dùng để hiệu chuẩn và không vào tập đánh giá của RQ1.
   - Chênh lệch không chỉ do hiệu chuẩn trôi theo thời gian: còn do đeo lại thiết bị, BP nền khác nhau giữa các ngày, PEP, và việc người tham gia quen dần nghiệm pháp ở phiên sau (nhất là tính nhẩm M2). Không quy toàn bộ chênh lệch cho một nguyên nhân.

Với RQ2a, giữ nguyên cách tạo cửa sổ, đặc trưng và thuật toán giữa các cách chia; chỉ thay đổi cách chia.

### C. Mô hình so sánh

- **RQ2a:** cùng một mô hình (B3 XGBoost, đã có trong code, xem mục 7; hoặc Ridge) trên cách chia A và B; B0 (trung bình train) trên từng cách chia để biết mức sai số khi không dùng tín hiệu.
- **RQ2b:** các mô hình của RQ1 (zero-change, PPG-only, PPG + PAT), cùng dự đoán vòng ngoài.

### D. Chỉ số

- **RQ2a:** MAE, RMSE, ME ± SD cho SBP và DBP; $`\Delta\text{MAE} = \text{MAE}_{\text{B}} - \text{MAE}_{\text{A}}`$ và tỷ lệ suy giảm $`(\text{MAE}_{\text{nghiêm}} - \text{MAE}_{\text{ngẫu nhiên}}) / \text{MAE}_{\text{ngẫu nhiên}} \times 100\%`$.
- **RQ2b:** $`e_s = \text{MAE}_s(\text{khác phiên}) - \text{MAE}_s(\text{cùng phiên})`$, với MAE chuẩn hóa theo nghiệm pháp (mục B), cho từng mô hình; trung bình và CI 95% bootstrap theo người; báo riêng SBP, DBP và theo nghiệm pháp.
- CI bootstrap theo người cho từng MAE.
- Bland–Altman: độ lệch trung bình và **giới hạn đồng thuận 95%** (LoA), không gọi là khoảng tin cậy; với dữ liệu đo lặp cần phương pháp LoA cho đo lặp (chưa khóa).

### E. Tiêu chí kết luận

Báo cáo ΔMAE (RQ2a) và $e_s$ (RQ2b) với CI theo người, riêng SBP và DBP; không đặt ngưỡng đạt/không đạt. RQ2a báo ở phụ lục như kiểm tra rò rỉ. Mức suy giảm 40% và ngưỡng $p < 0{,}001$ trong bản v0.1 là đề xuất chưa có căn cứ và **không** được dùng làm tiêu chí. Kế hoạch kiểm định phải được duyệt trước khi mở test.

### F. Rủi ro

- Nếu dải BP hẹp, mọi mô hình tiến gần B0/zero-change và chênh lệch giữa các cách chia khó đo.
- Với PulseDB, mỗi người có rất nhiều đoạn 10 giây gần nhau về thời gian; chia ngẫu nhiên theo đoạn gần như chắc chắn rò rỉ, nên chênh lệch có thể lớn hơn trên dữ liệu prototype.

### G. Dữ liệu và tính khả thi

- **Phần (a), làm được ngay:** PulseDB (phần VitalDB trên Kaggle) với reader, inventory và split theo người `pulsedb-split-v2` đã có, cùng pipeline B0/B3 trên split này (mục 7; đã chạy trên raw PulseDB VitalDB Train 400 người ngày 2026-10-25, chỉ chấm val; [báo cáo](../reports/weekly/week_05/pulsedb_b3_v1/README.md)). Cần thêm: một hàm chia ngẫu nhiên theo đoạn (chỉ cho đối chứng A).
- **Rào chắn cho phần (a) (chốt 2026-10-29):**
  - RQ2(a) chỉ chạy trên người thuộc train ∪ val của split v2, so chia theo đoạn với chia theo người (k-fold theo người) trên cùng pool đó.
  - 40 người test của split v2 và tập CalFree không tham gia.
  - Hàm chia ngẫu nhiên theo đoạn phải từ chối mọi dòng có `split = test`; viết kèm test cho điều này trước khi viết hàm.
  - Không dùng CalBased Test: tập này cùng người với Train, đã loại trong quyết định pool ngày 2026-10-24 ([provenance](pulsedb_provenance.md)).
  - Theo Bảng 4 của bài báo PulseDB (Wang et al., 2023), phần VitalDB có 1.293 người ở cả Train và CalBased Test, 144 người ở CalFree Test; các con số 2.506 và 279 là tổng MIMIC-III + VitalDB.
- **Phần (b):** dùng đúng dữ liệu của RQ1 (cấu trúc `subject_id → session_id → event_id → window_id`), không cần thêm phiên; chỉ tính trên người có cuff nghiệm pháp ở cả phiên 1 và phiên ≥ 2. Nếu hội đồng không duyệt nghiệm pháp M1, M2 thì RQ2b không làm được theo định nghĩa trên.

---

## 6. RQ3 (thăm dò): Từ chối dự đoán theo SQI và độ bất định

**Thay đổi ở v0.4 (đề xuất 2026-10-29, chờ thầy):** RQ3 là phân tích thăm dò, không phải câu hỏi xác nhận. Protocol yêu cầu ngồi yên lúc đo nên có thể có ít đoạn nhiễu tự nhiên (mục G); không đủ dữ liệu thì không dùng RQ3 để tuyên bố trong bài.

> **Câu hỏi:** Từ chối dự đoán dựa trên SQI của tín hiệu đầu vào kết hợp với độ bất định của mô hình có cho sai số trên phần được giữ lại thấp hơn so với từ chối ngẫu nhiên và so với chỉ dùng SQI, ở cùng tỷ lệ giữ lại (coverage) hay không?

### A. Giả thuyết

- **$H_{0,\text{RQ3}}$:** Ở cùng coverage, MAE trên phần được giữ của chiến lược SQI + độ bất định không thấp hơn MAE của từ chối ngẫu nhiên.
- **$H_{1,\text{RQ3}}$:** Chiến lược SQI + độ bất định cho đường cong risk–coverage tốt hơn từ chối ngẫu nhiên và SQI đơn lẻ; điểm số từ chối tương quan dương với độ lớn sai số $|e|$.

Mức từ chối 15–20% và mức giảm MAE 20% trong bản v0.1 là đề xuất chưa có căn cứ và **không** được dùng làm tiêu chí.

### B. Biến nghiên cứu

- **Đơn vị từ chối:** một quan sát của phân tích BP, tức một lần đo cuff (prototype) hoặc một đoạn (PulseDB). SQI tính trên từng cửa sổ rồi tổng hợp về quan sát theo quy tắc khóa trước.
- **SQI của PPG:** skewness (Elgendi, 2016), độ nhất quán hình dạng nhịp so với template trong cửa sổ (đã có trong SQI v0), tỷ lệ ghép nhịp R–foot. Perfusion index cần thành phần DC và đơn vị vật lý, hiện chưa có.
- **SQI của ECG:** biên độ R so với nhiễu nền, độ đều của RR, trôi đường nền.
- **Độ bất định:** chọn phương pháp hợp với mô hình đang dùng (Ridge/Random Forest/XGBoost): phương sai giữa các mô hình trong ensemble, độ rộng khoảng của quantile regression, hoặc khoảng conformal (Shen et al., 2025). MC Dropout hoặc evidential regression chỉ áp dụng nếu dùng mạng nơ-ron.
- **Biến điều khiển:** coverage từ 100% xuống khoảng 70% (tỷ lệ từ chối 0–30%).
- **Đầu ra:** MAE trên phần được giữ theo từng mức coverage, riêng SBP và DBP.

### C. Chiến lược so sánh

1. **Không từ chối** (coverage = 100%).
2. **Từ chối ngẫu nhiên** ở cùng coverage, lặp nhiều lần để lấy phân phối.
3. **Chỉ SQI.**
4. **Chỉ độ bất định.**
5. **SQI + độ bất định** (chiến lược đề xuất).

### D. Chỉ số

- Đường cong risk–coverage (risk = MAE trên phần được giữ) và diện tích dưới đường cong (AURC, càng nhỏ càng tốt).
- MAE tại một mức coverage được chọn trên validation, đánh giá một lần trên test.
- Tương quan hạng Spearman giữa điểm số từ chối và $|e|$.
- Tỷ lệ phát hiện các quan sát có $|e| > 10$ mmHg, chỉ để mô tả.
- Báo cáo coverage theo từng người: một chiến lược có thể đạt coverage tổng 80% nhưng từ chối gần hết dữ liệu của vài người.
- **Phân bố |ΔBP| tham chiếu của các lần cuff bị từ chối so với được giữ (v0.4):** nếu chiến lược chủ yếu loại các lần BP thay đổi lớn, MAE giảm không chứng minh được rằng nó phát hiện tín hiệu kém.

Lưu ý: "coverage" ở đây là **tỷ lệ quan sát được giữ lại**, khác với coverage của khoảng dự đoán trong conformal prediction.

### E. Tiêu chí kết luận

Ủng hộ $H_1$ khi đường cong của chiến lược đề xuất nằm dưới đường của từ chối ngẫu nhiên và SQI đơn lẻ trên phần lớn dải coverage, và CI bootstrap theo người của chênh lệch MAE tại mức coverage đã chọn trên validation nằm dưới 0. Mức vận hành chỉ được chọn trên validation; với dữ liệu prototype, validation là vòng trong của LOSO lồng. Vì RQ3 là thăm dò (v0.4), kết quả chỉ báo như vậy, không thêm vào kết luận chính.

### F. Rủi ro

- Ngưỡng quá chặt làm từ chối quá nhiều, giảm tính sử dụng được của thiết bị.
- SQI và độ bất định có thể tương quan mạnh với nhau, khiến kết hợp không thêm thông tin.
- Từ chối không đều giữa các người làm MAE "tốt lên" chỉ vì loại bỏ người khó.

### G. Dữ liệu và tính khả thi

- Cần dữ liệu có cả đoạn tốt và đoạn kém chất lượng tự nhiên, có nhãn BP. Protocol prototype yêu cầu ngồi yên lúc đo, nên số đoạn kém có thể ít. PulseDB là dữ liệu đã làm sạch, nên dải chất lượng hẹp.
- Các lựa chọn cần nhóm quyết định: (a) ghi nhận các lần đo kém tự nhiên trong protocol thay vì đo lại ngay; (b) xin truy cập dataset có nhãn chất lượng như CardioWave-Portable (cần credentialed access và DUA); (c) giới hạn RQ3 thành phân tích thăm dò (đã chọn ở v0.4, chờ thầy xác nhận); (a) và (b) vẫn có thể làm thêm.

---

## 7. Bảng tổng hợp baseline và đối chiếu với code

| Tên trong RQ | Tên trong code / kế hoạch | Bài toán | Trạng thái |
|---|---|---|---|
| — | **B0** `PopulationMeanBaseline` (trung bình nhãn train; trong b3-pipeline-v1 là trung bình các trung bình theo người) | BP tuyệt đối, người mới; dùng cho RQ2a | Đã cài; chạy sơ bộ trên CSV PulseDB (Tuần 3, lịch sử), rồi cùng B3 trên raw PulseDB VitalDB Train 400 người ngày 2026-10-25, chỉ chấm val |
| **Zero-change** | **B1** `PersonalMeanBaseline`, khi $`\text{BP}_0`$ là trung bình các lần cuff hiệu chuẩn | $`\widehat{\text{BP}} = \text{BP}_0`$, tương đương $`\Delta\widehat{\text{BP}} = 0`$; RQ1 | Đã cài, mới kiểm tra bằng dữ liệu giả lập |
| — | **B3** `XGBoostBaseline` (`software/models/xgboost_baseline.py`), đặc trưng `pulsedb-simple-stats-v0`; pipeline `software/pulsedb/pipeline.py`, runner `scripts/run_b3_pulsedb.py` | BP tuyệt đối (không phải ΔBP) trên PulseDB; RQ2a | Đã cài: fit trên train, chỉ đánh giá val (không trích đặc trưng tập test); đã chạy trên raw PulseDB ngày 2026-10-25 (val 40 người), chưa chấm test |
| — | **B2** nhân khẩu học + HR từ ECG (`software/pulsedb/pipeline_b2.py`, `features_b2.py`; runner `scripts/run_b2_pulsedb.py`; định nghĩa [b2_pulsedb_definition.md](protocol/b2_pulsedb_definition.md)) | BP tuyệt đối trên PulseDB | Có code và test SYNTHETIC; định nghĩa chưa duyệt, runner từ chối chạy, chưa có kết quả |
| PAT-only, PPG-only, PPG + PAT | Chưa có | ΔBP; RQ1 | Chưa triển khai, cần dữ liệu prototype |
| Không từ chối / ngẫu nhiên / SQI / SQI + độ bất định | Cờ SQI `features-sqi-v1`/`v2` trong `week04.py`, cờ cử động `motion-sqi-v0` (`motion_sqi.py`); chưa có cơ chế từ chối | RQ3 | Mới có cờ SQI, chưa có ngưỡng khóa |

Tên B0/B1/B3 trong code không trùng với số thứ tự "Baseline 1/2/3" của bản v0.1; bảng này thay thế cách đánh số cũ.

---

## 8. Các điểm cần nhóm và giảng viên xác nhận

> [!IMPORTANT]
> - [ ] **Đại lượng dự đoán:** xác nhận dự đoán ΔSBP/ΔDBP có hiệu chuẩn cá nhân, không làm BP tuyệt đối không hiệu chuẩn trong RQ1.
> - [ ] **Phép so sánh chính của RQ1:** PPG-only so với PPG + PAT trên cùng tập lần đo, cùng thuật toán.
> - [ ] **Endpoint RQ1 khi có nghiệm pháp M0–M2** (đề xuất của nhóm 2026-10-29, mục 4.B): mọi lần cuff hợp lệ ở phiên ≥ 2 so với $`\text{BP}_0`$ = trung bình M0 phiên 1; nghiệm pháp là biến phân tầng; chỉ M0 là phân tích phụ.
> - [ ] **Cỡ mẫu và kiểm định:** trần tuyển 25 người và số phiên (mục 4.G, đề xuất 2026-10-29); tất cả khóa trước khi mở test, dựa trên pilot.
> - [ ] **Tiêu chí kết luận RQ1 v0.4** (mục 4.E, đề xuất 2026-10-29): cùng chuẩn CI cho so sánh với zero-change và với PPG-only; chọn phương án đa kiểm định A (giao–hợp, Holm giữa SBP/DBP) hay B (Holm trên bốn so sánh); giá trị δ và cách lấy từ độ lặp lại của cuff ở pilot; estimand (mục 4.A).
> - [x] **RQ2:** phần (a) dùng train ∪ val của split v2, không dùng test, CalFree hay CalBased (chốt 2026-10-29, mục 5.G); random split chỉ là đối chứng minh họa.
> - [ ] **RQ2 v0.4** (đề xuất 2026-10-29): RQ2a báo ở phụ lục; RQ2b đổi thành cùng phiên so với khác phiên (mục 5.B), cần sinh dự đoán cho cuff nghiệm pháp phiên 1 trong cùng lần chạy vòng ngoài.
> - [ ] **RQ3:** là phân tích thăm dò (v0.4, đề xuất 2026-10-29); nguồn dữ liệu có đoạn nhiễu tự nhiên (mục 6.G); phương pháp đo độ bất định; mức coverage chọn ở vòng trong.
> - [ ] **Rủi ro áp lực tiếp xúc** (mục 4.F): cách chuẩn hóa vị trí và nấc dây đeo trong protocol.
> - [ ] **Mốc PEP:** PEP thường tính từ Q/QRS, còn PAT của dự án tính từ R; không đồng nhất hai mốc khi diễn giải.
