# Biên bản / Chương trình Họp Khởi động Tuần 1 (Kickoff Meeting Draft & Agenda)

> **Loại tài liệu:** Biên bản / Chương trình nghị sự dự thảo (Draft Agenda & Minutes)
> **Người khởi tạo:** Nguyễn Đức Huy
> **Ngày lập:** 2026-09-22
> **Trạng thái:** Bản dự thảo nội dung khởi động dự án *(Đánh dấu các phần cần nhóm xác nhận tại buổi họp chính thức)*

---

## 1. Thông tin buổi họp

- **Thời gian dự kiến:** Tuần 1 (Thời gian chi tiết: *[CẦN NHÓM XÁC NHẬN]*).
- **Địa điểm:** Phòng thí nghiệm / Trực tuyến (*[CẦN NHÓM XÁC NHẬN]*).
- **Thành viên tham dự:**
  - **Linh:** Phụ trách phần mềm, pipeline dữ liệu, mô hình hóa, kiểm thử tự động và CI.
  - **Đức Anh:** Phụ trách phần cứng, firmware nhúng, BOM, thiết kế mạch PCB và kiểm thử thiết bị.
  - **Huy:** Phụ trách xử lý tín hiệu, nghiên cứu PAT, phương pháp thống kê, xây dựng protocol, đạo đức nghiên cứu, tổng quan y văn và điều phối báo cáo/bài báo.

---

## 2. Mục tiêu buổi họp

1. Thống nhất vai trò, trách nhiệm và phạm vi phân công công việc trong toàn bộ lộ trình 28 tuần.
2. Thống nhất câu hỏi nghiên cứu trung tâm của dự án và các tiêu chuẩn phương pháp luận.
3. Rà soát danh mục sản phẩm bàn giao bắt buộc của Tuần 1 theo kế hoạch `docs/plans/WEEK_01.md`.
4. Khóa quy trình làm việc Git, review chéo và chính sách bảo mật dữ liệu.
5. Tổng hợp các vấn đề học thuật và kỹ thuật cần tham vấn ý kiến giảng viên hướng dẫn.

---

## 3. Câu hỏi nghiên cứu trung tâm của dự án

Nhóm làm rõ định hướng khoa học chủ đạo:
> **Câu hỏi nghiên cứu trung tâm:**
> *"Sau khi hiệu chuẩn cá nhân ban đầu, việc bổ sung tín hiệu ECG và đại lượng PAT có cải thiện khả năng ước lượng biến thiên huyết áp ($\Delta\text{SBP}$ và $\Delta\text{DBP}$) ở các phiên đo tương lai so với việc chỉ sử dụng đặc trưng hình thái từ tín hiệu PPG hay không?"*

**Lưu ý phương pháp luận đã khóa:**
- Tín hiệu đo tại cổ tay từ đỉnh R của ECG đến chân sóng PPG là **PAT (Pulse Arrival Time)**, bao gồm cả thời gian tiền tống máu ($\text{PEP}$). $\text{PAT} = \text{PEP} + \text{PTT}$. Tuyệt đối không gọi nhầm là PTT thực sự.
- Phân tích và báo cáo kết quả tách biệt hoàn toàn giữa SBP và DBP.
- Không tuyên bố thiết bị đạt chuẩn y tế thay thế máy đo thương mại; mục tiêu đề tài là nguyên mẫu nghiên cứu kỹ thuật y sinh.

---

## 4. Rà soát sản phẩm Tuần 1 (Theo docs/plans/WEEK_01.md)

| Thành viên | Nhiệm vụ tuần 1 | Sản phẩm đầu ra | Trạng thái ghi nhận |
|---|---|---|---|
| **Linh** | Chuẩn hóa repository, môi trường Python, thiết lập CI, quy ước dữ liệu và tên file | Repository cấu trúc chuẩn, CI passing, tài liệu quy ước | *[CẦN LINH XÁC NHẬN BẰNG CHỨNG TRONG REPO]* |
| **Đức Anh** | Chốt yêu cầu phần cứng, lập BOM v0.1, đề xuất $\ge 2$ phương án điện cực ECG, danh sách linh kiện | BOM v0.1, sơ đồ khối phần cứng, tài liệu phương án điện cực | *[CẦN ĐỨC ANH XÁC NHẬN BẰNG CHỨNG TRONG REPO]* |
| **Huy** | Lập ma trận 10–12 bài báo, chốt bản thảo RQ1–RQ3, khung protocol v0.1, khung hồ sơ đạo đức v0.1, biên bản họp và báo cáo tuần | `week_01_literature_matrix.md`, `research_questions_v0.1.md`, `protocol_outline_v0.1.md`, `ethics_outline_v0.1.md`, `week_01_kickoff.md`, `reports/weekly/week_01/README.md` | Đã hoàn thành bản thảo v0.1, chờ nhóm review |

---

## 5. Quy trình làm việc kỹ thuật và Quy định phối hợp

### 5.1. Luồng nhánh Git (Branching Model)
- **Luồng chuẩn:**
  $$\text{dev/thanh-vien} \longrightarrow \text{Pull Request} \longrightarrow \text{develop} \longrightarrow \text{main (mốc ổn định)}$$
  - Nhánh làm việc cá nhân: `dev/linh`, `dev/ducanh`, `dev/huy`.
  - Nhánh tích hợp: `develop`.
  - Nhánh ổn định (chỉ merge khi có mốc nghiệm thu/báo cáo): `main`.
- **Nguyên tắc:**
  - Không ai được commit trực tiếp lên `main` hoặc `develop`.
  - Không tự ý merge Pull Request của chính mình.
  - Không dùng force push (`git push -f`) hoặc reset cứng (`git reset --hard`) trên các nhánh dùng chung.

### 5.2. Quy định Review chéo (Cross-Review Policy)
- Mọi Pull Request muốn merge vào `develop` bắt buộc phải:
  1. Được ít nhất một thành viên khác review và phê duyệt (Approve).
  2. Toàn bộ các bước kiểm tra tự động của GitHub Actions CI hiển thị màu xanh (pass Ruff, Pytest, Check environment).
  3. Không có xung đột (merge conflicts).
- Review chéo theo ranh giới kỹ thuật:
  - Phần cứng/Firmware $\leftrightarrow$ Xử lý tín hiệu: Đức Anh và Huy review chéo về tần số lấy mẫu, định dạng dữ liệu và giao diện điện cực.
  - Phần mềm/Pipeline $\leftrightarrow$ Xử lý tín hiệu: Linh và Huy review chéo về thuật toán lọc sóng, trích xuất đặc trưng và cấu trúc train/val/test split.

### 5.3. Quy định dữ liệu và bảo mật (Data & Privacy Rules)
- Tuân thủ tuyệt đối [docs/DATA_POLICY.md](file:///D:/ppg-ecg-blood-pressure/docs/DATA_POLICY.md):
  - Không commit dữ liệu người tham gia thật, dữ liệu thô dung lượng lớn.
  - Không đưa token, mật khẩu, khóa API hoặc file `.env` lên Git.
  - Mọi dữ liệu thử nghiệm phải sử dụng định danh `subject_id`, `session_id`, `event_id`. Không dùng tên hay mã sinh viên.
  - Chỉ dữ liệu mẫu nhỏ vô danh tính mới được phép đặt trong `data/sample/`.

---

## 6. Các quyết định kỹ thuật đã khóa (Locked Decisions)

1. **Quyết định 1 (Ngôn ngữ và Môi trường):** Python 3.11/3.13 làm môi trường phân tích dữ liệu chuẩn; quản lý phụ thuộc bằng `requirements.txt` và `environment.yml`. Bộ kiểm tra code gồm `ruff` và `pytest`.
2. **Quyết định 2 (Cấu trúc thư mục):** Tổ chức theo chức năng kỹ thuật (`hardware/`, `firmware/`, `software/`, `docs/`, `reports/`), tuyệt đối không tạo thư mục cá nhân theo tên người.
3. **Quyết định 3 (Đại lượng mục tiêu):** Dự đoán biến thiên huyết áp $\Delta\text{SBP}$ và $\Delta\text{DBP}$ sau hiệu chuẩn cá nhân, không theo đuổi bài toán dự đoán tuyệt đối không hiệu chuẩn ("calibration-free") do không khả thi về mặt sinh lý học trên thiết bị một vị trí đeo.
4. **Quyết định 4 (Nguyên tắc dữ liệu tuần 1):** Tuần 1 tuyệt đối không tuyển người hay thu dữ liệu thật.

---

## 7. Các vấn đề cần xin ý kiến giảng viên hướng dẫn

> [!NOTE]
> **Danh sách câu hỏi cần giảng viên giải đáp/định hướng:**
> 1. *Thủ tục phê duyệt đạo đức:* Quy trình đăng ký và thời gian xét duyệt hồ sơ đạo đức nghiên cứu tại trường/khoa mất bao lâu? Có cần liên kết với cơ sở y tế để hỗ trợ đo đối chứng hay không?
> 2. *Thiết bị đo đối chứng chuẩn:* Giảng viên có yêu cầu cụ thể về dòng máy đo huyết áp chuẩn lâm sàng (ví dụ dòng Omron hay máy đo vỗ kế liên tục nếu có sẵn tại phòng thí nghiệm) hay không?
> 3. *Tiêu chí công bố bài báo:* Mục tiêu bài báo hướng tới hội nghị quốc tế (ví dụ IEEE EMBC/BHI) hay tạp chí chuyên ngành? Yêu cầu về số lượng đối tượng tối thiểu cho bài báo là bao nhiêu?
> 4. *Tài chính và linh kiện:* Hạn mức ngân sách cho việc đặt mua linh kiện điện tử, cảm biến và gia công PCB của Đức Anh trong Tuần 2/Tuần 3.

---

## 8. Kế hoạch và Checklist cho buổi họp tiếp theo (Tuần 2)

- [ ] Linh demo pipeline nạp dữ liệu mẫu và chạy thử nghiệm các baseline mẫu.
- [ ] Đức Anh trình bày bản vẽ sơ đồ nguyên lý mạch sơ bộ (Schematic v0.1) và kết quả thử nghiệm cảm biến trên breadboard.
- [ ] Huy trình bày chi tiết thuật toán phát hiện đỉnh R của ECG và chân sóng PPG trên dữ liệu mẫu để tính PAT.
- [ ] Rà soát phản hồi của giảng viên về hồ sơ đạo đức và câu hỏi nghiên cứu.
