# Báo cáo tiến độ Tuần 2

> **Giai đoạn:** Tuần 2 / 28 tuần (2026-09-24 → 2026-09-30)
>
> **Thành viên:** Linh, Trương Đức Anh, Nguyễn Đức Huy

## 1. Tóm tắt công việc của tuần (mục tiêu)

Theo [kế hoạch Tuần 2](../../../docs/plans/WEEK_02.md), tuần này làm việc trên dữ
liệu công khai và thiết kế trên giấy (chưa có phần cứng PPG/ECG):

1. Xây và kiểm thử reader PulseDB; khảo sát ít nhất 1.000 đoạn ECG, PPG, ABP.
2. Chuẩn bị thiết kế phần cứng v0: BOM, pin map, packet schema, kế hoạch bring-up.
3. Định nghĩa mẫu, nhãn, cửa sổ; tổng hợp PAT/PTT/PEP/PWA và giới hạn diễn giải PAT.
4. Thống nhất giao diện dữ liệu logger → pipeline.

## 2. Thành viên phụ trách và phân công công việc

| Thành viên | Công việc Tuần 2 |
| --- | --- |
| Linh | Reader PulseDB (metadata, ECG/PPG/ABP, nhãn), validator, notebook EDA, test, provenance |
| Đức Anh | Cập nhật BOM V0.1 kèm pin map, packet schema V0.1, quy trình bring-up |
| Huy | Thuật ngữ PAT/PTT/PEP/PWA, đơn vị quan sát và nhãn, cửa sổ, quy tắc chống rò rỉ, schema metadata, phiếu kiểm tra tín hiệu, tổng hợp báo cáo |

## 3. Tóm tắt công việc đã hoàn thành của từng người

### Linh

- Viết `PulseDBReader` đọc file `.mat` PulseDB thành các đoạn có subject, nhân khẩu
  học, SBP/DBP và waveform ECG/PPG/ABP; thêm tùy chọn `limit` và cắt sớm để đọc nhanh.
- Thêm validator kiểm tra giới tính và schema kênh; module vẽ tín hiệu.
- Notebook EDA vẽ tín hiệu và thống kê trên 1.000 đoạn.
- Test reader (`tests/test_pulsedb.py`), sửa lỗi Ruff.
- Tài liệu nguồn gốc và quyền dùng PulseDB.

### Đức Anh

- Sửa BOM V0.1, bổ sung pin map vào BOM (`BOM_V0.1_with_PinMap.xlsx`).
- Viết packet schema V0.1: version, session/channel, `SEQ`, timestamp thời điểm
  lấy mẫu, `SAMPLE_COUNT`, Fs, `STATUS`; ECG 512 SPS.
- Viết quy trình bring-up phần cứng.

### Huy

- Tài liệu thuật ngữ: PAT là R peak ECG → PPG foot; PAT = PEP + PTT là cách viết
  gọn, không đo riêng hai thành phần; PWA và giới hạn diễn giải PAT.
- Định nghĩa người, phiên, lần cuff, quan sát BP, cửa sổ, nhịp và các khóa
  `subject_id`, `session_id`, `event_id`, `window_id`.
- Cửa sổ ứng viên 10/20/30/60 giây trước mốc bơm cuff `t0`.
- Quy tắc chống rò rỉ: chia theo người, hiệu chuẩn trước đánh giá, không tuning
  trên test, bootstrap theo người.
- Bảng schema nhãn/metadata đề xuất; phân biệt nguồn nhãn `public_abp`,
  `prototype_cuff`, `simulation`.
- Phiếu kiểm tra tín hiệu: timestamp, R peak, trôi nền, PPG foot, ghép nhịp.

## 4. Danh mục sản phẩm đầu ra và đường dẫn

| STT | Sản phẩm | Người làm | Đường dẫn |
| --- | --- | --- | --- |
| 1 | Reader PulseDB | Linh | [reader.py](../../../software/pulsedb/reader.py) |
| 2 | Validator, visualizer | Linh | [validator.py](../../../software/pulsedb/validator.py), [visualizer.py](../../../software/pulsedb/visualizer.py) |
| 3 | Test reader | Linh | [test_pulsedb.py](../../../tests/test_pulsedb.py) |
| 4 | Notebook EDA | Linh | [01_eda_and_visualization.ipynb](../../../notebooks/01_eda_and_visualization.ipynb) |
| 5 | Provenance PulseDB | Linh | [pulsedb_provenance.md](../../../docs/pulsedb_provenance.md) |
| 6 | Packet schema V0.1 | Đức Anh | [Packet_Schema_V0.1.md, bản Tuần 2](https://github.com/ndhuy1127/ppg-ecg-blood-pressure/blob/b8e8912a1cefc07a9ce3894760717158b2048e44/configs/hardware/Packet_Schema_V0.1.md) (commit `b8e8912`); bản hiện hành: [Packet_Schema_V0.1.md](../../../configs/hardware/Packet_Schema_V0.1.md) |
| 7 | BOM V0.1 kèm pin map | Đức Anh | [BOM_V0.1_with_PinMap.xlsx](https://github.com/ndhuy1127/ppg-ecg-blood-pressure/blob/5ff545a2179219f7329ff327e347515e6d1393d3/hardware/bom/BOM_V0.1_with_PinMap.xlsx) (nhánh `dev/ducanh`, commit `5ff545a`); bản hiện hành: [danh sách mua](../../../hardware/bom/purchase_list_v1_module.md), pin map [A.7](../../../configs/hardware/custom_board_proposal.md) |
| 8 | Quy trình bring-up | Đức Anh | [Quy trinh bring-up.docx](https://github.com/ndhuy1127/ppg-ecg-blood-pressure/blob/e13d6699b165ee7d16bcc91649db3815d30b983b/configs/hardware/Quy%20trinh%20bring-up.docx) (nhánh `dev/ducanh`, commit `e13d669`); bản hiện hành: [v1_bringup_procedure.md](../../../hardware/test_reports/v1_bringup_procedure.md) |
| 9 | Thuật ngữ, mẫu/nhãn, cửa sổ, schema, phiếu kiểm tra | Huy | [week_02_sample_label_glossary.md](../../../docs/protocol/week_02_sample_label_glossary.md) |

## 5. Tóm tắt các nội dung chuyên môn chính

### 5.1. Dữ liệu PulseDB (Linh)

- Mỗi đoạn PulseDB dài 10 giây, có ECG, PPG, ABP và nhãn SBP/DBP dẫn xuất từ ABP.
- Reader kiểm tra `subject_id`, kênh, đơn vị, tần số lấy mẫu; validator từ chối
  giới tính và kênh sai schema.
- ABP PulseDB là tham chiếu công khai, không phải nhãn cuff của prototype.

### 5.2. Packet schema và timestamp (Đức Anh)

- Timestamp phải là thời điểm lấy mẫu, không phải lúc đọc FIFO hay lúc gửi gói.
- Thời điểm mẫu thứ i trong gói: t_i = t_0 + i / Fs.
- `SEQ` phát hiện mất, trùng, đảo thứ tự ở mức gói; mất mẫu cần thêm
  `SAMPLE_COUNT`, timestamp và Fs.

### 5.3. Đơn vị quan sát và nhãn (Huy)

- Một lần cuff hợp lệ tạo tối đa một cặp nhãn SBP/DBP độc lập; các cửa sổ cùng
  `event_id` dùng chung nhãn và không thành nhiều quan sát độc lập.
- Cửa sổ lấy trước `t0`, ghi `window_start`/`window_end`.
- Chia theo `subject_id`; hiệu chuẩn có trước phần đánh giá theo thời gian.

## 6. Kết quả kiểm tra kỹ thuật

Kiểm tra cục bộ ngày 2026-10-01, workspace `ae67fb9`:

| Kiểm tra | Lệnh | Kết quả |
| --- | --- | --- |
| Ruff | `ruff check .` | Đạt, exit 0 |
| Pytest | `pytest -q` | `3 passed in 0.10s` |
| Kiểm tra môi trường | `python scripts/check_environment.py` | Đạt (Python 3.13.12) |
| Khoảng trắng/conflict | `git diff --check` | Đạt |
| Liên kết tài liệu | Kiểm tra liên kết tương đối, conflict marker, URL file cục bộ | Đạt trên 8 tệp sửa |

Phần reader PulseDB (Linh): test reader trong `tests/test_pulsedb.py` và notebook EDA
trên 1.000 đoạn, commit `6ad1954`, `d81c1e5`, `4c80e6e`, `e92a0d4`, `100ec92`.
