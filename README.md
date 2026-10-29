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
`mat73==0.65` (reader PulseDB), `h5py==3.16.0` (đọc từng phần file `.mat` v7.3, thêm
2026-10-24), `pyserial==3.5` (logger đọc cổng serial, thêm 2026-10-24) và
`xgboost==3.2.0` (baseline B3). PyTorch chưa có
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

Dự án đang ở tuần 6 trong lộ trình 28 tuần (bắt đầu 2026-09-17; cập nhật 2026-10-29). Tóm tắt theo mức bằng chứng:

| Mức | Nội dung |
| --- | --- |
| Có code và test cục bộ (dữ liệu giả lập) | Reader PulseDB; inventory và split theo người `pulsedb-split-v2`; baseline hằng số B0/B1; MAE/bias/SD; đặc trưng PPG/HR/PAT, SQI `features-sqi-v1` và bootstrap theo người (Tuần 4); pipeline B0/B3 (XGBoost, đặc trưng `pulsedb-simple-stats-v0`) trên split v2, fit trên train và chỉ chấm val ([hướng dẫn](docs/protocol/run_b3_pulsedb.md)); logger packet V0.1 và V0.2 (mốc `SAMP` bit 8, nhiệt độ `0xB1`, cấu hình AFE `0xD2`, lệnh và xác nhận `0xD3`, kênh im lặng), mô phỏng `synthetic-packet-v3`, mốc R/foot thứ hai và quy tắc PAT hợp lệ (Tuần 5) |
| Build được, chưa chạy trên bo | Firmware ESP32-S3 gửi packet V0.2 (`0xD1`, IMU, mốc `SAMP`, nhiệt độ `0xB1`, cấu hình AFE `0xD2`, lệnh từ PC, xung kích thích đồng bộ) từ nguồn AFE giả, và driver chip thật MAX30001, MAX30101, BMI270 chưa chạy trên chip ([firmware/](firmware/README.md)) |
| Có code và test SYNTHETIC, chưa chạy | B2 trên PulseDB (nhân khẩu học cộng HR từ đỉnh R của ECG): chờ duyệt định nghĩa, runner từ chối chạy khi status là `PENDING_APPROVAL_NOT_RUN` ([định nghĩa B2](docs/protocol/b2_pulsedb_definition.md)) |
| Đã chạy sơ bộ trên dữ liệu công khai | B0 trên CSV nhãn PulseDB 1.000 đoạn (Tuần 3, lịch sử: tập AAMI Cal đã lộ test, xem [hướng dẫn](docs/protocol/run_b0_pulsedb_csv.md)); B0/B3 trên PulseDB VitalDB Train 400 người, chỉ chấm val, nhãn ABP công khai, không phải cuff ([Tuần 5](reports/weekly/week_05/pulsedb_b3_v1/README.md)) |
| Bản thảo | Câu hỏi nghiên cứu, protocol v0.3 ([protocol_outline_v0.2.md](docs/protocol/protocol_outline_v0.2.md)), hồ sơ đạo đức (các mục thiết kế/đạo đức đã có phương án của nhóm ngày 2026-10-29, chờ thầy duyệt trước khi nộp), tổng quan tài liệu, danh sách mua |
| Phần cứng V1, chưa có trong tay | Thiết kế KiCad V1-draft5: PCB V1 đang đặt gia công ở CXT từ 2026-10-28. Bo Waveshare ESP32-S3-DEV-KIT-N8R8-M đã đặt 2026-10-27; MAX30001, MAX30101, BMI270 và điện cực chưa đặt |
| Chưa có | Phần cứng lắp ráp, bản ghi ECG/PPG của nhóm, dữ liệu cuff, mô hình ΔBP và mọi kết quả trả lời RQ1–RQ3 |

Kết quả trên dữ liệu giả lập chỉ kiểm tra code, không phải hiệu năng ước lượng
huyết áp. Kế hoạch từng tuần nằm trong [docs/plans/](docs/plans/README.md); trạng
thái và bằng chứng nằm trong báo cáo tuần tại [reports/weekly/](reports/weekly/).
