# Báo cáo tiến độ Tuần 4 — phần Huy

> **Giai đoạn:** Tuần 4 / 28 tuần
>
> **Người tổng hợp:** Nguyễn Đức Huy
>
> **Ngày cập nhật:** 2026-10-13
>
> **Nhánh/commit nền:** dev/huy @ 8472721; thay đổi Tuần 4 chưa commit
>
> **Trạng thái:** Hoàn thiện phần mềm độc lập và kiểm tra fixture; chưa nghiệm thu
> dữ liệu công khai, thiết bị thật, CI Python 3.11 hoặc toàn bộ G1.

## 1. Mục tiêu và phạm vi

Kế thừa kế hoạch tại `docs/plans/WEEK_04.md`:
đặc trưng v0, kiểm tra mốc R/foot/PAT, SQI v0, bootstrap theo người và bàn giao
đánh giá baseline. Không triển khai lại B0/B1/metrics, không làm thay B3 hoặc
schematic/PCB của thành viên khác. Git sạch trước khi bắt đầu; giữ nguyên
reader/manifest và mọi đầu ra lịch sử. Không commit/push/merge/tạo PR.

## 2. Việc đã làm

- Triển khai 8 đặc trưng PPG/HR/PAT với tên, công thức, đơn vị, điều kiện,
  missing và provenance. Nhãn/ABP không tham gia trích đặc trưng hoặc SQI.
- Detector R sơ bộ dùng prominence/refractory, foot tiếp tuyến maximum
  upslope, ghép nhịp forward duy nhất; không giả nhận là Pan–Tompkins.
- Hỗ trợ fs riêng từng kênh, timestamp s/ms/us, clock/alignment evidence,
  độ trễ upstream; PAT thiếu không trở thành 0. Không dùng PAT suy clock offset.
- SQI finite/phẳng/nhịp/shape/ghép PAT, trả cờ/lý do và thống kê; không tự loại
  hoặc sửa raw. Motion/saturation/AC–DC chưa khả dụng vì thiếu IMU/ADC/DC thật.
- Bootstrap CI percentile 95%, seed 20261013, 2000 lượt, giữ cụm người và
  toàn bộ quan sát; người lấy lặp có cluster occurrence riêng. Cùng draws cho
  các model. MAE/bias chính cân bằng theo người; SD chung `ddof=1`.
- Prediction API kiểm tra inventory/manifest v2, exact sample ID/subject/split,
  thiếu/thừa/trùng dòng, cùng tập quan sát và nhãn lấy từ manifest.
- Test reader adapter không đọc ABP/nhãn; test B0/B1/metrics cũ qua bootstrap.
- Sinh JSON/CSV và SVG từ fixture analytic có đáp án, lưu config/code/input/
  figure/table hash, commit nền và dirty. Đã có tài liệu ví dụ bàn giao.

## 3. File đầu ra

Đường dẫn tính từ thư mục gốc của repo:

| Sản phẩm | Đường dẫn |
| --- | --- |
| Mốc/kiểm tra thời gian | `software/signal_processing/fiducials.py` |
| Đặc trưng/SQI/reader adapter | `software/feature_extraction/week04.py` |
| Bootstrap/prediction evaluation | `software/evaluation/subject_bootstrap.py` |
| Config ngưỡng sơ bộ và bootstrap | `configs/data/week04_huy.json` |
| Định nghĩa/API/ví dụ/giới hạn | `docs/protocol/week04_features_sqi_bootstrap.md` |
| Runner analytic fixture | `scripts/demo_week04_huy.py` |
| Test mới | `tests/test_week04_features.py`, `tests/test_subject_bootstrap.py` |
| JSON kiểm tra fixture | `reports/weekly/week_04/fixture_checks.json` |
| Bảng feature fixture, không phải baseline công khai | `reports/weekly/week_04/fixture_features.csv` |
| Hình R/foot/cặp PAT fixture | `reports/figures/week04_synthetic_fiducials.svg` |
| Log xác minh cuối | `reports/weekly/week_04/verification.txt` |

## 4. Kết quả kiểm tra và môi trường

Đã chạy từ Git root bằng `.venv/Scripts/python.exe`:

| Lệnh / kiểm tra | Kết quả cuối |
| --- | --- |
| `python -B -m pytest -q -p no:cacheprovider` | **257 passed in 5.69s**, exit 0; gồm 58 test Tuần 4 |
| `python -m ruff check .` | exit 0, không có cảnh báo |
| `python scripts/check_environment.py` | exit 0 |
| `python -m pip check` | exit 0, No broken requirements found |
| `python scripts/demo_week04_huy.py` | exit 0, JSON/CSV/SVG đã sinh |
| `git diff --check` | exit 0; kiểm tra whitespace file mới bổ sung riêng ở log |

Môi trường thực: Python **3.13.12**, NumPy 2.5.3, SciPy 1.18.1, pandas 3.0.6,
matplotlib 3.11.2, scikit-learn 1.9.1, PyYAML 6.0.3. Khác Python 3.11 và
dependency pins của repo; **chưa thay CI hoặc xác nhận tương thích môi trường
chính thức**. Không tìm thấy Python khác qua launcher `py -0p`; không cài/thay
môi trường ngoài phạm vi. Log lưu cả exit code, không dựa exit status của tool
wrapper bị lỗi capture terminal.

Trong quá trình bổ sung test shape có một assertion không đúng: median
correlation có thể không gắn cờ minority outlier khi đa số chu kỳ giống template.
Đã sửa fixture để kiểm tra hai chu kỳ thực sự khác nhau, **không đổi ngưỡng
config theo test**. Suite cuối đạt. Giới hạn detector/SQI này được giữ rõ.

Test bao phủ mốc/PAT đã biết, fs 250/125 và 512/128, cực tính, delay/timestamp
units/gaps/invalid timestamp, missing/phẳng/NaN/Inf, nhịp thiếu, ambiguous PAT,
shape và số nhịp không đủ; bootstrap multiplicity/seed/degenerate/ít người,
prediction mismatch và compatibility baseline/reader/manifest/metrics.

**Bản sửa sau review 2026-10-13:** chặn HR một nhịp thành NaN, bảo đảm mọi
feature hữu hạn hoặc None; missing reason theo feature; validation config và
metadata trả ValueError cho kiểu không hợp lệ/bool/edge whitespace. Bổ sung
hash fixture waveform/metadata timing/input tổng thể, không đánh đồng với raw
file checksum. Thêm 23 test cho các hành vi trên và timing/biên/short-window
của lọc zero-phase. Regenerate JSON/CSV/SVG, giữ nguyên ngưỡng/config khoa học.
Python 3.11 chưa chạy được: `py -0p` không thấy interpreter đăng ký;
`Get-Command python,python3.11` chỉ thấy Python 3.13. Không cài môi trường mới.

**Bản sửa ngày 2026-10-14:**

- **Lỗi detector PPG foot ở HR cao:** khi RR ngắn hơn `foot_lookback_s` (0,5 s),
  cửa sổ tìm valley có thể lùi qua peak PPG trước đó, khiến hai nhịp dùng chung
  một valley. Hệ quả là foot bị lệch hoặc trùng; khi trùng, `pair_pat` báo lỗi
  và `extract_windows` dừng cả batch thay vì gắn cờ một cửa sổ. Trên 3.000 cửa
  sổ giả lập ngẫu nhiên (RR 0,41–1,2 s), có 7 lần crash trước khi sửa và 0 lần
  sau khi sửa. Đã giới hạn valley nằm sau peak liền trước và thêm test hồi quy
  ở RR 0,42 s (test fail khi bỏ bản sửa).
- **Cờ thiếu:** `ppg:no_complete_half_height_pulse` trước đây chỉ có trong
  `missing_reasons`, nay được thêm cả vào `flags`.
- **Hash hình:** SVG trước đây chứa ngày giờ và ID ngẫu nhiên nên `figure_sha256`
  đổi sau mỗi lần chạy; nay lưu không kèm ngày giờ và với salt cố định.
- Kết quả sau sửa: `pytest -q -p no:cacheprovider` **258 passed**, `ruff check .`
  đạt. Đã chạy lại `scripts/demo_week04_huy.py`: bảng fixture và tóm tắt (5 đoạn,
  2 có đặc trưng PPG, 1 có PAT, 4 gắn cờ) không đổi; hash code và hình được cập
  nhật trong `fixture_checks.json`. `verification.txt` là log của lần chạy
  2026-10-13, giữ nguyên làm mốc lịch sử.

## 5. Fixture và dữ liệu công khai — không trộn kết quả

**Fixture SYNTHETIC:** R tại 1..8 s, chân PPG R+0.2 s, rise 160 ms,
width50 200 ms, HR 60 bpm. JSON/CSV ghi kết quả tính bằng mã; không phải
waveform sinh lý thật hoặc chứng minh độ chính xác trên người.
Runner xử lý 5 đoạn: 2 đoạn có feature PPG/HR, 1 đoạn có PAT, 4 đoạn gắn cờ
(PPG missing/phẳng/nonfinite và alignment chưa xác minh). Một đoạn có thể có
nhiều lý do; tổng số flags không phải số đoạn bị loại. Các đoạn vẫn được giữ.

**Công khai:** chỉ tìm thấy CSV manifest 1.000 đoạn lịch sử ở
`data/processed/linh_week03/pulsedb_manifest_1000.csv`
và metrics B0 cũ trong `runs/b0_pulsedb`.
Không có raw waveform/metadata timing hoặc inventory v2/prediction B3 hợp lệ
trong các đầu vào cục bộ đã kiểm tra. Không mở/in dữ liệu người; không tạo
timestamp hoặc inventory thay thế. Chưa chạy feature/PAT/SQI/CI trên PulseDB
Tuần 4, chưa có hình công khai. Kết quả B0 công khai Tuần 3 giữ tại báo cáo cũ,
không coi là lần chạy Tuần 4 hoặc tự nâng nghiệm thu nguồn/pool/split.

| Phân tích baseline công khai Tuần 4 | Trạng thái |
| --- | --- |
| B0/B3 cùng validation, MAE/bias/SD và CI | Chờ prediction, inventory/manifest và provenance Linh |
| B1 công khai | N/A: chưa có chronology/calibration hợp lệ được bàn giao |
| Beta/r ΔBP, phân tích theo thời gian | N/A: thiếu metadata/định nghĩa phù hợp |
| PAT công khai và tín hiệu thiết bị | N/A: chưa đủ raw/căn chỉnh/độ trễ kiểm chứng |

## 6. Bàn giao và phần còn chờ

**Linh có thể dùng ngay:** `extract_window`, `extract_windows`,
`from_pulse_segment`, `SignalConfig`, `BootstrapConfig`, `bootstrap_bp`,
`evaluate_prediction_table`; config, ví dụ và fixture output. Feature thiếu
giữ None; fit imputer/scaler chỉ train. SQI trả cờ để pipeline chọn qua config,
không có filtering mặc định. B0/B3 phải cùng tập/weighting/draws. Đơn vị cuff
event phải tổng hợp trước evaluation, không coi nhiều window là nhiều nhãn.

| Blocker / đầu vào cần nhận | Người bàn giao / review |
| --- | --- |
| Raw PulseDB được phép, version/checksum/pool/holdout, inventory v2/manifest, channel/fs/unit, upstream filter/delay/alignment đã xác minh; tập nhỏ train/val | Linh bàn giao, Huy review |
| Prediction B0/B3 có sample/subject/split/model/pred_sbp/pred_dbp, cùng eligible observations và config/log | Linh bàn giao, Huy chạy API và review |
| Calibration riêng trước evaluation, session/time/event/record độc lập và định nghĩa biến thiên | Linh–Huy/nhóm xác nhận trước B1/ΔBP |
| Clock/timestamp lấy mẫu–FIFO, fs/packet chính thức, delay/gaps và bản ghi hardware an toàn | Đức Anh bàn giao; Linh/Huy review |
| Ngưỡng/missing/SD/CI phương pháp và code review, CI Python 3.11 | Linh review code; Đức Anh review timing; nhóm review phương pháp |

## 7. Hạn chế và chuyển tiếp

Detector maxima v0 chưa kiểm chứng với QRS đảo cực/nhiễu/T-wave; foot phụ thuộc
morphology và lọc. Gaps làm chặn cả kênh theo xử lý bảo thủ. Shape median có thể
bỏ qua minority outlier. Flat threshold phụ thuộc đơn vị/scaling; ngưỡng chưa
khóa trên pilot/validation. Hai người là điều kiện tối thiểu tính CI, không
chứng minh đủ cỡ mẫu suy luận. API không tự xác nhận quyền dùng/clock/calibration
chỉ từ khai báo của caller. Cần review trước thí nghiệm và khóa test.

Phần độc lập có code/test/output; phần công khai và thiết bị **vẫn bị chặn**.
Không hoàn thành schematic/PCB/bring-up thay Đức Anh, không đánh dấu toàn bộ
Tuần 4 hoặc G1 đạt và không tuyên bố thiết bị y tế/thay cuff.