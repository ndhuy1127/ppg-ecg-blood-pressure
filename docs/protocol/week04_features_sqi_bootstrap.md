# Tuần 4 — giao diện đặc trưng, SQI v0 và bootstrap người

Huy, 2026-10-13. **Triển khai sơ bộ, kiểm tra bằng fixture SYNTHETIC; chờ
review của Linh/Đức Anh.** Không phải phương pháp đã khóa trên dữ liệu công khai.
Không thay protocol, split, calibration hoặc chính sách raw.

## 1. Giao diện bàn giao

Mã trong `software/signal_processing/fiducials.py`,
`software/feature_extraction/week04.py` và
`software/evaluation/subject_bootstrap.py`.
Config: `configs/data/week04_huy.json`.

`Channel` nhận vector số thực, `fs_hz` riêng từng kênh, `unit`, `clock_id`,
`start_s` hoặc vector timestamp với đơn vị `s/ms/us`. Timestamp là **thời gian
lấy mẫu**, không phải thời gian nhận gói/FIFO. `processing_delay_s=None` nghĩa là
chưa biết độ trễ upstream và chặn PAT; `0` chỉ dùng khi có căn cứ không trễ.
Độ trễ hằng đã biết được trừ khỏi thời gian. Clock phải cùng quy chiếu;
`alignment_verified=True` cần `alignment_basis` có bằng chứng. API không tự
chứng nhận khai báo đồng bộ và không suy clock offset từ PAT.

`SignalWindow(metadata, ecg, ppg, alignment_verified, alignment_basis)` giữ
sample/subject/source/checksum/raw_index/split và ID/hash tùy chọn. Các trường
ID/provenance **không phải feature**. `from_pulse_segment()` chỉ đọc subject,
ECG và PPG của reader hiện có; caller cung cấp metadata từng kênh rõ ràng. Không
đọc ABP, SBP/DBP, tuổi/giới hoặc thông tin tương lai. Không đổi reader/manifest v2.

`extract_window(window, SignalConfig)` trả dict: metadata, features,
missing_reasons, quality, flags, unavailable, fiducials và processing.
`extract_windows(windows, config)` giữ thứ tự, đúng một dòng/đầu vào và trả
summary; từ chối sample_id trùng. Không tự loại dòng hoặc sửa raw.

## 2. Bộ đặc trưng tối thiểu

Mọi đặc trưng tính trên cửa sổ được caller bàn giao, không tự chọn cửa sổ bằng
nhãn. Đặc trưng theo nhịp lấy median nhịp hợp lệ trong cửa sổ.

| Tên | Định nghĩa / đơn vị | Điều kiện |
| --- | --- | --- |
| `ppg_std` | SD `ddof=0` của PPG đã xử lý; đơn vị PPG khai báo | PPG hữu hạn, không phẳng, thời gian hợp lệ |
| `ppg_amplitude_median` | Median peak trừ valley trước peak; đơn vị PPG | Ít nhất `min_beats` foot hợp lệ |
| `ppg_rise_time_median_ms` | Median thời gian peak trừ foot tiếp tuyến, ms | Như trên |
| `ppg_width50_median_ms` | Median khoảng hai lần qua mức valley + amplitude/2; nội suy tuyến tính, ms | Có sườn lên/xuống đầy đủ; nhịp thiếu sườn không đóng góp |
| `ppg_hr_bpm` | 60 / median khoảng foot liên tiếp, bpm | Ít nhất `min_beats` foot |
| `ecg_hr_bpm` | 60 / median RR, bpm | Ít nhất `min_beats` R candidate |
| `pat_median_ms` | Median `(PPG foot - ECG R) * 1000`, ms | Đồng bộ/độ trễ có căn cứ và đủ cặp duy nhất |
| `pat_iqr_ms` | Percentile 75 trừ 25 của PAT nhịp, ms | Như trên |

Giá trị thiếu là Python `None` / JSON `null` / ô CSV rỗng, **không phải 0**.
HR luôn cần ít nhất hai mốc và đủ `min_beats`; đặt `min_beats=1` không cho phép
tính HR từ một nhịp. Mọi feature là số hữu hạn hoặc None. `missing_reasons`
theo từng feature: RR/foot intervals, chất lượng kênh, pulse half-height đầy đủ
hoặc timing/PAT; không gán cờ PAT vào feature PPG-only.
Linh chỉ lấy cột theo `FEATURE_NAMES`; không đưa metadata/SQI vào model một cách
ngầm định. Nếu impute/scaling cần fit, chỉ fit trên train; quy tắc missing và
lọc SQI phải review/khóa trước test. Có thể dùng PPG feature khi PAT chưa khả dụng.
`ppg_feature_segments` trong summary nghĩa là tính được `ppg_hr_bpm`, không có
nghĩa mọi cột đều đầy đủ hay mọi đoạn đã được chấp nhận.

## 3. Mốc và xử lý tín hiệu

R v0 dùng local maxima với prominence tương đối dải tín hiệu, refractory và
cực tính khai báo. Đây là detector đơn giản cho kiểm tra ban đầu, **không gọi là
Pan–Tompkins đã triển khai**; đề xuất Pan–Tompkins ở Tuần 1 chưa được nghiệm thu.
PPG peak dùng cùng cơ chế; foot là giao điểm tiếp tuyến tại maximum upslope với
mức valley trước peak. Valley được tìm trong `foot_lookback_s` **và sau peak PPG
liền trước**; nếu không có giới hạn này, ở HR cao (RR < `foot_lookback_s`) hai
nhịp có thể dùng chung một valley, foot bị lệch hoặc trùng nhau và `pair_pat` báo
lỗi cho cả batch (đã sửa ngày 2026-10-14, có test hồi quy RR 0,42 s).
Foot được nội suy dưới một sample; **R-peak thì không**, nên PAT có sai số lượng
tử khoảng ±1/fs của ECG (±2 ms ở 500 Hz).
Prominence tính theo `prominence_fraction × peak-to-peak` của cả cửa sổ. Với
`filter_mode=none`, trôi đường nền lớn có thể làm prominence vượt biên độ xung
và không phát hiện được peak nào (gắn cờ `too_few_peaks`, không crash).
Không mở khảo sát nhiều detector; chưa xác nhận độ nhạy/PPV trên ECG thật.

Default `filter_mode=none`: không thêm lọc khi chưa biết xử lý upstream.
Tùy chọn `zero_phase` là Butterworth SOS forward–backward, band/order trong
config, kiểm tra Nyquist riêng từng kênh. Không có trễ nhóm hằng của lọc này,
nhưng có thể biến dạng foot và hiệu ứng biên; `edge_s` bỏ mốc sát biên và chưa
chứng minh loại hết artifact. Đây là xử lý offline trong cửa sổ hiện có, không
phải bộ lọc causal triển khai firmware. Không dùng mẫu ngoài cửa sổ hoặc sau mốc cuff.

Ghép forward R→foot trong `pat_min_s..pat_max_s`, trước R tiếp theo; yêu cầu
một foot ứng viên và một R owner, từ chối mơ hồ. R/foot phải hữu hạn tăng nghiêm
ngặt. Nhịp mất không ghép sang nhịp sau; báo số R/foot không ghép. PAT = R→foot,
không phải PTT; cách viết gọn PAT = PEP + PTT giữ giới hạn mốc Q/R ở glossary.

NaN/Inf, rỗng, phẳng, timestamp sai, gaps hoặc sampling không khớp: gắn cờ và
không phát hiện nhịp trên cả kênh bị lỗi. Đây là xử lý bảo thủ v0, không nội suy
qua gaps hay chia đoạn âm thầm. Không sửa/xóa raw; không resample hai kênh.

## 4. SQI và ngưỡng sơ bộ

Config chứa: `flat_std` (đơn vị kênh), `min_beats`, refractory/lookback/edge (s),
prominence fraction (tỷ lệ peak prominence / peak-to-peak), PAT bounds (s),
`gap_factor` (ngưỡng dt / nominal dt), shape correlation (-1..1), polarity/band/order.
Sampling inconsistency dùng `sampling_rtol=0.05` và `sampling_atol_s=1e-6` trong config;
đây là kiểm tra giao diện, không tiêu chuẩn đồng bộ thiết bị.
Các ngưỡng là đề xuất kỹ thuật **chưa kiểm chứng/khóa**, không chọn bằng test/BP.

Quality: finite fraction, SD kênh, số peak/foot/pair, tỷ lệ ghép và số mốc
không ghép. Shape SQI: nội suy mỗi chu kỳ foot→foot vào 64 điểm, z-normalize,
tính median Pearson correlation với median template trong chính cửa sổ;
cần ít nhất hai chu kỳ không phẳng. Không có template học từ test/train chung.
`flagged` là có bất kỳ cờ, **không phải quyết định loại tự động**; cờ PAT có thể
không chặn PPG-only. Motion/ADC saturation/AC–DC đều N/A do thiếu bằng chứng đầu vào.

## 5. Bootstrap và prediction

`bootstrap_bp(reference, {model: predictions}, subject_ids, BootstrapConfig)`
kế thừa `evaluate_bp`. Cột BP `[SBP, DBP]`, mmHg, sai số prediction-reference.
MAE/bias chính trung bình đều các người; MAE/bias theo dòng là phụ.
SD chung theo mọi dòng, `ddof=1`; **không trung bình SD từng người**.
Caller phải tổng hợp cửa sổ cùng cuff event trước, không tạo nhiều nhãn độc lập.

Mỗi lượt lấy N người có hoàn lại và giữ toàn bộ dòng của từng người. ID bootstrap
được tạo riêng cho **mỗi lần lấy**, để A,A,B vẫn có ba cluster occurrences,
không gộp A sau lấy mẫu. RNG seed 20261013, 2000 lượt, percentile 2.5/97.5.
Mọi model dùng cùng draws. Không fit lại model; CI chỉ mô tả uncertainty theo
người của predictions đã có, không chứng minh CI nominal coverage.
Ít hơn 2 người: giữ point metric, CI N/A và `insufficient_subjects`; quá ít người
dù >=2 vẫn cần cảnh báo diễn giải. Replicates thiếu SD được đếm, phân phối hằng
gắn `degenerate`; không coi CI hằng là bằng chứng chắc chắn trên quần thể.

`evaluate_prediction_table(manifest, inventory, predictions, split='val')`
gọi validator v2 rồi join theo sample_id, kiểm tra đúng subject/split, số dòng,
không trùng/mất/thêm ID và cùng tập cho các model. Prediction table có đúng:
`sample_id, subject_id, split, model, pred_sbp, pred_dbp`. Không nhận nhãn từ
prediction table; reference lấy từ manifest được inventory kiểm tra.
Nguồn/quyền dùng/pool, raw hash, chronology/calibration và khóa test vẫn là
trách nhiệm caller/reviewer; API không đủ metadata để xác nhận B1 hợp lệ.
Beta/r ΔBP không triển khai khi chưa có định nghĩa/metadata phù hợp.

## 6. Ví dụ tích hợp và tái chạy

```python
import json
from pathlib import Path
from software.signal_processing.fiducials import SignalConfig
from software.feature_extraction.week04 import from_pulse_segment, extract_windows
from software.evaluation.subject_bootstrap import BootstrapConfig, evaluate_prediction_table

config = json.loads(Path("configs/data/week04_huy.json").read_text())
# segment/row/channel metadata do reader + manifest/config upstream bàn giao.
def features_for_segment(segment, row, ecg_metadata, ppg_metadata):
    window = from_pulse_segment(segment, row, ecg_metadata, ppg_metadata)
    return extract_windows([window], SignalConfig(**config["signal"]))

def evaluate_predictions(manifest, inventory, predictions):
    return evaluate_prediction_table(manifest, inventory, predictions,
        config=BootstrapConfig(**config["bootstrap"]))
```

Adapter mặc định chặn PAT tới khi caller cung cấp alignment evidence; không đặt
True chỉ để có feature. Runner fixture không tải/đọc dataset:

```powershell
& '.venv/Scripts/python.exe' 'scripts/demo_week04_huy.py'
& '.venv/Scripts/python.exe' -m pytest -q 'tests/test_week04_features.py' 'tests/test_subject_bootstrap.py'
```

Runner sinh JSON, CSV fixture và SVG theo đường dẫn báo cáo Tuần 4, ghi raw fixture/
config/code/figure/table SHA256, seed, commit và dirty. Đường dẫn `--output`,
`--figure` có thể đổi; runner chủ động tạo lại output được chỉ định, không dùng
cho raw. Khác với các runner khác trong `scripts/` (từ chối ghi đè), runner này
**ghi đè** output mặc định trong `reports/`; muốn giữ bản cũ thì truyền
`--output`/`--figure` tới thư mục mới. SVG được lưu không kèm ngày giờ và với
`svg.hashsalt` cố định, nên `figure_sha256` giống nhau giữa các lần chạy trong
cùng môi trường. Không đưa bảng fixture vào bảng baseline công khai.

**Sửa sau review ngày 2026-10-13:** validation số thực từ chối bool/string/array
và trả ValueError; ID/clock không nhận edge whitespace, alignment_basis phải là
chuỗi. Config và ngưỡng mặc định không đổi. Fixture có `fixture_input_provenance`
cho từng case: hash waveform canonical little-endian float64 theo kênh/shape,
hash metadata fs/unit/clock/start/timestamps/delay/alignment và hash input tổng
hợp (`analytic-fixture-input-v2`). `source_sha256` trong fixture synthetic là
hash input tổng hợp có ghi `hash_kind`, **không phải checksum file raw công khai**.
Metadata timing khác nhau cho hash input khác nhau dù waveform giống nhau.

Test lọc zero-phase kiểm tra R trong một sample ECG, foot/PAT trong hai sample
PPG trên analytic fixture, cửa sổ quá ngắn và loại mốc sát biên. Đây là tolerance
regression theo độ phân giải fixture, không phải tiêu chí y tế/đồng bộ thiết bị;
không đổi filter/SQI để đạt test. Vẫn chưa xác nhận timing trên PulseDB thật.

Nguồn nội bộ đã đối chiếu: glossary Tuần 2, kế hoạch Tuần 4, reader và
`docs/pulsedb_provenance.md` (ghi ECG_F/PPG_F).
Không suy ra đơn vị vật lý hoặc độ trễ từ shape 1250. Chưa audit lại nguồn
upstream hoặc có raw phiên bản cụ thể để xác minh xử lý/căn chỉnh của file nhóm dùng.