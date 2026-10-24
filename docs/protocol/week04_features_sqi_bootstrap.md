# Tuần 4 — giao diện đặc trưng, SQI và bootstrap người

Version hiện tại: `features-sqi-v1` (đổi quy tắc đếm nhịp không ghép ở biên, mục 3).

Huy, 2026-10-13. Kiểm tra bằng fixture SYNTHETIC.
Không phải phương pháp đã khóa trên dữ liệu công khai.
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
Pipeline chỉ lấy cột theo `FEATURE_NAMES`; không đưa metadata/SQI vào model một cách
ngầm định. Nếu impute/scaling cần fit, chỉ fit trên train; quy tắc missing và
lọc SQI phải khóa trước test. Có thể dùng PPG feature khi PAT chưa khả dụng.
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
Tuần 5 thêm phương pháp ứng viên chọn qua `SignalConfig` (`r_method`,
`foot_method`), xem [week05_fiducials_pat_validity.md](week05_fiducials_pat_validity.md);
`features-sqi-v1` chỉ nhận phương pháp mặc định và output không đổi.

Default `filter_mode=none`: không thêm lọc khi chưa biết xử lý upstream.
Tùy chọn `zero_phase` là Butterworth SOS forward–backward, band/order trong
config, kiểm tra Nyquist riêng từng kênh. Không có trễ nhóm hằng của lọc này,
nhưng có thể biến dạng foot và hiệu ứng biên; `edge_s` bỏ mốc sát biên và chưa
chứng minh loại hết artifact. **Độ lệch đã đo:** trên analytic fixture (foot
R + 200 ms, rise 160 ms), `zero_phase` với band mặc định 0,5–8 Hz làm foot trễ
khoảng **+5,7 ms** so với `none`, ở cả 125 Hz và 500 Hz; R không đổi. Vì độ lệch
không phụ thuộc fs, đây là hiệu ứng của lọc lên hình dạng xung, không phải lượng
tử hóa; với PPG thật, độ lệch phụ thuộc hình dạng xung và chưa được đo. Test
`test_zero_phase_foot_bias_is_morphological_not_sampling` ghi lại độ lệch này. Đây là xử lý offline trong cửa sổ hiện có, không
phải bộ lọc causal triển khai firmware. Không dùng mẫu ngoài cửa sổ hoặc sau mốc cuff.

Ghép forward R→foot trong `pat_min_s..pat_max_s`, trước R tiếp theo; yêu cầu
một foot ứng viên và một R owner, từ chối mơ hồ. R/foot phải hữu hạn tăng nghiêm
ngặt. Nhịp mất không ghép sang nhịp sau; báo số R/foot không ghép.

Từ `features-sqi-v1` (2026-10-20), R hoặc foot không ghép chỉ bị đếm vào
`pat_unmatched_r_count`/`pat_unmatched_foot_count` và gây cờ `pat:unmatched_beats`
khi **toàn bộ** vùng tìm partner nằm trong đoạn kênh kia phát hiện được mốc. Với R
tại `r`, vùng đó là `[r + pat_min_s, r + pat_max_s]`, cần nằm trong
`[t0_PPG + edge_s, t_end_PPG - edge_s - foot_lookback_s]`; khoảng
`foot_lookback_s` ở cuối vì peak nằm sau foot tối đa chừng đó. Với foot tại `f`,
vùng `[f - pat_max_s, f - pat_min_s]` cần nằm trong `[t0_ECG + edge_s, t_end_ECG - edge_s]`.
Nhịp không ghép vì sát biên được đếm riêng ở `pat_edge_unpaired_r_count` /
`pat_edge_unpaired_foot_count`. Ở v0, `peaks()` cắt mép từng kênh độc lập nên
89/200 cửa sổ 10 s sạch có pha nhịp ngẫu nhiên bị gắn cờ nhầm; v1 cho 0/200.

PAT = R→foot,
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

**`features-sqi-v2` (2026-10-24):** chọn bằng `extract_window(..., version=
"features-sqi-v2")`; mặc định vẫn là v1, giữ đúng từng byte. Khác v1 đúng một điểm:
khi không ghép PAT vì timing chưa kiểm (`alignment_unverified`, `clock_unverified`,
`upstream_delay_unknown`, mặc định với PulseDB), v1 ghi `pat_pair_count` = 0,
`pat_pair_fraction` = 0.0 và đếm mọi nhịp là không ghép, nên dễ bị đọc nhầm là tín
hiệu xấu. v2 ghi `None` cho sáu trường đó (`pat_pair_count`,
`pat_unmatched_r_count`, `pat_unmatched_foot_count`, `pat_edge_unpaired_r_count`,
`pat_edge_unpaired_foot_count`, `pat_pair_fraction`) và lý do ở
`quality["pat_quality_unavailable"]` (`None` khi đã ghép). Đặc trưng và cờ giống v1.
Dùng v2 cho mọi nơi đọc các trường chất lượng PAT.

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
Ít hơn 2 người: giữ point metric, CI N/A và `insufficient_subjects`. Từ 2 tới dưới
`few_subjects` người (mặc định 10, quy ước ngày 2026-10-24, không phải ngưỡng suy
ra): vẫn tính CI nhưng `status` = `few_subjects`, vì bootstrap theo cụm với ít cụm
thường cho CI hẹp hơn độ phủ danh nghĩa; diễn giải các CI này là mô tả. Replicates thiếu SD được đếm, phân phối hằng
gắn `degenerate`; không coi CI hằng là bằng chứng chắc chắn trên quần thể.

**So sánh ghép cặp (thêm 2026-10-23):** `bootstrap_bp(..., contrasts=[(A, B)])`
trả thêm `contrasts`, mỗi phần tử có `model`, `reference`, `point` và `ci` của hiệu
A − B cho `subject_balanced_mae` và `sample_weighted_mae` theo từng huyết áp. Hiệu
được lấy **trong từng lượt** từ cùng draw, rồi mới lấy percentile; không trừ đầu
mút của hai CI riêng, và không kết luận từ việc hai CI riêng chồng nhau hay không.
Hiệu MAE âm nghĩa là A sai số thấp hơn B. Hiệu của MAE trung bình đều theo người
bằng trung bình theo người của MAE_s(A) − MAE_s(B), tức đại lượng $d_s$ của
[RQ](../research_questions_v0.1.md) khi A là PPG + PAT và B là PPG-only. Không
truyền `contrasts` thì output giữ nguyên như trước.

`evaluate_prediction_table(manifest, inventory, predictions, split='val')`
gọi validator v2 rồi join theo sample_id, kiểm tra đúng subject/split, số dòng,
không trùng/mất/thêm ID và cùng tập cho các model. Prediction table có đúng:
`sample_id, subject_id, split, model, pred_sbp, pred_dbp`. Không nhận nhãn từ
prediction table; reference lấy từ manifest được inventory kiểm tra.
Từ 2026-10-24 API chỉ nhận `split='val'`: đánh giá test bị từ chối ở đây và phải đi
qua một script riêng đòi file khóa (model, config, phiên bản đặc trưng, ngưỡng, ngày)
đã commit trước khi chạy. Nguồn/quyền dùng/pool, raw hash và chronology/calibration
vẫn là trách nhiệm caller; API không đủ metadata để xác nhận B1 hợp lệ.
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
CSV và JSON được ghi với LF; `config_sha256` và `code_sha256` tính trên nội dung
đã đổi CRLF thành LF (như blob trong Git), nên checkout Windows và Linux cho cùng
hash. File `reports/weekly/week_04/fixture_checks.json` (commit vào `14aa817`) là
kết quả chạy `features-sqi-v0` trên working tree chưa commit (ghi `commit`
`8472721`, `dirty: true`), được giữ làm bản ghi lịch sử; các hash trong đó tính
trên byte CRLF của máy chạy nên không tái tạo được từ blob Git.

**Sửa ngày 2026-10-13:** validation số thực từ chối bool/string/array
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