# Báo cáo tiến độ Tuần 3

> **Giai đoạn:** Tuần 3 / 28 tuần
> **Người tổng hợp:** Nguyễn Đức Huy
> **Vai trò:** Xử lý tín hiệu, PAT, phương pháp thống kê, protocol, tổng quan y văn và điều phối báo cáo
> **Ngày báo cáo:** 2026-10-03 (mốc báo cáo gốc)
> **Ngày kiểm tra bổ sung:** 2026-10-05
> **Ngày cập nhật bố cục:** 2026-10-08. Giữ kết quả kiểm tra lịch sử; code/test giả lập chưa thay review chéo, phê duyệt phương pháp hoặc nghiệm thu toàn bộ Tuần 3.

> **Bổ sung 2026-10-08:** mục 6.4 ghi lần chạy B0 sơ bộ trên nhãn CSV công khai
> do Linh bàn giao. Các mô tả kiểm thử chỉ dùng SYNTHETIC ở phần lịch sử áp dụng
> cho lần triển khai ban đầu; B1/PAT/thiết bị thật vẫn chưa được đánh giá.

---

## 1. Mục tiêu tuần 3

Theo [kế hoạch Tuần 3](../../../docs/plans/WEEK_03.md), các mục tiêu trọng tâm gồm:

1. Linh chuẩn bị split PulseDB theo người, manifest/config/seed và kiểm thử chống rò rỉ.
2. Đức Anh hoàn thiện quy ước timestamp/packet và fixture kiểm tra đồng bộ ECG–PPG trên máy tính.
3. Huy triển khai B0 hằng số từ train và B1 hằng số từ calibration riêng trước evaluation.
4. Huy xây MAE/bias/SD riêng SBP/DBP, test đáp án biết trước, demo tái lập và đặc tả các chỉ số mở rộng còn cần thống nhất.
5. Bàn giao code, cấu hình, test, bằng chứng và các đầu vào còn chờ để chuẩn bị pipeline baseline Tuần 4.

Báo cáo ban đầu ghi nhận **phần độc lập của Huy đã làm bằng dữ liệu SYNTHETIC**.
Bổ sung mục 6.4 chạy B0 từ nhãn CSV PulseDB; kết quả là sơ bộ, chờ review nguồn
raw và phương pháp. Chưa chạy B1 trên PulseDB/PAT hoặc đánh giá thiết bị thật;
chưa hoàn thành toàn bộ Tuần 3.

---

## 2. Thành viên phụ trách và Phân công công việc

| Công việc | Người phụ trách chính | Reviewer dự kiến | Trạng thái ghi nhận |
| --- | --- | --- | --- |
| Split/manifest PulseDB và bằng chứng chống rò rỉ | Linh | Huy, Đức Anh | Có bản sửa split v2 và test giả lập; chờ raw/config/pool được review và chạy lại để nghiệm thu; xem mục 6.6 |
| Timestamp/packet, fixture đồng bộ và kế hoạch đo thật | Đức Anh | Linh, Huy | Có công cụ hỗ trợ mô phỏng v2 và test; chờ Đức Anh review schema/clock, kế hoạch đo thật; xem mục 6.6 |
| B0/B1, validation, metrics, test và demo | Huy | Linh | Đã triển khai và kiểm thử cục bộ bằng giả lập; chờ review code và phương pháp |
| Quy ước đánh giá và tổng hợp báo cáo Tuần 3 | Huy | Linh, Đức Anh; nhóm/giảng viên review phương pháp | Đã có tài liệu/báo cáo; các quyết định khoa học còn mở chưa được khóa |

---

## 3. Công việc đã hoàn thành của Huy

Dấu tích xác nhận output/code và kiểm tra cục bộ trên dữ liệu giả lập; không xác nhận hiệu năng trên dữ liệu thật hoặc phê duyệt khoa học.

- [x] **B0:** Tính trung bình SBP/DBP từ nhãn train; predict không nhận nhãn evaluation.
- [x] **B1:** Tính trung bình hiệu chuẩn từng người; báo lỗi khi người chưa hiệu chuẩn, không fallback sang B0.
- [x] **Validation dùng chung:** Kiểm tra input rỗng, shape, kiểu, giá trị hữu hạn, ID và overflow; không tự bỏ mẫu.
- [x] **Metrics:** MAE/bias/SD riêng SBP/DBP, tổng hợp theo mẫu, theo người và trung bình đều theo người.
- [x] **Test và demo:** Fixture có đáp án biết trước, seed cố định, JSON đánh dấu SYNTHETIC; bổ sung hỗ trợ chạy trực tiếp demo.
- [x] **Tài liệu phương pháp:** API, công thức, lỗi input và đặc tả beta/Pearson ΔBP/Bland–Altman/coverage; các lựa chọn chưa khóa được ghi chờ review.
- [x] **Báo cáo và bàn giao:** Ghi lệnh/kết quả kiểm tra, giới hạn dữ liệu giả lập và đầu vào còn chờ Linh/Đức Anh.

---

## 4. Danh mục sản phẩm đầu ra và Đường dẫn

| STT | Tên sản phẩm | Đường dẫn tương đối | Trạng thái |
| --- | --- | --- | --- |
| 1 | B0 train-mean, B1 calibration-mean | [constant_baselines.py](../../../software/models/constant_baselines.py) | Đã triển khai, test giả lập |
| 2 | MAE/bias/SD SBP và DBP, tổng hợp theo mẫu/người | [bp_metrics.py](../../../software/evaluation/bp_metrics.py) | Đã triển khai, test đáp án tính tay |
| 3 | Validation dùng chung tối thiểu | [_bp_validation.py](../../../software/_bp_validation.py) | Từ chối input lỗi và overflow, không tự bỏ mẫu |
| 4 | Test baseline và chống dùng nhãn evaluation | [test_week_03_baselines.py](../../../tests/test_week_03_baselines.py) | Đã chạy |
| 5 | Test metrics và demo tái lập | [test_bp_metrics.py](../../../tests/test_bp_metrics.py) | Đã chạy |
| 6 | Demo độc lập seed cố định | [demo_week_03_baselines.py](../../../scripts/demo_week_03_baselines.py) | Đã chạy, đầu ra JSON SYNTHETIC |
| 7 | API, công thức, điều kiện tích hợp, chỉ số mở rộng | [quy ước Tuần 3](../../../docs/protocol/week_03_baselines_metrics.md) | Đã viết, chưa thay phê duyệt khoa học |

Baseline/metrics trước tác vụ chỉ là khung `__init__.py`; reader PulseDB và test
Tuần 2 đã có trong workspace và được giữ nguyên. Thư mục báo cáo Tuần 3 chưa
tồn tại nên tạo README này. Ở lần triển khai ban đầu, trạng thái Git sạch,
nhánh `dev/huy`, base commit `573bd92`; các đầu ra mới chưa commit trên base đó.
Lần triển khai đó không commit/push/merge/đổi nhánh hoặc gửi tin nhắn cho thành
viên khác. Kiểm tra trước commit/push theo yêu cầu ngày 2026-10-08 nằm ở mục 6.3.

---

## 5. Tóm tắt các nội dung chuyên môn chính

### 5.1. Quy ước B0/B1, dữ liệu và chỉ số đánh giá

- B0 dùng trung bình **dòng nhãn train** độc lập cho SBP/DBP theo WEEK_03;
  trọng số train khi tích hợp dataset thật cần nhóm review.
- B1 dùng trung bình nhãn hiệu chuẩn riêng từng người theo yêu cầu tác vụ.
  Quy tắc chọn/tổng hợp calibration thực tế chưa khóa. Predict không nhận nhãn
  evaluation; người chưa hiệu chuẩn gây lỗi, không chuyển sang B0. B1 thuộc
  cá nhân hóa có hiệu chuẩn, không phải đánh giá người mới chưa hiệu chuẩn.
- Cột `[SBP, DBP]`, BP tuyệt đối, mmHg; `error = prediction - reference`.
  MAE/bias/SD riêng từng đầu ra. `SD` mẫu `ddof=1`, `None`/JSON `null` khi n=1;
  đầu vào rỗng lỗi. Không tự loại NaN/Inf, missing hoặc dòng không hợp lệ.
- `sample_weighted` mô tả tất cả dòng; `by_subject` mô tả từng người;
  `subject_balanced` trung bình đều MAE/bias theo người (chỉ số chính theo kế
  hoạch). Không lấy trung bình SD từng người làm SD chung.
- API không có metadata nên không thể xác minh split/chronology/event;
  caller phải kiểm tra trước. Một cuff event chỉ có một cặp nhãn độc lập.
  ABP PulseDB không phải cuff và không thay kết quả ΔBP cross-session.
- Chỉ đặc tả beta, Pearson ΔBP, Bland–Altman và coverage; không cài chỉ số
  chưa thống nhất hoặc chạy phân tích thật. Công thức ứng viên được đánh dấu
  chờ review; LoA phân biệt với CI, coverage phân biệt với tỷ lệ sai số ≤5/10.

### 5.2. Phạm vi kiểm chứng và giới hạn diễn giải

Test dùng fixture số tự tạo. Đã kiểm tra hằng số đúng, thứ tự dự đoán, thay nhãn
evaluation chỉ đổi metrics, B1 không fallback, lỗi input, prediction trước fit,
không alias state, refit B1 thay state và fit lỗi giữ state. Ví dụ metrics có
sai số SBP `[-2, 0, 2]`, DBP `[1, -1, 3]` được kiểm tra với đáp án tính tay;
fixture 3 dòng của A và 1 dòng của B kiểm tra rõ khác biệt weighting.
Test demo chạy hai lần trong cùng môi trường cho cùng kết quả.

Chưa chạy CI online, chưa review chéo, chưa kiểm thử Python 3.11. Không đọc
dataset/người tham gia, không tạo artifact dữ liệu thật, không đo phần cứng.
Các số trong demo chỉ kiểm chứng code/công thức; không dùng so sánh hiệu năng
mô hình hoặc khẳng định khả năng dự đoán BP của dự án.

---

## 6. Kết quả kiểm tra kỹ thuật (Verification Results)

Các kết quả dưới đây giữ nguyên ngày kiểm tra và số liệu đã ghi nhận; đổi bố cục ngày 2026-10-08 không phải một lần chạy lại test/CI.

### 6.1. Kiểm tra cục bộ ngày 2026-10-03

Ngày 2026-10-03, dùng `.venv` hiện có: Python **3.13.12**, NumPy **2.5.3**,
pytest **9.1.1**, Ruff **0.3.0**. Environment check còn in scipy 1.18.1,
pandas 3.0.6, matplotlib 3.11.2, scikit-learn 1.9.1, PyYAML 6.0.3.
Môi trường này **khác Python 3.11 và dependency pin của repo**; không sửa
môi trường/cấu hình hỗ trợ và không coi kết quả cục bộ là CI Python 3.11.

| Công cụ kiểm tra | Lệnh thực hiện | Kết quả | Chi tiết / Bằng chứng |
| --- | --- | --- | --- |
| **Ruff Linter** | `.\.venv\Scripts\python.exe -m ruff check .` | **PASS** | Đạt, exit 0 |
| **Pytest trong sandbox** | `.\.venv\Scripts\python.exe -m pytest -q` | **LỖI HẠ TẦNG** | 70 passed, 2 errors, 2 warnings; hai test reader hiện có lỗi setup WinError 5 ở thư mục Temp, cache cũng bị giới hạn quyền |
| **Pytest chạy lại ngoài sandbox** | Cùng lệnh pytest, chạy lại ngoài sandbox sau khi được cho phép | **PASS cục bộ** | Ban đầu 72 passed; sau bổ sung test bool trộn với số, lần cuối **74 passed in 0.41s**, exit 0 |
| **Test B0/B1 và metrics** | `.\.venv\Scripts\python.exe -m pytest -q tests/test_week_03_baselines.py tests/test_bp_metrics.py` | **PASS cục bộ** | **67 passed in 0.60s**, exit 0; một cảnh báo cache WinError 5 trong sandbox |
| **Environment Check** | `.\.venv\Scripts\python.exe scripts/check_environment.py` | **PASS cục bộ** | Đạt, exit 0; import thư viện và phép tính NumPy đúng |
| **Dependency Check** | `.\.venv\Scripts\python.exe -m pip check` | **PASS** | `No broken requirements found.`, exit 0; không chứng minh khớp dependency pin |
| **Demo giả lập** | `.\.venv\Scripts\python.exe -m scripts.demo_week_03_baselines` | **PASS** | Đạt, exit 0; JSON SYNTHETIC chứa B0/B1, SBP/DBP, n, MAE/bias/SD, theo người và trung bình đều theo người |
| **Git Diff / Kiểm tra tài liệu** | `git diff --check` và kiểm tra tệp thay đổi bằng Python | **PASS** | Đạt: 9 tệp; không whitespace cuối dòng/conflict markers, liên kết tương đối tài liệu tồn tại, cú pháp Python parse theo grammar 3.11; không thay kiểm thử runtime 3.11 |

### 6.2. Kiểm tra bổ sung ngày 2026-10-05

**Kiểm tra bổ sung 2026-10-05 sau lỗi import khi chạy trực tiếp:** đã sửa demo
để thiết lập đường dẫn repo trước khi import `software`. Chạy lại đúng lệnh
người dùng cung cấp với `.venv/bin/python.exe` và đường dẫn file demo tuyệt đối:
đạt, exit 0, in JSON `SYNTHETIC` (Python 3.13.12, NumPy 2.5.3).
Đã thêm test chạy file trực tiếp từ `scripts/` trong isolated mode, kết quả khớp
`run_demo()`. Hai file test mới đạt **68 passed in 0.53s** (tắt cache); Ruff và
`git diff --check` đạt. Chưa chạy lại full suite/CI trong lần sửa này. Có thể
bấm **Run Python File in Terminal** trên file demo, không cần `launch.json`.

### 6.3. Kiểm tra trước commit/push ngày 2026-10-08

Theo yêu cầu đưa các đầu ra lên `dev/huy`, đã kiểm tra lại toàn bộ repo với
`.venv` hiện có (Python 3.13.12), giữ nguyên cấu hình hỗ trợ Python 3.11.

| Công cụ kiểm tra | Lệnh thực hiện | Kết quả | Chi tiết / Bằng chứng |
| --- | --- | --- | --- |
| **Ruff Linter** | `.\.venv\Scripts\python.exe -m ruff check .` | **PASS** | Exit 0 |
| **Pytest toàn repo** | `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider` | **PASS cục bộ** | `75 passed in 0.38s`, exit 0; chạy ngoài sandbox sau khi được cho phép |
| **Environment Check** | `.\.venv\Scripts\python.exe scripts/check_environment.py` | **PASS cục bộ** | Exit 0; Python 3.13.12, NumPy 2.5.3; chưa thay CI/runtime Python 3.11 |
| **Dependency Check** | `.\.venv\Scripts\python.exe -m pip check` | **PASS** | `No broken requirements found.`, exit 0 |
| **Git Diff Check** | `git diff --check` | **PASS** | Không có lỗi khoảng trắng trong diff |

Lần pytest trong sandbox có `73 passed, 2 errors` do hai fixture reader không
truy cập được thư mục Temp (`WinError 5`). Chạy lại ngoài sandbox đã đạt toàn bộ
75 test; không bỏ hoặc sửa logic test để che lỗi hạ tầng. Các thay đổi gồm code,
test, tài liệu API/README và báo cáo; không có dữ liệu thật. Chưa xác nhận CI
online hoặc review chéo. Push nhánh cá nhân không đồng nghĩa nghiệm thu dự án.

---

### 6.4. Runner B0 và CSV bàn giao ngày 2026-10-08

- Workspace chính chuyển sang `dev/ngoclinh`, chưa có baseline/metrics. Đã tạo
  checkout riêng `tmp/b0_pulsedb_work` từ `dev/huy@7ba230f` (đã gỡ 2026-10-22),
  giữ nhánh chính.
  Khi workspace chính đã trở lại `dev/huy@7ba230f` và Git sạch, đã sao các file
  runner/test/tài liệu đã kiểm thử cùng JSON kết quả về workspace chính. Không
  tự checkout, commit, push hoặc merge; checkout riêng vẫn giữ bản kiểm thử.
- Lấy CSV `notebooks/pulsedb_manifest_1000.csv` và đọc code notebook
  `week3-split-hash.ipynb` ở `origin/dev/ngoclinh@1f218eb` sau Git fetch.
  Không in bảng/ID người hoặc đọc waveform; CSV cục bộ nằm ngoài Git.
- Runner mới `scripts/run_b0_pulsedb_csv.py` dùng B0/metrics hiện có, giữ split,
  kiểm tra metadata mọi tập và chỉ dùng nhãn train/val. Notebook ghi split
  seed 72. Không dùng nhãn test hoặc tạo calibration B1.
- Lệnh đã chạy: `python scripts/run_b0_pulsedb_csv.py D:\ppg-ecg-blood-pressure\data\processed\linh_week03\pulsedb_manifest_1000.csv --unit mmHg --split-seed 72 --manifest-ref 1f218eb`,
  với interpreter `.venv` của workspace chính, trong checkout riêng.
- JSON do runner tạo: `runs/b0_pulsedb/20261008T082734462661Z/metrics.json`,
  lưu số mẫu/người từng split, mức B0, MAE/bias/SD, weighting, seed, hash CSV,
  ref CSV, môi trường, commit/hash code, log và giới hạn. Đây là artifact cục
  bộ được ignore; không phải số liệu nhập tay hoặc bằng chứng nghiệm thu.
- Hai file test cũ cùng test runner mới: 81 passed. Full suite: **88 passed in
  0.43s**, exit 0 sau khi được phép chạy ngoài sandbox. Lần sandbox có lỗi
  thư mục tạm, gồm thiếu thư mục cha (WinError 3), sau đó giới hạn quyền
  (WinError 5); không đổi logic reader/test. Ruff toàn checkout đạt.
- Môi trường vẫn là Python 3.13.12, chưa thay kiểm chứng CI Python 3.11.
- Giới hạn: notebook đọc `file_paths[0]` nhưng ghi source cố định; cần xác nhận
  file/raw checksum thực dùng, pool/holdout gốc, mapping người, index raw và
  trọng số quan sát. Chưa tái tính sample_hash từ raw. Kết quả B0 chỉ mô tả
  nhãn CSV bàn giao; chưa chứng minh hiệu năng cuff/ΔBP hoặc hoàn thành Tuần 3.
- [Hướng dẫn chạy lại](../../../docs/protocol/run_b0_pulsedb_csv.md).
- Theo yêu cầu làm trên nhánh Huy, đã xác nhận workspace chính ở `dev/huy`
  và chạy lại runner trực tiếp từ Git root. JSON lần chạy trên dev/huy:
  `runs/b0_pulsedb/20261008T083043729745Z/metrics.json`
  cho cùng kết quả như lần kiểm thử checkout riêng. Ruff đạt và 81 test
  baseline/metrics/runner đạt trong 0.35s; không chạy lại full suite trong lần
  này. Thay đổi vẫn chưa commit/push; B1 trên CSV vẫn chưa đủ calibration.
- Bổ sung hỗ trợ **Run Python File in Terminal** sau lỗi thiếu `csv_path` và
  `--unit`: khi không truyền đối số, runner đọc cấu hình versioned
  `configs/data/b0_pulsedb_validation.json`, dùng đường dẫn theo repo và kiểm tra
  hash của CSV đã ghi nhận. CSV truyền riêng vẫn phải xác nhận đơn vị và không
  kế thừa seed/ref mặc định. Không đổi split, weighting hoặc công thức metrics.
  Đã chạy không đối số bằng `.venv/bin/python.exe` với file script tuyệt đối
  từ thư mục `scripts/`, exit 0; JSON lần chạy:
  `runs/b0_pulsedb/20261008T083535378627Z/metrics.json`
  khớp kết quả trước. Test baseline/metrics/runner đạt 84 passed in 0.35s,
  Ruff và diff check đạt; chưa chạy lại full suite/CI trong lần sửa này.

### 6.5. Kiểm tra file dự kiến commit ngày 2026-10-09

- Nhánh `dev/huy`; các file dự kiến commit gồm runner, test SYNTHETIC, cấu hình
  JSON, hướng dẫn chạy và hai README. Không stage/commit/push trong lần rà soát.
- Ruff và `git diff --check` đạt. Full suite chạy ngoài sandbox: **91 passed
  in 0.47s**, exit 0. Lần sandbox có 89 passed, 2 errors do WinError 5 trong
  fixture Temp của reader; không đổi test hoặc bỏ test để che lỗi quyền.
- `scripts/check_environment.py` và `pip check` đạt trong môi trường hiện có
  Python 3.13.12. Chưa kiểm thử runtime/CI Python 3.11 hoặc review chéo.
- Không thấy secret hay dữ liệu thật theo người trong sáu file dự kiến commit.
  CSV ở `data/processed/`, JSON kết quả ở `runs/`, checkout tạm ở `tmp/` (đã gỡ
  2026-10-22) được ignore và không nằm trong danh sách file thay đổi Git.
- Các đường dẫn JSON ở mục 6.4 là artifact cục bộ, không có trong GitHub.
  Hướng dẫn runner ghi cách lấy CSV đúng version và chạy lại để tạo kết quả.

### 6.6. Bản sửa hỗ trợ phần Linh và Đức Anh ngày 2026-10-10

- **Phần Linh:** `software/data_io/split_manifest.py`,
  `scripts/build_pulsedb_split.py` và `tests/test_split_manifest.py` có inventory,
  split theo người, hash waveform độc lập ID/nhãn, kiểm tra bảo toàn mẫu và
  metadata round-trip. [Hướng dẫn bàn giao](../../../docs/protocol/run_pulsedb_split.md)
  ghi schema `pulsedb-split-v2`, đầu vào/pool phải review và giới hạn raw/ID.
- **Phần Đức Anh:** `software/data_io/packet_simulation.py`,
  `scripts/simulate_packets.py`, config tại `configs/hardware/packet_simulation.json`,
  expected fixture tại `tests/fixtures/packet_simulation_expected.json` và test
  `tests/test_packet_simulation.py`. Sáu case kiểm tra valid/missing/duplicate/
  reordered/timestamp/offset, giữ gap và thời gian phân số chính xác, có
  seed/hash/code/commit truy vết. [Schema và hướng dẫn](../../../docs/protocol/packet_simulation.md)
  chỉ áp dụng SYNTHETIC; chờ Đức Anh review, không phải decoder firmware.
- **Tích hợp B0:** runner kiểm tra `waveform_hash` khi cột này có mặt, từ chối
  hash giao split dù `subject_id`/`sample_hash` khác nhau. Có regression test cho
  train–val/test, hash lỗi và lặp cùng split. Không đọc nhãn test để đánh giá,
  không đổi split/trọng số/B0; kiểm tra CSV không thay validator với inventory.
- **Kiểm tra cục bộ:** Ruff và `git diff --check` đạt; full suite **199 passed
  in 2.08s**, exit 0, chạy ngoài sandbox để dùng fixture Temp. Python vẫn
  **3.13.12**, chưa thay kiểm chứng CI/runtime Python 3.11. Các test mới dùng
  SYNTHETIC; không chạy raw PulseDB hoặc thiết bị trong lần tích hợp này.
- **Còn chờ:** Linh bàn giao raw/config/checksum/pool được review, chạy hai lần
  đối chiếu inventory/manifest; Đức Anh thống nhất version V0.1 trong Markdown
  với V1 trong Word tại ref `40ede49`, clock/FIFO và kế hoạch đo 10 phút.
  Các bước đo người chỉ thực hiện khi đủ điều kiện an toàn/phê duyệt theo repo.
  CI và review chéo sẽ được kiểm tra trên PR; chưa nghiệm thu toàn bộ Tuần 3.

## 7. Khó khăn, Rủi ro và Vướng mắc kỹ thuật

B0 đã chạy sơ bộ từ CSV ở mục 6.4; nguồn raw/split chưa nghiệm thu đầy đủ.
Chronology/calibration cho B1, fixture/waveform xác minh và dữ liệu thiết bị thật
vẫn chưa có. Các công việc đang chờ và yêu cầu bàn giao:

| Công việc | Người cung cấp / phối hợp | Đầu vào cần nhận | Sau bàn giao Huy sẽ làm |
| --- | --- | --- | --- |
| B0/B1 trên split PulseDB chính thức | Linh; Huy review | Manifest version/hash, file/checksum/nguồn/quyền sử dụng, `sample_id`, `subject_id`, source/record/window gốc, split, nhãn SBP/DBP và đơn vị, config/seed/commit, log validator không giao người/trùng/mất mẫu | Xác minh đơn vị quan sát, mapping/split; fit B0 chỉ train rồi đánh giá theo cấu hình đã review; B1 chỉ khi đủ calibration hợp lệ |
| Chọn calibration B1 PulseDB | Linh + Huy/nhóm | Metadata người, phiên/thời điểm đáng tin cậy, sample/record ID; danh sách calibration/evaluation không trùng, quyền dùng nhãn, chronology và quy tắc tổng hợp được duyệt | Kiểm tra calibration trước evaluation; fit B1 trên calibration riêng và báo cáo kịch bản cá nhân hóa |
| Review đồng bộ ECG–PPG, offset/jitter/drift/mất gói | Đức Anh; Linh hỗ trợ replay | Schema version, session/channel, sequence, timestamp và đơn vị/ý nghĩa lấy mẫu–FIFO–nhận gói, sample count, fs từng kênh, clock chung/ánh xạ clock; fixture/config/seed/replay và expected results | Chạy replay, kiểm tra gaps/clock/timestamp, ghi lỗi và review; chưa thay kiểm thử thiết bị thật |
| PAT trên dữ liệu dự án | Đức Anh/Linh theo nguồn | Waveform được phép dùng, ánh xạ kênh/fs/đơn vị/căn chỉnh xác minh, timestamp/gaps và quy tắc R peak/foot/ghép nhịp được review | Kiểm tra tín hiệu và minh họa PAT từ R đến foot; không gọi PAT là PTT |
| Đánh giá thiết bị thật | Đức Anh; nhóm/giảng viên | Phần cứng bring-up, cấu hình/raw manifest/checksum/log, an toàn/phê duyệt cần thiết; nhãn cuff và event/session/clock khi phân tích BP | Review bản ghi và thực hiện protocol được duyệt, ghi kết quả thiết bị riêng |
| Khóa phương pháp và review code | Linh/Huy/nhóm | Review code baseline/metrics; trọng số B0, calibration, SD báo cáo, định nghĩa beta, Bland–Altman đo lặp/CI, eligible/weighting coverage | Cập nhật quyết định trước thí nghiệm Tuần 4; không chọn bằng test set |

Không tạo split/calibration/fixture/waveform thay thế để đánh dấu các mục trên
hoàn thành. Không chạy bootstrap, kiểm định đầy đủ, train model hoặc đánh giá
ΔBP thật của Tuần 4. Không ghi đạt G1 hoặc hoàn thành cả Tuần 3.

---

## 8. Các vấn đề cần nhóm và giảng viên xác nhận

> [!IMPORTANT]
> **Checklist lấy ý kiến thống nhất:**
> - [ ] **Linh:** Review code baseline/metrics, manifest/split, đơn vị quan sát và trọng số nhãn train B0.
> - [ ] **Linh/Huy/nhóm:** Xác nhận nguồn, chronology, quyền dùng nhãn và quy tắc tách/tổng hợp calibration B1 trước evaluation.
> - [ ] **Đức Anh/Linh/Huy:** Khóa schema/clock/timestamp, fs từng kênh và bằng chứng replay; giữ riêng kết quả mô phỏng và thiết bị thật.
> - [ ] **Nhóm/giảng viên:** Review SD cho báo cáo chính, định nghĩa beta, Bland–Altman đo lặp/CI, eligible/weighting của coverage trước phân tích thật.
> - [ ] **Nhóm/giảng viên:** Xác nhận tiêu chí/lịch G1 và điều kiện an toàn/phê duyệt cần thiết; chưa ghi đạt G1 khi thiếu bằng chứng.

Các nội dung trên còn chờ xác nhận, không được lựa chọn/tuning bằng test set hoặc coi là quyết định khoa học đã phê duyệt.

---

## 9. Kế hoạch chuyển giao sang Tuần 4

1. Bàn giao module B0/B1, validation, metrics, test, demo và tài liệu API cho Linh review/tích hợp.
2. Khi nhận đủ manifest/split và quy tắc quan sát, xác minh nguồn/ID/đơn vị rồi fit B0 chỉ trên train.
3. Chỉ chạy B1 công khai sau khi có calibration riêng, không trùng và trước evaluation theo thời gian đã xác minh.
4. Nhận fixture/waveform và thông tin clock/fs của Đức Anh để review replay, đồng bộ và chuẩn bị kiểm tra PAT khi đủ điều kiện.
5. Khóa phương pháp trước phân tích thật; bootstrap/kiểm định đầy đủ và kết quả thiết bị vẫn thuộc phần chưa thực hiện, không thay bằng demo giả lập.

### Hướng dẫn chạy lại đầu ra đã bàn giao

```powershell
.\.venv\Scripts\python.exe scripts/demo_week_03_baselines.py
.\.venv\Scripts\python.exe -m scripts.demo_week_03_baselines
.\.venv\Scripts\python.exe -m pytest -q tests/test_week_03_baselines.py tests/test_bp_metrics.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/check_environment.py
.\.venv\Scripts\python.exe -m pip check
git diff --check
```

Thực hiện từ `D:\ppg-ecg-blood-pressure`; dùng interpreter môi trường hiện có
hoặc Python 3.11 đã cài theo README. Trong sandbox, full pytest có thể cần quyền
truy cập Temp; lần chạy thực tế ở trên đã xử lý bằng approval cho lệnh pytest,
không sửa test reader để che lỗi hạ tầng. Danh sách test riêng chỉ chạy phần mới.
