# Packet Logger — Kiểm thử RAM trên Mac

## Môi trường
- Nhánh: dev/ngoclinh
- Commit nền: 61fd4af
- Nguồn dữ liệu: SYNTHETIC
- Phương pháp: record từ source-file, đọc nhanh từ đĩa
- Hệ điều hành: macOS

## Kết quả
- Packet giải mã: 30002
- Dữ liệu đầu vào: 2220092 bytes
- Lỗi giải mã: 0
- Issue counts: {}
- Live/offline decode khớp: True
- Maximum resident set size: 59342848 bytes (~59.34 MB)
- Peak memory footprint: 49349760 bytes (~49.35 MB)
- Thời gian thực thi: 1.03 giây

## Kết luận
Logger xử lý thành công luồng SYNTHETIC 30002 packet,
không phát hiện lỗi giải mã hoặc bất nhất live/offline.

Đây là kiểm thử chức năng và tải ngắn trên Mac,
không thay thế phép đo 120 phút trên laptop thu dữ liệu.

## Bằng chứng
- runs/packet_simulation_v3/linh_ram_10000/
- runs/packet_logger/linh_ram_10000/session_manifest.json
