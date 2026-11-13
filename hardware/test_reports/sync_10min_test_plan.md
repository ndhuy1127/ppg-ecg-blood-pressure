# Kế hoạch đo đồng bộ ECG–PPG 10 phút (thử trên bàn với PCB V1, không người)

> Chưa thực hiện vì chưa có phần cứng.
>
> **Tiêu chí đạt/không đạt ở mục 9 đề xuất ngày 2026-11-11, duyệt ngày 2026-11-14**, viết trước khi
> có số đo nào. Bản trước ghi "chưa chốt, chỉ đặt sau khi có số đo đầu tiên"; đặt ngưỡng sau
> khi đã thấy số thì ngưỡng không còn kiểm được gì. Sau khi đo không đổi ngưỡng. Nếu buộc phải
> đổi thì ghi lý do, ngày, và báo kết quả theo cả ngưỡng cũ lẫn ngưỡng mới.

## 1. Mục tiêu

Trên thiết bị V1 (PCB V1-module) đã qua bring-up, đo trong 10 phút liên tục:

1. Tốc độ lấy mẫu **thực** của từng kênh so với tốc độ danh định.
2. Drift: tốc độ thực của mỗi kênh lệch bao nhiêu so với clock MCU, và hai kênh
   lệch nhau bao nhiêu theo thời gian.
3. Jitter của mốc đọc FIFO (`T_ANCHOR_US`).
4. Độ trễ hiệu dụng của từng kênh (gộp `d_pipe` và `δ` trong packet schema) và
   **lệch thời gian ECG–PPG** (offset) sau khi dựng lại thời điểm mẫu.
5. Tỷ lệ mất packet, mất mẫu bên trong AFE và lỗi CRC.

Kết quả dùng để hiệu chỉnh thời gian trước khi tính PAT. Phép đo này **không**
dùng PAT hay mốc sinh lý để suy ra lệch clock.

## 2. Điều kiện trước khi đo

- Bring-up đạt tới bước giao tiếp và thu được dữ liệu từ cả hai AFE
  ([v1_bringup_procedure.md](v1_bringup_procedure.md) mục 7–8).
- Firmware gửi packet có `FIRST_SAMPLE_INDEX`, `T_ANCHOR_US` và packet sự kiện
  `0xC1`. Phép đo `L_ECG,SAMP` cần firmware V0.2 có mốc `SAMP` (bit 8, Packet Schema
  V0.2 mục 7); lần đo với firmware V0.1 chỉ cho `L_ECG` của mốc đọc FIFO và ghi riêng.
- Cấu hình AFE (tốc độ, FMSTR, chế độ LED, lấy trung bình, bộ lọc) đã ghi vào
  metadata phiên. Mỗi cấu hình khác nhau là một lần đo riêng.
- **Độ rộng xung LED đã chốt** (thêm 2026-10-29) theo luật viết trước ở
  [interface_power_sampling_v0.md](../../configs/hardware/interface_power_sampling_v0.md)
  mục 6, từ số đo bring-up mục 8. Chưa chốt thì chưa đo: khoảng lệch giữa các khe PPG
  và `L_PPG` phụ thuộc độ rộng xung. `sync10` mặc định 411 µs; chọn 215 µs thì build
  với `-DBOARD_PPG_LED_PW_US=215` (mục 3). Kiểm `SPO2_CONFIG` trong `0xD2` của phiên
  khớp độ rộng xung đã chọn.
- **Cực tính `SAMP` đã kiểm** ở bring-up mục 7 bước 4, cùng việc xung `SAMP` đầu tiên
  ứng với mẫu đầu tiên của FIFO (mục 3).
- **Không gắn điện cực lên người.** Mọi đo đạc dùng tín hiệu nhân tạo.

## 3. Bố trí kích thích chung

Cần một sự kiện vật lý mà **cả hai kênh cùng thấy**, với thời điểm do chính MCU
ghi lại:

- GPIO6 của ESP32-S3, đưa ra header J3 (GPIO6, GND) trên bo đế (chốt 2026-10-24,
  `custom_board_proposal.md` A.2), phát xung vuông, chu kỳ 1 s, độ rộng khoảng
  50 ms.
  MCU gửi packet sự kiện mã `3` với `T_ANCHOR_US` tại cạnh lên.
- **Firmware (chốt 2026-10-25, chưa chạy trên chip):** bản build
  `pio run -d firmware -e esp32s3_devkitc_sync10` (ba chip thật, capture `SAMP` có
  bit 8 nhờ `BOARD_SAMP_VERIFIED=1`, xung bật bằng `BOARD_STIM=1`). Chỉ nạp bản này sau
  khi bring-up mục 7 đã xác nhận cạnh `SAMP` đầu tiên ứng với mẫu đầu tiên của FIFO;
  chưa xác nhận thì packet ECG mang bit 8 sai mốc (sửa 2026-10-25: bản trước thiếu cờ
  này nên không có bit 8, không đo được `L_ECG,SAMP`). Cạnh lên đầu tiên 2 s sau khi khởi động; các cạnh sau
  cách nhau 1 000 000 µs cộng độ lệch đều trong [0; 1 953) µs (`stim_plan.c`,
  xorshift32), lịch tính theo thời điểm đích nên độ trễ callback không cộng dồn;
  độ rộng 50 000 µs. `T_ANCHOR_US` của packet mã 3 là `esp_timer` đọc **ngay sau**
  khi đặt GPIO6 lên mức cao (sai số cỡ µs, gồm cả độ trễ ghi GPIO). Seed của dãy độ
  lệch là `SESSION_ID`, có trong mọi packet: mỗi lần khởi động một dãy mới, tái lập
  được. Số thứ tự sự kiện đếm chung với sự kiện t0 (Packet Schema V0.1 mục 10).
- **Cờ build của `sync10` (chốt 2026-10-29):** env này đặt sẵn `BOARD_SAMP_VERIFIED=1`
  và `BOARD_STIM=1`, nên chỉ dùng sau khi bring-up mục 7 bước 4 đã kiểm cực tính
  `SAMP`, và phải truyền đúng cạnh đo được. Mặc định của firmware là cạnh xuống
  (`BOARD_SAMP_RISING_EDGE=0`). Sai cạnh thì mốc bit 8 lệch một khoảng cố định, cỡ độ
  rộng xung `SAMP` (khoảng 488 µs); logger không bắt được lệch cố định này, và
  `L_ECG,SAMP` đo ở đây chỉ đúng với cạnh đã dùng. Độ rộng xung LED truyền cùng lúc.
  Giá trị đo được truyền lúc build bằng biến môi trường, không sửa `platformio.ini`
  ([firmware/README.md](../../firmware/README.md) mục "Bản build"):

  ```powershell
  $env:PLATFORMIO_BUILD_FLAGS = "-DBOARD_SAMP_RISING_EDGE=1 -DBOARD_PPG_LED_PW_US=411"
  pio run -d firmware -e esp32s3_devkitc_sync10 -t upload --upload-port COM5
  Remove-Item Env:PLATFORMIO_BUILD_FLAGS
  ```

  (ví dụ: cạnh lên, 411 µs.) Ghi nguyên văn biến môi trường, commit và ELF SHA-256
  (packet `0xD1`) vào báo cáo; cực tính `SAMP` không có trong luồng packet.
- **Kênh ECG:** đưa xung qua mạch chia áp vào đầu vào điện cực của breakout
  MAX30001, để biên độ ở mức vài mV (đúng dải ECG). Mạch chia áp là mức bắt buộc tối
  thiểu (chốt 2026-10-29, [bring-up](v1_bringup_procedure.md) mục 7 bước 5). ECG/patient
  simulator có QRS, nếu lab có, dùng cho bước tùy chọn kiểm phát hiện R-peak (bring-up
  mục 7 bước 6); chỉ thay mạch chia áp trong phép đo này khi simulator có đầu vào
  trigger nhận xung GPIO6. Không nối GPIO trực tiếp vào đầu vào ECG.
  **Nút tham chiếu (chốt 2026-10-25): nút "cơ thể" nối chân sleeve của jack điện
  cực** (RL → R3 220 kΩ → VCM), không phải GND của bo. Lý do: ở AVDD = 1,8 V đầu
  vào ECG chỉ làm việc trong VMID ± 550 mV, VMID = AVDD/2,15 ≈ 0,84 V, tức khoảng
  0,29–1,39 V (MAX30001 tr. 3, tr. 22); GND 0 V nằm ngoài dải này, còn VCM 0,65 V
  (tr. 8) nằm trong. Đấu nối: tip (RA) nối sleeve; GPIO6 → điện trở trên cỡ 10 MΩ →
  ring (LA) → điện trở dưới cỡ 3,3 kΩ → sleeve. Ước lượng (kiểm bằng
  oscilloscope trước khi chạy; mạch là GPIO6 → 10 MΩ → 3,3 kΩ → R3 220 kΩ → VCM
  0,65 V): khi GPIO6 ở 3,3 V, dòng khoảng (3,3 − 0,65) V / 10,22 MΩ ≈ 0,26 µA, cho
  vi sai khoảng +0,86 mV ở LA so với RA và đẩy mức chung lên khoảng 57 mV qua R3;
  khi GPIO6 ở 0 V, dòng khoảng −64 nA, vi sai khoảng −0,21 mV, mức chung lệch khoảng
  −14 mV. Biên độ xung vi sai vì vậy khoảng 1,07 mV, mọi mức vẫn trong dải trên. Ghi
  giá trị điện trở thực tế và số đo vào sơ đồ đấu nối.
- **Kênh PPG:** cùng xung đó điều khiển một LED ngoài (qua điện trở hạn dòng)
  đặt trên cửa sổ cảm biến MAX3010x, trong hộp tối. Ánh sáng tăng làm số đếm ADC
  tăng. Chọn dòng LED để không bão hòa ADC hay tràn khử ánh sáng môi trường
  (STATUS bit 6 phải bằng 0).
- **Chưa kiểm:** MAX3010x có khử ánh sáng môi trường (ambient light
  cancellation, ALC). LED ngoài sáng liên tục trong cả xung 50 ms có thể bị ALC
  coi là ánh sáng môi trường và trừ đi, khi đó số đếm ADC không tăng như giả định
  ở trên [chưa đối chiếu datasheet]. Bit 6 = 0 (`ALC_OVF` không bật) chỉ cho biết
  ALC chưa tràn, không chứng minh kích thích thấy được trong dữ liệu PPG. Phải
  thử trên bàn với PCB V1 (không người), sau bring-up mục 8, nhìn trực tiếp số đếm
  ADC tại cạnh xung, trước khi chạy đủ 10 phút (mục 8).
- **Phép thử trước 1 phút và phương án thay thế (đề xuất 2026-11-11, duyệt 2026-11-14).** Ghi 1
  phút có kích thích trong hộp tối. Kích thích PPG được coi là **thấy được** khi, ở cả ba
  khe, bước nhảy trung vị của số đếm ADC tại cạnh lên lớn hơn 10 lần độ lệch chuẩn của số đếm
  lúc không có xung, và STATUS bit 6 bằng 0 suốt 1 phút. Không đạt thì **không chạy** phép đo
  10 phút với LED ngoài sáng liên tục, và không đổi ngưỡng 10 lần để cho qua. Khi đó phải
  thiết kế và duyệt một phương án khác trước khi đo. Hai ứng viên, chưa thử:
  1. đo thẳng thời điểm xung LED của chính cảm biến bằng photodiode và oscilloscope, lấy cạnh
     GPIO6 làm mốc. Xung LED là lúc cảm biến lấy mẫu quang, nên cách này không phụ thuộc ALC;
     phải thêm cách xác định xung nào ứng với mẫu nào;
  2. chớp LED ngoài thật ngắn (ngắn hơn độ rộng xung của cảm biến) ở pha ngẫu nhiên, rồi xem
     chớp nào làm đổi số đếm: tập các pha có đáp ứng cho biết cửa sổ lấy mẫu nằm ở đâu so với
     clock MCU. Rủi ro: chớp có thể rơi đúng lúc ALC lấy mẫu ánh sáng nền;
  3. chắn và mở đường phản xạ của chính LED cảm biến bằng một màn chắn quang, đo thời điểm chắn
     bằng một photodiode tham chiếu (gợi ý của phản biện độc lập).

  Bước nhảy lớn hơn 10 lần nhiễu chỉ cho biết kích thích thấy được, không chứng minh thời điểm
  đo được là đúng.

  Nếu chưa có phương án nào đạt thì offset ECG–PPG **chưa đo được**, và không tính PAT từ thiết
  bị (mục 9).
- Ghi lại sơ đồ đấu nối thực tế, giá trị điện trở, khoảng cách LED–cảm biến.

Nếu chưa dựng được kích thích chung, vẫn đo được mục 1–3 và 5 (chỉ dùng chỉ số
mẫu và `T_ANCHOR_US`), nhưng **chưa** đo được offset ECG–PPG (mục 4).

Trên KiCad V1-module (pin map chuẩn của V1), INT2B của MAX30001 đã nối vào GPIO47
(`configs/hardware/custom_board_proposal.md` mục A.6, A.7). Firmware bật xung `SAMP`
luôn và dùng làm mốc thời gian ECG (chốt 2026-10-24; xung ở tốc độ dữ liệu ECG, lúc
mẫu vào FIFO chứ không phải lúc lấy mẫu analog; MAX30001 tr. 42, tr. 44;
`Packet_Schema_V0.1.md` mục 5.2), nên bản cuối cũng phải nối INT2B. Trong phép đo
này, ghi thêm thời điểm các cạnh xung.
Chúng cho tốc độ ECG thực độc lập với mốc đọc FIFO và kiểm tra chéo được kết quả
hồi quy ở mục 5.

Độ trễ ECG dự kiến để đối chiếu với `L_ECG` đo được: MAX30001 tr. 26, Bảng 4 chỉ
cho độ trễ bộ lọc số (ví dụ 512 sps: 19,836 ms không LPF, 31,555 ms có LPF). Ghi
chú ứng dụng của ADI cho MAX30003 đo thêm 1,003 ms trễ lấy mẫu ADC, tức 20,839 /
32,558 ms tính từ lúc lấy mẫu analog tới cạnh xuống của xung `SAMP` (ngay sau khi
mẫu vào FIFO), độ lệch chuẩn khoảng 3–4 µs (`Packet_Schema_V0.1.md` mục 5.2).
`L_ECG` tính theo `T_ANCHOR_US` còn cộng thêm thời gian mẫu nằm trong FIFO trước khi
được đọc. Kết quả đo lệch xa các giá trị này là dấu hiệu sai cấu hình hoặc sai cách
gán thời điểm.

Từ V0.2, packet ECG có bit 8 mang mốc `SAMP` (Packet Schema V0.2 mục 7). Với các packet này,
đại lượng đo là `L_ECG,SAMP`: độ trễ từ lúc lấy mẫu analog tới cạnh `SAMP` đã chốt,
**không** gồm thời gian mẫu nằm trong FIFO. Tính và báo riêng `L_ECG,SAMP` và `L_ECG`
của mốc đọc FIFO; khi phân tích không trừ cả hai. Nếu ánh xạ xung ↔ mẫu lệch cố định
một mẫu, `L_ECG,SAMP` đo được lệch 1,953 ms so với giá trị dự kiến: phép đo này là
kiểm tra độc lập cho ánh xạ đó.

## 4. Quy trình

1. Khởi động MCU, ghi metadata phiên. Laptop chạy pin.
2. Thu 1 phút để ổn định, bỏ khỏi phân tích (ghi lại, không xóa).
3. Thu 10 phút liên tục với kích thích khoảng 1 Hz: khoảng 600 sự kiện. Mỗi xung
   cách xung trước 1 s cộng một độ lệch ngẫu nhiên đều trong [0; 1 953) µs (seed là
   `SESSION_ID`, ghi lại vào metadata; thời điểm thật của từng xung đã có trong packet
   sự kiện), để pha của
   xung phủ đều một chu kỳ mẫu ECG; vì độ lệch cộng dồn, pha cũng phủ đều chu kỳ mẫu PPG
   (mục 5, "Độ phủ pha của kênh PPG"). Một chu kỳ cố định (ví dụ 1 000 049 µs) có thể
   khóa pha nếu tốc độ ECG thật lệch đúng khoảng −49 ppm. Khi phân tích, đo độ phủ pha
   so với cạnh `SAMP`; chỉ báo `L_ECG,SAMP` với độ phân giải dưới một mẫu khi độ phủ
   đạt, nếu không thì khởi động lại MCU (`SESSION_ID` mới là seed mới) và đo lại.
4. Lặp lại **5 lần** cho mỗi cấu hình, khởi động lại MCU giữa các lần, rồi **5 lần nữa vào một
   ngày khác**, bo tắt nguồn giữa hai ngày (sửa 2026-11-11, bản trước ghi 3 lần: tiêu chí A5 ở
   mục 9 so offset giữa các lần khởi động, và ΔPAT của nghiên cứu so các phiên khác ngày).
5. Lưu: file packet nhị phân thô, file `t_rx` của PC, metadata JSON, sơ đồ đấu nối,
   SHA-256 của từng file, commit firmware và commit script phân tích.
6. **Một lần chạy 120 phút có kích thích** (thêm 2026-11-11), bằng buổi đo dài nhất, cho tiêu
   chí A6. Lần chạy này tách khỏi phép thử nhiệt và lần chạy cả hệ 120 phút của bring-up, vì
   LED ngoài che cửa sổ cảm biến.

## 5. Phân tích

Ký hiệu cho mỗi kênh c: `k` là chỉ số mẫu tích lũy của mẫu cuối mỗi packet,
`A_us(k)` là `T_ANCHOR_US` tương ứng (µs); `fs_c` tính bằng Hz.

Mọi hồi quy và chỉ số dưới đây tính riêng cho từng phiên, từng chuỗi liên tục (ranh
giới bit 5) và, với ECG, từng nguồn mốc (bit 8 = 1: mốc `SAMP`; bit 8 = 0: mốc đọc
FIFO; Packet Schema V0.2 mục 7.5); bỏ anchor của packet bit 0/bit 7. Không gộp hai
nguồn mốc trong một hồi quy, và `L_ECG` luôn ghi kèm nguồn mốc.

**Ba khe PPG (chốt 2026-10-29).** Theo quy ước offset giữa các khe
([Packet_Schema_V0.1.md](../../configs/hardware/Packet_Schema_V0.1.md) mục 7): mốc
`t'` của khe j là mốc dựng theo V0.1 mục 5.3 cộng (j − 1) · Δ(PW), gốc là khe 1, Δ
suy từ `SPO2_CONFIG` trong `0xD2` của phiên.

- `L_PPG` đo trên trục thời gian **đã cộng** Δ: một giá trị `L_PPG` cho cấu hình, ước
  lượng từ cạnh kích thích thấy trên các khe sau khi cộng Δ.
- Phần dư theo từng khe (`L_PPG,j` riêng từng khe trừ `L_PPG`) chỉ để kiểm quy ước (ví
  dụ Δ sai hay một khe lệch), **không** trừ lần hai khi dựng thời gian mẫu.
- Ghi version của quy ước cùng kết quả; Δ danh định 1 107 µs (411 µs) hay 720 µs
  (215 µs), Δ dùng thật suy từ `0xD2`.

| Chỉ số | Cách tính |
| --- | --- |
| Tốc độ thực `fs_c` | Hồi quy tuyến tính `A_us(k) = a_us + b_us · k`, với `b_us = 10⁶ / fs_c` (µs/mẫu; ví dụ 200 Hz cho `b_us ≈ 5 000`). Suy ra `fs_c = 10⁶ / b_us`, báo cáo kèm khoảng tin cậy |
| Drift so với danh định | `(fs_c / fs_danh_định − 1) × 10⁶` ppm |
| Drift ECG so với PPG | Hiệu hai giá trị ppm; quy ra µs lệch tích lũy sau 10 phút |
| Jitter mốc đọc | Độ lệch chuẩn và phân vị 99 của phần dư hồi quy (µs) |
| Thời điểm mẫu tạm | `t'_us[i]` theo packet schema mục 5.3, dùng `fs_c` đã ước lượng nhưng **tạm đặt** `δ = 0`, `d_pipe = 0` |
| Độ trễ hiệu dụng `L_c` | Với mỗi sự kiện: thời điểm tâm xung của đáp ứng theo `t'` trừ tâm xung vào (`T_ANCHOR_US` của packet sự kiện cộng nửa độ rộng xung); lấy trung bình, báo kèm trung vị (sửa 2026-11-11, mục 9; bản trước dùng thời điểm cạnh và trung vị). `L_c` gộp `d_pipe` và giá trị trung bình của `δ`, chính là lượng cần trừ khỏi `t'` |
| Jitter theo sự kiện | Độ lệch chuẩn của hiệu trên qua 600 sự kiện |
| Offset ECG–PPG | `L_ECG − L_PPG` cho từng nguồn mốc ECG (`L_ECG,SAMP` và `L_ECG` của mốc đọc FIFO báo riêng), kèm khoảng tin cậy |
| Ổn định theo thời gian | Vẽ hiệu trên theo thời gian; độ dốc khác 0 là drift chưa hiệu chỉnh |
| Mất dữ liệu | Số `SEQ` thiếu / tổng; số mẫu mất từ `FIRST_SAMPLE_INDEX`; số lần STATUS bit 0, 1, 5; số lỗi CRC |

**Dấu của offset so với mô phỏng.** `L_c` là lượng thời điểm cạnh trên trục `t'`
của kênh c đi sau `T_ANCHOR_US` của sự kiện, nên cùng một cạnh vật lý có nhãn
thời gian trên kênh PPG trừ nhãn trên kênh ECG bằng `L_PPG − L_ECG`. Mô phỏng
`synthetic-packet-v2` báo `offset_ppg_minus_ecg_us` = anchor PPG − anchor ECG
(`software/data_io/packet_simulation.py`, `replay_packets`; anchor là
`timestamp_us` của packet hợp lệ đầu tiên quy về sequence start, hai kênh cùng
epoch giả lập), tức cùng ý nghĩa "nhãn PPG trừ nhãn ECG". Vì vậy
`offset_ppg_minus_ecg_us` tương ứng `L_PPG − L_ECG = −(L_ECG − L_PPG)`: đổi dấu
offset ở bảng trên trước khi so với mô phỏng. Dương nghĩa là kênh PPG gán nhãn
muộn hơn kênh ECG.

Cách phát hiện cạnh (ngưỡng, nội suy giữa hai mẫu) phải chốt **trước** khi xem
kết quả và giữ nguyên cho mọi lần đo. Độ phân giải thời gian bị giới hạn bởi
chu kỳ lấy mẫu; ghi rõ trong báo cáo.

**Độ phủ pha của kênh PPG (thêm 2026-11-11, sửa cùng ngày).** Lịch kích thích tính theo thời
điểm đích, nên độ lệch ngẫu nhiên **cộng dồn**: cạnh thứ n cách cạnh đầu n × 1 s cộng tổng n độ
lệch. Cả 1 s lẫn tổng các độ lệch đều không phải bội của 5 000 µs, và 1 s là bội đúng của cả
1 953,125 µs (512 chu kỳ) lẫn 5 000 µs (200 chu kỳ), nên pha của cạnh so với lưới mẫu là một bước
ngẫu nhiên trên vòng tròn, với bước trung bình khoảng 976 µs. Sau 600 cạnh, bước này đã quay
khoảng 117 vòng chu kỳ PPG, nên pha phủ đều cả chu kỳ 5 000 µs dù mỗi độ lệch chỉ dài tối đa
1 953 µs. Test `tests/test_firmware_stim_plan.py` kiểm điều này trên dãy thật của firmware, ở tốc
độ danh định và ở tốc độ lệch ± 3 %. Bản đầu của đoạn này cho rằng pha PPG chỉ phủ khoảng 39 % chu
kỳ và đề xuất đổi dải độ lệch thành [0; 125 000) µs; nhận định đó coi các độ lệch như không cộng
dồn, và đã bỏ. **Không cần sửa firmware.** Khi phân tích vẫn đo độ phủ pha cho **cả hai kênh**
(tiêu chí A9 ở mục 9), vì phép kiểm trên giả định tốc độ lấy mẫu không đổi trong lần đo.

## 6. Báo cáo

Lưu tại `hardware/test_reports/` dưới dạng báo cáo có ngày, kèm: cấu hình, sơ đồ
đấu nối, đường dẫn và SHA-256 của dữ liệu thô (dữ liệu thô lưu ngoài Git theo
chính sách dữ liệu), bảng chỉ số ở mục 5 cho từng lần đo, các bất thường và giới
hạn. Ghi riêng "giá trị thiết kế/datasheet" và "giá trị đo được".

## 7. Giới hạn

- Kích thích nhân tạo không có hình thái sinh lý; kết quả chỉ nói về thời gian
  của chuỗi đo, không nói về chất lượng tín hiệu trên người.
- Độ trễ của LED ngoài và mạch chia áp được coi là không đáng kể so với chu kỳ
  lấy mẫu; nếu nghi ngờ, kiểm tra bằng oscilloscope.
- Độ trễ hiệu dụng phụ thuộc cấu hình: đổi tốc độ, bộ lọc hay lấy trung bình
  thì phải đo lại.

## 8. Việc còn mở

1. Kích thích PPG bằng LED ngoài có bị ALC của MAX3010x trừ đi không, và cách
   hiểu STATUS bit 6 (`ALC_OVF`) trong phép đo này (mục 3). Kiểm trước, khi thử
   trên bàn với PCB V1 (không người) sau bring-up mục 8.
2. MAX30101 ở multi-LED ba khe: datasheet không có bảng tổ hợp tốc độ × độ rộng
   xung cho chế độ này (`custom_board_proposal.md` A.6 mục 3), và chip tự đổi tốc
   độ khi tổ hợp không được phép. Trước khi đo, đọc lại thanh ghi `SPO2_SR`; khi
   đo, so tốc độ thực từng khe với tốc độ cấu hình chia `SMP_AVE` (bắt đầu với
   `SMP_AVE = 1`). Chênh lệch nằm trong sai số dao động nội là bình thường; chênh
   theo bội số (ví dụ còn một nửa) nghĩa là chip đã đổi tốc độ.

## 9. Tiêu chí chấp nhận (đề xuất 2026-11-11, duyệt 2026-11-14; viết trước khi đo)

Áp cho cấu hình sẽ dùng trên người (512 sps, 200 sps ba khe, độ rộng xung đã chốt). Mọi ngưỡng
là đề xuất kỹ thuật, **chưa có nguồn**; căn cứ ghi ở cuối mục.

| # | Đại lượng | Đạt khi | Căn cứ của ngưỡng |
| --- | --- | --- | --- |
| A1 | Toàn vẹn dữ liệu trong một lần 10 phút | 0 mẫu mất trong AFE (STATUS bit 0), 0 lỗi CRC, 0 packet thiếu. Lần có mất dữ liệu thì không tính và đo lại; quá 1 trong 5 lần phải đo lại thì không đạt | Mất mẫu cắt chuỗi liên tục, làm hồi quy thời gian phải chia đoạn |
| A2 | Tốc độ thực | PPG: mỗi khe trong 200 sps ± 3 %. ECG: trong 512 sps ± 1 000 ppm | Dùng lại hai dung sai đã có: [interface_power_sampling_v0.md](../../configs/hardware/interface_power_sampling_v0.md) mục 6 ý (b) và Packet Schema V0.2 mục 7 (tạm) |
| A3 | Mô hình thời gian tuyến tính | Phần dư của hồi quy mốc theo chỉ số mẫu, lấy trung vị theo khối 10 s, không vượt ± 0,2 ms trong cả lần đo, cho từng kênh (ECG dùng mốc `SAMP`) | Một đường thẳng cho cả bản ghi chỉ dùng được khi tốc độ không trôi trong lúc ghi |
| A4 | Độ bất định của offset ECG–PPG trong một lần đo | Nửa độ rộng CI 95 % của `L_ECG,SAMP − L_PPG` ≤ 0,15 ms. Offset ước lượng bằng **trung bình** qua các sự kiện, gộp ba khe PPG sau khi cộng Δ; CI lấy bằng bootstrap theo sự kiện | Đủ nhỏ để A5 phân biệt được các lần khởi động; phép tính ở dưới |
| A5 | Offset lặp lại giữa các lần khởi động | Giá trị lớn nhất trừ nhỏ nhất của offset qua **10 lần** (5 lần ngày thứ nhất, 5 lần vào một ngày khác, bo tắt nguồn giữa hai ngày) ≤ 0,3 ms | Bảo vệ ΔPAT giữa các phiên khác ngày; phép tính ở dưới |
| A6 | Offset không trôi trong buổi đo dài | Lần chạy 120 phút: chia thành sáu khối 20 phút, offset của từng khối; giá trị lớn nhất trừ nhỏ nhất ≤ 0,4 ms. Lần 10 phút chỉ báo độ dốc của offset theo thời gian kèm CI, không có ngưỡng | Buổi đo dài tới 120 phút; trôi cộng thẳng vào ΔPAT giữa các lần cuff. Trong 10 phút, nhiễu của phép đo lớn hơn mức trôi cần bắt |
| A7 | Jitter theo sự kiện | **Chỉ báo cáo, không phải tiêu chí đạt/không đạt:** độ lệch chuẩn của (thời điểm đáp ứng − mốc sự kiện) từng kênh | Giá trị kỳ vọng do lượng tử một chu kỳ mẫu (chu kỳ / √12): 0,56 ms với ECG, 1,44 ms với một khe PPG. Lớn hơn hẳn thì tìm nguyên nhân |
| A8 | Độ trễ ECG so với thiết kế | \|`L_ECG,SAMP` − 32,558 ms\| ≤ 0,98 ms, với `L_ECG,SAMP` đo theo **tâm xung** (xem dưới) | Nửa chu kỳ mẫu ECG: lệch cố định một mẫu (1,953 ms) phải bị bắt. Giá trị 32,558 ms theo mục 3 |
| A9 | Độ phủ pha của kích thích | Chia chu kỳ mẫu của mỗi kênh thành 10 ô pha; mỗi ô có ít nhất 5 % số sự kiện (kỳ vọng 10 %) | Chỉ khi pha phủ đều thì ước lượng qua các sự kiện mới có độ phân giải dưới một mẫu |

Cách đọc:

- **Đạt** khi A1–A6, A8 và A9 cùng đạt. A9 không đạt ở kênh nào thì A4–A6 và A8 là "không đánh
  giá được", không tính là đạt; khởi động lại (`SESSION_ID` mới là dãy độ lệch mới) rồi đo lại.
- **A3 không đạt** với một đường thẳng: dùng hồi quy theo đoạn 60 s rồi xét lại A3–A6 với mô
  hình đó. Mô hình nào đạt thì đó là mô hình **bắt buộc** khi dựng thời gian cho dữ liệu buổi
  đo, kể cả buổi 120 phút.
- A7 chỉ để báo cáo.
- **A4, A5, A6 hoặc A8 không đạt:** không tính PAT từ thiết bị cho tới khi tìm ra nguyên nhân,
  sửa, và đo lại đủ bộ. Không nới ngưỡng để cho qua.
- Độ trễ PPG `L_PPG` không có giá trị thiết kế để so (datasheet không cho), nên chỉ xét độ lặp
  lại qua A5.
- Kết quả đạt chỉ đúng cho cấu hình đã đo. Đổi tốc độ, bộ lọc, độ rộng xung, cực tính `SAMP`
  hay firmware phần thời gian thì đo lại.

**Cách đo độ trễ (sửa 2026-11-11 sau phản biện độc lập).** Thời điểm của đáp ứng lấy ở **tâm
xung**: trung điểm của hai lần cắt mức 50 % ở sườn lên và sườn xuống của đáp ứng. Tâm xung vào
bằng mốc sự kiện cộng nửa độ rộng xung, với độ rộng xung đo bằng oscilloscope. Giá trị thiết kế
32,558 ms được nhà sản xuất xác minh theo tâm xung vào và tâm xung ra (theo phản biện độc lập;
chưa đối chiếu lại với ghi chú ứng dụng); thời điểm cắt ngưỡng trên
một sườn đã qua bộ lọc thì phụ thuộc mức ngưỡng và đáp ứng của bộ lọc, nên không so thẳng được
với giá trị đó. Mục 5 trước đây lấy trung vị qua các sự kiện; nay lấy trung bình và báo kèm trung
vị, vì với sai số lượng tử phân bố đều, trung vị kém chính xác hơn trung bình khoảng 1,7 lần.

**Phép tính cho A4 và A5** (giả định sai số chỉ do lượng tử, pha phủ đều, 600 sự kiện):

- Độ lệch chuẩn mỗi sự kiện: ECG 1,953 / √12 = 0,56 ms; PPG một khe 5 / √12 = 1,44 ms; PPG gộp
  ba khe lệch nhau Δ = 1,107 ms khoảng 0,64 ms.
- Nửa CI 95 % của offset: 1,96 × √(0,56² + 1,44²) / √600 = 0,12 ms với một khe, và
  1,96 × √(0,56² + 0,64²) / √600 = 0,07 ms khi gộp ba khe. Ngưỡng 0,15 ms vì vậy chỉ dư ít nếu
  phải dùng một khe.
- Với độ chính xác kỳ vọng ở trên (nửa CI 0,07–0,12 ms), khoảng biến thiên của mười ước lượng
  đúng nằm dưới 0,3 ms trong hơn 95 % trường hợp. Nếu nửa CI sát ngưỡng 0,15 ms thì khoảng một
  phần mười trường hợp vượt 0,3 ms chỉ vì nhiễu đo; khi đó đo lại với nhiều sự kiện hơn, không
  nới ngưỡng. Một lần khởi động gán nhầm mốc ít nhất 488 µs sẽ đẩy khoảng biến thiên lên khoảng
  0,49 ms, vượt ngưỡng 0,3 ms.

**A5 và A8 không bắt được gì.** Các lỗi gán mốc đã biết đều rời rạc: sai cực tính `SAMP` khoảng
488 µs (mục 3); lệch một khe PPG 720 µs hay 1 107 µs (mục 5); lệch một mẫu ECG 1 953 µs; lệch
một mẫu PPG 5 000 µs.

- A5 chỉ bắt lỗi **đổi giữa các lần khởi động**. Lỗi giống nhau ở mọi lần cho khoảng biến thiên
  bằng 0. Lỗi như vậy là offset cố định: nó triệt tiêu trong ΔPAT, nhưng làm sai PAT tuyệt đối.
- A8 bắt lệch một mẫu ECG, không bắt sai cực tính `SAMP` (488 µs nhỏ hơn dung sai 0,98 ms). Cực
  tính được kiểm riêng bằng oscilloscope ở bring-up mục 7 bước 4.
- Phía PPG không có giá trị thiết kế, nên lệch cố định một khe hay một mẫu PPG **không có phép
  kiểm độc lập nào** trong kế hoạch này. Muốn kiểm phải đo thẳng thời điểm xung LED của cảm biến
  (mục 3, phương án thay thế 1). Cho tới khi làm được, PAT tuyệt đối từ thiết bị có thể lệch cố
  định tới 5 ms; báo cáo phải ghi điều này.
- A3 kiểm tổng của thời gian lấy mẫu và độ trễ đọc FIFO; hai phần có thể bù nhau. A6 là phép kiểm
  độc lập hơn cho trôi.

## 10. Ngân sách sai số PAT (đề xuất 2026-11-11, duyệt 2026-11-14)

Phân tích dùng ΔPAT: trung vị PAT của một cửa sổ trừ trung vị PAT của cửa sổ hiệu chuẩn
([SAP v1](../../docs/protocol/sap_v1.md) mục 4). Bảng dưới là ước lượng khi các tiêu chí ở mục 9 đạt.

| Nguồn sai số | Loại | Độ lớn | Ghi chú |
| --- | --- | --- | --- |
| Định vị đỉnh R, 512 sps, không nội suy | Ngẫu nhiên theo nhịp | SD 0,56 ms | Chu kỳ 1,953 ms / √12 |
| Định vị chân sóng PPG, 200 sps, không nội suy | Ngẫu nhiên theo nhịp | SD 1,44 ms | Chu kỳ 5 ms / √12; phương pháp có nội suy dưới mẫu thì nhỏ hơn, chưa đo |
| Trung vị PAT của một cửa sổ, 20 cặp nhịp | Ngẫu nhiên theo cửa sổ | Sai số chuẩn khoảng 0,56 ms | Sai số mỗi nhịp là hiệu của hai phân bố đều (rộng 1,953 và 5 ms), mật độ tại 0 là 0,2 /ms, nên sai số chuẩn của trung vị là 1 / (2 × 0,2 × √20); 20 cặp là 30 s ở nhịp 40 lần/phút |
| ΔPAT giữa hai cửa sổ | Ngẫu nhiên | Sai số chuẩn khoảng 0,8 ms | √2 × 0,56 ms, nếu hai cửa sổ độc lập |
| Offset ECG–PPG, phần không đổi | Hệ thống, cố định | Triệt tiêu trong ΔPAT | Chỉ ảnh hưởng PAT tuyệt đối và khoảng PAT hợp lệ 80–400 ms; có thể tới 5 ms (mục 9) |
| Offset đổi giữa các lần khởi động | Hệ thống, giữa phiên | Tối đa 0,3 ms | A5 |
| Offset trôi trong buổi đo | Hệ thống, trong phiên | Tối đa 0,4 ms trong 120 phút | A6 |

- Đây là ước lượng theo các giả định ghi trong bảng, **không phải cận trên đã chứng minh**. Nếu
  A5 và A6 đạt thì sai số hệ thống của ΔPAT giữa hai phiên do thiết bị vào khoảng 0,5–0,7 ms
  (0,7 ms nếu hai phần cộng thẳng). Phần này **không giảm** khi lấy trung bình nhiều nhịp.
- Bảng chưa gồm: độ trễ đọc FIFO của kênh PPG; pha lấy mẫu của MAX30101 đổi sau mỗi lần khởi
  động; lỗi gán khe; và sự dịch mốc do bộ lọc khi hình dạng sóng đổi.
- **Chưa quy được các con số này ra mmHg.** Độ nhạy của PAT theo huyết áp ở quần thể và vị trí
  đo của nhóm chưa biết. Pilot cho độ lệch chuẩn của ΔPAT sinh lý giữa các lần cuff; nếu sai số
  hệ thống ở trên không nhỏ hơn hẳn giá trị đó thì kết quả về PAT phải nêu giới hạn này.
- Bảng chưa gồm sai số sinh lý và sai số thuật toán (nhịp bị bỏ sót, mốc giả, thay đổi hình
  dạng sóng); các phần đó thuộc [tài liệu mốc Tuần 5](../../docs/protocol/week05_fiducials_pat_validity.md).
