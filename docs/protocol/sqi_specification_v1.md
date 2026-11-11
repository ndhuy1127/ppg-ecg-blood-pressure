# Đặc tả SQI v1: chất lượng tín hiệu của một lần đo cuff

> **Trạng thái: đề xuất ngày 2026-11-07; cấu trúc cờ và cách dùng chốt 2026-11-12 (báo thầy);
> ngưỡng khóa trên bản ghi G2.** Gộp các quyết định đã chốt ở
> [protocol v0.3](protocol_outline_v0.2.md) mục 7.3, cờ `features-sqi-v2`
> ([week04.py](../../software/feature_extraction/week04.py)) và `motion-sqi-v0`
> ([motion_sqi.py](../../software/feature_extraction/motion_sqi.py)) thành một đặc tả cho dữ
> liệu thiết bị, rồi thêm các cờ của phần cứng V1 (mục 3.3).
>
> - Mọi ngưỡng ở đây là đề xuất kỹ thuật **chưa có nguồn**. Chúng được khóa trên bản ghi G2 của
>   thành viên nhóm (ghi ngày và commit) trước khi thu dữ liệu chính.
> - Không chọn ngưỡng theo sai số dự đoán BP.
> - Đặc tả này không áp cho PulseDB: PulseDB là dữ liệu đã làm sạch, không có STATUS hay IMU.

## 1. Vai trò của SQI trong phân tích

- **Phân tích chính của RQ1 không loại lần đo nào theo SQI** (chốt 2026-10-29). Lần đo chỉ ra
  khỏi phép so sánh chính khi không **tính được** đặc trưng (mục 4). Đây là điều kiện tính được,
  không phải ngưỡng chất lượng. Mất ECG hay mất PPG xử lý theo protocol mục 10 và
  [SAP v1](sap_v1.md) mục 10.
- **Phân tích phụ đăng ký trước:** lặp lại phép so sánh chính sau khi bỏ các lần đo có cờ trong
  tập loại của mục 5. Coverage được báo trên toàn bộ lần đo, theo từng người.
- **RQ3 (thăm dò):** dùng các chỉ số liên tục ở mục 3 làm điểm từ chối, so trên cùng một tập
  lần đo.

## 2. Đơn vị và cửa sổ

- Đơn vị là một lần đo cuff (`event_id`), cho đúng một cặp nhãn SBP/DBP (protocol 7.1). Không
  có cửa sổ nào thành mẫu riêng.
- Cửa sổ tín hiệu là `[t0 − L, t0)`, với `t0` là lúc bấm cuff (protocol 6.2). L được chọn trong
  10/20/30/60 s và khóa trên pilot. Đề xuất chính là 30 s, chờ pilot.
- Mỗi cờ được tính trên cả cửa sổ. Đặc trưng là trung vị theo nhịp trong cửa sổ, theo `week04.py`.

## 3. Các cờ và chỉ số

### 3.1. ECG và PPG (`features-sqi-v2`, đã có code)

| Cờ | Ý nghĩa |
| --- | --- |
| `ecg:<issue>`, `ppg:<issue>` | Kênh không chuẩn bị được (`prepare`: phẳng, không hữu hạn, quá ngắn) |
| `ecg:too_few_peaks`, `ecg:insufficient_rr_intervals` | Không đủ đỉnh R (dưới `min_beats`) hay khoảng RR để tính HR |
| `ppg:too_few_feet`, `ppg:insufficient_foot_intervals` | Không đủ chân sóng hay khoảng giữa chân sóng |
| `ppg:no_complete_half_height_pulse` | Không có nhịp đủ để đo độ rộng tại 50 % biên độ |
| `ppg:shape_inconsistent` | Tương quan hình dạng nhịp với template dưới `shape_min_correlation` |
| `pat:alignment_unverified`, `pat:clock_unverified`, `pat:upstream_delay_unknown` | Chưa đủ căn cứ thời gian để ghép R với chân sóng; PAT không tính |
| `pat:unmatched_beats`, `pat:too_few_pairs` | Có nhịp không ghép được, hoặc ít cặp R–foot hơn `min_beats` |
| `feature:<tên>:arithmetic_nonfinite` | Một đặc trưng tính ra không hữu hạn |

Chỉ số liên tục cho RQ3: `ppg_shape_correlation`, `pat_pair_fraction`, `pat_iqr_ms`, số đỉnh
và số chân sóng.

### 3.2. Cử động (`motion-sqi-v0`, đã có code)

Mỗi cửa sổ có đúng một nhãn: `motion`, `no_motion_detected` hoặc `not_evaluable`. Định nghĩa
theo protocol 7.3 ý 5:

- gia tốc lọc 0,5–10 Hz và gyro lọc thông thấp 10 Hz;
- lấy P95 trên cửa sổ trượt 1 s;
- ngưỡng nháp 0,15 g và 20 °/s.

Chỉ số liên tục: giá trị lớn nhất của P95 trượt, tỷ lệ mẫu vượt ngưỡng.

### 3.3. Cờ của phần cứng V1 (mới ở v1, chưa có code)

Lấy từ STATUS và nội dung packet của Packet Schema V0.2 trong cửa sổ:

| Cờ | Định nghĩa | Ngưỡng đề xuất |
| --- | --- | --- |
| `ppg:adc_saturation` | Tỷ lệ mẫu PPG của từng màu chạm trần ADC. Trần lấy theo độ phân giải trong `0x0A` của `0xD2`, như dòng DC của logger ([packet_logger.md](packet_logger.md)) | > 5 % thời gian cửa sổ, theo protocol 6.1 và 7.3 ý 1 |
| `ppg:alc_overflow` | Có packet PPG mang STATUS bit 6 | Bất kỳ |
| `ecg:lead_off` | Có packet ECG mang STATUS bit 2 | Bất kỳ |
| `afe:fifo_overflow` | Có packet ECG hay PPG mang STATUS bit 0 (mẫu cũ, mất mẫu) | Bất kỳ |
| `stream:gap` | Logger báo khoảng trống của kênh ECG hay PPG trong cửa sổ (`gaps`, `channel_holes` trong `decode.json`) | Bất kỳ |
| `ppg:led_not_locked` | Trạng thái MAX30101 trong cửa sổ không mang mã LED đã khóa (`ppg_led_lock`) | Bất kỳ |

Chỉ số liên tục cho RQ3: tỷ lệ chạm trần theo màu, mức DC theo % thang đo.

## 4. Điều kiện tính được (không phải SQI)

Một lần đo vào phép so sánh chính khi thỏa đủ ba điều kiện:

- có nhãn cuff;
- có đủ đặc trưng PPG của bộ đã khóa (không có cờ `ppg:too_few_feet`,
  `ppg:insufficient_foot_intervals` và mọi đặc trưng PPG hữu hạn);
- tính được PAT (không có cờ `pat:*` làm PAT trống).

Các lần đo không tính được PAT nhưng có PPG vẫn vào phân tích phụ PPG-only trên toàn bộ lần đo
(protocol mục 10).

## 5. Tập loại của phân tích phụ lọc SQI

Đề xuất, chờ G2 xác nhận ngưỡng: loại một lần đo nếu nó có bất kỳ cờ nào sau đây.

- `motion`;
- `ppg:adc_saturation`, `ppg:alc_overflow`, `ppg:shape_inconsistent`, `ppg:led_not_locked`;
- `ecg:lead_off`, `afe:fifo_overflow`, `stream:gap`;
- `pat:unmatched_beats`.

Lần đo `not_evaluable` về cử động **không** bị loại. Phân tích phụ thứ hai loại thêm các lần đo
này. Không có bước "chọn tập loại tốt nhất".

## 6. Khóa ngưỡng trên G2

Trên bản ghi G2 của thành viên nhóm, chưa có người tham gia, chỉ sau khi có phê duyệt phù hợp:

1. Ghi lúc ngồi yên và lúc cử động theo hướng dẫn có nhãn độc lập.
2. Đặt ngưỡng cử động sao cho lúc ngồi yên gần như không bị gắn cờ.
3. Kiểm `shape_min_correlation` và `min_beats` trên đoạn ngồi yên.
4. Ghi các giá trị, ngày và commit vào file này trước khi thu chính.

Không dùng nhãn BP để chọn ngưỡng.

## 7. Báo cáo

- Theo người và theo nghiệm pháp: số lần đo, tỷ lệ có từng cờ, tỷ lệ không tính được PAT.
- Coverage của phân tích phụ lọc SQI trên toàn bộ lần đo, kèm phân bố |ΔBP| của lần đo bị loại
  so với lần đo được giữ (RQ v0.4 mục 6.D).

## 8. Việc còn lại để có code

- Tính cờ mục 3.3 từ output của logger (`packets.csv`, `decode.json`) theo cửa sổ của từng
  `event_id`.
- Gộp các cờ ở mức cửa sổ thành bảng mức lần đo.
- Test SYNTHETIC cho từng cờ.

Việc này làm sau khi có bản ghi thiết bị đầu tiên (Tuần 8 trở đi).
