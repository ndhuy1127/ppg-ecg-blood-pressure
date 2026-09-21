# Báo cáo tiến độ Tuần 1

> **Giai đoạn:** Tuần 1 / 28 tuần
> **Người tổng hợp:** Nguyễn Đức Huy
> **Vai trò:** Xử lý tín hiệu, PAT, phương pháp thống kê, protocol, tổng quan y văn và điều phối báo cáo
> **Ngày báo cáo:** 2026-09-22

---

## 1. Mục tiêu tuần 1

Theo kế hoạch tuần tại [docs/plans/WEEK_01.md](../../../docs/plans/WEEK_01.md), các mục tiêu trọng tâm gồm:
1. Chuẩn hóa cấu trúc repository, thiết lập môi trường Python và pipeline CI hoạt động ổn định.
2. Xác định yêu cầu phần cứng, thiết lập bảng BOM v0.1 và đề xuất các phương án điện cực ECG.
3. Hoàn thành ma trận tổng quan sơ bộ 10–12 bài báo: xác minh DOI/tiêu đề, trích xuất phương pháp và đánh dấu rõ các số liệu cần audit toàn văn trước khi đưa vào bài báo.
4. Xây dựng và chốt bản thảo bộ câu hỏi nghiên cứu RQ1–RQ3 (v0.1).
5. Xây dựng khung protocol nghiên cứu thực nghiệm v0.1 và khung nguyên tắc đạo đức y sinh v0.1.
6. Thiết lập biên bản/agenda họp khởi động nhóm và tổng hợp báo cáo tiến độ tuần 1.

---

## 2. Thành viên phụ trách và Phân công công việc

| Công việc | Người phụ trách chính | Reviewer dự kiến | Trạng thái ghi nhận |
|---|---|---|---|
| Chuẩn hóa repo, môi trường Python, CI, quy ước dữ liệu | Linh | Huy, Đức Anh | Đang tích hợp *(Cần Linh xác nhận bằng chứng commit trong repo)* |
| Yêu cầu phần cứng, BOM v0.1, sơ đồ khối, phương án điện cực ECG | Đức Anh | Huy, Linh | Đang thực hiện *(Cần Đức Anh xác nhận bằng chứng commit trong repo)* |
| Ma trận tổng quan 12 bài báo, RQ1–RQ3, khung protocol, khung ethics | Huy | Linh, Đức Anh | **Đã có đủ bản thảo v0.1; đang chờ review chéo và phê duyệt của giảng viên** |
| Biên bản họp khởi động và tổng hợp báo cáo tuần 1 | Huy | Cả nhóm | **Đã hoàn thành bản thảo v0.1** |

---

## 3. Công việc đã hoàn thành của Huy

Trong phạm vi trách nhiệm của mình trong Tuần 1, Huy đã hoàn thành 100% các đầu việc được giao:

- [x] **Ma trận tổng quan 12 bài báo khoa học (A):** Đã xác minh DOI và tiêu đề của 12 công trình; đã hiệu chỉnh các sai lệch số liệu được phát hiện. Đây là structured rapid review, chưa phải systematic review. Mọi con số dùng trong bản thảo bài báo phải có trích dẫn tới đúng bảng/hình/trang của nguồn gốc.
- [x] **Bộ câu hỏi nghiên cứu RQ1–RQ3 (B):** Xây dựng chi tiết 3 câu hỏi nghiên cứu trung tâm bản v0.1 kèm đầy đủ giả thuyết $H_0/H_1$, biến đầu vào/đầu ra, hệ thống baseline đối chứng (Zero-change, PPG-only, PAT linear, ECG+PPG fusion), chỉ số đánh giá riêng biệt cho SBP và DBP, điều kiện kiểm định thống kê và phân tích rủi ro phương pháp luận.
- [x] **Khung protocol nghiên cứu thực nghiệm v0.1 (C):** Thiết lập quy trình đo đối chứng đồng bộ ECG+PPG tại cổ tay với máy đo cuff bắp tay, quy tắc ghép cửa sổ tín hiệu (chỉ lấy cửa sổ trước khi bơm cuff), định nghĩa nghiêm ngặt một mẫu độc lập (1 lần đo cuff = 1 nhãn), chiến lược chia dữ liệu Subject-wise và Cross-session, và kế hoạch thống kê Bootstrap theo đối tượng.
- [x] **Khung đạo đức nghiên cứu v0.1 (D):** Xây dựng bản thảo khung bảo vệ quyền lợi người tham gia, quy trình giải thích và lấy phiếu đồng thuận (Informed Consent), tiêu chí dừng phiên đo, chính sách bảo mật ẩn danh hóa bằng `subject_id` (đồng bộ tuyệt đối với `docs/DATA_POLICY.md`), và quy định an toàn điện tối thượng: **Tuyệt đối không sạc thiết bị khi đang đeo**.
- [x] **Biên bản / Chương trình họp khởi động tuần 1 (E):** Lập dự thảo biên bản/agenda họp làm rõ vai trò từng người, khóa quy trình nhánh `dev/thanh-vien` $\rightarrow$ `develop` $\rightarrow$ `main`, quy tắc review chéo và danh sách các vấn đề kỹ thuật/học thuật cần xin ý kiến giảng viên.
- [x] **Kiểm tra kỹ thuật tự động:** Chạy toàn bộ các bộ công cụ kiểm tra chất lượng mã nguồn và môi trường trên máy local, đạt kết quả tuyệt đối.

---

## 4. Danh mục sản phẩm đầu ra và Đường dẫn

| STT | Tên sản phẩm | Đường dẫn tương đối | Trạng thái |
|---|---|---|---|
| 1 | Ma trận tổng quan 12 bài báo khoa học | [docs/literature/week_01_literature_matrix.md](../../../docs/literature/week_01_literature_matrix.md) | Bản thảo v0.1 đã audit vòng 1 |
| 2 | Bộ câu hỏi nghiên cứu RQ1–RQ3 | [docs/research_questions_v0.1.md](../../../docs/research_questions_v0.1.md) | Đã hoàn thành v0.1 |
| 3 | Khung Protocol nghiên cứu thực nghiệm | [docs/protocol/protocol_outline_v0.1.md](../../../docs/protocol/protocol_outline_v0.1.md) | Đã hoàn thành v0.1 |
| 4 | Khung Đạo đức nghiên cứu | [docs/ethics/ethics_outline_v0.1.md](../../../docs/ethics/ethics_outline_v0.1.md) | Đã hoàn thành v0.1 |
| 5 | Biên bản / Chương trình họp khởi động | [docs/meetings/week_01_kickoff.md](../../../docs/meetings/week_01_kickoff.md) | Đã hoàn thành v0.1 |
| 6 | Báo cáo tiến độ tuần 1 | [reports/weekly/week_01/README.md](README.md) | Đã cập nhật đầy đủ |

---

## 5. Tóm tắt các nội dung chuyên môn chính

### 5.1. Tóm tắt ma trận 12 bài báo khoa học
1. **Mukkamala et al. (2015, IEEE TBME):** Khung lý thuyết nền tảng về PTT/PAT. Chứng minh công thức $\text{PAT} = \text{PEP} + \text{PTT}$ và nhấn mạnh sự biến thiên độc lập của PEP có thể làm sai lệch dự đoán huyết áp.
2. **Zhang et al. (2011, J Appl Physiol):** Thực nghiệm can thiệp thuốc trên động vật chứng minh PAT có sai số RMSE cao gấp hơn 2 lần PTT thực ($10.4\text{ mmHg}$ so với $4.8\text{ mmHg}$). Cảnh báo không thể dùng PAT thay thế trực tiếp cho PTT.
3. **Payne et al. (2006, J Appl Physiol):** Khẳng định trên người rằng sự thay đổi sức co bóp cơ tim làm biến đổi PEP, phá vỡ mối quan hệ tuyến tính đơn thuần giữa PAT và huyết áp.
4. **Yoshizawa et al. (2023, IEEE Sensors J):** Chỉ rõ hiện tượng rò rỉ dữ liệu (data leakage) khi chia ngẫu nhiên từng cửa sổ tín hiệu (window-wise). Đặt ra tiêu chuẩn bắt buộc phải chia dữ liệu theo đối tượng (subject-wise split).
5. **Kachuee et al. (2017, IEEE TBME):** Khai thác 21 đặc trưng hình thái PPG kết hợp PAT và các thuật toán học máy cổ điển (Ridge Regression, Random Forest) có hiệu chuẩn cá nhân.
6. **Esmaili et al. (2017, IEEE TIM):** Đánh giá các mô hình hiệu chuẩn cá nhân hóa phi tuyến tính trên người khỏe mạnh, so sánh sai số khi có và không có bù trừ PEP.
7. **Ding et al. (2016, IEEE TBME):** Bổ sung tỷ số cường độ quang học PPG (PIR) nhằm phản ánh sự thay đổi đường kính mạch máu, giúp cải thiện độ ổn định khi theo dõi huyết áp liên tục.
8. **Zhang Q. et al. (2017, BioMed Eng OnLine):** Chứng minh tính khả thi của hệ thống đo một bên tay (single-arm ECG+PPG) để trích xuất PAT tại cổ tay/cẳng tay.
9. **Vybornova et al. (2021, Blood Press Monit):** Nghiên cứu lâm sàng 1 tháng của vòng đeo tay quang học Aktiia theo chuẩn ISO 81060-2, chứng minh tính khả thi của phương pháp hiệu chuẩn cá nhân ban đầu để theo dõi huyết áp dài hạn.
10. **Elgendi (2016, Bioengineering):** Tổng hợp và chuẩn hóa các chỉ số chất lượng tín hiệu PPG ($s\text{SQI}$, $q\text{SQI}$) để lọc bỏ nhiễu trước khi trích xuất đặc trưng.
11. **Shen et al. (2024, Biomed Signal Process Control):** Đề xuất cơ chế định lượng độ bất định (Evidential Deep Learning) để từ chối các mẫu dự đoán không tin cậy trong ước lượng huyết áp không cuff.
12. **Wang et al. (2023, Front Digit Health - PulseDB):** Bộ dữ liệu gồm 5,245,454 đoạn 10 giây từ 5,361 người; cung cấp các tập calibration-based, calibration-free và AAMI test để benchmark có thể tái lập.

### 5.2. Tóm tắt bộ câu hỏi nghiên cứu RQ1–RQ3
- **RQ1:** Đánh giá giá trị gia tăng của việc kết hợp ECG và PAT so với mô hình chỉ dùng PPG sau khi đã hiệu chuẩn cá nhân, trên các phiên đo tương lai. Baseline bắt buộc gồm: Zero-change, PPG-only, PAT linear và ECG+PPG fusion.
- **RQ2:** Kiểm chứng sự suy giảm hiệu năng khi chuyển từ cách chia cửa sổ ngẫu nhiên (Window-wise Random Split - có rò rỉ) sang cách chia tách người (Subject-wise Split) và tách phiên đo (Cross-session Split).
- **RQ3:** Đánh giá hiệu quả của cơ chế từ chối dự đoán (rejection mechanism) hai tầng (SQI tín hiệu đầu vào + độ bất định mô hình đầu ra) trong việc giảm thiểu sai số trên tập mẫu được chấp nhận.

### 5.3. Tóm tắt Khung Protocol và Khung Đạo đức
- **Protocol v0.1:** Thiết kế đo lặp lại nhiều phiên (`session_id`) trên 15–20 người khỏe mạnh. Vòng đeo tay bên tay không thuận, cuff chuẩn bắp tay đối diện, tư thế ngồi tựa lưng ngang tim. Cửa sổ ghép nhãn là 60 giây tĩnh trước khi bơm cuff. Không nhân bản cửa sổ (1 lần đo cuff = 1 nhãn độc lập duy nhất). Đánh giá thống kê Bootstrap theo đối tượng.
- **Ethics v0.1:** Nhấn mạnh bản chất nguyên mẫu nghiên cứu kỹ thuật y sinh, không phải thiết bị y tế. Quy trình lấy phiếu đồng thuận (Informed Consent) minh bạch, quyền rút lui vô điều kiện. Ẩn danh hóa triệt để bằng `subject_id`, không lưu PII trong dữ liệu. Quy tắc an toàn điện: **Tuyệt đối không sạc thiết bị khi đang đeo**.

---

## 6. Kết quả kiểm tra kỹ thuật (Verification Results)

Toàn bộ các công cụ kiểm tra tự động của dự án đã được chạy trực tiếp trên môi trường ảo của repository:

| Công cụ kiểm tra | Lệnh thực hiện | Kết quả | Chi tiết / Bằng chứng |
|---|---|---|---|
| **Ruff Linter** | `ruff check .` | **PASS** | 0 cảnh báo, 0 lỗi cú pháp |
| **Pytest** | `pytest -q` | **PASS** | `3 passed in 1.20s` |
| **Environment Check cục bộ** | python scripts/check_environment.py | **PASS cục bộ** | Đã chạy trên Python 3.13.12; chưa thay thế cho CI của dự án trên Python 3.11. Phải xác nhận lại khi mở PR vào develop. |
| **Git Diff Check** | `git diff --check` | **PASS** | Không có lỗi khoảng trắng (whitespace errors) hay conflict markers |
| **Git Status** | `git status` | **CLEAN** | Nhánh `dev/huy` sạch, chỉ sẵn sàng commit các file tài liệu theo đúng phạm vi tuần 1 |

---

## 7. Khó khăn, Rủi ro và Vướng mắc kỹ thuật

1. **Rủi ro suy hao biên độ ECG tại cổ tay:** Việc đo ECG đạo trình I qua cổ tay và ngón tay đối diện có biên độ nhỏ ($< 100\mu\text{V}$) và rất dễ bị ảnh hưởng bởi nhiễu cử động. Cần phối hợp chặt chẽ với Đức Anh trong thiết kế phần cứng khuếch đại vi sai (INA) và điện cực tiếp xúc.
2. **Hiện tượng trôi thời gian tiền tống máu ($\text{PEP}$ drift):** Khi đo lặp lại giữa các ngày, sự thay đổi tâm lý hoặc nhiệt độ phòng có thể làm biến đổi PEP, làm suy giảm mối liên hệ giữa PAT và huyết áp. Cần bù trừ bằng các đặc trưng hình thái PPG và tần số tim (HR).
3. **Cân đối giữa tỷ lệ từ chối (Rejection rate) và tính sẵn sàng của thiết bị:** Nếu đặt ngưỡng SQI và độ bất định quá khắt khe, số lượng kết quả đo bị hủy sẽ quá lớn, làm giảm trải nghiệm người dùng.

---

## 8. Các vấn đề cần nhóm và giảng viên xác nhận

> [!IMPORTANT]
> **Checklist lấy ý kiến thống nhất:**
> 1. [ ] **Giảng viên:** Quy trình và thủ tục xin phê duyệt đạo đức y sinh tại trường/khoa; yêu cầu về cỡ mẫu tối thiểu cho bài báo khoa học mục tiêu.
> 2. [ ] **Nhóm:** Chốt chính thức bản v0.1 của RQ1–RQ3 và khung protocol làm căn cứ triển khai cho các tuần tiếp theo.
> 3. [ ] **Đức Anh & Linh:** Xác nhận định dạng dữ liệu truyền thông (data packet) từ thiết bị về máy tính đảm bảo chứa timestamp phần cứng vi giây để tính PAT chính xác.

---

## 9. Kế hoạch chuyển giao sang Tuần 2

1. Thảo luận và nghiệm thu chéo các sản phẩm Tuần 1 của Linh (repository/CI) và Đức Anh (BOM/phần cứng).
2. Xây dựng tài liệu chi tiết về thuật toán xử lý tín hiệu ECG/PPG và trích xuất đặc trưng:
   - Thuật toán Pan-Tompkins thích nghi cho đỉnh R của ECG.
   - Thuật toán đạo hàm bậc hai và tiếp tuyến giao cắt phát hiện chân sóng foot của PPG.
   - Tính toán đại lượng PAT trên dữ liệu mẫu `data/sample/`.
3. Chuẩn bị biểu mẫu phiếu đồng thuận (Informed Consent Form template) chi tiết cho hồ sơ đạo đức.
4. Phối hợp với Đức Anh để kiểm tra các phương án điện cực ECG thử nghiệm trên bo mạch thử nghiệm (breadboard).
