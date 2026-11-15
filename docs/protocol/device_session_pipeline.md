# Pipeline dữ liệu thiết bị: ingest, mốc và PAT, phân tích RQ1

> **Trạng thái: đề xuất ngày 2026-11-13; sửa theo rà soát độc lập và duyệt 2026-11-14; sửa
> 2026-11-15 sau rà soát toàn dự án (chờ duyệt): mục 2, 3.3, 3.4, 4.1–4.3, 5.** Mới chạy
> trên dữ liệu SYNTHETIC. Chưa có bản ghi thiết bị nào. Kết quả SYNTHETIC chỉ kiểm chứng code, không nói gì về thiết bị hay BP.

Ba bước, mỗi bước dùng đầu ra của bước trước:

| Bước | Code | Config | Đầu ra |
| --- | --- | --- | --- |
| Ingest phiên | `software/device/session_ingest.py` | `configs/data/device_session_v1.json` (`window`) | Thời gian mẫu, sự kiện, cửa sổ cuff, tóm tắt phiên ([quy ước dữ liệu](../data_convention.md) mục 4) |
| Mốc, PAT, cờ SQI | `software/device/features.py` | cùng config (`signal`, `pat_validity`, `sqi_hardware`) | `cuff_features.csv`, `cuff_features.json` |
| Phân tích RQ1 | `software/evaluation/rq1_analysis.py` | `configs/analysis/rq1_analysis_v1.json` | `report.json`, `summary.md` |
| Dữ liệu thử | `software/device/synthetic_session.py` | tham số trong `SessionSpec` | Luồng byte V0.2 có dạng sóng, metadata, đáp án |

## 1. Lệnh

```powershell
# Một bản ghi + nhật ký cuff -> cửa sổ, đặc trưng theo lần cuff
.\.venv\Scripts\python.exe scripts\device_session.py --recording <thư mục bản ghi> --cuff-log <cuff_log.csv> --output <thư mục mới>
# Mọi bảng đặc trưng -> RQ1 (G5 chỉ còn lệnh này)
.\.venv\Scripts\python.exe scripts\run_rq1_analysis.py --features <a>\cuff_features.csv <b>\cuff_features.csv --output <thư mục mới>
```

Dữ liệu người: output của `device_session.py` ghi vào
`data/interim/<subject_id>/<session_id>/<recording>/`. Script từ chối ghi vào `data/raw/` và từ
chối ghi đè. Với dữ liệu không phải SYNTHETIC, `run_rq1_analysis.py` từ chối chạy khi `status`
của config chưa là `LOCKED`, hoặc khi chính file config đã truyền, `sap_v1.md` hay một file code
trong `LOCKED` (phân tích, CI, mô phỏng, provenance, ingest, đặc trưng) chưa được Git theo dõi hay
khác HEAD (SAP mục 12; sửa 2026-11-13, duyệt 2026-11-14). Report ghi `approval_committed`.

Thêm và duyệt 2026-11-14: `LOCKED` gồm cả toàn bộ code của bước tính đặc trưng
(`device_session.py` và mọi module nó import, danh sách `CODE`; test so danh sách với đồ thị
import) và `configs/data/device_session_v1.json`. Mỗi `cuff_features.csv` phải có
`provenance.json` do `device_session.py` ghi cạnh nó. Với dữ liệu thật: provenance phải ghi
workspace sạch, có commit, hash code và config bằng hash của các file đang khóa. Với mọi bảng có
provenance: `source_type` của dòng phải khớp provenance, nên bảng thiết bị bị gắn nhầm SYNTHETIC
sẽ bị từ chối. Report ghi `feature_provenance`.

Sửa 2026-11-14 sau rà soát độc lập (duyệt 2026-11-14): `provenance.json` ghi hash của
`cuff_features.csv` và `cuff_features.json` (`outputs_sha256`); runner từ chối bảng không
khớp hash này, nên không thể đặt bảng khác hay bảng đã sửa cạnh một provenance. Với dữ liệu
thật, `git_commit` phải là commit có thật của repo và chứa đúng code và config đã ghi trong
provenance. Danh sách khóa có thêm các `__init__.py` của package cha (Python chạy chúng khi
import). Endpoint 5 và 7 báo thêm `confirmatory: false`, số người còn được đánh giá, cờ dưới
15 người, và tách số lần cuff có cờ thành số bỏ khỏi tập học và số bỏ khỏi tập đánh giá.

Sửa 2026-11-14 sau rà soát độc lập lần hai (duyệt 2026-11-14):

- "Chưa đổi so với HEAD" giờ so cả nội dung: file được băm như Git lưu (cùng bộ lọc dòng) rồi so
  với blob của HEAD. Trước đó chỉ dùng `git diff`, nên file đánh dấu `assume-unchanged` hay
  `skip-worktree` có thể khác HEAD mà không bị thấy. Hàm `committed_unchanged` dùng chung với
  runner B2, B5.
- **Phạm vi của cổng.** Cổng chặn việc chạy nhầm dữ liệu thật trên code hay config chưa commit,
  khi chạy bằng hai script. Nó không chặn người cố ý lách: gọi thẳng `analyze()` hay
  `device_session.run()` trong Python không qua cổng; hash trong `provenance.json` chỉ chứng minh
  bảng khớp với file provenance đặt cạnh nó, không chứng minh commit đã ghi là commit thật sự đã
  tạo ra bảng, vì provenance là file sửa được. Kết quả RQ1 chỉ được báo từ `report.json` do
  `run_rq1_analysis.py` ghi, trên bảng do `device_session.py` tạo từ bản ghi gốc còn đúng SHA-256.

## 2. Ingest (việc F)

- Kiểm bản ghi theo manifest của logger. Thiếu manifest, lệch SHA-256, lệch số packet hay số mẫu
  thì dừng. Không sửa, không nội suy.
- Thời gian mẫu theo Packet Schema V0.1 mục 5.3: hồi quy mốc theo chỉ số mẫu cho từng chuỗi, trừ
  độ trễ hiệu dụng L của metadata, cộng offset khe PPG theo `LED_PW` của `0xD2`. Hồi quy cho luôn
  tốc độ thực của từng kênh.
- Cửa sổ theo protocol 6.2 và 6.4: lưu `[t0 − 60 s, t0)`; phân tích 10/20/30/60 s; đoạn bơm
  `[t0, cuff_end]`; với M1/M2 kiểm cửa sổ có nằm sau mốc pha (mã 4) không.
- Khoảng cách khe PPG theo `LED_PW` lấy từ `software/device/max30101.py` (datasheet MAX30101
  Table 11); trước 2026-11-15 ingest lấy hằng số này từ module SYNTHETIC, nên test ingest và bộ
  tạo dùng chung một giá trị và không bắt được giá trị sai. A4 kiểm giá trị này trên bàn.
- Tiêu chí A3 trên mọi bản ghi (thêm 2026-11-15, chờ duyệt): trung vị phần dư của hồi quy mốc theo
  khối 10 s, lớn nhất theo trị tuyệt đối, ghi ở cột `residual_block_max_us` của `timebase.csv`;
  vượt 0,2 ms thì có cờ phiên `<kênh>:chain<k>:timebase_residual_above_a3`. Khối cuối ngắn hơn
  5 s gộp vào khối trước, để vài mốc cuối không mang riêng jitter của chúng; chuỗi dưới 3 mốc
  không đánh giá được (ô trống). Chỉ báo, không đổi thời gian mẫu; khi đó một đường thẳng cho
  cả chuỗi không còn đủ (kế hoạch đo đồng bộ mục 9).
- Test (`tests/test_device_ingest.py`, luồng qua `packet_logger.record`): số packet, tốc độ thực
  (−40 và +2 500 ppm đặt trước, sai ≤ 5 ppm), packet mất chèn cố ý (ECG 2, PPG khe 1 một packet,
  8 mẫu), thời gian mẫu so với thời gian thật (≤ 60 µs), metadata hay output bị sửa thì báo lỗi,
  nhật ký cuff trỏ sai sự kiện thì báo lỗi.

## 3. Mốc và PAT ở tần số thiết bị (việc G)

### 3.1. Ghép hai trục thời gian

ECG và PPG giữ thời gian mẫu riêng trên cùng đồng hồ MCU. `fiducials.Channel` nhận thẳng các thời
gian này (`timestamps`), nên mốc R và chân sóng ra trên cùng đồng hồ và PAT = chân sóng − R.
Không resample, không dịch kênh. Một kênh thiếu L thì PAT không được tính
(`pat:upstream_delay_unknown`), như `features-sqi-v2`.

### 3.2. Sai số lượng tử hóa dự kiến

- Đỉnh R chọn trên mẫu: sai tới nửa chu kỳ ECG, 0,98 ms ở 512 sps.
- Chân sóng chọn trên mẫu (`valley_min`): tới nửa chu kỳ PPG, 2,5 ms ở 200 sps. Chân sóng
  `tangent` của `features-sqi-v1` nằm giữa hai mẫu.
- Tổng do lấy mẫu: tới 0,98 + 2,5 ≈ 3,5 ms trong trường hợp xấu nhất, chưa kể jitter mốc và sai
  số của L. Với `tangent` trên sườn lên tuyến tính, chỉ còn phần của R.

### 3.3. Kết quả test (`tests/test_device_features.py`, SYNTHETIC)

- Bộ tạo đặt PAT hằng (200 ms), PAT trôi (170 → 260 ms), PAT nhảy bậc (150 → 210 ms) kèm lệch
  clock (PPG +3 000 ppm, ECG −60 ppm). Sai số PAT của mọi cặp ≤ 0,98 ms + 0,15 ms (phần hồi quy
  mốc), ở cả ba màu.
- Nhịp lỡ (một xung PPG bị bỏ): R đó có trạng thái `no_foot`, cửa sổ có cờ `pat:unmatched_beats`.
- Đoạn nhiễu nặng trong cửa sổ: có cờ `ppg:shape_inconsistent` hoặc `pat:unmatched_beats`;
  cửa sổ sạch không có cờ.
- Mất một packet PPG trong cửa sổ: cờ `stream:gap`, kênh đó có `ppg:time_gap` và không có PAT;
  hai khe còn lại không bị ảnh hưởng.
- Test PulseDB cũ không đổi (`week04.py` chỉ nhận thêm giá trị split `device`).
- Thêm 2026-11-15:
  - các test thời gian ở trên chạy với `filter_mode = none` để tách riêng phép ghép trục;
  - trôi nền (ECG khoảng 3 lần đỉnh R, PPG khoảng 4 lần biên độ xung, đỉnh–đỉnh): không lọc thì
    chỉ tìm được 8/34 đỉnh R; với bộ lọc của config tìm đủ 34, sai số PAT lớn nhất 2,7 ms,
    trung bình +1,2 ms do bộ lọc làm tròn góc của sườn lên tuyến tính (mục 3.4);
  - PPG dừng ngay sau đầu cửa sổ (còn 0,32 s): kênh đó có cờ `pat:no_foot_span`, không có PAT,
    buổi vẫn chạy tiếp; trước đó lỗi này làm dừng cả buổi;
  - `led_lock_status` đủ các trường hợp (mục 4.3 ý 19), và cờ `ppg:led_not_locked` tới được bảng
    theo lần cuff.

### 3.4. Ghi chú và giới hạn

- Sườn lên tuyến tính làm chân sóng `tangent` trùng mốc đặt. Khi có nhiễu, độ dốc lớn nhất bị
  nhiễu đẩy lên nên chân sóng `tangent` lệch muộn có hệ thống: ở nhiễu 0,2 % biên độ, lệch tới
  khoảng 10 ms trên dữ liệu giả (thử 2026-11-13). Đây là tính chất của phương pháp, không phải
  của việc ghép trục; việc chọn phương pháp chân sóng thuộc [Tuần 5](week05_fiducials_pat_validity.md).
- Mất một packet trong cửa sổ làm cả kênh của cửa sổ đó không có mốc (`time_gap`), như
  `features-sqi-v1`. Chưa tách đoạn liên tục.
- Cờ cử động chưa tính: ingest v1 chưa đọc IMU, nên mọi cửa sổ là `not_evaluable` về cử động.
- Ngưỡng SQI vẫn là đề xuất của [SQI v1](sqi_specification_v1.md), khóa trên G2.
- L của PPG chưa có giá trị thiết kế; PAT tuyệt đối có thể lệch cố định
  ([kế hoạch đo đồng bộ](../../hardware/test_reports/sync_10min_test_plan.md) mục 9–10).
- **Bộ lọc (đổi 2026-11-15, chờ duyệt):** `filter_mode = zero_phase`, ECG 0,5–40 Hz, PPG
  0,5–8 Hz, Butterworth bậc 2 chạy xuôi rồi ngược trong từng cửa sổ (mặc định của
  `features-sqi-v1`). Trước đó config để `none`, trong khi bộ lọc thông cao số của MAX30001 đã
  tắt vì lọc 0,5 Hz được định làm offline
  ([đề xuất bo](../../configs/hardware/custom_board_proposal.md), 2026-10-25). Ngưỡng
  prominence bằng 0,2 lần biên độ đỉnh–đỉnh của cả cửa sổ, nên khi không lọc, trôi nền che phần
  lớn nhịp (mục 3.3). Đây là giá trị cho pilot, khóa trên pilot theo độ chính xác mốc, không theo
  sai số RQ1. Giới hạn đã biết, nêu ở vòng phản biện độc lập:
  - đệm mặc định của bộ lọc chỉ 15 mẫu (75 ms PPG, 29 ms ECG) và `edge_s` 0,1 s không chứng minh
    bộ lọc 0,5 Hz đã ổn định ở mép; ngưỡng prominence tính trên cả cửa sổ trước khi bỏ mép, nên
    quá độ ở mép có thể che nhịp bên trong;
  - bộ lọc đổi hình thái: trên xung giả, thời gian lên tăng từ 103 lên 126 ms; độ lệch có thể đổi
    theo HR (trên xung giả, biên độ chênh 0,3 % giữa 70 và 90 nhịp/phút);
  - trước khi khóa: đo trên bản ghi G2 độ phủ nhịp, PAT, ΔPAT, biên độ, thời gian lên, độ rộng
    khi có và không có lọc; cân nhắc lọc trên đoạn dài hơn trước cửa sổ, không lọc qua khoảng
    trống, ranh giới cấu hình hay đoạn bơm sau `t0`.

## 4. Phân tích RQ1 (việc H)

### 4.1. Ánh xạ với SAP v1

| SAP | Code |
| --- | --- |
| Mục 2: lần cuff hợp lệ, người đạt chuẩn, tập phân tích chính | `prepare`: `status = valid`; lần cuff có cờ `ppg:led_not_locked` ra khỏi hiệu chuẩn, phiên đạt, tập chính, tập học và endpoint 3, vào lại endpoint 6 (sửa 2026-11-15, chờ duyệt; mục 4.3 ý 19); phiên đạt khi ≥ 2 lần cuff tính được PPG và PAT; một lần cuff có `led_readjusted` ở phiên ≥ 2 thì **cả phiên** không đạt, ra khỏi tập chính và tập học; một dòng có `pilot` thì loại người đó. Ba cột 0/1 đọc qua một hàm `flag01`; dòng không phải SYNTHETIC thiếu cột thì dừng |
| Mục 2, 9: ≥ 15 người đạt chuẩn | Dưới 15 vẫn chạy, report có `below_min_eligible` và `warnings` |
| Mục 4: BP₀, đặc trưng nền, Δ | Trung bình M0 hợp lệ phiên 1; trung vị đặc trưng trên các lần M0 đó |
| Mục 4: Ridge α = 1, không hệ số chặn, chia SD, trọng số 1 / số lần cuff | `loso_ridge`, cùng phép tính với `rq1_holm_loso.loso_ridge` |
| Mục 4: baseline theo pha, độ lệch hằng số, biến thể trung vị | `phase_mean`; số lượt có pha rỗng theo pha (`phase_baseline_empty_phase_folds`), lần cuff mỗi pha không vào tập chính và số phiên ≥ 2 thiếu pha (`counts.skipped_by_phase`) |
| Mục 3 endpoint 10: biến chỉ pha | `phase_columns` (M1, M2, phiên ≥ 2) |
| Mục 5: bootstrap theo người, 10 000 lượt, khoảng bao | `draw_counts`, `mean_intervals.interval(..., "t_envelope")`; cùng lượt rút cho d, d⁰, dᴾ |
| Mục 5: độ nhạy theo kiểu CI | `ci_sensitivity`: làm lại kết luận chính (d, d⁰, Holm) với percentile, BCa, bootstrap-t, Student t; `changed` liệt kê kiểu CI làm kết luận đổi |
| Mục 6: Holm phương án A | `main_decision` (dùng `rq1_holm_loso.holm`) |
| Mục 7: đọc theo δ | `reading`; δ null thì `delta_not_set` |
| Mục 10: dữ liệu thiếu, lượt dừng | Không điền; lần cuff mất PAT vẫn vào endpoint 3; lượt dừng giữ ở phân tích chính, bỏ ở endpoint 7 (hiệu chuẩn giữ như phân tích chính; báo số lần cuff bỏ và số lần cuff chính mất); tỷ lệ mất ECG theo người (`ecg_loss_share`) |
| Mục 3 endpoint 11 | Trung bình hiệu và CI 95 % theo cách tính chính |

### 4.2. Kết quả test (`tests/test_rq1_analysis.py`, SYNTHETIC)

- Khớp `rq1_holm_loso` trên cùng dữ liệu: d, d⁰, dᴾ theo người và endpoint 10 lệch ≤ 10⁻⁹ mmHg.
- PAT giúp rõ cả hai đầu ra: kết luận chính đạt ở 97,5 % cho SBP và DBP, dᴾ dưới 0.
- PAT không thêm gì: không đầu ra nào được tuyên bố, CI của d chạm 0.
- Chỉ SBP có hiệu ứng: SBP được tuyên bố ở 97,5 %, DBP xét ở 95 % và không được tuyên bố.
- Thiếu lần cuff: người chỉ còn phiên 1 và người có phiên 1 không đạt bị loại kèm lý do; lần cuff
  mất PAT ra khỏi phép so chính nhưng vẫn vào endpoint 3; lần cuff không có số không được điền.
- Người bị giữ lại không vào phần học của lượt đó (Ridge, chia SD, baseline theo pha); đổi nhãn
  của người đó không đổi dự đoán cho người đó.
- Thêm 2026-11-13, mỗi test hỏng nếu bỏ đúng điều nó kiểm:
  - Holm: d dưới 0 mà d⁰ không thì không tuyên bố; cả hai đầu ra chỉ đạt ở 95 % thì không tuyên
    bố gì; một đầu ra đạt 97,5 % thì đầu ra kia xét ở 95 %;
  - một lần cuff có `led_readjusted` loại cả phiên khỏi tập chính và tập học;
  - một dòng `pilot = 1` loại người đó; dòng không SYNTHETIC thiếu `pilot`, `led_readjusted` hay
    `safety_stop` thì dừng;
  - endpoint 7 báo đúng số lần cuff bị bỏ; `safety_stop` viết `"true"` cũng được nhận;
  - số lần cuff khác nhau giữa người: hệ số Ridge (trọng số 1/số lần cuff) và baseline theo pha
    (trung bình theo người trước) khớp phép tính tay;
  - CI chính bằng đúng `interval(..., "t_envelope")` trên cùng lượt rút;
  - đếm lượt có pha rỗng; tỷ lệ mất ECG chỉ đếm lần cuff không có HR từ ECG;
  - cổng dữ liệu thật: config chưa `LOCKED`, config chép ra ngoài repo, một file code đổi đều
    bị từ chối.
- Thêm 2026-11-14, sau rà soát độc lập lần hai:
  - số phiên ngược thời gian (hai phiên đổi giờ, hai phiên cùng giờ, một bản ghi muộn xếp vào phiên 1) thì dừng; dòng thật thiếu
    `session_start_utc`, giờ không có múi giờ hay không đúng ISO 8601 thì dừng;
  - `led_readjusted = 1` ở phiên 1 thì dừng;
  - ablation thiếu HRV ở hai lần cuff: hiệu với PPG-only chỉ tính trên các lần cuff còn lại, khớp
    phép tính tay;
  - đếm riêng không có ECG, ECG không dùng được, không có PAT, theo người và theo pha; số lần cuff
    hiệu chuẩn của BP₀ và của từng đặc trưng;
  - cửa sổ không có ECG vẫn ra đúng đặc trưng PPG như khi có ECG, PAT trống, có cờ `ecg:absent`
    (`tests/test_device_features.py`);
  - file đánh dấu `assume-unchanged` rồi sửa thì `committed_unchanged` báo đã đổi (repo Git tạm).
- Thêm 2026-11-15:
  - chỉ SYN_00 còn lần cuff M1: ở lượt giữ SYN_00 lại, cột chỉ M1 của mô hình endpoint 10 bằng 0
    trên mọi lần cuff học, nên mô hình đó không học được. Phân tích vẫn chạy, kết luận chính
    giống hệt lần chạy bỏ hai mô hình endpoint 10, endpoint 10 ghi `not_computed`; trước đó cả
    phân tích dừng;
  - mô hình của phép so chính không học được thì vẫn dừng;
  - cờ `ppg:led_not_locked`: lần cuff mang cờ ra khỏi tập chính và tập học; phiên 1 hiệu chuẩn
    bằng lần M0 còn lại; người không còn lần M0 nào thì bị loại
    (`session1_m0_led_not_locked`); endpoint 6 đưa chúng trở lại; report đếm theo người và pha.

### 4.3. Chỗ SAP chưa đủ rõ để code (đã tự chọn; sửa theo rà soát độc lập và duyệt 2026-11-14)

1. **Lần cuff dùng để học.** SAP mục 4: "mọi lần cuff có nhãn của người huấn luyện". Code học trên
   các lần cuff hợp lệ tính được cả PPG và PAT, của người đạt chuẩn, mọi phiên, trừ phiên ≥ 2 có
   `led_readjusted`. Hai mô hình của phép so chính học trên cùng tập lần cuff. PAT-only và
   ablation học trên các lần cuff có đủ đặc trưng của mô hình đó, trong số các lần cuff học
   được của phép so chính (tập con, không phải mọi lần cuff tính được đặc trưng của mô hình đó).
   Lần cuff M0 phiên 1 vào tập học như SAP mục 4 viết; trung bình ΔBP của chúng bằng 0 theo cách
   tính BP₀, từng lần cuff thì không nhất thiết.
2. **Người huấn luyện.** Chỉ người đạt chuẩn. Người chỉ có phiên 1 không vào phần học.
3. **Đặc trưng nền.** Trung vị trên các lần M0 phiên 1 có nhãn hợp lệ, như BP₀; khớp
   [protocol v0.3](protocol_outline_v0.2.md) mục 3 và SAP mục 4 (lời đã làm rõ 2026-11-14). Mỗi
   đặc trưng chỉ lấy các lần cuff có đặc trưng đó, nên số lần cuff của BP₀ và của từng đặc trưng
   có thể khác nhau; report báo các số này theo người (`counts.calibration_counts`).
4. **HRV của ablation.** SAP không nêu chỉ số; code dùng RMSSD của khoảng RR trong cửa sổ.
   Chỉ cần 3 đỉnh R (2 khoảng RR), không loại nhịp ngoại tâm thu hay nhịp sai. Đây là một ước
   lượng thô cho endpoint mô tả, không phải đo HRV đã kiểm chứng; báo đúng như vậy.
5. **PAT của lần cuff.** Trung vị PAT hợp lệ của `pat-validity-v1` (`pat_ms`); cách ghép của
   `features-sqi-v2` giữ ở cột riêng. Duyệt cách làm hiện tại; phương pháp và cửa sổ vẫn khóa
   trên pilot (SAP mục 4), không chỉnh theo sai số mô hình.
6. **Màu PPG.** Xanh (khe 1, gốc thời gian của các khe); cả ba màu đều được tính. Màu này dùng
   cho **mọi** đặc trưng của bảng (hình thái PPG, HR từ PPG và PAT), không riêng PAT. Chọn cố
   định trước để không chọn kênh theo kết quả; việc là gốc thời gian không chứng minh màu xanh
   có tín hiệu tốt nhất.
7. **Thứ tự phiên.** Số của `session_id` (`S001` là phiên 1), **có kiểm theo thời gian** (sửa
   2026-11-14): bảng đặc trưng có cột `session_start_utc` (giờ PC lúc bắt đầu ghi, từ manifest
   của logger); với mỗi người, mọi bản ghi của một phiên phải bắt đầu sau mọi bản ghi của các
   phiên số nhỏ hơn (giờ muộn nhất của phiên k trước giờ sớm nhất của phiên sau), nếu không thì
   dừng; một bản ghi muộn bị xếp nhầm vào phiên 1 cũng bị bắt. Đánh số nhầm sẽ làm BP₀ lấy từ một buổi sau, hỏng cả d và d⁰. Dòng không
   phải SYNTHETIC thiếu cột này thì dừng.
8. **Seed bootstrap.** 20261113; ghi lại trong commit khóa SAP, trước lần chạy xác nhận.
9. **Endpoint 5 (lọc SQI) và 7 (bỏ lượt dừng).** Sửa và duyệt 2026-11-14: giữ BP₀, đặc trưng
   nền và tư cách đạt chuẩn của phân tích chính; chỉ bỏ lần cuff có cờ khỏi tập học và tập đánh
   giá rồi học lại ([SAP v1](sap_v1.md) mục 3, cách tính endpoint 5 và 7). Report ghi
   `calibration: main_analysis`, người không còn lần cuff đánh giá và số lần cuff còn lại theo
   người.
10. **Endpoint 1, 2, 4, 11.** Báo trung bình hiệu và CI 95 % (1, 2, 11) hoặc MAE và hiệu trung
    bình (4); không áp Holm cho endpoint phụ (không xác nhận). **So trên cùng các lần cuff**
    (sửa 2026-11-14): hiệu của PAT-only, ablation với PPG-only, và của endpoint 10, chỉ tính trên
    các lần cuff mà cả hai mô hình đều có dự đoán (`paired_subject_mae`). Trước đó lần cuff thiếu
    HRV bị bỏ khỏi ablation nhưng vẫn ở PPG-only, trộn hiệu ứng mô hình với hiệu ứng tập cuff.
    Report ghi `paired_cuffs`, `main_set_cuffs`, `paired_subjects`. MAE riêng của từng mô hình
    vẫn tính trên các lần cuff của mô hình đó.
11. **Chưa làm:** endpoint 8 (RQ2b), Bland–Altman, hình. Duyệt việc hoãn, không phải coi SAP đã
    đủ: hình vẫn bắt buộc (SAP mục 11). Phương pháp LoA cho đo lặp đã chọn trước khi có dữ liệu
    (SAP mục 11, 2026-11-15, chờ duyệt); code chưa làm.

Thêm 2026-11-13 (liệt kê để chốt, chưa sửa theo):

12. **Endpoint 5 và 7 đổi BP₀.** Đã xử lý và duyệt 2026-11-14 theo mục 9: hiệu chuẩn giữ như
    phân tích chính; SAP mục 3 có thêm quy tắc này.
13. **"Mất ECG".** `ecg_loss_share` giữ như cũ: lần cuff hợp lệ ở phiên ≥ 2 không có HR từ ECG.
    Sửa 2026-11-14: report tách ba trường hợp theo người và theo pha (`counts.ecg_pat_by_subject`,
    `counts.ecg_pat_by_phase`): `ecg_absent` (cửa sổ không có mẫu ECG nào, cờ `ecg:absent`),
    `ecg_unusable` (có ECG nhưng không ra HR), `pat_failed` (có HR từ ECG nhưng không có PAT hợp
    lệ). Cửa sổ không có ECG vẫn được tính đặc trưng PPG, nên vào được endpoint 3 (SAP mục 10);
    trước đó code dừng trước khi tính PPG.
14. **"Số lần cuff mỗi pha bị bỏ qua"** (SAP mục 4). Bảng đặc trưng không có lịch đo dự kiến, nên
    code báo các dòng mỗi pha không vào tập chính (không hợp lệ, không tính được, phiên chỉnh LED)
    và số phiên ≥ 2 không có lần cuff chính nào của pha đó. Lần đo không được bấm thì không có
    dòng, nên không đếm được trực tiếp. **Giới hạn đã biết, duyệt kèm điều kiện:** cả một phiên
    không ghi thì cũng không có dòng nào. Trước pilot cần một sổ lịch đo dự kiến (người, phiên,
    pha, số lần cuff định đo) để đối chiếu, vì việc bỏ lần đo có thể phụ thuộc BP; đã thêm vào
    việc còn lại của [SAP](sap_v1.md) mục 13.
15. **`led_readjusted` ở phiên 1.** SAP chỉ nói phiên sau. Sửa 2026-11-14: cờ này ở phiên 1 là
    lỗi nhật ký (phiên 1 là lần đặt mã LED đầu tiên, protocol 6.1), nên phân tích dừng và nêu
    người, phiên; trước đó code bỏ qua cờ mà không báo.
16. **Độ nhạy theo kiểu CI** (SAP mục 5). Code so kết luận chính đã tuyên bố hay không; cách đọc
    theo δ và việc vượt baseline theo pha không được so. `robust` chỉ nói về việc tuyên bố.
17. **Mức CI của endpoint 11.** 95 %, như dᴾ; SAP chỉ nói "cùng cách tính".

Thêm 2026-11-15 sau rà soát toàn dự án (chờ duyệt):

18. **Mô hình phụ không học được ở một lượt.** Vòng ngoài chỉ chạy một lần, nên một mô hình
    ngoài phép so chính (PAT-only, ablation, hai mô hình endpoint 10) không được làm dừng kết
    quả chính. Lượt đó không có dự đoán của mô hình phụ; report ghi lượt và lý do
    (`main.model_fit_failures`, `fit_failures` ở từng mô hình); MAE của mỗi mô hình có kèm
    `n_subjects`, số người đứng sau MAE đó. Endpoint 10 cần dự đoán ghép cặp
    cho mọi người đạt chuẩn, thiếu thì ghi `not_computed` thay vì báo trên một tập con; endpoint 3
    lỗi cũng chỉ ghi `not_computed`. Mô hình của phép so chính không học được thì vẫn dừng.
19. **Cờ khóa LED.** Trước đó `ppg:led_not_locked` chỉ bật khi mã khóa có hiệu lực sau đầu
    cửa sổ. `led_lock_status` của mỗi cửa sổ nay là một trong: `locked`; `not_checked` (không có
    mã khóa và không có `subject_id`: bring-up, SYNTHETIC); `no_lock_metadata`; `not_applied`;
    `applied_after_window_start`; `state_unverified` (không tìm được trạng thái nơi mã khóa có
    hiệu lực theo `seq` và `generation`, hay trạng thái đang chạy không phải chip đã cấu hình);
    `codes_differ`. Mọi trạng thái trừ `locked` và `not_checked` bật cờ. Phân tích bỏ đúng lần
    cuff mang cờ ([SAP v1](sap_v1.md) mục 2, sửa 2026-11-15). Giới hạn đã biết: thời điểm của
    một trạng thái là mốc của packet `0xD2` đầu tiên báo nó, nên một thay đổi ngay trước mép
    cửa sổ mà packet báo tới sau mép thì không thấy; khoảng hở bằng độ trễ firmware gửi `0xD2`
    sau khi cấu hình chip.
20. **Còn mở: mã khóa giữa các phiên.** Mỗi bản ghi chỉ được so với mã trong metadata của chính
    nó, nên metadata ghi sai mã ở một phiên sau vẫn qua. Cần kiểm mã khóa giống nhau giữa các
    phiên của cùng một người trước pilot (SAP mục 13).

## 5. Tự chốt trong việc này (duyệt 2026-11-14)

| Chỗ | Giá trị | Lý do |
| --- | --- | --- |
| Định dạng output ingest | [quy ước dữ liệu](../data_convention.md) mục 4; thêm cột `session_start_utc` và cờ `ecg:absent` (2026-11-14) | Giao diện cho mốc/PAT và RQ1 |
| Định dạng `cuff_log.csv` | Mục 4.4 của quy ước | Trước đó chưa chốt; cần để nối nhãn với `t0` |
| Cửa sổ chính 30 s | `window.primary_pre_s` | Đề xuất của SQI v1 mục 2; duyệt làm giá trị cho pilot, khóa trên pilot |
| Màu PPG cho mọi đặc trưng của bảng | xanh | Khe 1 là gốc thời gian; không phụ thuộc Δ(`LED_PW`); xem mục 4.3 ý 6 |
| Tham số mốc | mặc định `features-sqi-v1` | Không chỉnh theo dữ liệu nào; chạy đúng trên SYNTHETIC chưa chứng minh hợp với tín hiệu thiết bị, khóa trên pilot |
| Tham số PAT hợp lệ | như `week05_fiducials.json` | Đã duyệt 2026-10-25; là quy tắc kỹ thuật, chưa kiểm chứng sinh lý |
| Phần học, nền, HRV, seed | Mục 4.3 | SAP chưa nói rõ |
| `led_readjusted`, `pilot` điền ở nhật ký cuff (2026-11-13) | [quy ước dữ liệu](../data_convention.md) mục 4.4 | Metadata logger viết trước khi biết buổi có chỉnh LED |
| Bộ lọc tín hiệu thiết bị (2026-11-15, chờ duyệt) | `zero_phase`, ECG 0,5–40 Hz, PPG 0,5–8 Hz, bậc 2 | Bộ lọc thông cao số của MAX30001 đã tắt vì lọc 0,5 Hz làm offline; không lọc thì trôi nền che nhịp; khóa trên pilot (mục 3.4) |
| Cờ khóa LED và cách loại (2026-11-15, chờ duyệt) | Mục 4.3 ý 19; [SAP v1](sap_v1.md) mục 2 | Biên độ PPG đổi theo dòng LED; nền M0 chưa khóa làm lệch mọi Δ |
| Ngưỡng cờ A3 trên mọi bản ghi (2026-11-15, chờ duyệt) | 0,2 ms trên trung vị khối 10 s | Đúng tiêu chí A3 của kế hoạch đo đồng bộ; chỉ báo |
| Trạng thái khóa của config RQ1 (2026-11-13) | `status = LOCKED`, đặt trong commit khóa SAP; trước đó là `APPROVED_NOT_LOCKED` | Cổng dữ liệu thật cần một giá trị cố định; cổng so nội dung với HEAD và chỉ chặn chạy nhầm (mục 1) |
