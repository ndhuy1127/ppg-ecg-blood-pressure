# Pipeline dữ liệu thiết bị: ingest, mốc và PAT, phân tích RQ1

> **Trạng thái: đề xuất ngày 2026-11-13, chờ duyệt.** Mới chạy trên dữ liệu SYNTHETIC. Chưa có
> bản ghi thiết bị nào. Kết quả SYNTHETIC chỉ kiểm chứng code, không nói gì về thiết bị hay BP.

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
khác HEAD (SAP mục 12; sửa 2026-11-13, chờ duyệt). Report ghi `approval_committed`.

Thêm 2026-11-14 (chờ duyệt): `LOCKED` gồm cả toàn bộ code của bước tính đặc trưng
(`device_session.py` và mọi module nó import, danh sách `CODE`; test so danh sách với đồ thị
import) và `configs/data/device_session_v1.json`. Mỗi `cuff_features.csv` phải có
`provenance.json` do `device_session.py` ghi cạnh nó. Với dữ liệu thật: provenance phải ghi
workspace sạch, có commit, hash code và config bằng hash của các file đang khóa. Với mọi bảng có
provenance: `source_type` của dòng phải khớp provenance, nên bảng thiết bị bị gắn nhầm SYNTHETIC
sẽ bị từ chối. Report ghi `feature_provenance`.

Sửa 2026-11-14 sau rà soát độc lập (chờ duyệt): `provenance.json` ghi hash của
`cuff_features.csv` và `cuff_features.json` (`outputs_sha256`); runner từ chối bảng không
khớp hash này, nên không thể đặt bảng khác hay bảng đã sửa cạnh một provenance. Với dữ liệu
thật, `git_commit` phải là commit có thật của repo và chứa đúng code và config đã ghi trong
provenance. Danh sách khóa có thêm các `__init__.py` của package cha (Python chạy chúng khi
import). Endpoint 5 và 7 báo thêm `confirmatory: false`, số người còn được đánh giá, cờ dưới
15 người, và tách số lần cuff có cờ thành số bỏ khỏi tập học và số bỏ khỏi tập đánh giá.

## 2. Ingest (việc F)

- Kiểm bản ghi theo manifest của logger. Thiếu manifest, lệch SHA-256, lệch số packet hay số mẫu
  thì dừng. Không sửa, không nội suy.
- Thời gian mẫu theo Packet Schema V0.1 mục 5.3: hồi quy mốc theo chỉ số mẫu cho từng chuỗi, trừ
  độ trễ hiệu dụng L của metadata, cộng offset khe PPG theo `LED_PW` của `0xD2`. Hồi quy cho luôn
  tốc độ thực của từng kênh.
- Cửa sổ theo protocol 6.2 và 6.4: lưu `[t0 − 60 s, t0)`; phân tích 10/20/30/60 s; đoạn bơm
  `[t0, cuff_end]`; với M1/M2 kiểm cửa sổ có nằm sau mốc pha (mã 4) không.
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

## 4. Phân tích RQ1 (việc H)

### 4.1. Ánh xạ với SAP v1

| SAP | Code |
| --- | --- |
| Mục 2: lần cuff hợp lệ, người đạt chuẩn, tập phân tích chính | `prepare`: `status = valid`; phiên đạt khi ≥ 2 lần cuff tính được PPG và PAT; một lần cuff có `led_readjusted` ở phiên ≥ 2 thì **cả phiên** không đạt, ra khỏi tập chính và tập học; một dòng có `pilot` thì loại người đó. Ba cột 0/1 đọc qua một hàm `flag01`; dòng không phải SYNTHETIC thiếu cột thì dừng |
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

### 4.3. Chỗ SAP chưa đủ rõ để code (đã tự chọn, chờ duyệt)

1. **Lần cuff dùng để học.** SAP mục 4: "mọi lần cuff có nhãn của người huấn luyện". Code học trên
   các lần cuff hợp lệ tính được cả PPG và PAT, của người đạt chuẩn, mọi phiên, trừ phiên ≥ 2 có
   `led_readjusted`. Hai mô hình của phép so chính học trên cùng tập lần cuff. PAT-only và
   ablation học trên các lần cuff có đủ đặc trưng của mô hình đó.
2. **Người huấn luyện.** Chỉ người đạt chuẩn. Người chỉ có phiên 1 không vào phần học.
3. **Đặc trưng nền.** Trung vị trên các lần M0 phiên 1 có nhãn hợp lệ, như BP₀. Một lần M0 không
   ra số cuff vẫn có cửa sổ tín hiệu; SAP không nói có dùng không.
4. **HRV của ablation.** SAP không nêu chỉ số; code dùng RMSSD của khoảng RR trong cửa sổ.
5. **PAT của lần cuff.** Trung vị PAT hợp lệ của `pat-validity-v1` (`pat_ms`); cách ghép của
   `features-sqi-v2` giữ ở cột riêng. SAP để khóa trên pilot.
6. **Màu PPG.** Xanh (khe 1, gốc thời gian của các khe); cả ba màu đều được tính.
7. **Thứ tự phiên.** Số của `session_id` (`S001` là phiên 1).
8. **Seed bootstrap.** 20261113, đề xuất; ghi lại trong commit khóa SAP.
9. **Endpoint 5 (lọc SQI) và 7 (bỏ lượt dừng).** Sửa và duyệt 2026-11-14: giữ BP₀, đặc trưng
   nền và tư cách đạt chuẩn của phân tích chính; chỉ bỏ lần cuff có cờ khỏi tập học và tập đánh
   giá rồi học lại ([SAP v1](sap_v1.md) mục 3, cách tính endpoint 5 và 7). Report ghi
   `calibration: main_analysis`, người không còn lần cuff đánh giá và số lần cuff còn lại theo
   người.
10. **Endpoint 1, 2, 4, 11.** Báo trung bình hiệu và CI 95 % (1, 2, 11) hoặc MAE và hiệu trung
    bình (4); chưa áp Holm cho endpoint phụ.
11. **Chưa làm:** endpoint 8 (RQ2b), Bland–Altman (SAP để chọn phương pháp LoA sau), hình.

Thêm 2026-11-13 (liệt kê để chốt, chưa sửa theo):

12. **Endpoint 5 và 7 đổi BP₀.** Đã xử lý và duyệt 2026-11-14 theo mục 9: hiệu chuẩn giữ như
    phân tích chính; SAP mục 3 có thêm quy tắc này.
13. **"Mất ECG".** Code đếm lần cuff hợp lệ ở phiên ≥ 2 không có HR từ ECG (`ecg_hr_bpm` trống).
    SAP mục 2 và 10 không định nghĩa; lần cuff có ECG nhưng không ghép được PAT không tính là mất
    ECG.
14. **"Số lần cuff mỗi pha bị bỏ qua"** (SAP mục 4). Bảng đặc trưng không có lịch đo dự kiến, nên
    code báo các dòng mỗi pha không vào tập chính (không hợp lệ, không tính được, phiên chỉnh LED)
    và số phiên ≥ 2 không có lần cuff chính nào của pha đó. Lần đo không được bấm thì không có
    dòng, nên không đếm được trực tiếp.
15. **`led_readjusted` ở phiên 1.** SAP chỉ nói phiên sau. Code bỏ qua cờ ở phiên 1.
16. **Độ nhạy theo kiểu CI** (SAP mục 5). Code so kết luận chính đã tuyên bố hay không; cách đọc
    theo δ không được so.
17. **Mức CI của endpoint 11.** 95 %, như dᴾ; SAP chỉ nói "cùng cách tính".

## 5. Tự chốt trong việc này (chờ duyệt)

| Chỗ | Giá trị | Lý do |
| --- | --- | --- |
| Định dạng output ingest | [quy ước dữ liệu](../data_convention.md) mục 4 | Giao diện cho mốc/PAT và RQ1 |
| Định dạng `cuff_log.csv` | Mục 4.4 của quy ước | Trước đó chưa chốt; cần để nối nhãn với `t0` |
| Cửa sổ chính 30 s | `window.primary_pre_s` | Đề xuất của SQI v1 mục 2; khóa trên pilot |
| Màu PPG cho PAT | xanh | Khe 1 là gốc thời gian; không phụ thuộc Δ(`LED_PW`) |
| Tham số mốc | mặc định `features-sqi-v1` | Không chỉnh theo dữ liệu nào |
| Tham số PAT hợp lệ | như `week05_fiducials.json` | Đã duyệt 2026-10-25 |
| Phần học, nền, HRV, seed | Mục 4.3 | SAP chưa nói rõ |
| `led_readjusted`, `pilot` điền ở nhật ký cuff (2026-11-13) | [quy ước dữ liệu](../data_convention.md) mục 4.4 | Metadata logger viết trước khi biết buổi có chỉnh LED |
| Trạng thái khóa của config RQ1 (2026-11-13) | `status = LOCKED`, đặt trong commit khóa SAP | Cổng dữ liệu thật cần một giá trị cố định |
