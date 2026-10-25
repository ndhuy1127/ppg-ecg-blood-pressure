# Logger packet phía máy tính (Packet Schema V0.1)

## Phạm vi và ranh giới

Logger đọc luồng byte theo [Packet Schema V0.1](../../configs/hardware/Packet_Schema_V0.1.md)
(mục 6), làm các kiểm tra ở mục 12 theo **từng phiên và từng kênh**, ghi raw bất
biến, rồi ghi session manifest có hash. Phiên bản logger: `packet-logger-v1`
(config `configs/hardware/packet_logger.json` cùng version).

- **Đã có (2026-10-21):** decoder, kiểm tra, runner `record`/`replay`, test với
  luồng SYNTHETIC `synthetic-packet-v3` ([mô phỏng](packet_simulation.md)).
- **Sửa theo review độc lập Tuần 5 (2026-10-22):** kiểm
  `T_ANCHOR_US` hai chiều, thêm dung sai tốc độ, thêm cột `chain_id`, cách ly
  packet `FS_NOMINAL_MHZ = 0`, thêm cận trên số mẫu mất, đổi cách đếm lỗi decode.
  Chi tiết ở các mục dưới và trong `reports/weekly/week_05/README.md`. Vẫn là
  `packet-logger-v0`, vì trước lần sửa này code chưa từng được commit; v0 được
  commit ở `250139d`.
- **`packet-logger-v1` (2026-10-23):** cùng một luồng byte có thể cho output khác
  v0, nên nâng version (config và manifest cùng ghi `packet-logger-v1`):
  - thêm `channel_missing` và `channels_missing` của phiên;
  - kiểm số thứ tự sự kiện so với `SEQ` (`events_lost_before_send`,
    `event_ordinal_inconsistent`), thêm `event_ordinal` vào sự kiện (R1);
  - packet `FS_NOMINAL_MHZ = 0` không còn làm mốc index;
  - dung sai ±3 % áp lên tốc độ mẫu, không phải lên chu kỳ (dung sai mặc định);
  - packet có bit 0 giữ mẫu nhưng anchor không được kiểm, không làm mốc
    (`accepted_anchor_unreliable`, bước 6);
  - `record` ghi bản sao config/metadata trước byte đầu tiên;
  - đọc thêm Packet Schema V0.2 (2026-10-24, mục "Packet Schema V0.2" dưới).

  Metadata phiên (`packet-session-metadata-v0`) không đổi tên version; nhận thêm khóa
  kênh của V0.2. Config đổi trường `packet_schema` thành `packet_schemas`. Phiên ghi bằng v0 vẫn đọc được manifest; replay bằng v1 so với
  manifest v0 có thể lệch hash và manifest ghi rõ `logger_version` của mỗi bên.
- **Đọc cổng serial trực tiếp** (2026-10-24, `pyserial==3.5` được duyệt):
  `record --port ... --duration-s ...` (mục Nguồn byte). **Chờ:** chạy 10 phút với
  firmware khung trên bo thật.
- Không phải phép đo đồng bộ phần cứng, không ước lượng fs thật/drift/jitter
  (việc đó thuộc [kế hoạch đo 10 phút](../../hardware/test_reports/sync_10min_test_plan.md)),
  không tính PAT. Kết quả SYNTHETIC chỉ kiểm chứng code.

| Thành phần | Vai trò |
| --- | --- |
| `software/data_io/packet_wire.py` | Layout byte, CRC-16/CCITT-FALSE, `encode_packet`, `StreamDecoder` (thuần, không I/O) |
| `software/data_io/packet_receiver.py` | Kiểm tra mục 12, metadata phiên, xuất JSON/CSV dạng byte (thuần) |
| `scripts/packet_logger.py` | I/O: `record` từ nguồn byte, `replay` từ raw, provenance, manifest |
| `configs/hardware/packet_logger.json` | Dung sai và kích thước đọc; `status: NOT_HARDWARE_VALIDATED` |
| `tests/test_packet_logger.py`, `tests/fixtures/packet_v3_expected.json` | Test với đáp án độc lập |

## Nguồn byte

`record(source, ...)` nhận bất kỳ object nào có `read(n) -> bytes`; `b""` nghĩa
là hết phiên. CLI có hai nguồn:

- `--source-file`: mở file (chế độ `rb`), coi như luồng đến từ thiết bị.
- `--port COM5 --duration-s 600 [--baud 115200]`: đọc cổng serial bằng `pyserial`
  qua `SerialSource`. `read` của serial trả `b""` khi hết timeout (0,1 s); ở đây đó
  chỉ là chưa có byte, nên logger đọc tiếp tới khi hết `--duration-s`. Ctrl+C trong
  lúc đọc kết thúc phiên bình thường: raw, decode và manifest vẫn được ghi. Manifest
  ghi `source = {kind: "serial", name, baudrate, duration_s, stopped_by, pyserial}`.
  Cổng được mở với DTR và RTS ở mức không kích hoạt, vì USB Serial/JTAG của
  ESP32-S3 khởi động lại chip với một số chuyển trạng thái DTR/RTS (như esptool
  dùng); chưa kiểm trên bo thật. Cổng USB gốc bỏ qua baud. Ghi xuống cổng có
  timeout 0,5 s (`record --commands`, mục "Lệnh xuống thiết bị"). Decoder nhận byte
theo từng đoạn bất kỳ: test xác nhận kết quả giống hệt nhau với đoạn 1, 2, 41,
4096 byte hoặc cả luồng.

## Decoder (mục 6; mục 12 bước 1, 2, 5)

1. Dò `SYNC` `0xA5 0x5A`. Byte không thuộc packet hợp lệ nào được gom thành từng
   đoạn liền nhau, mỗi đoạn một issue `skipped_bytes`.
2. Kiểm theo thứ tự: `VERSION` = `0x01`, rồi `1 ≤ SAMPLE_COUNT ≤ 32`, rồi đủ
   `42 + 4N` byte, rồi CRC16 trên byte 2 … 39 + 4N, rồi `CHANNEL_ID` ∈ {`0xE1`,
   `0xF1`–`0xF4`, `0xC1`}.
3. Lỗi (`unsupported_version`, `bad_sample_count`, `crc_mismatch`) thì bỏ **một**
   byte và dò `SYNC` tiếp, **không** nhảy theo độ dài khai báo. Riêng
   `unknown_channel` đã qua CRC nên độ dài đáng tin, và cả packet được bỏ.
4. Cuối luồng thiếu byte thì báo `truncated_packet`, không đệm. Một byte `0xA5`
   lẻ ở cuối luồng (nửa đầu của `SYNC`) cũng là `truncated_packet`.

**Cách đếm lỗi decode: mỗi packet hỏng là một lỗi** (mục 12 bước 1). Sau một
`crc_mismatch`, các ứng viên `SYNC` bắt đầu bên trong độ dài khai báo của packet
đó, nếu bị từ chối, không cộng vào `errors`, mà được đếm riêng trong
`decode.sync_candidates_rejected`. Tương tự, `truncated_packet` đầu tiên phủ hết
phần còn lại của luồng. Ứng viên nào qua CRC bên trong vùng đó vẫn được nhận
(hoặc báo `unknown_channel`), và sau nó thì đếm lại bình thường. Byte của mọi ứng
viên bị từ chối vẫn nằm trong `skipped_bytes`.

**Khác với thứ tự liệt kê ở mục 12:** `VERSION` được kiểm trước CRC, vì gặp
version lạ thì không biết layout nên không tính được CRC. CRC16 được đọc
little-endian theo ghi chú "little-endian" của mục 6 (câu hỏi D1).
`SAMPLE_COUNT = 0` bị coi là header vô lý (D7). Không loại trừ được trường hợp
gặp `SYNC` giả mà CRC vẫn trùng (khoảng 1/65 536 mỗi ứng viên).

## Kiểm tra theo phiên và kênh (mục 12)

Đổi `SESSION_ID` thì ghi `session_change`. Mỗi phiên được kiểm riêng, không bao
giờ nối sang phiên khác.

| Bước mục 12 | Cách làm | Issue |
| --- | --- | --- |
| 3. `SEQ` | Mở rộng uint32 qua mốc 2³² (giá trị gần nhất với `SEQ` lớn nhất đã nhận). Thiếu = mất. Lặp cùng nội dung = trùng (giữ bản đầu). Lặp khác nội dung = xung đột (cách ly **cả hai** bản). Nhỏ hơn giá trị lớn nhất đã nhận = đảo thứ tự (vẫn nhận, sắp lại offline) | `missing_packets` (một issue mỗi đoạn, kèm `count`), `duplicate`, `conflicting_duplicate`, `out_of_order` |
| 4. `FIRST_SAMPLE_INDEX` | Mở rộng uint32 rồi so với `index + N` của packet trước. Packet `FS_NOMINAL_MHZ = 0` có header không tin được: có `sample_index_ext` trong `packets.csv` nhưng không bao giờ làm mốc cho packet sau (cách ly ở bước 6). Nhảy tiến khi `SEQ` liên tục: có bit 0 hoặc 1 thì biết số mẫu mất, không có bit nào là không giải thích được. Index nhảy kèm bit 5: neo lại, không biết số mẫu mất, chuỗi mới (`chain_id` + 1). Index lùi: cách ly packet. Báo bất nhất khi số mẫu mất ít hơn số packet vắng, hoặc nhiều hơn 32 × số packet vắng (`SAMPLE_COUNT` ≤ 32) mà không có bit 0/1. Kênh nhiệt độ `0xB1` (V0.2 mục 11): chỉ số là nhịp 1 s, nên nhảy tiến không ít hơn số packet vắng là khoảng trống đã đếm, không cắt chuỗi | `sample_gap_status`, `sample_gap_unexplained`, `sample_gap_counted`, `sample_index_reanchored`, `sample_index_overlap`, `sample_index_inconsistent` |
| 5. `STATUS` | Đếm từng bit theo kênh (`status_bit_counts`) và ghi `status` của từng packet trong `packets.csv`. Bit dự trữ khác 0 thì báo: V0.1 bit 7–15; V0.2 bit 9–15, và bit 8 ở mọi kênh trừ ECG `0xE1`; ở `0xB1` mọi bit trừ bit 1 và 3 (bit dự trữ không được đếm tên) | `status_reserved_bits` |
| 6. `T_ANCHOR_US` | Theo từng chuỗi (`chain_id`). Packet có `FS_NOMINAL_MHZ = 0` bị cách ly trước và không cắt chuỗi. Packet có bit 0 (FIFO AFE tràn) giữ mẫu nhưng anchor không được kiểm và không làm mốc, vì FIFO đã đầy nên anchor đến muộn so với mẫu cuối (`disposition` = `accepted_anchor_unreliable`, đếm ở `packets_anchor_unreliable`; từ 2026-10-23, trước đó cả packet bị cách ly `timestamp_anomaly`). Mỗi packet so với packet được giữ gần nhất trước nó: phải tăng cùng chiều với chỉ số mẫu, và \|Δk\|·T/(1 + r) − F ≤ ΔA ≤ \|Δk\|·T/(1 − r) + F (ΔA tính theo chiều của Δk), với T = 10⁹/`FS_NOMINAL_MHZ` µs, Δk là số mẫu tính từ mốc, r = `anchor_rate_tolerance_ppm`·10⁻⁶ (ECG: `ecg_anchor_rate_tolerance_ppm`) là dung sai của **tốc độ** mẫu (chu kỳ thật nằm trong [T/(1 + r), T/(1 − r)]) và F = `anchor_tolerance_samples`·T + `anchor_tolerance_extra_us`. `deviation_us` vẫn báo ΔA − Δk·T. Sai thì cách ly packet, mốc giữ nguyên. Phép kiểm chạy **xuôi và ngược**, giữ chiều cách ly ít packet hơn (bằng nhau thì giữ chiều xuôi). Chuỗi mới sau neo lại hoặc khi đổi FS. ECG V0.2: kiểm riêng từng nguồn mốc (mục "Packet Schema V0.2") | `timestamp_anomaly` (`kind` = `not_increasing`/`mismatch`, `deviation_us`, `reference_seq`), `fs_changed`, `fs_invalid` |
| 7. Không nội suy | `gaps` liệt kê lỗ hổng chỉ số mẫu (`index_from`, `index_to`, `lost_samples`, lý do). `samples.csv` chỉ chứa mẫu của packet được nhận | — |
| 8. Không ghép ECG–PPG | Không ghép theo chỉ số mẫu, không dịch kênh, không dùng PAT. Offset kênh chỉ tính ở mô phỏng (mục dưới) | `channel_offset` (chỉ SYNTHETIC) |

Kiểm tra bổ sung: `channel_without_metadata`, `fs_metadata_mismatch`, và
`data_out_of_range` (ECG ngoài [0, 2²⁴), PPG ngoài [0, 2¹⁸), mục 8; dữ liệu vẫn
giữ). Kênh dữ liệu (ECG/PPG) khai báo trong `channels` của metadata mà cả phiên
không có packet nào giải mã được thì báo `channel_missing` và liệt kê trong
`channels_missing` của phiên; kênh chỉ có packet bị cách ly vẫn tính là có mặt.
Metadata vì vậy chỉ khai báo các kênh dự kiến chạy. Không có packet `0xC1` thì không
báo (buổi bench có thể không bấm t0). Luồng không giải mã được packet nào thì không
có phiên để báo. Packet sự kiện: xem R1.

**Dung sai mặc định (chưa kiểm chứng trên phần cứng):** 1 chu kỳ mẫu + 500 µs, cộng
phần do tốc độ mẫu thật lệch tới ±3 % so với danh định (`anchor_rate_tolerance_ppm` =
30 000). ECG có dung sai tốc độ riêng ±1 000 ppm (`ecg_anchor_rate_tolerance_ppm`),
và mốc `SAMP` của ECG V0.2 có phần cố định riêng 200 µs (`samp_anchor_tolerance_us`);
cả hai là giá trị tạm, chốt 2026-10-24 (Packet Schema V0.2 mục 7.5), chỉnh sau
bring-up. Kênh nhiệt độ `0xB1` không so từng cặp: pha `T_ANCHOR_US` − k · 1 s của
cả chuỗi phải nằm trong một cửa sổ 150 ms (`temp_anchor_tolerance_us`, V0.2 mục 11.2,
chốt 2026-10-25); ở 1 Hz, dung sai 1 chu kỳ + 500 µs nhận cả hai anchor cách nhau
1 ms, và so từng cặp để pha trôi dần.

- **Phần cố định:** theo mục 5.1–5.2, `0 ≤ δ < 10⁶/fs + d`, với d khoảng
  0,1–0,2 ms (I²C) hoặc 6 µs (SPI). Vì vậy hiệu δ giữa hai packet nằm trong
  (−T − d, T + d).
- **Phần tăng theo Δk:** tốc độ thực khác danh định. Mục 4 của schema cho clock
  ADC MAX30101 10,2–10,8 MHz và ghi rằng tốc độ PPG thực **chưa biết**. Giá trị
  ±3 % dựa trên **giả định** tốc độ mẫu tỉ lệ với clock ADC và giá trị danh định
  ứng với khoảng giữa dải (10,5 MHz ± 2,9 %); datasheet không nêu điều này.
- Sau một khoảng mất k packet, sai số do tốc độ tích lũy theo cả khoảng: với
  Δk = k · N mẫu, khoảng thời gian thật nằm trong [Δk·T/1,03; Δk·T/0,97]. Nếu
  không có phần này, mọi packet sau khoảng mất bị cách ly (review 2026-10-22: lệch
  3 % và mất 10 packet PPG là đủ). Trước 2026-10-23, logger áp ±3 % lên **chu kỳ**
  (3 % · Δk · T hai phía), tức tốc độ chậm đúng 3 % bị loại oan.
- Từ 2026-10-24, ECG dùng hệ số riêng ±1 000 ppm: tốc độ ECG theo FCLK 32,768 kHz
  (mục 4), nên ±3 % chỉ làm giảm độ nhạy. Hệ số này áp cho ECG của cả V0.1 lẫn V0.2
  (tốc độ là của chip, không phụ thuộc version); các luồng mô phỏng V0.1 cho cùng
  kết quả như trước.
- Hệ số này không phải ước lượng tốc độ thực ở mục 5.3. Thay bằng số đo bench
  khi có (D10).

### Quy tắc R1–R6 (ghi ngày 2026-10-21, đối chiếu với firmware ngày 2026-10-23)

R1–R4 và R6 khớp quy ước của firmware khung (câu hỏi D3–D7 ở cuối tài liệu) và đã
chạy đúng trên luồng giả lập theo firmware (mục "Đối chiếu với firmware khung").
R5 vẫn là giá trị tạm, chờ số đo bench (D8, D10).

- **R1, packet `0xC1`:** kiểm CRC/`SYNC`/`VERSION` và `SEQ` (bước 1–3, 5), **bỏ
  bước 6**; `FS_NOMINAL_MHZ`, `T_FIRST_US` được ghi lại nhưng không diễn giải.
  `SAMPLE_COUNT` phải bằng 1 (mục 10). Từ 2026-10-23 bước 4 áp cho thứ tự sự kiện:
  `FIRST_SAMPLE_INDEX` là số thứ tự sự kiện (`event_ordinal` trong `decode.json`).
  `SEQ` gán lúc gửi, nên giữa hai sự kiện nhận được, số thứ tự tăng bằng khoảng
  `SEQ` (sự kiện mất trên USB, đã có `missing_packets`) cộng số sự kiện bị bỏ trước
  khi có `SEQ`. Tăng nhiều hơn: `events_lost_before_send` kèm `lost`. Tăng ít
  hơn hoặc lùi: `event_ordinal_inconsistent`, rồi kiểm tiếp từ sự kiện đó (số mất
  cạnh một số thứ tự sai không tin được). Bit 1 mà không có khoảng đếm được (sự
  kiện đầu, hoặc firmware bỏ một cạnh t0 trước khi thành sự kiện):
  `events_lost_before_send` với `lost` = null. Không suy ra `SEQ` bắt đầu
  từ 0; mất sự kiện cuối phiên không phát hiện được. Trước 2026-10-23 logger bỏ cả
  bước 4, nên t0 (mốc bơm cuff) bị bỏ trong hàng đợi MCU không để lại issue nào.
- **R2:** bit 0/1/5 ở packet **trước hoặc sau** chỗ nhảy đều được chấp nhận làm
  lời giải thích.
- **R3:** bit 1 (tràn bộ đệm MCU) giải thích một bước nhảy index khi `SEQ` liên
  tục, với giả định `SEQ` được gán lúc gửi.
- **R4:** `VERSION` được kiểm trước CRC; CRC16 little-endian; `SAMPLE_COUNT = 0`
  là vô lý.
- **R5:** dung sai ở `configs/hardware/packet_logger.json`, kể cả dung sai tốc độ
  ±3 % (thêm 2026-10-22), dung sai tốc độ ECG ±1 000 ppm và dung sai mốc `SAMP`
  200 µs (thêm 2026-10-24).
- **R6 (2026-10-22):** chuỗi chỉ số/thời gian (`chain_id`) đánh số từ 0 trong
  từng phiên và kênh, tăng 1 khi index nhảy kèm bit 5 (neo lại, `sample_index_reanchored`)
  hoặc khi `FS_NOMINAL_MHZ` đổi. Theo R2 bit 5 có thể ở packet trước hoặc sau chỗ
  nhảy, nên bit 5 mà index vẫn liên tục **không** cắt chuỗi; nếu khi đó anchor cũng
  đổi thì bước 6 báo `timestamp_anomaly`. Đây là giới hạn đã biết: neo lại mà chỉ
  số tình cờ trùng giá trị kỳ vọng không được coi là chuỗi mới. Phiên mới luôn bắt
  đầu chuỗi 0 của phiên đó. Packet `FS_NOMINAL_MHZ = 0` bị cách ly (`fs_invalid`)
  và không cắt chuỗi.

## Packet Schema V0.2 (từ 2026-10-24)

Logger đọc cả V0.1 và V0.2 ([spec V0.2](../../configs/hardware/Packet_Schema_V0.2.md)).
Config `wire_versions` = `[1, 2]`, `packet_schemas` = `["packet-v0.1", "packet-v0.2"]`.

- **Bảng mã kênh theo version** (decoder, sau CRC): `0xA1`–`0xA6` (IMU) và `0xD1`
  (thông tin thiết bị) chỉ hợp lệ ở V0.2; ở V0.1 là `unknown_channel`. Bit `STATUS`
  dự trữ: 7–15 ở V0.1; 9–15 ở V0.2, cộng bit 8 ở mọi kênh trừ `0xE1`.
- **Một phiên trộn version:** `version_mixed_in_session`; mọi packet được giữ và kiểm
  riêng theo (phiên, version), nên `decode.json` có một mục phiên cho mỗi version
  (`packet_schema`), issue theo kênh mang trường `version`, và kênh khai báo mà
  version đó không có sẽ thành `channel_missing`.
- **IMU:** dữ liệu có dấu, nhận −32 768 … 32 767. Packet bit 7 (phần tồn đọng) giữ
  mẫu, không kiểm anchor, không làm mốc (`accepted_anchor_unreliable`), như bit 0.
- **Bit 5 ở V0.2:** chỉ xét bit của chính packet; packet bit 5 luôn bắt đầu chuỗi mới,
  kể cả khi chỉ số liên tục (`sample_index_reanchored`, `lost_samples` = null). Bit
  của packet `FS_NOMINAL_MHZ = 0` (bị cách ly) được áp cho packet tin cậy kế tiếp,
  nên ranh giới neo lại không mất. V0.1 giữ R2/R6.
- **Thông tin thiết bị `0xD1`:** kiểm payload (`device_info_invalid` kèm `problem`:
  `sample_count`, `layout`, `header`, `status`, `text`); số thứ tự so với `SEQ`
  (`device_info_lost_before_send`, `device_info_ordinal_inconsistent`, cùng khóa
  `ordinal`/`lost` như sự kiện); mỗi phiên có `device_info` (`valid_packets`, các
  định danh khác nhau theo thứ tự `SEQ`). Báo `device_info_changed`,
  `device_info_missing` (phiên V0.2 nguồn `DEVICE` không có `0xD1` hợp lệ) và
  `firmware_metadata_mismatch`. `0xD1` không vào `samples.csv` và không thuộc kiểm
  `channel_missing`.
- **Nhiệt độ trong chip `0xB1` (V0.2 mục 11, từ 2026-10-25):** chỉ hợp lệ ở V0.2. Trước
  bước 4, packet phải có `SAMPLE_COUNT = 1`, `FS_NOMINAL_MHZ = 1 000`,
  `T_FIRST_US = T_ANCHOR_US` và chỉ bit 1, 3; sai thì `temp_header_invalid` và cách ly
  (header không tin được: không làm mốc, bit `STATUS` của nó không áp cho packet sau).
  Dữ liệu có dấu, nhận −2 048 … 2 047 (1/16 °C). Chỉ số nhảy nhiều hơn số packet
  vắng là `sample_gap_counted` (khoảng trống biết độ dài, chuỗi giữ nguyên nên
  timing vẫn được kiểm qua khoảng trống); nhảy đúng bằng số packet vắng chỉ có
  `missing_packets`. Timing kiểm theo cửa sổ pha (`timestamp_anomaly` với `kind` =
  `phase`). Không tham gia `channel_offset` (anchor là thời điểm đọc ra). Chỉ khai báo
  `0xB1` trong metadata khi firmware có gửi.
- **Mốc `SAMP` của ECG (bit 8, spec mục 7; từ 2026-10-24):** packet ECG bit 8 có
  `T_ANCHOR_US` là cạnh `SAMP` của mẫu cuối; không có bit 8 là mốc đọc FIFO như V0.1.
  Trong mỗi chuỗi, bước 6 chạy **riêng** cho từng nguồn: packet bit 8 chỉ so với
  packet bit 8, với F = `samp_anchor_tolerance_us` (200 µs, không cộng chu kỳ mẫu)
  để lệch một mẫu (1,953 ms) bị bắt; packet mốc đọc FIFO so với nhau với F như cũ.
  Hai nguồn lệch nhau một khoảng chưa biết (thời gian mẫu nằm trong FIFO cộng độ trễ
  đọc), nên không bao giờ so chéo; đổi nguồn không cắt chuỗi. `timestamp_anomaly`
  của ECG V0.2 có thêm `anchor_source` (`samp` hoặc `fifo_read`).
  - Phép kiểm `SAMP` qua n mẫu là **yếu** khi (n + 1)·T/(1 + r) − F ≤ n·T/(1 − r) + F:
    anchor muộn một mẫu, ở tốc độ nhanh nhất trong dung sai và sai số anchor tới F,
    vẫn lọt (sớm một mẫu chỉ lọt khi muộn một mẫu đã lọt). Với giá trị mặc định là
    n ≥ 398 mẫu (khoảng 0,78 s; với packet 16 mẫu là từ 24 packet mất liền). Logger
    báo `anchor_check_weak` (`seq`, `reference_seq`, `steps`) thay vì coi là đã kiểm;
    chuỗi chỉ nhận được đúng một packet bit 8 (không có gì để so) cũng báo, với
    `reference_seq` và `steps` = null.
  - Tóm tắt kênh ECG V0.2 có `anchor_sources`: số packet theo bit 8 như firmware gửi
    (`samp`, `fifo_read`), tính trên **mọi** packet nhận được trừ bản trùng và packet
    xung đột (kể cả packet bị cách ly hoặc có bit 0/7), và `switch_seqs` (các `SEQ`
    mà bit 8 đổi so với packet nhận được trước đó). Nhờ vậy một lần rơi về mốc đọc
    FIFO luôn lộ ra; anchor dùng được hay không xem ở `packets_anchor_unreliable` và
    `disposition`. Bit 8 được đếm trong `status_bit_counts` với tên `anchor_samp`.
  - Theo spec mục 7.2, mốc `SAMP` chỉ trở lại sau khi khởi động lại ánh xạ bằng
    `SYNCH`, mà packet đầu tiên sau đó mang bit 5. Packet bit 8 đi ngay sau (`SEQ`
    liền, không mất gì ở giữa) một packet không có bit 8 mà không có bit 5 (của chính
    nó, hoặc chuyển từ các packet `FS_NOMINAL_MHZ = 0` ngay trước nó như ở bước 4) thì
    báo `samp_resumed_without_reanchor`. Có `SEQ` mất ở giữa thì không báo, vì packet
    bit 5 có thể nằm trong phần mất.
  - Luồng có packet bit 8 mà metadata `0xE1` thiếu `latency_samp_l_us` thì báo
    `samp_latency_metadata_missing` (spec mục 8): độ trễ của mốc `SAMP` khác của mốc
    đọc FIFO.
  - Lệch cố định một mẫu ngay từ packet bit 8 đầu tiên của chuỗi thì logger **không**
    bắt được (spec mục 7.2); chỉ phép đo kích thích bắt được.
  - Một lệch phát sinh giữa chuỗi bị bắt, nhưng theo quy ước số đông logger cách ly
    phía ngắn hơn, có thể là phía đúng (ca mô phỏng `samp_shift`).
- **Cấu hình AFE `0xD2` (spec mục 12, từ 2026-10-25):** không có mẫu, không cần khóa
  metadata, không thuộc `channel_missing`. Packet sai báo `afe_config_invalid` kèm
  `problem` (`header`, `status`, `sample_count`, `layout`, `afe`, `source_or_state`,
  `generation`, `registers`: đúng bộ và thứ tự thanh ghi của từng chip, giá trị 8 bit
  với MAX30101 và BMI270). Số thứ tự so với `SEQ` như `0xD1`. Mỗi phiên có
  `afe_config`: theo từng AFE, các trạng thái khác nhau (`first_seq`, `t_anchor_us`,
  nguồn, đang chạy hay không, thế hệ, thanh ghi dạng hex, số packet). Báo
  `afe_config_generation_backwards`, `afe_config_changed_in_generation`; với phiên
  `DEVICE`, theo từng AFE có kênh khai báo trong metadata: `afe_config_missing`,
  `afe_not_configured`, `afe_fake_source`.
- **Xác nhận lệnh `0xD3` (spec mục 13):** kiểm miền từng trường và quan hệ giữa kết
  quả và thế hệ (`command_ack_invalid`); `SET_PPG_LED` xong mà phiên không có `0xD2` của
  MAX30101 cùng thế hệ báo `command_ack_without_config`; kết quả khác 0 báo
  `command_failed` kèm tên kết quả. Mỗi phiên có `commands`.

## Lệnh xuống thiết bị (spec mục 13, từ 2026-10-25)

`record --port ... --duration-s ... --commands` tạo `command_inbox.jsonl` (rỗng) trong
thư mục output. Trong lúc ghi, người vận hành dùng:

```powershell
.\.venv\Scripts\python.exe scripts/device_command.py --recording runs/packet_logger/<thư mục> ping
.\.venv\Scripts\python.exe scripts/device_command.py --recording runs/packet_logger/<thư mục> set-ppg-led --green 18 --red 36 --ir 36
```

Mã dòng LED theo bước 0,2 mA, xanh là mã **mỗi nhánh** (LED3 và LED4); firmware từ chối
mã > 127. "queued" chỉ nghĩa là đã ghi vào hộp thư. Vòng ghi xem hộp thư sau mỗi lần đọc
cổng (kể cả khi không có byte), lấy `SESSION_ID` đích từ packet gần nhất, gửi một lệnh
mỗi lần, chờ `0xD3` 500 ms, gửi lại cùng byte tối đa 3 lần, rồi ghi kết quả "không biết".
Hai lần gửi bất kỳ (lệnh mới hay gửi lại) cách nhau ít nhất 0,5 s. `CMD_SEQ` không lặp
trong một lần ghi: sau 65 536 lệnh, các lệnh sau bị từ chối. Dòng hộp thư dài quá
1 024 byte bị bỏ tới hết ký tự xuống dòng.
`SESSION_ID` đổi (MCU khởi động lại) thì lệnh đang chờ bị hủy. Mọi bước ghi vào
`commands_sent.jsonl` (`queued`, `rejected`, `sent`, `acked`, `unknown`,
`session_changed`, `inbox_truncated`, `not_sent`); hai file này có hash trong manifest
(`commands`). `decode.json`, `packets.csv`, `samples.csv` chỉ phụ thuộc `raw.bin`, nên
replay không cần nhật ký lệnh.

## Lệch kênh: chỉ có nghĩa trong mô phỏng

Trên thiết bị, ECG và PPG đi qua hai AFE có độ trễ hiệu dụng `L` khác nhau và
chưa đo. Logger không thể biết lệch kênh từ packet, nên với `DEVICE`, giá trị
`offset_vs_ecg_us` là `null` kèm lý do. Offset thật được đo bằng kích thích
chung theo kế hoạch đo 10 phút.

Với `SYNTHETIC`, generator khai báo `common_index_epoch: true` (mẫu 0 của mọi
kênh cùng thời điểm), trừ ca V0.2 `samp_remap`: index ECG bắt đầu lại từ 0 sau
`SYNCH` trong khi thời gian vẫn chạy, nên ca này khai `false` và không có offset
kênh. Logger ước lượng epoch của mỗi kênh là `T_ANCHOR_US` của
packet được nhận đầu tiên trừ `k_last·T`, rồi lấy hiệu so với ECG. Vượt
`channel_offset_tolerance_us` thì báo `channel_offset`. Giá trị dương nghĩa là
nhãn thời gian của kênh đó muộn hơn ECG, cùng quy ước với `offset_ppg_minus_ecg_us`
của v2, tức `L_PPG − L_ECG`. Offset này **không phải PAT**.

## Chạy

Từ Git root, PowerShell, môi trường đã cài theo repo:

```powershell
.\.venv\Scripts\python.exe scripts/simulate_packets.py --config configs/hardware/packet_simulation_v3.json --case crc --output runs/packet_simulation_v3/crc_01
.\.venv\Scripts\python.exe scripts/packet_logger.py record --source-file runs/packet_simulation_v3/crc_01/stream.bin --metadata runs/packet_simulation_v3/crc_01/session_metadata.json --output runs/packet_logger/crc_record_01
.\.venv\Scripts\python.exe scripts/packet_logger.py replay --raw runs/packet_logger/crc_record_01/raw.bin --metadata runs/packet_simulation_v3/crc_01/session_metadata.json --expect runs/packet_logger/crc_record_01/session_manifest.json --output runs/packet_logger/crc_replay_01
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_packet_logger.py
```

Không truyền `--output` thì output là `runs/packet_logger/<UTC>_record` hoặc
`_replay`. Mọi thư mục output phải là thư mục mới; mọi file được mở bằng
exclusive create (`xb`). Exit 1 nghĩa là input/config/metadata sai, hoặc replay
khác manifest. Exit 0 **không** có nghĩa là luồng sạch: phải đọc `issue_counts`.

## Metadata phiên (đầu vào, mục 11)

`--metadata` là JSON `packet-session-metadata-v0`, gồm:

- `source_type` (`SYNTHETIC` hoặc `DEVICE`), `clock_id`, `firmware_version`,
  `firmware_commit`, `device_id`, `operator`, `electrode_type`,
  `electrode_placement`;
- `channels`, khóa dạng `"0xE1"`, mỗi kênh có `sensor`, `fs_nominal_mhz`,
  `latency_l_us`, `latency_source`, `unit_conversion`, `afe_config` (object
  thanh ghi AFE theo mục 11, ví dụ `ECG_RATE`, `LED_PW`). Riêng `0xE1` có thể
  thêm cặp `latency_samp_l_us`, `latency_samp_source` (V0.2 mục 8: độ trễ của mốc
  `SAMP`; `latency_l_us` là của mốc đọc FIFO): có cả hai hoặc không có cái nào,
  kênh khác không được có. Phiên có packet ECG bit 8 phải khai báo cặp này (null
  kèm lý do khi chưa đo), nếu không logger báo `samp_latency_metadata_missing`;
- `simulation` (chỉ cho SYNTHETIC, `null` với DEVICE);
- `null_reasons`.

Mọi trường `null` (trừ `simulation`) phải có lý do trong `null_reasons`, với
khóa là đường dẫn như `channels.0xE1.latency_l_us`. Lý do cho trường không null
bị từ chối. Generator v3 tự ghi `session_metadata.json`. Với thiết bị, người vận
hành điền tay trước phiên; không có giá trị thì để `null` kèm lý do, không đoán.

Với firmware khung (`firmware/README.md`), lấy các giá trị sau:

- `firmware_version`: phiên bản và ELF SHA-256 in trên log UART0 lúc khởi động;
  `firmware_commit`: commit đã build. `SESSION_ID` cũng in trên log UART0.
- `electrode_placement`: theo protocol v0.2 mục 5.2 (LA cổ tay trái, RA cổ tay
  phải, RL cẳng tay trái).
- Mỗi kênh trong luồng phải có mục trong `channels`, kể cả `0xC1`; thiếu thì logger
  báo `channel_without_metadata`.
- `afe_config` của PPG ghi cả ánh xạ khe → LED (schema mục 7, 11).

## Đầu ra

`record` ghi các file sau. Hai bản sao đầu vào được ghi **trước** byte đầu tiên,
nên phiên bị ngắt vẫn biết đã thu với config và metadata nào; manifest ghi **sau
cùng**. Thiếu manifest nghĩa là phiên chưa hoàn tất: giữ nguyên `raw.bin` dở để
kiểm tra, không xóa. Bản sao đầu vào chỉ giúp khi tiến trình bị ngắt, không bảo
đảm dữ liệu còn nguyên khi mất điện.

| File | Nội dung |
| --- | --- |
| `raw.bin` | Đúng từng byte đã nhận, kể cả byte lỗi; mở `xb`, `fsync` cuối phiên |
| `rx_chunks.csv` | Mỗi lần đọc: offset trong luồng, số byte, `t_rx_monotonic_ns` của PC |
| `t_rx_packets.csv` | `t_rx` của từng packet (theo lần đọc chứa byte cuối). Chỉ dùng chẩn đoán đường truyền, **không bao giờ** là thời gian mẫu |
| `decode.json` | Lỗi decode, `sync_candidates_rejected`, issue, `issue_counts`, tóm tắt từng phiên/kênh (kể cả số chuỗi `chains`), `gaps`, sự kiện, offset (chỉ SYNTHETIC), giới hạn |
| `packets.csv` | Mỗi packet đã giải mã theo thứ tự đến: trường header (kể cả `version`), `seq_ext`, `sample_index_ext`, `chain_id`, `disposition`. `chain_id` để trống với bản trùng, xung đột và packet `0xC1`/`0xD1` |
| `samples.csv` | Mẫu của packet được nhận: phiên, kênh, `chain_id`, `seq_ext`, `sample_index_ext`, giá trị, `version` (cột cuối, từ 2026-10-24). Sắp theo (phiên, version, kênh, `chain_id`, `sample_index_ext`); khóa này là duy nhất, kể cả khi một phiên trộn hai version, còn `sample_index_ext` có thể lặp giữa hai chuỗi khi neo lại lùi. Không có cột thời gian |
| `logger_config.json`, `session_metadata.json` | Bản sao đầu vào, ghi trước khi đọc nguồn |
| `session_manifest.json` | Trường mục 11 (`packet_schemas` của luồng, `sessions` với `packet_schema` và `device_info` của từng phiên, `session_id`/`session_ids`, `clock_id`, firmware, thiết bị, giờ PC lúc bắt đầu/kết thúc, metadata kênh, `null_reasons`); SHA-256 raw và mọi output; `issue_counts`; hash config/metadata; git commit/dirty, hash code (LF), Python; `source_type` |

Trong `record`, decode chạy trực tiếp theo từng đoạn đọc. Sau đó `raw.bin` được
đọc lại từ đĩa và decode lần nữa. Hai kết quả phải giống từng byte, nếu không thì
dừng (`live_equals_offline_decode`). `replay` ghi `decode.json`, `packets.csv`,
`samples.csv` và `replay_report.json`. Với `--expect`, hash raw, ba output decode
và hash config/metadata được so với manifest.

## Giới hạn

- Chưa chạy với MCU thật hay cổng serial; chưa có dữ liệu `DEVICE`.
- Không phát hiện được packet mất trước `SEQ` đầu tiên hoặc sau `SEQ` cuối cùng
  đã nhận. D5 nay đã chốt `SEQ` bắt đầu từ 0 mỗi phiên, nên logger có thể báo mất
  đầu phiên khi `SEQ` nhận đầu tiên lớn hơn 0; code hiện chưa dùng điều này.
- Trên thiết bị, cổng USB native có chữ của ROM và bootloader trước packet đầu
  tiên. Decoder bỏ qua và báo một `skipped_bytes` ở offset 0; đây là bình thường,
  không phải lỗi đường truyền.
- Một raw có thể kéo qua nhiều lần MCU khởi động lại (reset, nạp lại firmware). Mỗi
  lần là một phiên mới (`session_change`, `SEQ`, chỉ số và đồng hồ từ 0), chữ ROM lại
  xuất hiện trước packet đầu của phiên, và reset có thể cắt cụt packet đang gửi:
  packet đó hỏng CRC (`crc_mismatch`) và bị bỏ cùng chữ ROM sau nó trong một
  `skipped_bytes`. Packet bị cắt là `SEQ` cuối của kênh trong phiên cũ nên không có
  khoảng trống nào chỉ ra nó. Manifest ghi `session_ids` và `sessions` theo từng
  `SESSION_ID` (`packet_schema`, `device_info`); firmware nạp lại giữa hai phiên hiện
  thành hai định danh ở hai phiên, không phải `device_info_changed`. Kiểm bằng
  `tests/test_packet_v02.py` (ba lần khởi động trong một raw, 2026-10-24).
- `T_ANCHOR_US` được kiểm xuôi và ngược, rồi giữ chiều cách ly ít packet hơn. Vì
  vậy một anchor sai ở đầu chuỗi, ở cuối chuỗi, hoặc ngay sau khoảng mất (khi dung
  sai đã nới theo Δk) chỉ làm mất packet đó. Hai trường hợp vẫn khó:
  - Một bước nhảy thời gian kéo dài làm **phía ngắn hơn** của chuỗi bị cách ly.
    Logger không biết phía nào đúng, nên đây là quy ước số đông. Issue
    `timestamp_anomaly` vẫn lộ rõ, và người xem phải kiểm tra raw.
  - Nếu cả anchor đầu lẫn anchor cuối của một chuỗi đều sai, hai chiều cách ly
    bằng nhau. Chiều xuôi được giữ, nên các packet **đúng** ở giữa bị cách ly
    (ECG 8 packet, đầu và cuối cùng +20 ms: cách ly SEQ 1–6).
- Dung sai tốc độ ±3 % (ECG ±1 000 ppm) là giả định chưa đo (xem dung sai mặc
  định). Một bước nhảy thời gian nhỏ hơn dung sai đã nới sau một khoảng mất dài
  không bị phát hiện; với mốc `SAMP`, trường hợp này được báo `anchor_check_weak`.
- Logger không kiểm được lệch cố định của ánh xạ xung `SAMP` ↔ mẫu, và không dùng
  `latency_samp_l_us` (không tính thời gian mẫu).
- Toàn bộ packet được giữ trong RAM tới cuối phiên. 10 phút (khoảng 5·10⁴ packet)
  không có vấn đề; phiên rất dài sẽ cần ghi theo dòng.
- Chỉ dùng thư viện chuẩn; chưa có hiệu chỉnh `L`, fs thật hay drift.

## Câu hỏi cho Đức Anh

Trả lời ngày 2026-10-23 theo firmware khung
([firmware/README.md](../../firmware/README.md), mục "Quy ước packet của
firmware"); D8 và D10 chờ bench.

- **D1.** Byte order của CRC16: little-endian như các trường khác (đang giả định)
  hay big-endian? → **Little-endian.**
- **D2.** Firmware có lúc nào gửi `VERSION` khác `0x01` trên cùng cổng không? Đổi
  layout thì có tăng `VERSION` (mục 2) không? → **Luôn `0x01`; đổi layout thì
  tăng `VERSION` cùng bản firmware mới, không trộn trong một phiên.**
- **D3.** Bit 0/5 bật ở packet nào so với khoảng mất (packet đọc lúc phát hiện
  tràn hay packet đã neo lại)? `SEQ` được gán trước hay sau bộ đệm MCU (bit 1)?
  → **Bit 0 bật ở packet đọc lúc phát hiện tràn; packet kế có index nhảy. `SEQ`
  gán lúc gửi, sau hàng đợi MCU: packet bị bỏ ở hàng đợi không có `SEQ`, packet
  kế bật bit 1 (đúng giả định của R3); nếu packet mang bit 0 hoặc 1 bị bỏ ở hàng
  đợi hoặc firmware gửi thất bại (driver USB không nhận trong 20 ms), các bit đó
  chuyển sang packet gửi được kế tiếp (bit 0 từ
  2026-10-23). Firmware khung chưa sinh bit 5.**
- **D4.** Bit 4 bật từ khi nào và tắt khi nào (theo từng cấu hình sau bench)?
  Có bật cho `0xC1` không? → **Bật trên mọi packet ECG/PPG cho tới khi đo xong
  `L` của cấu hình; không bật cho `0xC1`.**
- **D5.** `SEQ` và `FIRST_SAMPLE_INDEX` có bắt đầu từ 0 ở mỗi phiên không? →
  **Có.**
- **D6.** Packet `0xC1`: gửi giá trị gì cho `FIRST_SAMPLE_INDEX`, `FS_NOMINAL_MHZ`,
  `T_FIRST_US`? `SEQ` của `0xC1` có đếm riêng không? (mục 15) → **Như quy tắc tạm
  R1: số thứ tự sự kiện, 0, `T_ANCHOR_US`; `SEQ` đếm riêng (schema mục 10).**
- **D7.** Có khi nào `SAMPLE_COUNT = 0` (đọc FIFO rỗng) không? Có gửi packet đó
  không? → **Không gửi.**
- **D8.** Sau bench: `d_ptr_us`/`d_word_us` đo được để chốt dung sai `T_ANCHOR_US`.
- **D9.** USB CDC: baud, kích thước buffer; có log text nào đi chung cổng packet
  không (mục 13)? → **Packet đi USB Serial/JTAG native, không có baud; bộ đệm TX
  8 192 byte, hàng đợi MCU 64 packet, timeout ghi 20 ms. Log chữ đi UART0;
  firmware không ghi chữ ra cổng packet, nhưng lúc khởi động có thể có chữ của
  ROM và bootloader trước packet đầu tiên.**
- **D10 (thêm 2026-10-22).** Tốc độ lấy mẫu thật của PPG (và ECG) lệch bao nhiêu so
  với `FS_NOMINAL_MHZ` trên board? Logger đang giả định ±3 %
  (`anchor_rate_tolerance_ppm` = 30 000), suy từ clock ADC MAX30101
  10,2–10,8 MHz ở mục 4. Phép đo 10 phút có cho số này không? → **ECG: tạm
  ±1 000 ppm (`ecg_anchor_rate_tolerance_ppm`, chốt 2026-10-24, Packet Schema V0.2
  mục 7.5), chỉnh sau bring-up. PPG vẫn chờ số đo.**

## Danh sách để Đức Anh review logger theo spec

Review ngày 2026-10-23, đối chiếu với firmware khung (`firmware/`):

- [x] `HEADER = struct.Struct("<2sBBIIIQQIHH")` và vị trí DATA/CRC khớp struct
      firmware: encoder C (`firmware/app/packet_v01.c`, từ 2026-10-24 là
      `firmware/app/packet_wire.c` gửi V0.2) ghi đúng thứ tự, độ rộng,
      little-endian, CRC trên byte 2 … 39 + 4N.
- [x] CRC: known answer `0x29B1` cho `"123456789"`; packet ví dụ 50 byte trong
      `tests/fixtures/packet_v3_expected.json` giống từng byte với known-answer của
      firmware lúc đó (`tests/test_firmware_packet_kat.py`; từ 2026-10-24 firmware
      tự kiểm bằng known-answer V0.2, packet V0.1 vẫn nằm trong fixture). Encoder C chạy thật trên máy
      tính trong `tests/test_firmware_c_encoder.py` (cần trình biên dịch C, xem
      `firmware/README.md`), cho cùng byte với `packet_wire.py` trên packet ngẫu
      nhiên. Firmware tự kiểm lại trên bo lúc khởi động; phần này chưa chạy vì chưa
      có bo.
- [x] Mã kênh (mục 7) và tên bit STATUS (mục 9) trong `packet_wire.py` khớp
      `firmware/include/packet_v01.h` (nay là `packet_wire.h`, thêm mã kênh và bit
      `STATUS` của V0.2).
- [x] Quy tắc R1–R6: R1–R4 và R6 giữ nguyên; R5 giữ giá trị tạm tới khi có số đo
      bench.
- [x] Dung sai mặc định phù hợp cấu hình dự kiến (ECG 512 sps, N = 16): dung sai
      một packet bình thường khoảng 3,4 ms. Dung sai tốc độ ±3 % giữ tới khi có
      số đo (D10). Từ 2026-10-24 ECG dùng ±1 000 ppm: khoảng 2,48 ms với mốc đọc
      FIFO, 0,23 ms với mốc `SAMP`.
- [x] Trường metadata phiên đủ cho mục 11; cách điền cho firmware khung ở mục
      "Metadata phiên".
- [ ] Khi có bo và cách đọc cổng serial được duyệt: chạy 10 phút không tải,
      `SEQ` và `T_ANCHOR_US` tăng đơn điệu, lưu raw + manifest, ghi rõ là dữ liệu
      thiết bị, không đo trên người.

### Đối chiếu với firmware khung

[`tests/test_firmware_stream_compat.py`](../../tests/test_firmware_stream_compat.py)
dựng luồng byte theo đúng quy ước của firmware khung trong 10 phút (V0.2 từ
2026-10-24): chữ ROM ở đầu, ECG giả 1 953 µs × 16 mẫu, PPG giả ba khe 5 000 µs × 8
mẫu dùng chung mốc neo, IMU giả sáu trục 10 000 µs × 10 mẫu dùng chung mốc neo,
task đọc trễ ngẫu nhiên 20–400 µs, 7 sự kiện t0, packet thông tin thiết bị `0xD1`
mỗi 10 s, nhiệt độ giả `0xB1` mỗi 1 s (đọc ra 29–39 ms sau nhịp), một lần tràn hàng
đợi MCU kèm USB timeout của chính packet mang bit 1, một USB timeout ở PPG khe 2. Với
config mặc định, logger nhận 101 046 packet (gồm 60 packet `0xD1`, 36 000 packet IMU,
600 packet `0xB1` và 180 packet `0xD2`; trước khi có `0xD1` và IMU là 64 206), 1 027 792
mẫu, tất cả
đúng công thức `DATA` của firmware. Phần tồn đọng và FIFO IMU đầy được
kiểm riêng trong `tests/test_firmware_imu_plan.py`. Chỉ có các issue đã cài: `skipped_bytes` (chữ ROM ở offset 0) và 2
`missing_packets`, cùng hai khoảng trống: ECG mất 32 mẫu (bit 1 đã chuyển sang
packet kế), PPG khe 2 mất 8 mẫu. Không có `timestamp_anomaly`. Test thứ hai cho
thấy khi mất 48 mẫu ECG (hai lần tràn hàng đợi cộng một USB timeout), logger chỉ
giải thích được khoảng trống nhờ bit 1 được chuyển sang packet kế; không chuyển
thì báo `sample_index_inconsistent`. Tương tự với bit 0: một packet ECG báo tràn
FIFO AFE 40 mẫu rồi gửi thất bại chỉ được giải thích khi bit 0 được chuyển sang
packet kế. Hai test khác kiểm sự kiện t0: packet sự kiện bị bỏ ở hàng đợi MCU cho
`events_lost_before_send` với `lost` = 1; cạnh bị hàng đợi ISR bỏ cho issue
đó với `lost` = null ở sự kiện kế tiếp. Đây là luồng SYNTHETIC dựng bằng
`encode_packet` trong Python theo quy ước của firmware, không phải byte từ MCU.
