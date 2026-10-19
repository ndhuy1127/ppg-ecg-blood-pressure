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
| Sự kiện | Nút bấm `t0` vào GPIO, LED trạng thái | Đánh dấu bắt đầu bơm cuff trên cùng đồng hồ `esp_timer` |
| Phụ | Header cái cho module, tụ 100 nF + 10 µF mỗi module, test point mọi rail và bus | |

### A.3. Bo cảm biến cổ tay (gắn trên dây đeo)

| Khối | Linh kiện | Giao tiếp, ghi chú |
| --- | --- | --- |
| PPG | SparkFun Photodetector Breakout MAX30101 (Qwiic), SEN-16474 | **I²C bus 1, dùng riêng.** Chỉ cần cấp 3,3 V (A.4). Không chọn bo có chip MAX32664 (chỉ xuất nhịp tim/SpO2 đã tính) |
| IMU | SparkFun Qwiic 6DoF BMI270 (bản 1×1), mặt dưới bo | **SPI bus 2**, tách khỏi bus của MAX30001. Phải cắt jumper `I2C` và `ADR` để dùng SPI |
| Áp lực | FSR 402 + điện trở chia áp | **Tùy chọn.** Vào chân ADC1 (ADC2 không dùng được khi bật WiFi) |
| Cơ khí | Hai khe 3 × 22 mm trên PCB cho dây velcro 20 mm; tấm kính hoặc acrylic che | Theo ảnh sản phẩm, hai đầu nối Qwiic cao hơn chip cảm biến nên da cổ tay chạm đầu nối trước: tháo đầu nối Qwiic hoặc làm giá đỡ |

**Cáp nối hai bo:** box header 2×8 bước 2,54 mm có khóa chiều ở cả hai bo + cáp
dẹt IDC 16P bấm sẵn, dài 20–30 cm, dây GND xen giữa các dây tín hiệu. Tín hiệu: 3V3, GND, PPG SDA/SCL/INT, BMI270 SCK/MOSI/MISO/CS/INT,
FSR. Không cần dây 5 V vì bo MAX30101 tự tạo 5 V.

Schematic và PCB (đã đi dây) của hai bo: `hardware/kicad/v1_module/`.

### A.4. Bo SparkFun MAX30101: điều đã kiểm trong schematic

Nguồn: `Hardware/SparkFun_MAX30101_Qwiic.sch` (Eagle) trong repo
`sparkfun/SparkFun_Photodetector_Breakout_MAX30101_Qwiic`, nhánh `master`, đọc
ngày 2026-10-16.

| Chức năng | Trên bo | Hệ quả cho bo đế |
| --- | --- | --- |
| Nguồn vào | Chỉ 3,3 V (chân 3.3V và Qwiic) | Cấp 3V3 từ DevKitC |
| VDD 1,8 V của MAX30101 | LDO SP6214 1,8 V/100 mA từ 3,3 V | **Chân header "1.8V" là đầu ra LDO**; không nối nguồn vào |
| VDD_LED (VLED+) | Boost PAM2401 từ 3,3 V lên net 5V | LED xanh có nguồn 5 V ngay trên bo |
| I²C | Chuyển mức bằng 2 MOSFET kênh N; kéo lên 2,2 kΩ ở cả phía 1,8 V và phía 3,3 V (phía 3,3 V qua jumper `I2C PU`) | Bus 1 không cần thêm kéo lên; chừa footprint, không hàn |
| INT | Kéo lên 4,7 kΩ lên 3,3 V (jumper `INT`) | Nối thẳng GPIO |

### A.5. Không dùng ở V1

LiPo, BQ25180, TPS62840, W25Q128, LDO 1,8 V và oscillator riêng: dữ liệu ghi trên
laptop; nguồn, clock và chuyển mức đã có trên module. Các linh kiện này thuộc
Phần B.

### A.6. Cần kiểm tra trước khi vẽ

1. ~~Header breakout MAX30001 có đưa chân INT2B ra không.~~ Có (chân 4 của SV1,
   theo `pc_max30001_brk_v1.0.brd`); đã nối vào GPIO4. Vẫn phải kiểm revision
   breakout thật.
2. Đối chiếu module thật đã mua với footprint.
3. Tổ hợp tốc độ × độ rộng xung cho ba khe LED của MAX30101 (bảng trong
   datasheet), và VLED 5 V đủ cho dòng LED xanh đã chọn.
4. Thầy chấp nhận MAX30101 dùng I²C trên bus riêng.
5. Đức Anh đồng ý pin map mới (MAX30001 riêng SPI bus 1, BMI270 sang SPI bus 2,
   nút `t0`); bảng GPIO ở `hardware/kicad/v1_module/README.md`.

## Phần B — bản hoàn chỉnh dùng chip trần

Các mục 1–7 dưới đây áp dụng cho bản hoàn chỉnh.

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
  schema.
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
- **Địa chỉ I²C 7 bit:** MAX30101 0x57 (ghi/đọc 0xAE/0xAF như MAX30102 tr. 29; số trang
  MAX30101 [chưa đối chiếu]); TMP117 0x48–0x4B,
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
6. Có nối INT2B (xung `SAMP`) của MAX30001 vào GPIO không.
7. Ngủ giữa các cửa sổ (thêm thạch anh 32 kHz) hay giữ MCU thức suốt phiên.
