# Nhóm dự án

## Vai trò và phạm vi phụ trách

| Thành viên | Vai trò chính | Thư mục phụ trách chính |
| --- | --- | --- |
| Linh | Phần mềm, pipeline dữ liệu, mô hình, kiểm thử và CI | **software/**, **configs/data/**, **configs/models/**, **tests/**, **.github/workflows/** |
| Đức Anh | Phần cứng, firmware, BOM, PCB và kiểm thử thiết bị | **hardware/**, **firmware/**, **configs/hardware/** |
| Huy | Xử lý tín hiệu, PAT, thống kê, protocol, tài liệu và điều phối bài báo | **software/signal_processing/**, **software/feature_extraction/**, **docs/**, **reports/** |

Phạm vi trên xác định người điều phối, không trao quyền sở hữu độc quyền.

## Nguyên tắc tổ chức

- Không tạo thư mục theo tên cá nhân như **Linh/**, **DucAnh/** hay **Huy/**.
- Tài liệu và sản phẩm được lưu theo chức năng kỹ thuật để dễ tìm và
  bàn giao.
- Một sản phẩm liên quan nhiều mảng phải có người phụ trách chính.
- Quyết định ảnh hưởng tới protocol, định dạng dữ liệu hoặc giao diện phần
  cứng–phần mềm phải được ghi lại trong issue, pull request hoặc biên bản họp.
