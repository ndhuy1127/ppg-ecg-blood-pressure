# Scripts

Các script hỗ trợ chạy thử và kiểm tra môi trường. Các lệnh bên dưới dùng thư
mục gốc repository; demo còn hỗ trợ chạy trực tiếp từ thư mục làm việc khác.

## Mỗi file làm gì và dùng dữ liệu nào

| File | Mục đích | Đầu vào / dữ liệu trong code | Đầu ra |
| --- | --- | --- | --- |
| [demo_week_03_baselines.py](demo_week_03_baselines.py) | Chạy thử B0/B1 và metrics cùng nhau | Tự sinh train, calibration, evaluation; các mảng BP `(3, 2)`, ID và thời điểm giả lập; seed `20261003` | JSON `SYNTHETIC` in ra Terminal |
| [check_environment.py](check_environment.py) | Kiểm tra import thư viện và phép tính NumPy | Mảng tự tạo `[1.0, 2.0, 3.0]`; không nhận dataset | Phiên bản Python/thư viện, kết quả `[2.0, 4.0, 6.0]`; exit 0 khi đạt |
| [run_b0_pulsedb_csv.py](run_b0_pulsedb_csv.py) | Fit B0 trên train, đánh giá val từ manifest CSV | Các cột trong bảng bàn giao của Linh; kiểm tra metadata mọi split, dùng nhãn train/val | Metrics tổng hợp và JSON truy vết trong `runs/`; không dùng nhãn test hoặc chạy B1 |
| [build_pulsedb_split.py](build_pulsedb_split.py) | Tạo split có inventory đối chiếu từ reader repo | Một file raw và config/checksum/pool đã chốt; giữ mọi dòng reader | Inventory, manifest, config và report trong thư mục mới; không ghi đè bàn giao cũ |
| [run_b3_pulsedb.py](run_b3_pulsedb.py) | Fit B0/B3 XGBoost trên train, đánh giá val | Raw `.mat`, thư mục split v2 và config `configs/models/b3_pulsedb_v0.json`; không đụng test | Report, bảng baseline, dự đoán val và model trong thư mục mới của `runs/` |
| [simulate_packets.py](simulate_packets.py) | Sinh/replay packet giả lập và kiểm tra lỗi | Config/seed SYNTHETIC, 6 case hoặc JSON giả lập | Packet, timeline/gap và report trong output mới; không phải đồng bộ phần cứng |

Hướng dẫn runner CSV: [chạy B0 trên PulseDB](../docs/protocol/run_b0_pulsedb_csv.md).
Hướng dẫn split mới: [inventory, config, hash và giới hạn](../docs/protocol/run_pulsedb_split.md).
Hướng dẫn B0/B3: [đặc trưng, model, đầu ra và giới hạn](../docs/protocol/run_b3_pulsedb.md).
Hướng dẫn mô phỏng: [schema riêng, expected results và giới hạn](../docs/protocol/packet_simulation.md).
Runner CSV có đầu vào riêng; các mô tả dữ liệu tự tạo bên dưới chỉ áp dụng demo.
Có thể mở `run_b0_pulsedb_csv.py` và bấm **Run Python File in Terminal**:
không truyền đối số thì script dùng `configs/data/b0_pulsedb_validation.json`
với CSV cục bộ đã bàn giao và kiểm tra hash trước khi chạy. CSV khác cần truyền
đường dẫn và đơn vị rõ ràng; xem hướng dẫn runner ở trên.

Demo không cần file dữ liệu đầu vào hoặc đối số CLI. Nó không đọc PulseDB,
không chứa nhãn/người tham gia thật và không ghi kết quả ra file. Các ID
`SYN_*` và thời điểm là số do code tạo, không thay metadata dự án. B0 dùng
train riêng; B1 dùng calibration của người đánh giá trước evaluation trong
ví dụ. Các hằng số và mảng chỉ tồn tại trong bộ nhớ của lần chạy.

## Chạy demo bằng nút VSCode

1. Mở `scripts/demo_week_03_baselines.py`.
2. Chọn interpreter `.venv` của repo nếu chưa chọn môi trường có dependency.
3. Bấm **Run Python File in Terminal** ở góc phải editor.
4. Xem JSON ở Terminal phía dưới. Không cần chạy các module lần lượt hoặc mở
   `launch.json`.

Demo tự thêm đường dẫn repo khi chạy trực tiếp để import package `software`.
Trong Windows, interpreter đã dùng là `.venv\Scripts\python.exe`; workspace
cũng đã kiểm tra chạy được demo với `.venv\bin\python.exe`.

Nếu dùng terminal từ Git root:

```powershell
.\.venv\Scripts\python.exe scripts/demo_week_03_baselines.py
# Cách chạy theo module cũng được hỗ trợ:
.\.venv\Scripts\python.exe -m scripts.demo_week_03_baselines
.\.venv\Scripts\python.exe scripts/check_environment.py
```

## Đọc kết quả demo

JSON có `source_type`, `purpose`, `seed`, `python`, `numpy`, `columns`, `unit`,
`error`, `sd_ddof`, `sd_if_n_lt_2` và hai mục `B0`, `B1`. Mỗi mục baseline có:

| Trường | Nội dung |
| --- | --- |
| `sample_weighted` | MAE/bias/SD riêng SBP/DBP tính từ tất cả mẫu, kèm `n` |
| `by_subject` | Các metrics riêng từng người; SD là `null` khi người chỉ có một mẫu |
| `subject_balanced` | MAE/bias trung bình đều theo người, kèm `n_subjects` |

Script hiện in metrics, không in các mảng train/calibration/evaluation hoặc
từng dự đoán. Xem [README models](../software/models/README.md) và
[README evaluation](../software/evaluation/README.md) để gọi API lấy những
kết quả đó. Seed giúp tái lập trong cùng môi trường; các số giả lập chỉ kiểm
chứng code/công thức, không chứng minh hiệu năng dự đoán BP trên dữ liệu thật.

Chi tiết phương pháp và giới hạn:
[quy ước Tuần 3](../docs/protocol/week_03_baselines_metrics.md).
