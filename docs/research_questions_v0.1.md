# Câu hỏi nghiên cứu (Research Questions) - Phiên bản v0.1

> **Phiên bản:** v0.1
>
> **Người thực hiện:** Nguyễn Đức Huy
>
> **Vai trò:** Xử lý tín hiệu, PAT, thống kê, protocol, tổng quan tài liệu và điều phối bài báo
>
> **Ngày cập nhật:** 2026-09-22
>
> **Trạng thái:** Bản thảo đề xuất v0.1 (Chờ thảo luận và phê duyệt chính thức từ nhóm và giảng viên)

---

## 1. Bối cảnh và nguyên tắc thiết lập câu hỏi nghiên cứu

Dự án hướng tới việc giải quyết bài toán cốt lõi: **Xây dựng nguyên mẫu thiết bị đeo cổ tay thu nhận đồng bộ PPG và ECG để ước lượng biến thiên huyết áp ($\Delta\text{SBP}$, $\Delta\text{DBP}$) giữa các phiên đo sau khi đã hiệu chuẩn cá nhân hóa.**

Các nguyên tắc phương pháp luận bắt buộc:

1. **Phân tích tách biệt tuyệt đối giữa SBP (Huyết áp tâm thu) và DBP (Huyết áp tâm trương):** Cơ chế sinh lý chi phối SBP (chủ yếu liên quan đến thể tích nhát bóp, vận tốc tống máu và độ cứng động mạch lớn) khác với DBP (chịu ảnh hưởng lớn bởi kháng lực ngoại vi và độ đàn hồi động mạch nhỏ). Tuyệt đối không gộp chung SBP và DBP thành một chỉ số sai số duy nhất.
2. **Tuân thủ bản chất sinh lý của PAT:** Đại lượng đo được từ đỉnh R của ECG đến chân sóng PPG ở cổ tay là **Pulse Arrival Time (PAT)**, bao gồm cả thời gian tiền tống máu ($\text{PEP}$). $\text{PAT} = \text{PEP} + \text{PTT}$. Không giả định mù quáng rằng PAT tuân theo trực tiếp các phương trình động lực học chất lỏng thuần túy của PTT mà phải kiểm chứng thực nghiệm.
3. **Phòng chống rò rỉ dữ liệu (Data Leakage):** Mọi câu hỏi nghiên cứu phải được kiểm chứng trong cấu trúc đánh giá chặt chẽ, loại bỏ hoàn toàn khả năng mô hình học vẹt "vân tay sinh lý" của đối tượng đo.

---

## 2. Chi tiết các câu hỏi nghiên cứu (RQ1 – RQ3)

### 2.1. RQ1: Giá trị gia tăng của ECG và PAT sau hiệu chuẩn cá nhân hóa

> **Nội dung câu hỏi:**
>
> *Sau khi thực hiện hiệu chuẩn cá nhân ban đầu, việc bổ sung kênh ECG và đại lượng PAT có mang lại cải thiện có ý nghĩa thống kê trong việc dự đoán biến thiên huyết áp ($\Delta\text{SBP}$ và $\Delta\text{DBP}$) ở các phiên đo tương lai so với mô hình chỉ sử dụng đặc trưng hình thái từ PPG hay không?*

#### A. Giả thuyết nghiên cứu

- **Giả thuyết không ($H_{0, \text{RQ1}}$):**
  Mô hình kết hợp đa phương thức ($\text{ECG} + \text{PPG} + \text{PAT}$) không làm giảm sai số tuyệt đối trung bình (MAE) trong việc dự đoán $\Delta\text{SBP}$ và $\Delta\text{DBP}$ ở các phiên đo tương lai so với mô hình tối ưu chỉ dùng tín hiệu quang học $\text{PPG}$ ($\text{MAE}_{\text{ECG+PPG}} \ge \text{MAE}_{\text{PPG-only}}$ trên cả hai chỉ số).

- **Giả thuyết đối ($H_{1, \text{RQ1}}$):**
  Mô hình kết hợp ($\text{ECG} + \text{PPG} + \text{PAT}$) có MAE dự đoán $\Delta\text{SBP}$ và $\Delta\text{DBP}$ thấp hơn mô hình PPG-only trên các phiên đo tương lai. Mức cải thiện sẽ được báo cáo bằng chênh lệch MAE theo người, khoảng tin cậy 95% bootstrap theo người và kiểm định cặp Wilcoxon mang tính hỗ trợ. Không khóa ngưỡng $1.5/1.0\text{ mmHg}$ khi chưa có phân tích pilot, power và phê duyệt của nhóm/giảng viên.

#### B. Biến nghiên cứu

- **Biến đầu vào (Inputs):**
    - Tín hiệu PPG cổ tay: Các đặc trưng hình thái chu kỳ xung (thời gian dốc lên $T_r$, độ rộng xung tại 50% biên độ $W_{50}$, tỷ số diện tích tâm thu/tâm trương, chỉ số suy giảm dicrotic notch, tỷ số cường độ quang học PIR).
    - Tín hiệu ECG: Khoảng cách R-R (nhịp tim tức thời HR), biến thiên nhịp tim HRV ngắn hạn.
    - Đại lượng phối hợp: PAT (tính từ đỉnh R của ECG đến chân sóng foot của PPG cùng chu kỳ tim), $\Delta\text{PAT} = \text{PAT}_{\text{current}} - \text{PAT}_{\text{calib}}$.
    - Thông tin hiệu chuẩn cá nhân: Giá trị huyết áp mốc ban đầu ($\text{SBP}_0$, $\text{DBP}_0$).

- **Biến đầu ra (Outputs):**
    - Biến thiên huyết áp tâm thu: $\Delta\text{SBP} = \text{SBP}_{\text{target}} - \text{SBP}_0$ (đơn vị: $\text{mmHg}$).
    - Biến thiên huyết áp tâm trương: $\Delta\text{DBP} = \text{DBP}_{\text{target}} - \text{DBP}_0$ (đơn vị: $\text{mmHg}$).
    - *Lưu ý:* Giá trị huyết áp ước tính cuối cùng được tái tạo bởi $\widehat{\text{SBP}} = \text{SBP}_0 + \Delta\widehat{\text{SBP}}$ và $\widehat{\text{DBP}} = \text{DBP}_0 + \Delta\widehat{\text{DBP}}$.

#### C. Hệ thống Baseline đối chứng bắt buộc

1. **Baseline 1 (Zero-Change Baseline):** Dự đoán $\Delta\text{SBP} = 0$ và $\Delta\text{DBP} = 0$ (tức là coi huyết áp phiên đo mới bằng đúng giá trị mốc hiệu chuẩn ban đầu $\widehat{\text{BP}} = \text{BP}_0$). Bất kỳ mô hình học máy nào không vượt qua được baseline này đều coi như thất bại sinh lý học.
2. **Baseline 2 (PPG-Only Baseline):** Mô hình hồi quy (Ridge Regression / Random Forest) chỉ sử dụng các đặc trưng hình thái sóng PPG cổ tay và HR.
3. **Baseline 3 (PAT-Based Linear Baseline):** Mô hình hồi quy tuyến tính cổ điển dựa trên nghịch đảo bình phương của PAT: $\Delta\text{BP} = a \cdot \Delta(1/\text{PAT}^2) + b$.
4. **Mô hình đề xuất (ECG + PPG Multi-feature Fusion):** Mô hình hồi quy kết hợp toàn diện đặc trưng hình thái PPG, PAT và biến thiên nhịp tim.

#### D. Chỉ số đánh giá

- Sai số tuyệt đối trung bình: $\text{MAE} = \frac{1}{N}\sum |y_i - \hat{y}_i|$ (đánh giá riêng cho SBP và DBP).
- Sai số chuẩn hóa và độ lệch chuẩn: $\text{ME} \pm \text{STD}$.
- Hệ số tương quan Pearson ($r$) giữa $\Delta\text{BP}_{\text{true}}$ và $\Delta\text{BP}_{\text{pred}}$.
- Tỷ lệ sai số nằm trong khoảng chuẩn y tế $\le 5\text{ mmHg}, \le 10\text{ mmHg}$ theo hướng chuẩn AAMI/ISO.

#### E. Điều kiện bác bỏ hoặc chấp nhận giả thuyết

- **Kết luận có bằng chứng ủng hộ $H_1$:** khi các điều kiện chính sau được đáp ứng:
    1. Mô hình kết hợp $\text{ECG} + \text{PPG}$ vượt trội hơn Baseline Zero-Change trên cả SBP và DBP.
    2. Chênh lệch MAE theo người giữa mô hình ECG+PPG và PPG-only có hướng cải thiện nhất quán; báo cáo ước lượng hiệu ứng, khoảng tin cậy 95% bootstrap theo người và $p$-value của Wilcoxon signed-rank test như phân tích hỗ trợ.
    3. Ngưỡng ý nghĩa thực tiễn, nếu sử dụng, phải được xác định trước trên dữ liệu pilot/validation và được khóa trước khi mở test set; không lựa chọn ngưỡng sau khi xem kết quả kiểm thử.

- **Ngược lại:** Nếu bằng chứng chưa đủ mạnh, không bác bỏ $H_0$; báo cáo trung thực độ bất định và không khẳng định ECG/PAT mang lại lợi ích vượt trội.

#### F. Rủi ro phương pháp

- Hiện tượng biến thiên thời gian tiền tống máu ($\text{PEP}$ drift): Khi người tham gia thay đổi trạng thái căng thẳng hoặc tư thế, PEP thay đổi làm triệt tiêu tương quan giữa PAT và huyết áp.
- Biên độ ECG đo tại cổ tay/ngón tay đối diện có thể nhỏ và dễ suy hao, dẫn đến sai số định vị đỉnh R.

#### G. Dữ liệu tối thiểu cần có

- Tối thiểu 15–20 người tham gia khỏe mạnh.
- Mỗi người thực hiện tối thiểu 2 đến 3 phiên đo độc lập ở các thời điểm khác nhau trong ngày hoặc cách ngày (multi-session).
- Mỗi phiên đo ghi nhận đồng thời tín hiệu ECG, PPG liên tục cùng tối thiểu 2 lần đo huyết áp chuẩn bằng máy đo bắp tay tự động đạt chuẩn lâm sàng.

---

### 2.2. RQ2: Tác động của cơ chế chia dữ liệu và rò rỉ dữ liệu (Data Leakage)

> **Nội dung câu hỏi:**
>
> *Hiệu năng ước lượng biến thiên huyết áp thay đổi như thế nào khi chuyển từ phương pháp chia ngẫu nhiên từng cửa sổ tín hiệu (Window-wise Random Split) sang phương pháp đánh giá tách biệt nghiêm ngặt theo người (Subject-wise Split) và tách biệt theo thời gian/phiên đo (Cross-session Temporal Split)?*

#### A. Giả thuyết nghiên cứu

- **Giả thuyết không ($H_{0, \text{RQ2}}$):**
  Sai số dự đoán (MAE) và hệ số tương quan ($r$) của mô hình không có sự khác biệt có ý nghĩa thống kê giữa phương pháp chia Window-wise Random Split và phương pháp Subject-wise / Cross-session Split.

- **Giả thuyết đối ($H_{1, \text{RQ2}}$):**
  Có hiện tượng rò rỉ dữ liệu (data leakage) nghiêm trọng trong phương pháp chia Window-wise Random Split:
    - Sai số $\text{MAE}_{\text{Window-wise}}$ bị làm đẹp nhân tạo (lạc quan quá mức, thấp hơn rõ rệt so với thực tế).
    - Khi chuyển sang Subject-wise Split và Cross-session Split, sai số MAE sẽ tăng tối thiểu $40\%$ và hệ số tương quan $r$ suy giảm đáng kể, phản ánh đúng năng lực tổng quát hóa sinh lý của mô hình trên người mới và phiên đo mới.

#### B. Biến nghiên cứu

- **Biến phân chia (Splitting Strategies):**
    1. *Strategy A (Window-wise Random Split - Nguy cơ rò rỉ cao):* Cắt toàn bộ tín hiệu thành các cửa sổ 5–10 giây rồi xáo trộn ngẫu nhiên vào Train/Test. Các cửa sổ của cùng một đối tượng và cùng một lần đo xuất hiện ở cả hai tập.
    2. *Strategy B (Subject-wise Split - Không rò rỉ người):* Leave-One-Subject-Out (LOSO) hoặc chia theo danh sách người tham gia ($k$-fold theo subject_id).
    3. *Strategy C (Cross-session / Temporal Split - Không rò rỉ thời gian):* Với mỗi người, phiên đo thứ nhất (Session 1) dùng để huấn luyện/hiệu chuẩn, các phiên đo sau (Session 2, Session 3...) độc lập hoàn toàn dùng để kiểm thử.

- **Biến đầu ra:** Độ biến thiên sai số ($\Delta\text{MAE} = \text{MAE}_{\text{Subject-wise}} - \text{MAE}_{\text{Window-wise}}$) phân tích riêng cho SBP và DBP.

#### C. Baseline so sánh

- So sánh hiệu năng của cùng một kiến trúc mô hình (Ridge Regression và mô hình phi tuyến) trên 3 chiến lược phân chia Strategy A, B và C.
- Đối chứng với Baseline Zero-Change trên từng chiến lược.

#### D. Chỉ số đánh giá

- Sai số MAE (mmHg), RMSE (mmHg) cho SBP và DBP.
- Hệ số tương quan Pearson ($r$) và biểu đồ Bland-Altman (độ lệch trung bình và khoảng tin cậy 95%).
- Mức độ suy giảm hiệu năng: $\text{Degradation Ratio} = \frac{\text{MAE}_{\text{Strict}} - \text{MAE}_{\text{Random}}}{\text{MAE}_{\text{Random}}} \times 100\%$.

#### E. Điều kiện bác bỏ hoặc chấp nhận giả thuyết

- **Chấp nhận $H_1$:** Khi chứng minh được $\text{MAE}_{\text{Subject-wise}}$ và $\text{MAE}_{\text{Cross-session}}$ lớn hơn $\text{MAE}_{\text{Window-wise}}$ có ý nghĩa thống kê ($p < 0.001$), khẳng định rằng việc chia ngẫu nhiên cửa sổ gây rò rỉ nhận dạng cá nhân và tạo ra độ chính xác ảo.

#### F. Rủi ro phương pháp

- Nếu phân phối biến thiên huyết áp ($\Delta\text{BP}$) giữa các đối tượng trong tập dữ liệu quá hẹp (ví dụ toàn bộ người tham gia đều có huyết áp không đổi trong điều kiện nghỉ), mô hình có thể vô tình tiệm cận với Baseline Zero-Change và khó đo lường độ suy giảm thực chất.

#### G. Dữ liệu tối thiểu cần có

- Tập dữ liệu có cấu trúc phân cấp định danh rõ ràng: `subject_id` $\rightarrow$ `session_id` $\rightarrow$ `event_id` $\rightarrow$ `window_id`.
- Tối thiểu 30–40 phiên đo phân bố trên ít nhất 15 đối tượng, trong đó có biên độ biến thiên huyết áp tự nhiên giữa các phiên đo.

---

### 2.3. RQ3: Năng lực của chỉ số chất lượng tín hiệu (SQI) và độ bất định trong cơ chế từ chối dự đoán

> **Nội dung câu hỏi:**
>
> *Việc tích hợp bộ lọc chất lượng tín hiệu đầu vào (SQI) kết hợp với ngưỡng định lượng độ bất định (Uncertainty Estimation) của mô hình có giúp phát hiện và từ chối một cách hiệu quả các cửa sổ đo không đáng tin cậy để cải thiện độ chính xác tổng thể của hệ thống hay không?*

#### A. Giả thuyết nghiên cứu

- **Giả thuyết không ($H_{0, \text{RQ3}}$):**
  Việc áp dụng ngưỡng lọc SQI và độ bất định để từ chối dự đoán (rejection mechanism) không mang lại sự suy giảm sai số MAE có ý nghĩa thống kê trên tập các mẫu được chấp nhận so với việc giữ lại toàn bộ mẫu đo ($\text{MAE}_{\text{accepted}} \approx \text{MAE}_{\text{all}}$).

- **Giả thuyết đối ($H_{1, \text{RQ3}}$):**
  Tồn tại một cơ chế từ chối chọn lọc (selective prediction) hiệu quả:
    - Bằng cách từ chối tối đa $15\% - 20\%$ số mẫu có SQI thấp hoặc độ bất định dự đoán cao nhất, sai số MAE trên tập mẫu giữ lại giảm tối thiểu $20\%$ đối với cả SBP và DBP.
    - Các mẫu bị từ chối có tương quan thuận rõ rệt với độ lớn sai số thực tế ($|y_i - \hat{y}_i|$).

#### B. Biến nghiên cứu

- **Biến đầu vào đánh giá độ tin cậy:**
    - *SQI tín hiệu PPG:* Chỉ số độ lệch Skewness ($s\text{SQI}$), chỉ số tưới máu (Perfusion Index - PI), tương quan chu kỳ nhịp với mẫu chuẩn ($q\text{SQI}$).
    - *SQI tín hiệu ECG:* Biên độ đỉnh R, tỷ số tín hiệu trên nhiễu (SNR), độ lệch đường nền (baseline wander).
    - *Độ bất định mô hình (Model Uncertainty):* Phương sai dự đoán từ kỹ thuật Monte Carlo Dropout, Ensembling, hoặc mô hình hồi quy chứng cứ (Evidential Regression).

- **Biến điều khiển:** Tỷ lệ từ chối mẫu (Rejection Rate / Abstention Rate) thay đổi từ $0\%$ đến $30\%$.

- **Biến đầu ra:**
    - $\text{MAE}_{\text{retained}}$ (cho SBP và DBP).
    - Diện tích dưới đường cong Sai số theo Tỷ lệ chấp nhận (Error-Retention Curve / AUC-RC).

#### C. Baseline so sánh

1. **Baseline No-Rejection:** Toàn bộ các cửa sổ thu được đều bị ép buộc đưa ra dự đoán (Coverage = $100\%$).
2. **Baseline Random Rejection:** Từ chối ngẫu nhiên cùng một tỷ lệ phần trăm mẫu mà không dựa vào SQI hay độ bất định.
3. **SQI-Only Rejection:** Chỉ lọc bỏ mẫu dựa trên ngưỡng biên độ/nhiễu thô của tín hiệu đầu vào.
4. **Mô hình đề xuất (Two-stage SQI + Uncertainty Rejection):** Bộ lọc phối hợp chất lượng dạng sóng đầu vào và độ bất định phân phối đầu ra.

#### D. Chỉ số đánh giá

- Đường cong đánh đổi giữa tỷ lệ dữ liệu giữ lại (Coverage) và sai số MAE/RMSE trên tập giữ lại.
- Hệ số tương quan hạng Spearman giữa độ bất định ước tính và sai số tuyệt đối thực tế.
- Tỷ lệ phát hiện đúng các mẫu có sai số lớn ($> 10\text{ mmHg}$).

#### E. Điều kiện bác bỏ hoặc chấp nhận giả thuyết

- **Kết luận có bằng chứng ủng hộ $H_1$:** khi:
    1. Chiến lược từ chối đề xuất cải thiện đường cong risk–coverage so với Baseline Random Rejection và SQI-only; báo cáo khoảng tin cậy theo người thay vì khóa trước một ngưỡng $p$ tùy ý.
    2. Đường cong risk–coverage của phương pháp đề xuất tốt hơn các baseline: tại cùng mức coverage, MAE thấp hơn; hoặc tại cùng mức MAE mục tiêu, coverage cao hơn. Một mức vận hành cụ thể chỉ được chọn trên validation set, sau đó đánh giá duy nhất trên test set đã khóa.

#### F. Rủi ro phương pháp

- Thiết lập ngưỡng quá khắt khe khiến tỷ lệ từ chối quá cao (ví dụ từ chối $> 40\%$ mẫu), làm mất đi tính khả dụng liên tục của thiết bị đeo.
- Cần cân bằng giữa tính toàn vẹn thông tin và yêu cầu tính toán nhẹ trên vi điều khiển nhúng.

#### G. Dữ liệu tối thiểu cần có

- Tập dữ liệu thực nghiệm bao gồm cả các đoạn tín hiệu ở trạng thái tĩnh lý tưởng và các đoạn có nhiễu nhẹ tự nhiên (thay đổi vị trí tay, ho, hít thở sâu) đã được gán nhãn đối chứng cuff.

---

## 3. Tổng hợp ma trận so sánh các Baseline trong đề tài

| Baseline | RQ liên quan | Dữ liệu đầu vào | Bản chất thuật toán | Kỳ vọng đối chứng |
|---|---|---|---|---|
| **Zero-Change** | RQ1, RQ2 | Không (chỉ dùng $\text{BP}_0$ mốc) | $\Delta\widehat{\text{BP}} = 0 \Rightarrow \widehat{\text{BP}} = \text{BP}_0$ | Ngưỡng sàn sinh lý; mô hình học máy bắt buộc phải vượt qua baseline này |
| **PPG-Only (Morphology)** | RQ1 | Đặc trưng hình thái PPG cổ tay + HR | Ridge Regression / Random Forest | Xác định trần hiệu năng của tín hiệu quang học đơn lẻ |
| **PAT-Only (Linear)** | RQ1 | Đại lượng PAT từ đỉnh R ECG đến PPG foot | Mô hình nghịch đảo tuyến tính Moens-Korteweg | Kiểm tra giá trị thuần túy của thời gian truyền sóng mạch |
| **ECG + PPG Multi-feature** | RQ1, RQ2 | Kết hợp đặc trưng PPG + PAT + HRV | Hồi quy Ridge / Random Forest / Mô hình phi tuyến | Mô hình đề xuất chính của đề tài |
| **No-Rejection vs Rejection** | RQ3 | Mô hình ECG + PPG kèm SQI & Uncertainty | Ngưỡng lọc SQI và độ bất định | Kiểm chứng cơ chế bảo vệ an toàn và độ tin cậy |

---

## 4. Các điểm cần nhóm và giảng viên xác nhận

> [!IMPORTANT]
> **Checklist xác nhận bản v0.1:**
>
> - [ ] **Thống nhất về đại lượng dự đoán:** Xác nhận dự đoán biến thiên $\Delta\text{SBP}$ và $\Delta\text{DBP}$ có hiệu chuẩn cá nhân thay vì cố gắng dự đoán huyết áp tuyệt đối không hiệu chuẩn.
> - [ ] **Mức cải thiện thực tiễn:** Thống nhất có sử dụng ngưỡng cải thiện MAE hay không; nếu có, phải nêu căn cứ tài liệu/pilot, phân tích cỡ mẫu và khóa ngưỡng trước khi mở test set.
> - [ ] **Tỷ lệ từ chối tối đa:** Chọn mức coverage/tỷ lệ từ chối trên validation set dựa trên đường cong risk–coverage; test set chỉ dùng một lần để báo cáo kết quả cuối.
