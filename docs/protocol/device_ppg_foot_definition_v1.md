# Chân sóng PPG cho dữ liệu thiết bị (`device-foot-v1`, bản nháp)

> **Trạng thái (2026-11-25):** mục 2 (hướng tín hiệu) **chốt và đã cài**. Mục 3 **đã cài** cho PAT
> của dữ liệu thiết bị (`fiducials.feet_after_r`, `rise-after-r-v1`, `device-features-v4`; config
> `pat_foot` mang trạng thái `DRAFT_NOT_LOCKED`) sau hai vòng phản biện độc lập, nhưng các ngưỡng và
> cả định nghĩa vẫn là **bản nháp, chưa khóa**: chỉ khóa sau khi thử trên bản ghi cổ tay có cả ECG
> thật và PPG thật (mục 6), theo [protocol](protocol_outline_v0.2.md) mục 8.1. Đặc trưng chỉ dùng
> PPG vẫn dùng chân sóng `tangent` của `features-sqi-v2`. Không chọn hay chỉnh định nghĩa theo huyết
> áp, theo ΔBP hay theo dữ liệu thẩm định.

## 1. Vì sao cần

- Đánh dấu tay trên PulseDB dừng ngày 2026-11-16: định nghĩa "điểm cực tiểu ngay trước sườn lên
  tâm thu" không vận hành được khi đáy có gờ hoặc đáy phẳng. Hai điểm ứng viên cách nhau 50–370 ms
  và người đánh dấu chọn gần như chia đôi ([tài liệu mốc Tuần 5](week05_fiducials_pat_validity.md)
  mục 9.7).
- Protocol mục 8.1 yêu cầu: trước khi đánh dấu tay trên dữ liệu thiết bị phải chốt một định nghĩa
  chân sóng có quy tắc cho các trường hợp này, kèm hình ví dụ, và thử trên bản ghi ngoài tập thẩm
  định trước khi khóa.
- PAT = chân sóng PPG − đỉnh R, trên cùng một đồng hồ MCU (ECG 512 sps, PPG 200 sps). Endpoint
  chính dùng ΔPAT trong cùng người giữa hai phiên: một lệch cố định giữa hai định nghĩa triệt tiêu,
  còn một lệch **thay đổi giữa hai phiên** thì đi thẳng vào kết quả.

## 2. Hướng tín hiệu (chốt 2026-11-25, đã cài)

- Số đếm của MAX30101 là ánh sáng phản xạ về; máu tăng ở thì tâm thu hấp thụ nhiều hơn nên số đếm
  **giảm**. PPG thô của thiết bị vì vậy lộn ngược: lên chậm, xuống gắt (bản ghi bring-up ngày
  2026-11-22 và 2026-11-24, ngón tay và cổ tay).
- `configs/data/device_session_v1.json`: `ppg_polarity = −1`, lật PPG trước mọi bước tìm mốc.
  Bộ sinh SYNTHETIC (`synthetic-device-session-v2`) sinh số đếm giảm theo mạch như thiết bị, còn ánh
  sáng của xung kích thích đồng bộ vẫn làm số đếm tăng; `SessionSpec(ppg_raw_inverted=False)` tạo
  lại số đếm thẳng của v1. Mức DC, kiểm bão hòa ADC và phần hiển thị DC dùng số đếm thô, không lật.
- Chọn theo vật lý của phép đo và hình dạng sóng, không theo PAT, độ phân tán của nó hay huyết áp.
  Test kiểm riêng bộ sinh (số đếm giảm theo mạch, ánh sáng kích thích làm số đếm tăng) và config
  (lật sai thì chân sóng lệch khoảng 175 ms), để một lỗi dấu ở cả hai chỗ không lọt qua.

## 3. Định nghĩa chân sóng (bản nháp, đã cài)

Tín hiệu: PPG đã lật (mục 2), lọc zero-phase Butterworth bậc 2, 0,5–8 Hz trong từng cửa sổ, như
`device-session-v1`. Các giá trị trong ngoặc là bản nháp của config `pat_foot`.

1. **Khoảng tìm của mỗi R:** [R, min(R kế tiếp, R + 0,9 s)).
2. **Thang biên độ:** trung vị, qua mọi R của cửa sổ, của biên độ cục bộ (lớn nhất trừ nhỏ nhất)
   trong khoảng tìm. Một nhiễu lớn ở xa không đổi thang của các nhịp khác.
3. **Đoạn đi lên:** chuỗi bước có độ dốc tiến dương. Hai đoạn cách nhau không quá 2 bước (10 ms ở
   200 sps) mà phần không đi lên chỉ tụt không quá 2 % thang được nối thành một và giữ điểm bắt đầu
   của đoạn đầu, để lượng tử hóa hay một bước phẳng không tách một sườn lên và đẩy B lên cao. Khuyết
   thật giữa hai sóng dài hơn hoặc sâu hơn nên không bị nối.
4. **Sườn lên tâm thu:** đoạn đi lên **đầu tiên** bắt đầu trong khoảng tìm và lên ít nhất 30 % thang.
   Không chọn theo đỉnh cao nhất: sóng sau (phản xạ) có thể cao hơn sóng tâm thu. Một đoạn đủ điều
   kiện xuất hiện **sau** sườn đã chọn không làm nhịp mơ hồ.
5. **Điểm A:** bước dốc nhất của sườn đó (giữa các bước dốc bằng nhau). **Mức B:** giá trị tại điểm
   bắt đầu của chính sườn đó. **Chân sóng:** giao điểm của tiếp tuyến tại A với đường ngang ở mức B.
6. **Trạng thái mỗi R** (mỗi R một bản ghi, giữ lý do bị loại):
   - `ok`: chân sóng trong [R + 80 ms, R + 400 ms] (giới hạn áp lên **chân sóng ngoại suy**);
   - `out_of_range`: chân sóng ngoài khoảng đó;
   - `no_rise`: không có đoạn đủ điều kiện;
   - `ambiguous`: một đoạn đi lên **trước** sườn đã chọn, lên từ 15 % tới dưới 30 % thang, cũng cho
     chân sóng trong khoảng (có thể là điểm bắt đầu thật); hoặc chân sóng rơi vào hay sau R kế tiếp
     (không biết thuộc R nào); hoặc chân sóng không sau chân sóng của nhịp trước;
   - `edge`: chân sóng trong `edge_s` đầu cửa sổ, sườn chạm cuối cửa sổ (chưa lên xong), hoặc không có
     đoạn đủ điều kiện khi khoảng tìm bắt đầu trước PPG hay vượt cuối cửa sổ (không phải nhịp mất).

   So với giới hạn 80 ms và 400 ms dùng cùng sai số làm tròn 1e-6 ms như `pat-validity-v1`.

   PAT của các nhịp `ok` qua quy tắc khoảng và MAD của `pat-validity-v1`. Số đếm: R = n_pairs +
   n_out_of_range + n_no_foot (`no_rise`) + n_ambiguous + n_edge. Cờ PAT của lần cuff lấy từ bộ tìm
   này; cờ ghép nhịp của `features-sqi-v2` (`pat:unmatched_beats`, `pat:too_few_pairs`) giữ riêng ở
   `legacy_pat_flags`.
7. **Đặc trưng chỉ dùng PPG** (thời gian lên, độ rộng, biên độ, nhịp tim PPG) không dùng R, để giữ một
   baseline PPG-only độc lập với ECG.

`valley_min` và `d2_max` giữ làm phương pháp phụ được báo cáo, không phải mốc chính.

**Ngưỡng tạo bước nhảy:** cùng hai sóng ở cùng thời điểm, chỉ đổi chiều cao sóng trước: dưới 15 %
thang thì lấy sóng sau, từ 15 % tới dưới 30 % thì mơ hồ, từ 30 % thì lấy sóng trước (test
`test_two_wave_outcome_follows_the_draft_thresholds`). Đây là tính chất của ngưỡng, không sửa được
mà chỉ chọn được ngưỡng; ngưỡng khóa trên bản ghi cổ tay.

## 4. Các trường hợp khó

Hình SYNTHETIC: [device_foot_v1_cases.svg](../../reports/figures/device_foot_v1_cases.svg), tạo bằng
`python scripts/demo_device_foot_cases.py` (test: `tests/test_demo_device_foot_cases.py`). Bốn nhịp
dựng tay, chân sóng đặt ở R + 200 ms. Sườn lên dạng cos nên tiếp tuyến cắt sau điểm bắt đầu 18 ms ở
mọi trường hợp; đó là tính chất của tiếp tuyến giao cắt, giống nhau giữa các trường hợp.

| Trường hợp | Quy tắc | Bản nháp | Code hiện tại (`tangent`) |
| --- | --- | --- | --- |
| Bình thường | — | 218 ms | 218 ms |
| Gờ trước sườn lên (khuyết sâu của nhịp trước, rồi một sóng nhỏ) | B là đáy ngay trước sườn (sau gờ), không phải khuyết sâu hơn | 218 ms | **202 ms**: B lấy ở khuyết sâu, chân sóng sớm hơn |
| Đáy phẳng | Đáy phẳng không đổi mức B; tiếp tuyến không phụ thuộc điểm nào trên đáy | 218 ms | 218 ms |
| Sóng sau cao hơn sóng tâm thu | A trên sườn lên **đầu tiên** sau R | 214 ms | **331 ms**: lấy nhầm sóng sau |

Hệ quả: cách cũ (đáy thấp nhất trước **đỉnh cao nhất**) sai ở hai trường hợp; quy tắc mục 3 giữ
đúng cả bốn và nay là cách tính PAT của dữ liệu thiết bị. Cột "Code hiện tại" là `tangent` của
`features-sqi-v2`, vẫn dùng cho đặc trưng chỉ dùng PPG.

## 5. Thẩm định trên dữ liệu thiết bị (bản nháp)

- **Người đánh dấu không click điểm chân sóng.** Hai người độc lập, không thấy kết quả của bộ tìm và
  không thấy huyết áp, đánh dấu trên mỗi nhịp đủ điều kiện **khoảng thời gian của sườn lên tâm thu**
  hoặc "không xác định". Chấm: chọn sai sóng, bỏ sót, nhịp thừa, đồng thuận giữa hai người, số nhịp bị
  loại. Đây là thẩm định **việc chọn sườn**; nó không cho sai số thời gian độc lập, vì chân sóng của cả
  hai bên đều tính bằng cùng quy tắc tiếp tuyến.
- **Sai số thời gian** lấy từ nguồn khác: phát lại dạng sóng có điểm bắt đầu biết trước (nhiễu, gờ, đáy
  phẳng, sóng sau cao hơn); phép đo đồng bộ trên bàn bằng xung kích thích (độ trễ kênh); độ lặp lại
  nhịp–nhịp lúc nghỉ. Muốn khẳng định độ chính xác sinh lý thì cần thêm một tham chiếu thời gian độc
  lập trên dạng sóng thiết bị.
- Quy tắc chấm và hình ví dụ trên cổ tay phải **cố định trước** khi thẩm định.

## 6. Thử trên dữ liệu phát triển và việc còn lại trước khi khóa

**Đã thử (2026-11-25), code hiện tại, cửa sổ 30 s, ngoài mọi tập thẩm định** (bản ghi bring-up
`runs/bringup_v1/2026-11-22_ppg_real_finger1`, `2026-11-24_all_real_fifo_finger`,
`2026-11-24_all_real_fifo_wrist`; ba bản ghi này là dữ liệu phát triển, không dùng để khóa):

| Bản ghi | Kết quả |
| --- | --- |
| Ngón tay 60 s, xanh, lật dấu | chân sóng → đỉnh tâm thu: `tangent` 119 ms (SD 4,9 ms), `valley_min` 150 (5,6), `d2_max` 125 (6,7) |
| Cùng bản ghi, **không** lật dấu | `tangent` 334 ms (SD 43,7): tìm trên sườn xuống của mạch thật |
| Ngón tay 120 s, đỏ/IR | chân sóng → đỉnh khoảng 124 ms; màu xanh 351 ms vì sóng sau cao hơn được lấy làm đỉnh (trường hợp cuối của mục 4) |
| `tangent` − `valley_min` từng nhịp, ngón tay | trung vị 30–32 ms, p90 32–35 ms, > 50 ms ở 0–2 trên khoảng 130 nhịp |
| Cổ tay (dòng LED mặc định, DC 0,4–13 % thang) | ít nhịp tìm được, lệch > 50 ms ở 9–20 trên 24–55 nhịp: tín hiệu quá yếu để đánh giá |

**Giới hạn đã biết của tiếp tuyến giao cắt:** chân sóng nằm sau điểm bắt đầu một khoảng tỉ lệ với
độ dài sườn lên (với sườn dạng cos: 0,18 × độ dài sườn, ví dụ 18 ms cho 100 ms và 36 ms cho 200 ms;
test `test_tangent_offset_grows_with_the_rise_width`). Lệch cố định triệt tiêu trong ΔPAT, nhưng nếu
hình dạng sườn lên đổi giữa hai phiên (vị trí đeo, lực áp, bộ lọc) thì phần đổi đi thẳng vào ΔPAT.
Phải báo kèm ΔPAT một chỉ số thời gian lên của sườn tâm thu theo phiên. Chưa có bản ghi nào có cả ECG
thật và PPG thật, nên bộ tìm mục 3 mới chỉ chạy trên SYNTHETIC.

**Việc còn lại trước khi khóa:**

1. Ghi cổ tay có ECG sau khi chỉnh dòng LED (bring-up mục 8): độ phủ nhịp và số nhịp theo từng trạng
   thái, cả sau khi tháo và đeo lại; độ nhạy theo biên cửa sổ; thay đổi của `tangent` − `valley_min`
   và của thời gian lên giữa hai lần đeo. Huyết áp không được xem.
2. Chốt ba ngưỡng của mục 3 (30 %, 15 %, 2 bước / 2 %) trên dữ liệu phát triển ở bước 1, không theo
   PAT hay BP; nếu đổi thì tăng phiên bản.
3. Kiểm hướng tín hiệu tự động theo phiên (trung vị PPG thô căn theo R) để gắn cờ khi hướng khác dự
   kiến hoặc không rõ.
4. Kiểm bão hòa ở cả mức dưới của ADC (hiện `ppg:adc_saturation` chỉ kiểm trần).
5. Phát lại dạng sóng có điểm bắt đầu biết trước (nhiễu, gờ, đáy phẳng, sóng sau cao hơn, sườn dài
   ngắn khác nhau) qua đúng bộ lọc của pipeline, báo ΔPAT biểu kiến và tỉ lệ nhịp giữ lại.
6. Báo độ phủ theo cặp phiên, không chỉ theo nhịp. Màu xanh vẫn là màu chính đã chọn trước.
