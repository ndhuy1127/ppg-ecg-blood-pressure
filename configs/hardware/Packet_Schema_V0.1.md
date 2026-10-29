# Packet Schema V0.1 – ECG/PPG Data Acquisition

> **Datasheet đã đối chiếu** (trích dẫn dạng "MAX30001 tr. 26, Bảng 4"):
> MAX30001 Rev 3 (1/23), MAX30101 Rev 3 (6/20), MAX30102 Rev 1 (10/18). Danh
> sách tại `hardware/datasheets/README.md`.

## 1. Mục đích

Quy định dữ liệu ESP32-S3 gửi về PC khi thu ECG/PPG trên thiết bị V1 (PCB
V1-module; bench V0 đã bỏ ngày 2026-10-24). Mục tiêu:

- truyền ổn định;
- phát hiện mất, trùng, đảo thứ tự packet và mất mẫu bên trong AFE;
- giữ đủ thông tin thời gian để dựng lại thời điểm từng mẫu và kiểm tra đồng bộ;
- giữ raw data cho tiền xử lý và dataset.

## 2. Phiên bản

- Chuỗi version của tài liệu: **V0.1**. Trong packet, trường `VERSION = 0x01`.
- Layout byte ở mục 6 là layout đầu tiên của V0.1, khóa ngày 2026-10-23: firmware
  khung (`firmware/`), logger (`software/data_io/packet_wire.py`) và mô phỏng
  `synthetic-packet-v3` đều dùng nó. Bản nháp đầu của schema (trường không có
  layout byte, `HEADER` 0xE1/0xF1, file docx metadata ghi "V1") được thay thế; chưa
  thiết bị nào gửi theo bản nháp đó, nên không đặt version riêng cho nó.
- Đổi layout byte hoặc ý nghĩa trường thì tăng version: V0.1 → V0.2 → V1.0.
  Receiver phải từ chối version không hỗ trợ, không tự đoán.

## 3. Ba mốc thời gian khác nhau

| Ký hiệu | Ý nghĩa | Ở đâu |
| --- | --- | --- |
| `t_sample[i]` | Thời điểm AFE lấy mẫu i. Không đo trực tiếp được; phải ước lượng | Suy ra từ packet |
| `T_ANCHOR_US` | Thời điểm MCU đọc `esp_timer` ngay sau khi **chốt số mẫu** sẽ đọc từ FIFO (mục 5) | Trong packet |
| `t_rx` | Thời điểm PC nhận packet | Do PC ghi riêng, **không** nằm trong packet |

`t_rx` chỉ dùng chẩn đoán đường truyền, không bao giờ dùng làm thời gian mẫu.
Thời điểm ngắt (IRQ) cũng không phải thời điểm mẫu: giữa lúc AFE lấy mẫu và lúc
MCU đọc có độ trễ ngưỡng FIFO, độ trễ phục vụ ngắt và độ trễ xử lý trong AFE.

## 4. Clock

- Clock duy nhất của packet: `esp_timer` của ESP32-S3, đơn vị µs, 64 bit, mốc 0 là
  lúc MCU khởi động (`clock_id = "ESP32_ESP_TIMER_US"`).
- **MAX30001:** lấy mẫu theo FCLK 32,768 kHz ngoài (MAX30001 tr. 19, chân FCLK).
  Chế độ 500/250/125 sps dùng FMSTR = FCLK × 625/640 (tr. 27, Bảng 6), tức vẫn
  từ cùng dao động. Trên breakout, FCLK lấy từ dao động 32,768 kHz gắn sẵn.
- **MAX30101/MAX30102:** dùng dao động nội (MAX30101 tr. 10, sơ đồ chức năng).
  Datasheet cho clock ADC 10,2–10,8 MHz ở MAX30101 (tr. 3) và 10,32–10,64 MHz ở
  MAX30102 (tr. 3), nhưng không nêu sai số của tốc độ lấy mẫu. Vì vậy phải coi
  tốc độ PPG thực là chưa biết cho tới khi đo.
- Hai AFE không chung clock, nên drift giữa hai kênh là chắc chắn có; độ lớn phải
  đo theo `hardware/test_reports/sync_10min_test_plan.md`.
- Khi MCU khởi động lại, clock về 0 và phiên mới bắt đầu (`SESSION_ID` mới).

## 5. Chốt số mẫu, neo thời gian và thời điểm từng mẫu

Nguyên tắc: firmware **chốt trước** số mẫu N sẽ đọc, ghi `T_ANCHOR_US` ngay sau
khi chốt, rồi đọc **đúng N mẫu**. Mẫu đến trong lúc đọc nằm lại FIFO cho packet
sau. Nhờ vậy mẫu cuối của packet (`DATA[N−1]`) chắc chắn được tạo **trước**
`T_ANCHOR_US`.

### 5.1. MAX30101 / MAX30102 (I²C)

1. Đọc một lượt (burst, địa chỉ tự tăng) các thanh ghi `FIFO_WR_PTR` (0x04),
   `OVF_COUNTER` (0x05), `FIFO_RD_PTR` (0x06). Ghi `T_ANCHOR_US` ngay khi lượt đọc
   kết thúc. `OVF_COUNTER` phải đọc **trước** khi lấy dữ liệu, vì nó bị xóa về 0
   khi một mẫu được lấy ra khỏi FIFO (MAX30102 tr. 13; MAX30101 tr. 14).
2. `N = (FIFO_WR_PTR − FIFO_RD_PTR) mod 32` (MAX30102 tr. 16, mã giả). Con trỏ
   5 bit nên FIFO **đầy** và **rỗng** đều cho `WR = RD`. Nếu `WR = RD` mà
   `OVF_COUNTER > 0` thì FIFO đầy, `N = 32`. Đặt `FIFO_A_FULL` (MAX30102 tr. 17)
   để ngắt xảy ra khi FIFO còn nhiều chỗ trống, tránh vùng không phân biệt được.
3. Đọc đúng N mẫu; mỗi mẫu gồm 3 byte × số khe LED đang bật (MAX30102 tr. 14).

Giới hạn sai số: mẫu thứ N đã được ghi trước lúc đọc `FIFO_WR_PTR`, còn mẫu kế
tiếp chưa được ghi khi bắt đầu lượt đọc. Do đó
`0 ≤ δ < 10⁶/fs + d_ptr_us`, với `d_ptr_us` là thời gian lượt đọc con trỏ trên
I²C (cỡ 0,1–0,2 ms ở 400 kHz; phải đo).

V1 (chốt 2026-10-24; chi tiết Packet Schema V0.2 mục 7.6): `PPG_RDY` giữ chân INT ở
mức thấp tới khi đọc `Interrupt Status 1` (0x00), nên firmware đọc 0x00 sau mỗi ngắt
để xóa cờ rồi đọc con trỏ FIFO; khi có 8 mẫu đang chờ thì chốt con trỏ và đọc **hết**
số mẫu có trong FIFO lúc chốt (thường 8, tức 25 packet/s mỗi khe ở 200 sps), không cố
định 8. Vì đọc ngay
sau mẫu thứ 8, `δ` thực tế chỉ còn cỡ độ trễ ngắt cộng `d_ptr_us`. `FIFO_A_FULL`
không dùng để kích đọc (chỉ ngắt được khi có 17–32 mẫu chưa đọc). `PPG_RDY` ở chế độ
ba khe phải kiểm khi bring-up; không chạy thì đọc theo timer.

### 5.2. MAX30001 (SPI)

MAX30001 **không** có thanh ghi đếm số mẫu trong FIFO ECG (bản đồ thanh ghi
tr. 38–40). Trạng thái FIFO đi kèm từng word qua ETAG (tr. 65, Bảng 48).

1. Khi INTB báo `EINT` (có ít nhất `EFIT[4:0] + 1` mẫu chưa đọc; tr. 41, tr. 44),
   đọc burst `ECG_FIFO_BURST` (0x20) cho tới word có ETAG = `010` hoặc `011`
   (EOF: mẫu cuối hiện có trong FIFO).
2. Ghi `T_ANCHOR_US` ngay khi nhận xong word EOF. Word EOF là mẫu mới nhất tại lúc
   chip cập nhật con trỏ đọc của nó (cạnh SCLK thứ 30 + n × 24, tr. 36), nên
   `0 ≤ δ < 10⁶/fs + d_word_us`, với `d_word_us` là thời gian truyền một word 24 bit
   (khoảng 6 µs ở SCLK 4 MHz; tối đa SCLK 12 MHz, tr. 10).
3. Word ETAG `110` (FIFO rỗng) không phải bước thời gian: bỏ, không đưa vào packet.
   Word ETAG `001`/`011` (fast recovery) vẫn là bước thời gian hợp lệ nhưng điện áp
   không hợp lệ: giữ nguyên (mục 8). ETAG `111` (tràn): xem mục 9.

**Phương án neo tốt hơn (chốt dùng từ V0.2 ngày 2026-10-24, Packet Schema V0.2 mục 7):** MAX30001 phát xung `SAMP` ở tốc độ
dữ liệu ECG (tr. 42), mỗi 1/2/4/16 mẫu tùy `SAMP_IT` (tr. 44), đưa ra chân INT2B
qua `EN_INT2`. Xung này **không** đánh dấu lúc lấy mẫu analog. Theo ghi chú ứng
dụng của ADI cho MAX30003 (cùng kênh ECG; ghi chú nói MAX30001 cũng dùng được),
cạnh xuống của xung đến ngay sau khi mẫu được ghi vào FIFO (khoảng 30 µs) và trước
khi cờ FIFO bật (15 µs). Thời điểm lấy mẫu analog sớm hơn cạnh đó một khoảng
`t_ECG_DELAY` cố định theo cấu hình: ở 512 sps là 20,839 ms khi bỏ qua DLPF và
32,558 ms khi DLPF 40 Hz, độ lệch chuẩn đo được khoảng 3–4 µs. Con số này gồm độ
trễ bộ lọc số ở bảng của datasheet (mục 5.3) cộng **1,003 ms** trễ lấy mẫu ADC
(1,020 ms nếu FMSTR 32 000 Hz). Dù vậy, chụp `esp_timer` tại cạnh xung vẫn cho
mỗi mẫu một mốc trên clock MCU với jitter rất nhỏ, không phụ thuộc độ trễ đọc
FIFO. Chưa kiểm trên MAX30001; phép đo đồng bộ 10 phút
(`hardware/test_reports/sync_10min_test_plan.md`) phải xác nhận độ trễ này. KiCad
V1-module, pin map chuẩn của V1, nối INT2B vào GPIO47
(`configs/hardware/custom_board_proposal.md` mục A.6, A.7). Từ V0.2 (chốt
2026-10-24): firmware bật `SAMP` luôn và dùng làm mốc ECG (Packet Schema V0.2 mục 7);
bản cuối cũng phải nối INT2B. Firmware V0.1 không dùng `SAMP`.

### 5.3. Thời điểm từng mẫu

Mọi thời gian tính bằng µs, `fs` tính bằng Hz (sps). Với i = 0 … N−1:

```text
t_sample_us[i] = t_last_us − (N − 1 − i) · 10⁶ / fs
t_last_us      = T_ANCHOR_US − δ − d_pipe_us
```

- `δ`: khoảng chưa biết trong giới hạn ở mục 5.1/5.2.
- `d_pipe_us`: độ trễ cố định trong AFE.
  - MAX30001: tr. 26, Bảng 4 cho độ trễ ECG theo tốc độ dữ liệu, ví dụ 512 sps:
    19,836 ms không LPF / 31,555 ms có LPF; 500 sps: 20,313 / 32,313 ms;
    128 sps: 102,844 / 149,719 ms; 125 sps: 105,313 / 153,313 ms. Bảng này chỉ là
    độ trễ bộ lọc số; ghi chú ADI cho MAX30003 (mục 5.2) đo thêm khoảng 1,0 ms trễ
    lấy mẫu ADC (512 sps: 20,839 / 32,558 ms tính tới lúc mẫu vào FIFO). Dùng
    `L_ECG` đo trong phép đo đồng bộ 10 phút, không dùng thẳng bảng datasheet.
  - MAX3010x: datasheet không cho độ trễ. Khi bật `SMP_AVE`, chip lấy trung bình
    N mẫu liền kề rồi giảm tốc độ (MAX30102 tr. 17, Bảng 3); độ trễ thêm ước lượng
    khoảng (N−1)/2 chu kỳ lấy mẫu gốc, **phải đo**.

Trên thực tế không tách riêng được `δ` và `d_pipe` cho từng packet. Phép đo đồng bộ
10 phút (`hardware/test_reports/sync_10min_test_plan.md`) cho **độ trễ hiệu dụng**
`L_us = d_pipe_us + E[δ]` của từng kênh và cấu hình. Khi phân tích, tính thời điểm
tạm với `δ = d_pipe = 0` rồi trừ `L_us`; phần dao động còn lại của `δ` là jitter.

**Ước lượng tốc độ thực (offline, trên PC):** với `k` là chỉ số tích lũy của mẫu
cuối mỗi packet (`FIRST_SAMPLE_INDEX + N − 1`), hồi quy tuyến tính

```text
T_ANCHOR_US(k) = a_us + b_us · k
fs_thực        = 10⁶ / b_us
```

`b_us` có đơn vị µs/mẫu; ví dụ 200 Hz cho `b_us ≈ 5 000`. Phần dư của hồi quy là
jitter của mốc neo. Dùng `fs_thực` thay `fs` danh định khi dựng thời gian bản ghi
dài, vì sai số danh định tích lũy theo chỉ số mẫu.

**Packet có bit 0 (FIFO AFE tràn):** FIFO đã đầy trước lúc đọc, nên mẫu cuối cũ
hơn `T_ANCHOR_US` một khoảng chưa biết (cỡ số mẫu mất × chu kỳ). Không dùng anchor
của packet đó trong hồi quy trên và không lấy nó làm mốc; mẫu của nó vẫn hợp lệ
(PPG) và lấy thời điểm theo hồi quy của các packet khác trong cùng chuỗi. Logger
`packet-logger-v1` làm đúng như vậy (chốt 2026-10-23, `docs/protocol/packet_logger.md`).
Packet nhận bit 0 do chuyển tiếp từ packet bị mất (mục 9) cũng bị bỏ anchor như
vậy; đó chỉ là mất một mốc, không mất mẫu.

`T_FIRST_US` trong packet là ước lượng tiện dụng của firmware:
`T_ANCHOR_US − (N − 1) · 10⁶ / fs_danh_định`, **chưa** trừ `δ` và `d_pipe`. Phân
tích PAT phải tính lại theo các công thức trên.

## 6. Layout byte (little-endian)

Mỗi kênh có packet riêng; không giả định 1 mẫu ECG = 1 mẫu PPG.

| Offset | Kích thước | Trường | Kiểu | Ý nghĩa |
| ---: | ---: | --- | --- | --- |
| 0 | 2 | `SYNC` | 2 × uint8 | `0xA5 0x5A`, để bắt lại đầu packet khi mất byte trên USB |
| 2 | 1 | `VERSION` | uint8 | `0x01` = V0.1 |
| 3 | 1 | `CHANNEL_ID` | uint8 | Mục 7 (giữ `0xE1` ECG, `0xF1` PPG của bản gốc) |
| 4 | 4 | `SESSION_ID` | uint32 | Một phiên thu; đổi khi MCU khởi động lại |
| 8 | 4 | `SEQ` | uint32 | Số thứ tự packet **riêng từng kênh**, +1 mỗi packet |
| 12 | 4 | `FIRST_SAMPLE_INDEX` | uint32 | Chỉ số tích lũy (từ đầu phiên) của `DATA[0]` trong kênh này |
| 16 | 8 | `T_ANCHOR_US` | uint64 | Mục 3, 5 |
| 24 | 8 | `T_FIRST_US` | uint64 | Mục 5.3 (ước lượng firmware) |
| 32 | 4 | `FS_NOMINAL_MHZ` | uint32 | Tốc độ danh định, đơn vị mHz (millihertz), **không phải** MHz: 512 000 = 512 Hz |
| 36 | 2 | `SAMPLE_COUNT` | uint16 | N; `DATA[0] … DATA[N−1]` |
| 38 | 2 | `STATUS` | uint16 | Mục 9 |
| 40 | 4·N | `DATA[]` | int32[N] | Mục 8 |
| 40 + 4·N | 2 | `CRC16` | uint16 | CRC-16/CCITT-FALSE trên byte 2 … 39 + 4·N |

Ví dụ ECG N = 16: 106 byte/packet. Ở 512 sps là 32 packet/s, khoảng 3,4 kB/s.

## 7. Mã kênh và khe LED

| `CHANNEL_ID` | Kênh |
| --- | --- |
| `0xE1` | ECG (MAX30001) |
| `0xF1` | PPG khe 1 (`SLOT1`) |
| `0xF2` | PPG khe 2 (`SLOT2`) |
| `0xF3` | PPG khe 3 (`SLOT3`) |
| `0xF4` | PPG khe 4 (`SLOT4`) |
| `0xC1` | Sự kiện (mục 10) |

Phân biệt **số khe** và **loại LED**:

- **Số khe:** ở multi-LED mode, mỗi mẫu chia tối đa bốn khe `SLOT1`–`SLOT4` ở
  **cả** MAX30101 (tr. 20–21, Bảng 9) và MAX30102 (tr. 21, Bảng 9). Các khe phải
  bật theo thứ tự (không tắt `SLOT1` khi `SLOT2` bật).
- **Loại LED mỗi khe:** MAX30102 chỉ chọn được đỏ (`001`) hoặc IR (`010`).
  MAX30101 chọn thêm được xanh (`011`, LED3 + LED4).
- **Chế độ khác:** Heart Rate mode chỉ dùng LED đỏ (một kênh); SpO2 mode dùng đỏ
  và IR (hai kênh) (MAX30102 tr. 18, Bảng 4; MAX30101 tr. 19, Bảng 4). Trong hai
  chế độ này, thứ tự kênh trong FIFO là đỏ rồi IR (MAX30102 tr. 15, Hình 2), và
  receiver dùng `0xF1` cho đỏ, `0xF2` cho IR.

Ánh xạ khe → LED ghi trong metadata phiên. V1 (chốt 2026-10-24): `SLOT1` xanh (`0xF1`), `SLOT2` đỏ (`0xF2`), `SLOT3` IR (`0xF3`), 200 sps mỗi khe, `SMP_AVE = 1`. Các khe của cùng một mẫu PPG có chung
`FIRST_SAMPLE_INDEX` và `T_ANCHOR_US`, nhưng **không** cùng thời điểm phát LED:
khoảng cách cạnh lên giữa hai khe liên tiếp là 427 / 525 / 720 / 1 107 µs với độ
rộng xung 69 / 118 / 215 / 411 µs (MAX30102 tr. 25, Bảng 14; MAX30101 tr. 22,
Bảng 11). Khe thứ j lệch khoảng (j−1) lần giá trị này so với khe 1.

**Quy ước offset giữa các khe (chốt 2026-10-29; trước đó còn mở):**

- Raw giữ nguyên. Packet, logger và `samples.csv` không cộng độ lệch: ba khe chung
  `FIRST_SAMPLE_INDEX` và `T_ANCHOR_US`, `samples.csv` chỉ có chỉ số mẫu (sửa
  2026-10-25: bản trước ghi receiver đã cộng).
- Phân tích offline lấy khe 1 làm gốc. Mốc thời gian dựng theo mục 5.3 là mốc của
  khe 1; mẫu ở khe j có mốc đó cộng (j − 1) · Δ(PW).
- Δ(PW) là khoảng cách cạnh lên giữa hai khe liên tiếp, suy từ độ rộng xung
  (`LED_PW`) trong `SPO2_CONFIG` của packet `0xD2` của MAX30101 trong phiên
  (Packet Schema V0.2 mục 12), không lấy từ metadata gõ tay hay từ mặc định của
  firmware. Phiên không có `0xD2` hợp lệ của MAX30101 thì không cộng được: ghi là
  thiếu, không đoán.
- Giá trị Δ phụ thuộc độ rộng xung, mà độ rộng xung (411 hay 215 µs) còn chờ
  bring-up. Danh định: 1 107 µs với 411 µs, 720 µs với 215 µs
  ([custom_board_proposal.md](custom_board_proposal.md) A.6 mục 3, bảng trên).
- Quy ước gắn với version của feature hay config dùng thời gian theo khe: ghi
  version đó cùng kết quả; đổi gốc, công thức hay nguồn của Δ là đổi version.

## 8. Dữ liệu và đơn vị

- **ECG:** `DATA[i]` là **nguyên word 24 bit** đọc từ FIFO ECG (bit 23…0, mở rộng
  không dấu thành int32), để giữ cờ từng mẫu. Theo MAX30001 tr. 64, Bảng 47:
  bit 23…6 là mẫu ECG 18 bit bù hai căn trái, bit 5…3 là ETAG, bit 2…0 là PTAG.
  Receiver tách giá trị 18 bit có dấu rồi đổi đơn vị theo tr. 65:
  `V_ECG (mV) = ADC × VREF / (2¹⁷ × ECG_GAIN)`, với `VREF` khoảng 1 000 mV
  (0,995–1,005 V, tr. 8) và `ECG_GAIN` ∈ {20, 40, 80, 160} V/V (tr. 53). Mẫu có
  ETAG `001`/`011` (fast recovery) vẫn là bước thời gian hợp lệ nhưng điện áp
  không hợp lệ (tr. 65, Bảng 48).
- **PPG:** mỗi khe 3 byte, dữ liệu 18 bit căn trái `FIFO_DATA[17:0]`, bit 23…18
  không dùng (MAX30102 tr. 14–15, Bảng 1–2). `DATA[i]` là giá trị 18 bit không
  dấu. Độ phân giải thực 15–18 bit theo `LED_PW` (tr. 19, Bảng 7). Đơn vị là số
  đếm ADC; 1 LSB = 7,81 / 15,63 / 31,25 / 62,5 pA theo `SPO2_ADC_RGE` (tr. 18,
  Bảng 5). Giá trị phụ thuộc dòng LED, độ rộng xung và dải ADC, nên các tham số
  này phải ghi vào metadata phiên.
- Thứ tự `DATA[i]` tăng theo thời gian lấy mẫu.

## 9. STATUS và xử lý mất mẫu

| Bit | Ý nghĩa |
| ---: | --- |
| 0 | FIFO của AFE tràn trước khi đọc: đã mất mẫu bên trong AFE |
| 1 | Bộ đệm phía MCU tràn: có packet bị bỏ trước khi gửi |
| 2 | ECG lead-off (`DCLOFFINT`, MAX30001 tr. 41) |
| 3 | Lỗi cấu hình hoặc giao tiếp AFE (ví dụ đọc lại thanh ghi không khớp, con trỏ FIFO bất thường) |
| 4 | Độ trễ hiệu dụng `L` của cấu hình hiện tại chưa được đo (bật cho tới khi có kết quả phép đo đồng bộ 10 phút) |
| 5 | Đếm lại sau khoảng mất mẫu **không biết chính xác độ dài**: `FIRST_SAMPLE_INDEX` được neo lại |
| 6 | PPG: tràn khử ánh sáng môi trường (`ALC_OVF`, MAX30102 tr. 12) |
| 7–15 | Dự trữ, gửi 0 |

**MAX30101/MAX30102:**

- Khi FIFO đầy, mẫu mới không được ghi và bị mất; `OVF_COUNTER` đếm số mẫu mất,
  **bão hòa ở 31** (0x1F) và bị xóa khi lấy mẫu ra (MAX30102 tr. 13).
- Đề xuất đặt `FIFO_ROLLOVER_EN = 0`. Khi đó FIFO đầy thì không cập nhật cho tới
  khi được đọc (MAX30102 tr. 17), nên các mẫu còn trong FIFO liên tục, và khoảng
  mất nằm **sau** mẫu cuối của packet này, **trước** mẫu đầu của packet sau. Với
  `FIFO_ROLLOVER_EN = 1`, datasheet chỉ nói FIFO quay vòng và tiếp tục ghi dữ liệu
  mới, không nói rõ vị trí khoảng mất; vì vậy không dùng chế độ này.
- Nếu `0 < OVF_COUNTER < 31`: bật bit 0; packet sau có
  `FIRST_SAMPLE_INDEX = chỉ số mẫu cuối + 1 + OVF_COUNTER`.
- Nếu `OVF_COUNTER = 31`: số mẫu mất ≥ 31, không biết chính xác; bật bit 0 và
  bit 5, neo lại chỉ số theo `T_ANCHOR_US` và tốc độ đã ước lượng.

**MAX30001:**

- Tràn FIFO ECG làm hỏng dữ liệu và mất mẫu cùng thông tin thời gian (tr. 64);
  chip không báo số mẫu mất. Khi gặp ETAG `111` hoặc cờ `EOVF` (tr. 41): bật bit 0
  và bit 5, gửi lệnh `FIFO_RST` (0x0A) để tiếp tục (tr. 46), neo lại chỉ số.
- Mọi lần đổi `CNFG_GEN`/`CNFG_ECG` có thể làm gián đoạn bản ghi; datasheet khuyến
  nghị lệnh `SYNCH` (0x09) để khởi động lại sạch (tr. 46–47, tr. 52). Sau `SYNCH`,
  bắt đầu chuỗi chỉ số mới và bật bit 5.

**Bộ đệm MCU (bit 1):** `SEQ` được gán **lúc gửi**, khi lấy packet ra khỏi hàng
đợi MCU (chốt 2026-10-23). Packet bị bỏ vì hàng đợi đầy không có `SEQ`; packet kế
tiếp của cùng kênh bật bit 1 và có `FIRST_SAMPLE_INDEX` nhảy trong khi `SEQ` liên
tục. Thiếu `SEQ` nghĩa là packet mất sau hàng đợi, trên đường USB. Nếu packet bị
bỏ ở hàng đợi hoặc firmware gửi thất bại (driver không nhận trong thời hạn) mà mang bit 0
hay bit 1, packet gửi được kế tiếp của kênh mang thêm các bit đó (2026-10-23), nên
khoảng mất vẫn được giải thích dù packet đánh dấu không tới. Mất sau khi driver đã
nhận packet thì firmware không biết và không chuyển bit.

## 10. Packet sự kiện

`CHANNEL_ID = 0xC1`, `SAMPLE_COUNT = 1`, `DATA[0]` là mã sự kiện, `T_ANCHOR_US`
là thời điểm MCU ghi nhận sự kiện (cạnh GPIO hoặc lệnh). Mã sự kiện:

| Mã | Sự kiện | Nguồn và mốc |
| ---: | --- | --- |
| `1` | Bắt đầu bơm cuff (`t0`) | Nút SW1 (GPIO4), cạnh xuống đầu tiên |
| `2` | Kết thúc đo cuff (`CUFF_END`) | Lệnh PC `MARK_EVENT` (Packet Schema V0.2 mục 13, chốt 2026-10-29); mốc là lúc thiết bị nhận lệnh, độ trễ PC → thiết bị chưa đo |
| `3` | Xung kích thích đồng bộ (phép đo 10 phút) | MCU tự phát trên GPIO6, `esp_timer` ngay sau cạnh lên |
| `4` | Người vận hành đánh dấu (`OPERATOR_MARK`) | Như mã 2 |

Mốc cần chính xác tới ms vẫn là `t0` (mã 1). Giá trị SBP/DBP của cuff được nhập ở
PC theo `event_id`, không đi trong packet.

Các trường còn lại (chốt 2026-10-23, [firmware/README.md](../../firmware/README.md)):

- `SEQ` đếm riêng cho kênh `0xC1`, bắt đầu từ 0 mỗi phiên.
- `FIRST_SAMPLE_INDEX` = số thứ tự sự kiện trong phiên (0, 1, …).
- `FS_NOMINAL_MHZ = 0`; `T_FIRST_US = T_ANCHOR_US`.
- `STATUS` bit 4 không bật (độ trễ AFE không áp dụng cho sự kiện); bit 1 bật ở
  packet sự kiện kế tiếp nếu một packet sự kiện bị bỏ do hàng đợi MCU đầy, hoặc
  nếu hàng đợi của ISR bỏ một cạnh nút trước khi lọc dội (cạnh đó không có số thứ
  tự; xem `firmware/README.md`, mục Nút t0).
- Receiver không kiểm bước 6 của mục 12 cho `0xC1`. Bước 4 áp cho số thứ tự sự
  kiện (sửa 2026-10-23, layout byte không đổi): giữa hai sự kiện nhận được, số thứ
  tự tăng bằng khoảng `SEQ` cộng số sự kiện bị bỏ trước khi có `SEQ`, để mất một
  mốc t0 luôn để lại issue ([packet_logger.md](../../docs/protocol/packet_logger.md), R1).

## 11. Metadata phiên (file JSON do PC ghi)

Bắt buộc: `schema_version` (`packet-v0.1`), `session_id`, `clock_id`, phiên bản và
commit firmware, mã thiết bị, ngày giờ PC lúc bắt đầu (chỉ để tham chiếu).

Với **mỗi kênh**: `CHANNEL_ID`, cảm biến, `fs` danh định, độ trễ hiệu dụng `L` và
nguồn của nó (datasheet hay phép đo đồng bộ 10 phút, kèm mã báo cáo), công thức đổi
đơn vị.

- ECG: `FMSTR`, `ECG_RATE`, `ECG_GAIN`, `ECG_DHPF`, `ECG_DLPF`, `EFIT`, `INTB_TYPE`,
  `SAMP_IT` nếu dùng INT2B.
- PPG: `MODE`, ánh xạ khe → LED, `SPO2_SR`, `LED_PW`, `SPO2_ADC_RGE`, `SMP_AVE`,
  `LEDx_PA`, `FIFO_ROLLOVER_EN`, `FIFO_A_FULL`.

Thêm loại điện cực, vị trí đặt, người vận hành. PC ghi kèm `t_rx` của từng packet
vào file riêng.

## 12. Receiver kiểm tra

1. `SYNC` đúng, `CRC16` đúng; sai thì bỏ packet và đếm lỗi CRC.
2. `VERSION` được hỗ trợ.
3. `SEQ` liên tục **theo từng kênh**: thiếu → mất packet; lặp cùng nội dung →
   trùng; nhỏ hơn giá trị đã nhận → đảo thứ tự. Mở rộng `SEQ` và
   `FIRST_SAMPLE_INDEX` qua mốc tràn 2³² (cả hai là uint32).
   `FIRST_SAMPLE_INDEX` tăng theo mẫu nên tràn sau 2³²/fs giây: ở 512 sps là
   khoảng 8,39·10⁶ s ≈ 97 ngày. `SEQ` tăng theo packet nên tràn sau 2³²·N/fs
   giây: ECG 512 sps, N = 16 (32 packet/s, mục 6) là khoảng 1,34·10⁸ s ≈ 1 553
   ngày.
4. `FIRST_SAMPLE_INDEX[k] = FIRST_SAMPLE_INDEX[k−1] + SAMPLE_COUNT[k−1]`; nếu
   không → khoảng mất mẫu, kể cả khi `SEQ` liên tục. Đối chiếu với `STATUS`.
5. `SAMPLE_COUNT` trong giới hạn (≤ 32 mẫu mỗi lần đọc FIFO); `STATUS` được ghi
   lại, không bỏ qua.
6. `T_ANCHOR_US` tăng và khớp với chỉ số mẫu / `fs` trong dung sai.
7. Không nội suy hay nối dữ liệu qua khoảng mất; đánh dấu khoảng trống.
8. Không ghép ECG–PPG theo chỉ số mẫu. Mọi căn chỉnh dùng clock MCU, hiệu chỉnh
   độ trễ hiệu dụng `L` và kết quả đo đồng bộ. **Không** dịch kênh để R-peak trùng
   chân PPG và không dùng PAT làm lệch clock.

## 13. Truyền USB/Serial

Thiết bị V1 dùng binary packet để thu raw data. Log dạng text chỉ để debug, đi cổng hoặc
file riêng, không trộn vào luồng packet.

## 14. Đối chiếu với mô phỏng `synthetic-packet-v2`

`software/data_io/packet_simulation.py` (Huy) là giao diện **giả lập** dạng JSON,
không phải decoder của schema này.

| Schema V0.1 | `synthetic-packet-v2` | Ghi chú |
| --- | --- | --- |
| `VERSION` | `schema_version` | Chuỗi khác nhau; cần bảng ánh xạ khi viết decoder |
| `CHANNEL_ID` 0xE1 / 0xF1–0xF4 | `channel` "ECG" / "PPG" | Mô phỏng chỉ có một kênh PPG |
| `SESSION_ID` | `session_id` | |
| — (metadata phiên) | `clock_id` | |
| `SEQ` uint32 | `sequence` int | Mô phỏng không xử lý tràn uint32 |
| `FIRST_SAMPLE_INDEX` | — | Mô phỏng chưa có |
| `T_FIRST_US` / `T_ANCHOR_US` | `timestamp_us` (`first_sample`) | Mô phỏng coi timestamp là thời điểm mẫu đầu chính xác |
| `FS_NOMINAL_MHZ` (mHz) | `fs_hz` (integer Hz) | Đơn vị khác nhau. Mô phỏng dùng PPG 128 Hz, không có trong bảng tốc độ MAX3010x (MAX30102 tr. 19, Bảng 6) |
| `SAMPLE_COUNT` uint16; mục 12 bước 5: ≤ 32 mẫu mỗi lần đọc FIFO, N đổi theo từng lần đọc (mục 5) | `sample_count` | Mô phỏng: cố định theo kênh trong config, mỗi packet phải bằng giá trị config; `validate_config` cho 1–4 096 và tổng ≤ 1 000 000 mẫu; config mặc định ECG 16, PPG 4. Giới hạn 4 096 lớn hơn giới hạn 32 của phần cứng |
| `STATUS`, `SYNC`, `CRC16` | — | Mô phỏng chưa có |
| `DATA` int32 (ECG giữ ETAG/PTAG) | `samples` int32, `sample_unit` | |

### 14.1. Đối chiếu với `synthetic-packet-v3` và logger `packet-logger-v0` (2026-10-21; v1 từ 2026-10-23)

`software/data_io/packet_simulation_v3.py` (Linh) sinh **luồng byte** theo đúng
mục 6. `software/data_io/packet_wire.py` và `packet_receiver.py` là decoder và
kiểm tra mục 12 của logger ([hướng dẫn](../../docs/protocol/packet_logger.md)).
v2 ở bảng trên giữ nguyên.

| Schema V0.1 | v3 / logger | Ghi chú |
| --- | --- | --- |
| `SYNC` `0xA5 0x5A` | Sinh đúng; decoder dò `SYNC`, lỗi thì bỏ 1 byte rồi dò tiếp | Case `byte_loss` kiểm bắt lại `SYNC` |
| `VERSION` `0x01` | Sinh `0x01`; decoder từ chối version khác **trước** khi kiểm CRC | Khác thứ tự liệt kê ở mục 12 (version lạ thì không biết độ dài). Case `version` |
| `CHANNEL_ID` | `0xE1`, `0xF1`, `0xF2`, `0xC1` trong config mặc định; decoder nhận `0xF1`–`0xF4` | Mã lạ có CRC đúng: báo `unknown_channel`, bỏ cả packet |
| `SESSION_ID` | uint32; đổi `SESSION_ID` = phiên mới, kiểm riêng, không nối | Case `session_restart` |
| `SEQ` uint32 | Riêng từng kênh, mở rộng qua 2³² | Test bắt đầu từ 2³² − 3 |
| `FIRST_SAMPLE_INDEX` uint32 | Có; mở rộng qua 2³²; kiểm liên tục, đối chiếu `STATUS` | Case `index_jump`, `reanchor` |
| `T_ANCHOR_US`, `T_FIRST_US` uint64 | Có; `T_FIRST_US` = `T_ANCHOR_US − (N−1)·T` làm tròn; logger chỉ kiểm `T_ANCHOR_US` | Dung sai trong `configs/hardware/packet_logger.json`, chưa kiểm chứng phần cứng |
| `FS_NOMINAL_MHZ` (mHz) | Có, đơn vị mHz; ECG 512 000, PPG 100 000 là **thông số mô phỏng** | PPG 100 Hz có trong bảng tốc độ MAX3010x; phần cứng V1 chốt PPG 200 sps (2026-10-24) |
| `SAMPLE_COUNT` ≤ 32 | Config 1–32; decoder từ chối 0 và > 32 | 0 bị coi là vô lý (câu hỏi D7 trong hướng dẫn logger) |
| `STATUS` (mục 9) | Bit 4 bật trên mọi packet ECG/PPG; `0xC1` gửi 0 như mục 10 và firmware (sửa 2026-10-23; trước đó `0xC1` cũng bật bit 4); bit 0/5 ở case lỗi; bit 7–15 = 0 | Logger đếm từng bit và báo bit dự trữ, không dựa vào bit 4 để kiểm |
| `DATA` int32 | ECG: word 24 bit, ETAG/PTAG = 0; PPG: 18 bit không dấu | Số ngẫu nhiên, không phải waveform |
| `CRC16` CCITT-FALSE | Có; đọc/ghi little-endian | Firmware cũng ghi little-endian (D1). Known-answer `0x29B1` |
| Packet `0xC1` (mục 10) | `SAMPLE_COUNT` 1, mã 1–4. `FIRST_SAMPLE_INDEX` = thứ tự sự kiện trong phiên (0, 1, …), `FS_NOMINAL_MHZ` = 0, `T_FIRST_US` = `T_ANCHOR_US` | Logger bỏ bước 6 cho `0xC1`; bước 4 kiểm số thứ tự sự kiện so với `SEQ` (từ 2026-10-23). Firmware gửi đúng các giá trị này (mục 10, D6) |
| Metadata phiên (mục 11) | `session_metadata.json` (`packet-session-metadata-v0`; từ 2026-10-29 là v1, thêm `subject_id`, `session_id`, `ppg_led_lock`, `cuff_log`: [packet_logger.md](../../docs/protocol/packet_logger.md)), trường chưa biết là `null` kèm lý do; manifest `schema_version` `packet-v0.1` | |
| `t_rx` (mục 3) | File riêng `rx_chunks.csv`, `t_rx_packets.csv`; không vào kết quả decode | |

## 15. Việc còn mở

- Độ rộng xung LED PPG: 411 hay 215 µs, chọn bằng số đo bring-up (V1 chốt
  multi-LED ba khe ở 200 sps, `SMP_AVE = 1`, 2026-10-24). Quy ước offset giữa các
  khe không còn mở (chốt 2026-10-29, mục 7); chỉ giá trị Δ còn chờ độ rộng xung.
- Độ trễ hiệu dụng `L` của từng cấu hình (đo theo kế hoạch đo 10 phút), kể cả
  khoảng 1,0 ms trễ lấy mẫu ADC của MAX30001 ngoài bảng datasheet (mục 5.2, 5.3).

- Câu hỏi D8 (`d_ptr_us`/`d_word_us`) và D10 (tốc độ mẫu thật lệch bao nhiêu so
  với danh định) trong `docs/protocol/packet_logger.md`: D8 chờ số đo khi bring-up
  trên PCB V1 (thử trên bàn, không người;
  `hardware/test_reports/v1_bringup_procedure.md` chưa có bước riêng); D10 chờ phép
  đo đồng bộ 10 phút (`hardware/test_reports/sync_10min_test_plan.md` mục 5, tốc độ
  thực `fs_c`).
