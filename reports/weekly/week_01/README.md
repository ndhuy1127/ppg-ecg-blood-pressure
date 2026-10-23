# Báo cáo tiến độ Tuần 1

> **Giai đoạn:** Tuần 1 / 28 tuần (2026-09-17 → 2026-09-23)
>
> **Thành viên:** Linh, Trương Đức Anh, Nguyễn Đức Huy

## 1. Tóm tắt công việc của tuần (mục tiêu)

Theo [kế hoạch Tuần 1](../../../docs/plans/WEEK_01.md), tuần đầu dựng nền cho cả
ba mảng:

1. Chuẩn hóa repository, môi trường Python, CI và quy ước dữ liệu.
2. Xác định yêu cầu phần cứng, lập BOM v0.1, sơ đồ khối và các phương án điện cực ECG.
3. Lập ma trận 10–12 bài báo, câu hỏi nghiên cứu RQ1–RQ3, khung protocol và khung
   đạo đức v0.1.

## 2. Thành viên phụ trách và phân công công việc

| Thành viên | Vai trò | Công việc Tuần 1 |
| --- | --- | --- |
| Linh | Phần mềm, pipeline dữ liệu, CI | Chuẩn hóa repo, tạo môi trường Python, thiết lập CI, viết quy ước dữ liệu và tên file |
| Đức Anh | Phần cứng, firmware, BOM | Yêu cầu phần cứng V0, BOM v0.1, sơ đồ khối, hai phương án điện cực ECG, danh sách linh kiện thay thế |
| Huy | Xử lý tín hiệu, thống kê, protocol, tài liệu | Ma trận 12 bài báo, RQ1–RQ3, khung protocol, khung đạo đức, agenda khởi động, tổng hợp báo cáo |

## 3. Tóm tắt công việc đã hoàn thành của từng người

### Linh

- Khởi tạo môi trường `venv`, `requirements.txt`, `environment.yml`, `pyproject.toml`;
  bổ sung dependency còn thiếu (scikit-learn, PyYAML).
- Cập nhật workflow CI (`.github/workflows/ci.yml`), xóa conflict marker còn sót.
- Viết quy ước dữ liệu, tên file và ước lượng dung lượng.
- Thêm test khởi tạo môi trường.

### Đức Anh

- Viết yêu cầu phần cứng V0: V0 là prototype dùng board rời và module/breakout để
  kiểm chứng tín hiệu, chưa phải thiết bị đeo hoàn chỉnh.
- Chốt MCU prototype ESP32-S3-DevKitC-1 N16R8, ECG AFE MAX30001 (breakout
  ProtoCentral, SPI).
- Lập BOM V0.1 theo khối chức năng (MCU, ECG AFE, PPG, IMU, điện cực, giao tiếp PC).
- Vẽ sơ đồ khối phần cứng.
- Viết tài liệu hai phương án điện cực ECG: Ag/AgCl có gel và điện cực khô.

### Huy

- Ma trận tổng quan 12 bài báo: xác minh DOI/tiêu đề, trích phương pháp, đánh dấu
  số liệu cần đối chiếu toàn văn.
- Bộ câu hỏi nghiên cứu RQ1–RQ3 v0.1 với giả thuyết H0/H1, biến vào/ra, baseline
  đối chứng và chỉ số đánh giá riêng SBP/DBP.
- Khung protocol v0.1: quy trình đo đồng bộ ECG+PPG cổ tay với cuff bắp tay, quy
  tắc ghép cửa sổ, định nghĩa mẫu độc lập, chia dữ liệu theo người và bootstrap.
- Khung đạo đức v0.1: quyền lợi, đồng thuận, tiêu chí dừng, giả danh hóa bằng
  `subject_id`, không sạc thiết bị khi đang đeo.
- Agenda họp khởi động nhóm.

## 4. Danh mục sản phẩm đầu ra và đường dẫn

| STT | Sản phẩm | Người làm | Đường dẫn |
| --- | --- | --- | --- |
| 1 | Workflow CI | Linh | [.github/workflows/ci.yml](../../../.github/workflows/ci.yml) |
| 2 | Môi trường Python | Linh | [requirements.txt](../../../requirements.txt), [environment.yml](../../../environment.yml), [pyproject.toml](../../../pyproject.toml) |
| 3 | Quy ước dữ liệu và tên file | Linh | [quy_uoc_du_lieu.md](../../../docs/quy_uoc_du_lieu.md), [data_convention.md](../../../docs/data_convention.md) |
| 4 | Yêu cầu phần cứng V0 | Đức Anh | [hardware_requirements_for_V0.md](../../../configs/hardware/hardware_requirements_for_V0.md) |
| 5 | Sơ đồ khối phần cứng | Đức Anh | [Hardware_Diagram.png](../../../configs/hardware/Hardware_Diagram.png); bản hiện hành: [hardware_diagram_v1.svg](../../../configs/hardware/hardware_diagram_v1.svg) |
| 6 | BOM V0.1 | Đức Anh | [BOM_V0.1.xlsx](../../../hardware/bom/BOM_V0.1.xlsx) |
| 7 | Hai phương án điện cực ECG | Đức Anh | [Hai_phuong_an_dien_cuc_ECG.pdf](../../../hardware/Hai_phuong_an_dien_cuc_ECG.pdf) |
| 8 | Ma trận 12 bài báo | Huy | [week_01_literature_matrix.md](../../../docs/literature/week_01_literature_matrix.md) |
| 9 | Câu hỏi nghiên cứu RQ1–RQ3 | Huy | [research_questions_v0.1.md](../../../docs/research_questions_v0.1.md) |
| 10 | Khung protocol v0.1 | Huy | [protocol_outline_v0.1.md](../../../docs/protocol/protocol_outline_v0.1.md) |
| 11 | Khung đạo đức v0.1 | Huy | [ethics_outline_v0.1.md](../../../docs/ethics/ethics_outline_v0.1.md) |
| 12 | Agenda khởi động | Huy | [week_01_kickoff.md](../../../docs/meetings/week_01_kickoff.md) |

## 5. Tóm tắt các nội dung chuyên môn chính

### 5.1. Kiến trúc phần cứng V0 (Đức Anh)

- Luồng ECG: điện cực → MAX30001 → SPI → ESP32-S3 → USB → laptop. ECG lấy mẫu
  512 Hz (chu kỳ 1,953125 ms).
- Luồng PPG: cảm biến PPG → I²C → ESP32-S3 → USB → laptop. PPG AFE và tần số lấy
  mẫu PPG để mở ở tuần này.
- ECG và PPG có thể khác tần số lấy mẫu, nên đồng bộ theo timestamp chứ không theo
  chỉ số mẫu.
- Điện cực: Ag/AgCl có gel tiếp xúc tốt, phù hợp kiểm chứng tín hiệu ban đầu; điện
  cực khô hợp với hướng thiết bị đeo nhưng nhạy chuyển động và lực ép.

### 5.2. Tổng quan tài liệu (Huy)

Mười hai công trình trong ma trận, gồm:

1. **Mukkamala et al. (2015, IEEE TBME):** cơ sở PTT/PAT và vai trò PEP;
   PAT = PEP + PTT là cách viết gọn, cần khai báo mốc ECG.
2. **Zhang et al. (2011, J Appl Physiol):** trên 6 con chó, với MBP mô hình theo
   1/PAT có RMSE 10,4 mmHg so với 4,8 mmHg của 1/PTT (abstract).
3. **Payne et al. (2006, J Appl Physiol):** 12 nam khỏe mạnh; PEP chiếm 12–35%
   khoảng R → xung ngón tay.
4. **Yoshizawa et al. (2023, IEEE Sensors J):** nguy cơ rò rỉ khi chia dữ liệu tín hiệu.
5. **Kachuee et al. (2017, IEEE TBME):** PAT kết hợp hình thái PPG trên khoảng
   1.000 bản ghi MIMIC-II.
6. **Esmaili et al. (2017, IEEE TIM):** 32 người; so sánh PTT từ PCG với PAT từ ECG
   ở ba mốc PPG.
7. **Ding et al. (2016, IEEE TBME):** bổ sung tỷ số cường độ PPG (PIR).
8. **Zhang Q. et al. (2017, BioMed Eng OnLine):** ECG và PPG cùng một cánh tay,
   10 người, chỉ SBP.
9. **Vybornova et al. (2021, Blood Press Monit):** 86 người, theo dõi 1 tháng vòng
   Aktiia (chỉ PPG).
10. **Elgendi (2016, Bioengineering):** so sánh 8 SQI cho PPG; skewness tốt nhất.
11. **Shen et al. (2024, BSPC):** định lượng độ bất định cho BP cuffless (PEEL),
    96 người MIMIC-III.
12. **Wang et al. (2023, Front Digit Health — PulseDB):** 5.245.454 đoạn 10 giây
    từ 5.361 người, năm tập con để benchmark.

### 5.3. Câu hỏi nghiên cứu (Huy)

- **RQ1:** giá trị gia tăng của ECG + PAT so với chỉ PPG sau hiệu chuẩn cá nhân,
  trên phiên đo tương lai. Baseline: Zero-change, PPG-only, PAT linear, ECG+PPG fusion.
- **RQ2:** chênh lệch hiệu năng giữa chia random window-wise (minh họa rò rỉ),
  subject-wise và temporal cross-session.
- **RQ3:** hiệu quả của cơ chế từ chối dự đoán hai tầng (SQI đầu vào + độ bất định
  đầu ra) trong việc giảm sai số trên tập mẫu được chấp nhận.

### 5.4. Protocol và đạo đức (Huy)

- Protocol v0.1: đo lặp nhiều phiên trên 15–20 người; lưu 60 giây trước cuff; cửa
  sổ ứng viên 10/20/30/60 giây; một lần cuff hợp lệ tạo tối đa một cặp nhãn độc
  lập; bootstrap theo người.
- Đạo đức v0.1: đồng thuận và quyền rút lui; giả danh hóa bằng `subject_id`; không
  sạc thiết bị khi đang đeo; không thu dữ liệu người trước khi có phê duyệt.

## 6. Kết quả kiểm tra kỹ thuật

Kiểm tra cục bộ ngày 2026-09-22 trên nhánh `dev/huy`:

| Kiểm tra | Lệnh | Kết quả |
| --- | --- | --- |
| Ruff | `ruff check .` | Đạt, 0 lỗi |
| Pytest | `pytest -q` | `3 passed in 1.20s` |
| Kiểm tra môi trường | `python scripts/check_environment.py` | Đạt (Python 3.13.12) |
| Khoảng trắng/conflict | `git diff --check` | Đạt |

Phần cứng (Đức Anh): yêu cầu V0, BOM V0.1, sơ đồ khối và phương án điện cực có đủ
các khối chính; ECG 512 SPS đã xác định; tài liệu được commit trên `dev/ducanh`
(`aa64df9`, `2c904dd`, `54712b8`, `0a4a5b6`).
