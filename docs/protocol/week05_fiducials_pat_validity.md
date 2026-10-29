# Tuần 5 — mốc R/foot thứ hai, PAT hợp lệ và so với đánh dấu tay

Huy, 2026-10-21; sửa ngày 2026-10-22 theo review độc lập; bốn quyết định ngày
2026-10-25 ở mục 8; kế hoạch đánh dấu tay và ngưỡng chấp nhận ngày 2026-10-25 ở
mục 9; các điểm chốt 2026-10-29 ở mục 3, 4, 7, 8, 9.1–9.4 và 9.6. Version config:
`fiducials-week05-v2` (v1 sáng 2026-10-25, v0 tới 2026-10-24), trạng thái
`NOT_TEST_TUNED`; file config giữ nguyên, kể cả câu `note` cũ (mục 9.1). Kết quả mới
chỉ có trên SYNTHETIC. Bộ đoạn PulseDB để đánh dấu đã được
xuất (mục 6), nhưng **chưa chạy `compare` hay `gate` trên mốc tay nào**. Không phải
phương pháp đã khóa.

Kế thừa [tài liệu Tuần 4](week04_features_sqi_bootstrap.md). PAT là khoảng
R → chân sóng PPG, không phải PTT. BP/ABP không là đầu vào của mốc, PAT hay SQI.

## 1. Mã và config

| Thành phần | Đường dẫn |
| --- | --- |
| Phương pháp mốc, chọn qua `SignalConfig` | `software/signal_processing/fiducials.py` (`R_METHODS`, `FOOT_METHODS`, `r_peaks`, `detect`) |
| PAT hợp lệ và outlier | `software/signal_processing/pat_validity.py` (`PatRules`, `pair_between_r`, `classify_pat`, `pat_beats`) |
| So với đánh dấu tay | `software/evaluation/fiducial_agreement.py` (`match_events`, `agreement`) |
| Ngưỡng chấp nhận và độ lặp lại (mục 9) | `software/evaluation/fiducial_gate.py` (`gate`, `repeatability`) |
| Script synth/export/plot/annotate/detect/compare/repeat/gate | `scripts/week05_fiducials.py` |
| Config và ghi chú nguồn | `configs/data/week05_huy.json` |
| Mẫu CSV đánh dấu tay (trống) | `docs/protocol/templates/manual_fiducials_template.csv` |
| Test | `tests/test_week05_fiducials.py`, `tests/test_fiducial_gate.py` |

## 2. Phương pháp ứng viên

**R peak** (`r_method`):

- `prominence` (mặc định, v0/v1): local maxima, prominence tương đối, refractory.
- `derivative_energy` (mới): bình phương sai phân bậc nhất, lấy trung bình trượt
  căn giữa rộng `r_energy_window_s` (0,1 s), tìm cực đại của đường bao với cùng
  refractory/prominence, rồi dời về cực đại tín hiệu trong ±1 cửa sổ. Ý tưởng
  đạo hàm + bình phương có trong Pan–Tompkins, nhưng **đây không phải
  Pan–Tompkins**: không có bộ lọc dải cố định, ngưỡng thích nghi hay search-back.
  Ngưỡng prominence của đường bao (`r_energy_threshold`, từ 2026-10-25):
  `quantile` = 0,2 × (Q95 − Q05) của năng lượng (mặc định), `ptp` = 0,2 × biên độ
  đỉnh-đỉnh (cách của v0, giữ để tái tạo kết quả cũ).

**PPG foot** (`foot_method`), cùng valley và peak như v1:

- `tangent` (mặc định): tiếp tuyến tại sườn lên dốc nhất cắt mức valley.
- `d2_max` (mới): cực đại sai phân bậc hai giữa valley và điểm dốc nhất.
- `valley_min` (mới): cực tiểu cuối trước sườn lên.

**Nội suy parabol dưới một mẫu** (`foot_interpolation`, **mặc định tắt** từ
2026-10-25, mục 8): khi bật, chỉ dời mốc ở cực trị chặt ba điểm (cực tiểu chặt của
tín hiệu cho `valley_min`, cực đại chặt của sai phân bậc hai cho `d2_max`; đoạn
phẳng không nội suy), tối đa nửa mẫu. Trước 2026-10-25, `d2_max` chỉ xét chiều cong
nên điểm argmax ở biên đoạn tìm vẫn có thể bị dời nửa mẫu. **Lý do tắt:** một góc
nhọn bất đối xứng (sườn xuống dốc, sườn lên thoải, như điểm bắt đầu xung SYNTHETIC)
vẫn là cực trị chặt nên bị nội suy, và nội suy làm sai số **tăng** ở cả hai phương
pháp (quét 101 pha onset, Codex 2026-10-25): `valley_min` 3,32 → 6,59 ms ở 125 Hz,
2,00 → 3,91 ms ở 200 Hz; `d2_max` 9,90 → 11,93 ms ở 125 Hz, 6,63 → 8,25 ms ở 200 Hz.
Trên cực trị trơn đối xứng thì nội suy giảm sai số (khoảng 2 ms xuống gần 0), nên
giữ làm tùy chọn để đối chứng; chốt cuối sau khi có đánh dấu tay.

`d2_max` và `valley_min` chưa có làm mượt; trên dữ liệu nhiễu kết quả kém hơn
`tangent` (mục 5). Nếu dùng thật cần lọc trước, và lựa chọn đó phải khóa trên train
(mục 9.1).

**Không đổi output mặc định của `features-sqi-v1`.** Mặc định vẫn là
`prominence` + `tangent`. Đã so ngày 2026-10-22 sau các sửa đổi:

- bảng đặc trưng fixture Tuần 4 tạo lại giống từng byte với blob đã commit
  (`232772f9…`) và với bản tạo từ HEAD sạch; file working copy chỉ khác ở CRLF;
- 240 cửa sổ SYNTHETIC × 2 config (6 cặp fs, có nhiễu, đảo cực, mất PPG, NaN,
  trôi nền) cho output giống hệt HEAD.

`extract_window` **từ chối** phương pháp khác mặc định thay vì ghi nhãn
`features-sqi-v1` cho output không phải v1. Muốn dùng phương pháp mới trong đặc
trưng phải chọn trên train trước (mục 9.1), rồi tăng version (ví dụ
`features-sqi-v2`) kèm lý do.

## 3. PAT hợp lệ

Một nhịp PAT hợp lệ khi đủ **tất cả**:

1. Clock chung hoặc ánh xạ clock đã kiểm, độ trễ upstream đã biết, alignment có
   căn cứ (như v1; không suy clock từ PAT).
2. Có R và foot, ghép bằng `pair_between_r` (khác `pair_pat` của v1):
   - Ứng viên của R là các foot sau R và trước R kế tiếp. R cuối nhìn tới một RR
     trước đó; chỉ có một R thì không giới hạn trên. Các khoảng không chồng nhau,
     nên một foot thuộc tối đa một R.
   - Một foot thì ghép, **bất kể PAT**. Nhiều foot thì chỉ ghép khi đúng một foot
     nằm trong giới hạn; ngược lại R được gắn `ambiguous`.
   - Không có foot: `no_foot`. Nhịp mất không ghép sang nhịp sau. Ngoại lệ
     (`pat-validity-v1`, 2026-10-23): nếu cửa sổ `[R + min_ms, R + max_ms]` không
     nằm trọn trong khoảng PPG phát hiện được foot (`foot_span`), R được gắn `edge`
     và không tính vào `n_unpaired_r`, như quy tắc nhịp sát biên của
     `features-sqi-v1`. `foot_span` là tham số bắt buộc, tính bằng
     `detectable_foot_span(ppg_times, edge_s, foot_lookback_s)` từ thời gian của
     PPG đã xử lý: bỏ `edge_s` ở đầu và `edge_s + foot_lookback_s` ở cuối, vì foot
     chỉ được tìm từ một đỉnh nằm sau nó tối đa `foot_lookback_s`. Không lấy
     khoảng này từ các foot đã tìm thấy. Truyền `None` thì không miễn trừ nhịp nào
     (hành vi của v0, khi đó R sát biên vẫn là `no_foot`). Nhịp `paired` và
     `ambiguous` không đổi nhãn.
   - Giới hạn 80–400 ms **không** dùng để loại khi ghép, nên PAT 450 ms hay 60 ms
     vẫn được ghép rồi gắn `out_of_range`. Trước 2026-10-22, `pat_beats` ghép bằng
     `pair_pat` với cùng giới hạn, nên các nhịp này biến mất thành "R không ghép"
     (lỗi review C1).
3. Trong giới hạn `[min_ms, max_ms]` = 80–400 ms (gồm hai biên, dung sai float
   `1e-6` ms), ngược lại là `out_of_range`.
4. Không phải outlier trong cửa sổ: với các nhịp trong giới hạn, outlier khi
   `|PAT − median| > max(mad_k · 1,4826 · MAD, mad_floor_ms)`, `mad_k = 3`,
   `mad_floor_ms = 10`. Chỉ áp khi có ít nhất `min_pairs = 3` nhịp trong giới hạn.

Nhịp không hợp lệ được **gắn nhãn, không xóa**:

- `pat_beats` trả `r_status` cho từng R (`paired`, `no_foot`, `ambiguous`,
  `edge`) cùng các số đếm; số R = `n_pairs` + `n_unpaired_r` + `n_edge`.
- `classify_pat` trả trạng thái từng cặp, số `out_of_range`/`outlier`, và
  `median_all_ms` (mọi cặp) cạnh `median_valid_ms`, để thấy quy tắc ảnh hưởng tới
  đâu.

Quy tắc không dùng giá trị BP; không loại dữ liệu vì BP cao/thấp. Chưa có script
nào gọi `pat_beats`; config `pat_validity` hiện được dùng trong test, và test
khóa các giá trị của nó bằng đúng bảng dưới.

**Nguồn của các con số** (ghi cả trong `sources` của config):

| Tham số | Giá trị | Nguồn |
| --- | --- | --- |
| Giới hạn PAT | 80–400 ms | **Chưa có nguồn**; cùng cửa sổ ghép của v1. Tham khảo: PAT ngón tay lúc nghỉ khoảng 180–260 ms (Mukkamala 2015, [10.1109/TBME.2015.2441951](https://doi.org/10.1109/TBME.2015.2441951), ma trận Tuần 1 #1); nguồn này không cho PAT cổ tay |
| Quy tắc MAD | median ± k · 1,4826 · MAD | Leys et al. 2013, [10.1016/j.jesp.2013.03.013](https://doi.org/10.1016/j.jesp.2013.03.013); mới đối chiếu metadata, chưa đọc toàn văn |
| `mad_k` | 3 | **Chưa có nguồn** cho giá trị; lựa chọn kỹ thuật |
| `mad_floor_ms` | 10 ms | **Chưa có nguồn**. Thêm ngày 2026-10-21 sau khi test SYNTHETIC cho thấy không có sàn thì PAT gần như hằng bị gắn outlier chỉ vì lượng tử hóa 1 mẫu (8 ms ở 125 Hz) |
| `refractory_s` (config Tuần 5) | 0,25 s, cho đỉnh R | **Chưa có nguồn**; để HR cao không bị refractory cắt. v1 (features-sqi) giữ 0,4 s cho cả hai kênh, nhưng ở ECG 512 Hz với RR 0,4 s (HR 150) chỉ còn 17/21 đỉnh R (Codex 2026-10-25) |
| `ppg_refractory_s` (config Tuần 5 v2) | 0,35 s, cho đỉnh PPG | Quyết định 2026-10-25 (mục 8), **chưa có nguồn**: chặn sóng phụ cách đỉnh tâm thu 0,30 s và vẫn dưới RR 0,4 s; sóng phụ ở +0,36 s vẫn lọt |
| `r_energy_threshold` | `quantile`, 0,2 × (Q95 − Q05) | Quyết định 2026-10-25 (mục 8); Q95/Q05 là lựa chọn kỹ thuật, **chưa có nguồn** |
| Dung sai so khớp | R 24 ms, foot 48 ms (3 và 6 mẫu ở 125 Hz) | Chốt ngày 2026-10-25, trước khi đánh dấu (mục 9); **chưa có nguồn**. v1 dùng 50/100 ms, mức đó từng tính sóng S trễ 30 ms là R đúng. Không đổi sau khi xem kết quả |

### 3.1. PulseDB: chế độ ghép R–foot riêng (chốt 2026-10-29, chưa có code)

Quy tắc ghép ở trên (`pair_between_r`, giới hạn 80–400 ms) **chỉ dùng cho dữ liệu
thiết bị**. Nó không dùng được nguyên trạng cho PulseDB:

- Trên 80 đoạn train đã xuất, R → foot kế tiếp có trung vị theo đoạn 572 ms (p10
  374, p90 632); 86% số đoạn trên 400 ms
  ([báo cáo Tuần 5](../../reports/weekly/week_05/README.md) mục 6.5;
  `derivative_energy` + `valley_min`, chưa thẩm định). PPG của PulseDB có vẻ trễ thêm
  khoảng 300 ms so với ECG ([provenance](../pulsedb_provenance.md) mục 6, nguồn thứ
  cấp).
- `pair_between_r` chỉ xét foot trước R kế tiếp; `pair_pat` của v1 cũng cắt ở R kế.
  Khi RR ngắn hơn khoảng 570 ms, foot của nhịp k rơi sau R(k+1) và bị ghép âm thầm
  với R(k+1), cho PAT ≈ 572 ms − RR. Giá trị đó có thể lọt 80–400 ms mà không bị gắn
  cờ.

Vì vậy PulseDB dùng một chế độ ghép riêng, version mới `pat-validity-pulsedb-v0`:

1. Cửa sổ R → foot cố định `[R + cận dưới, R + cận trên]`, **không cắt ở R kế
   tiếp**.
2. Trong cửa sổ phải có **đúng một** foot thì mới ghép. Nếu không (không có foot,
   hoặc từ hai foot trở lên), R được gắn cờ `ambiguous`.
3. Ghép một–một: một foot nằm trong cửa sổ của hai R trở lên thì không ghép với R
   nào, các R đó đều gắn `ambiguous`.
4. Hai cận lấy từ phân bố R → foot trên **train**. Chỉ ước lượng sau khi `gate` cho
   `B4_ALLOWED` và trước khi chấm B4 trên val. Con số chưa có. Cách lấy cận (phân vị
   nào) và tiêu chí "độ trễ ổn định giữa các ca" (ý 6) phải ghi ở đây, kèm ngày,
   trước lần ước lượng đó.
5. Báo tỉ lệ `ambiguous`.
6. Nếu không chứng minh được độ trễ ECG–PPG ổn định giữa các ca thì không làm B4
   trên PulseDB.

Khoảng 80–400 ms hiện hành chỉ dùng cho dữ liệu thiết bị. PAT trên PulseDB vẫn chỉ
là đặc trưng tương đối, kèm cờ `upstream_delay_unknown` (mục 9.5). Code chỉ viết khi
`gate` cho `B4_ALLOWED`, theo [kế hoạch Tuần 6](../plans/WEEK_06.md).
`pat-validity-v1` và `features-sqi-v1/v2` không đổi.

## 4. So với đánh dấu tay

Phương pháp mốc chỉ được chọn trên **train** (chốt 2026-10-25, mục 9.1); val và test
không bao giờ dùng để chọn mốc.

- `export` chỉ xuất train. Script từ chối bản ghi ngoài train/val, và `agreement`
  luôn từ chối test.
- Từ 2026-10-29, `agreement` (lệnh `compare`) còn từ chối split `val` khi mốc tham
  chiếu là đánh dấu tay (`reference_type = MANUAL`). Ngoại lệ duy nhất: bản ghi là
  output nguyên vẹn của `synth`, để tập đánh dấu. `detect` kiểm điều này bằng
  `synth.provenance.json` (hash `records.csv`) và ghi `records_from_synth`; chỉ sửa
  cột `source_type` thành SYNTHETIC thì không đủ. Không rõ nguồn thì coi là dữ liệu
  thật và bị từ chối. Đáp án SYNTHETIC (`--allow-synthetic-truth`) vẫn dùng được trên
  val để kiểm code.
- `gate` từ chối dòng so khớp không thuộc train, và export có `records.csv` không
  đúng split train của `review_plan`.

Quy trình:

1. Lấy bản ghi: `synth` (SYNTHETIC) hoặc `export` (tập nhỏ train của PulseDB,
   mục 6).
2. Đánh dấu **mù**: `annotate` mở từng bản ghi, nhấp trái trên trục ECG để thêm R,
   trên trục PPG để thêm foot, nhấp phải để xóa mốc gần nhất; đóng cửa sổ để sang
   bản ghi sau. Không hiển thị kết quả detector và không tự hút về đỉnh. Có thể
   dùng `plot` để in hình tĩnh (lưới 0,1 s) rồi điền tay vào mẫu CSV.
3. `detect` chạy mọi phương pháp, ghi một dòng đánh dấu đã chạy cho mỗi
   (bản ghi, phương pháp, mốc), để phân biệt "chạy mà không thấy" với "chưa chạy".
   Cạnh CSV có file `<out>.provenance.json`, ghi:
   - hash config và `signal_config` đã dùng;
   - hash `records.csv`;
   - lỗi kênh của từng phương pháp (`channel_issues`), để kênh bị loại không bị
     hiểu là "chạy mà không thấy";
   - hash output, git, phiên bản numpy/scipy/pandas/matplotlib và `source_type`.
4. `compare` tính cho từng phương pháp: TP/FP/FN, độ nhạy = TP/số mốc tay,
   PPV = TP/(TP + FP), bias/MAE/SD thời gian (tự động − tay, ms; SD `ddof=1`) trên
   cặp khớp.
   - **Ghép một–một:** tối đa số cặp trong dung sai, hòa thì lấy tổng |sai số| nhỏ
     nhất (quy hoạch động trên trục thời gian). Cách cũ ghép cặp gần nhất trước,
     có thể bỏ sót cặp.
   - **So biên:** dùng dung sai float `1e-9` s, nên lệch đúng bằng dung sai vẫn
     khớp.
   - **Vùng review:** mốc tay chỉ tính trong vùng. Detection nằm ngoài vùng không
     quá một dung sai vẫn được ghép với mốc sát mép, nhưng nếu không ghép thì
     không tính là FP. Nhờ vậy phương pháp có bias không bị phạt ở mép.
   - **Kiểm config:** `compare` từ chối khi thiếu provenance của `detect`, khi CSV
     detections đã đổi sau `detect`, hoặc khi config khác config `detect` đã dùng.
     Output chép provenance của `detect`.
   - **Kiểm nguồn đánh dấu (2026-10-23):** mốc tay phải được đánh trên đúng
     `records.csv` mà `detect` đã dùng. `compare` đọc `<annotations>.provenance.json`
     của `annotate`, hoặc với đáp án SYNTHETIC là `synth.provenance.json` cạnh
     `truth_synthetic.csv`, rồi kiểm hash của chính file đánh dấu và hash
     `records.csv`. File provenance có mà không khớp hoặc hỏng thì luôn bị từ
     chối. CSV điền tay theo mẫu (không có provenance) chỉ được so khi thêm
     `--annotations-without-provenance`; output ghi `annotation_provenance.kind =
     "none"`. Trước đó `compare` không kiểm điều này, nên mốc tay của bản ghi này có
     thể bị so với detection của bản ghi khác cùng `record_id`.
   - Kết quả gộp kèm bảng theo từng bản ghi, vì các nhịp trong một bản ghi không
     độc lập.

CSV đánh dấu tay theo mẫu: `record_id, split, fiducial (ecg_r|ppg_foot), time_s,
review_start_s, review_end_s, annotator, annotated_on, note`. Dòng có `time_s`
rỗng khai báo vùng đã xem mà không có mốc. **Script không bao giờ tự sinh nhãn
thủ công.**

- **Đáp án SYNTHETIC:** file đáp án ghi annotator
  `SYNTHETIC_GROUND_TRUTH_NOT_MANUAL`.
  - `agreement` và `compare` từ chối mọi annotator bắt đầu bằng `SYNTHETIC` (bỏ
    khoảng trắng, không phân biệt hoa thường) nếu không có
    `--allow-synthetic-truth`.
  - Trộn đáp án SYNTHETIC với mốc tay thì luôn bị từ chối.
  - Output ghi `reference_type`.
- **`annotate`:**
  - Từ chối tên bắt đầu bằng `SYNTHETIC`.
  - Kiểm `--out` và `<out>.provenance.json` **trước** khi mở cửa sổ đầu tiên.
  - Ghi từng bản ghi ngay khi đóng cửa sổ, nên một buổi đánh dấu không bị mất vì
    lỗi giữa chừng.
  - Click ngoài vùng review bị bỏ và được đếm trong provenance.
- **File đánh dấu trên PulseDB:** không commit (`subject_id` công khai nhưng vẫn
  là dữ liệu người); lưu cạnh output ngoài Git.

```powershell
.\.venv\Scripts\python.exe scripts\week05_fiducials.py synth --out tmp\w5\rec
.\.venv\Scripts\python.exe scripts\week05_fiducials.py plot --records tmp\w5\rec --out tmp\w5\fig
.\.venv\Scripts\python.exe scripts\week05_fiducials.py annotate --records tmp\w5\rec --out tmp\w5\manual.csv --annotator Huy --date 2026-10-21
.\.venv\Scripts\python.exe scripts\week05_fiducials.py detect --records tmp\w5\rec --out tmp\w5\det.csv
.\.venv\Scripts\python.exe scripts\week05_fiducials.py compare --annotations tmp\w5\manual.csv --detections tmp\w5\det.csv --out tmp\w5\agreement.json
```

Mọi lệnh từ chối ghi đè output có sẵn (kể cả file provenance đi kèm), và mỗi lệnh
ghi provenance:

| Lệnh | File provenance |
| --- | --- |
| `synth` | `synth.provenance.json`: version generator, case, hash output |
| `plot` | `plot.provenance.json` |
| `annotate`, `detect` | `<out>.provenance.json` |
| `export` | `export.json` (hash raw đầy đủ; từ 2026-10-23 hash thêm `reader.py`, `split_manifest.py`, `pipeline.py` và ghi phiên bản `mat73`, `h5py`) |
| `compare` | Trong JSON output (`annotation_provenance`, `detect_provenance`) |

`export` đặt `record_id = PDB_<12 ký tự đầu SHA-256 raw>_<split>_<raw_index>`
(từ 2026-10-23; trước đó không có phần hash), để bản ghi của hai file raw (hai
pool) không trùng ID.

## 5. Kết quả SYNTHETIC (chỉ kiểm chứng code)

### 5.1. Kết quả v1 (2026-10-25, sau các quyết định ở mục 8)

Generator `week05-synthetic-records-v1` (đỉnh T ở R + 0,28 × √RR, thêm bản ghi biên
`SYN_T_EDGE_HR60` với T ở R + 0,25 s, tổng 6 bản ghi), config `fiducials-week05-v1`
(R 0,25 s, PPG 0,35 s, không nội suy, ngưỡng năng lượng `quantile`), code commit
`034771d`. Output: `reports/weekly/week_05/synthetic_fiducials_v1/`.

| Mốc | Phương pháp | Mốc đúng | TP | FP | FN | Bias (ms) | MAE (ms) | SD (ms) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R | `derivative_energy` | 64 | 64 | 7 | 0 | −0,1 | 0,1 | 0,5 |
| R | `prominence` | 64 | 64 | 44 | 0 | −0,1 | 0,1 | 0,5 |
| foot | `tangent` | 63 | 63 | 0 | 0 | 27,4 | 27,4 | 10,7 |
| foot | `d2_max` | 63 | 59 | 4 | 4 | 6,8 | 13,0 | 20,4 |
| foot | `valley_min` | 63 | 57 | 6 | 6 | −1,3 | 2,7 | 13,1 |

Cách đọc (theo `per_record`):

- `prominence` ở refractory 0,25 s bắt đỉnh T ở **mọi** bản ghi HR 60 (9 FP mỗi bản
  ghi, kể cả bản ghi biên); ở HR 143 đỉnh T cách R 0,18 s, nằm trong refractory, nên
  0 FP. Đây là giới hạn đã biết của bộ dò cực đại địa phương khi refractory ngắn.
- 7 FP của `derivative_energy` đều ở bản ghi nhiễu (v0: 2 FP). Ngưỡng `quantile`
  thấp hơn ngưỡng `ptp`, nên cho nhiều đỉnh nhiễu qua hơn: đó là cái giá của quyết
  định 2 (đổi lại một nhịp lớn không còn che các nhịp khác).
- `valley_min` lệch 0,0 ms và `d2_max` +8 ms trên các bản ghi sạch HR 60 chỉ vì điểm
  bắt đầu xung SYNTHETIC rơi đúng lưới mẫu PPG (1,2 s + k ở 125 Hz). Không phải độ
  chính xác thật: quét pha onset (mục 2) mới cho sai số theo pha, khoảng 2–3 ms với
  `valley_min` không nội suy. Cả hai vẫn hỏng trên bản ghi nhiễu (chưa làm mượt).
- `tangent` không đổi so với v0 (lệch do hình dạng xung, mục 5.2).
- Đây là đáp án do mã sinh, không phải đánh dấu tay.

### 5.2. Kết quả v0 (2026-10-21/22, lịch sử)

Năm bản ghi `SYN_*` 10 s, ECG 500 Hz, PPG 125 Hz: sạch HR 60, nhiễu (trắng SD 0,03
và trôi nền 0,25 Hz), ngừng một nhịp, mất một xung PPG, HR 143 (RR 0,42 s).
ECG: Gaussian QRS + sóng T (biên độ 0,3 tại R + 0,25 s). PPG: sườn lên nửa cosin
rồi suy giảm mũ; foot đúng = điểm bắt đầu sườn lên. Hình dạng tự chọn, không
phải mô hình sinh lý. Dung sai R 50 ms / foot 100 ms.

- **Output chính:** `reports/weekly/week_05/synthetic_fiducials/`, config
  `week05_huy.json` (`refractory_s` 0,25 s).
- **Biến thể độ nhạy:** `refractory_040/` chỉ đổi `refractory_s` thành 0,4 s (giá
  trị v1). Config của biến thể nằm ngay trong thư mục output, không phải đề xuất
  thứ hai.
- **Tạo lại ngày 2026-10-22 sau các sửa đổi:** đáp án và detections giống từng
  byte với bản 2026-10-21, số liệu không đổi, chỉ provenance là mới.

| Mốc | Phương pháp | `refractory_s` | Mốc đúng | TP | FP | FN | Bias (ms) | MAE (ms) | SD (ms) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R | `derivative_energy` | 0,25 | 55 | 55 | 2 | 0 | −0,1 | 0,1 | 0,5 |
| R | `prominence` | 0,25 | 55 | 55 | 29 | 0 | −0,1 | 0,1 | 0,5 |
| R | `derivative_energy` | 0,4 | 55 | 55 | 1 | 0 | −0,1 | 0,1 | 0,5 |
| R | `prominence` | 0,4 | 55 | 55 | 0 | 0 | −0,1 | 0,1 | 0,5 |
| foot | `tangent` | 0,25 hoặc 0,4 | 54 | 54 | 0 | 0 | 27,5 | 27,5 | 11,6 |
| foot | `d2_max` | 0,25 hoặc 0,4 | 54 | 50 | 4 | 4 | 8,5 | 15,9 | 22,3 |
| foot | `valley_min` | 0,25 hoặc 0,4 | 54 | 48 | 6 | 6 | −4,3 | 4,5 | 13,7 |

Cách đọc:

- **So sánh hai phương pháp R phụ thuộc refractory.**
  - Ở 0,25 s, `prominence` bắt cả **sóng T** (29 FP), còn `derivative_energy`
    phân biệt được T nhờ năng lượng độ dốc (2 FP, ở bản ghi nhiễu).
  - Ở 0,4 s (v1), `prominence` không có FP và `derivative_energy` có 1 FP. Khi đó
    HR trên 150 bpm sẽ bị refractory cắt.
  - Sóng T SYNTHETIC đặt đúng R + 0,25 s, trùng biên refractory, nên kết quả ở
    0,25 s nhạy với lựa chọn này.
  - Không kết luận phương pháp nào tốt hơn từ bảng này.
- **`tangent` lệch có hệ thống so với điểm bắt đầu sườn lên.**
  - Với sườn nửa cosin, lệch giải tích là (1/2 − 1/π) × thời gian lên: 27,25 ms
    khi lên 150 ms, 18,17 ms khi lên 100 ms.
  - Theo `per_record`: bản ghi sạch, ngừng nhịp và mất PPG lệch 27,2 ms; HR143
    (lên 100 ms) lệch 18,8 ms; bản ghi nhiễu lệch 47,4 ms.
  - Con số gộp 27,5 ms gần giá trị giải tích của bản ghi sạch chỉ do HR143 và bản
    ghi nhiễu bù trừ nhau. Đó **không** phải phép kiểm giải tích; phép kiểm đúng
    là theo từng bản ghi (test `test_clean_feet_known_answer_per_method`).
  - Lệch này phụ thuộc **thời gian lên**, tức hình dạng xung. Nếu nghiệm pháp làm
    đổi hình dạng xung, nó đi thẳng vào ΔPAT trong cùng người.
- **`d2_max` và `valley_min`** gần điểm bắt đầu trên bản ghi sạch HR 60: lệch
  +11,4 ms ≈ 1,4 mẫu PPG và −3,5 ms < 1 mẫu, theo `per_record`. Cả hai hỏng trên
  bản ghi nhiễu (FP/FN đều ở đó) vì chưa làm mượt.
- Đây là đáp án do mã sinh ra, **không phải đánh dấu tay**, và không nói gì về
  độ chính xác trên người hay PulseDB.

## 6. PulseDB: xuất bộ đoạn để đánh dấu

Từ 2026-10-25 có raw và split Train 400 người
([provenance](../pulsedb_provenance.md) mục 5). `export` theo `review_plan` của
config (mục 9):

```powershell
python scripts\week05_fiducials.py export --raw data\raw\pulsedb\VitalDB_Train_Subset.mat --split-dir data\processed\pulsedb_train400_split_run01 --fs-hz 125 --out data\processed\pulsedb_w5_review_v1
```

Các bước của `export`:

1. Từ chối khi `--out` đã tồn tại, trước khi đọc raw.
2. Kiểm SHA-256 raw/inventory/manifest với `report.json` của split.
3. Đọc mọi hàng có trong inventory (từ 2026-10-25 bằng reader `h5py`, từng khối,
   nên dùng được cả split có lấy mẫu con theo người) và chạy `verify_inputs`, tức
   dựng lại inventory và băm lại mọi hàng, **kể cả hàng test**, như
   `b3-pipeline-v1`. Bước này chỉ để kiểm bàn giao; không trích đặc trưng, không
   ghi và không xem waveform hay nhãn test.
4. Chỉ hàng **train** là ứng viên (val và test bị bỏ trước khi chọn).
5. Chọn `n_subjects` người bằng hoán vị có seed, chỉ dựa vào `subject_id`;
   `selection_subjects` người đầu thành nhóm chọn phương pháp, phần còn lại thành
   nhóm xác nhận. Với mỗi người, danh sách `raw_index` đã sắp xếp được chia thành
   `per_subject` phần và lấy ngẫu nhiên một đoạn trong mỗi phần (`raw_index` là
   dòng trong file, không phải thời gian).
6. Ghi `main/` (mọi đoạn, thứ tự xáo trộn, cho lần đánh dấu đầu), `repeat/`
   (`repeat_segments` đoạn, một nửa mỗi nhóm, một đoạn mỗi người, thứ tự xáo trộn
   khác, cho lần đánh dấu lại) và `export.json` (nhóm người, hash hai
   `records.csv`; có ID người nên để ngoài Git).

Chỉ xuất ECG/PPG; ABP và nhãn ở lại file raw. `--fs-hz` do người chạy khai báo
(125 Hz theo [provenance PulseDB](../pulsedb_provenance.md)), không suy từ shape.
Chạy trên raw thật ngày 2026-10-25 (kết quả ở mục 9.4).

## 7. Giới hạn

- Chưa chạy `compare` trên mốc tay, nên chưa có độ nhạy/PPV hay sai số thời gian
  thật.
- R chưa nội suy dưới một mẫu (như v1).
- **Ngưỡng của `derivative_energy`** là 0,2 · ptp của năng lượng trên **cả cửa
  sổ**. Năng lượng tỉ lệ bình phương biên độ, nên một nhịp lớn làm mất nhịp ở cả
  trước lẫn sau nó. Probe review 2026-10-22, 9 nhịp:
  - một nhịp ×2,3: vẫn 9/9;
  - một nhịp ×2,5: chỉ còn **1/9**;
  - một spike 1 mẫu biên độ 0,8 × R: 0/9.

  Trong cả ba trường hợp `prominence` vẫn 9/9, tới nhịp ×5,5. Từ 2026-10-25 ngưỡng
  mặc định là `quantile` (mục 8): nhịp ×2,5 cho lại 9/9, nhưng gai 1 mẫu vẫn cho 1
  FP và biên độ tụt còn 0,3 giữa chừng vẫn chỉ 5/9 (probe Codex, 512 Hz). Đó là các
  hạn chế đã biết của `derivative_energy`; chúng vẫn đúng.

  **Vai trò của `derivative_energy` (chốt 2026-10-29).** Nó không phải mặc định của
  `SignalConfig`, nên output `features-sqi-v1/v2` không đổi. Nhưng ở cổng mục 9.3 nó
  là ứng viên R ngang hàng với `prominence`: `tie_order` của config phải liệt kê đúng
  mọi phương pháp đã so, và chỉ dùng khi MAE trung bình theo người hòa tuyệt đối.
  Phương pháp R nào thắng ở nhóm chọn và được xác nhận ở nhóm xác nhận thì thành bộ dò
  R cho B4, kể cả `derivative_energy`. Các hạn chế trên đi kèm nó vào B4 và phải
  được báo cùng kết quả. B2 đã dùng `derivative_energy` làm bộ dò HR
  (`HR_CONFIG` trong `software/pulsedb/features_b2.py`) dù nó **chưa qua cổng**.
- **Refractory chung cho đỉnh PPG** (tới 2026-10-24 `detect` dùng chung
  `config.refractory_s` 0,25 s; từ 2026-10-25 PPG dùng `ppg_refractory_s` 0,35 s,
  mục 8). PPG có sóng tâm trương thì sinh foot giả: probe HR 75,
  sóng tâm trương biên độ 0,5, cách ≥ 0,30 s cho 21 foot, trong khi chỉ có 11 foot
  thật; với 0,4 s ra đúng 11. Foot giả ảnh hưởng ghép PAT theo ba cách: làm R
  thành `ambiguous` (mất cặp, nên số nhịp có PAT giảm và median tính trên tập nhịp
  khác); nằm ngoài giới hạn; hoặc, nếu là ứng viên duy nhất trong giới hạn của
  khoảng R–R, được ghép thành một PAT sai mà quy tắc không phát hiện. PPV foot so
  với đánh dấu tay cũng giảm. SYNTHETIC hiện không có sóng tâm trương; test
  `test_separate_ppg_refractory_skips_a_secondary_wave` dựng riêng một sóng phụ ở
  +0,30 s. Refractory 0,35 s không giải quyết sóng tâm trương nói chung (sóng phụ
  ở +0,36 s vẫn lọt); chọn foot gần R nhất cũng không an toàn (lặng lẽ chọn foot
  giả). `pair_between_r` giữ quy tắc ở mục 3: khi một khoảng R–R có nhiều foot thì
  nhịp chỉ được ghép nếu **đúng một** foot nằm trong giới hạn PAT, còn lại là
  `ambiguous`; vì vậy một foot giả nằm ngoài giới hạn không chặn nhịp, nhưng một
  foot giả trong giới hạn bên cạnh foot thật làm nhịp thành `ambiguous`.
- ECG đảo cực mà không đặt `ecg_polarity`: theo probe review 2026-10-22, cả hai
  phương pháp bắt sóng S SYNTHETIC (R + 0,03 s), lệch +30 ms. Ca này chỉ là TP với
  dung sai cũ 50 ms; với dung sai đã chốt 24 ms (mục 3, 9) nó là FN + FP. PPG đảo
  cực thì 0 TP. Polarity phải khai báo đúng.
- `pair_pat` của v1 (dùng trong `features-sqi-v1`) vẫn so biên 80/400 ms không có
  dung sai float. Đây là hành vi v1, giữ nguyên để không đổi output v1.
- Chưa thử QRS rộng, ngoại tâm thu.
- Quy tắc outlier theo cửa sổ không phân biệt outlier do mốc sai với thay đổi
  sinh lý nhanh trong cửa sổ.
- Các giới hạn và dung sai chưa có nguồn (mục 3); phải khóa trước pilot/validation,
  không chỉnh theo test.

## 8. Quyết định ngày 2026-10-25

Huy chọn ngày 2026-10-25, sau khi Codex phân tích độc lập và chạy probe trong bộ
nhớ. Cả bốn là đề xuất kỹ thuật tạm, **không** phải tham số đã thẩm định; lựa chọn
cuối cho nội suy và bộ tham số chờ đánh dấu tay, chọn theo người, không bao giờ
trên test (từ 2026-10-25 chỉ trên train, mục 9).

1. **Nội suy foot:** thành tùy chọn `foot_interpolation`, mặc định tắt; khi bật chỉ
   nội suy ở cực trị chặt ba điểm, tối đa nửa mẫu (mục 2).
2. **Ngưỡng `derivative_energy`:** `r_energy_threshold = "quantile"`, tức
   0,2 × (Q95 − Q05) của năng lượng; `prominence` vẫn là bộ dò R mặc định của
   `SignalConfig`. Mặc định đó không quyết định bộ dò R của B4: ở cổng mục 9.3 hai
   phương pháp R là ứng viên ngang hàng, và phương pháp thắng, được xác nhận thì
   thành bộ dò R cho B4 (chốt 2026-10-29, mục 7). Ngưỡng thích nghi kiểu
   Pan–Tompkins (T = N + 0,25 (S − N), cập nhật 0,125) để sau, chỉ khi có dữ liệu
   đánh dấu để thẩm định (mục 7).
3. **Refractory:** tách `ppg_refractory_s`; config Tuần 5 (v1, giữ ở v2) dùng R
   0,25 s, PPG 0,35 s. `features-sqi-v1/v2` giữ một `refractory_s` cho cả hai kênh
   và từ chối `ppg_refractory_s` khác `None`. Ứng viên sau: refractory PPG theo RR cục bộ
   (`min(0,40 s; 0,75 × trung vị RR)`), cần R tin cậy và phải báo riêng.
4. **Sóng T SYNTHETIC:** đỉnh T đặt ở R + 0,28 × √(RR / 1 s) giây (khoảng 280 ms ở
   60 bpm, 177 ms ở 150 bpm; phỏng theo cách co giãn theo nhịp của ECGSYN, không
   phải mô hình sinh lý đã thẩm định). Bản ghi `SYN_T_EDGE_HR60` giữ T ở 0,25 s làm
   ca biên. Generator `week05-synthetic-records-v1`, script `week05-fiducials-v2`;
   kết quả mới ở mục 5.1; bảng mục 5.2 là kết quả v0 (T ở 0,25 s, nội suy bật,
   ngưỡng `ptp`), giữ làm lịch sử.

Không quyết định nào chặn việc tải PulseDB hay phát triển thiết bị. Quyết định 4
phải có trước khi tạo bảng so sánh SYNTHETIC mới; quyết định 3 trước khi tin độ phủ
PAT ở nhịp tim cao (M4); quyết định 2 trước khi dùng `derivative_energy` làm bộ dò
thật. Hai chỗ dùng đó là bộ dò HR của B2 (đã dùng, chưa qua cổng) và bộ dò R của B4
(chỉ khi thắng và được xác nhận ở cổng mục 9.3).

## 9. Kế hoạch đánh dấu tay PulseDB và ngưỡng chấp nhận (chốt 2026-10-25)

Huy chọn ngày 2026-10-25, **trước khi đánh dấu bất kỳ đoạn PulseDB nào**, từ đề
xuất của Codex (2026-10-25). Mọi con số ở đây là đề xuất kỹ thuật, **chưa có
nguồn**; chúng được khóa trong `review_plan` và `acceptance` của config
`fiducials-week05-v2`, và không được đổi sau khi xem kết quả. Theo quyết định B3/B4
([run_b3_pulsedb.md](run_b3_pulsedb.md)), B4 chỉ được xây khi bước này đạt.

### 9.1. Mẫu

- **Chỉ train**: 40 người × 2 đoạn = 80 đoạn (khoảng 2.000 click). Người val không
  được dùng để chọn phương pháp mốc, để B4 − B3 trên val vẫn là bằng chứng độc lập.
  Từ 2026-10-29 code chặn cả mốc tay trên val (mục 4).
- Câu `note` của config vẫn ghi "SYNTHETIC and train/val only". Đó là chữ cũ, đã được
  mục này thay: chỉ train. Config giữ nguyên từng byte, vì `export.json` và
  `detections_main.provenance.json` đã ghi hash của nó; sửa thì `compare`, `repeat`
  và `gate` từ chối export và detections đã có. Code tự chặn val (chốt 2026-10-29).
- 20 người **nhóm chọn**, 20 người **nhóm xác nhận**, chia sẵn khi xuất (seed
  20261025).
- Mỗi người: một đoạn ngẫu nhiên trong mỗi nửa danh sách `raw_index` đã sắp xếp.
- **Đánh dấu lặp lại**: 16 đoạn (20%; 8 mỗi nhóm, mỗi người một đoạn), thứ tự xáo
  trộn, đánh dấu lại **ít nhất 2 ngày** sau lần đầu, không xem lần trước hay kết
  quả detector.

### 9.2. Định nghĩa mốc khi click

- **R**: đỉnh sóng R.
- **Foot PPG**: **điểm cực tiểu ngay trước sườn lên tâm thu**. `valley_min` nhắm
  đúng điểm này; `tangent` (giao điểm tiếp tuyến) và `d2_max` nhắm điểm khác, nên
  lệch có hệ thống so với mốc tay là thông tin về định nghĩa, không phải lỗi của
  chúng. Nếu sau này cần PAT theo tiếp tuyến thì phải có đợt đánh dấu riêng.
- Dùng zoom của cửa sổ (click không tự hút về đỉnh). Đoạn hay nhịp không chắc thì
  vẫn đánh dấu theo định nghĩa và ghi chú; không âm thầm bỏ đoạn khó.
- **Nhịp sát biên vùng review (chốt 2026-10-29).** `annotate` chỉ giữ click có thời
  điểm trong `[edge_s, T − edge_s]` (gồm hai biên), với T = số mẫu ECG / tần số.
  Click ngoài vùng bị bỏ và chỉ được đếm trong provenance
  (`clicks_outside_region_dropped`). Với đoạn PulseDB 10 s và `--edge-s` mặc định
  0,5, vùng là [0,5 s; 9,5 s], trùng hai vạch lưới chính 0,5 s và 9,5 s. Ở 125 Hz
  hai biên này rơi giữa hai mẫu: mẫu gần nhất cách biên 4 ms. Quy tắc, giống hệt ở
  lần 1 và lần 2:
  1. Mốc là một mẫu cụ thể (mẫu cao nhất của sóng R; mẫu thấp nhất trước sườn lên).
  2. Mẫu mốc nằm trong vùng thì **phải click**, kể cả khi sát biên. Bỏ nhịp này thì
     detection đúng ở đó bị tính FP, và hai lần đánh dấu có thể lệch nhau.
  3. Mẫu mốc nằm ngoài vùng thì **không click**.
  4. Mốc nằm trong 0,1 s (một vạch lưới phụ) quanh biên: phóng to tới khi thấy từng
     mẫu, xác định mẫu mốc nằm bên nào của vạch biên, rồi click đúng lên mẫu đó.
     Sai số click phải dưới 4 ms, nếu không click có thể rơi sang phía kia biên và bị
     bỏ hay giữ khác với ý định.
  5. Hai mẫu ở hai bên vạch biên ngang nhau, không phân định được mẫu mốc: lấy mẫu
     nằm trong vùng.

### 9.3. Ngưỡng chấp nhận và quy tắc chọn

Dung sai ghép R ±24 ms, foot ±48 ms (3 và 6 mẫu ở 125 Hz). Sai số = tự động − tay.

| Chỉ số | R | Foot |
| --- | ---: | ---: |
| Độ nhạy và PPV (mỗi chỉ số) | ≥ 99% | ≥ 98% |
| \|Bias\| | ≤ 4 ms | ≤ 8 ms |
| MAE | ≤ 8 ms | ≤ 16 ms |
| SD (`ddof=1`) | ≤ 8 ms | ≤ 16 ms |

- Độ nhạy, PPV và MAE: tính cho từng người (gộp các đoạn của người đó) rồi lấy
  trung bình đều theo người. Bias và SD: gộp mọi cặp ghép được. Nếu một chỉ số
  không xác định được ở bất kỳ người nào (không có mốc tay, không có detection,
  không ghép được cặp nào) thì chỉ số đó là `None` và coi như không đạt.
- Phải có đủ mọi đoạn đã xuất cho mọi phương pháp (80 đoạn × 5 phương pháp), và
  mốc tay phải có provenance của `annotate` trên đúng `main/`. Thiếu đoạn, hoặc
  CSV điền tay không có provenance, thì `gate` từ chối.
- Thêm điều kiện theo đoạn: ít nhất 95% số đoạn có độ nhạy và PPV ≥ 90%; đoạn
  không có mốc tay nào thì không đạt. Báo đoạn tệ nhất.
- Quyết định dựa trên **ước lượng điểm**. CI 95% bootstrap theo người (2.000 lượt,
  seed 20261025) được báo cáo nhưng không dùng để quyết định.
- **Chọn** trên nhóm chọn: trong các phương pháp đạt mọi ngưỡng, lấy MAE trung bình
  theo người nhỏ nhất. Hòa tuyệt đối thì theo thứ tự `prominence` trước
  `derivative_energy`, và `valley_min` trước `tangent` trước `d2_max`. Mọi thiết
  lập khác giữ nguyên (không nội suy). Phương pháp thắng và được xác nhận là bộ dò
  R/foot cho B4, kể cả `derivative_energy` (mục 7).
- **Xác nhận** trên nhóm xác nhận: chỉ chấm phương pháp thắng, một lần. Không đổi
  phương pháp sau khi xác nhận thất bại.
- **Độ lặp lại** của người đánh dấu (lần 2 − lần 1, cùng dung sai): MAE R ≤ 8 ms,
  foot ≤ 16 ms, **và** mọi mốc của cả hai lần đều ghép được. Nếu không có điều kiện
  này, các mốc bỏ sót hay lệch quá dung sai sẽ bị loại khỏi MAE và bị che đi
  (Codex review 2026-10-25). Lần 2 phải phủ đúng 16 đoạn của `repeat/`, cùng vùng
  review, và bắt đầu ít nhất 2 ngày sau ngày cuối của lần 1. Không đạt thì `gate`
  ra `B4_NOT_ALLOWED`; với PulseDB đó là kết luận cuối (mục 9.6, từ 2026-10-29),
  không sửa quy trình rồi làm vòng mới.
  **Chốt 2026-10-29** (trước khi chạy `compare`, `repeat` hay `gate`): giữ nguyên
  điều kiện ghép đủ 100%, không bỏ mốc sát biên khỏi phép đếm, không đổi config.
  Nguồn trượt cơ học ở biên được xử lý bằng quy tắc click nhịp sát biên ở mục 9.2.
- `gate` chỉ nhận kết quả độ lặp lại của `repeat`, làm từ đúng file mốc lần 1 mà
  `compare` đã dùng, cùng config và cùng export, và có `passed` đúng bằng `true`.
- Kết luận của lệnh `gate`: `B4_ALLOWED` chỉ khi cả R và foot được xác nhận và độ
  lặp lại đạt. `PENDING_REPEATABILITY` khi chưa có lần đánh dấu lại.
  `B4_NOT_ALLOWED` thì không xây B4 theo quyết định này, kể cả khi kèm ghi chú
  giới hạn; đây là kết luận cuối cho PulseDB (mục 9.6).

### 9.4. Bộ đoạn đã xuất và lệnh chạy

Kết quả lần xuất ngày 2026-10-25 được ghi ở
[báo cáo Tuần 5](../../reports/weekly/week_05/README.md) mục 6.5. Thư mục
`data/processed/pulsedb_w5_review_v1/` nằm ngoài Git, vì `records.csv` và
`export.json` có ID người.

**Tuổi của 40 người đã xuất (kiểm 2026-10-29).** Không ai dưới 18 tuổi; tuổi nhỏ
nhất là 21. Rủi ro của `ppg_refractory_s` 0,35 s ở trẻ nhỏ (chặn đỉnh PPG khi HR trên
khoảng 171 bpm, tức RR < 0,35 s) vì vậy không áp dụng cho bộ đoạn này; refractory
giữ nguyên. Cách kiểm: lấy `raw_index` từ cột `origin` của `main/records.csv`, rồi
chỉ đọc trường `Age` của đúng 80 dòng đó bằng h5py (`_Source.values` của
`software/pulsedb/h5_reader.py`); không đọc BP, ABP hay nhãn. SHA-256 của raw khớp
`export.json`. Ghi thêm để biết, không đổi gì: theo R của `derivative_energy` (chưa
thẩm định) trong `detections_main.csv`, trung vị HR theo đoạn là 74,6 bpm; 1/80 đoạn
có trung vị HR trên 171 bpm (208 bpm) và 3/80 đoạn có ít nhất một RR < 0,35 s. Hai
đoạn có nhiều RR ngắn nhất có 20 và 23 R trong 10 s, nên hợp với R thừa hơn là nhịp
nhanh thật.

Bước đánh dấu cần cửa sổ Tk. Python 3.11.7 của PlatformIO không có tkinter, nên tới
2026-10-25 bước này chạy bằng `.venv` (khi đó Python 3.13, có Tk 8.6). Từ 2026-10-29
`.venv` đang được dựng lại từ Python 3.11.9 (scoop), bản này có tkinter.

Mỗi đoạn được ghi ngay khi đóng cửa sổ, và `<out>.progress.json` ghi các đoạn đã
xong. Có thể dừng giữa chừng (Ctrl+C trong terminal), rồi chạy lại đúng lệnh kèm
`--resume`, có thể vào ngày khác (`--date` là ngày của lần ngồi mới). `--resume`
yêu cầu cùng `records`, `annotator` và `--edge-s`. Sau mỗi đoạn, file progress ghi
độ dài và SHA-256 của CSV (checkpoint). Khi resume, phần đầu CSV phải khớp từng byte
với checkpoint, nên CSV bị sửa tay thì bị từ chối. Nếu máy dừng đúng lúc đã ghi CSV
mà chưa ghi checkpoint, các hàng của đoạn đó bị cắt bỏ, số byte bị cắt được ghi vào
`sittings`, và đoạn đó được đánh dấu lại. File provenance chỉ được ghi khi xong
đoạn cuối, nên `compare` chỉ chạy được trên một lần đánh dấu đã hoàn tất.

```powershell
# Lần 1: mọi đoạn trong main/; dừng giữa chừng thì chạy lại lệnh này kèm --resume
.\.venv\Scripts\python.exe scripts\week05_fiducials.py annotate --records data\processed\pulsedb_w5_review_v1\main --out data\processed\pulsedb_w5_review_v1\manual_main.csv --annotator Huy --date <YYYY-MM-DD>
# So với detector (detections_main.csv đã chạy sẵn), rồi chấm ngưỡng
python scripts\week05_fiducials.py compare --annotations data\processed\pulsedb_w5_review_v1\manual_main.csv --detections data\processed\pulsedb_w5_review_v1\detections_main.csv --out data\processed\pulsedb_w5_review_v1\agreement_main.json
python scripts\week05_fiducials.py gate --agreement data\processed\pulsedb_w5_review_v1\agreement_main.json --export data\processed\pulsedb_w5_review_v1\export.json --out data\processed\pulsedb_w5_review_v1\gate_v1.json
# Lần 2 (ít nhất 2 ngày sau lần 1): repeat/, rồi độ lặp lại và gate cuối
.\.venv\Scripts\python.exe scripts\week05_fiducials.py annotate --records data\processed\pulsedb_w5_review_v1\repeat --out data\processed\pulsedb_w5_review_v1\manual_repeat.csv --annotator Huy --date <YYYY-MM-DD>
python scripts\week05_fiducials.py repeat --first data\processed\pulsedb_w5_review_v1\manual_main.csv --second data\processed\pulsedb_w5_review_v1\manual_repeat.csv --export data\processed\pulsedb_w5_review_v1\export.json --out data\processed\pulsedb_w5_review_v1\repeatability.json
python scripts\week05_fiducials.py gate --agreement data\processed\pulsedb_w5_review_v1\agreement_main.json --export data\processed\pulsedb_w5_review_v1\export.json --repeatability data\processed\pulsedb_w5_review_v1\repeatability.json --out data\processed\pulsedb_w5_review_v1\gate_final.json
```

`compare` in tóm tắt gộp mọi đoạn của cả hai nhóm. Bảng đó chỉ để xem; quyết định
lấy từ `gate`, vốn tách nhóm chọn và nhóm xác nhận. Output của `gate` không có ID
người, nhưng `record_id` của đoạn tệ nhất vẫn truy ngược được về dòng raw, nên giữ
nó ngoài Git cùng các file còn lại.

### 9.5. Điều được và không được kết luận

- Đánh dấu tay chỉ kiểm vị trí mốc trên tín hiệu **đã lọc** của PulseDB, không kiểm
  PAT sinh lý. Chưa biết bộ lọc của PulseDB là zero-phase hay causal
  ([provenance](../pulsedb_provenance.md) mục 6), nên khoảng R → foot đo trên
  PulseDB là một khoảng thời gian trên tín hiệu đã xử lý, kèm một sai lệch hệ thống
  chưa biết. Được dùng nó làm đặc trưng tương đối cho mô hình; không so trị tuyệt
  đối (ms) với PAT của thiết bị, không gọi là PTT.
- Ở 125 Hz một mẫu là 8 ms. Mốc có phần lẻ dưới một mẫu (ví dụ `tangent`) không
  chứng minh độ chính xác dưới một mẫu.
- Một người đánh dấu chỉ đo được độ lặp lại của chính người đó, không đo được độ
  thống nhất giữa các người đánh dấu.
- Khi có B4: báo B4 − B3 ghép cặp theo người trên cùng các dòng val, riêng SBP/DBP,
  kèm mô hình đối chứng **B3 + HR/SQI** (không có PAT), để biết phần cải thiện có
  đến từ PAT hay không.

### 9.6. Nếu `gate` ra `B4_NOT_ALLOWED` (chốt 2026-10-29)

Chốt ngày 2026-10-29, trước khi chạy `compare` hay `gate` trên mốc tay PulseDB. Lúc
chốt, file mốc lần 1 (`manual_main.csv`) có một phiên dở ngày 2026-10-25; chưa có
bảng so khớp hay kết quả cổng nào.

- `B4_NOT_ALLOWED` là **kết luận cuối cho PulseDB**. Không có vòng đánh dấu 2, không
  đổi phương pháp hay ngưỡng rồi chấm lại, và không làm B4 trên PulseDB.
- PAT chỉ được đánh giá trên **dữ liệu thiết bị**. Detector cho thiết bị được thẩm
  định riêng trên bản ghi thiết bị, vì tần số lấy mẫu khác: thiết bị ECG 512 sps, PPG
  200 sps; PulseDB 125 Hz.
- Hệ quả cho [kịch bản bài báo](../paper_scenarios_v0.1.md): bỏ bảng B4 PulseDB.
  RQ1 không đổi.
- **`tangent` gần như không thể đạt** theo định nghĩa mốc tay. Mốc tay foot là cực
  tiểu ngay trước sườn lên (mục 9.2), tức đúng điểm `valley_min` nhắm. `tangent` lệch
  có hệ thống khỏi điểm đó: +18,8 đến +47,4 ms trên SYNTHETIC (mục 5.2), trong khi
  giới hạn |bias| của foot là 8 ms. `d2_max` có bias +6,8 ms trên SYNTHETIC v1 (mục
  5.1), sát giới hạn, và hỏng trên bản ghi nhiễu. Theo bằng chứng SYNTHETIC này, ở
  foot thực tế chủ yếu còn `valley_min`.
