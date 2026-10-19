# Quy ước dữ liệu và ước lượng dung lượng

Quy ước dữ liệu chính thức (thư mục, ID, tên file, đơn vị, tần số lấy mẫu, truy
xuất nguồn gốc) là [quy_uoc_du_lieu.md](quy_uoc_du_lieu.md). File này chỉ giữ
quy tắc đặt tên ngắn gọn và ước lượng dung lượng lưu trữ; nếu hai file mâu
thuẫn, `quy_uoc_du_lieu.md` được ưu tiên.

## 1. Quy tắc đặt tên

- Phần không phải ID dùng chữ thường và snake_case (ví dụ `ecg_raw_2026.csv`).
- File dữ liệu nghiên cứu theo mẫu
  `<subject_id>_<session_id>_<event_id>_<data_type>.<ext>` như định nghĩa trong
  `quy_uoc_du_lieu.md`. Phần ID giữ đúng định dạng ở đó (ví dụ
  `SUB001_S001_E01_raw.csv`).

## 2. Tần số lấy mẫu (trạng thái)

| Nguồn | ECG | PPG | Trạng thái |
| --- | --- | --- | --- |
| PulseDB Subset (công khai) | 125 Hz | 125 Hz | Suy ra từ shape: 1250 mẫu mỗi đoạn 10 giây; khớp với bài báo PulseDB, xem [provenance PulseDB](pulsedb_provenance.md), mục 6 |
| Thiết bị prototype | 500 hoặc 512 sps (MAX30001 cấu hình được cả hai) | Phụ thuộc linh kiện PPG, chế độ LED và lấy trung bình | **Chưa chốt**; bảng tốc độ và phương án dự kiến ở [interface_power_sampling_v0.md, mục 4](../configs/hardware/interface_power_sampling_v0.md), quyết định còn mở ở mục 6 của tài liệu đó |

Không giả định hai kênh dùng chung một tần số lấy mẫu hay một clock.

## 3. Ước lượng dung lượng

Ước lượng để lập kế hoạch lưu trữ, không phải số đo:

- Giả định: 500 mẫu/s, mỗi mẫu một dòng CSV, khoảng 48 byte mỗi dòng
  (timestamp, ECG, PPG, sequence, status dạng text).
- Kết quả: 500 × 60 × 48 byte ≈ 1,44 MB mỗi phút CSV raw.

Tính lại khi đã chốt tần số lấy mẫu của thiết bị và định dạng file của logger.
Packet nhị phân (xem [packet schema V0.1](../configs/hardware/Packet_Schema_V0.1.md))
nhỏ hơn vài lần.
