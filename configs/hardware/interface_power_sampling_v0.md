# Nguồn, mức logic, giao tiếp và cấu hình lấy mẫu — V1-module

## 1. Sơ đồ khối

Sơ đồ khối của V1-module (bo đế, bo cổ tay, cáp, bus, nguồn, điện cực):
[hardware_diagram_v1.svg](hardware_diagram_v1.svg).

Nguồn: DevKitC nhận 5 V qua USB từ laptop chạy pin (không cắm sạc); LDO 3,3 V của
DevKitC cấp cho breakout MAX30001 và qua cáp cho bo cổ tay. Bo SparkFun MAX30101 tự
tạo 1,8 V và VLED+ 5 V. V1 không có pin LiPo, mạch sạc hay DC-DC
([custom_board_proposal.md](custom_board_proposal.md) A.5).

## 2. Bảng nguồn và mức logic

| Khối | Linh kiện / module | Cấp vào module | Rail bên trong IC | Mức logic tại MCU | Nguồn |
| --- | --- | --- | --- | --- | --- |
| MCU | ESP32-S3-DevKitC-1-N8R8 | USB 5 V, hoặc chân 5V, hoặc chân 3V3 — **ba cách loại trừ nhau**, không cấp đồng thời | 3,3 V qua LDO trên DevKitC | GPIO 3,3 V; VIH ≥ 0,75·VDD ≈ 2,48 V; VIL ≤ 0,25·VDD ≈ 0,83 V | DevKitC User Guide v1.1; ESP32-S3 datasheet v2.2 |
| ECG AFE | ProtoCentral MAX30001 breakout | VDD 3,3 V tại header [BRK] | AVDD = DVDD 1,1–2,0 V; OVDD 1,65–3,6 V (MAX30001 tr. 8); breakout cấp 1,8 V từ LDO AP2112K-1.8 [BRK] | SPI qua TXB0108, logic theo VDD = 3,3 V [BRK]. Ở chân IC: VIH ≥ 0,7·OVDD (tr. 8) | MAX30001 tr. 8; [BRK] |
| PPG AFE | MAX30101, bo SparkFun SEN-16474 (chốt 2026-10-22) | 3,3 V; bo tự tạo VDD 1,8 V (LDO SP6214) và VLED+ 5 V (boost PAM2401) ([custom_board_proposal.md](custom_board_proposal.md) A.4) | VDD 1,7–2,0 V. VLED+ 3,1–5,0 V cho đỏ/IR và **4,5–5,5 V cho LED xanh** (MAX30101 tr. 2) | SDA, INT open-drain; SCL/SDA của IC có VIH ≥ 0,7·VDD và chịu được tới 6 V (tuyệt đối tối đa "All other pins", tr. 2). Bo SparkFun chuyển mức I²C bằng MOSFET, kéo lên 2,2 kΩ ở phía 3,3 V; INT kéo lên 4,7 kΩ lên 3,3 V (A.4). Kiểm mức thực khi nhận hàng | MAX30101 tr. 2, 5, 9; A.4 |
| IMU | BMI270 (SparkFun Qwiic 6DoF, bo cổ tay) | 3V3 qua cáp | VDD 1,71–3,6 V; VDDIO 1,2–3,6 V, **bắt buộc cấp** cho giao tiếp; tụ 100 nF tại VDDIO và VDD | Theo VDDIO | BST-BMI270-DS000-08 |

Lưu ý:

- LED xanh của MAX30101 (thường dùng cho PPG cổ tay) cần VLED+ 4,5–5,5 V. Bo
  SparkFun lấy VLED+ từ boost PAM2401 trên bo, đặt 5,1 V danh định: trong dải
  của LED xanh nhưng vượt 0,1 V dải 3,1–5,0 V bảo đảm PSRR cho đỏ/IR. Chốt
  2026-10-24: giữ nguyên, không sửa bo SparkFun. Phải đo khi không tải và dưới tải ([custom_board_proposal.md](custom_board_proposal.md)
  A.6 mục 3).
- MAX3010x cần tụ bypass ≥ 1 µF sát chân VLED+ và đường cấp có trở kháng ≪ 1 Ω, để
  xung dòng LED không thành nhiễu quang (MAX30102 tr. 23).
- BMI270 có trong V1-module (bo cổ tay, SPI bus 2); packet V0.2 có kênh IMU
  (`Packet_Schema_V0.2.md` mục 2).

## 3. Giao tiếp và pin map

Pin map chuẩn của V1 là bảng A.7 của
[custom_board_proposal.md](custom_board_proposal.md) (KiCad V1-module, chốt
2026-10-23); firmware dùng cùng bảng trong `firmware/boards/board_v1_module.h`.
Pin map V1 cũ (`Pin_Map_V1.md`, `V1.SchDoc` trên nhánh `dev/ducanh`: MAX30001 và
BMI270 chung SPI, không nối INT2B) không dùng nữa. Mọi GPIO của bảng A.7 đều có
trên header DevKitC và không trùng chân strapping (0, 3, 45, 46), PSRAM octal
(35–37), USB (19, 20) hay UART0 (43, 44).

Ghi chú giao tiếp theo bảng A.7:

| Bus / tín hiệu | GPIO | Ghi chú |
| --- | --- | --- |
| SPI bus 1, MAX30001 (SCLK, MOSI, MISO, CS) | 15, 16, 17, 7 | Bus riêng, nên đường MISO không dùng chung với thiết bị khác qua TXB0108 luôn bật của breakout [BRK]. Đi qua GPIO matrix, chạy 4 MHz (A.2); MAX30001 cho SCLK tới 12 MHz, SPI mode 0 hoặc 3 (MAX30001 tr. 10, tr. 36). GPIO15/16 trùng XTAL_32K_P/N, chỉ ảnh hưởng bản hoàn chỉnh (mục 6 ý 2) |
| MAX30001 INTB | 21 | Tích cực mức thấp. Mặc định open-drain kéo lên nội 125 kΩ; đi qua TXB0108 nên firmware đặt CMOS (`INTB_TYPE = 01`, tr. 43; A.2) |
| MAX30001 INT2B | 47 | Xung `SAMP` ở tốc độ dữ liệu ECG (tr. 42, tr. 44): đánh dấu lúc mẫu vào FIFO, không phải lúc lấy mẫu analog (`Packet_Schema_V0.1.md` mục 5.2). Chạy 3,3 V với module WROOM-1-N16R8/N8R8 (A.6 mục 4) |
| I²C bus 1, MAX30101 (SDA, SCL) | 8, 9 | Bus riêng, tối đa 400 kHz; địa chỉ ghi/đọc 0xAE/0xAF (MAX30101 Rev 2, Bảng 17, tr. 30). Kéo lên trên bo SparkFun (A.4) |
| MAX30101 INT | 18 | Open-drain, tích cực mức thấp; bo SparkFun kéo lên 4,7 kΩ lên 3,3 V (A.4) |
| SPI bus 2, BMI270 (SCK, MOSI, MISO, CS) | 12, 11, 13, 10 | Bus riêng, bắt đầu 1 MHz, lên 2 MHz sau khi đo scope (A.2); điện trở 33 Ω nối tiếp trên SCK, MOSI, CS. Firmware dùng `SPI3_HOST` có DMA (đọc 170 frame trong một giao dịch), chế độ 0, CS phần cứng (chốt 2026-10-25) |
| BMI270 INT1 | 14 | |
| Nút `t0`, LED trạng thái | 4, 5 | Nút tích cực mức thấp, kéo lên 10 kΩ và 100 nF trên bo đế |

**MAX30001 không có chân SYNCH**: danh sách chân (tr. 18–19) không có chân này;
`SYNCH` là lệnh ghi qua SPI vào thanh ghi 0x09 (tr. 46). Kế hoạch chân trong
`BOM_V0.1.xlsx` từng ghi "SYNCH của MAX30001" ở GPIO7. Chân phần cứng có ích cho
đồng bộ là INT2B (xung `SAMP`).

## 4. Khả năng lấy mẫu theo linh kiện

| Linh kiện | Tốc độ cấu hình được | Đạt 500 Hz? | Đạt 512 Hz? | Đạt 125/128 Hz? | Nguồn |
| --- | --- | --- | --- | --- | --- |
| MAX30001 ECG | FMSTR 00 (32 768 Hz): 512 / 256 / 128 sps. FMSTR 01 (32 000 Hz): 500 / 250 / 125 sps. FMSTR 10/11: 200 / 199,8 sps | Có (FMSTR 01) | Có (FMSTR 00) | Có 125 hoặc 128 tùy FMSTR | MAX30001 tr. 49, Bảng 26; tr. 52 |
| MAX30101 / MAX30102 | 50, 100, 200, 400, 800, 1000, 1600, 3200 sps; lấy trung bình trên chip `SMP_AVE` = 1, 2, 4, 8, 16, 32 mẫu | Chỉ bằng 1000 sps lấy trung bình 2 mẫu | Không | 125 bằng 1000 sps lấy trung bình 8; 128 không | MAX30102 tr. 19, Bảng 6; tr. 17, Bảng 3 |

**Tổ hợp tốc độ × độ rộng xung được phép** (MAX30102 tr. 23, Bảng 11–12; MAX30101
tr. 29–30, Bảng 15–16):

| Tốc độ (sps) | SpO2 mode: độ rộng xung được phép (µs) | HR mode: độ rộng xung được phép (µs) |
| ---: | --- | --- |
| 50–400 | 69, 118, 215, 411 | 69, 118, 215, 411 |
| 800 | 69, 118, 215 | 69, 118, 215, 411 |
| 1000 | 69, 118 | 69, 118, 215, 411 |
| 1600 | 69 | 69, 118, 215 |
| 3200 | không có | 69 |

Độ rộng xung quyết định độ phân giải ADC: 69 / 118 / 215 / 411 µs ứng với
15 / 16 / 17 / 18 bit (MAX30102 tr. 19, Bảng 7). Nếu chọn tổ hợp không được phép,
chip tự lấy tốc độ cao nhất hợp lệ (tr. 19), nên tốc độ thực khác giá trị đã ghi.

Lưu ý khi chốt:

- **Chế độ LED quyết định số kênh PPG.** Heart Rate mode chỉ dùng LED đỏ; SpO2 mode
  dùng đỏ + IR; multi-LED mode chia mỗi mẫu thành tối đa bốn khe `SLOT1`–`SLOT4`
  ở **cả** MAX30101 và MAX30102. MAX30102 mỗi khe chỉ chọn đỏ hoặc IR; MAX30101
  chọn thêm được xanh (MAX30102 tr. 18, 21; MAX30101 tr. 19, 21). Các khe trong một
  mẫu lệch nhau 427–1 107 µs tùy độ rộng xung (MAX30102 tr. 25, Bảng 14).
- **Độ trễ trong AFE:**
  - MAX30001: tr. 26, Bảng 4. Ví dụ 512 sps: 19,836 ms không LPF, 31,555 ms có
    LPF; 128 sps: 102,844 / 149,719 ms; 125 sps: 105,313 / 153,313 ms. Độ trễ này
    cùng bậc với PAT, phải ghi theo cấu hình và hiệu chỉnh. Bảng chỉ gồm độ trễ
    bộ lọc số; ghi chú ADI cho MAX30003 đo thêm khoảng 1,0 ms trễ lấy mẫu ADC
    (`Packet_Schema_V0.1.md` mục 5.2).
  - MAX3010x: datasheet không cho độ trễ; lấy trung bình N mẫu thêm trễ ước lượng
    (N−1)/2 chu kỳ lấy mẫu gốc. Phải đo.
- **Tốc độ cấu hình khác tốc độ thực.** MAX30001 chạy theo dao động 32,768 kHz (cả
  FMSTR 01 cũng suy ra từ đó, tr. 27, Bảng 6). MAX3010x dùng dao động nội; clock
  ADC 10,2–10,8 MHz (MAX30101 tr. 3) hoặc 10,32–10,64 MHz (MAX30102 tr. 3), và
  datasheet không nêu sai số tốc độ lấy mẫu. Tốc độ thực của từng kênh phải đo
  (xem kế hoạch đo 10 phút).

**Cấu hình V1:**

- **ECG 512 sps** (FMSTR 00, đúng tần số dao động trên breakout; chốt 2026-10-23,
  `custom_board_proposal.md` A.2). Không đổi sang 500 sps (FMSTR 01) chỉ để hạ về
  125 Hz theo hệ số nguyên. 256 sps chỉ xét nếu bench cho thấy MCU đọc FIFO ECG
  không kịp: FIFO 32 mẫu chứa khoảng 62,5 ms ở 512 sps. Gain 20 V/V, lọc thông thấp
  số 40,96 Hz, tắt lọc thông cao số, phát hiện rời điện cực DC 10 nA, ±400 mV (chốt
  2026-10-25, `custom_board_proposal.md` A.2).
- **PPG 200 sps mỗi khe**, multi-LED ba khe (`SLOT1` xanh, `SLOT2` đỏ, `SLOT3` IR),
  `SMP_AVE = 1` (chốt 2026-10-24, A.6 mục 3); độ rộng xung (411 hay 215 µs) còn mở
  (mục 6). Dải ADC 16 384 nA; dòng LED hiệu chuẩn theo người ở buổi đầu rồi khóa
  (chốt 2026-10-25, `custom_board_proposal.md` A.3). Lý do:
  - MAX3010x không có 500 sps; ba khe chạy tới mức 200 sps (A.6 mục 3).
  - `SMP_AVE = 1` không thêm trễ lấy trung bình vào PAT.
  - Ở 200 sps, nhấp nháy 100 Hz của đèn (điện lưới 50 Hz) nằm ở tần số Nyquist,
    lọc được; ở 100 sps nó gập về gần DC. Hài 200 Hz vẫn gập về gần DC ở cả hai
    tốc độ: đo ở bench (mục 6).
  - Dữ liệu 200 sps hạ được về tốc độ thấp hơn để thử. Riêng hành vi khi chip chạy
    thật ở 100 sps (nhiễu, dòng LED) phải đo riêng, không suy từ dữ liệu 200 sps đã
    hạ tần số.
  - Không dùng 400 sps lấy trung bình 2: ba khe ở 400 sps chỉ cho độ rộng xung
    ≤ 215 µs, thêm khoảng 1,25 ms trễ, và chưa có bằng chứng SNR tốt hơn.
- **Hệ quả cho firmware:** FIFO PPG 32 mẫu chứa 160 ms ở 200 sps. `FIFO_A_FULL` chỉ
  đặt được để ngắt khi có 17–32 mẫu chưa đọc (MAX30102 tr. 17), nên muốn đọc lô nhỏ
  hơn thì dùng ngắt `PPG_RDY` hoặc đọc theo timer. Chốt 2026-10-24: xóa ngắt
  `PPG_RDY` sau mỗi mẫu (đọc 0x00) và đọc con trỏ FIFO, khi có 8 mẫu thì đọc hết FIFO
  (thường 8 mẫu, 25 packet/s mỗi khe; Packet Schema V0.2 mục 7.6); ECG `EFIT = 15`, đọc tới EOF
  (thường 16 mẫu, tối đa 32).
  Thời gian LED sáng của ba khe chiếm 24,7% ở 411 µs và 12,9% ở 215 µs (tính từ giá
  trị danh định): dòng xung LED ảnh hưởng VLED+ và 3V3 (A.6 mục 3).

`configs/hardware/packet_simulation.json` (mô phỏng SYNTHETIC v2, giữ nguyên) dùng
PPG 128 Hz, **không có trong bảng tốc độ MAX3010x**. Mô phỏng v3
(`packet_simulation_v3.json`) dùng PPG 100 sps, khác tốc độ đã chốt; đây chỉ là
tham số mô phỏng. Nguồn giả của firmware chạy PPG 200 sps, 8 mẫu mỗi lần đọc
(`firmware/README.md`).

## 5. Clock, ngắt và đồng bộ

- Clock tham chiếu duy nhất: bộ đếm `esp_timer` (µs, 64 bit, tính từ lúc MCU
  khởi động) trên ESP32-S3. Mọi timestamp trong packet theo clock này.
- MAX30001 báo FIFO ECG đạt ngưỡng `EFIT` qua INTB → GPIO21 (tr. 41, tr. 44).
  MAX3010x báo FIFO gần đầy (`A_FULL`) hoặc có mẫu mới (`PPG_RDY`) qua INT → GPIO18
  (MAX30102 tr. 12). Số GPIO theo bảng A.7 (mục 3). Cách chốt số mẫu và ghi mốc
  thời gian: packet schema mục 5.
- Không có clock chung giữa hai AFE. Drift giữa hai kênh là chắc chắn có; độ lớn
  phải đo.
- **INT2B:** KiCad V1-module nối INT2B của MAX30001 vào GPIO47. Firmware bật xung
  `SAMP` luôn (`EN_INT2`, `SAMP_IT`; tr. 42–44; chốt 2026-10-24, Packet Schema V0.2
  mục 7). MCPWM capture chốt bộ đếm riêng của nó tại cạnh xung, quy đổi sang
  `esp_timer`, được mốc phần cứng lúc mẫu ECG vào FIFO;
  thời điểm lấy mẫu analog bằng mốc này trừ độ trễ đo ở bench
  (`Packet_Schema_V0.1.md` mục 5.2). MAX3010x không có chân tương đương; phía PPG vẫn dựa vào
  mốc đọc FIFO và phép đo bench.
- Không dùng PAT hay mốc sinh lý để ước lượng lệch clock.

## 6. Quyết định còn mở

1. Độ rộng xung LED PPG: 411 hay 215 µs, chọn bằng số đo bring-up. V1 chốt
   multi-LED ba khe (`SLOT1` xanh, `SLOT2` đỏ, `SLOT3` IR) ở 200 sps, `SMP_AVE = 1`
   (2026-10-24, `custom_board_proposal.md` A.6 mục 3).
2. KiCad V1-module dùng GPIO15/16 cho SCLK/MOSI của MAX30001, trùng XTAL_32K_P/N
   của ESP32-S3 (datasheet ESP32-S3 v2.2, Bảng 2-4 tr. 21, Bảng 2-8 tr. 24).
   `custom_board_proposal.md` Phần B mục 5 đề xuất thạch anh 32,768 kHz cho RTC;
   nếu bản cuối giữ pin map V1-module thì hai việc này xung đột. V1 không có thạch
   anh 32 kHz nên không bị ảnh hưởng.
