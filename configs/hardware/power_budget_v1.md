# Ước lượng dòng V1-module so với cổng USB của laptop

> **Ước lượng từ datasheet, không phải số đo.** Phải đo lại trên bo thật ở bring-up. Hai
> datasheet Maxim đọc từ bản mirror cũ hơn bản đang dùng trong
> [hardware/datasheets/README.md](../../hardware/datasheets/README.md) (trang
> analog.com chặn công cụ tải tự động), nên **số trang phải đối chiếu lại** với Rev 3.
> Datasheet PAM2401, BMI270 và SGM2212 đã đối chiếu lại ngày 2026-10-26 trên bản tải
> từ trang hãng (sửa theo review: chế độ BMI270, số trang, dòng khởi động của boost,
> giới hạn USB có điều kiện).

## 1. Cấu hình đang dùng

- ESP32-S3 chạy **160 MHz**: mặc định của ESP-IDF 5.5.3 cho ESP32-S3
  (`CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ`); `firmware/sdkconfig.defaults` không đặt tần số,
  file `sdkconfig.<env>` sinh ra khi build (không theo dõi bằng Git) ghi 160. BT tắt;
  Wi-Fi có trong build nhưng firmware không bật; PSRAM tắt. Dữ liệu đi qua USB
  Serial/JTAG native.
- MAX30001: chỉ ECG, 512 sps, lead-off DC 10 nA, BioZ tắt (`max30001_v1_regs`).
- MAX30101: ba khe, 200 sps mỗi khe, độ rộng xung 411 hay 215 µs (còn mở). Mã LED mặc
  định đỏ = IR = 0x24 (7,2 mA), xanh 0x12 (3,6 mA) ở **cả** LED3 và LED4
  (`max30101_v1_regs`); lệnh từ PC cho tới 0x7F (25,4 mA, `CMD_LED_CODE_MAX`).
- BMI270: gia tốc và con quay 100 Hz, cả hai ở chế độ performance (`acc_conf` 0xA8,
  `gyr_conf` 0xE8, `firmware/drivers/bmi270.c`).

## 2. Số liệu nguồn

| Khối | Điều kiện | Điển hình | Tối đa | Nguồn |
| --- | --- | --- | --- | --- |
| ESP32-S3, 160 MHz | Modem-sleep (RF tắt), mọi clock ngoại vi bật; từ WAITI tới hai nhân 128 bit | 42,3 → 81,1 mA | không ghi | ESP32-S3 Datasheet v2.2, tr. 67, Bảng 5-9; chú thích 3 tr. 68: thêm khoảng 10 mA khi đọc flash |
| Module WROOM-1 | Nguồn phải cấp được | ≥ 0,5 A | — | WROOM-1 v1.8, tr. 27, Bảng 6-2 |
| LDO 3,3 V của DevKitC (SGM2212-3.3) | Dòng ra | 800 mA | — | Schematic DevKitC v1.1 tr. 2; SGM2212 REV A.2 (7/2023), tr. 1 |
| SGM2212 | Dòng chân GND, 25 °C, không tải / 100 mA | 80 / 290 µA | 110 / 360 µA (370 µA ở 100 mA trên dải nhiệt) | SGM2212 REV A.2, tr. 6 |
| MAX30001 AVDD + DVDD | Kênh ECG | 95 µA | 120 µA | Rev 2 (8/19), tr. 9 (bản mirror) |
| MAX30001 OVDD | 3,6 V, ECG 512 sps | 0,6 µA | 1,6 µA | Rev 2, tr. 9 |
| AP2112K-1.8 (breakout ECG) | Iq | 55 µA | 80 µA | Diodes DS39724 Rev 2-2, tr. 5 |
| TXB0108 (breakout ECG) | ICCA, ICCB tĩnh | — | 5 µA mỗi phía | TI SCES643L, tr. 6–7 |
| MAX30101 VDD | Chế độ SpO2, 215 µs, 50 sps | 600 µA | 1 100 µA | Rev 0 (3/16), tr. 2 (bản mirror); không có số cho 200 sps ba khe |
| MAX30101 LED | 0,2 mA mỗi bước mã | — | — | Rev 0, tr. 21, Bảng 8 |
| PAM2401 (boost VLED 5,1 V) | Iq ở PSM | 150 µA | — | Diodes DS37285 Rev 1-2, tr. 1 |
| PAM2401 | Hiệu suất, VIN 3,3 V, VOUT 5 V, 100–1 000 mA | khoảng 90–94 % | — | DS37285, tr. 6, Hình 4; dưới khoảng 50 mA không đọc được |
| PAM2401 | Dòng nạp trước (pre-charge) lúc khởi động, khi VOUT + 0,5 V < VIN | 500 mA trong 400 µs | — | DS37285 Rev 1-2, tr. 4 |
| BMI270 | Gia tốc + con quay, performance / normal, 1,8 V, 25 °C | 970 / 685 µA | không ghi | BST-BMI270-DS000-08, tr. 11, Bảng 1; firmware dùng performance; không có số cho 100 Hz |
| SP6214 (LDO 1,8 V bo MAX30101) | Iq / dòng GND ở 100 mA | 65 / 135 µA | — | Trang sản phẩm MaxLinear SP6213/SP6214 (đọc 2026-10-26; sản phẩm đã ngưng, chưa mở datasheet 241DSR00) |
| Cổng USB 2.0 | Một unit load = 100 mA. Trước khi được host cấu hình, thiết bị chỉ được lấy 1 unit load; thiết bị high-power lấy tới 5 unit load (500 mA) sau khi được cấu hình, đúng mức `bMaxPower` khai trong descriptor | 100 / ≤ 500 mA | — | USB 2.0 Specification, mục 7.2.1 (theo nội dung chuẩn, chưa mở lại bản PDF) |
| USB Serial/JTAG của ESP32-S3 (`303A:1001`) | `bMaxPower` trong configuration descriptor | chưa tìm được | — | Bộ điều khiển cố định bằng phần cứng, firmware không đổi được descriptor; đọc bằng USBView hay `lsusb -v` ở bring-up mục 2 |

## 3. Tính toán

**LED** (trung bình = Σ biên độ × độ rộng xung × 200 sps; xanh tính hai lần; các khe
phát lần lượt nên đỉnh là khe lớn nhất). Hệ số chiếm xung 0,0822 ở 411 µs và 0,0430 ở
215 µs. Độ rộng xung datasheet là thời gian tích phân ADC; thời gian LED sáng thật có
thể dài hơn một chút, chưa kiểm.

| Trường hợp | Tổng các khe | TB ở 411 µs | TB ở 215 µs | Đỉnh |
| --- | --- | --- | --- | --- |
| Mặc định firmware (xanh 0x12 × 2) | 21,6 mA | 1,78 mA | 0,93 mA | 7,2 mA |
| Mọi mã 0x24 | 28,8 mA | 2,37 mA | 1,24 mA | 14,4 mA |
| Mọi mã 0x7F | 101,6 mA | 8,35 mA | 4,37 mA | 50,8 mA |

**Quy về 3,3 V** qua boost: I_3V3 = 5,1 × I_LED / (3,3 × η). η = 0,85 và 0,70 là
**giả định không có nguồn**: Hình 4 của PAM2401 không đọc được dưới khoảng 50 mA, mà
dòng LED trung bình chỉ vài mA.

| Tổng ở 3,3 V | Thành phần | Kết quả |
| --- | --- | --- |
| Điển hình | ESP32-S3 một nhân 160 MHz 54,6 + LED 0x24/411 µs 4,3 + Iq boost 0,15 + MAX30101 0,6 + chuỗi MAX30001 0,15 + BMI270 (performance) 0,97 + SP6214 0,065 | **khoảng 61 mA** |
| Trung bình, kịch bản xấu giả định | ESP32-S3 hai nhân 81,1 + flash 10 + LED 0x7F/411 µs, η 0,70, kèm Iq 18,6 + MAX30101 1,1 + MAX30001 0,21 + BMI270 0,97 + SP6214 0,065 | **khoảng 112 mA** |
| Trong xung LED xanh 0x7F, khi đã ổn định, cùng kịch bản | Như trên, thay LED trung bình bằng xung xanh 0x7F (khoảng 112 mA ở 3,3 V cho LED), trước khi tụ VLED san bớt | **khoảng 206 mA** |

Hai dòng dưới là **kịch bản**, không phải cận trên: MAX30101 1,1 mA là số tối đa ở
50 sps, 215 µs (không có số cho 200 sps ba khe), η không có nguồn, ESP32-S3 dùng số
điển hình.

Dòng ở 5 V USB bằng dòng 3,3 V cộng dòng chân GND của SGM2212. Datasheet chỉ cho các
mốc 80 µA (không tải) và 290 µA điển hình, 370 µA tối đa (100 mA), rồi 1,35 mA điển
hình ở 800 mA; ở 112–206 mA chưa có số, nhưng theo các mốc đó vẫn cỡ dưới 1 mA, không đổi
các tổng trên. LDO tỏa (V_vào − 3,3 V) × I: với V_vào ≤ 5 V (thấp hơn nếu đường USB
có diode) là tối đa khoảng 0,10 W ở 61 mA và 0,19 W ở 112 mA; chưa đánh giá nhiệt theo
vỏ và PCB của DevKitC. **Chưa tính:** LED nguồn và LED RGB của DevKitC, chip chuyển
USB–UART của cổng UART0 (nếu cắm), LED D1 của bo đế.

**Khởi động và quá độ (chưa định lượng):** các số trên là trạng thái đã ổn định. Lúc
boost khởi động, PAM2401 nạp trước tụ đầu ra với 500 mA điển hình trong 400 µs; lúc cắm
USB còn dòng nạp các tụ trên DevKitC, breakout và bo SparkFun. Các xung này không bị
chặn bởi bảng trên, và USB tester thường không bắt được xung vài trăm µs: đo bằng
oscilloscope qua điện trở shunt ở bring-up.

## 4. Kết luận tạm

- **Có điều kiện, chưa xác nhận tuân thủ USB.** Ước lượng ổn định điển hình khoảng
  61 mA, dưới 100 mA; đó không phải dòng đo ở trạng thái chưa cấu hình và chưa gồm các
  khối bỏ sót ở trên. Kịch bản xấu (LED 0x7F) khoảng 112 mA trung bình và khoảng 206 mA
  trong xung LED: cần host đã cấu hình thiết bị và `bMaxPower` của USB Serial/JTAG khai
  ít nhất cỡ đó. `bMaxPower` chưa biết: nếu nó khai 100 mA thì kịch bản này vượt mức
  khai báo (laptop thường không cắt, nhưng không có gì bảo đảm), và khi đó giới hạn mã
  LED tối đa phải tính lại. Chỉ kết luận tuân thủ sau khi đo dòng lúc chưa cấu hình và
  dòng hoạt động trên đúng cáp cấp nguồn (bring-up mục 2, 6, 8).
- Dòng khởi động (pre-charge 500 mA của PAM2401, nạp tụ lúc cắm) chưa định lượng, nên
  chưa kết luận được biên an toàn cho cả hệ.
- Phiên 75 phút không đổi kết luận về dòng: laptop chạy pin cấp liên tục; cần theo dõi
  pin laptop và nhiệt LDO, không phải dung lượng pin thiết bị (V1 không có pin). Công
  suất tỏa 0,10–0,19 W chưa đủ để kết luận về nhiệt: bring-up mục 8 chạy cả hệ 75 phút
  và ghi nhiệt độ LDO.
- Các số trên dùng giá trị điển hình hay giả định nên **không phải giới hạn bảo đảm**.
  Bring-up đọc `bMaxPower` (mục 2), đo dòng 5 V USB khi LED ở mã mặc định và ở 0x7F, và
  chụp dòng khởi động bằng oscilloscope (mục 8).
