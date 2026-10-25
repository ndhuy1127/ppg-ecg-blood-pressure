# Phần cứng

- **bom/**: danh mục linh kiện và phương án thay thế;
  [danh sách mua V1-module](bom/purchase_list_v1_module.md).
- **datasheets/**: liên kết datasheet chính thức và mức độ đối chiếu thông số
  ([README](datasheets/README.md)); không lưu file PDF.
- **kicad/**: thiết kế KiCad của V1-module, gồm `kicad/v1_module/base` (bo đế)
  và `kicad/v1_module/wrist` (bo cổ tay), mỗi bo có `.kicad_sch`, `.kicad_pcb`,
  `.kicad_pro`. PCB lưu theo định dạng KiCad 10.0, schematic theo 9.0: mở
  `.kicad_pcb` bằng KiCad ≥ 10. Mô tả, bảng GPIO và bảng chân cáp:
  [custom_board_proposal.md](../configs/hardware/custom_board_proposal.md) Phần A.
- **schematics/**: sơ đồ nguyên lý và bản xuất; hiện chỉ có `.gitkeep`.
- **pcb/**: nguồn thiết kế PCB; output và Gerber được Git bỏ qua. Hiện chỉ có
  `.gitkeep`; PCB của V1-module nằm ở `kicad/`.
- **mechanical/**: thiết kế cơ khí và ràng buộc kích thước.
- **test_reports/**: kế hoạch và báo cáo kiểm thử thiết bị:
  - [v1_bringup_procedure.md](test_reports/v1_bringup_procedure.md): trình tự
    kiểm khi nhận hàng, sửa module, hàn, cấp nguồn và kiểm từng khối của V1-module;
  - [sync_10min_test_plan.md](test_reports/sync_10min_test_plan.md): đo tốc độ
    thực, drift, jitter, độ trễ và lệch ECG–PPG trên bench.

Tài liệu cấu hình liên quan ở `configs/hardware/`: yêu cầu V0,
[sơ đồ khối V1-module](../configs/hardware/hardware_diagram_v1.svg),
[nguồn/giao tiếp/lấy mẫu](../configs/hardware/interface_power_sampling_v0.md),
[V1 dùng module và bản chip trần](../configs/hardware/custom_board_proposal.md) và
packet schema [V0.1](../configs/hardware/Packet_Schema_V0.1.md) và bản sửa đổi
[V0.2](../configs/hardware/Packet_Schema_V0.2.md) mà firmware V1 dùng.

Mọi quyết định mua linh kiện phải được duyệt. Tài liệu ở đây không chứng nhận
thiết bị đạt chuẩn y tế.
