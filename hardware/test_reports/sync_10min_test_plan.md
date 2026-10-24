# Kế hoạch đo đồng bộ ECG–PPG 10 phút (bench, không đo người)

> Chưa thực hiện vì chưa có phần cứng. Chỉ tiêu đạt/không
> đạt chưa chốt; theo `configs/hardware/hardware_requirements_for_V0.md` §4.4,
> giới hạn jitter/drift chỉ đặt sau khi có số đo đầu tiên.

## 1. Mục tiêu

Trên thiết bị V0 đã bring-up, đo trong 10 phút liên tục:

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
- Firmware gửi packet theo `configs/hardware/Packet_Schema_V0.1.md`, có
  `FIRST_SAMPLE_INDEX`, `T_ANCHOR_US` và packet sự kiện `0xC1`.
- Cấu hình AFE (tốc độ, FMSTR, chế độ LED, lấy trung bình, bộ lọc) đã ghi vào
  metadata phiên. Mỗi cấu hình khác nhau là một lần đo riêng.
- **Không gắn điện cực lên người.** Mọi đo đạc dùng tín hiệu nhân tạo.

## 3. Bố trí kích thích chung

Cần một sự kiện vật lý mà **cả hai kênh cùng thấy**, với thời điểm do chính MCU
ghi lại:

- GPIO6 của ESP32-S3, đưa ra header J3 (GPIO6, GND) trên bo đế (chốt 2026-10-24,
  `custom_board_proposal.md` A.2), phát xung vuông, chu kỳ 1 s, độ rộng khoảng
  50 ms.
  MCU gửi packet sự kiện mã `3` với `T_ANCHOR_US` tại cạnh lên.
- **Kênh ECG:** đưa xung qua mạch chia áp vào đầu vào điện cực của breakout
  MAX30001, để biên độ ở mức vài mV (đúng dải ECG). Nếu có ECG simulator có
  đầu vào trigger thì dùng simulator. Không nối GPIO trực tiếp vào đầu vào ECG.
  Nút tham chiếu của mạch chia áp (GND của bo, hay VCM/chân sleeve của jack điện
  cực) **chưa chốt** (mục 8); phải ghi rõ trên sơ đồ đấu nối.
- **Kênh PPG:** cùng xung đó điều khiển một LED ngoài (qua điện trở hạn dòng)
  đặt trên cửa sổ cảm biến MAX3010x, trong hộp tối. Ánh sáng tăng làm số đếm ADC
  tăng. Chọn dòng LED để không bão hòa ADC hay tràn khử ánh sáng môi trường
  (STATUS bit 6 phải bằng 0).
- **Chưa kiểm:** MAX3010x có khử ánh sáng môi trường (ambient light
  cancellation, ALC). LED ngoài sáng liên tục trong cả xung 50 ms có thể bị ALC
  coi là ánh sáng môi trường và trừ đi, khi đó số đếm ADC không tăng như giả định
  ở trên [chưa đối chiếu datasheet]. Bit 6 = 0 (`ALC_OVF` không bật) chỉ cho biết
  ALC chưa tràn, không chứng minh kích thích thấy được trong dữ liệu PPG. Phải
  thử trên bench, nhìn trực tiếp số đếm ADC tại cạnh xung, trước khi chạy đủ 10
  phút (mục 8).
- Ghi lại sơ đồ đấu nối thực tế, giá trị điện trở, khoảng cách LED–cảm biến.

Nếu chưa dựng được kích thích chung, vẫn đo được mục 1–3 và 5 (chỉ dùng chỉ số
mẫu và `T_ANCHOR_US`), nhưng **chưa** đo được offset ECG–PPG (mục 4).

Trên KiCad V1-module (pin map chuẩn của V1), INT2B của MAX30001 đã nối vào GPIO47
(`configs/hardware/custom_board_proposal.md` mục A.6, A.7); với bản cuối thì còn
mở. Nếu INT2B được nối và firmware bật xung `SAMP` (ở tốc độ dữ liệu ECG, lúc mẫu
vào FIFO chứ không phải lúc lấy mẫu analog; MAX30001 tr. 42, tr. 44;
`Packet_Schema_V0.1.md` mục 5.2), ghi thêm thời điểm các cạnh xung này.
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

## 4. Quy trình

1. Khởi động MCU, ghi metadata phiên. Laptop chạy pin.
2. Thu 1 phút để ổn định, bỏ khỏi phân tích (ghi lại, không xóa).
3. Thu 10 phút liên tục với kích thích 1 Hz: khoảng 600 sự kiện.
4. Lặp lại 3 lần cho mỗi cấu hình, khởi động lại MCU giữa các lần.
5. Lưu: file packet nhị phân thô, file `t_rx` của PC, metadata JSON, sơ đồ đấu nối,
   SHA-256 của từng file, commit firmware và commit script phân tích.

## 5. Phân tích

Ký hiệu cho mỗi kênh c: `k` là chỉ số mẫu tích lũy của mẫu cuối mỗi packet,
`A_us(k)` là `T_ANCHOR_US` tương ứng (µs); `fs_c` tính bằng Hz.

| Chỉ số | Cách tính |
| --- | --- |
| Tốc độ thực `fs_c` | Hồi quy tuyến tính `A_us(k) = a_us + b_us · k`, với `b_us = 10⁶ / fs_c` (µs/mẫu; ví dụ 200 Hz cho `b_us ≈ 5 000`). Suy ra `fs_c = 10⁶ / b_us`, báo cáo kèm khoảng tin cậy |
| Drift so với danh định | `(fs_c / fs_danh_định − 1) × 10⁶` ppm |
| Drift ECG so với PPG | Hiệu hai giá trị ppm; quy ra µs lệch tích lũy sau 10 phút |
| Jitter mốc đọc | Độ lệch chuẩn và phân vị 99 của phần dư hồi quy (µs) |
| Thời điểm mẫu tạm | `t'_us[i]` theo packet schema mục 5.3, dùng `fs_c` đã ước lượng nhưng **tạm đặt** `δ = 0`, `d_pipe = 0` |
| Độ trễ hiệu dụng `L_c` | Với mỗi sự kiện: thời điểm cạnh trong tín hiệu theo `t'` trừ `T_ANCHOR_US` của packet sự kiện; lấy trung vị. `L_c` gộp `d_pipe` và giá trị trung bình của `δ`, chính là lượng cần trừ khỏi `t'` |
| Jitter theo sự kiện | Độ lệch chuẩn của hiệu trên qua 600 sự kiện |
| Offset ECG–PPG | `L_ECG − L_PPG`, kèm khoảng tin cậy |
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
   hiểu STATUS bit 6 (`ALC_OVF`) trong phép đo này (mục 3). Kiểm trên bench
   trước.
2. Nút tham chiếu của mạch chia áp đưa xung vào đầu vào ECG: GND của bo hay
   VCM/sleeve của jack điện cực (mục 3).
3. INT2B (xung `SAMP`): đã nối GPIO47 trên KiCad V1-module; còn mở cho bản cuối
   và cấu hình firmware (mục 3).
4. MAX30101 ở multi-LED ba khe: datasheet không có bảng tổ hợp tốc độ × độ rộng
   xung cho chế độ này (`custom_board_proposal.md` A.6 mục 3), và chip tự đổi tốc
   độ khi tổ hợp không được phép. Trước khi đo, đọc lại thanh ghi `SPO2_SR`; khi
   đo, so tốc độ thực từng khe với tốc độ cấu hình chia `SMP_AVE` (bắt đầu với
   `SMP_AVE = 1`). Chênh lệch nằm trong sai số dao động nội là bình thường; chênh
   theo bội số (ví dụ còn một nửa) nghĩa là chip đã đổi tốc độ.
