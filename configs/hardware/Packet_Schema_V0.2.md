# Packet Schema V0.2 – thêm IMU và packet thông tin thiết bị

> **Bản nháp chờ duyệt (2026-10-24), chưa triển khai, chưa kiểm chứng trên thiết bị.**
> V0.2 là bản sửa đổi của [V0.1](Packet_Schema_V0.1.md): mọi mục của V0.1 giữ
> nguyên, trừ các thay đổi dưới đây. V0.1 vẫn là bản khóa cho dữ liệu đã ghi và
> cho firmware chưa nâng cấp.
>
> Quyết định của Huy ngày 2026-10-24: `VERSION = 0x02` cho phiên mới; thêm gia tốc
> **và** con quay của BMI270; gửi hết phần FIFO tồn đọng (bit 7); thêm packet thông
> tin thiết bị để buổi đo trên người chỉ cần một cáp USB. Thiết kế chi tiết đã qua
> hai vòng phản biện của Codex (thiết kế IMU, rồi spec đầy đủ).
>
> Datasheet BMI270: BST-BMI270-DS000 (Bosch Sensortec). Các chi tiết thanh ghi và
> thứ tự frame FIFO ghi "theo datasheet §…" phải được đối chiếu lại khi viết
> driver thật; chưa kiểm trên chip.

## 1. Version và tương thích

- Layout byte (V0.1 mục 6) **không đổi**: header 40 byte, `DATA` int32[N],
  CRC-16/CCITT-FALSE, N = 1…32.
- Firmware theo V0.2 gửi `VERSION = 0x02` trên **mọi** packet, kể cả ECG/PPG/sự
  kiện. Firmware V0.1 tiếp tục gửi `0x01`.
- Logger hỗ trợ cả hai (`wire_versions` = `[1, 2]`). Bảng mã kênh và bit `STATUS`
  hợp lệ **theo version của từng packet**:

  | VERSION | Mã kênh hợp lệ | Bit `STATUS` dự trữ (phải là 0) |
  | --- | --- | --- |
  | `0x01` | `0xE1`, `0xF1`–`0xF4`, `0xC1` | 7–15 |
  | `0x02` | như V0.1, thêm `0xA1`–`0xA6` (IMU), `0xD1` (thông tin thiết bị) | 8–15 |

- Bảng mã kênh được kiểm ở **decoder, sau CRC**: mã không có trong bảng của
  version đó thì bỏ cả packet và báo `unknown_channel` (như V0.1).
- Packet V0.1 có bit 7 bật: báo `status_reserved_bits`, giữ packet, **vẫn kiểm
  anchor**; không hiểu là phần tồn đọng.
- Một `SESSION_ID` không được trộn hai version. Nếu có: báo
  `version_mixed_in_session`, giữ mọi packet, và kiểm riêng theo
  (phiên, version, kênh), để cùng `SEQ` ở hai version không bị coi là bản trùng
  xung đột và không nối timing qua hai quy ước.

## 2. Mã kênh IMU

| `CHANNEL_ID` | Kênh | Đơn vị `DATA` |
| --- | --- | --- |
| `0xA1` / `0xA2` / `0xA3` | Gia tốc X / Y / Z | LSB có dấu, ±4 g |
| `0xA4` / `0xA5` / `0xA6` | Con quay X / Y / Z | LSB có dấu, ±500 °/s |

- Trục là **trục cảm biến** BMI270. Raw giữ nguyên trục cảm biến; phân tích dùng
  khung cổ tay qua ma trận cảm biến → cổ tay ghi trong metadata (mục 7), xác nhận
  dấu và trục bằng bench. Không tự suy dấu từ việc module gắn ở mặt dưới bo.
- `DATA[i]` = giá trị int16 của thanh ghi FIFO, mở rộng dấu thành int32. Receiver
  kiểm −32 768 ≤ `DATA[i]` ≤ 32 767 cho `0xA1`–`0xA6` (ECG/PPG giữ dải không dấu
  của V0.1). Không dùng −32 768 làm giá trị đánh dấu thiếu mẫu: đó là mẫu hợp lệ.
- Đổi đơn vị (danh định): gia tốc g = raw × 4 / 32 768; con quay °/s = raw × 500 /
  32 768.

## 3. Cấu hình và cách đọc BMI270

**Cấu hình V1 (chốt 2026-10-24):** gia tốc và con quay cùng ODR **100 Hz**, gia tốc
±4 g, con quay ±500 °/s, lọc chế độ thường (`acc_bwp`/`gyr_bwp` normal, chế độ hiệu
năng), FIFO lấy dữ liệu **đã lọc**, không giảm mẫu, FIFO không header, bật gia
tốc và con quay, `fifo_stop_on_full = 1`, ngưỡng watermark 10 frame. Một frame có
12 byte (con quay rồi gia tốc, theo datasheet §4.7), nên watermark = 120 byte.
Driver phải ánh xạ đúng thứ tự frame sang `0xA1`–`0xA6`. File cấu hình microcode
nạp lúc khởi động và giá trị từng thanh ghi ghi vào metadata (mục 7).

**Mỗi lần đọc** (sau ngắt watermark trên INT1):

1. Đọc `FIFO_LENGTH`, ghi `esp_timer` ngay lúc đó: đây là `T_ANCHOR_US` = A.
2. Tính M = số frame trọn vẹn trong độ dài đã chốt; đọc **đúng 12·M byte**. Frame đến
   sau lúc chốt nằm lại cho lần đọc sau; không đọc tới khi FIFO rỗng.
3. Đọc lỗi hoặc thiếu byte: bỏ lần đọc này, bật bit 3 trên packet kế của mỗi kênh IMU
   và neo lại chỉ số như mục 5.
4. Anchor A chỉ đại diện cho **frame mới nhất** của lần đọc, và chỉ khi FIFO chưa đầy
   (mục 5). Bit 4 bật cho tới khi đo được độ trễ hiệu dụng `L` (riêng gia tốc và con
   quay).

## 4. Phần tồn đọng (M > 32) và bit 7

Một packet chứa tối đa 32 mẫu, còn FIFO BMI270 (2 KB) chứa được khoảng 170 frame.
Khi M > 32, chia lần đọc thành các phần liên tiếp, mỗi phần tối đa 32 frame:

- Mỗi phần cho 6 packet (một packet mỗi trục), tổng 6 × ⌈M/32⌉ packet. Sáu trục dùng
  chung chỉ số mẫu; `SEQ` và bit chuyển tiếp vẫn riêng từng kênh.
- Phần bắt đầu tại frame s (s = 0, 32, 64, …): `FIRST_SAMPLE_INDEX` = chỉ số của frame
  đầu lần đọc + s, nên chỉ số liên tục giữa các phần.
- `T_ANCHOR_US` = A trên **mọi** phần.
- `T_FIRST_US` của phần bắt đầu tại s = A − round_half_up((M − 1 − s) · T), với T =
  10⁹ / `FS_NOMINAL_MHZ` µs.
- **Bit 7 (mới ở V0.2): "phần tồn đọng, anchor thuộc phần mới nhất của cùng lần
  đọc".** Mọi phần trừ phần chứa frame mới nhất bật bit 7. Bit 7 không bao giờ được
  chuyển sang packet khác.

Logger xử lý packet bit 7 như packet bit 0 của V0.1: **giữ mẫu**, kiểm chỉ số như
thường, nhưng anchor không được kiểm và không bao giờ làm mốc. Quy tắc này áp cho
**cả hai chiều** kiểm anchor, cho việc chọn mốc và cho mốc tính offset kênh (chỉ
SYNTHETIC). Bit 7 không tạo khoảng mất và không cắt chuỗi. Nếu phần mới nhất bị
mất, các phần trước **không** được thay nó làm mốc. Chuỗi không còn anchor tin cậy
nào thì ghi timing là chưa xác định.

## 5. FIFO đầy, mất mẫu không biết số lượng, bit 5

**Phát hiện đầy:** FIFO được coi là đầy khi độ dài đã chốt không còn chỗ cho thêm
một frame (độ dài + 12 byte > dung lượng hữu dụng của cấu hình). Không dùng riêng
`FIFO_LENGTH == dung lượng` (chip có thể bỏ frame khi chỗ trống nhỏ hơn một frame),
và không dùng ngắt FIFO-full làm bằng chứng mất mẫu (ngắt này báo sớm).

**Khi đầy:**

- Dữ liệu còn trong FIFO vẫn hợp lệ (`stop_on_full`), khoảng mất nằm **sau** frame
  mới nhất, số mẫu mất không biết. Bật **bit 0** trên mọi packet của lần đọc này
  (cờ bảo thủ: đầy chưa chứng minh chắc chắn đã mất). Anchor của chúng không được
  kiểm (quy tắc bit 0 của V0.1).
- Lần đọc kế tiếp **neo lại chỉ số** và bật **bit 5** trên phần đầu tiên của
  **mỗi** trục:

  ```text
  q          = round_half_up((A_next − A_ref) / T)
  FIRST_next = max(last_prev + 1, I_ref + q − (M_next − 1))
  ```

  (I_ref, A_ref) là chỉ số mẫu cuối và anchor của lần đọc **tin cậy** gần nhất
  (không đầy, không lỗi), **không** phải lần đọc vừa đầy; `last_prev` là chỉ số mẫu
  cuối đã gửi; T là chu kỳ danh định. Tính bằng số nguyên có dấu 64 bit rồi mới lấy
  modulo 2³². Không có mốc tin cậy, A_next − A_ref ≤ 0, hoặc đầy liên tiếp: dùng
  `FIRST_next = last_prev + 1` và vẫn bật bit 5; số mẫu mất là không biết.

**Bit 5 ở V0.2:** chỉ nằm ở packet **đầu tiên sau** khoảng mất (packet đã neo lại),
không bao giờ ở packet trước. Firmware chuyển bit 0, 1 và 5 của packet bị bỏ ở hàng
đợi hoặc gửi thất bại (driver USB không nhận) sang packet gửi được kế tiếp của kênh.
Packet đã vào bộ đệm driver rồi mới mất thì firmware không biết, nên không chuyển.

Receiver với packet V0.2:

- Xử lý bit 5 của **chính packet đó** trước mọi kiểm chồng lấn hay liên tục: packet
  bit 5 luôn bắt đầu chuỗi mới, **kể cả khi chỉ số tình cờ liên tục**; khoảng trống
  ghi `lost_samples = null`.
- Bit 5 của packet trước không giải thích bước nhảy ở packet sau.
- Nhiều lần neo lại bị gộp do mất packet thì chỉ thấy một ranh giới; số lần neo lại
  không đếm được.

Packet V0.1 giữ nguyên quy tắc R2/R6 (bit ở trước hoặc sau chỗ nhảy; chỉ cắt chuỗi
khi chỉ số nhảy).

## 6. Packet thông tin thiết bị `0xD1`

Mục đích: định danh firmware (ELF SHA-256, phiên bản) nằm **trong** luồng raw, nên
khi đo trên người chỉ nối cổng USB native.

| Trường | Giá trị |
| --- | --- |
| `CHANNEL_ID` | `0xD1` |
| `SEQ` | Đếm riêng cho `0xD1`, từ 0 mỗi phiên |
| `FIRST_SAMPLE_INDEX` | Số thứ tự packet thông tin trong phiên (0, 1, …) |
| `T_ANCHOR_US` = `T_FIRST_US` | `esp_timer` lúc task tạo packet (chỉ tham khảo) |
| `FS_NOMINAL_MHZ` | 0 |
| `SAMPLE_COUNT` | 25 (packet 142 byte) |
| `STATUS` | 0; cho phép bit 1 (hàng đợi MCU bỏ một packet thông tin) |

| `DATA` | Nội dung |
| --- | --- |
| `[0]` | Phiên bản layout của payload = 1 |
| `[1]` … `[8]` | ELF SHA-256 (32 byte). Word k = byte 4k … 4k+3 của hash ghép theo thứ tự big-endian, lưu đúng mẫu bit trong int32 (word ≥ 2³¹ thành số âm); receiver lấy `word & 0xFFFFFFFF` |
| `[9]` … `[16]` | Chuỗi phiên bản ứng dụng (`esp_app_desc_t.version`), 32 byte ASCII, kết thúc và đệm bằng NUL, 4 byte mỗi word ghép big-endian |
| `[17]` … `[24]` | Chuỗi phiên bản ESP-IDF (`esp_app_desc_t.idf_ver`), cùng cách đóng gói |

"Big-endian" ở đây chỉ là cách ghép 4 byte thành một word; byte trên dây vẫn
little-endian như V0.1 mục 6. `SESSION_ID` đã có trong header, không lặp trong
payload.

**Nhịp gửi:** một lần ngay sau khi driver USB khởi động, sau đó mỗi 10 s, nên logger
bắt đầu giữa phiên vẫn nhận được trong vòng 10 s.

**Logger:**

- Kiểm `SAMPLE_COUNT = 25`, `DATA[0] = 1`, `FS_NOMINAL_MHZ = 0`,
  `T_FIRST_US = T_ANCHOR_US`, chuỗi đúng ASCII và đúng quy tắc NUL. Sai thì báo
  `device_info_invalid`; packet sai không được tính là "đã có thông tin thiết bị".
- Ghi vào phiên: `device_info` (ELF SHA-256 dạng hex, phiên bản ứng dụng, phiên bản
  ESP-IDF, số packet hợp lệ).
- Báo `device_info_changed` khi nội dung định danh (hash và hai chuỗi) khác nhau
  trong cùng phiên; so nội dung, không so `SEQ`, số thứ tự hay timestamp.
- Báo `device_info_missing` khi một phiên V0.2 có `source_type = DEVICE` mà không
  có packet `0xD1` hợp lệ nào. Kiểm này độc lập với metadata.
- Báo `firmware_metadata_mismatch` khi `firmware_version` trong metadata khác null
  và khác phiên bản ứng dụng. `firmware_version` trong metadata chỉ chứa phiên bản
  ứng dụng, không ghép thêm hash.
- Kiểm số thứ tự so với `SEQ` như packet sự kiện (R1). Không kiểm anchor, không đưa
  vào `samples.csv`, không thuộc kiểm `channel_missing`.

## 7. Metadata phiên và manifest

- Metadata phiên (`packet-session-metadata-v0`) nhận thêm khóa kênh `0xA1`–`0xA6` và
  `0xD1`. Khai báo đủ sáu trục IMU để `channel_missing` có tác dụng.
- Kênh IMU: `sensor` `"BMI270"`, `fs_nominal_mhz` 100 000, `latency_l_us` và
  `latency_source` null kèm lý do, `unit_conversion` theo mục 2. `afe_config` ghi:
  ODR, dải, bộ lọc và chế độ hiệu năng của gia tốc và con quay; nguồn dữ liệu FIFO
  (đã lọc), giảm mẫu, header, `stop_on_full`, watermark; chế độ nguồn; bù offset;
  hash và phiên bản microcode; vị trí lắp và ma trận cảm biến → cổ tay (hoặc null
  kèm lý do).
- Manifest và `decode.json` ghi version schema **theo từng phiên** (`packet-v0.1`
  hoặc `packet-v0.2`), không ghi cứng `packet-v0.1`, và chép `device_info` theo từng
  `SESSION_ID` khi một raw có nhiều lần khởi động lại. Bản sao metadata đầu vào giữ
  nguyên, không ghi đè.
- Logger giữ `packet-logger-v1` (chưa phát hành bản nào khác).

## 8. Kế hoạch triển khai và test

Mỗi bước là một commit riêng, có test, và qua Codex review diff trước khi sang bước
sau.

1. **Codec, receiver, simulator:**
   - bảng mã kênh và bit dự trữ theo version; dữ liệu IMU có dấu;
   - bit 5 và bit 7 của V0.2; thông tin thiết bị; version theo phiên; trộn version.
   - Simulator v3 sinh V0.2 khi config có `wire_version: 2`; config mặc định vẫn là
     V0.1, nên fixture hiện tại không đổi. Trong config V0.1, ca `version` đổi
     `unsupported_version` từ 2 sang 3 (2 giờ hợp lệ).
   - Thêm config và fixture V0.2 với các ca: IMU hợp lệ, tồn đọng 32/33/64/65 frame,
     mất phần cuối, FIFO đầy rồi neo lại, mất packet bit 5, trộn version, thông tin
     thiết bị thiếu, sai hoặc đổi.
2. **Firmware:**
   - `PKT_VERSION = 0x02`; known-answer V0.2 mới cho tự kiểm lúc khởi động (giữ
     known-answer V0.1 trong fixture làm bản cũ);
   - nguồn IMU giả 6 khe có dấu, có chế độ cố ý dừng đọc để tạo tồn đọng và FIFO đầy
     (thuật toán mục 5 chạy thật, số mất thật chỉ dùng làm đáp án);
   - task thông tin thiết bị; chuyển bit 5; chia phần trước khi ghi `p.data[]`
     (không nâng `PKT_MAX_SAMPLES` quá 32).
   - Test C trên máy tính mở rộng cho VERSION 2, cực trị IMU và word hash có bit 31.
3. **Tích hợp record/replay:** manifest theo phiên và `device_info`, nhiều lần khởi
   động lại, hash output xác định.
4. **Sau khi có bo:** driver BMI270 thật (nạp microcode, cấu hình mục 3), đo `L` và
   kiểm dấu trục trên bench.

## 9. Việc còn mở

- `L` của gia tốc và con quay (đo bench); có cần sensortime để ánh xạ clock BMI270
  hay không (chưa bắt buộc ở V1 nếu đo được ngân sách sai số timing).
- Ma trận cảm biến → cổ tay và quy ước khung cổ tay (đề xuất: +X hướng ngón tay, +Z
  ra mặt lưng bàn tay, +Y theo quy tắc tay phải), xác nhận trên bench.
- Kiểm tải: với ECG 512 sps (N = 16), PPG ba khe 100 sps (N = 4, như nguồn giả) và IMU
  sáu trục 100 Hz (N = 10), tổng khoảng 167 packet/s, 12,7 kB/s (ECG 3,4 + PPG 4,35 +
  IMU 4,9 kB/s). Hàng đợi MCU 64 packet chịu khoảng 0,38 s khi USB không nhận. PPG
  thật tới 200 sps sẽ tăng con số này. Cần test burst, host ngừng đọc và timeout
  20 ms.
