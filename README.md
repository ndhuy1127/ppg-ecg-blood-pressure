# Thiết bị đeo cổ tay ước lượng biến thiên huyết áp từ PPG và ECG


[![CI](https://github.com/ndhuy1127/ppg-ecg-blood-pressure/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/ndhuy1127/ppg-ecg-blood-pressure/actions/workflows/ci.yml)

**Thành viên mới:** đọc [Quy trình làm việc GitHub](docs/WORKFLOW.md) trước khi tạo commit hoặc Pull Request.


## Mục tiêu

Dự án xây dựng nguyên mẫu thiết bị đeo cổ tay và pipeline phân tích nhằm nghiên
cứu khả năng ước lượng biến thiên huyết áp giữa các phiên đo từ tín hiệu PPG và
ECG. Sản phẩm hiện chỉ phục vụ nghiên cứu, không phải thiết bị y tế và không
được dùng để chẩn đoán hay đưa ra quyết định điều trị.

## Câu hỏi nghiên cứu

Chi tiết trong
[docs/research_questions_v0.1.md](docs/research_questions_v0.1.md):

1. **RQ1 (câu hỏi chính):** Sau khi hiệu chuẩn bằng một lần đo cuff, việc bổ
   sung ECG để tính PAT có làm giảm sai số dự đoán ΔSBP và ΔDBP ở các phiên đo
   sau so với mô hình chỉ dùng PPG hay không?
2. **RQ2:** Sai số thay đổi bao nhiêu khi chuyển từ chia ngẫu nhiên theo cửa sổ
   (có rò rỉ dữ liệu) sang chia theo người và chia theo phiên đo?
3. **RQ3:** Từ chối dự đoán dựa trên SQI và độ bất định có cho sai số thấp hơn
   so với từ chối ngẫu nhiên ở cùng tỷ lệ giữ lại (coverage) không?

Trong dự án này, **PAT (Pulse Arrival Time)** là thời gian từ đỉnh R của ECG đến
chân sóng PPG. PAT gồm cả thời gian tiền tống máu (PEP), `PAT = PEP + PTT`, nên
**không được gọi là PTT**.

## Thành viên và trách nhiệm

| Thành viên | Trách nhiệm |
| --- | --- |
| Linh | Phần mềm, dữ liệu, mô hình, kiểm thử và CI |
| Đức Anh | Phần cứng, firmware, BOM, PCB và kiểm thử thiết bị |
| Huy | Xử lý tín hiệu, PAT, thống kê, protocol, tài liệu và bài báo |

Phân công chi tiết xem [docs/TEAM.md](docs/TEAM.md).

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

Bắt buộc dùng **Python 3.11**: `pyproject.toml` khai báo
`requires-python = ">=3.11,<3.12"` và CI chạy Python 3.11. Có thể dùng một
trong hai cách:

### pip

Windows PowerShell (`py -3.11` chọn đúng Python 3.11 khi máy có nhiều bản):

~~~powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

Linux/macOS:

~~~bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

### Conda

~~~text
conda env create -f environment.yml
conda activate ppg-ecg-env
~~~

`requirements.txt`, `pyproject.toml` và `environment.yml` cố định phiên bản
`mat73==0.65` (reader PulseDB) và `xgboost==3.2.0` (baseline B3). PyTorch chưa có
trong dependency; thành viên cần dùng sẽ bổ sung kèm phiên bản cố định.

## Chạy kiểm tra

Từ thư mục gốc của repository, sau khi kích hoạt môi trường:

~~~text
ruff check .
pytest -q
python scripts/check_environment.py
python -m pip check
~~~

## Quy trình nhánh

Luồng tích hợp:

~~~text
dev/thanh-vien → develop → main
~~~

Mỗi người đồng bộ từ **develop**, làm việc trên nhánh cá nhân, tạo pull request
vào **develop** và chờ CI thành công. Chỉ tích hợp **develop** vào
**main** tại một mốc ổn định. Không làm việc trực tiếp trên **main**.

## Dữ liệu và bảo mật

Không commit dữ liệu ECG/PPG thật, dữ liệu định danh, dữ liệu nghiên cứu dung
lượng lớn, bí mật, token hay tệp môi trường. Chỉ dữ liệu mẫu nhỏ và đã ẩn danh
được phép đặt trong **data/sample/**. Dữ liệu nghiên cứu phải dùng
**subject_id**, **session_id** và **event_id**. Xem
[docs/DATA_POLICY.md](docs/DATA_POLICY.md) trước khi thêm dữ liệu.

## Trạng thái dự án

Dự án đang ở tuần 4 trong lộ trình 28 tuần. Tóm tắt theo mức bằng chứng:

| Mức | Nội dung |
| --- | --- |
| Có code và test cục bộ (dữ liệu giả lập) | Reader PulseDB; inventory và split theo người `pulsedb-split-v2`; baseline hằng số B0/B1; MAE/bias/SD; generator/replay packet giả lập; đặc trưng PPG/HR/PAT, SQI `features-sqi-v1` và bootstrap theo người (Tuần 4); pipeline B0/B3 (XGBoost, đặc trưng `pulsedb-simple-stats-v0`) trên split v2, fit trên train và chỉ chấm val, chưa chạy trên raw PulseDB ([hướng dẫn](docs/protocol/run_b3_pulsedb.md)) |
| Đã chạy sơ bộ trên dữ liệu công khai | B0 trên CSV nhãn PulseDB 1.000 đoạn (Tuần 3); nguồn raw và pool chưa nghiệm thu |
| Bản thảo | Câu hỏi nghiên cứu, protocol, ethics, tổng quan tài liệu, BOM và thiết kế mạch |
| Chưa có | Phần cứng lắp ráp, bản ghi ECG/PPG của nhóm, dữ liệu cuff, mô hình ΔBP và mọi kết quả trả lời RQ1–RQ3 |

Kết quả trên dữ liệu giả lập chỉ kiểm tra code, không phải hiệu năng ước lượng
huyết áp. Kế hoạch từng tuần nằm trong [docs/plans/](docs/plans/README.md); trạng
thái và bằng chứng nằm trong báo cáo tuần tại [reports/weekly/](reports/weekly/).
