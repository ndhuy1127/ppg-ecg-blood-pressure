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
| Thiết bị prototype (V1-module) | 512 sps (MAX30001, chốt 2026-10-23) | 200 sps mỗi khe, MAX30101 ba khe xanh/đỏ/IR, `SMP_AVE = 1` (chốt 2026-10-24) | Giá trị danh định; tốc độ thực phải đo. Lý do và độ rộng xung PPG còn mở: [interface_power_sampling_v0.md, mục 4 và 6](../configs/hardware/interface_power_sampling_v0.md) |

Không giả định hai kênh dùng chung một tần số lấy mẫu hay một clock.

## 3. Ước lượng dung lượng

Ước lượng để lập kế hoạch lưu trữ, không phải số đo:

- Giả định (cập nhật 2026-10-25): raw là luồng packet nhị phân `raw.bin` của logger
  ([packet schema V0.1](../configs/hardware/Packet_Schema_V0.1.md) và V0.2), mỗi packet
  42 byte header/CRC cộng 4 byte mỗi mẫu; số mẫu mỗi packet như firmware V1 hiện dùng:
  ECG 512 sps, 16 mẫu (106 B); PPG 3 khe × 200 sps, 8 mẫu (74 B); IMU 6 trục × 100 Hz,
  10 mẫu (82 B); nhiệt độ 1 Hz; `0xD1`/`0xD2` mỗi 10 s.
- Kết quả: khoảng 3,4 + 5,6 + 4,9 kB/s ≈ 14 kB/s, tức khoảng 0,84 MB mỗi phút hay
  50 MB mỗi giờ `raw.bin`. `packets.csv` và `samples.csv` logger sinh ra lớn hơn
  vài lần; chúng sinh lại được từ raw.

Tính lại khi đổi số mẫu mỗi packet hay tốc độ lấy mẫu.
