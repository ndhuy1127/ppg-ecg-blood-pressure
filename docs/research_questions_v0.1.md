# Câu hỏi nghiên cứu (Research Questions) — v0.2

> **Người thực hiện:** Nguyễn Đức Huy
>
> **Vai trò:** Xử lý tín hiệu, PAT, thống kê, protocol, tổng quan tài liệu và điều phối bài báo
>
> **Ngày lập:** 2026-09-22; **cập nhật:** 2026-10-14 (v0.2: thêm phần vấn đề nghiên cứu, làm rõ phép so sánh chính của RQ1, tính khả thi của RQ2/RQ3 và đối chiếu tên baseline với code)
>
> Tên file giữ `v0.1` để không làm gãy liên kết.

---

## 1. Vấn đề nghiên cứu

Thiết bị đo huyết áp không vòng bít (cuffless) dựa trên PPG ở cổ tay thường cần hiệu chuẩn bằng một lần đo cuff, sau đó theo dõi thay đổi so với mốc này. Có ba vấn đề làm cho việc đánh giá các thiết bị này khó:

1. **Mốc hiệu chuẩn tự nó đã là một dự đoán tốt.** Nếu BP ít thay đổi sau hiệu chuẩn, chỉ cần giữ nguyên giá trị cuff ban đầu cũng cho sai số nhỏ. Mukkamala et al. (2021) chỉ ra điểm này bằng mô phỏng, và dự án Aurora (1.125 người) không tìm thấy mô hình dạng sóng nào dự đoán BP ngày hôm sau tốt hơn rõ rệt so với baseline chỉ dùng BP hiệu chuẩn (Mukkamala et al., 2023). Xem [tổng quan bổ sung](literature/literature_update_2026-10-14.md), S2–S3.
2. **PAT không phải PTT.** ECG cho phép đo PAT (R-peak → chân sóng PPG), nhưng PAT chứa thời gian tiền tống máu (PEP), vốn thay đổi theo trạng thái giao cảm. Payne et al. (2006) cho thấy PEP chiếm 12–35% khoảng R → xung ngón tay. Vì vậy, việc thêm ECG có giúp hơn PPG đơn lẻ hay không là câu hỏi thực nghiệm, không suy ra được từ lý thuyết PTT.
3. **Cách chia dữ liệu làm kết quả đẹp giả.** Khi cửa sổ của cùng một người nằm ở cả tập huấn luyện và tập kiểm tra, sai số giảm đáng kể so với khi chia theo người (Yoshizawa et al., 2023; Mehta et al., 2024).

**Mục tiêu nghiên cứu:** xây dựng nguyên mẫu vòng đeo cổ tay thu đồng bộ ECG và PPG, và dùng nó để kiểm tra, trên một nhóm nhỏ người khỏe mạnh, liệu PAT có làm giảm sai số dự đoán ΔSBP/ΔDBP ở các phiên đo sau hiệu chuẩn so với chỉ dùng PPG hay không. Đánh giá phải có baseline zero-change, chia dữ liệu theo người và theo thời gian, và khoảng tin cậy theo người.

Mục tiêu triển khai (chế tạo prototype, firmware, pipeline) là điều kiện để trả lời câu hỏi, không phải câu hỏi nghiên cứu.

---

## 2. Nguyên tắc phương pháp chung

1. **Đánh giá SBP và DBP riêng.** Hai đại lượng chịu ảnh hưởng của các yếu tố sinh lý khác nhau một phần (SBP gắn nhiều hơn với tống máu và độ cứng động mạch lớn, DBP với kháng lực ngoại vi). Không gộp thành một chỉ số sai số chung.
2. **Gọi đúng PAT.** Khoảng từ đỉnh R của ECG đến chân sóng PPG là PAT, `PAT = PEP + PTT` (cách viết gọn; mốc R không trùng mốc Q/QRS mà PEP thường dùng). Không áp trực tiếp phương trình của PTT lên PAT.
3. **Chống rò rỉ dữ liệu.** Chia theo người; với cá nhân hóa, dữ liệu hiệu chuẩn có trước dữ liệu kiểm tra. Một lần đo cuff là một nhãn; nhiều cửa sổ cùng lần đo không phải nhiều mẫu độc lập. Bootstrap lấy mẫu lại theo người. Các biện pháp này giảm nguy cơ mô hình nhận dạng người thay vì học quan hệ với BP, nhưng không loại trừ hoàn toàn mọi dạng rò rỉ.
4. **Không chọn gì trên tập test.** Đặc trưng, cửa sổ, ngưỡng SQI, siêu tham số và mức vận hành đều chọn trên train/validation; test chỉ dùng một lần sau khi đã khóa.

---

## 3. Tóm tắt ba câu hỏi nghiên cứu

| | Yếu tố khảo sát | So sánh với | Chỉ số chính | Dữ liệu cần | Làm được khi nào |
|---|---|---|---|---|---|
| **RQ1** (chính) | Thêm PAT (từ ECG) vào mô hình PPG | Cùng mô hình chỉ dùng PPG; zero-change | Chênh lệch MAE theo người cho ΔSBP, ΔDBP, kèm CI 95% bootstrap theo người | Prototype, 15–20 người, ≥ 2 phiên/người, nhãn cuff | Sau khi có phần cứng, phê duyệt đạo đức và thu dữ liệu |
| **RQ2** | Cách chia dữ liệu | Chia ngẫu nhiên theo cửa sổ vs theo người vs theo phiên | Chênh lệch MAE giữa các cách chia | (a) PulseDB: theo cửa sổ vs theo người; (b) prototype: theo phiên | (a) làm được ngay với code hiện có; (b) cần dữ liệu prototype |
| **RQ3** | Từ chối dự đoán theo SQI và độ bất định | Không từ chối; từ chối ngẫu nhiên cùng coverage; SQI đơn lẻ | Đường cong risk–coverage, MAE tại coverage chọn trên validation | Dữ liệu có cả đoạn tốt và đoạn nhiễu tự nhiên, có nhãn | Phụ thuộc nguồn dữ liệu (xem 6.G) |

---

## 4. RQ1: Giá trị gia tăng của PAT sau hiệu chuẩn cá nhân

> **Câu hỏi:** Sau khi hiệu chuẩn bằng cuff ở phiên đầu, việc thêm PAT (tính từ ECG) vào mô hình đặc trưng PPG có làm giảm sai số dự đoán $`\Delta\text{SBP}`$ và $`\Delta\text{DBP}`$ ở các phiên đo sau so với cùng mô hình chỉ dùng PPG hay không?

### A. Giả thuyết

- **$H_{0,\text{RQ1}}$:** Với mỗi đầu ra (SBP, DBP), MAE theo người của mô hình PPG + PAT không thấp hơn MAE của mô hình PPG-only trên các phiên sau.
- **$H_{1,\text{RQ1}}$:** MAE theo người của mô hình PPG + PAT thấp hơn mô hình PPG-only.

SBP và DBP được kiểm định riêng. Bằng chứng hiện có (Payne 2006: PAT gần như không giải thích DBP khi chưa trừ PEP; Aurora: mô hình dạng sóng không vượt baseline hiệu chuẩn) cho thấy không bác bỏ được $H_0$ là một khả năng thực tế. Kết quả đó vẫn được báo cáo đầy đủ.

### B. Biến nghiên cứu

- **Đặc trưng PPG:** thời gian lên (rise time), độ rộng xung tại 50% biên độ, biên độ xung, HR tính từ PPG; ứng viên mở rộng là tỷ số diện tích tâm thu/tâm trương và PIR (Ding et al., 2016). Bộ đặc trưng v0 đã có trong code Tuần 4 (`software/feature_extraction/week04.py`), chưa được khóa.
- **Đặc trưng từ ECG:** PAT (R-peak → PPG foot cùng nhịp, trung vị trong cửa sổ) và $`\Delta\text{PAT} = \text{PAT}_{\text{hiện tại}} - \text{PAT}_{\text{hiệu chuẩn}}`$. HR và HRV ngắn hạn từ ECG là đặc trưng phụ cho phân tích ablation.
- **Mốc hiệu chuẩn:** $`\text{SBP}_0`$, $`\text{DBP}_0`$ từ lần cuff hợp lệ ở phiên 1 (cách tổng hợp nhiều lần cuff chưa khóa).
- **Đầu ra:** $`\Delta\text{SBP} = \text{SBP}_{\text{target}} - \text{SBP}_0`$, $`\Delta\text{DBP} = \text{DBP}_{\text{target}} - \text{DBP}_0`$ (mmHg). Ước lượng BP cuối: $`\widehat{\text{BP}} = \text{BP}_0 + \Delta\widehat{\text{BP}}`$.

### C. Các mô hình so sánh

| Mô hình | Đầu vào | Vai trò |
|---|---|---|
| **Zero-change** | Không có đặc trưng; $`\Delta\widehat{\text{BP}} = 0`$, tức $`\widehat{\text{BP}} = \text{BP}_0`$ | Baseline bắt buộc. Mô hình không vượt baseline này thì không có giá trị gia tăng so với chỉ dùng mốc hiệu chuẩn |
| **PAT-only** | $`\Delta(1/\text{PAT}^2)`$ hoặc $`\Delta\text{PAT}`$ | Kiểm tra lượng thông tin của riêng PAT. Hệ số học ở mức quần thể trên người thuộc tập train, vì một lần cuff hiệu chuẩn không đủ để fit hệ số riêng cho từng người. Đây là hồi quy thực nghiệm, không phải áp Moens–Korteweg lên PAT |
| **PPG-only** | Đặc trưng PPG + HR từ PPG | Đối chứng chính của RQ1 |
| **PPG + PAT** | Như PPG-only, thêm PAT/ΔPAT | Mô hình chính của RQ1 |
| **PPG + PAT + ECG-HRV** | Thêm HR/HRV từ ECG | Ablation phụ, tách phần đóng góp của PAT với phần của các đặc trưng ECG khác |

**Phép so sánh chính là PPG-only với PPG + PAT**, dùng cùng thuật toán (ví dụ Ridge), cùng ngân sách chọn siêu tham số trên validation và **cùng tập lần đo đánh giá** (những lần đo có cả ECG và PPG đạt chất lượng). Nếu PPG-only được đánh giá trên nhiều lần đo hơn (gồm cả lần ECG hỏng), hai mô hình sẽ bị so trên hai tập khác nhau. Kết quả PPG-only trên toàn bộ lần đo và tỷ lệ lần đo mất ECG được báo cáo riêng như phân tích phụ.

### D. Chỉ số đánh giá

Tính riêng cho ΔSBP và ΔDBP:

- MAE, ME ± SD của sai số (sai số = dự đoán − tham chiếu), tổng hợp đều theo người (như `evaluate_bp`).
- **Hiệu ứng chính:** $`d_s = \text{MAE}_s(\text{PPG+PAT}) - \text{MAE}_s(\text{PPG})`$ cho từng người $s$; báo cáo trung bình của $d_s$ và CI 95% bootstrap theo người (`software/evaluation/subject_bootstrap.py`). Wilcoxon signed-rank trên $d_s$ là phân tích hỗ trợ.
- Pearson $r$ giữa ΔBP tham chiếu và ΔBP dự đoán (không xác định cho zero-change vì dự đoán là hằng).
- Tỷ lệ lần đo có $|e| \le 5$ và $\le 10$ mmHg, chỉ để mô tả; không phải tiêu chí AAMI/ISO.
- **Bắt buộc báo cáo kèm:** SD của ΔBP tham chiếu và tỷ lệ lần đo có $|\Delta\text{BP}| > 5$ mmHg. Nếu ΔBP tham chiếu rất hẹp, mọi so sánh MAE đều kém nhạy, và người đọc cần biết điều đó.

### E. Tiêu chí kết luận

- **Ủng hộ $H_1$** khi: (1) mô hình PPG + PAT có MAE thấp hơn zero-change; và (2) CI 95% bootstrap theo người của trung bình $d_s$ nằm hoàn toàn dưới 0, với hướng hiệu ứng nhất quán. Đánh giá riêng SBP và DBP.
- Hai đầu ra tạo hai phép kiểm định; cách xử lý đa kiểm định (ví dụ Holm) phải được chọn trước khi mở test.
- Nếu nhóm muốn dùng ngưỡng ý nghĩa thực tiễn (ví dụ "giảm ít nhất X mmHg"), ngưỡng đó phải có căn cứ từ pilot hoặc tài liệu và được khóa trước khi mở test. Bản v0.1 từng nêu 1,5/1,0 mmHg; con số này chưa có căn cứ và **không** được dùng.
- Nếu không đạt các điều kiện trên: không bác bỏ $H_0$, báo cáo ước lượng hiệu ứng và CI, không khẳng định PAT có lợi.

### F. Rủi ro phương pháp

- **PEP thay đổi giữa các phiên** (căng thẳng, tư thế, nhiệt độ) làm PAT thay đổi mà BP không đổi.
- **PAT ở cổ tay chịu ảnh hưởng của co cơ trơn mạch ngoại vi**, độc lập với mức BP (Mukkamala et al., 2023).
- **ΔBP giữa các phiên nhỏ** ở người trẻ khỏe mạnh đo lúc nghỉ, làm zero-change khó bị vượt và giảm độ nhạy của so sánh.
- **ECG ngón tay–cổ tay có biên độ nhỏ hơn ECG ngực và dễ nhiễu khi chạm không ổn định**, gây sai lệch R-peak. Lần đo mất ECG không ngẫu nhiên có thể làm lệch tập đánh giá; vì vậy phải so trên cùng tập (mục C).
- **Độ phân giải thời gian:** ở 500 Hz mỗi mẫu là 2 ms; sai số định vị mốc và đồng bộ hai kênh cộng trực tiếp vào PAT.

### G. Dữ liệu tối thiểu và tính khả thi

- 15–20 người khỏe mạnh, mỗi người ít nhất 2 phiên ở các thời điểm khác nhau (1 phiên hiệu chuẩn + ≥ 1 phiên đánh giá); protocol đề xuất 3 phiên. Mỗi phiên có ít nhất 2 lần cuff hợp lệ. Đơn vị phân tích cho kiểm định là người.
- Các con số này là đề xuất khả thi, chưa dựa trên phân tích power; cần tính lại từ pilot.
- **Hiện trạng:** chưa có prototype, phê duyệt đạo đức hay dữ liệu cuff. PulseDB **không** trả lời được RQ1: nhãn là ABP xâm lấn chứ không phải cuff, và không có cấu trúc phiên theo thời gian. PulseDB chỉ dùng để phát triển và kiểm tra đặc trưng.

---

## 5. RQ2: Ảnh hưởng của cách chia dữ liệu

> **Câu hỏi:** Sai số ước lượng BP thay đổi bao nhiêu khi chuyển từ chia ngẫu nhiên theo cửa sổ sang chia theo người, và (với dữ liệu nhiều phiên) sang chia theo phiên đo?

### A. Giả thuyết

- **$H_{0,\text{RQ2}}$:** MAE không khác nhau giữa chia ngẫu nhiên theo cửa sổ và chia theo người/theo phiên.
- **$H_{1,\text{RQ2}}$:** MAE khi chia theo người/theo phiên cao hơn khi chia ngẫu nhiên theo cửa sổ.

Hiệu ứng này đã được ghi nhận trong y văn (Yoshizawa 2023, Mehta 2024, Moulaeifard 2025). RQ2 là **kiểm chứng lại và lượng hóa** hiệu ứng trong pipeline của nhóm, không phải phát hiện mới. Chênh lệch sai số giữa các cách chia không tự chứng minh nguyên nhân duy nhất là mô hình nhận dạng người.

### B. Các cách chia

1. **A — Ngẫu nhiên theo cửa sổ (đối chứng có rò rỉ):** chia ngẫu nhiên các cửa sổ/đoạn, cùng người có thể nằm ở nhiều tập. Chỉ dùng để minh họa rò rỉ, không dùng để chọn mô hình hay báo cáo hiệu năng chính.
2. **B — Theo người:** mỗi người chỉ nằm trong một tập (train/validation/test cố định theo `subject_id`, hoặc k-fold/LOSO theo người).
3. **C — Theo phiên (chỉ với dữ liệu prototype):** mô hình chung học trên người thuộc tập train; với người thuộc tập test, chỉ dùng phiên 1 để hiệu chuẩn rồi đánh giá các phiên sau. Không dùng phiên sau để huấn luyện, hiệu chuẩn hay tuning.

Giữ nguyên cách tạo cửa sổ, đặc trưng và thuật toán giữa các cách chia; chỉ thay đổi cách chia.

### C. Mô hình so sánh

- Cùng một mô hình (B3 XGBoost, đã có trong code, xem mục 7; hoặc Ridge) trên các cách chia A, B (và C).
- B0 (trung bình train) trên từng cách chia để biết mức sai số khi không dùng tín hiệu.

### D. Chỉ số

- MAE, RMSE, ME ± SD cho SBP và DBP; $`\Delta\text{MAE} = \text{MAE}_{\text{B hoặc C}} - \text{MAE}_{\text{A}}`$ và tỷ lệ suy giảm $`(\text{MAE}_{\text{nghiêm}} - \text{MAE}_{\text{ngẫu nhiên}}) / \text{MAE}_{\text{ngẫu nhiên}} \times 100\%`$.
- CI bootstrap theo người cho từng MAE.
- Bland–Altman: độ lệch trung bình và **giới hạn đồng thuận 95%** (LoA), không gọi là khoảng tin cậy; với dữ liệu đo lặp cần phương pháp LoA cho đo lặp (chưa khóa).

### E. Tiêu chí kết luận

Báo cáo ΔMAE với CI theo người, riêng SBP và DBP. Mức suy giảm 40% và ngưỡng $p < 0{,}001$ trong bản v0.1 là đề xuất chưa có căn cứ và **không** được dùng làm tiêu chí. Kế hoạch kiểm định phải được duyệt trước khi mở test.

### F. Rủi ro

- Nếu dải BP hẹp, mọi mô hình tiến gần B0/zero-change và chênh lệch giữa các cách chia khó đo.
- Với PulseDB, mỗi người có rất nhiều đoạn 10 giây gần nhau về thời gian; chia ngẫu nhiên theo đoạn gần như chắc chắn rò rỉ, nên chênh lệch có thể lớn hơn trên dữ liệu prototype.

### G. Dữ liệu và tính khả thi

- **Phần (a), làm được ngay:** PulseDB (phần VitalDB trên Kaggle) với reader, inventory và split theo người `pulsedb-split-v2` đã có, cùng pipeline B0/B3 trên split này (mục 7; mới kiểm tra bằng dữ liệu SYNTHETIC, chưa chạy trên raw PulseDB). Cần thêm: một hàm chia ngẫu nhiên theo đoạn (chỉ cho đối chứng A). Một lựa chọn khác cần nhóm cân nhắc là dùng chính các tập của PulseDB: tập kiểm thử có hiệu chuẩn (CalBased) chứa người đã có trong tập huấn luyện, còn tập không hiệu chuẩn (CalFree) chứa người mới. Theo Bảng 4 của bài báo PulseDB (Wang et al., 2023), phần VitalDB có 1.293 người ở cả Train và CalBased Test, 144 người ở CalFree Test; các con số 2.506 và 279 là tổng MIMIC-III + VitalDB.
- **Phần (b):** cần dữ liệu prototype có cấu trúc `subject_id → session_id → event_id → window_id`, tối thiểu khoảng 30–40 phiên trên ít nhất 15 người, có biến thiên BP tự nhiên giữa các phiên.

---

## 6. RQ3: Từ chối dự đoán theo SQI và độ bất định

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

Lưu ý: "coverage" ở đây là **tỷ lệ quan sát được giữ lại**, khác với coverage của khoảng dự đoán trong conformal prediction.

### E. Tiêu chí kết luận

Ủng hộ $H_1$ khi đường cong của chiến lược đề xuất nằm dưới đường của từ chối ngẫu nhiên và SQI đơn lẻ trên phần lớn dải coverage, và CI bootstrap theo người của chênh lệch MAE tại mức coverage đã chọn trên validation nằm dưới 0. Mức vận hành chỉ được chọn trên validation.

### F. Rủi ro

- Ngưỡng quá chặt làm từ chối quá nhiều, giảm tính sử dụng được của thiết bị.
- SQI và độ bất định có thể tương quan mạnh với nhau, khiến kết hợp không thêm thông tin.
- Từ chối không đều giữa các người làm MAE "tốt lên" chỉ vì loại bỏ người khó.

### G. Dữ liệu và tính khả thi

- Cần dữ liệu có cả đoạn tốt và đoạn kém chất lượng tự nhiên, có nhãn BP. Protocol prototype yêu cầu ngồi yên lúc đo, nên số đoạn kém có thể ít. PulseDB là dữ liệu đã làm sạch, nên dải chất lượng hẹp.
- Các lựa chọn cần nhóm quyết định: (a) ghi nhận các lần đo kém tự nhiên trong protocol thay vì đo lại ngay; (b) xin truy cập dataset có nhãn chất lượng như CardioWave-Portable (cần credentialed access và DUA); (c) giới hạn RQ3 thành phân tích thăm dò.

---

## 7. Bảng tổng hợp baseline và đối chiếu với code

| Tên trong RQ | Tên trong code / kế hoạch | Bài toán | Trạng thái |
|---|---|---|---|
| — | **B0** `PopulationMeanBaseline` (trung bình nhãn train) | BP tuyệt đối, người mới; dùng cho RQ2 | Đã cài, đã chạy sơ bộ trên CSV PulseDB (Tuần 3) |
| **Zero-change** | **B1** `PersonalMeanBaseline`, khi $`\text{BP}_0`$ là trung bình các lần cuff hiệu chuẩn | $`\widehat{\text{BP}} = \text{BP}_0`$, tương đương $`\Delta\widehat{\text{BP}} = 0`$; RQ1 | Đã cài, mới kiểm tra bằng dữ liệu giả lập |
| — | **B3** `XGBoostBaseline` (`software/models/xgboost_baseline.py`), đặc trưng `pulsedb-simple-stats-v0`; pipeline `software/pulsedb/pipeline.py`, runner `scripts/run_b3_pulsedb.py` | BP tuyệt đối (không phải ΔBP) trên PulseDB; RQ2 | Đã cài: fit trên train, chỉ đánh giá val (không trích đặc trưng tập test); mới kiểm tra bằng dữ liệu SYNTHETIC, chưa chạy trên raw PulseDB |
| PAT-only, PPG-only, PPG + PAT | Chưa có | ΔBP; RQ1 | Chưa triển khai, cần dữ liệu prototype |
| Không từ chối / ngẫu nhiên / SQI / SQI + độ bất định | Cờ SQI `features-sqi-v1` có trong `week04.py`; chưa có cơ chế từ chối | RQ3 | Mới có cờ SQI, chưa có ngưỡng khóa |

Tên B0/B1/B3 trong code không trùng với số thứ tự "Baseline 1/2/3" của bản v0.1; bảng này thay thế cách đánh số cũ.

---

## 8. Các điểm cần nhóm và giảng viên xác nhận

> [!IMPORTANT]
> - [ ] **Đại lượng dự đoán:** xác nhận dự đoán ΔSBP/ΔDBP có hiệu chuẩn cá nhân, không làm BP tuyệt đối không hiệu chuẩn trong RQ1.
> - [ ] **Phép so sánh chính của RQ1:** PPG-only so với PPG + PAT trên cùng tập lần đo, cùng thuật toán.
> - [ ] **Cỡ mẫu và kiểm định:** số người/phiên, cách xử lý đa kiểm định cho SBP/DBP, có dùng ngưỡng ý nghĩa thực tiễn hay không; tất cả khóa trước khi mở test, dựa trên pilot.
> - [ ] **RQ2:** dùng split của nhóm hay các tập có sẵn của PulseDB cho phần (a); random split chỉ là đối chứng minh họa.
> - [ ] **RQ3:** nguồn dữ liệu có đoạn nhiễu tự nhiên (mục 6.G); phương pháp đo độ bất định; mức coverage chọn trên validation.
> - [ ] **Mốc PEP:** PEP thường tính từ Q/QRS, còn PAT của dự án tính từ R; không đồng nhất hai mốc khi diễn giải.
