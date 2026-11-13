# Quy ước dữ liệu và ước lượng dung lượng

Quy ước dữ liệu chính thức (thư mục, ID, tên file, đơn vị, tần số lấy mẫu, truy
xuất nguồn gốc) là [quy_uoc_du_lieu.md](quy_uoc_du_lieu.md). File này chỉ giữ
quy tắc đặt tên ngắn gọn và ước lượng dung lượng lưu trữ; nếu hai file mâu
thuẫn, `quy_uoc_du_lieu.md` được ưu tiên.

## 1. Quy tắc đặt tên

- Phần không phải ID dùng chữ thường và snake_case (ví dụ `ecg_raw_2026.csv`).
- File dữ liệu **dẫn xuất** (`data/interim/`, `data/processed/`) theo mẫu
  `<subject_id>_<session_id>_<event_id>_<data_type>.<ext>` như định nghĩa trong
  `quy_uoc_du_lieu.md`. Phần ID giữ đúng định dạng ở đó (ví dụ
  `SUB001_S001_E01_window.parquet`).
- Raw thiết bị không theo mẫu trên (chốt 2026-10-29, `quy_uoc_du_lieu.md` mục 1–2):
  mỗi lần ghi là một thư mục `data/raw/<subject_id>/<session_id>/<recording>/` chứa
  một `raw.bin`. Sửa 2026-11-10: bản trước lấy `SUB001_S001_E01_raw.csv` làm ví dụ.

## 2. Tần số lấy mẫu (trạng thái)

| Nguồn | ECG | PPG | Trạng thái |
| --- | --- | --- | --- |
| PulseDB Subset (công khai) | 125 Hz | 125 Hz | Suy ra từ shape: 1250 mẫu mỗi đoạn 10 giây; khớp với bài báo PulseDB, xem [provenance PulseDB](pulsedb_provenance.md), mục 6 |
| Thiết bị prototype (V1-module) | 512 sps (MAX30001, chốt 2026-10-23) | 200 sps mỗi khe, MAX30101 ba khe xanh/đỏ/IR, `SMP_AVE = 1` (chốt 2026-10-24) | Giá trị danh định; tốc độ thực phải đo. Lý do và độ rộng xung PPG còn mở: [interface_power_sampling_v0.md, mục 4 và 6](../configs/hardware/interface_power_sampling_v0.md) |

Không giả định hai kênh dùng chung một tần số lấy mẫu hay một clock.

## 3. Ước lượng dung lượng

Ước lượng để lập kế hoạch lưu trữ, không phải số đo:

- Giả định (cập nhật 2026-10-25): raw là luồng packet nhị phân `raw.bin` của logger
  ([packet schema V0.1](../configs/hardware/Packet_Schema_V0.1.md) và V0.2), mỗi packet
  42 byte header/CRC cộng 4 byte mỗi mẫu; số mẫu mỗi packet như firmware V1 hiện dùng:
  ECG 512 sps, 16 mẫu (106 B); PPG 3 khe × 200 sps, 8 mẫu (74 B); IMU 6 trục × 100 Hz,
  10 mẫu (82 B); nhiệt độ 1 Hz; `0xD1`/`0xD2` mỗi 10 s.
- Kết quả: khoảng 3,4 + 5,6 + 4,9 kB/s ≈ 14 kB/s, tức khoảng 0,84 MB mỗi phút hay
  50 MB mỗi giờ `raw.bin`. `packets.csv` và `samples.csv` logger sinh ra lớn hơn
  vài lần; chúng sinh lại được từ raw.

Tính lại khi đổi số mẫu mỗi packet hay tốc độ lấy mẫu.

## 4. Đầu ra của ingest phiên thiết bị (`device-session-v1`, đề xuất 2026-11-13, chờ duyệt)

Giao diện giữa ingest, mốc/PAT và phân tích RQ1. Code:
[session_ingest.py](../software/device/session_ingest.py),
[features.py](../software/device/features.py), script
[device_session.py](../scripts/device_session.py), config
[device_session_v1.json](../configs/data/device_session_v1.json). Cách chạy và giới hạn ở
[device_session_pipeline.md](protocol/device_session_pipeline.md).

### 4.1. Đầu vào và nơi ghi

- Đầu vào là một thư mục bản ghi của `packet-logger-v3` có `session_manifest.json`. Ingest
  kiểm SHA-256 của `raw.bin` và mọi file trong `outputs_sha256`, kiểm số packet của
  `packets.csv` với `decode.json`, số mẫu từng kênh của `samples.csv` với `decode.json`.
  Lệch một chỗ là dừng (`IngestError`), không sửa.
- Không ghi gì vào thư mục bản ghi. Output là thư mục mới, ngoài `data/raw/`: dữ liệu người
  ở `data/interim/<subject_id>/<session_id>/<recording>/`; SYNTHETIC và bring-up ở
  `runs/device_session/`. Không ghi đè.

### 4.2. Thời gian mẫu (`timebase.csv`, `window_samples.csv`)

- Mọi thời gian là **µs trên đồng hồ `esp_timer` của MCU** (`clock_id` của metadata), gốc là
  lúc MCU khởi động của `device_session_id` đó. Cột `t_us`, số thực.
- Mỗi kênh giữ thời gian riêng. Không resample, không dịch kênh này cho khớp kênh kia, không
  ghép theo chỉ số mẫu.
- Theo từng (`device_session_id`, kênh, `chain_id`): hồi quy `T_ANCHOR_US = a + b·k` trên các
  packet có `disposition = accepted`, k là chỉ số mẫu cuối của packet (Packet Schema V0.1 mục
  5.3). Rồi `t_us(k) = a + b·k − L`, L là `latency_l_us` của kênh trong metadata (ECG có mốc
  `SAMP` dùng `latency_samp_l_us`; không trộn hai nguồn mốc trong một chuỗi).
- Khe PPG j cộng (j − 1)·Δ(`LED_PW`) theo trạng thái MAX30101 của `0xD2` (Packet Schema V0.1
  mục 7). Không có `0xD2` hoặc `LED_PW` đổi trong phiên thì không cộng và gắn cờ
  `slot_offset_unknown`.
- L là null thì thời gian không trừ L, kênh mang cờ `latency_unknown`, và PAT không được tính
  (`pat:upstream_delay_unknown`).
- `timebase.csv`: `device_session_id, channel, chain_id, n_anchors, a_us, b_us, fs_hz,
  residual_sd_us, anchor_source, nominal_rate, latency_l_us`. Chuỗi chỉ có một mốc dùng tốc độ
  danh định (`nominal_rate = True`, cờ `single_anchor_nominal_rate`).
- `window_samples.csv`: `event_id, channel, name, chain_id, sample_index, t_us, value` cho mọi
  mẫu trong cửa sổ lưu `[t0 − 60 s, t0)` của từng lần cuff.
- Đơn vị `value`: mã ADC như `samples.csv`. ECG là nguyên word 24 bit của MAX30001; phần tính
  đặc trưng tách mẫu 18 bit có dấu (`ecg_codes`). PPG là số đếm 18 bit. Chưa đổi sang mV hay nA.

### 4.3. Sự kiện (`events.csv`)

`device_session_id, event_ordinal, code, name, t_us`. Mã: 1 `cuff_t0`, 2 `cuff_end`,
3 `sync_pulse`, 4 `operator_mark` (Packet Schema V0.1 mục 10). `t_us` là `T_ANCHOR_US` của packet
`0xC1`, không trừ độ trễ.

### 4.4. Nhật ký cuff (`cuff_log.csv`, đầu vào) và cửa sổ (`cuffs.json`)

Định dạng nhật ký cuff (chốt 2026-11-13, chờ duyệt; trước đó metadata ghi "chưa chốt"). Một
dòng mỗi lần bấm cuff, cột đúng thứ tự:

`recording, event_id, phase, device_session_id, t0_event_ordinal, phase_mark_event_ordinal,
cuff_end_event_ordinal, sbp_mmhg, dbp_mmhg, pulse_rate_bpm, status, safety_stop, led_readjusted,
pilot, note`

- `event_id` dạng `E01`, duy nhất trong buổi; `phase` ∈ {M0, M1, M2}.
- `status`: `valid` (có SBP/DBP), `no_result` (máy xả bình thường nhưng không ra số; lần đo lại
  là một dòng mới), `device_error` (máy lỗi). Chỉ dòng `valid` có SBP/DBP; DBP < SBP.
- `safety_stop`: 1 nếu lượt có cờ dừng an toàn (SAP mục 10), ngược lại 0.
- `led_readjusted`, `pilot` (thêm 2026-11-13, chờ duyệt): 0 hoặc 1, **giống nhau trên mọi dòng**
  của một nhật ký (một nhật ký là một buổi của một người); ingest từ chối nếu khác. `led_readjusted`
  = 1 khi buổi đó chỉnh lại mã LED (protocol 6.1, "Buổi sau lệch thang"). `pilot` = 1 khi người
  này làm pilot (SAP mục 1–2). Lý do điền ở nhật ký cuff, không ở metadata phiên của logger:
  metadata được viết lúc bắt đầu ghi, trước khi biết buổi có phải chỉnh LED hay không; nhật ký cuff
  được điền trong và sau buổi, cùng chỗ với các thông tin khác của buổi.
- Ba cột `*_event_ordinal` là `event_ordinal` của sự kiện mã 1, 4, 2 trong `decode.json`, do
  người vận hành điền sau buổi. Ingest từ chối khi ordinal không có hoặc sai mã. `t0` bắt buộc;
  thiếu `cuff_end` thì gắn cờ `cuff_end_missing`; M1/M2 thiếu mốc pha thì `phase_mark_missing`.
- `recording` là tên thư mục bản ghi; một buổi nhiều bản ghi dùng chung một nhật ký.

`cuffs.json`: mỗi lần cuff có `t0_us`, `cuff_end_us`, cửa sổ lưu `stored_window_us` =
`[t0 − 60 s, t0)`, các cửa sổ phân tích `pre_10s`, `pre_20s`, `pre_30s`, `pre_60s`
(protocol 6.2), đoạn bơm `cuff_inflating_us` = `[t0, cuff_end]`, `inflation_s`,
`phase_mark_to_t0_s` và cờ `window_starts_before_phase_mark` khi cửa sổ lưu bắt đầu trước mốc
pha (protocol 6.4: cửa sổ phải nằm trọn trong nghiệm pháp).

### 4.5. Tóm tắt phiên (`session_summary.json`)

Thời lượng; theo kênh: tốc độ danh định, tốc độ ước lượng và độ lệch ppm, số chuỗi, packet
nhận, mất, tỷ lệ mất, mẫu nhận, mẫu mất đã đếm, số khoảng trống, packet bị cách ly, đếm bit
STATUS (FIFO tràn, bộ đệm MCU tràn, lead-off, lỗi AFE, ALC tràn), L đã trừ chưa, offset khe; số
sự kiện theo mã, số marker, số lần cuff theo `status`, `issue_counts` của logger, cờ của ingest,
`ppg_led_lock`.

### 4.6. Bảng đặc trưng theo lần cuff (`cuff_features.csv`)

Đầu vào của [run_rq1_analysis.py](../scripts/run_rq1_analysis.py). Một dòng mỗi lần cuff:

`subject_id, session_id, recording, event_id, phase, status, safety_stop, led_readjusted, pilot,
sbp_mmhg, dbp_mmhg, window_pre_s, ppg_color, ppg_rise_time_ms, ppg_width50_ms, ppg_amplitude, ppg_hr_bpm,
ecg_hr_bpm, ecg_rmssd_ms, pat_ms, pat_sqi_v2_median_ms, pat_n_valid, flags, source_type`

- Đặc trưng tính trên cửa sổ chính `[t0 − 30 s, t0)` (đề xuất, khóa trên pilot), của màu ghi
  ở `ppg_color` (đề xuất: xanh, khe 1). Ô trống là không tính được.
- `pat_ms` là trung vị PAT hợp lệ của `pat-validity-v1`; `pat_sqi_v2_median_ms` là trung vị
  của cách ghép `features-sqi-v2`, giữ để so.
- `flags`: cờ SQI v1 (mục 3.1, 3.3) và cờ cửa sổ, nối bằng `;`.
- `led_readjusted`, `pilot` (0/1) chép từ nhật ký cuff (mục 4.4; thêm 2026-11-13, chờ duyệt).
  Phân tích RQ1 bắt buộc hai cột này và `safety_stop` trên mọi dòng không phải SYNTHETIC; thiếu
  hay sai giá trị thì dừng, không mặc định 0. `led_readjusted` loại cả buổi đó (phiên ≥ 2) khỏi tập
  chính và tập học; `pilot` loại người đó (SAP mục 1–2).
