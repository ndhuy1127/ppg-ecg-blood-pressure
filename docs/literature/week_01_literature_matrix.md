# Ma trận tổng quan tài liệu nghiên cứu (Tuần 1)

> **Phiên bản:** v0.1
> **Người thực hiện:** Nguyễn Đức Huy
> **Vai trò:** Xử lý tín hiệu, PAT, thống kê, protocol, tổng quan tài liệu và điều phối bài báo
> **Ngày cập nhật:** 2026-09-22

---

## 1. Mục tiêu và phạm vi tổng quan

Tài liệu này tổng hợp và phân tích có hệ thống 12 công trình khoa học tiêu biểu liên quan trực tiếp đến bài toán nghiên cứu của đề tài: **Ước lượng biến thiên huyết áp (ΔSBP, ΔDBP) không dùng băng quấn từ tín hiệu ECG và PPG trên thiết bị đeo cổ tay**.

Ma trận tập trung vào các khía cạnh cốt lõi:
1. **Phân biệt bản chất sinh lý giữa PAT và PTT:** Làm rõ vai trò của thời gian tiền tống máu (Pre-ejection Period - PEP) và hệ quả khi lấy PAT làm đại diện cho PTT.
2. **Giá trị gia tăng của ECG + PPG so với PPG đơn lẻ.**
3. **Hiệu chuẩn cá nhân hóa (Personalized Calibration) và dự đoán biến thiên ($\Delta\text{BP}$):** Phương pháp theo dõi huyết áp qua các phiên đo (cross-session/longitudinal).
4. **Tránh rò rỉ dữ liệu (Data Leakage):** Tách tập dữ liệu theo người (subject-wise) và theo thời gian (temporal/session-wise), phê phán việc chia ngẫu nhiên từng cửa sổ tín hiệu (record/window-wise split).
5. **Chất lượng tín hiệu (SQI) và cơ chế từ chối dự đoán (Uncertainty / Rejection Mechanism):** Đảm bảo an toàn và độ tin cậy trong điều kiện đo thực tế.
6. **Tính khả thi trên thiết bị đeo cổ tay (Wrist-worn form factor).**

---

## 2. Bảng ma trận tổng quan 12 nghiên cứu

| STT | Trích dẫn ngắn | Năm | DOI / URL | Loại dữ liệu | Vị trí PPG | ECG? | Đại lượng PAT/PTT | Nhãn huyết áp | Chia Train/Val/Test | Hiệu chuẩn cá nhân? | Chỉ số đánh giá | Kết quả chính | Hạn chế | Mức độ liên quan | Ý tưởng kế thừa |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **1** | Mukkamala et al. | 2015 | [10.1109/TBME.2015.2441951](https://doi.org/10.1109/TBME.2015.2441951) | Tổng quan lý thuyết & thực nghiệm | Ngón tay, cổ tay, tai | Có | **PTT vs PAT:** Phân tích bản chất $\text{PAT} = \text{PEP} + \text{PTT}$ | Xâm lấn (A-line) & Cuff | Lý thuyết tổng quan | Bắt buộc (cần hiệu chuẩn định kỳ) | Tương quan $r$, sai số mmHg | Thiết lập cơ sở vật lý (Moens-Korteweg, Hughes). Chứng minh PEP chiếm tỷ trọng lớn và biến thiên độc lập với BP, gây sai lệch nếu coi PAT là PTT | Cần hiệu chuẩn thường xuyên; các giả định đàn hồi mạch bị đơn giản hóa | Rất cao (Lý thuyết nền tảng) | Khung lý thuyết phân tách PEP khỏi PTT; mô hình hóa toán học phi tuyến giữa PTT và huyết áp |
| **2** | Zhang et al. | 2011 | [10.1152/japplphysiol.00980.2011](https://doi.org/10.1152/japplphysiol.00980.2011) | Thực nghiệm động vật (6 chó) can thiệp thuốc | Động mạch ngoại vi | Có | **PAT vs PTT:** So sánh trực tiếp PTT thực (aorta-to-femoral) và PAT | Huyết áp động mạch xâm lấn liên tục | Đánh giá theo cá thể qua can thiệp vận mạch | Có hiệu chuẩn ban đầu theo cá thể | RMSE (mmHg) cho MAP | PTT dự đoán MAP đạt RMSE $4.8 \pm 1.0\text{ mmHg}$, trong khi PAT có RMSE $10.4 \pm 5.6\text{ mmHg}$. Kết luận: PAT không phải là đại lượng thay thế tương đương cho PTT | Cỡ mẫu nhỏ (động vật); thuốc vận mạch làm biến đổi PEP mạnh hơn sinh hoạt thường ngày | Rất cao (Cảnh báo phương pháp) | Tuyệt đối không gọi PAT là PTT; trong mô hình cổ tay phải xử lý hoặc bù trừ thành phần biến thiên PEP |
| **3** | Payne et al. | 2006 | [10.1152/japplphysiol.00657.2005](https://doi.org/10.1152/japplphysiol.00657.2005) | Lâm sàng người (20 người khỏe mạnh) can thiệp thuốc | Ngón tay | Có | **PAT (gọi là PTT từ ECG):** R-peak đến chân sóng PPG | Đo huyết áp vỗ kế Finapres | Theo đối tượng qua các giai đoạn can thiệp | Có | Hệ số tương quan $r$ | Thay đổi PAT không tương quan chặt với SBP khi có can thiệp làm thay đổi co bóp tim (inotropic). Biến thiên PEP phá vỡ giả định tuyến tính giữa PAT và BP | Thử nghiệm cấp tính trong phòng thí nghiệm; chưa đánh giá thiết bị đeo | Cao (Cơ sở sinh lý học) | Thiết kế protocol cần có các pha kích hoạt sinh lý (stress/vận động) để kiểm tra độ bền vững của PAT |
| **4** | Yoshizawa et al. | 2023 | [10.1109/JSEN.2023.3272921](https://doi.org/10.1109/JSEN.2023.3272921) | Dữ liệu công khai (MIMIC-II/III) | Ngón tay | Có | PAT và dạng sóng PPG/ECG | Huyết áp xâm lấn A-line | **So sánh trực tiếp:** Random split vs Subject-wise split | Không (zero-shot) và có thích nghi | MAE, RMSE, Pearson $r$ | **Rò rỉ dữ liệu (Data leakage):** Random split khiến mô hình ghi nhớ hình thái sóng cá nhân, tạo kết quả ảo ($r > 0.85$, MAE thấp). Khi chuyển sang Subject-wise split, MAE tăng mạnh, $r$ sụt giảm nghiêm trọng | Chỉ dùng dữ liệu ICU hồi sức; PPG ngón tay; chưa thử nghiệm trên cổ tay | Rất cao (Chuẩn mực đánh giá) | **Bắt buộc phân chia Subject-wise split**; không bao giờ dùng random split theo từng nhịp/cửa sổ tín hiệu |
| **5** | Kachuee et al. | 2017 | [10.1109/TBME.2016.2580904](https://doi.org/10.1109/TBME.2016.2580904) | Dữ liệu MIMIC-II (gần 1,000 bản ghi) | Ngón tay | Có | PAT và 21 đặc trưng hình thái PPG | Huyết áp xâm lấn A-line | Chia theo bản ghi / bệnh nhân | Có mô hình cá nhân hóa và tổng quát | MAE, STD (AAMI/BHS) | Kết hợp PAT và đặc trưng PPG qua Random Forest / Ridge Regression đạt MAE $\sim 8.2\text{ mmHg}$ (SBP) và $\sim 4.3\text{ mmHg}$ (DBP) sau khi hiệu chuẩn cá nhân | Dữ liệu ICU nhiều bệnh lý; một số đoạn vẫn có nguy cơ rò rỉ nếu cùng bệnh nhân có nhiều record | Cao (Đặc trưng & Baseline) | Bộ đặc trưng hình thái PPG (độ rộng xung, tỷ lệ diện tích, thời gian dốc) và baseline Ridge/Random Forest |
| **6** | Esmaili et al. | 2017 | [10.1109/TIM.2017.2745081](https://doi.org/10.1109/TIM.2017.2745081) | Thực nghiệm 26 người khỏe mạnh (nghỉ & gắng sức) | Ngón tay | Có | So sánh PTT (từ âm tim PCG) và PAT (từ ECG) | Máy đo cuff tự động | Chia kiểm tra chéo theo đối tượng | Có hiệu chuẩn ban đầu (1 điểm & 2 điểm) | MAE, STD, AAMI | Mô hình phi tuyến kết hợp PAT + thông tin cá nhân cải thiện đáng kể so với mô hình tuyến tính đơn biến. MAE SBP đạt $4.9\text{ mmHg}$ khi có hiệu chuẩn | Kích thước mẫu còn nhỏ (26 người); đo ở ngón tay trong phòng thí nghiệm | Rất cao (So sánh PAT vs PTT & Hiệu chuẩn) | Công thức hiệu chuẩn cá nhân hóa 1 điểm và 2 điểm; so sánh trực tiếp sai số giữa việc có/không có bù trừ PEP |
| **7** | Ding et al. | 2016 | [10.1109/TBME.2015.2480679](https://doi.org/10.1109/TBME.2015.2480679) | 12 người khỏe mạnh thực nghiệm (thay đổi tư thế, lạnh, đạp xe) | Ngón tay | Có | PTT/PAT kết hợp tỷ số cường độ PPG (PIR) | Finapres & Cuff | Đánh giá cá thể qua chuỗi thời gian | Có hiệu chuẩn cá nhân | ME $\pm$ SD, MAE | Bổ sung tỷ số cường độ PPG (Photoplethysmogram Intensity Ratio - PIR) phản ánh đường kính lòng mạch giúp bù trừ sự thay đổi trương lực mạch, giảm đáng kể độ lệch trôi khi theo dõi liên tục | Cỡ mẫu 12 người; cảm biến kẹp ngón tay chưa tích hợp gọn trên cổ tay | Cao (Đặc trưng bù trừ biến thiên) | Bổ sung đặc trưng biên độ quang phổ / PIR vào danh sách trích xuất từ PPG để theo dõi biến thiên huyết áp $\Delta\text{BP}$ |
| **8** | Zhang Q. et al. | 2017 | [10.1186/s12938-017-0317-z](https://doi.org/10.1186/s12938-017-0317-z) | Thực nghiệm trên người (20 tình nguyện viên) | Cổ tay & cẳng tay | Có | PAT đo trên cùng một cánh tay (single-arm ECG+PPG) | Cuff chuẩn AAMI | Đánh giá trên từng cá thể qua thời gian | Có hiệu chuẩn ban đầu | MAE, Correlation coefficient | Chứng minh tính khả thi của hệ thống đeo một tay (đo ECG cánh tay - ngực hoặc 2 điểm trên cùng cánh tay) để tính PAT cổ tay, MAE SBP $5.3 \pm 4.1\text{ mmHg}$ | Biên độ ECG một tay rất nhỏ ($< 100\mu\text{V}$), dễ nhiễu cử động | Rất cao (Thiết kế phần cứng đeo cổ tay) | Phương án bố trí điện cực ECG trên cùng thiết bị đeo cổ tay; kỹ thuật xử lý tín hiệu ECG biên độ nhỏ |
| **9** | Vybornova et al. | 2021 | [10.1097/MBP.0000000000000531](https://doi.org/10.1097/MBP.0000000000000531) | Thử nghiệm lâm sàng 86 đối tượng theo dõi 1 tháng | **Cổ tay** (Vòng đeo Aktiia) | Không (chỉ quang học PPG) | Pulse wave analysis (PWA) cổ tay | Máy đo cuff chuẩn kép theo ISO 81060-2 | Tách biệt hoàn toàn theo thời gian (1 tháng) | **Có (bắt buộc hiệu chuẩn 1 lần đầu bằng cuff)** | Độ lệch trung bình $\pm$ SD theo ISO 81060-2 | Đáp ứng tiêu chuẩn ISO 81060-2 sau 1 tháng theo dõi: SBP sai số $0.46 \pm 7.75\text{ mmHg}$, DBP $0.39 \pm 6.22\text{ mmHg}$ khi ngồi nghỉ | Chỉ đo tự động khi người dùng bất động hoàn toàn; không có ECG/PAT để hỗ trợ khi mạch co thắt mạnh | Rất cao (Đánh giá dài hạn & Chuẩn ISO) | Protocol đánh giá hiệu chuẩn kéo dài qua các phiên đo (cross-session/longitudinal); quy định đo ở trạng thái nghỉ ổn định |
| **10** | Elgendi | 2016 | [10.3390/bioengineering3040021](https://doi.org/10.3390/bioengineering3040021) | Tập dữ liệu lâm sàng & thử nghiệm PPG đa dạng | Đa vị trí (ngón tay, cổ tay) | Không | Hình thái chu kỳ xung PPG | Nhãn gán chất lượng bởi chuyên gia | Phân loại và đánh giá SQI | Không áp dụng | Độ nhạy, độ đặc hiệu, F1-score | Đề xuất và so sánh các bộ chỉ số chất lượng tín hiệu (SQI) cho PPG. Chỉ số độ lệch (Skewness SQI - $s\text{SQI}$) và tương quan mẫu ($q\text{SQI}$) là tiêu chí hiệu quả nhất để loại bỏ xung nhiễu | Chưa liên kết trực tiếp với mô hình dự đoán huyết áp | Cao (Xử lý tín hiệu & SQI) | Ứng dụng Skewness SQI và Perfusion Index (PI) để xây dựng ngưỡng lọc sạch tín hiệu trước khi đưa vào mô hình |
| **11** | Shen et al. | 2024 | [10.1016/j.bspc.2024.106104](https://doi.org/10.1016/j.bspc.2024.106104) | Dữ liệu công khai & thực nghiệm | Ngón tay | Có | PAT và chuỗi PPG | Huyết áp A-line và Cuff | Subject-wise split | Có hiệu chuẩn | MAE, RMSE, Tỷ lệ loại trừ (Rejection rate) | Ứng dụng Deep Evidential Regression để định lượng độ bất định (epistemic & aleatoric). Từ chối 15% mẫu có độ bất định cao giúp giảm MAE từ $7.2\text{ mmHg}$ xuống $4.6\text{ mmHg}$ | Độ phức tạp tính toán cao; chưa tối ưu hóa cho vi điều khiển nhúng | Rất cao (Độ bất định & Cơ chế từ chối) | Thiết kế cơ chế từ chối dự đoán (rejection mechanism) dựa trên độ bất định dự đoán kết hợp SQI tín hiệu đầu vào |
| **12** | Wang et al. (PulseDB) | 2023 | [10.3389/fdgth.2022.1090854](https://doi.org/10.3389/fdgth.2022.1090854) | 5,394 đối tượng từ MIMIC-III & VitalDB (3.8 triệu nhịp) | Ngón tay / bẹn | Có | ECG + PPG + ABP | Xâm lấn A-line liên tục | **Subject-level 3-way split** (Train/Val/Test độc lập) | Phân tích cả Zero-shot và Few-shot calibration | MAE, SD, Correlation | Công bố benchmark chuẩn hóa lớn nhất; chỉ ra rằng hầu hết các báo cáo trước đây đạt sai số siêu nhỏ là do data leakage hoặc tập test quá hẹp | Tín hiệu từ bệnh nhân hồi sức/phẫu thuật, có can thiệp thuốc tim mạch | Cao (Benchmark & Benchmark protocol) | Quy tắc làm sạch dữ liệu, phát hiện đỉnh R/chân sóng PPG chuẩn hóa; cấu trúc benchmark tách bạch người tham gia |

---

## 3. Tổng hợp chi tiết các trục kỹ thuật chính

### 3.1. Bản chất vật lý: PAT khác biệt PTT như thế nào?
- **Định nghĩa chuẩn xác:**
  $$\text{PAT} = \text{PEP} + \text{PTT}$$
  - $\text{PEP}$ (Pre-ejection Period): Thời gian tiền tống máu, tính từ lúc tâm thất khử cực (đỉnh R trên ECG) đến khi van động mạch chủ mở (máu bắt đầu tống vào quai động mạch chủ).
  - $\text{PTT}$ (Pulse Transit Time): Thời gian sóng áp lực cơ học thực sự lan truyền trong lòng mạch từ gốc động mạch chủ đến vị trí đo ngoại vi (cổ tay).
- **Hệ quả nghiên cứu:**
  - $\text{PTT}$ tuân theo phương trình Moens-Korteweg và Hughes, tỷ lệ nghịch với vận tốc sóng mạch ($\text{PWV}$) và độ cứng thành mạch, do đó có tương quan vật lý chặt chẽ với huyết áp.
  - Tuy nhiên, $\text{PEP}$ chịu ảnh hưởng mạnh bởi trạng thái giao cảm, sức co bóp cơ tim (inotropic state) và tiền gánh/hậu gánh, có thể biến thiên từ $30\text{ ms}$ đến $120\text{ ms}$ độc lập với huyết áp (như đã chứng minh trong các nghiên cứu của Zhang 2011 và Payne 2006).
  - **Quy ước bắt buộc trong dự án:** Khoảng thời gian từ đỉnh R của ECG đến chân sóng PPG ở cổ tay phải được gọi chính xác là **PAT (Pulse Arrival Time)**, tuyệt đối không được gọi là PTT thực sự. Mọi mô hình dựa trên PAT phải hiểu rõ rằng tín hiệu chứa thành phần nhiễu PEP.

### 3.2. Hiệu chuẩn cá nhân hóa và bài toán dự đoán biến thiên ($\Delta\text{BP}$)
- Mối quan hệ giữa PAT/PPG và huyết áp phụ thuộc vào thông số giải phẫu và sinh lý riêng của từng cá nhân: chiều dài động mạch ($L$), đường kính mạch không tải ($r_0$), độ dày thành mạch ($h$), và mô đun đàn hồi cơ bản ($E_0$).
- Không thể có một mô hình tổng quát "calibration-free" dự đoán huyết áp tuyệt đối chính xác cho toàn bộ quần thể nếu chỉ dựa vào tín hiệu ngoại vi một vị trí mà không có rò rỉ dữ liệu.
- Do đó, cách tiếp cận khoa học nhất là:
  1. Sử dụng 1 hoặc 2 lần đo cuff chuẩn ban đầu làm mốc hiệu chuẩn (Calibration Baseline: $\text{SBP}_0, \text{DBP}_0$).
  2. Mô hình tập trung dự đoán **biến thiên huyết áp giữa các phiên đo**:
     $$\Delta\text{SBP} = \text{SBP}_{\text{target}} - \text{SBP}_0$$
     $$\Delta\text{DBP} = \text{DBP}_{\text{target}} - \text{DBP}_0$$
  3. Giá trị huyết áp ước tính: $\widehat{\text{BP}} = \text{BP}_0 + \Delta\widehat{\text{BP}}$.

### 3.3. Rò rỉ dữ liệu (Data Leakage) trong dữ liệu sinh lý dạng chuỗi/cửa sổ
Nghiên cứu của Yoshizawa et al. (2023) và benchmark PulseDB (Wang et al., 2023) đã chỉ rõ vấn đề nhức nhối nhất trong các công bố về ước lượng huyết áp bằng học máy:
- **Random sample/window split (Sai lầm phổ biến):** Cắt tín hiệu liên tục của một người thành hàng ngàn cửa sổ nhỏ (ví dụ 5 giây), sau đó xáo trộn ngẫu nhiên vào tập Train, Validation và Test.
  - *Hậu quả:* Mô hình không học quy luật động học huyết áp mà học cách nhận diện "vân tay sinh lý" (dạng sóng đặc trưng của cá nhân đó). Kết quả test đạt MAE $< 3\text{ mmHg}$, nhưng khi áp dụng cho người mới hoặc phiên đo mới, sai số bùng nổ $> 15\text{ mmHg}$.
- **Subject-wise split (Quy chuẩn bắt buộc):** Dữ liệu của một người chỉ được xuất hiện ở duy nhất một tập (Train, Val HOẶC Test).
- **Temporal / Cross-session split:** Trong bài toán hiệu chuẩn cá nhân, các cửa sổ dùng để hiệu chuẩn phải diễn ra trước theo trục thời gian, và các cửa sổ kiểm tra phải thuộc phiên đo hoàn toàn độc lập sau đó, ngăn cách tối thiểu nhiều giờ hoặc nhiều ngày.

### 3.4. Chất lượng tín hiệu (SQI) và cơ chế từ chối dự đoán (Rejection Mechanism)
- Dữ liệu thu từ thiết bị đeo cổ tay rất nhạy cảm với nhiễu chuyển động (motion artifacts) và thay đổi áp lực tiếp xúc.
- Việc ép mô hình đưa ra dự đoán trên các đoạn tín hiệu suy hao dẫn đến sai số nghiêm trọng.
- Nghiên cứu của Shen et al. (2024) và Elgendi (2016) chứng minh rằng: Một hệ thống đáng tin cậy phải có khả năng trả lời: *"Tín hiệu không đủ tin cậy, từ chối đưa ra kết quả đo"* (Selective Prediction / Abstention).
- Sự kết hợp giữa SQI tiền xử lý (loại bỏ cửa sổ có skewness bất thường hoặc mất đỉnh) và độ bất định của mô hình (Uncertainty threshold) là chìa khóa để giảm MAE trên các mẫu được chấp nhận.

---

## 4. Tổng hợp khoảng trống nghiên cứu (Research Gaps)

Từ việc khảo sát 12 công trình trên, nhóm xác định 4 khoảng trống nghiên cứu lớn mà y văn hiện tại chưa giải quyết trọn vẹn:

1. **Khoảng trống 1 (Hình thức đeo cổ tay đa cảm biến đồng bộ):**
   Phần lớn các nghiên cứu PTT/PAT chính xác cao đều sử dụng cảm biến ngón tay kết hợp dán điện cực ngực chuẩn phòng thí nghiệm (MIMIC, Finapres). Các thiết bị thương mại đeo cổ tay thành công (như Aktiia) lại chỉ dùng PPG quang học đơn thuần và phụ thuộc vào đo khi ngủ/nghỉ, thiếu tín hiệu ECG để tách pha huyết động. Nghiên cứu tích hợp đồng thời ECG và PPG trên cùng một thiết bị cổ tay để đánh giá PAT còn khan hiếm và gặp trở ngại về chất lượng tín hiệu.
2. **Khoảng trống 2 (Độ tin cậy của gia số PAT so với chỉ dùng PPG):**
   Chưa có câu trả lời dứt khoát trong điều kiện đo thực tế: Khi đã thực hiện hiệu chuẩn cá nhân và đánh giá nghiêm ngặt tách người (subject-wise), việc bổ sung kênh ECG để lấy PAT có thực sự mang lại ý nghĩa thống kê vượt trội hơn so với một mô hình trích xuất sâu các đặc trưng hình thái PPG cổ tay hay không?
3. **Khoảng trống 3 (Sự thiếu vắng đánh giá theo phiên đo độc lập - Cross-session Generalization):**
   Hầu hết các bài báo chỉ thu dữ liệu trong một buổi duy nhất kéo dài vài chục phút với các bài test gắng sức ngắn. Sự trôi dạt (drift) của mô hình sau 24 giờ, 48 giờ hoặc 1 tuần do thay đổi vị trí đeo vòng, trương lực mạch nền và thay đổi điện cực chưa được mô hình hóa thấu đáo trong các thiết kế nguồn mở.
4. **Khoảng trống 4 (Thiếu cơ chế định lượng độ tin cậy hai tầng):**
   Các hệ sinh thái thuật toán hiện nay thường xử lý tách rời: hoặc lọc nhiễu ở mức tín hiệu (SQI thô), hoặc tính toán độ bất định của mạng nơ-ron nhưng bỏ qua ngữ cảnh vật lý. Một quy trình kết hợp SQI tín hiệu đầu vào + độ bất định đầu ra để quyết định "từ chối dự đoán" (rejection mechanism) chưa được chuẩn hóa cho thiết bị đeo cổ tay.

---

## 5. Định vị đóng góp của đề tài

Dựa trên các khoảng trống nghiên cứu đã chỉ ra, đề tài này định vị các đóng góp khoa học và kỹ thuật rõ ràng:

1. **Về thiết kế hệ thống (Hardware & Sensing):**
   Xây dựng nguyên mẫu nghiên cứu dạng vòng đeo cổ tay tích hợp đồng bộ phần cứng giữa cảm biến quang học PPG (bước sóng tối ưu cho mao mạch cổ tay) và khối khuếch đại vi sai ECG (bố trí điện cực mặt đáy tiếp xúc cổ tay và mặt trên tiếp xúc ngón tay đối diện), đảm bảo thu nhận đồng thời tín hiệu để trích xuất PAT trên cùng một thiết bị.
2. **Về phương pháp luận đánh giá (Methodological Rigor):**
   - Áp dụng triệt để nguyên tắc **Không rò rỉ dữ liệu (No Data Leakage)**: Đánh giá theo cơ chế Leave-Subject-Out Cross-Validation và Temporal Session Split.
   - Định nghĩa mẫu độc lập nghiêm ngặt: Mỗi lần đo cuff là một mốc đối chứng duy nhất, không nhân bản cửa sổ để thổi phồng kích thước mẫu.
   - Thử nghiệm kiểm định thống kê đa tầng (Ablation study): So sánh trực diện mô hình Baseline Zero-change, Mô hình PPG-only, Mô hình PAT-only, và Mô hình tích hợp ECG + PPG để trả lời chính xác câu hỏi về giá trị thực sự của PAT.
3. **Về thuật toán và an toàn dự đoán (Signal Quality & Rejection):**
   Xây dựng pipeline hai tầng:
   - Tầng 1: Đánh giá SQI (dựa trên $s\text{SQI}$, tương quan hình thái và kiểm tra đỉnh R/chân sóng PPG đồng bộ).
   - Tầng 2: Định lượng độ bất định của mô hình dự đoán. Hệ thống sẽ từ chối đưa ra kết quả nếu độ tin cậy dưới ngưỡng an toàn, đảm bảo tính ứng dụng thực tế trong giám sát sức khỏe dài hạn.
