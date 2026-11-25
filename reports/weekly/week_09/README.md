# Báo cáo tiến độ Tuần 9

## 1. Tóm tắt công việc của tuần (mục tiêu)

Theo [kế hoạch Tuần 9](../../../docs/plans/WEEK_09.md) (16/11–22/11/2026):

1. Bring-up V1-module khi hàng về: bo Waveshare đứng riêng, bo đế, MAX30001; thử nhanh MAX30101 và
   BMI270; firmware chẩn đoán khi một bước không đạt.
2. Mô phỏng độ nhạy RQ1 v3 (nhiều lần cuff, M6, đo lặp cuff) để quyết số phiên, trần δ và điều kiện
   của M6.
3. Sửa hồ sơ đạo đức, protocol và SAP theo các mục nhóm chốt trong tuần.
4. Rà soát toàn dự án sau Tuần 8; quyết hướng đi cho đánh dấu tay PulseDB.
5. Thời gian ECG–PPG: chốt mốc thời gian ECG nếu breakout không cho `SAMP`; tiêu chí và công cụ chấm
   phép đo đồng bộ.
6. Đo lại RAM của logger trên laptop đã đóng ứng dụng; đọc DUA và gửi yêu cầu truy cập Aurora-BP.
7. Chốt định nghĩa foot cho dữ liệu thiết bị trước pilot.

Không đo trên người.

## 2. Thành viên phụ trách và phân công công việc

| Thành viên | Công việc Tuần 9 |
| --- | --- |
| Đức Anh | Bring-up V1 (bo Waveshare, bo đế, MAX30001, thử nhanh MAX30101 và BMI270); firmware chẩn đoán và chế độ mốc FIFO cho ECG; định nghĩa tải A11 và script lịch tải; áp quyết định không sửa module vào tài liệu phần cứng |
| Linh | Ingest dữ liệu thiết bị (thống kê A3 theo khối, quy tắc 11.4 trong `device_session`); đếm mô hình lỗi trong phân tích RQ1; đo lại RAM logger; Aurora-BP |
| Huy | Mô phỏng độ nhạy v3 và các mục chốt trong SAP; hồ sơ đạo đức, protocol, SAP theo các mục chốt 19/11; rà soát toàn dự án, dừng đánh dấu tay PulseDB; chốt mốc thời gian ECG; kiểm A10 và công cụ phân tích đồng bộ; định nghĩa chân sóng PPG cho dữ liệu thiết bị; kế hoạch Tuần 10 |

## 3. Tóm tắt công việc đã hoàn thành của từng người

### Đức Anh

- **Không sửa module** (d588222, 2026-11-19; nhóm chốt cùng ngày): không thay, gỡ hay cắt linh
  kiện, jumper nào trên bo Waveshare, breakout MAX30001, MAX30101 và BMI270. Điện trở giới hạn dòng
  của cáp điện cực đặt trong một đầu chuyển giắc 3,5 mm ngoài breakout; giá đỡ che LED nguồn và
  đầu Qwiic của MAX30101; BMI270 chạy SPI mà giữ nguyên jumper. Cập nhật trình tự bring-up, mẫu báo
  cáo, checklist, kế hoạch dòng rò và đồng bộ, danh sách mua, checklist an toàn buổi đo.
- **Bring-up bo Waveshare đứng riêng** (e6c096a, 2026-11-20): BU mục 2 đạt (chip, eFuse, bản ghi
  10 phút, ba bản build tạo lỗi, lệnh từ PC); BU mục 1 một phần (cáp ECG, đo thông mạch breakout
  MAX30001 v2). Phát hiện image nạp mang phiên bản cũ khi build tăng dần: thêm yêu cầu build sạch
  trước khi nạp.
- **MAX30001 trên bo đế** (17792bd, 2026-11-21): BU mục 6 (nút t0) đạt; BU mục 7: chip trả `INFO`
  đúng, đọc lại cấu hình 8/8 khớp, nhưng `PLLINT` luôn bật nên bản nghiên cứu báo lỗi PLL. Thêm env
  chẩn đoán `esp32s3_devkitc_ecg_pll_diag` (chạy tiếp sau timeout PLL, in `STATUS`, bit 8 tắt) và
  bộ đếm `PLLINT`. Đếm cạnh bằng PCNT: không có xung `SAMP` 512/s ở chân header nào.
- **Chế độ mốc FIFO cho ECG trong firmware** (0356e5f, 2026-11-21): cờ `BOARD_ECG_FIFO_MODE`, bit 8
  tắt, không ánh xạ `SAMP`, `PLLINT` chỉ đếm, kiểm tốc độ 10 s so với `esp_timer` (± 1 000 ppm) bật
  bit 3 và 5; ba env `ecg_fifo`, `all_real_fifo`, `sync_fifo`. Pilot 190 s trên chip thật: A10 đạt,
  kiểm tốc độ 19 cửa sổ 0 lỗi.
- **Định nghĩa tải A11 và script lịch tải** (31926a1, 2026-11-21; duyệt cùng ngày): tải cao thêm
  ping mỗi 1 s, mark mỗi 5 s và một tiến trình chiếm một lõi CPU; 12 khối 2 phút xen kẽ, mốc ranh
  giới trên đồng hồ thiết bị. Chạy thử 32 s trên bo: 17/17 lệnh có xác nhận.
- **Hai lượt dài mốc FIFO, lead-off và nguồn breakout** (34dfc70, 2026-11-22): lượt 20 phút và lượt
  26 phút có lịch tải đạt A2, A3, A10; mốc ECG lệch theo tải +0,7 µs. Ba đầu bấm nối chung: nhiễu
  nền 0,5–40 Hz 2,6 µV rms nhưng cờ lead-off vẫn bật ở 0,65 V; quét ngưỡng cho VMID khoảng
  1,05–1,10 V. Đo nguồn breakout: ổn áp `3N3` là 3,3 V, chưa tìm thấy điểm 1,8 V.
- **`PLLINT` theo thời gian và theo từng thanh ghi** (787c290, c2cd797, 2026-11-22): phần `PLLINT`
  theo nhịp mẫu đi theo hai sườn của INT2B; tắt INT2B ở chế độ mốc FIFO thì chip qua bước chờ PLL.
  Phần ngẫu nhiên còn lại (khoảng 100–150 đợt/s) không đổi theo thanh ghi nào đã thử.
- **Thử nhanh MAX30101 và BMI270 nối thẳng ESP32** (6b13353, f435e28, 2026-11-22): PPG ngón trỏ thấy
  rõ từng nhịp ở cả ba khe (DC 1–12 % thang vì dòng LED mặc định); trục BMI270 đúng chiều. Tốc độ
  MAX30101 −336 ppm, BMI270 +0,68 % (trong sai số ODR của datasheet). Bỏ đo thước kẹp (lắp thử thấy
  vừa).
- **Firmware MAX30101** (83e9cf5, 2026-11-16): timeout I²C tăng theo kích thước giao dịch.

### Linh

- **Ingest dữ liệu thiết bị** (83e9cf5, 2026-11-16): phần dư mốc theo khối 10 s dùng thống kê của
  A3, cờ `timebase_residual_above_a3`, cột `residual_block_max_us` trong `timebase.csv`; hằng số
  khoảng cách khe MAX30101 dùng chung một chỗ.
- **Phân tích RQ1** (83e9cf5, 2026-11-16): endpoint 10, đếm mô hình lỗi và số người sau MAE.
- **Quy tắc thời gian ECG 11.4 trong `device_session`** (ba06b7b, 2026-11-21): chạy A10 trên mọi
  packet, gắn trạng thái cho từng packet ECG; cửa sổ có packet bị A10 gắn cờ, chưa chấm được (10 s
  đầu chuỗi) hoặc mang bit 3 thì có cờ `ecg:timing_unverified` hay `ecg:afe_error` và không tính
  PAT, đặc trưng PPG vẫn tính. Nâng `device-features-v2`. Test qua logger và `device_session`.
- **RAM logger trên laptop đã đóng ứng dụng** (làm bù ngày 2026-11-25): cùng luồng SYNTHETIC 120 phút
  (819 288 packet), hai lần, sau khi đóng trình duyệt, trình soạn thảo và `wsl --shutdown`. Đỉnh
  logger 895 MB như lần 13/11; RAM trống tối thiểu 10,3–10,5 GB (61–62 %), gấp khoảng 5 lần mức
  2 GB. Bước đóng ứng dụng của protocol 5.1 là đủ, không cần giải mã theo khối
  ([packet_logger.md](../../../docs/protocol/packet_logger.md)).
- **Aurora-BP** (làm bù ngày 2026-11-25): đọc các trang công khai (GitHub, Zenodo, bài báo), ghi nguồn,
  điều khoản chính của DUA, mô tả dữ liệu, bảng đối sánh biến và nội dung soạn sẵn cho phần mục đích
  sử dụng ([aurora_bp_access_and_variables.md](../../../docs/literature/aurora_bp_access_and_variables.md)).
  Bộ đầy đủ trên Zenodo đang ghi là mở, tải trực tiếp; tải hay dùng dữ liệu là chấp nhận DUA. DUA cấm
  tái phân phối, tái định danh và **kết hợp với nguồn dữ liệu khác**. Chưa tải dữ liệu, chưa chấp
  nhận DUA; số cặp trong người dùng được chỉ biết sau khi có dữ liệu.

### Huy

- **Rà soát toàn dự án sau Tuần 8** (83e9cf5, 2026-11-16): trạng thái khóa LED theo cửa sổ
  `[t0 − 30 s, t0)` và cờ `ppg:led_not_locked`; cờ `pat:no_foot_span` thay vì dừng lỗi; lọc
  zero-phase Butterworth bậc 2 trong `device-session-v1`; cập nhật SAP v1, SQI v1, quy ước dữ liệu,
  hướng dẫn pipeline theo code; kịch bản bài báo bỏ điều kiện r < 0,3 khỏi P C.
- **Dừng đánh dấu tay PulseDB** (83e9cf5, 2026-11-16): dừng ở 69/80 đoạn vì định nghĩa foot không
  vận hành được nhất quán khi đáy có gờ hoặc đáy phẳng; không làm B4 trên PulseDB. Ghi là thẩm định
  chưa hoàn tất (chưa chạy `compare`, `repeat` hay `gate`), [tài liệu mốc Tuần 5](../../../docs/protocol/week05_fiducials_pat_validity.md)
  mục 9.7.
- **Cách ghi nhận rà soát** (16e9103, 2026-11-17): đổi cách ghi trong tài liệu thành "thảo luận".
- **Mô phỏng độ nhạy RQ1 v3** (0f5595a, 2026-11-19): thêm M6, đo lặp cuff và so với BP thật; luật
  đọc kết quả R1–R4 ghi trong config trước khi chạy. Kết quả và các mục chốt ở mục 5.1.
- **Hồ sơ đạo đức, protocol và SAP theo các mục chốt 2026-11-19** (7f295c8, 2026-11-21): mỗi người
  2 phiên, phiên 2 cách phiên 1 từ 7 ngày tới 4 tuần; khóa dữ liệu 21/05/2027, đề tài kết thúc
  tháng 7/2027; mục 11 tùy chọn chia sẻ dữ liệu qua kho có kiểm soát; thêm 2 người trực; đầu chuyển
  ECG có điện trở giới hạn dòng và giá đỡ bo cổ tay; đề cương nộp hội đồng theo SAP v1 (khoảng tin
  cậy, Holm, quy tắc và trần δ, P2); README hồ sơ có bảng thay đổi và việc còn thiếu trước khi nộp.
- **Chốt mốc thời gian ECG khi breakout không có `SAMP`** (87af166, 2026-11-21; sau hai vòng phản
  biện độc lập): dùng mốc đọc FIFO, bit 8 luôn tắt, chỉ kiểm ΔPAT giữa các phiên trên bo này; thêm
  A10 (phần dư từng packet ≤ 0,5 ms) và A11 (offset theo tải ≤ 0,3 ms); A8 không đánh giá được.
  Cập nhật Packet Schema V0.2 mục 7, câu hỏi nghiên cứu và [kế hoạch đo đồng bộ](../../../hardware/test_reports/sync_10min_test_plan.md)
  mục 11.
- **Kiểm A10** (ae96277, 2026-11-21): `ecg-anchor-residual-v1`, với mỗi packet ECG khớp đường thẳng
  trên 10 s packet hợp lệ ngay trước; lệch quá 0,5 ms thì gắn cờ và cắt chuỗi.
- **Công cụ phân tích đồng bộ** (695821b, 2026-11-21; 974fb38, 2026-11-22): `sync-analysis-v1` tính
  độ trễ L từng kênh và offset ECG–PPG từ xung kích thích chung, chấm A1–A11 cho một lượt và A5
  trên 10 lượt; `sync-analysis-v2` thêm mô hình thời gian theo đoạn 60 s khi A3 trượt.
- **Kế hoạch Tuần 10** (0d67079, 2026-11-22).
- **Định nghĩa chân sóng PPG cho dữ liệu thiết bị** (làm bù ngày 2026-11-25, sau hai vòng phản biện độc
  lập): số đếm MAX30101 giảm khi máu tăng nên chốt `ppg_polarity = −1`, bộ sinh SYNTHETIC lên v2; định
  nghĩa `device-foot-v1` (sườn lên đầu tiên sau R, mức đáy tại đầu sườn, tiếp tuyến giao cắt, mỗi R
  một trạng thái) có quy tắc cho đáy có gờ, đáy phẳng, sóng sau cao hơn, kèm hình ví dụ SYNTHETIC, và
  đã cài cho PAT (`device-features-v4`). Thử trên bản ghi bring-up ngón tay: chân sóng tới đỉnh 119 ms
  (SD 4,9 ms) khi lật dấu, 334 ms khi không lật. Chưa khóa: cần bản ghi cổ tay có cả ECG và PPG thật
  ([device_ppg_foot_definition_v1.md](../../../docs/protocol/device_ppg_foot_definition_v1.md)).

## 4. Danh mục sản phẩm đầu ra và đường dẫn

| STT | Sản phẩm | Người làm | Đường dẫn |
| --- | --- | --- | --- |
| 1 | Không sửa module: đầu chuyển ECG, giá đỡ MAX30101, BMI270 giữ jumper | Đức Anh | [custom_board_proposal.md](../../../configs/hardware/custom_board_proposal.md), [v1_bringup_procedure.md](../../../hardware/test_reports/v1_bringup_procedure.md), [purchase_list_v1_module.md](../../../hardware/bom/purchase_list_v1_module.md) |
| 2 | Báo cáo bring-up V1 (BU mục 1, 2, 6, 7; mốc FIFO; MAX30101 và BMI270) | Đức Anh | [2026-11-20_v1_bringup.md](../../../hardware/test_reports/2026-11-20_v1_bringup.md) mục 1–10 |
| 3 | Firmware: env chẩn đoán PLL, chế độ mốc FIFO, kiểm tốc độ ECG, chẩn đoán lead-off, INT2B tắt | Đức Anh | [firmware/README.md](../../../firmware/README.md), [ecg_rate.c](../../../firmware/app/ecg_rate.c), [platformio.ini](../../../firmware/platformio.ini), [test_firmware_ecg_rate.py](../../../tests/test_firmware_ecg_rate.py) |
| 4 | Định nghĩa tải A11, script lịch tải | Đức Anh | [sync_10min_test_plan.md](../../../hardware/test_reports/sync_10min_test_plan.md) mục 11.7, [sync_load_schedule.py](../../../scripts/sync_load_schedule.py), [test_sync_load_schedule.py](../../../tests/test_sync_load_schedule.py) |
| 5 | Ingest: thống kê A3 theo khối; quy tắc 11.4 trong `device_session` | Linh | [session_ingest.py](../../../software/device/session_ingest.py), [device_session.py](../../../scripts/device_session.py), [test_device_ingest.py](../../../tests/test_device_ingest.py) |
| 6 | Mô phỏng độ nhạy RQ1 v3, các mục chốt trong SAP | Huy | [rq1_sensitivity_v3.json](../../../configs/analysis/rq1_sensitivity_v3.json), [rq1_sensitivity.py](../../../software/evaluation/rq1_sensitivity.py), [rq1_sensitivity_v3/](rq1_sensitivity_v3/summary.md), [sap_v1.md](../../../docs/protocol/sap_v1.md) mục 8, 9, 13 |
| 7 | Hồ sơ đạo đức, protocol, SAP theo các mục chốt 19/11 | Huy | [docs/ethics/](../../../docs/ethics/README.md), [protocol_outline_v0.2.md](../../../docs/protocol/protocol_outline_v0.2.md), [sap_v1.md](../../../docs/protocol/sap_v1.md) |
| 8 | Chốt mốc đọc FIFO cho ECG, tiêu chí A10, A11 | Huy | [sync_10min_test_plan.md](../../../hardware/test_reports/sync_10min_test_plan.md) mục 11, [Packet_Schema_V0.2.md](../../../configs/hardware/Packet_Schema_V0.2.md) mục 7 |
| 9 | Kiểm A10, công cụ phân tích đồng bộ v1, v2 | Huy | [ecg_anchor_residual.py](../../../software/device/ecg_anchor_residual.py), [check_ecg_anchor_residual.py](../../../scripts/check_ecg_anchor_residual.py), [sync_analysis.py](../../../software/device/sync_analysis.py), [analyze_sync.py](../../../scripts/analyze_sync.py), [test_sync_analysis.py](../../../tests/test_sync_analysis.py) |
| 10 | Dừng đánh dấu tay PulseDB | Huy | [week05_fiducials_pat_validity.md](../../../docs/protocol/week05_fiducials_pat_validity.md) mục 9.7 |
| 11 | Kế hoạch Tuần 10 | Huy | [WEEK_10.md](../../../docs/plans/WEEK_10.md) |
| 12 | RAM logger trên laptop đã đóng ứng dụng | Linh | [packet_logger.md](../../../docs/protocol/packet_logger.md) |
| 13 | Aurora-BP: truy cập, DUA, đối sánh biến | Linh | [aurora_bp_access_and_variables.md](../../../docs/literature/aurora_bp_access_and_variables.md) |
| 14 | Hướng tín hiệu PPG, định nghĩa chân sóng `device-foot-v1`, PAT neo theo R | Huy | [device_ppg_foot_definition_v1.md](../../../docs/protocol/device_ppg_foot_definition_v1.md), [fiducials.py](../../../software/signal_processing/fiducials.py), [features.py](../../../software/device/features.py), [device_session_v1.json](../../../configs/data/device_session_v1.json), [test_feet_after_r.py](../../../tests/test_feet_after_r.py), [device_foot_v1_cases.svg](../../figures/device_foot_v1_cases.svg) |

## 5. Tóm tắt các nội dung chuyên môn chính

### 5.1. Mô phỏng độ nhạy RQ1 v3 và các mục chốt 2026-11-19

Chi tiết: [rq1_sensitivity_v3/summary.md](rq1_sensitivity_v3/summary.md),
[SAP v1](../../../docs/protocol/sap_v1.md) mục 9 (kết quả 11). Chỉ là mô phỏng theo giả định,
không có dữ liệu người.

- **R1 (độ chính xác) đạt ở mọi mức nhiễu cuff**, kể cả 25 × 2, nên R1 không phân biệt được các
  thiết kế. Giữ R1 như đã ghi, không sửa sau khi xem kết quả.
- **Điểm nghẽn là vượt zero-change**, không phải độ rộng CI của d: ở 32 × 2, nhiễu 5 mmHg, kịch bản
  "strong", CI của d nằm dưới 0 ở 82 % nghiên cứu nhưng CI của d⁰ chỉ ở 21 %. P(kết luận chính)
  0,19 (SBP), 0,10 (DBP), dưới mức báo động 0,50 của R2.
- **Đo lặp cuff giúp ít** (thêm 0–0,11). **M6 làm P(kết luận chính) tăng mạnh**, phần lớn nhờ
  zero-change kém ở M6, kể cả khi PAT không thêm gì ở M6.
- **Nhiễu cuff lớn làm δ theo quy tắc tăng tới 3,5 mmHg** và biến một lợi ích thật thành "tương
  đương".

Nhóm chốt 2026-11-19, báo thầy: mỗi người 2 phiên; trần δ_SBP ≤ 2 mmHg, δ_DBP ≤ 1,5 mmHg; điều
kiện để M6 vào endpoint chính (d, d⁰ trên M0–M2 báo riêng, dᴾ vẫn bắt buộc, tỷ trọng pha cố định
trước pilot); đo lặp cuff không chọn chỉ vì độ nhạy; ưu tiên máy cuff có validation và SD lặp lại
nhỏ. Cùng ngày nhóm chốt: không sửa module, đề tài kéo dài tới đầu tháng 7/2027, thêm 2 người trực,
mục tùy chọn chia sẻ dữ liệu.

### 5.2. Breakout MAX30001 v2: không có `SAMP`, `PLLINT` luôn bật

- Chip lấy mẫu đúng 512 sps (lệch khoảng +3 ppm so với `esp_timer`) dù `PLLINT` luôn bật.
- Đếm cạnh ở hai chân header chỉ thấy nhịp đọc FIFO 32 Hz, không có xung `SAMP` 512/s, kể cả khi
  đổi vai INTB/INT2B. Mốc `SAMP` (bit 8) vì vậy không dùng được trên bo này.
- Không mua được bo thứ hai. Sau hai vòng phản biện độc lập, nhóm chốt dùng mốc đọc FIFO
  (2026-11-21): chỉ kiểm ΔPAT giữa các phiên trên bo này; A10, A11 thay cho A8, A8 không đánh giá
  được. Hai lượt dài đạt A2, A3, A10 với biên rộng.
- Phần `PLLINT` theo nhịp mẫu đi theo sườn INT2B; tắt INT2B ở chế độ mốc FIFO (2026-11-22). Phần
  ngẫu nhiên còn lại chưa rõ nguyên nhân; hỏi hãng trong issue GitHub.

### 5.3. Dừng đánh dấu tay PulseDB

Đánh được 69/80 đoạn, R ổn định; foot không đánh được nhất quán vì đáy có gờ hoặc đáy phẳng cho
hai điểm ứng viên cách nhau 50–370 ms, và 164 nhịp như vậy được chọn gần như chia đôi. Nhóm dừng
ngày 2026-11-16, không làm B4 trên PulseDB. Mốc cho PAT sẽ thẩm định trên dữ liệu thiết bị với một
định nghĩa foot chốt trước, có hình ví dụ và thử trước khi khóa.

## 6. Kết quả kiểm tra kỹ thuật

### 6.1. Kiểm tra toàn repo

Chạy lại ngày 2026-11-25 trên commit cuối Tuần 9 (`c2cd797`, bản checkout sạch): `ruff check .`
sạch; `pytest -q` 1.478 đạt, 1 bỏ qua (tạo symlink cần quyền trên Windows), test firmware chạy
bằng trình dịch C `ziglang`; `scripts/check_environment.py` và `pip check` đạt.

### 6.2. Bring-up

| Hạng mục | Kết quả |
| --- | --- |
| Bo Waveshare đứng riêng (BU mục 2) | Đạt: chip, eFuse, bản ghi 10 phút, ba bản build tạo lỗi, lệnh từ PC |
| Nút t0 (BU mục 6) | Đạt |
| MAX30001 trên bo đế (BU mục 7) | `INFO` đúng, cấu hình 8/8 khớp; `PLLINT` luôn bật; không có `SAMP` |
| Mốc đọc FIFO, lượt 20 phút / lượt 26 phút có lịch tải | A2 +3,4 / +3,5 ppm; A3 22 / 13 µs; A10 0 cờ, phần dư lớn nhất 275 / 316 µs |
| Ba đầu bấm nối chung | Nhiễu nền 0,5–40 Hz 2,6 µV rms; cờ lead-off vẫn bật ở 0,65 V |
| MAX30101, BMI270 nối thẳng ESP32 | PPG ngón tay rõ ở ba khe; trục BMI270 đúng; tốc độ −336 ppm và +0,68 % |

## 7. Mốc đóng Tuần 9 và việc chuyển sang Tuần 10

Đánh giá ngày 2026-11-22 theo mục "Mốc đóng tuần" của
[kế hoạch Tuần 9](../../../docs/plans/WEEK_09.md).

| Mốc | Trạng thái | Người xử lý | Chuyển sang |
| --- | --- | --- | --- |
| Bring-up bo Waveshare, bo đế, MAX30001 | **Đạt phần lớn:** BU mục 2, 6 đạt; BU mục 7 chạy được với mốc đọc FIFO; nguồn AVDD/DVDD của breakout chưa rõ | Đức Anh | Tuần 10: nguồn breakout, đầu chuyển ECG, mạch chia áp kích thích |
| Phần A checklist (ô làm tay) | **Đã đi qua khi bring-up:** dụng cụ, cáp USB-C, nút BOOT/RESET dùng thực tế ngày 20–22/11; mạch đo MD thuộc phần đo dòng rò, tạm dừng từ 2026-11-22 | Đức Anh | — |
| Đối chiếu IEC 60601-1, người duyệt dòng rò | **Tạm dừng** theo quyết định ngày 2026-11-22 | Đức Anh | — |
| MAX30101, BMI270 trên bo cổ tay | **Chưa:** mới thử nối thẳng; chưa hàn | Đức Anh | Tuần 10: hàn bo cổ tay, BU mục 8 |
| Mô phỏng độ nhạy v3 và quyết định | **Đạt:** chạy, chốt số phiên, trần δ, điều kiện M6 (2026-11-19) | Huy | Tuần 10: phương án C2 và mô tả M6, quyết 04/12 |
| Hồ sơ đạo đức theo các mục chốt 19/11 | **Đạt phần `.md`** (7f295c8); bản Word chưa đối chiếu | Huy | — (bỏ khỏi Tuần 10 ngày 2026-11-25) |
| Chốt định nghĩa foot cho dữ liệu thiết bị | **Đạt phần định nghĩa** (làm bù 2026-11-25): hướng tín hiệu chốt; định nghĩa có quy tắc cho các trường hợp khó, hình ví dụ, đã thử trên bản ghi ngoài tập thẩm định và đã cài. **Khóa** cần bản ghi cổ tay có ECG và PPG thật | Huy | Khóa: sau khi hàn bo cổ tay và chỉnh dòng LED |
| RAM logger trên laptop đã đóng ứng dụng | **Đạt** (làm bù 2026-11-25): RAM trống tối thiểu 10,3 GB | Linh | — |
| Aurora-BP: đọc DUA, gửi yêu cầu truy cập | **Đạt phần đọc DUA và đối sánh biến** (làm bù 2026-11-25). Không cần gửi yêu cầu: bộ dữ liệu đang mở trên Zenodo, tải là chấp nhận DUA; nhóm quyết việc tải và ai đứng tên PI | Linh | Tuần 10: quyết tải hay không, số cặp, quyết 11/12 |

**Đường găng** Tuần 10 là G2 trên bàn (06/12), phụ thuộc máy hàn, oscilloscope và nguồn của
breakout MAX30001.
