# Phần cứng

- **bom/**: danh mục linh kiện và phương án thay thế.
- **datasheets/**: liên kết datasheet chính thức và mức độ đối chiếu thông số
  ([README](datasheets/README.md)); không lưu file PDF.
- **schematics/**: sơ đồ nguyên lý và bản xuất.
- **pcb/**: nguồn thiết kế PCB; output và Gerber được Git bỏ qua.
- **mechanical/**: thiết kế cơ khí và ràng buộc kích thước.
- **test_reports/**: kế hoạch và báo cáo kiểm thử thiết bị:
  - [sync_10min_test_plan.md](test_reports/sync_10min_test_plan.md): đo tốc độ
    thực, drift, jitter, độ trễ và lệch ECG–PPG trên bench.

Tài liệu cấu hình liên quan ở `configs/hardware/`: yêu cầu V0, sơ đồ khối,
[nguồn/giao tiếp/lấy mẫu](../configs/hardware/interface_power_sampling_v0.md) và
[packet schema](../configs/hardware/Packet_Schema_V0.1.md).

Mọi quyết định mua linh kiện phải được duyệt. Tài liệu ở đây không chứng nhận
thiết bị đạt chuẩn y tế.
