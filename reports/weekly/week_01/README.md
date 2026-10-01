# Báo cáo tiến độ Tuần 1

> **Giai đoạn:** Tuần 1 / 28 tuần
> **Người tổng hợp:** Nguyễn Đức Huy
> **Vai trò:** Xử lý tín hiệu, PAT, phương pháp thống kê, protocol, tổng quan y văn và điều phối báo cáo
> **Ngày báo cáo:** 2026-09-22
> **Ngày rà soát tài liệu:** 2026-10-01. Báo cáo giữ mốc lịch sử Tuần 1; các bản thảo chưa đồng nghĩa đã được nghiệm thu hoặc phê duyệt.

---

## 1. Mục tiêu tuần 1

Theo kế hoạch tuần tại [docs/plans/WEEK_01.md](../../../docs/plans/WEEK_01.md), các mục tiêu trọng tâm gồm (giữ mốc báo cáo lịch sử):
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

Huy đã có các bản thảo đầu ra Tuần 1 dưới đây. Dấu tích chỉ xác nhận có bản thảo hoặc ghi nhận kiểm tra lịch sử, không xác nhận review/phê duyệt. Task tạo Issue chưa có số Issue hoặc bằng chứng liên kết trong báo cáo này.

- [x] **Ma trận tổng quan 12 bài báo khoa học (A):** Đã xác minh DOI và tiêu đề của 12 công trình; đã hiệu chỉnh các sai lệch số liệu được phát hiện. Đây là structured rapid review, chưa phải systematic review. Mọi con số dùng trong bản thảo bài báo phải có trích dẫn tới đúng bảng/hình/trang của nguồn gốc.
- [x] **Bộ câu hỏi nghiên cứu RQ1–RQ3 (B):** Xây dựng chi tiết 3 câu hỏi nghiên cứu trung tâm bản v0.1 kèm đầy đủ giả thuyết $H_0/H_1$, biến đầu vào/đầu ra, hệ thống baseline đối chứng (Zero-change, PPG-only, PAT linear, ECG+PPG fusion), chỉ số đánh giá riêng biệt cho SBP và DBP, điều kiện kiểm định thống kê và phân tích rủi ro phương pháp luận.
- [x] **Khung protocol nghiên cứu thực nghiệm v0.1 (C):** Thiết lập quy trình đo đối chứng đồng bộ ECG+PPG tại cổ tay với máy đo cuff bắp tay, quy tắc ghép cửa sổ tín hiệu (chỉ lấy cửa sổ trước khi bơm cuff), định nghĩa nghiêm ngặt một mẫu độc lập (1 lần đo cuff = 1 nhãn), chiến lược chia dữ liệu Subject-wise và Cross-session, và kế hoạch thống kê Bootstrap theo đối tượng.
- [x] **Khung đạo đức v0.1 (D):** Có bản thảo quyền lợi, đồng thuận, tiêu chí dừng và giả danh hóa bằng `subject_id`; còn chờ đối chiếu chính sách dữ liệu và phê duyệt. **Không sạc thiết bị khi đang đeo**.
- [x] **Agenda khởi động (E):** Có dự thảo phân công, quy trình và câu hỏi giảng viên; chưa chứng minh cuộc họp đã diễn ra hoặc quyết định đã được khóa.
- [x] **Kiểm tra kỹ thuật tự động:** Báo cáo gốc ghi nhận kết quả kiểm tra cục bộ tại mục 6; đây không phải bằng chứng nghiệm thu nội dung khoa học hoặc CI hiện tại.

---

## 4. Danh mục sản phẩm đầu ra và Đường dẫn

| STT | Tên sản phẩm | Đường dẫn tương đối | Trạng thái |
|---|---|---|---|
| 1 | Ma trận 12 bài | [Literature matrix](../../../docs/literature/week_01_literature_matrix.md) | Có bản thảo; audit toàn văn chưa hoàn tất |
| 2 | RQ1–RQ3 | [Câu hỏi nghiên cứu](../../../docs/research_questions_v0.1.md) | Có bản thảo, chờ review/phê duyệt |
| 3 | Protocol | [Protocol outline](../../../docs/protocol/protocol_outline_v0.1.md) | Có outline, chưa duyệt |
| 4 | Ethics | [Ethics outline](../../../docs/ethics/ethics_outline_v0.1.md) | Có outline, chưa duyệt |
| 5 | Agenda khởi động | [Kickoff](../../../docs/meetings/week_01_kickoff.md) | Có agenda; chưa có biên bản xác nhận |
| 6 | Báo cáo tiến độ tuần 1 | [reports/weekly/week_01/README.md](README.md) | Đã cập nhật đầy đủ |

---

## 5. Tóm tắt các nội dung chuyên môn chính

### 5.1. Tóm tắt ma trận 12 bài báo khoa học

Tóm tắt sơ bộ từ literature matrix; các số liệu và diễn giải dưới đây cần đối chiếu toàn văn trước khi dùng trong bài báo, không phải kết luận của dự án.

1. **Mukkamala et al. (2015, IEEE TBME):** Tổng quan cơ sở PTT/PAT và vai trò PEP. Công thức $\text{PAT} = \text{PEP} + \text{PTT}$ là cách viết gọn; cần khai báo mốc ECG, không đồng nhất Q/QRS với R peak.
2. **Zhang et al. (2011, J Appl Physiol):** Theo tóm tắt ma trận, thực nghiệm can thiệp thuốc trên động vật báo cáo RMSE PAT $10.4\text{ mmHg}$ và PTT $4.8\text{ mmHg}$. Các số cần đối chiếu nguồn; không suy rộng thành hiệu năng trên người hoặc prototype.
3. **Payne et al. (2006, J Appl Physiol):** Khảo sát trên người về ảnh hưởng của thành phần trước tống máu tới quan hệ PAT–huyết áp.
4. **Yoshizawa et al. (2023, IEEE Sensors J):** Khảo sát nguy cơ rò rỉ khi chia dữ liệu tín hiệu; cần đối chiếu thiết kế split trong nguồn. Subject-wise là quy tắc dự án, không diễn giải bài này là tiêu chuẩn bắt buộc cho mọi nghiên cứu.
5. **Kachuee et al. (2017, IEEE TBME):** Khai thác 21 đặc trưng hình thái PPG kết hợp PAT và các thuật toán học máy cổ điển (Ridge Regression, Random Forest) có hiệu chuẩn cá nhân.
6. **Esmaili et al. (2017, IEEE TIM):** Đánh giá các mô hình hiệu chuẩn cá nhân hóa phi tuyến tính trên người khỏe mạnh, so sánh sai số khi có và không có bù trừ PEP.
7. **Ding et al. (2016, IEEE TBME):** Bổ sung tỷ số cường độ quang học PPG (PIR) nhằm phản ánh sự thay đổi đường kính mạch máu, giúp cải thiện độ ổn định khi theo dõi huyết áp liên tục.
8. **Zhang Q. et al. (2017, BioMed Eng OnLine):** Nghiên cứu hệ thống một bên tay (single-arm ECG+PPG) trích xuất PAT tại cổ tay/cẳng tay; chưa phải bằng chứng cho cấu hình prototype của nhóm.
9. **Vybornova et al. (2021, Blood Press Monit):** Theo ma trận, nghiên cứu 1 tháng về Aktiia có đánh giá theo ISO 81060-2; cần audit protocol/kết quả nguồn. Không suy rộng thành chứng nhận prototype hoặc mọi điều kiện theo dõi dài hạn.
10. **Elgendi (2016, Bioengineering):** Khảo sát chỉ số chất lượng PPG ($s\text{SQI}$, $q\text{SQI}$); ngưỡng dự án vẫn cần kiểm tra và review.
11. **Shen et al. (2024, Biomed Signal Process Control):** Đề xuất cơ chế định lượng độ bất định (Evidential Deep Learning) để từ chối các mẫu dự đoán không tin cậy trong ước lượng huyết áp không cuff.
12. **Wang et al. (2023, Front Digit Health - PulseDB):** Bộ dữ liệu gồm 5,245,454 đoạn 10 giây từ 5,361 người; cung cấp các tập calibration-based, calibration-free và AAMI test để benchmark có thể tái lập.

### 5.2. Tóm tắt bộ câu hỏi nghiên cứu RQ1–RQ3
- **RQ1:** Đánh giá giá trị gia tăng của việc kết hợp ECG và PAT so với mô hình chỉ dùng PPG sau khi đã hiệu chuẩn cá nhân, trên các phiên đo tương lai. Baseline bắt buộc gồm: Zero-change, PPG-only, PAT linear và ECG+PPG fusion.
- **RQ2:** Đánh giá chênh lệch hiệu năng giữa random window-wise có nguy cơ rò rỉ, subject-wise và temporal cross-session; không giả định trước hướng hoặc mức chênh lệch. Random window-wise chỉ là đối chứng minh họa nguy cơ rò rỉ, không dùng để chọn model hoặc báo cáo hiệu năng chính.
- **RQ3:** Đánh giá hiệu quả của cơ chế từ chối dự đoán (rejection mechanism) hai tầng (SQI tín hiệu đầu vào + độ bất định mô hình đầu ra) trong việc giảm thiểu sai số trên tập mẫu được chấp nhận.

### 5.3. Tóm tắt Khung Protocol và Khung Đạo đức
- **Protocol v0.1:** Đề xuất đo lặp lại nhiều phiên trên 15–20 người; cỡ mẫu và bố trí còn chờ duyệt. Lưu 60 giây trước cuff; cửa sổ chính dự kiến 20–30 giây, các ứng viên phân tích độ nhạy là 10/20/30/60 giây, chưa khóa. Một lần cuff hợp lệ tạo tối đa một cặp nhãn độc lập; bootstrap theo người.
- **Ethics v0.1:** Bản thảo phi y tế, đề xuất quy trình đồng thuận và quyền rút lui. Dùng `subject_id` để giả danh hóa; khi còn bảng liên kết danh tính thì không coi dữ liệu là ẩn danh không thể truy ngược. **Không sạc thiết bị khi đang đeo**; chưa được thu dữ liệu người trước phê duyệt cần thiết.

---

## 6. Kết quả kiểm tra kỹ thuật (Verification Results)

Bảng dưới là kết quả được ghi trong báo cáo ngày 2026-09-22, không phải kết quả chạy lại ngày rà soát. Chưa có log/CI gắn commit trong bảng; smoke test không kiểm chứng nội dung khoa học.

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
