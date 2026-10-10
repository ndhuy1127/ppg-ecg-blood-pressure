# Giao diện packet giả lập trên PC — chờ Đức Anh review

## Ranh giới

**SYNTHETIC ONLY.** Đây là đầu ra hỗ trợ phần mềm Tuần 3, không phải schema
phần cứng đã chốt, driver/firmware hoặc kết quả đồng bộ hai cảm biến thật.
Không sửa tài liệu V0.1/V1 của Đức Anh. Không dùng dữ liệu này để đánh giá
waveform, PAT, BP, độ trễ sinh lý, năng lượng hoặc hiệu năng thiết bị.

Tham khảo yêu cầu generator/replay và packet ở `origin/dev/ducanh@40ede49`.
Version riêng `synthetic-packet-v2`; JSON, không phải binary wire format.
Code: `software/data_io/packet_simulation.py`; runner: `scripts/simulate_packets.py`.

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
Schema phần cứng của Đức Anh không thay đổi. Issue counts/giá trị mẫu giữ nguyên
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

## Review và việc thực tế còn chờ

Đức Anh review field/version, sequence/reset/wrap, ý nghĩa timestamp lấy mẫu và
FIFO, mốc clock, fs từng kênh; Linh review decoder/schema/gap; Huy review ý nghĩa
thời gian và giới hạn offset. Đây không giải quyết mâu thuẫn version tài liệu
phần cứng, không thay quyết định giao diện firmware chính thức.

Khi có phần cứng: Đức Anh cần kế hoạch bản ghi **10 phút** trên điều kiện được
phép/an toàn, lưu raw/config/checksum/log, dùng mốc tham chiếu đồng bộ có kiểm
chứng. Báo riêng offset ban đầu, biến thiên timing/jitter, thay đổi offset theo
thời gian/drift và tỷ lệ missing packet/sample từ sequence/log. Không lấy trễ
R-peak→PPG làm clock offset. Mốc tham chiếu, công thức/đơn vị, tiêu chí/tolerance
và clock mapping phải được nhóm review; chưa có số đo nào từ công cụ này.