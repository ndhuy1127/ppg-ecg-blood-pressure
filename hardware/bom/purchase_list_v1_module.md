# Danh sách mua V1-module

> **Trạng thái (2026-10-28):** đã đặt bo Waveshare ESP32-S3 (2026-10-27); các mục khác
> chưa đặt.
>
> **Phạm vi:** một bộ module cắm thẳng vào bo đế và bo cổ tay V1
> ([custom_board_proposal.md](../../configs/hardware/custom_board_proposal.md)
> Phần A); không làm bench nối dây (chốt 2026-10-24). Giá, tồn kho và điều kiện giao tra ngày 2026-10-23 trên trang của từng
> nơi bán; giá có thể đổi khi đặt. Giá DigiKey, ProtoCentral bằng USD, chưa gồm
> thuế nhập khẩu/VAT.

## 1. Đợt 1: mua ngay

### 1.1. DigiKey (một đơn)

| STT | Khối | Linh kiện | Mã nhà sản xuất | Mã DigiKey | SL | Đơn giá | Tồn kho | Phương án thay thế |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PPG | SparkFun Photodetector Breakout MAX30101 (Qwiic) | SEN-16474 | 1568-16474-ND | 1 | $35,03 | 141 | Mouser 474-SEN-16474, $36,49 |
| 2 | IMU | SparkFun 6DoF IMU Breakout BMI270 (Qwiic), bản 1" × 1" | SEN-22397 | 1568-22397-ND | 1 | $18,50 | 491 | Mouser 474-SEN-22397, $18,50 |
| 4 | Sửa breakout ECG | Điện trở 220 kΩ ±1% 0805 (thay R3) | Yageo RC0805FR-07220KL | 311-220KCRCT-ND | 10 | $0,034 | 2 171 | Yageo AC0805FR-07220KL |
| 6 | MCU | ~~Espressif ESP32-S3-DevKitC-1-N8R8~~ **Đã đặt thay bằng Waveshare ESP32-S3-DEV-KIT-N8R8-M (module Espressif ESP32-S3-WROOM-1-N8R8, header hàn sẵn, một cổng USB-C)** (2026-10-27, xem ghi chú) | ESP32-S3-DEVKITC-1-N8R8 (bản cũ) | — | 1 | — | — | Bo Espressif chính hãng nếu cần thay |

- Không nhầm BMI270 với bản SEN-22398 ("Micro", 0,75" × 0,30"); footprint bo cổ
  tay theo bản SEN-22397.
- **MCU (dòng 6, đổi 2026-10-27):** Đã đặt bo Waveshare ESP32-S3-DEV-KIT-N8R8-M.
  Bo này công bố kích thước và pinout: hai hàng 1×22 cách 22,86 mm, thứ tự chân giống
  hệt DevKitC-1 (đối chiếu từng chân với footprint U1 ngày 2026-10-27; wiki Waveshare
  ghi "Compatible with the pinout of ESP32-S3-DevKitC-1"), module Espressif
  ESP32-S3-WROOM-1-N8R8. Khác bo Espressif: bo **63,30 × 25,40 mm** (chốt 2026-10-27
  theo bản vẽ kích thước của Waveshare: tâm chân đầu cách mép đầu anten 4,91 mm, tâm
  chân cuối cách mép đầu USB 5,05 mm; 4,91 + 21 × 2,54 + 5,05 = 63,30), có 4 lỗ vít
  Ø2 mm cách hai mép 1,80 mm, một cổng USB-C qua hub CH334 và cầu USB–UART CH343, nên
  một cáp mang cả cổng USB native (packet) lẫn UART0 (log). Với chân 1 của U1 ở
  (28,3; 1,6), bo chiếm x 27,03–52,43, y −3,31…59,99 trên bo đế: nhô 3,3 mm quá mép
  trên (đầu anten), không đụng linh kiện. Ghi chú cũ (chốt 2026-10-24): chỉ dùng bản
  chính hãng Espressif, vì bo OEM bán trong nước không công bố kích thước hay pinout. Theo
  [hướng dẫn DevKitC-1 v1.1](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html),
  cổng USB-to-UART là Micro-USB và cáp đi kèm hướng dẫn là USB-A – Micro-B. Flash
  8 MB đủ cho firmware (khoảng 208 KB); GPIO47 chạy 3,3 V với WROOM-1-N8R8
  (custom_board_proposal.md A.6 mục 4).
- Tạm tính: $68,87 + phí ship $25 (đơn dưới $150) = **$93,87**, chưa gồm thuế
  nhập khẩu/VAT. DigiKey giao 1–5 ngày bằng DHL/FedEx/UPS; thuế và phí hải quan
  thu khi nhận hàng
  ([biểu phí ship](https://www.digikey.com/en/help-support/delivery-information/international-shipping-rates?country=VN)).

### 1.2. ProtoCentral (đặt trực tiếp)

| STT | Khối | Linh kiện | Mã | SL | Đơn giá | Tình trạng | Phương án thay thế |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | ECG | [MAX30001 ECG and Respiration/Bio-Impedance Breakout Kit](https://protocentral.com/product/protocentral-max30001/) | PC-MED-0307 | 1 | $49,95 | Hết hàng tạm thời, giao trong 7–10 ngày | Không có bản cắm thẳng vào bo đế; đổi sang ADS1292R phải vẽ lại bo đế |

- Chỉ bán dạng kit: breakout, header thẳng, cáp ECG có jack 3,5 mm, 10 điện cực
  dán. Trang sản phẩm ghi cáp "2 điện cực", còn
  [hướng dẫn ProtoCentral](https://protocentral.com/product/protocentral-max30001/docs/getting-started/)
  ghi cáp 3 điện cực LA/RA/RL; kiểm khi nhận hàng (mục 3).
- DigiKey và Mouser không bán bo này; Tindie không giao về Việt Nam.
- **Chưa kiểm:** phí ship và việc có chọn được Việt Nam khi thanh toán (chỉ hiện
  trong giỏ hàng). Kiểm trước khi xin duyệt.

### 1.3. Mua trong nước

| STT | Khối | Linh kiện | Nơi bán | SL | Đơn giá | Tồn kho | Phương án thay thế |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | Điện cực | [3M Red Dot 2228](https://minhtrimedical.com/dien-cuc-do-tim-3m-2228-red-dot-4cm-x-33cm), 4 × 3,3 cm, hộp 50 miếng | Minh Trí Medical | 1 hộp | 150.000 đ | Còn hàng | 10 điện cực kèm kit MAX30001 |
| 8 | Kết nối | Cáp USB-C có dây dữ liệu, khoảng 1 m, đầu kia khớp cổng laptop (USB-A hay USB-C); đổi 2026-10-27 theo bo Waveshare | Chưa chọn nơi bán | 1 | Chưa tra | — | Cáp USB-C có dữ liệu bất kỳ (không dùng cáp chỉ sạc) |
| 9 | Lắp bo cổ tay | [Header đực 1×40, 2,54 mm](https://hshop.vn/rao-duc-don-chon-thang-40chon) | hshop | 2 | 2.000 đ | Còn hàng | — |

Tạm tính mua trong nước: **154.000 đ** cộng 1 cáp USB-C (chưa tra giá), chưa
gồm phí ship.

- Header đực (dòng 9) để hàn M1 (MAX30101) và M3 (BMI270) lên bo cổ tay
  ([custom_board_proposal.md](../../configs/hardware/custom_board_proposal.md) A.3).

- MCU mua qua DigiKey (dòng 6, mục 1.1). Bo OEM "ESP32-S3-DevKitC N16R8" (thegioiic,
  mã IC42459) trong bản trước của danh sách không mua nữa (2026-10-24): trang bán
  không ghi module, kích thước hay pinout, nên không bảo đảm cắm vừa bo đế.
- Một cáp USB-C mang cả cổng USB native (packet) và UART (log) qua hub trên bo
  Waveshare (đổi 2026-10-27; bo Espressif cần hai cáp). Khi đo trên người chỉ nối một cáp
  ([an toàn buổi đo](../../docs/ethics/session_safety_stopping_v0.1.md)).

### 1.4. Đồ dựng kích thích cho phép đo 10 phút

Theo [sync_10min_test_plan.md](../test_reports/sync_10min_test_plan.md) mục 3.
Kiểm đồ có sẵn ở lab trước, chỉ mua phần thiếu; chưa tra giá.

| Linh kiện | SL | Dùng cho |
| --- | --- | --- |
| Breadboard 830 lỗ | 1 | Dựng mạch kích thích (chia áp, LED) |
| Dây cắm breadboard | Vài sợi | Nối GPIO phát xung với mạch kích thích |
| Điện trở chân cắm 10 MΩ và 3,3 kΩ | Vài cái mỗi loại | Mạch chia áp đưa xung GPIO 3,3 V xuống khoảng 1 mV vi sai vào đầu vào ECG ([kế hoạch đo 10 phút](../test_reports/sync_10min_test_plan.md) mục 3; sửa 2026-10-26, bản trước ghi 1 MΩ và 1 kΩ) |
| LED 5 mm và điện trở hạn dòng | 2 | Kích thích quang trên cửa sổ MAX30101 |
| Dây kẹp cá sấu | 4 | Nối mạch chia áp vào đầu bấm của cáp ECG |
| Hộp tối nhỏ | 1 | Che MAX30101 khi đo |

## 2. Đợt 2: mua cùng PCB V1 (chưa mua)

Đặt gia công PCB ngay sau khi sửa bo đế (header J3, V1-draft4;
`custom_board_proposal.md` A.2) và ERC/DRC sạch, song song với đợt 1, không chờ
module (chốt 2026-10-24); lệch footprint thì làm lại PCB (A.6 mục 2). Trước khi gửi
file: in tờ kiểm footprint tỉ lệ 1:1 của từng bo (lớp fab, courtyard, silkscreen,
cạnh bo; mặt dưới in lật; kiểm thước 50 mm trên tờ in) và so các khoảng cách chính
với bản vẽ của nhà sản xuất (hai hàng chân DevKitC 22,86 mm, header và lỗ vít của ba
breakout); Gerber, file khoan và tờ kiểm xuất bằng `kicad-cli` ra ngoài thư mục dự án
(không lưu trong repo), lần đầu ngày 2026-10-25 từ commit `98279b9` (V1-draft4). **Bản V1-draft5
(2026-10-27: breakout ECG dời 0,5 mm, 3V3 hình sao, viền bo Waveshare, ghi chú M3;
`custom_board_proposal.md` A.3) thay bản này; Gerber và file khoan V1-draft5 xuất ngày 2026-10-27 bằng `kicad-cli`,
gửi nhà mạch thành hai thiết kế riêng, không lưu trong repo.** Danh sách lấy từ schematic KiCad V1-module
(`hardware/kicad/v1_module/`).

| Bo | Ký hiệu | Linh kiện | SL |
| --- | --- | --- | --- |
| Đế | U1 | Socket cái 1×22, 2,54 mm, cho DevKitC | 2 |
| Đế | J1 | Socket cái 1×10, 2,54 mm, cho header SV1 của breakout MAX30001 | 1 |
| Đế | J2 | Box header IDC 2×8, 2,54 mm, đứng | 1 |
| Đế | J3 | Header đực 1×2, 2,54 mm (GPIO6, GND), cắt từ header 1×40 ở dòng 9 | 1 |
| Cổ tay | J1 | Box header IDC 2×8, 2,54 mm, cong 90°, có khóa; **khe khóa ở vách xa mặt PCB**, tức hàng chân lẻ ở hàng lỗ xa thân, khớp footprint KiCad `IDC-Header_2x08_P2.54mm_Horizontal` (chốt 2026-10-27). Kiểm bản vẽ của mã chọn trước khi đặt: loại có khe ở vách sát PCB làm cáp đảo ngược (A.3) | 1 |
| Cáp | — | Cáp dẹt 16 dây + 2 socket IDC 2×8 có gờ khóa, dài 20–30 cm | 1 |
| Đế | SW1 | Nút nhấn 6 × 6 mm, 4 chân cắm, lưới chân 6,5 × 4,5 mm (footprint `SW_PUSH_6mm`: hai chân cách 6,5 mm nối sẵn bên trong) | 1 |
| Đế | D1 | LED 3 mm | 1 |
| Đế | R2 / R3 / R8 | Điện trở 0805: 10 kΩ / 1 kΩ / 100 kΩ | 1 / 1 / 1 |
| Đế | R9–R11 | Điện trở 0805 33 Ω | 3 |
| Đế + cổ tay | C3, C5, C7; C2 cổ tay | Tụ 0805 10 µF | 4 |
| Đế + cổ tay | C2, C4, C6, C8, C9 (mặt dưới, sát J2); C3 cổ tay | Tụ 0805 100 nF | 6 |
| Đế | — | Vít, đai ốc và spacer nylon M2 cho lỗ bắt vít breakout MAX30001; spacer cao bằng khe giữa bo đế và breakout khi đã cắm socket (đo khi có hàng); đầu vít hay đai ốc ở mặt trên breakout Ø < 5 mm (chốt 2026-10-27) | 1 bộ |
| Cổ tay | — | Vít, đai ốc và spacer nylon M2; spacer tròn Ø ≤ 4,5 mm hoặc lục giác 4 mm giữa hai cạnh, cao bằng thân nhựa header (thường 2,5 mm, đo khi có hàng); mỗi lỗ hai spacer, một giữa bo cổ tay và M1, một giữa bo cổ tay và M3 (chốt 2026-10-27) | 6 spacer, 3 vít, 3 đai ốc |
| Đế | — | Chân cao su dán (mặt dưới có R9–R11 và C9) | 4 |
| Cả hai | — | Gia công PCB bo đế và bo cổ tay | 1 bộ |

- **Vít và spacer (chốt 2026-10-27):** dùng bộ nylon M2 cho cả bốn lỗ. Ở bo cổ tay, tâm
  mỗi lỗ chỉ cách góc thân nhựa header gần nhất 2,54 mm (hình học của bo SparkFun):
  spacer lục giác cỡ M3 (5,5 mm giữa hai cạnh) lấn vào thân nhựa ít nhất 0,2 mm, spacer
  tròn Ø 4,5 mm còn hở khoảng 0,3 mm, lục giác M2 (4 mm giữa hai cạnh) hở khoảng 0,2 mm.
  Ở bo đế, pad gần lỗ nhất ở mặt trên breakout là tụ C1, cách tâm lỗ 2,52 mm (file
  `pc_max30001_brk_v1.0.brd`), nên đầu vít hay đai ốc ở mặt đó phải nhỏ hơn Ø 5 mm; đầu
  vít M3 thường (Ø 5,5 mm) chạm pad. Mặt dưới breakout không có linh kiện quanh lỗ.

## 3. Kiểm tra khi nhận hàng

Trình tự đầy đủ, kể cả bước cấp nguồn:
[v1_bringup_procedure.md](../test_reports/v1_bringup_procedure.md).

1. **Waveshare ESP32-S3-DEV-KIT-N8R8-M:**
   - Đo khoảng cách hai hàng chân (footprint KiCad: 22,86 mm).
   - So từng chân với bảng A.7, đặc biệt GPIO47 (`ECG_INT2B`), 3V3 và GND.
   - Ký hiệu trên vỏ module phải là ESP32-S3-WROOM-1-N8R8; đọc loại chip và eFuse
     VDD_SPI bằng lệnh chỉ đọc của esptool, đo INT2B ở phía MCU: GPIO47 phải chạy
     3,3 V (A.6 mục 4).
   - Một cáp USB-C cho hai cổng COM: USB native `303A:1001` (packet) và CH343 (log
     UART0); ghi cổng nào là cổng nào (firmware README).
2. **Breakout MAX30001:** kiểm revision so với `pc_max30001_brk_v1.0` và cỡ của R3,
   R7, R8. Theo file Eagle ở commit `99705eb` (2022-10-11) của repo
   `Protocentral/protocentral_max30001`: R3 10 kΩ cỡ 0805, R7/R8 0 Ω cỡ 0402. Silkscreen
   trong file `.brd` này là `pc_max30001/3/4_brk 03/22`, giống ảnh bo đã mua
   (đối chiếu 2026-10-27).
3. **Cáp ECG của kit:** đếm số dây. Phương án 3 điện cực ở A.2 cần dây thứ ba nối
   VCM (sleeve của jack). Chỉ có 2 dây thì phải có cáp 3 điện cực trước khi chạy
   cấu hình này (cáp 3 dây của ProtoCentral, hoặc tự làm từ jack 3,5 mm và 3 dây
   đầu bấm).
4. **SparkFun BMI270:** đúng bản SEN-22397, có jumper `I2C` và `ADR` để cắt khi
   dùng SPI.

## 4. Không mua đợt này

| Linh kiện | Lý do |
| --- | --- |
| FSR 402 | V1 không dùng FSR (chốt 2026-10-23) |
| Điện cực khô BIOPAC ELDRY | Để sau pilot; việc dùng điện cực khô trên người còn mở trong protocol v0.2 |
| TMP117 | V1 không có TMP117 (chốt 2026-10-16) |

## 5. Duyệt và đặt hàng

| Mục | Nội dung |
| --- | --- |
| Người duyệt | |
| Ngày duyệt | |
| Ngày đặt (DigiKey / ProtoCentral / trong nước) | |
| Ngày giao dự kiến | |
| Mã đơn | |
