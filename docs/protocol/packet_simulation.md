# Giao diện packet giả lập trên PC

## Ranh giới

**SYNTHETIC ONLY.** Đây là đầu ra hỗ trợ phần mềm Tuần 3, không phải schema
phần cứng đã chốt, driver/firmware hoặc kết quả đồng bộ hai cảm biến thật.
Không dùng dữ liệu này để đánh giá
waveform, PAT, BP, độ trễ sinh lý, năng lượng hoặc hiệu năng thiết bị.

Tham khảo yêu cầu generator/replay và packet ở `origin/dev/ducanh@40ede49`.
Ở commit đó, `configs/hardware/Packet_Schema_V0.1.md` là bản gốc của Đức Anh. Bản
cùng tên trong nhánh này đã được viết lại (layout byte, `T_ANCHOR_US`/`T_FIRST_US`,
`STATUS`) và khác bản gốc; mô phỏng giữ định nghĩa timestamp của bản gốc (thời
điểm sample đầu batch). Schema đã chốt định nghĩa timestamp ngày 2026-10-23 (mục 3, 5); bản v2 giữ định nghĩa cũ.
Version riêng `synthetic-packet-v2`; JSON, không phải binary wire format.
Bảng đối chiếu trường với schema phần cứng dự kiến nằm ở
[Packet_Schema_V0.1.md mục 14](../../configs/hardware/Packet_Schema_V0.1.md).
Code: `software/data_io/packet_simulation.py`; runner: `scripts/simulate_packets.py`.

Từ Tuần 5 có thêm `synthetic-packet-v3` (luồng byte đúng layout V0.1, mục cuối
của tài liệu này) để test [logger](packet_logger.md). **v2 vẫn được hỗ trợ**,
không đổi code, config, đáp án hay hash; v1 vẫn bị từ chối.

## Schema, clock và thông số giả lập

Mỗi packet gồm:

| Trường | Quy ước giao diện giả lập |
| --- | --- |
| `schema_version`, `source_type` | `synthetic-packet-v2`, `SYNTHETIC` bắt buộc |
| `session_id`, `clock_id` | Một phiên và một clock chung giả lập; không gộp phiên/clock khác |
| `channel` | ECG hoặc PPG; sequence riêng theo kênh |
| `sequence` | Integer tăng trong chuỗi chuẩn, phạm vi do config khai báo |
| `timestamp_us` | Integer microsecond của sample đầu batch, không phải lúc nhận gói |
| `timestamp_kind`, `timestamp_unit` | `first_sample`, `us` |
| `sample_count`, `fs_hz` | Số mẫu và tần số integer của từng kênh, khớp config |
| `samples`, `sample_unit` | List integer int32 giả lập, `synthetic_count`; không phải mV/ADC thật |

Thời gian sample i là `timestamp_us + i * 1_000_000 / fs_hz`.
Generator tính mốc batch bằng phân số, làm tròn microsecond một lần cho mỗi
packet; validator cho phép thêm tối đa 1 µs do lượng tử hóa của cả anchor và
packet (mỗi mốc tối đa 0,5 µs), kể cả khi mất gói đầu. Kiểm tra offset cũng dùng
biên cặp 1 µs; offset chèn phải lớn hơn tolerance cộng biên này để test có thể
phát hiện. Arrival order không được dùng làm thời gian mẫu.

Trong replay v2, `time_encoding` là `rational-string-us`: `timestamp_us` của
sample, `nominal_start_us`/`nominal_end_us` của gap và
`offset_ppg_minus_ecg_us` là chuỗi phân số chính xác, ví dụ `"1000000"` hoặc
`"32062500/32"`; offset không xác định vẫn là `null`. Packet đầu vào vẫn dùng
timestamp integer. Đọc bằng `Fraction(value)` trong Python. Không chuyển thời
gian tuyệt đối lớn sang float; nếu cần vẽ, trừ epoch bằng Fraction trước rồi mới
chuyển thời gian tương đối sang float. Điều này giữ độ chính xác với epoch gần
giới hạn integer và sampling rate tạo khoảng mẫu phân số.

Đây là thay đổi không tương thích với output v1: config/packet v1 bị từ chối.
Tạo lại artifact bằng config v2; không chỉ sửa version trên artifact cũ.
Issue counts/giá trị mẫu giữ nguyên
với config mặc định; hash packet/replay thay đổi do version/biểu diễn thời gian.

Config `configs/hardware/packet_simulation.json` chứa seed `20261010`, 4 packet
mỗi kênh, ECG **512 Hz/16 mẫu**, PPG **128 Hz/4 mẫu**, offset **20.000 µs**,
tolerance **1 µs**. Tất cả là **thông số mô phỏng**, không chốt fs PPG, buffer,
clock hay tiêu chí đạt phần cứng. Payload là số ngẫu nhiên tái lập, không mô
phỏng hình thái sinh lý. Config có giới hạn tổng một triệu mẫu để tránh chạy dài.
Config từ chối sequence cuối hoặc timestamp đầu batch cuối vượt `2**63 - 1`,
kể cả offset có thể chèn, trước khi sinh packet. Đây là giới hạn integer của
giao diện giả lập, không phải quy định uint32/uint64 của phần cứng.

## Sáu tình huống và xử lý

| Case | Lỗi chèn vào PPG theo config mặc định | Kết quả mong đợi |
| --- | --- | --- |
| `valid` | Không lỗi | 4 packet/kênh, không issue |
| `missing` | Bỏ sequence 101 | Báo missing; 1 gap 4 mẫu, không nối giả dữ liệu |
| `duplicate` | Gửi sequence 101 hai lần | Báo duplicate; giữ đúng một bản |
| `reordered` | Gửi 102 trước 101 | Báo out_of_order; offline sort và dựng lại dữ liệu đúng |
| `timestamp` | Cộng 20 ms vào sequence 101 | Báo timestamp_anomaly, cách ly packet, giữ gap |
| `offset` | Cộng 20 ms toàn chuỗi PPG | Báo channel_offset +20 ms; giữ nguyên timestamp hai kênh |

Fixture có thể tái tạo bằng config + case + seed. Expected results độc lập nằm
ở `tests/fixtures/packet_simulation_expected.json`; pytest kiểm tra exact issue
counts, packet/sample counts, giá trị, sample time, gap và offset.
Không coi exit 0 của generator là test PASS: các case lỗi phải tạo issue đúng
đáp án, còn bộ pytest tổng thể phải PASS. Input sai schema làm lệnh exit 1.

Receiver replay offline không đổi input, loại exact duplicate; bản sao cùng
sequence nhưng khác nội dung bị cách ly với gap. Số packet kỳ vọng có trong
config nên phát hiện được thiếu đầu/cuối chuỗi. Nominal gap intervals là thời
gian dự kiến trên clock giả lập, không phải mẫu đo hay nội suy dữ liệu.

**Giới hạn offset:** anchor là packet hợp lệ đầu tiên về cấu trúc, quy về sequence
start. Hai sequence start giả lập có cùng epoch đã biết nên có thể so offset.
**Dấu:** `offset_ppg_minus_ecg_us` = anchor PPG − anchor ECG; dương nghĩa là
timestamp PPG muộn hơn timestamp ECG cho cùng một thời điểm giả lập (case
`offset` cho +20 000 µs). Trong
[kế hoạch đo 10 phút](../../hardware/test_reports/sync_10min_test_plan.md) mục 5,
đại lượng tương ứng là `L_PPG − L_ECG`, ngược dấu với offset `L_ECG − L_PPG` của
kế hoạch.
Nếu anchor bị hỏng hoặc clock có drift, kết quả có thể mơ hồ; chưa có estimator
đồng bộ sensor tổng quát, clock mapping/correction, sequence wrap/reset, live
reorder buffer, FIFO/CRC/status hoặc decoder phần cứng. Không dịch kênh để ép
đỉnh ECG/PPG trùng nhau; offset này không phải PAT.

## Chạy và bàn giao

Ví dụ từ PowerShell, dùng môi trường đã có:

```powershell
& 'D:\ppg-ecg-blood-pressure\.venv\Scripts\python.exe' -B 'D:\ppg-ecg-blood-pressure\scripts\simulate_packets.py' --case missing --output 'D:\ppg-ecg-blood-pressure\runs\packet_simulation\missing_01'
& 'D:\ppg-ecg-blood-pressure\.venv\Scripts\python.exe' -B 'D:\ppg-ecg-blood-pressure\scripts\simulate_packets.py' --packets 'D:\ppg-ecg-blood-pressure\runs\packet_simulation\missing_01\packets.json' --output 'D:\ppg-ecg-blood-pressure\runs\packet_simulation\missing_replay_01'
& 'D:\ppg-ecg-blood-pressure\.venv\Scripts\python.exe' -B -m pytest -q -p no:cacheprovider 'D:\ppg-ecg-blood-pressure\tests\test_packet_simulation.py'
```

Đổi `--case` để chạy đủ sáu case; `--config` cho config riêng. Không dùng
`--case` cùng `--packets`. Mỗi output là thư mục mới, không ghi đè; lưu
`config.json`, `packets.json`, `replay.json`, `report.json`. Report có seed/hash
config/packets/result/code, commit/dirty, Python, số mẫu/gap/issues và giới hạn.
Hai lần cùng đầu vào/config/code phải cho cùng packets/result hash. Metadata
commit/dirty có thể thay đổi giữa các lần, nên không yêu cầu toàn report cùng hash.
Lỗi ghi có thể để lại thư mục chưa hoàn chỉnh: chỉ bàn giao khi lệnh exit 0,
đủ bốn file và hash khớp. Không đổi tên output giả lập thành dữ liệu đo thật.

## `synthetic-packet-v3`: luồng byte theo layout V0.1 (Tuần 5, Linh)

**Quyết định version (2026-10-21, Linh):** v3 là version mới, có module riêng
`software/data_io/packet_simulation_v3.py` và config riêng
`configs/hardware/packet_simulation_v3.json`. Đầu ra là byte theo mục 6 của
schema, không phải JSON, nên không thay thế v2. Config v2 chỉ nhận case v2;
config v3 không nhận `--packets` (replay v3 là việc của logger). Không đổi tên
version trên artifact cũ.

Mỗi packet có `SYNC` `0xA5 0x5A`, `VERSION` `0x01`, `CHANNEL_ID`, `SESSION_ID`,
`SEQ` uint32, `FIRST_SAMPLE_INDEX` uint32, `T_ANCHOR_US`/`T_FIRST_US` uint64,
`FS_NOMINAL_MHZ` (mHz), `SAMPLE_COUNT` ≤ 32, `STATUS`, `DATA` int32 và CRC16
(CRC-16/CCITT-FALSE trên byte 2 … 39 + 4N). Tất cả là little-endian, mỗi packet
dài 42 + 4N byte.

**Thông số mô phỏng, không phải quyết định phần cứng** (mục 15 của schema còn
mở). Seed `20261021`, 8 packet mỗi kênh dữ liệu.

- ECG `0xE1`: 512 000 mHz, N = 16. PPG `0xF1`/`0xF2`: 100 000 mHz, N = 4, hai khe
  chung một lần đọc FIFO nên chung `FIRST_SAMPLE_INDEX` và `T_ANCHOR_US`.
- Hai sự kiện `0xC1` (mã 1 lúc 1 050 000 µs, mã 2 lúc 1 080 000 µs).
- `STATUS` = 16 (bit 4: `L` chưa đo) trên mọi packet ECG/PPG. Packet sự kiện
  `0xC1` gửi `STATUS` = 0 như firmware (schema mục 10; sửa tại chỗ 2026-10-23, giữ
  tên `synthetic-packet-v3`: trước ngày này packet sự kiện cũng mang 16, nên
  `stream.bin` sinh trước đó khác byte ở các packet sự kiện; số issue và mẫu được
  nhận không đổi vì logger không dựa vào bit 4).

Mô hình thời gian: mẫu k của kênh c ở thời điểm `epoch_us + k·10⁹/FS_mHz`, với
`epoch_us` = 1 000 000 µs. `T_ANCHOR_US` là thời điểm mẫu cuối cộng
`anchor_delay_us` (1 000 µs) và jitter nguyên ngẫu nhiên trong [0, 200] µs, rồi
làm tròn (Python `round`, làm tròn nửa về số chẵn). `T_FIRST_US` =
`T_ANCHOR_US − (N−1)·T`, cũng làm tròn như vậy.

ECG DATA là mẫu 18 bit bù hai căn trái trong word 24 bit, ETAG/PTAG = 0. PPG
DATA là số 18 bit không dấu. Cả hai là số ngẫu nhiên tái lập, không phải hình
thái sinh lý. Packet `0xC1` dùng giá trị tạm: `FIRST_SAMPLE_INDEX` = thứ tự sự
kiện, `FS_NOMINAL_MHZ` = 0, `T_FIRST_US` = `T_ANCHOR_US`. Logger bỏ qua các trường
này (quy tắc R1 trong [logger](packet_logger.md)).

Lỗi chèn vào kênh `0xF1`, packet thứ tự 2 (đếm từ 0), trừ `session_restart` và
`timestamp_first` (packet thứ tự 0). Lỗi chỉ chèn vào **một** kênh để đáp án dễ
đối chiếu; mô phỏng không cố tái hiện tương quan giữa các khe PPG.

| Case | Lỗi chèn | Kết quả mong đợi (`tests/fixtures/packet_v3_expected.json`) |
| --- | --- | --- |
| `valid` | Không | Không issue; 8/8/8 packet dữ liệu, 2 sự kiện |
| `missing` | Bỏ packet | `missing_packets` 1; khoảng trống 4 mẫu |
| `duplicate` | Gửi hai lần cùng byte | `duplicate` 1; mẫu giống `valid` |
| `reordered` | Đổi chỗ packet 2 và 3 | `out_of_order` 1; mẫu giống `valid` |
| `timestamp` | `T_ANCHOR_US` +20 000 µs ở một packet | `timestamp_anomaly` 1; packet bị cách ly |
| `timestamp_first` (thêm 2026-10-22) | `T_ANCHOR_US` +20 000 µs ở packet **đầu** (thứ tự 0) của `0xF1` | `timestamp_anomaly` 1; chỉ packet đầu bị cách ly, 7 packet còn lại được nhận. Không có `gaps`, vì gap chỉ tính giữa hai packet được nhận; `first_sample_index` của kênh là 4. Offset kênh tính từ packet được nhận |
| `offset` | +20 000 µs cho cả kênh `0xF1` | `channel_offset` 1 (khoảng +20 000 µs ± jitter) |
| `crc` | Lật bit 0 của byte DATA đầu, giữ CRC | `crc_mismatch` 1, `skipped_bytes` 1 (58 byte), `missing_packets` 1 |
| `byte_loss` | Mất 5 byte giữa DATA của packet | `crc_mismatch` 1, `skipped_bytes` 1 (53 byte), `missing_packets` 1; packet sau được bắt lại nhờ dò `SYNC` |
| `index_jump` | `FIRST_SAMPLE_INDEX` +5 từ packet 3, bit 0 ở packet 2, `SEQ` liên tục | `sample_gap_status` 1; mất 5 mẫu |
| `reanchor` | `FIRST_SAMPLE_INDEX` +40 từ packet 3, bit 0 và 5 ở packet 3 | `sample_index_reanchored` 1; số mẫu mất `null` |
| `version` | `VERSION` = 3 (CRC tính lại; trước 2026-10-24 là 2, nay 2 là V0.2 hợp lệ) | `unsupported_version` 1, `skipped_bytes` 1, `missing_packets` 1 |
| `session_restart` | Sau packet 2 của mọi kênh: `SESSION_ID` mới, `SEQ`/index/clock bắt đầu lại | `session_change` 1; phiên 1 có 3 packet/kênh và 2 sự kiện, phiên 2 có 5 packet/kênh |

Đáp án được suy ra bằng tay từ định nghĩa case, không sinh bằng code đang
test. Packet ví dụ 50 byte trong fixture được ghép từng trường, CRC tính bằng
`binascii.crc_hqx(body, 0xFFFF)` của thư viện chuẩn. Known-answer:
CRC-16/CCITT-FALSE(`"123456789"`) = `0x29B1`. Test kiểm tra thêm điều kiện tiên
quyết là luồng không có `SYNC` giả, nên số lỗi decode khớp chính xác.

```powershell
.\.venv\Scripts\python.exe scripts/simulate_packets.py --config configs/hardware/packet_simulation_v3.json --case byte_loss --output runs/packet_simulation_v3/byte_loss_01
```

**V0.2 (từ 2026-10-24):** config có `wire_version: 2`
([packet_simulation_v3_v02.json](../../configs/hardware/packet_simulation_v3_v02.json))
sinh luồng [Packet Schema V0.2](../../configs/hardware/Packet_Schema_V0.2.md): mọi
packet mang `VERSION = 2`, thêm sáu trục IMU `0xA1`–`0xA6` (một lần đọc FIFO chung,
chung anchor và jitter, payload int16 có dấu) và packet thông tin thiết bị `0xD1`
theo `device_info.interval_us` (phát lại ở phiên mới sau `session_restart`). Các
case V0.1 chạy được trên config V0.2. Bốn case chỉ có ở V0.2:

| Case | Lỗi cài vào | Đáp án |
| --- | --- | --- |
| `imu_backlog` | Lần đọc IMU 2–5 thành một lần đọc trễ 40 frame: phần 32 frame (bit 7) và phần 8 frame | Không issue; mỗi trục 6 packet, 1 anchor không dùng, không khoảng trống |
| `imu_fifo_full` | Lần đọc 2 gặp FIFO đầy (bit 0, đọc trễ 2 lần), lần 3–4 mất, lần 5 neo lại theo công thức V0.2 mục 5 (bit 5) | `sample_index_reanchored` 6 (mỗi trục 1); 2 chuỗi mỗi trục, số mẫu mất `null` |
| `mixed_version` | Packet PPG khe 1 thứ 3 mang `VERSION = 1` | `version_mixed_in_session` 1, `missing_packets` 1, `channel_missing` 8 (ở phần V0.1) |
| `device_info_changed` | Packet `0xD1` thứ 2 có phiên bản ứng dụng khác | `device_info_changed` 2 (đổi rồi đổi lại) |

Config V0.1 sinh đúng từng byte như code trước khi có V0.2 (đã so SHA-256 của 13
case cùng config ngày 2026-10-24); IMU và `0xD1` được rút số ngẫu nhiên sau các kênh
V0.1. Test: `tests/test_packet_v02.py`.

Output là thư mục mới: `config.json`, `stream.bin`, `session_metadata.json`,
`report.json` (seed, hash config/stream/metadata, commit/dirty, hash code,
Python, số packet theo kênh, vị trí packet lỗi). Hai lần chạy cùng config/case
cho cùng `stream.bin`. Đọc luồng bằng [logger](packet_logger.md).

## Việc còn mở

Công cụ này không giải quyết mâu thuẫn version tài liệu phần cứng và không thay
quyết định giao diện firmware chính thức.

Khi có phần cứng: cần kế hoạch bản ghi **10 phút** trên điều kiện được
phép/an toàn, lưu raw/config/checksum/log, dùng mốc tham chiếu đồng bộ có kiểm
chứng. Báo riêng offset ban đầu, biến thiên timing/jitter, thay đổi offset theo
thời gian/drift và tỷ lệ missing packet/sample từ sequence/log. Không lấy trễ
R-peak→PPG làm clock offset. Mốc tham chiếu, công thức/đơn vị, tiêu chí/tolerance
và clock mapping phải chốt trước; chưa có số đo nào từ công cụ này.