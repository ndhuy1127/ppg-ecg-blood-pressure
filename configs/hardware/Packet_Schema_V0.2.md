# Packet Schema V0.2 – thêm IMU và packet thông tin thiết bị

> **Duyệt 2026-10-24. Đã triển khai bước 1 (codec, receiver, logger, simulator; mục 9),
> kể cả sửa đổi cùng ngày về mốc `SAMP` cho ECG và bit 8 (mục 7). Firmware: xong bước
> 2a (encoder V0.2, `0xD1`, chuyển bit 5), 2b (IMU giả, chia phần, neo lại) và 2c
> (ánh xạ `SAMP`, bit 8, với xung từ nguồn ECG giả; MCPWM capture thật chỉ mới build);
> cách đọc PPG mới chưa làm. Chưa kiểm chứng trên thiết bị.**
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
  | `0x02` | như V0.1, thêm `0xA1`–`0xA6` (IMU), `0xD1` (thông tin thiết bị) | 9–15 (bit 8: mốc `SAMP` của ECG, mục 7) |

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
  khung cổ tay qua ma trận cảm biến → cổ tay ghi trong metadata (mục 8), xác nhận
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
nạp lúc khởi động và giá trị từng thanh ghi ghi vào metadata (mục 8).

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

## 7. Mốc xung `SAMP` cho ECG, bit 8 (sửa đổi 2026-10-24)

Quyết định của Huy ngày 2026-10-24: bật xung `SAMP` của MAX30001 **luôn** và dùng làm
mốc thời gian ECG; chốt thời điểm cạnh bằng MCPWM capture của ESP32-S3; sửa V0.2 (chưa
có firmware V0.2 chạy, chưa có dữ liệu V0.2) thay vì nâng version; không thêm kênh
ghi mọi cạnh xung. PPG đọc theo mục 7.6. Thiết kế đã qua một vòng phản biện của Codex;
mọi chi tiết thanh ghi phải đối chiếu lại datasheet MAX30001 khi viết driver và kiểm
trên chip thật ở bring-up.

### 7.1. Cấu hình MAX30001 và chốt cạnh

- `EN_INT2` chỉ đưa `SAMP` ra INT2B; `SAMP_IT = 00` (một xung mỗi mẫu, 512 Hz);
  `CLR_SAMP = 1` (xung tự xóa sau khoảng 1/4 chu kỳ mẫu, cỡ 488 µs ở 512 sps).
  INT2B ra CMOS (`INTB_TYPE = 01` ở `EN_INT2`), qua TXB0108 tới GPIO47; tắt điện trở
  kéo của MCU trên GPIO47. Cực tính, độ rộng và rung của xung đo trước và sau
  TXB0108 ở bring-up.
- ESP32-S3 dùng **MCPWM capture**: cạnh của GPIO47 (cực tính theo số đo) chốt giá trị
  bộ đếm capture **riêng** của MCPWM bằng phần cứng (không phải `esp_timer`), không
  phụ thuộc độ trễ ngắt. Bật `CONFIG_MCPWM_ISR_CACHE_SAFE`; hàm callback cùng mọi mã
  và dữ liệu nó dùng nằm ở bộ nhớ trong (IRAM/DRAM), không chỉ riêng hàm callback.
  Callback chỉ đọc giá trị đã chốt, gán số thứ tự xung `e` và ghi vào bộ đệm vòng, mỗi
  mục có đánh dấu thế hệ để đọc nhất quán.
- Quy đổi bộ đếm capture sang `esp_timer` (µs): định kỳ đọc cặp hai đồng hồ theo kiểu
  kẹp (đọc `esp_timer`, chốt bộ đếm capture, đọc lại `esp_timer`; chỉ nhận cặp có hai
  lần đọc `esp_timer` cách nhau dưới 2 µs), xử lý tràn bộ đếm. Sai số quy đổi phải
  nằm trong ngân sách (mục tiêu dưới 5 µs) và ghi vào metadata; không đổi clock (tiết
  kiệm năng lượng) trong phiên.
  **Mô hình quy đổi (sửa 2026-10-24 khi viết `firmware/drivers/samp_capture.c`,
  chưa chạy trên chip; trước đó ghi "nội suy tuyến tính giữa các cặp"):** bộ đếm
  capture (APB 80 MHz) và `esp_timer` cùng lấy từ một thạch anh, nên tỉ lệ giữa hai
  đồng hồ là danh định và cố định. Giá trị capture được quy đổi theo tỉ lệ đó từ cặp
  kẹp gần nhất; cặp chỉ dùng để neo độ lệch. Không ước lượng độ dốc từ hai cặp: mốc
  cần ngay lúc gửi packet nên luôn là ngoại suy, và độ dốc ước lượng từ hai cặp cách
  100 ms với sai số đọc cỡ 1 µs chỉ thêm sai số. Cặp đọc kẹp bằng kênh capture thứ
  hai không nối GPIO, chốt bằng phần mềm, mỗi 100 ms; cặp cũ hơn 1 s thì không quy
  đổi (cạnh coi như thiếu, ánh xạ sang `LỖI`), xa trong giới hạn ±26,8 s của hiệu tick
  có dấu. Độ lệch giữa dự đoán theo cặp cũ và cặp mới được in ra UART0 làm sai số quy
  đổi; nếu ở bring-up sai số này vượt ngân sách (hai đồng hồ không cùng tỉ lệ như giả
  định) thì phải đổi sang mô hình có độ dốc.
- Giá trị chốt vẫn có thể bị ghi đè nếu hàm ngắt trễ hơn một chu kỳ xung (1,953 ms):
  phát hiện qua khoảng cách giữa hai giá trị chốt liên tiếp (gần 1 chu kỳ hay gần
  bội số).
- Bộ đệm vòng 64 mục (125 ms), dài hơn khoảng trống còn lại của FIFO ECG sau ngưỡng
  `EFIT` (16 mẫu, khoảng 31 ms).

### 7.2. Ánh xạ xung ↔ mẫu

- Mẫu ECG có chỉ số `k` (cùng gốc với `FIRST_SAMPLE_INDEX`, tính từ mỗi lần khởi động
  thu); xung có số `e`. Ánh xạ là `e = k + c`, hằng `c` xác định lúc khởi động thu.
- Trạng thái: `CHƯA_KHỚP` → `ĐÃ_KHỚP` → `LỖI` → khởi động lại ánh xạ. Khởi động
  ánh xạ: dừng thu, xóa ngắt đang chờ, bật capture, rồi khởi động chuyển đổi bằng
  lệnh `SYNCH` (`FIFO_RST` không thay được, vì nó không khởi động lại mạch chuyển
  đổi). Xung đầu tiên sau đó ứng với mẫu đầu tiên của FIFO; quan hệ này **phải được
  kiểm trên MAX30001 thật** ở bring-up trước khi tin bit 8: lệch cố định một mẫu
  (1,953 ms) không phép kiểm số lượng nào phát hiện được.
- Đếm mẫu theo word FIFO: ETAG `000` (hợp lệ), `010` (hợp lệ, EOF), `001` và `011`
  (fast recovery; `011` là EOF) đều là một bước thời gian; điện áp của `001`/`011`
  không dùng cho phát hiện mốc. Dừng đọc sau word `010` hoặc `011`. `110` (rỗng) và
  `111` (tràn) không phải mẫu.
- FIFO tràn (`111`), ECG khởi động lại, phát hiện xung mất, thừa hoặc giá trị chốt
  bị ghi đè: chuyển `LỖI`. Từ đó mọi packet dùng mốc đọc FIFO cho tới khi khởi động
  lại ánh xạ; packet sạch đầu tiên sau khi neo lại mang bit 5 như quy tắc hiện hành.
- **Khi nào khởi động lại ánh xạ (chốt 2026-10-24):** sau 1 s ở `LỖI` (khoảng 32
  packet dùng mốc đọc FIFO), và tối đa một lần mỗi 10 s (lần khởi động lúc bật máy
  không tính), để đường xung lỗi liên tục không gây khởi động lại liên tục. Mỗi lần
  khởi động lại mất một đoạn ECG (thời gian dừng, `SYNCH` và độ trễ bộ lọc số của
  MAX30001, đo ở bring-up) và chỉ số mẫu bắt đầu lại từ 0 (bit 5, chuỗi mới).

### 7.3. Gán mốc cho từng packet ECG

1. Khi `EINT` báo, đọc burst tới word EOF và **ghi ngay** thời điểm nhận xong EOF
   (mốc đọc FIFO, V0.1 mục 5.2). Giới hạn sai số của mốc này chỉ đúng khi đọc thật
   tới EOF, không đúng với burst cố định 16 word khi FIFO còn tồn.
2. Ở `ĐÃ_KHỚP`: mẫu cuối của packet là `k_last = FIRST_SAMPLE_INDEX + N − 1`. Chờ có
   giới hạn (tối đa 2 chu kỳ mẫu) đúng xung `e = k_last + c`, vì dữ liệu FIFO có thể
   đọc được trước khi xung của chính mẫu đó tới; **không** thay bằng xung mới nhất.
3. Có đúng xung đó, thế hệ hợp lệ, và kiểm danh tính đạt: `T_ANCHOR_US` = thời điểm
   xung, bật bit 8. Ngược lại: `T_ANCHOR_US` = mốc đọc FIFO, không bật bit 8, chuyển
   `LỖI`.
4. Kiểm danh tính, làm **trước** khi bật bit 8:
   - Khởi động ánh xạ (mỗi lần `SYNCH`): mở một kỷ nguyên ánh xạ mới, xóa bộ đệm vòng,
     đặt `e = 0` cho xung đầu tiên sau `SYNCH` và `c = 0`, tức xung `e` ứng với mẫu
     `k = e` của lần thu này (chỉ số bắt đầu từ 0).
   - Mọi khoảng cách giữa hai cạnh liên tiếp đã chốt, từ xung của mẫu cuối packet
     trước (hoặc từ xung 0 với packet đầu tiên của kỷ nguyên) tới xung `e = k_last`,
     phải nằm trong `1 953,125 µs` cộng trừ dung sai (tạm ±20 µs cộng sai số tốc độ
     ECG). Khoảng quá ngắn (xung giả) hoặc gần bội số (xung mất, giá trị bị ghi đè)
     đều chuyển `LỖI`.
   - Số cạnh trong đoạn đó phải đúng bằng `N`. Một xung mất cộng một xung thừa vẫn giữ
     đúng số lượng nhưng tạo hai khoảng bất thường, nên bị bắt ở bước trên.
   - Packet đầu tiên của kỷ nguyên chỉ được bật bit 8 khi các xung `0 … N − 1` đều có
     và qua kiểm khoảng cách.
5. `T_FIRST_US` giữ định nghĩa V0.1 (`T_ANCHOR_US − (N − 1) · 10⁶ / fs`).

### 7.4. Bit 8 của `STATUS`

- Bit 8 = 1: `T_ANCHOR_US` là thời điểm cạnh `SAMP` của **mẫu cuối của chính packet
  này**, chốt bằng MCPWM capture. Bit 8 = 0: mốc đọc FIFO như V0.1.
- Chỉ dùng cho kênh ECG `0xE1` của `VERSION = 0x02`; bit 8 trên kênh khác báo
  `status_reserved_bits`.
- Không chuyển tiếp bit 8 từ packet bị mất (khác bit 0/1). Đổi nguồn mốc giữa hai
  packet không phải neo lại và **không** bật bit 5.
- Bit dự trữ của `VERSION = 0x02`: 9–15 (mask `0xFE00`).
- Codec, logger, firmware, simulator và fixture V0.2 phải cập nhật cùng một đợt;
  logger cũ chỉ báo `status_reserved_bits` cho bit 8 và vẫn giữ packet, nên sẽ hiểu
  sai mốc nếu dùng với dữ liệu mới.

### 7.5. Logger và phân tích

- Kiểm anchor ECG **theo nguồn mốc**: packet bit 8 dùng dung sai riêng, nhỏ hơn hẳn
  một chu kỳ ECG (tạm 200 µs; chỉnh sau bring-up), để lệch một mẫu (1,953 ms) bị bắt.
  Dung sai tốc độ của ECG đặt riêng (dao động 32,768 kHz; tạm ±1 000 ppm), không dùng
  chung ±3 % tạm của PPG. Hai giá trị tạm ghi `NOT_HARDWARE_VALIDATED` trong config.
- Mọi kiểm tra và hồi quy ECG chia theo phiên, chuỗi liên tục (ranh giới bit 5) **và**
  nguồn mốc; loại anchor của packet bit 0/bit 7 như cũ. Không so trực tiếp mốc
  `SAMP` với mốc đọc FIFO qua chỗ đổi nguồn: hai nguồn lệch nhau một khoảng (thời
  gian mẫu nằm trong FIFO cộng độ trễ đọc) phải ước lượng riêng trước khi so.
- Dung sai tốc độ nhân theo độ dài khoảng trống giữa hai packet: với ±1 000 ppm và
  200 µs, tính cả sai số anchor tới 200 µs, phép kiểm qua từ 398 mẫu trở lên (khoảng
  0,78 s) không còn phân biệt được lệch một mẫu ECG; logger báo riêng các phép kiểm
  như vậy (`anchor_check_weak`) thay vì coi là đã kiểm.
- Báo số packet bit 8, số packet dùng mốc đọc FIFO và vị trí đổi nguồn.
- Quy ước: `t′` là thời điểm mẫu **chưa trừ độ trễ** (V0.1 mục 5.3 với `δ = d_pipe = 0`);
  chỉ trừ độ trễ đúng một lần, theo nguồn mốc của packet chứa mẫu đó. Nếu thời điểm
  đã được trừ độ trễ ở bước trước thì tính PAT trực tiếp, không trừ lần nữa.
- Với packet bit 8: `t_last = T_ANCHOR_US − L_ECG,SAMP`. `L_ECG,SAMP` là độ trễ từ lúc
  lấy mẫu analog tới cạnh đã chốt (bộ lọc số và ADC, TXB0108, độ lệch chốt); **không**
  gồm thời gian mẫu nằm trong FIFO. Không trừ đồng thời `L` của mốc đọc FIFO. Giá trị
  ADI đo trên MAX30003 (512 sps: 20,839 / 32,558 ms) chỉ để đối chiếu.
- Đo `L_ECG,SAMP` bằng kích thích chung trong phép đo đồng bộ 10 phút, quét pha kích
  thích qua một chu kỳ mẫu. Phép đo này cũng là kiểm tra độc lập cho lệch pha cố
  định của ánh xạ (mục 7.2).
- `PAT = (t′_foot − L_PPG) − (t′_R − L_ECG,nguồn)`. PPG vẫn dùng mốc đọc FIFO (mục 7.6)
  và lấy mẫu 200 sps (5 ms), nên sai số phía PPG vẫn là phần đóng góp chính.

### 7.6. Đọc FIFO PPG (sửa cách làm của quyết định 2026-10-24)

- `PPG_RDY` giữ chân INT ở mức thấp tới khi đọc `Interrupt Status 1` (0x00) hoặc
  `FIFO_DATA`; mẫu mới đến khi cờ chưa xóa thì không tạo cạnh mới. Firmware đọc 0x00
  sau **mỗi** ngắt để xóa và đếm; tới mẫu thứ 8 thì chốt con trỏ FIFO và đọc **hết**
  số mẫu có trong FIFO lúc chốt (thường 8; nhiều hơn nếu xử lý trễ), không cố định 8:
  đọc 8 khi FIFO có 9 làm mốc lệch khoảng 5 ms. `N` của packet PPG là số mẫu đọc
  được (tối đa 32).
- Datasheet chỉ mô tả `PPG_RDY` cho chế độ SpO2 và HR. Ở chế độ ba khe phải kiểm khi
  bring-up; không chạy thì đọc theo timer định kỳ (ví dụ 40 ms), vẫn đọc hết FIFO, và
  mốc có thể lệch tới một chu kỳ PPG (5 ms), dựa vào hồi quy offline.

### 7.7. Theo dõi và thử

- Firmware in ra UART0 (log chữ, không vào packet) các bộ đếm: xung mất, xung thừa,
  giá trị chốt bị ghi đè, số lần chuyển `LỖI`, số packet có và không có bit 8. Không
  thêm kênh ghi mọi cạnh xung (quyết định 2026-10-24); chỉ thêm nếu khi thử PCB các
  bộ đếm hoặc logger báo bất thường.
- Simulator và test: SAMP hợp lệ, mất xung, thừa xung, ghi đè, chuyển về mốc đọc FIFO,
  khởi động lại ánh xạ, và lệch một mẫu phát sinh giữa phiên (logger phải bắt bằng
  dung sai mới). Lệch cố định một mẫu ngay từ đầu phiên thì logger không thể bắt
  (mục 7.2); chỉ phép đo kích thích (mục 7.5) bắt được.

## 8. Metadata phiên và manifest

- Metadata phiên (`packet-session-metadata-v0`) nhận thêm khóa kênh `0xA1`–`0xA6` và
  `0xD1`. Khai báo đủ sáu trục IMU để `channel_missing` có tác dụng.
- Kênh IMU: `sensor` `"BMI270"`, `fs_nominal_mhz` 100 000, `latency_l_us` và
  `latency_source` null kèm lý do, `unit_conversion` theo mục 2. `afe_config` ghi:
  ODR, dải, bộ lọc và chế độ hiệu năng của gia tốc và con quay; nguồn dữ liệu FIFO
  (đã lọc), giảm mẫu, header, `stop_on_full`, watermark; chế độ nguồn; bù offset;
  hash và phiên bản microcode; vị trí lắp và ma trận cảm biến → cổ tay (hoặc null
  kèm lý do).
- Kênh ECG `0xE1` (mục 7): `afe_config` ghi thêm `EN_INT2`, `SAMP_IT`, `CLR_SAMP`,
  cách chốt cạnh (MCPWM capture) và chân; độ trễ hiệu dụng ghi **theo nguồn mốc**:
  `latency_l_us` cho mốc đọc FIFO và một khóa mới cho mốc `SAMP` (ví dụ
  `latency_samp_l_us`, kèm nguồn), nên validator metadata phải cập nhật cùng đợt.
- Manifest và `decode.json` ghi version schema **theo từng phiên** (`packet-v0.1`
  hoặc `packet-v0.2`), không ghi cứng `packet-v0.1`, và chép `device_info` theo từng
  `SESSION_ID` khi một raw có nhiều lần khởi động lại. Bản sao metadata đầu vào giữ
  nguyên, không ghi đè.
- Logger giữ `packet-logger-v1` (chưa phát hành bản nào khác).

## 9. Kế hoạch triển khai và test

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
   - **Sửa đổi mục 7 (làm 2026-10-24):** mask dự trữ V0.2 `0xFE00` và tên bit 8
     (`anchor_samp`); bit 8 chỉ hợp lệ trên `0xE1`; kiểm anchor ECG riêng theo nguồn
     mốc trong mỗi chuỗi (`samp_anchor_tolerance_us` 200, tốc độ ECG
     `ecg_anchor_rate_tolerance_ppm` 1 000), báo `anchor_check_weak`, đếm packet và
     chỗ đổi nguồn (`anchor_sources`), báo `samp_resumed_without_reanchor` khi mốc
     `SAMP` trở lại mà không neo lại; metadata `latency_samp_l_us` và
     `latency_samp_source` cho `0xE1` (thiếu khi luồng có bit 8:
     `samp_latency_metadata_missing`). Simulator: ECG V0.2 mặc định mang bit 8 (config
     `samp`), ca `samp_remap` (mất ánh xạ rồi khởi động lại) và `samp_shift` (lệch
     một mẫu giữa phiên). Mất xung, thừa xung, ghi đè được firmware phát hiện nên
     với logger giống `samp_remap`; phần phát hiện trong firmware thử ở bước 2.
     Logger không hồi quy tốc độ; hồi quy offline tách theo nguồn theo mục 7.5.
2. **Firmware** (chia thành 2a–2d, mỗi phần một commit):
   - **2a (làm 2026-10-24):** `PKT_VERSION = 0x02` (encoder đổi tên thành
     `packet_wire.c`); known-answer V0.2 mới cho tự kiểm lúc khởi động (packet ECG có
     bit 8 và packet `0xD1`; known-answer V0.1 giữ trong fixture làm bản cũ); task
     thông tin thiết bị; chuyển bit 5; test C trên máy tính cho VERSION 2, cực trị
     IMU và word hash có bit 31.
   - **2b (làm 2026-10-24):** nguồn IMU giả 6 khe có dấu, có chế độ cố ý dừng đọc để
     tạo tồn đọng và FIFO đầy (env `esp32s3_devkitc_imu_stall`; thuật toán mục 5 chạy
     thật trong `imu_plan.c`, số mất thật chỉ in UART0 làm đáp án); chia phần trước
     khi ghi `p.data[]` (không nâng `PKT_MAX_SAMPLES` quá 32).
   - **2c (làm 2026-10-24, mục 7):** trạng thái ánh xạ và kiểm danh tính trong
     `samp_map.c` (C thuần, test trên máy tính), bộ đệm vòng 64 cạnh có đánh dấu số
     cạnh, chờ đúng xung của mẫu cuối, bit 8, khởi động lại theo chính sách mục 7.2,
     bộ đếm in UART0; nguồn ECG giả phát xung (env `esp32s3_devkitc_samp_faults` cố ý
     bỏ và thêm xung). MCPWM capture thật và cặp đọc kẹp viết sẵn trong
     `samp_capture.c` (bật bằng `BOARD_SAMP_CAPTURE=1`), mới build, chưa chạy.
   - **2d (mục 7.6):** PPG xóa ngắt mỗi mẫu và đọc hết FIFO (nguồn giả có chế độ trễ
     để `N` lớn hơn 8).
3. **Tích hợp record/replay:** manifest theo phiên và `device_info`, nhiều lần khởi
   động lại, hash output xác định.
4. **Sau khi có bo:** driver BMI270 thật (nạp microcode, cấu hình mục 3), đo `L` và
   kiểm dấu trục trên bench. Driver MAX30001/MAX30101 thật: kiểm xung `SAMP` đầu
   tiên ứng với mẫu đầu tiên của FIFO, cực tính và độ rộng xung, `PPG_RDY` ở chế độ
   ba khe; đo `L_ECG,SAMP` với kích thích quét pha (mục 7.5).

## 10. Việc còn mở

- `L` của gia tốc và con quay (đo bench); có cần sensortime để ánh xạ clock BMI270
  hay không (chưa bắt buộc ở V1 nếu đo được ngân sách sai số timing).
- Ma trận cảm biến → cổ tay và quy ước khung cổ tay (đề xuất: +X hướng ngón tay, +Z
  ra mặt lưng bàn tay, +Y theo quy tắc tay phải), xác nhận trên bench.
- Mục 7: dung sai anchor `SAMP` (tạm 200 µs) và dung sai tốc độ ECG (tạm ±1 000 ppm)
  chỉnh theo số đo; chi tiết thanh ghi `EN_INT2`/`CLR_SAMP` đối chiếu datasheet
  MAX30001; nếu `PPG_RDY` không chạy ở chế độ ba khe thì chuyển sang đọc theo timer.
  Phía firmware: dung sai một khoảng cạnh tạm 22 µs (20 µs cộng 1 000 ppm của một chu
  kỳ); MCPWM capture thật (`samp_capture.c`) chưa chạy trên chip: kiểm cực tính,
  độ rộng xung, thử nối vòng GPIO trên DevKitC trần, đo sai số quy đổi và tỉ lệ cặp
  kẹp bị loại (đọc `esp_timer` hai lần cách nhau 2 µs trở lên).
- Kiểm tải: với ECG 512 sps (N = 16), PPG ba khe 200 sps (chốt 2026-10-24) và IMU
  sáu trục 100 Hz (N = 10): PPG N = 4 cho khoảng 242 packet/s, 17,0 kB/s (ECG 3,4 +
  PPG 8,7 + IMU 4,9 kB/s), hàng đợi MCU 64 packet chịu khoảng 0,26 s khi USB không
  nhận; PPG N = 8 cho 167 packet/s, 13,9 kB/s, hàng đợi chịu khoảng 0,38 s. Nguồn
  giả của firmware chạy PPG 200 sps, N = 8. Cần test burst, host ngừng đọc và
  timeout 20 ms.
