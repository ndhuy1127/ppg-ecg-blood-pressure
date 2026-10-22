# Logger packet phía máy tính (Packet Schema V0.1)

## Phạm vi và ranh giới

Logger đọc luồng byte theo [Packet Schema V0.1](../../configs/hardware/Packet_Schema_V0.1.md)
(mục 6), làm các kiểm tra ở mục 12 theo **từng phiên và từng kênh**, ghi raw bất
biến, rồi ghi session manifest có hash. Phiên bản logger: `packet-logger-v0`.

- **Đã có (2026-10-21):** decoder, kiểm tra, runner `record`/`replay`, test với
  luồng SYNTHETIC `synthetic-packet-v3` ([mô phỏng](packet_simulation.md)).
- **Sửa theo review độc lập Tuần 5 (2026-10-22):** kiểm
  `T_ANCHOR_US` hai chiều, thêm dung sai tốc độ, thêm cột `chain_id`, cách ly
  packet `FS_NOMINAL_MHZ = 0`, thêm cận trên số mẫu mất, đổi cách đếm lỗi decode.
  Chi tiết ở các mục dưới và trong `reports/weekly/week_05/linh.md`. Vẫn là
  `packet-logger-v0`, vì trước lần sửa này code chưa từng được commit.
- **Chờ:** đọc cổng serial trực tiếp, vì cần `pyserial`, mà gói này chưa có trong
  `requirements.txt` và chưa được nhóm duyệt (mục 7). Cũng chờ chạy 10 phút với
  firmware khung của Đức Anh, vì chưa có firmware.
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
là hết phiên. Hiện CLI mở file bằng `--source-file` (chế độ `rb`), coi như luồng
đến từ thiết bị. Khi `pyserial` được duyệt, có thể truyền `serial.Serial(...)`
vào đây. Riêng `read` của serial trả `b""` cả khi hết timeout, nên lúc đó cần
thêm điều kiện dừng (thời lượng, Ctrl+C); phần này chưa làm. Decoder nhận byte
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
| 4. `FIRST_SAMPLE_INDEX` | Mở rộng uint32 rồi so với `index + N` của packet trước. Nhảy tiến khi `SEQ` liên tục: có bit 0 hoặc 1 thì biết số mẫu mất, không có bit nào là không giải thích được. Bit 5: neo lại, không biết số mẫu mất, chuỗi mới (`chain_id` + 1). Index lùi: cách ly packet. Báo bất nhất khi số mẫu mất ít hơn số packet vắng, hoặc nhiều hơn 32 × số packet vắng (`SAMPLE_COUNT` ≤ 32) mà không có bit 0/1 | `sample_gap_status`, `sample_gap_unexplained`, `sample_index_reanchored`, `sample_index_overlap`, `sample_index_inconsistent` |
| 5. `STATUS` | Đếm từng bit theo kênh (`status_bit_counts`) và ghi `status` của từng packet trong `packets.csv`. Bit dự trữ 7–15 khác 0 thì báo | `status_reserved_bits` |
| 6. `T_ANCHOR_US` | Theo từng chuỗi (`chain_id`). Packet có `FS_NOMINAL_MHZ = 0` bị cách ly trước và không cắt chuỗi. Mỗi packet so với packet được giữ gần nhất trước nó: phải tăng cùng chiều với chỉ số mẫu, và \|ΔA − Δk·T\| ≤ `anchor_tolerance_samples`·T + `anchor_tolerance_extra_us` + `anchor_rate_tolerance_ppm`·10⁻⁶·\|Δk\|·T, với T = 10⁹/`FS_NOMINAL_MHZ` µs và Δk là số mẫu tính từ mốc. Sai thì cách ly packet, mốc giữ nguyên. Phép kiểm chạy **xuôi và ngược**, giữ chiều cách ly ít packet hơn (bằng nhau thì giữ chiều xuôi). Chuỗi mới sau neo lại hoặc khi đổi FS | `timestamp_anomaly` (`kind` = `not_increasing`/`mismatch`, `deviation_us`, `reference_seq`), `fs_changed`, `fs_invalid` |
| 7. Không nội suy | `gaps` liệt kê lỗ hổng chỉ số mẫu (`index_from`, `index_to`, `lost_samples`, lý do). `samples.csv` chỉ chứa mẫu của packet được nhận | — |
| 8. Không ghép ECG–PPG | Không ghép theo chỉ số mẫu, không dịch kênh, không dùng PAT. Offset kênh chỉ tính ở mô phỏng (mục dưới) | `channel_offset` (chỉ SYNTHETIC) |

Kiểm tra bổ sung: `channel_without_metadata`, `fs_metadata_mismatch`, và
`data_out_of_range` (ECG ngoài [0, 2²⁴), PPG ngoài [0, 2¹⁸), mục 8; dữ liệu vẫn
giữ). Với packet sự kiện có thêm `event_sample_count` và `unknown_event_code`
(mã ngoài 1–4 ở mục 10).

**Dung sai mặc định (chưa kiểm chứng trên phần cứng):** 1 chu kỳ mẫu + 500 µs +
3 % của khoảng mẫu tính từ mốc (`anchor_rate_tolerance_ppm` = 30 000).

- **Phần cố định:** theo mục 5.1–5.2, `0 ≤ δ < 10⁶/fs + d`, với d khoảng
  0,1–0,2 ms (I²C) hoặc 6 µs (SPI). Vì vậy hiệu δ giữa hai packet nằm trong
  (−T − d, T + d).
- **Phần tăng theo Δk:** tốc độ thực khác danh định. Mục 4 của schema cho clock
  ADC MAX30101 10,2–10,8 MHz và ghi rằng tốc độ PPG thực **chưa biết**. Giá trị
  ±3 % dựa trên **giả định** tốc độ mẫu tỉ lệ với clock ADC và giá trị danh định
  ứng với khoảng giữa dải (10,5 MHz ± 2,9 %); datasheet không nêu điều này.
- Sau một khoảng mất k packet, sai số do tốc độ tích lũy theo cả khoảng
  (khoảng 3 % · k · N · T). Nếu không có phần này, mọi packet sau khoảng mất bị
  cách ly (review 2026-10-22: lệch 3 % và mất 10 packet PPG là đủ).
- Hệ số được áp cho mọi kênh. Với ECG (FCLK 32,768 kHz, mục 4), hệ số này chỉ làm
  giảm độ nhạy, không gây cách ly giả.
- Hệ số này không phải ước lượng tốc độ thực ở mục 5.3. Thay bằng số đo bench
  khi có (D10).

### Quy tắc tạm, chờ Đức Anh xác nhận (ghi ngày 2026-10-21)

- **R1, packet `0xC1`:** chỉ kiểm CRC/`SYNC`/`VERSION` và `SEQ` (bước 1–3, 5),
  **bỏ bước 4 và 6**. `FIRST_SAMPLE_INDEX`, `FS_NOMINAL_MHZ`, `T_FIRST_US` được ghi
  lại nhưng không diễn giải. `SAMPLE_COUNT` phải bằng 1 (mục 10).
- **R2:** bit 0/1/5 ở packet **trước hoặc sau** chỗ nhảy đều được chấp nhận làm
  lời giải thích.
- **R3:** bit 1 (tràn bộ đệm MCU) giải thích một bước nhảy index khi `SEQ` liên
  tục, với giả định `SEQ` được gán lúc gửi.
- **R4:** `VERSION` được kiểm trước CRC; CRC16 little-endian; `SAMPLE_COUNT = 0`
  là vô lý.
- **R5:** dung sai ở `configs/hardware/packet_logger.json`, kể cả dung sai tốc độ
  ±3 % (thêm 2026-10-22).
- **R6 (2026-10-22):** chuỗi chỉ số/thời gian (`chain_id`) đánh số từ 0 trong
  từng phiên và kênh, tăng 1 khi neo lại (bit 5) hoặc khi `FS_NOMINAL_MHZ` đổi.
  Phiên mới luôn bắt đầu chuỗi 0 của phiên đó. Packet `FS_NOMINAL_MHZ = 0` bị cách
  ly (`fs_invalid`) và không cắt chuỗi.

## Lệch kênh: chỉ có nghĩa trong mô phỏng

Trên thiết bị, ECG và PPG đi qua hai AFE có độ trễ hiệu dụng `L` khác nhau và
chưa đo. Logger không thể biết lệch kênh từ packet, nên với `DEVICE`, giá trị
`offset_vs_ecg_us` là `null` kèm lý do. Offset thật được đo bằng kích thích
chung theo kế hoạch đo 10 phút.

Với `SYNTHETIC`, generator khai báo `common_index_epoch: true` (mẫu 0 của mọi
kênh cùng thời điểm). Logger ước lượng epoch của mỗi kênh là `T_ANCHOR_US` của
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
  thanh ghi AFE theo mục 11, ví dụ `ECG_RATE`, `LED_PW`);
- `simulation` (chỉ cho SYNTHETIC, `null` với DEVICE);
- `null_reasons`.

Mọi trường `null` (trừ `simulation`) phải có lý do trong `null_reasons`, với
khóa là đường dẫn như `channels.0xE1.latency_l_us`. Lý do cho trường không null
bị từ chối. Generator v3 tự ghi `session_metadata.json`. Với thiết bị, người vận
hành điền tay trước phiên; không có giá trị thì để `null` kèm lý do, không đoán.

## Đầu ra

`record` ghi các file sau (manifest **sau cùng**; thiếu manifest nghĩa là phiên
chưa hoàn tất, giữ nguyên `raw.bin` dở để kiểm tra, không xóa):

| File | Nội dung |
| --- | --- |
| `raw.bin` | Đúng từng byte đã nhận, kể cả byte lỗi; mở `xb`, `fsync` cuối phiên |
| `rx_chunks.csv` | Mỗi lần đọc: offset trong luồng, số byte, `t_rx_monotonic_ns` của PC |
| `t_rx_packets.csv` | `t_rx` của từng packet (theo lần đọc chứa byte cuối). Chỉ dùng chẩn đoán đường truyền, **không bao giờ** là thời gian mẫu |
| `decode.json` | Lỗi decode, `sync_candidates_rejected`, issue, `issue_counts`, tóm tắt từng phiên/kênh (kể cả số chuỗi `chains`), `gaps`, sự kiện, offset (chỉ SYNTHETIC), giới hạn |
| `packets.csv` | Mỗi packet đã giải mã theo thứ tự đến: trường header, `seq_ext`, `sample_index_ext`, `chain_id`, `disposition`. `chain_id` để trống với bản trùng, xung đột và packet `0xC1` |
| `samples.csv` | Mẫu của packet được nhận: phiên, kênh, `chain_id`, `seq_ext`, `sample_index_ext`, giá trị. Sắp theo (phiên, kênh, `chain_id`, `sample_index_ext`); khóa này là duy nhất, còn `sample_index_ext` có thể lặp giữa hai chuỗi khi neo lại lùi. Không có cột thời gian |
| `logger_config.json`, `session_metadata.json` | Bản sao đầu vào |
| `session_manifest.json` | Trường mục 11 (`schema_version` `packet-v0.1`, `session_id`/`session_ids`, `clock_id`, firmware, thiết bị, giờ PC lúc bắt đầu/kết thúc, metadata kênh, `null_reasons`); SHA-256 raw và mọi output; `issue_counts`; hash config/metadata; git commit/dirty, hash code (LF), Python; `source_type` |

Trong `record`, decode chạy trực tiếp theo từng đoạn đọc. Sau đó `raw.bin` được
đọc lại từ đĩa và decode lần nữa. Hai kết quả phải giống từng byte, nếu không thì
dừng (`live_equals_offline_decode`). `replay` ghi `decode.json`, `packets.csv`,
`samples.csv` và `replay_report.json`. Với `--expect`, hash raw, ba output decode
và hash config/metadata được so với manifest.

## Giới hạn

- Chưa chạy với MCU thật hay cổng serial; chưa có dữ liệu `DEVICE`.
- Không phát hiện được packet mất trước `SEQ` đầu tiên hoặc sau `SEQ` cuối cùng
  đã nhận, vì giá trị `SEQ` khởi đầu chưa được quy định (D5).
- `T_ANCHOR_US` được kiểm xuôi và ngược, rồi giữ chiều cách ly ít packet hơn. Vì
  vậy một anchor sai ở đầu chuỗi, ở cuối chuỗi, hoặc ngay sau khoảng mất (khi dung
  sai đã nới theo Δk) chỉ làm mất packet đó. Hai trường hợp vẫn khó:
  - Một bước nhảy thời gian kéo dài làm **phía ngắn hơn** của chuỗi bị cách ly.
    Logger không biết phía nào đúng, nên đây là quy ước số đông. Issue
    `timestamp_anomaly` vẫn lộ rõ, và người xem phải kiểm tra raw.
  - Nếu cả anchor đầu lẫn anchor cuối của một chuỗi đều sai, hai chiều cách ly
    bằng nhau. Chiều xuôi được giữ, nên các packet **đúng** ở giữa bị cách ly
    (ECG 8 packet, đầu và cuối cùng +20 ms: cách ly SEQ 1–6).
- Dung sai tốc độ ±3 % là giả định chưa đo (xem dung sai mặc định). Một bước nhảy
  thời gian nhỏ hơn dung sai đã nới sau một khoảng mất dài không bị phát hiện.
- Toàn bộ packet được giữ trong RAM tới cuối phiên. 10 phút (khoảng 5·10⁴ packet)
  không có vấn đề; phiên rất dài sẽ cần ghi theo dòng.
- Chỉ dùng thư viện chuẩn; chưa có hiệu chỉnh `L`, fs thật hay drift.

## Câu hỏi cho Đức Anh

- **D1.** Byte order của CRC16: little-endian như các trường khác (đang giả định)
  hay big-endian?
- **D2.** Firmware có lúc nào gửi `VERSION` khác `0x01` trên cùng cổng không? Đổi
  layout thì có tăng `VERSION` (mục 2) không?
- **D3.** Bit 0/5 bật ở packet nào so với khoảng mất (packet đọc lúc phát hiện
  tràn hay packet đã neo lại)? `SEQ` được gán trước hay sau bộ đệm MCU (bit 1)?
- **D4.** Bit 4 bật từ khi nào và tắt khi nào (theo từng cấu hình sau bench)?
  Có bật cho `0xC1` không?
- **D5.** `SEQ` và `FIRST_SAMPLE_INDEX` có bắt đầu từ 0 ở mỗi phiên không?
- **D6.** Packet `0xC1`: gửi giá trị gì cho `FIRST_SAMPLE_INDEX`, `FS_NOMINAL_MHZ`,
  `T_FIRST_US`? `SEQ` của `0xC1` có đếm riêng không? (mục 15)
- **D7.** Có khi nào `SAMPLE_COUNT = 0` (đọc FIFO rỗng) không? Có gửi packet đó không?
- **D8.** Sau bench: `d_ptr_us`/`d_word_us` đo được để chốt dung sai `T_ANCHOR_US`.
- **D9.** USB CDC: baud, kích thước buffer; có log text nào đi chung cổng packet không (mục 13)?
- **D10 (thêm 2026-10-22).** Tốc độ lấy mẫu thật của PPG (và ECG) lệch bao nhiêu so
  với `FS_NOMINAL_MHZ` trên board? Logger đang giả định ±3 %
  (`anchor_rate_tolerance_ppm` = 30 000), suy từ clock ADC MAX30101
  10,2–10,8 MHz ở mục 4. Phép đo 10 phút có cho số này không?

## Danh sách để Đức Anh review logger theo spec

- [ ] `HEADER = struct.Struct("<2sBBIIIQQIHH")` và vị trí DATA/CRC khớp struct firmware.
- [ ] CRC: known answer `0x29B1` cho `"123456789"`; packet ví dụ 50 byte trong
      `tests/fixtures/packet_v3_expected.json` giống từng byte với firmware.
- [ ] Mã kênh (mục 7) và tên bit STATUS (mục 9) trong `packet_wire.py`.
- [ ] Quy tắc tạm R1–R6: đồng ý hoặc sửa.
- [ ] Dung sai mặc định phù hợp cấu hình dự kiến (ECG 512 sps, N = 16), kể cả
      dung sai tốc độ ±3 % (D10).
- [ ] Trường metadata phiên đủ cho mục 11, nhất là danh sách thanh ghi trong `afe_config`.
- [ ] Khi có firmware khung và `pyserial` được duyệt: chạy 10 phút không tải,
      `SEQ` và `T_ANCHOR_US` tăng đơn điệu, lưu raw + manifest, ghi rõ là dữ liệu
      thiết bị, không đo trên người.
