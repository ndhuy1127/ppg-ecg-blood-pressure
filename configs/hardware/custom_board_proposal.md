# Phần cứng: V1 dùng module và bản hoàn chỉnh dùng chip trần

> Chưa đo trên phần cứng.
>
> **Phạm vi:** tài liệu có hai phần. **Phần A** là V1 dùng module và kit có sẵn
> (thầy cho phép), mục đích thu tín hiệu để xử lý. **Phần B** là bản hoàn chỉnh
> dạng đeo tay, hàn chip trần. Cả hai **khác** `hardware/bom/BOM_V1.xlsx` và
> `hardware/schematics/V1.SchDoc` hiện tại trên nhánh `dev/ducanh` (`9073aa8`):
> bản đó dùng MAX30102 và cho BMI270 chung bus SPI với MAX30001. Tài liệu V0
> tương ứng: [interface_power_sampling_v0.md](interface_power_sampling_v0.md).
>
> **Nguồn số trang:** số trang datasheet được đối chiếu ngày
> 2026-10-16. Dòng ghi **[chưa đối chiếu]** là thông số chưa kiểm trên
> datasheet gốc; phải kiểm trước khi chốt linh kiện.

## Phần A — V1 dùng module

### A.1. Nguyên tắc

- **Cùng chip với Phần B:** MAX30001, MAX30101, BMI270. Module chỉ khác
  mạch xung quanh; ADC, bộ lọc số và quang học trong chip giống nhau, để dữ liệu
  V1 dùng lại được cho bản hoàn chỉnh. Mô hình huấn luyện trên dữ liệu V1 vẫn
  phải kiểm định lại trên Phần B, nên thu thêm một tập cầu nối (cùng người, đo
  cả hai phần cứng trong một buổi).
- **PPG đo ở cổ tay**, đúng vị trí của bản hoàn chỉnh; ghi cả ba kênh xanh, đỏ,
  IR rồi chọn kênh chính bằng dữ liệu.
- **Cấu hình cố định trong một cửa sổ đo** (tốc độ, độ rộng xung, dòng LED, bộ
  lọc); không để firmware tự chỉnh gain; ghi toàn bộ thanh ghi vào metadata phiên.
- **Ưu tiên SPI** theo góp ý của thầy. MAX30101 chỉ có I²C, nên dùng một bus
  I²C riêng, không chung với cảm biến khác. Cần thầy xác nhận chấp nhận cách này.
- **Không có TMP117 ở V1** (Huy chốt 2026-10-16) để bo cổ tay nhỏ bằng một nửa;
  nhiệt độ lấy tạm từ cảm biến nhiệt trong chip MAX30101 (chỉ xu hướng).

### A.2. Bo đế (đặt trên bàn)

| Khối | Linh kiện | Giao tiếp, ghi chú |
| --- | --- | --- |
| MCU | ESP32-S3-DevKitC-1 N16R8 | Cấp nguồn và truyền dữ liệu qua USB với laptop **đang chạy pin, không cắm sạc** |
| ECG | Breakout ProtoCentral MAX30001 | **SPI bus 1, dùng riêng.** Oscillator 32,768 kHz, LDO 1,8 V và TXB0108 có sẵn trên breakout. 512 sps (chưa chốt) |
| Điện cực ECG | Điện cực dán Ag/AgCl (bộ kèm breakout hoặc 3M Red Dot 2228) | Qua jack 3,5 mm của breakout. Đạo trình I: cổ tay và ngón tay. Vài phiên dùng điện cực khô BIOPAC để so sánh |
| Sự kiện | Nút bấm `t0` (SW1) vào GPIO4, kéo lên 10 kΩ (R2) và tụ 100 nF (C2); LED trạng thái D1 qua 1 kΩ (R3) ở GPIO5 | Đánh dấu bắt đầu bơm cuff trên cùng đồng hồ `esp_timer` |
| FSR (phần trên bo đế) | R6 6,8 kΩ từ 3V3 tới `FSR_TOP`; R7 22 kΩ từ `FSR` xuống GND; R1 1 kΩ + C1 100 nF vào GPIO6 (ADC1_CH5, datasheet ESP32-S3 v2.2 Bảng 2-8, tr. 24) | FSR 402 nằm ở bo cổ tay, nối qua cáp (chân 15–16) |
| Phụ | Socket cho DevKitC (2 hàng 1×22) và breakout MAX30001 (header 10 chân SV1); R8 100 kΩ kéo `ECG_CS` lên 3V3 | Tụ 3V3–GND trên bo đế: C3, C5, C7 (10 µF) và C4, C6, C8 (100 nF). Test point: TP1 `3V3`, TP2 `GND`, TP4 `PPG_SCL`, TP5 `BMI_SCK`, TP6 `T0_BTN`; không có test point cho bus SPI ECG, `PPG_SDA`, `BMI_MOSI/MISO/CS` và các đường INT (mục 7 Việc còn mở) |

### A.3. Bo cảm biến cổ tay (gắn trên dây đeo)

| Khối | Linh kiện | Giao tiếp, ghi chú |
| --- | --- | --- |
| PPG | SparkFun Photodetector Breakout MAX30101 (Qwiic), SEN-16474 | **I²C bus 1, dùng riêng.** Chỉ cần cấp 3,3 V (A.4). Không chọn bo có chip MAX32664 (chỉ xuất nhịp tim/SpO2 đã tính) |
| IMU | SparkFun Qwiic 6DoF BMI270 (bản 1×1), mặt dưới bo | **SPI bus 2**, tách khỏi bus của MAX30001. Phải cắt jumper `I2C` và `ADR` để dùng SPI |
| Áp lực | FSR 402 + điện trở chia áp | **Tùy chọn.** FSR hàn vào J2 (1×2) ở mặt dưới bo cổ tay; điện trở chia áp nằm ở bo đế (A.2), vào GPIO6 thuộc ADC1 (ADC2 không dùng được khi bật WiFi) |
| Cơ khí | Hai khe 3 × 22 mm trên PCB cho dây velcro 20 mm; tấm kính hoặc acrylic che | Bo 40,4 × 31,5 mm theo Edge.Cuts. Theo ảnh sản phẩm, hai đầu nối Qwiic cao hơn chip cảm biến nên da cổ tay chạm đầu nối trước: tháo đầu nối Qwiic hoặc làm giá đỡ |
| Phụ | C2 10 µF + C3 100 nF trên 3V3–GND, dùng chung cho M1 (MAX30101) và M3 (BMI270) | Không có test point trên bo cổ tay |

**Cáp nối hai bo (theo KiCad):**

- Đầu bo đế: J2, box header IDC 2×8 bước 2,54 mm
  (`Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical`, DIN 41651), cắm socket IDC
  bấm trên cáp dẹt 16 dây.
- Đầu bo cổ tay: **không có đầu nối**. J1 (`Ribbon_2x08_P2.54mm_SolderHoles`) là
  16 lỗ hàn cho cáp dẹt 1,27 mm, dây n vào lỗ n theo đánh số IDC. Đầu này không có
  khóa chiều.
- Chiều dài dự kiến 20–30 cm (KiCad không thể hiện).
- GND ở chân 2, 4, 7, 9, 14. Các dây tín hiệu kề nhau không có GND xen giữa: 5–6
  (`PPG_SCL`, `PPG_INT`), 10–13 (`BMI_MOSI`, `BMI_MISO`, `BMI_CS`, `BMI_INT`),
  15–16 (`FSR`, `FSR_TOP`). Chân 1–2 là 3V3 và GND đặt kề nhau.
- Tín hiệu: 3V3, GND, PPG SDA/SCL/INT, BMI270 SCK/MOSI/MISO/CS/INT, `FSR`,
  `FSR_TOP`. Không cần dây 5 V vì bo MAX30101 tự tạo 5 V.

Bảng chân từng dây: A.7. Schematic và PCB (đã đi dây) của hai bo:
`hardware/kicad/v1_module/base/` và `hardware/kicad/v1_module/wrist/`.

### A.4. Bo SparkFun MAX30101: điều đã kiểm trong schematic

Nguồn: `Hardware/SparkFun_MAX30101_Qwiic.sch` (Eagle) trong repo
`sparkfun/SparkFun_Photodetector_Breakout_MAX30101_Qwiic`, nhánh `master`, đọc
ngày 2026-10-16.

| Chức năng | Trên bo | Hệ quả cho bo đế |
| --- | --- | --- |
| Nguồn vào | Chỉ 3,3 V (chân 3.3V và Qwiic) | Cấp 3V3 từ DevKitC |
| VDD 1,8 V của MAX30101 | LDO SP6214 1,8 V/100 mA từ 3,3 V | **Chân header "1.8V" là đầu ra LDO**; không nối nguồn vào |
| VDD_LED (VLED+) | Boost PAM2401 từ 3,3 V lên net 5V | LED xanh có nguồn 5 V ngay trên bo |
| I²C | Chuyển mức bằng 2 MOSFET kênh N; kéo lên 2,2 kΩ ở cả phía 1,8 V và phía 3,3 V (phía 3,3 V qua jumper `I2C PU`) | Bus 1 không cần thêm kéo lên. KiCad hiện **không có** footprint kéo lên I²C trên cả hai bo (mục 7 Việc còn mở) |
| INT | Kéo lên 4,7 kΩ lên 3,3 V (jumper `INT`) | Nối thẳng GPIO |

### A.5. Không dùng ở V1

LiPo, BQ25180, TPS62840, W25Q128, LDO 1,8 V và oscillator riêng: dữ liệu ghi trên
laptop; nguồn, clock và chuyển mức đã có trên module. Các linh kiện này thuộc
Phần B.

### A.6. Cần kiểm tra trước khi vẽ

1. ~~Header breakout MAX30001 có đưa chân INT2B ra không.~~ Có (chân 4 của SV1,
   theo `pc_max30001_brk_v1.0.brd`); trên KiCad V1-module đã nối vào GPIO47
   (net `/ECG_INT2B`, U1 pad 28). Vẫn phải kiểm revision breakout thật.
2. Đối chiếu module thật đã mua với footprint.
3. Tổ hợp tốc độ × độ rộng xung cho ba khe LED của MAX30101 (bảng trong
   datasheet), và VLED 5 V đủ cho dòng LED xanh đã chọn.
4. Thầy chấp nhận MAX30101 dùng I²C trên bus riêng.
5. Pin map: KiCad V1-module (MAX30001 riêng SPI bus 1, BMI270 sang SPI bus 2,
   nút `t0`; bảng ở A.7) khác pin map V1 của Đức Anh
   ([interface_power_sampling_v0.md](interface_power_sampling_v0.md) mục 3).
   Chọn bản nào làm chuẩn là việc còn mở (mục 7 Việc còn mở).
6. DevKitC N16R8 dùng chip nào; với ESP32-S3R8V/R16V thì GPIO47 (`ECG_INT2B`)
   chạy 1,8 V (datasheet ESP32-S3 v2.2, Bảng 2-1, chú thích 4, tr. 17)
   [chưa đối chiếu với tài liệu module].

### A.7. Bảng chân của KiCad V1-module

Bảng dưới lấy từ `hardware/kicad/v1_module/base/v1_base.kicad_pcb` (pad → net
của U1) và tên chân trong symbol `ESP32-S3-DevKitC-1` của
`v1_base.kicad_sch`; cáp lấy từ J1 của `v1_wrist.kicad_pcb` và J2 của
`v1_base.kicad_pcb`. Đây là pin map của **KiCad V1-module**, khác pin map V1 của
Đức Anh ở [interface_power_sampling_v0.md](interface_power_sampling_v0.md) mục 3
(`Pin_Map_V1.md`, `V1.SchDoc` trên nhánh `dev/ducanh`). Cả hai đều gọi là "V1";
bản nào là chuẩn còn mở (mục 7 Việc còn mở).

**GPIO của DevKitC (U1):**

| Net | GPIO | U1 pad | Thiết bị | Ghi chú |
| --- | ---: | ---: | --- | --- |
| `/ECG_CS` | 7 | 7 | MAX30001 CSB (J1 bo đế = SV1 chân 7) | R8 100 kΩ kéo lên 3V3 |
| `/ECG_SCLK` | 15 | 8 | MAX30001 SCLK (J1 bo đế = SV1 chân 8) | SPI bus 1. GPIO15 cũng là XTAL_32K_P (mục 7 Việc còn mở) |
| `/ECG_MOSI` | 16 | 9 | MAX30001 MOSI (J1 bo đế = SV1 chân 9) | GPIO16 cũng là XTAL_32K_N (mục 7 Việc còn mở) |
| `/ECG_MISO` | 17 | 10 | MAX30001 MISO (J1 bo đế = SV1 chân 10) | |
| `/ECG_INTB` | 21 | 27 | MAX30001 INTB (J1 bo đế = SV1 chân 5) | |
| `/ECG_INT2B` | 47 | 28 | MAX30001 INT2B (J1 bo đế = SV1 chân 4) | Xung `SAMP` nếu firmware bật (mục 7 Việc còn mở). Datasheet ESP32-S3 v2.2 (Bảng 2-1, chú thích 4, tr. 17): GPIO47/48 chạy 1,8 V ở chip ESP32-S3R8V/R16V; chip trên DevKitC N16R8 [chưa đối chiếu] |
| `/PPG_SDA` | 8 | 12 | MAX30101 SDA (cáp chân 3) | I²C bus 1 |
| `/PPG_SCL` | 9 | 15 | MAX30101 SCL (cáp chân 5) | TP4 |
| `/PPG_INT` | 18 | 11 | MAX30101 INT (cáp chân 6) | |
| `/BMI_CS` | 10 | 16 | BMI270 CS (cáp chân 12) | SPI bus 2 |
| `/BMI_MOSI` | 11 | 17 | BMI270 SDA/PICO (cáp chân 10) | |
| `/BMI_SCK` | 12 | 18 | BMI270 SCL/SCK (cáp chân 8) | TP5 |
| `/BMI_MISO` | 13 | 19 | BMI270 ADR/POCI (cáp chân 11) | |
| `/BMI_INT` | 14 | 20 | BMI270 INT1 (cáp chân 13) | |
| `/T0_BTN` | 4 | 4 | SW1 | R2 10 kΩ kéo lên, C2 100 nF, TP6 |
| `/LED_STAT` | 5 | 5 | D1 qua R3 1 kΩ | |
| `/FSR_ADC` | 6 | 6 | FSR qua R1 1 kΩ, C1 100 nF | ADC1_CH5 |
| `/+3V3` | — | 1, 2 | Nguồn 3V3 của DevKitC | Chân 5V (pad 21) không nối |
| `/GND` | — | 22, 23, 24, 44 | | |

Không nối: EN và GPIO0, 1, 2, 3, 19, 20, 35–42, 43, 44, 45, 46, 48.

**Cáp 16 dây (J2 bo đế ↔ J1 bo cổ tay, cùng số chân):**

| Chân | Net | Chân | Net |
| ---: | --- | ---: | --- |
| 1 | `/+3V3` | 2 | `/GND` |
| 3 | `/PPG_SDA` | 4 | `/GND` |
| 5 | `/PPG_SCL` | 6 | `/PPG_INT` |
| 7 | `/GND` | 8 | `/BMI_SCK` |
| 9 | `/GND` | 10 | `/BMI_MOSI` |
| 11 | `/BMI_MISO` | 12 | `/BMI_CS` |
| 13 | `/BMI_INT` | 14 | `/GND` |
| 15 | `/FSR` | 16 | `/FSR_TOP` |

Bo cổ tay: M1 MAX30101 (mặt trên) dùng chân 1–5 (GND, 3.3V, SDA, SCL, INT);
chân 6 `1.8V_OUT` không nối. M3 BMI270 (mặt dưới) dùng GND, 3.3V, PICO, SCK, POCI, CS,
INT1 (ASDX, ASCX, INT2, OCS, OSDO không nối); J2 FSR nối `FSR_TOP` và `FSR`.

Định dạng file: PCB lưu bằng KiCad 10.0, schematic bằng KiCad 9.0; mở
`.kicad_pcb` bằng KiCad ≥ 10.

## Phần B — bản hoàn chỉnh dùng chip trần

Các mục 1–6 dưới đây áp dụng cho bản hoàn chỉnh. Mục 7 (Việc còn mở) gom việc
còn mở của cả Phần A và Phần B.

## 1. Danh sách linh kiện

| Khối | Linh kiện | Ghi chú |
| --- | --- | --- |
| MCU | Module ESP32-S3 (ví dụ WROOM-1 N16R8) | Dùng module có anten và chứng nhận RF, không dùng chip trần. PSRAM octal chiếm GPIO35–37 [chưa đối chiếu] |
| ECG AFE | MAX30001 (IC trần) | Mục 3, 4 |
| PPG AFE | MAX30101 (IC trần) | Có LED xanh, đỏ, IR. Mục 3, 4 |
| Nguồn LED | Boost 5 V cho VLED+ (ví dụ PAM2401, như bo SparkFun ở A.4) | LED xanh cần 4,5–5,5 V; mục 4 [chưa đối chiếu] |
| IMU | BMI270 | Tùy chọn. Tham chiếu nhiễu chuyển động, đặt gần khối PPG |
| Áp lực tiếp xúc | FSR 402 + op-amp rail-to-rail dòng thấp (ví dụ TLV9001) | Tùy chọn. Bán định lượng: phi tuyến, trễ, trôi khi tải liên tục; phải hiệu chuẩn bằng quả cân [chưa đối chiếu] |
| Nhiệt độ da | TMP117 | Tùy chọn. Đặt trên đuôi flex hoặc pad tiếp xúc da, cách nhiệt khỏi MCU, LDO, LED [chưa đối chiếu] |
| Bộ nhớ | W25Q128 (16 MB) | Mục 6 [chưa đối chiếu] |
| Pin | LiPo 150 mAh | Phải đo dòng. Mục 6 |
| Sạc | BQ25180 | Dòng sạc ≤ 1C. Không có fuel gauge [chưa đối chiếu] |
| Nguồn 3V3 | TPS62840 | Buck, tối đa 750 mA [chưa đối chiếu] |
| Nguồn 1,8 V | LDO Iq thấp (ví dụ TPS7A02-1.8) | Mục 4 [chưa đối chiếu] |
| Clock ECG | Oscillator 32,768 kHz, CMOS (ví dụ họ SiT1533) | Bắt buộc nếu dùng MAX30001 trần. Mục 3 [chưa đối chiếu] |
| Điện cực ECG | 2 pad điện cực khô: mặt dưới chạm cổ tay, mặt trên chạm ngón tay | Đạo trình I, đo theo cửa sổ (mục 2) |
| USB | USB-C + ESD (ví dụ USBLC6-2SC6) | Nạp firmware, sạc [chưa đối chiếu] |
| Đo pin | Bộ chia áp có MOSFET đóng ngắt vào ADC ESP32 | Thay cho fuel gauge |
| Bring-up | Nút BOOT/RESET, LED trạng thái, test point từng rail và bus | |

## 2. Cách đo và tốc độ ECG

- **ECG 512 sps, FMSTR 00**, FCLK = 32,768 kHz (MAX30001 tr. 49, Bảng 26). Chưa
  chốt; quyết định số 3 trong mục 6 của tài liệu V0 vẫn mở. Nếu chốt, khớp `FS_NOMINAL_MHZ = 512 000` trong packet
  schema (đơn vị mHz, tức 512 Hz).
- **Đo theo cửa sổ:** ECG đạo trình I chỉ có khi người đo chạm ngón tay vào điện
  cực mặt trên, nên mỗi lần đo chỉ vài chục giây, không đo ECG liên tục suốt buổi
  1–2 giờ.
- **Vị trí cửa sổ theo protocol:** cửa sổ `[t0 − L, t0)` **kết thúc tại `t0`**,
  ngay trước khi bắt đầu bơm cuff; mỗi lần đo cuff là một nhãn
  (`docs/protocol/week_02_sample_label_glossary.md`). Không lấy tín hiệu trong
  lúc cuff đang bơm hoặc xả.

## 3. Clock của từng linh kiện

| Linh kiện | Nguồn clock | Linh kiện ngoài | Ghi chú |
| --- | --- | --- | --- |
| MAX30001 | Chân FCLK, ngõ vào số (tr. 8, tr. 18–19) | **Bắt buộc: oscillator 32,768 kHz** | Không có cặp chân XIN/XOUT, nên không gắn thạch anh thụ động được. FMSTR 01 (500 sps) cũng suy ra từ FCLK 32,768 kHz (tr. 27, Bảng 6) |
| MAX30101 | Dao động nội | Không có chân nhận clock ngoài | Không có 512 sps; bảng tốc độ chung họ MAX3010x ở `interface_power_sampling_v0.md` mục 4 |
| BMI270 | Dao động nội | Không | Sensortime chạy theo dao động nội của BMI270 (datasheet BMI270 mục 5.2.24–5.2.26): **thêm một miền clock**, cũng phải ánh xạ về `esp_timer` như hai AFE |
| ESP32-S3 module | Thạch anh 40 MHz trong module | Tùy chọn thạch anh 32,768 kHz (mục 5) | Nguồn của `esp_timer`, trục thời gian chung |
| TMP117, W25Q128, BQ25180, TPS62840 | Dao động nội hoặc SCK từ MCU | Không | [chưa đối chiếu] |

Hiện trạng: `BOM_V1.xlsx` và `V1.SchDoc` không có dòng oscillator, nhưng breakout
MAX30001 của ProtoCentral **đã có sẵn oscillator SiT1533 nối vào FCLK** (lần theo
net trong schematic ProtoCentral). Thiếu oscillator chỉ thành vấn đề
khi chuyển sang MAX30001 trần như Phần B.

Yêu cầu oscillator FCLK:

- Đầu ra CMOS, mức logic theo OVDD. OVDD = 3,3 V thì dùng oscillator 3,3 V từ
  rail 3V3.
- Sai số khoảng ±20 ppm: trong cửa sổ 60 s lệch tích lũy khoảng 1,2 ms so với
  tốc độ danh định. Vẫn phải ước lượng tốc độ thực từ mốc `esp_timer` (packet
  schema mục 5), không dùng 512 sps danh định.
- Dòng tiêu thụ cỡ µA [chưa đối chiếu].
- Tùy chọn: nối thêm FCLK vào một GPIO có PCNT để firmware đo sai số ppm của
  clock ECG so với thạch anh 40 MHz.

## 4. Nguồn và giao tiếp

- **Rail 1,8 V dùng chung:** MAX30001 AVDD/DVDD ≤ 2,0 V, OVDD 1,65–3,6 V
  (MAX30001 tr. 8); MAX30101 VDD 1,7–2,0 V (MAX30101 tr. 2). Thêm lọc ferrite
  hoặc RC riêng cho AVDD của MAX30001.
- **OVDD = 3,3 V:** SPI nối thẳng ESP32, bỏ TXB0108 và rủi ro `SPI_MISO` của
  breakout. Mức logic khớp: VIH của MAX30001 là 0,7·OVDD ≈ 2,31 V, VOH là
  OVDD − 0,4 V (MAX30001 tr. 8).
- **VLED+ của MAX30101:** 3,1–5,0 V cho đỏ/IR, 4,5–5,5 V cho LED xanh
  (MAX30101 tr. 2). Dùng boost 5 V từ VBAT, kèm tụ ≥ 1 µF sát chân VLED+, để
  xung dòng LED không đi vào rail 3V3. Nếu bỏ LED xanh thì VLED+ có thể lấy
  thẳng từ VBAT với ngưỡng cắt pin thấp ≥ 3,1 V.
- **Địa chỉ I²C 7 bit:** MAX30101 0x57 (ghi/đọc 0xAE/0xAF như MAX30102 tr. 29
  [chưa đối chiếu: `interface_power_sampling_v0.md` và `hardware/datasheets/README.md`
  ghi tr. 5]; số trang MAX30101 [chưa đối chiếu]); TMP117 0x48–0x4B,
  BMI270 0x68/0x69, BQ25180 0x6A [chưa đối chiếu]. Không trùng. Nếu thêm ADC họ
  ADS1115 cho FSR (0x48–0x4B) thì chọn chân ADDR khác TMP117.
- **Bảo vệ điện cực ECG:** mạng Rpp và VCM 200 kΩ theo MAX30001 tr. 84, Hình 17c.
- **Chặn ghi khi có VBUS:** khi đang cắm USB, người đo nối với đất điện lưới;
  firmware chặn ghi hoặc gắn cờ.

## 5. Ngủ giữa các cửa sổ và trục thời gian

- **Không ngủ trong lúc đang đo một cửa sổ.**
- Theo hiểu biết về ESP-IDF (chưa đối chiếu tài liệu Espressif): khi light
  sleep, `esp_timer` được bù bằng clock RTC; không có thạch anh 32 kHz thì clock
  này là RC nội, sai số lớn. Deep sleep khởi động lại MCU và reset `esp_timer`.
- Nếu packet sự kiện cuff (`t0`) và cửa sổ tín hiệu phải dùng chung trục thời
  gian qua các lần ngủ, thì **thêm thạch anh 32,768 kHz cho RTC của ESP32**
  hoặc **giữ MCU thức** suốt phiên.
- Thạch anh 32 kHz nối vào XTAL_32K_P/XTAL_32K_N, tức GPIO15/GPIO16 (datasheet
  ESP32-S3 v2.2, Bảng 2-4 tr. 21 và Bảng 2-8 tr. 24). KiCad V1-module đang dùng
  hai chân này cho `ECG_SCLK`/`ECG_MOSI` (A.7): nếu bản hoàn chỉnh giữ pin map
  đó thì không gắn được thạch anh (mục 7 Việc còn mở).

## 6. Thời điểm mẫu, dung lượng flash và pin

### 6.1. Thời điểm mẫu PPG

1. Gán thời điểm cho từng mẫu gốc theo packet schema mục 5.
2. Phát hiện chân sóng PPG trên mẫu gốc. Chỉ nội suy về lưới thời gian chung
   khi thật cần, và ghi lại phương pháp nội suy, vì nội suy trước có thể làm lệch
   mốc PAT.

### 6.2. Dung lượng flash

Theo packet schema V0.1 (int32 mỗi mẫu, 40 B header + 2 B CRC mỗi packet, mỗi
kênh/khe một packet):

| Kênh | Giả định | Tốc độ ghi |
| --- | --- | ---: |
| ECG | 512 sps, N = 16 (106 B/packet) | ≈ 3,4 kB/s |
| PPG | Ví dụ 400 sps, 3 khe (xanh + đỏ + IR), N = 16 | ≈ 8,0 kB/s |
| IMU | Packet schema V0.1 chưa có kênh IMU | chưa tính |

ECG + PPG theo schema ≈ 11,3 kB/s, nên W25Q128 (16 MiB) chứa khoảng **25 phút**
ghi thô. Nếu ghi theo định dạng nén 3 B mỗi mẫu, không có header từng packet, thì
thời lượng khoảng gấp đôi. Với đo theo cửa sổ vài chục giây, tổng thời gian ghi
mỗi buổi thường dưới mức này; phải tính lại khi chốt tốc độ PPG và kênh IMU.

V1 dự kiến truyền qua BLE hoặc ghi flash, nên mục 13 "Truyền USB/Serial" của
packet schema sẽ cần cập nhật sau (không sửa trong tài liệu này).

### 6.3. Pin

- Dòng trung bình khi truyền BLE ước khoảng 50–70 mA [chưa đối chiếu]. LiPo
  150 mAh đủ cho buổi 1–2 giờ chỉ khi MCU tiêu thụ thấp giữa các cửa sổ; cách
  ngủ phải theo mục 5. **Phải đo dòng trên bo thật** trước khi chốt.
- Nếu bật WiFi, dòng đỉnh 300–500 mA (2–3C với pin 150 mAh) có thể gây
  brownout: kiểm tra dòng xả tối đa của cell và thêm tụ bulk 22–47 µF ở 3V3
  [chưa đối chiếu].

## 7. Việc còn mở

1. Tốc độ ECG 512 hay 500 sps.
2. Tốc độ lấy mẫu PPG và kênh LED chính (chọn từ dữ liệu ba kênh của V1).
3. BMI270, FSR 402, TMP117 có trong phạm vi không.
4. ADC cho FSR: ADC nội ESP32 hay ADC ngoài.
5. Có jack điện cực dán Ag/AgCl để lấy ECG tham chiếu không.
6. INT2B (xung `SAMP`) của MAX30001: KiCad V1-module đã nối vào GPIO47 (A.7).
   Còn mở cho pin map V1 của Đức Anh và cho bản hoàn chỉnh, và firmware có bật
   `SAMP` (`EN_INT2`, `SAMP_IT`) hay không.
7. Ngủ giữa các cửa sổ (thêm thạch anh 32 kHz) hay giữ MCU thức suốt phiên.
8. Pin map nào là chuẩn: KiCad V1-module (A.7) hay pin map V1 của Đức Anh
   (`interface_power_sampling_v0.md` mục 3). Cả hai đều mang tên "V1".
9. Xung đột chân: KiCad V1-module dùng GPIO15/16 cho `ECG_SCLK`/`ECG_MOSI`, trùng
   XTAL_32K_P/N của ESP32-S3 (mục 5). Nếu bản hoàn chỉnh giữ pin map này thì
   phải bỏ thạch anh 32 kHz hoặc đổi chân SPI ECG.
10. Đầu cáp ở bo cổ tay hàn thẳng, không có khóa chiều; chân 1–2 (3V3, GND) kề
    nhau. Hàn sai thứ tự hay lật cáp sẽ đưa 3V3/GND vào sai net, có nguy cơ cấp
    nguồn ngược cho module. Có thêm header có khóa chiều trên bo cổ tay không.
11. Thứ tự dây cáp: mô tả ban đầu là GND xen giữa các dây tín hiệu, nhưng chân
    10–13 (`BMI_MOSI`, `BMI_MISO`, `BMI_CS`, `BMI_INT`), 5–6 và 15–16 kề nhau không
    có GND (A.3). Đổi thứ tự chân hay giữ nguyên.
12. Footprint kéo lên I²C (chừa sẵn, không hàn) chưa có trên bo nào (A.4). Có
    thêm không.
13. Tụ và test point: mô tả ban đầu là tụ 100 nF + 10 µF cho mỗi module và test
    point cho mọi rail và bus. Bản vẽ hiện có: bo cổ tay một cặp C2/C3 dùng chung
    cho M1 và M3, không có test point; bo đế có test point ở 3V3, GND,
    `PPG_SCL`, `BMI_SCK`, `T0_BTN` (A.2), thiếu bus SPI ECG, `PPG_SDA`,
    `BMI_MOSI/MISO/CS` và các đường INT. Có bổ sung không.
