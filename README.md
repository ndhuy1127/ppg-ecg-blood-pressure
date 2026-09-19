# Thiết bị đeo cổ tay ước lượng biến thiên huyết áp từ PPG và ECG

[![CI](https://github.com/ndhuy1127/ppg-ecg-blood-pressure/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/ndhuy1127/ppg-ecg-blood-pressure/actions/workflows/ci.yml)

**Thành viên mới:** đọc [Quy trình làm việc GitHub](docs/WORKFLOW.md) trước khi tạo commit hoặc Pull Request.

## Mục tiêu

Dự án xây dựng nguyên mẫu thiết bị đeo cổ tay và pipeline phân tích nhằm nghiên
cứu khả năng ước lượng biến thiên huyết áp giữa các phiên đo từ tín hiệu PPG và
ECG. Sản phẩm hiện chỉ phục vụ nghiên cứu, không phải thiết bị y tế và không
được dùng để chẩn đoán hay đưa ra quyết định điều trị.

## Câu hỏi nghiên cứu chính

> Việc bổ sung ECG và PAT có cải thiện khả năng dự đoán ΔSBP và ΔDBP qua các
> phiên đo so với chỉ sử dụng PPG hay không?

Trong dự án này, **PAT (Pulse Arrival Time)** là thời gian từ đỉnh R của ECG đến
chân sóng PPG. PAT bao gồm cả thành phần tiền tống máu nên **không được gọi là
PTT thực sự**.

## Thành viên và trách nhiệm

| Thành viên | Trách nhiệm |
| --- | --- |
| Linh | Phần mềm, dữ liệu, mô hình, kiểm thử và CI |
| Đức Anh | Phần cứng, firmware, BOM, PCB và kiểm thử thiết bị |
| Huy | Xử lý tín hiệu, PAT, thống kê, protocol, tài liệu và bài báo |

Mọi thay đổi đều cần được một thành viên khác review. Chi tiết xem
[docs/TEAM.md](docs/TEAM.md).

## Cấu trúc repository

- **configs/**: cấu hình dữ liệu, phần cứng và mô hình.
- **data/**: hướng dẫn quản lý dữ liệu và dữ liệu mẫu nhỏ đã ẩn danh.
- **docs/**: quy trình, kế hoạch, tài liệu nghiên cứu, protocol và đạo đức.
- **hardware/**: BOM, datasheet, sơ đồ nguyên lý, PCB, cơ khí và báo cáo thử.
- **firmware/**: ứng dụng nhúng, driver, board, header và kiểm thử.
- **software/**: nhập dữ liệu, tiền xử lý, xử lý tín hiệu, đặc trưng, mô hình,
  đánh giá và triển khai.
- **notebooks/**: khám phá dữ liệu và thí nghiệm có thể tái lập.
- **scripts/**: công cụ kiểm tra và tác vụ hỗ trợ.
- **tests/**: kiểm thử tự động.
- **reports/**: báo cáo tuần, hình và bản thảo bài báo.

## Cài đặt môi trường

Yêu cầu Python 3.11. Có thể dùng một trong hai cách:

### pip

~~~bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

### Conda

~~~bash
conda env create -f environment.yml
conda activate ppg-ecg-bp
~~~

PyTorch chưa được thêm ở giai đoạn dựng khung để giữ CI gọn nhẹ. Thư viện này
sẽ được bổ sung khi dự án bắt đầu giai đoạn xây dựng mô hình.

## Chạy kiểm tra

Từ thư mục gốc của repository:

~~~bash
ruff check .
pytest -q
python scripts/check_environment.py
~~~

## Quy trình nhánh

Luồng tích hợp:

~~~text
dev/thanh-vien → develop → main
~~~

Mỗi người đồng bộ từ **develop**, làm việc trên nhánh cá nhân, tạo pull request
vào **develop**, chờ review chéo và CI thành công. Chỉ tích hợp **develop** vào
**main** tại một mốc ổn định. Không làm việc trực tiếp trên **main**.

## Dữ liệu và bảo mật

Không commit dữ liệu ECG/PPG thật, dữ liệu định danh, dữ liệu nghiên cứu dung
lượng lớn, bí mật, token hay tệp môi trường. Chỉ dữ liệu mẫu nhỏ và đã ẩn danh
được phép đặt trong **data/sample/**. Dữ liệu nghiên cứu phải dùng
**subject_id**, **session_id** và **event_id**. Xem
[docs/DATA_POLICY.md](docs/DATA_POLICY.md) trước khi thêm dữ liệu.

## Trạng thái dự án

Dự án đang ở tuần 1 trong lộ trình 28 tuần. Các sản phẩm dự kiến của tuần 1:

- Repository có cấu trúc thống nhất và CI hoạt động.
- BOM v0.1 và sơ đồ khối phần cứng.
- Ít nhất hai phương án điện cực ECG.
- Ma trận 10–12 tài liệu.
- Câu hỏi nghiên cứu được thống nhất.
- Khung protocol và hồ sơ đạo đức v0.1.
- Báo cáo tuần 1.

Danh sách và người phụ trách chi tiết nằm tại
[docs/plans/WEEK_01.md](docs/plans/WEEK_01.md). Trạng thái thực tế phải được cập
nhật trong [reports/weekly/week_01/README.md](reports/weekly/week_01/README.md).
