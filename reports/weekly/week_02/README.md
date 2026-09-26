# Báo cáo Tuần 2 — trạng thái khởi tạo

> Cập nhật 2026-09-25. Đây là **báo cáo tiến độ**, không phải biên bản nghiệm thu Tuần 2.

## Sản phẩm đã có trong repository

| Sản phẩm | Bằng chứng | Trạng thái |
| --- | --- | --- |
| Kế hoạch và phụ thuộc Tuần 2 | [Kế hoạch Tuần 2](../../../docs/plans/WEEK_02.md) | Bản thảo chờ nhóm review |
| Định nghĩa mẫu, nhãn và thuật ngữ PAT/PTT/PEP/PWA | [Tài liệu phương pháp](../../../docs/protocol/week_02_sample_label_glossary.md) | Bản thảo chờ Linh và Đức Anh xác nhận giao diện |

## Chưa có bằng chứng để nghiệm thu

- Chưa có phiên bản PulseDB được phép dùng, checksum manifest, trình đọc, test hoặc notebook 1.000 đoạn trong repo.
- Đã có BOM v0.1 trong repo, nhưng chưa có firmware/log cấu hình hay bản ghi tín hiệu v0 được xác nhận; chưa thể kiểm tra R peak, trôi nền và PPG foot.
- Chưa có review chéo notebook/bản ghi v0 hoặc biên bản nhóm khóa schema, cửa sổ và SQI.
- Chưa xác nhận phê duyệt đạo đức và kiểm tra an toàn để thu tín hiệu trên người. Không diễn giải việc lắp/kiểm thử bàn máy là đã thu dữ liệu người tham gia.

## Việc tiếp theo để đóng Tuần 2

1. Linh ghi nguồn, phiên bản và điều khoản PulseDB; bàn giao trình đọc/test/notebook và số đoạn đọc thành công có truy vết.
2. Đức Anh bàn giao log cấu hình/timestamp và mã manifest của bản ghi v0 được phép dùng; xác nhận điều kiện an toàn.
3. Huy cùng Đức Anh điền phiếu kiểm tra trực quan trong tài liệu phương pháp; cùng Linh chốt ánh xạ nhãn và ghi thay đổi protocol/schema nếu có.
4. Nhóm review chéo, ghi issue tồn đọng trước Tuần 3; cập nhật bảng trạng thái theo bằng chứng thực tế.

## Rủi ro phương pháp đã nhận diện

PulseDB cung cấp ABP waveform, còn bài toán prototype dùng nhãn cuff theo `event_id`; hai nguồn không được gộp như cùng một thiết kế quan sát. PAT từ ECG R peak đến PPG foot không phải PTT. Cửa sổ 10/20/30/60 giây là phương án phân tích độ nhạy, chưa phải bốn nhãn độc lập.
