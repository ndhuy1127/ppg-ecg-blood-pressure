# Packet Generator / Replay

## Mục đích

Xây dựng công cụ **generator/replay** có cấu hình (`config`) và `seed` cố định để tạo hoặc phát lại chuỗi packet ECG/PPG phục vụ kiểm thử.

Công cụ phải cho phép cấu hình tối thiểu:

- `session_id`
- `channel` (`ECG` / `PPG`)
- `Fs`
- `sequence`
- `timestamp`
- `sample_count`
- dữ liệu sample
- loại lỗi cần chèn
- vị trí chèn lỗi
- `seed`

Với cùng `config` và `seed`, công cụ phải tạo ra cùng một chuỗi packet và cùng các lỗi được chèn, cho phép tái lập chính xác test case.

## Các kịch bản kiểm thử

| STT | Kịch bản | Cách tạo dữ liệu | Kết quả cần kiểm tra |
|---|---|---|---|
| 1 | **Gói hợp lệ** | Tạo packet đúng schema, `SEQ` liên tục, `timestamp` hợp lệ, `sample_count` và `Fs` đúng | Receiver chấp nhận packet và tái dựng đúng dữ liệu/timeline |
| 2 | **Mất gói** | Chủ động bỏ một hoặc nhiều packet, ví dụ `SEQ: 100, 101, 103` | Receiver phát hiện packet bị mất |
| 3 | **Gói trùng** | Phát lại cùng một packet, ví dụ `SEQ: 100, 101, 101, 102` | Receiver phát hiện packet bị trùng |
| 4 | **Đảo thứ tự** | Hoán đổi thứ tự packet, ví dụ `SEQ: 100, 101, 103, 102, 104` | Receiver phát hiện packet đến sai thứ tự |
| 5 | **Timestamp bất thường** | Tạo timestamp không tăng, nhảy quá lớn/quá nhỏ hoặc không phù hợp với `sample_count/Fs` | Receiver phát hiện timestamp bất thường |
| 6 | **Lệch hai kênh có chủ đích** | Chủ động tạo offset timestamp giữa ECG và PPG với giá trị biết trước | Receiver phát hiện và định lượng được độ lệch giữa hai kênh |

## Test lệch timestamp giữa ECG và PPG

Tạo offset có chủ đích:

\[
t_{PPG}=t_{ECG}+\Delta t
\]

Ví dụ:

\[
\Delta t=20\,ms
\]

Receiver phải xác định được độ lệch gần với giá trị đã tạo ra trong sai số cho phép.

Test này nhằm kiểm tra khả năng **phát hiện và xử lý lệch timestamp giữa ECG và PPG**, không dịch một kênh để ép hai tín hiệu có cùng timestamp.

## Yêu cầu tái lập test

Mỗi lần chạy generator/replay phải lưu lại:

- `seed`
- `config`
- `session_id`
- `channel`
- `Fs`
- số lượng packet
- `sample_count`
- timestamp bắt đầu
- loại lỗi
- vị trí chèn lỗi
- giá trị offset ECG–PPG nếu có

Với cùng `config + seed`, kết quả phải có khả năng tái tạo lại để phục vụ debug và regression test.
