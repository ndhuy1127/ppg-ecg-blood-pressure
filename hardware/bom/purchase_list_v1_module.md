# Danh sách mua V1-module

> **Trạng thái:** chờ duyệt, chưa đặt hàng.
>
> **Phạm vi:** một bộ module cho bench nối dây, sau đó cắm vào bo đế và bo cổ tay
> V1 ([custom_board_proposal.md](../../configs/hardware/custom_board_proposal.md)
> Phần A). Giá, tồn kho và điều kiện giao tra ngày 2026-10-23 trên trang của từng
> nơi bán; giá có thể đổi khi đặt. Giá DigiKey, ProtoCentral bằng USD, chưa gồm
> thuế nhập khẩu/VAT.

## 1. Đợt 1: mua ngay

### 1.1. DigiKey (một đơn)

| STT | Khối | Linh kiện | Mã nhà sản xuất | Mã DigiKey | SL | Đơn giá | Tồn kho | Phương án thay thế |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PPG | SparkFun Photodetector Breakout MAX30101 (Qwiic) | SEN-16474 | 1568-16474-ND | 1 | $35,03 | 141 | Mouser 474-SEN-16474, $36,49 |
| 2 | IMU | SparkFun 6DoF IMU Breakout BMI270 (Qwiic), bản 1" × 1" | SEN-22397 | 1568-22397-ND | 1 | $18,50 | 491 | Mouser 474-SEN-22397, $18,50 |
| 3 | Bench | SparkFun Flexible Qwiic Cable – Breadboard Jumper (nối MAX30101 ra breadboard) | 17912 | 1568-17912-ND | 1 | $1,95 | 1 579 | Hàn header đực rồi dùng dây Dupont |
| 4 | Sửa breakout ECG | Điện trở 220 kΩ ±1% 0805 (thay R3) | Yageo RC0805FR-07220KL | 311-220KCRCT-ND | 10 | $0,034 | 2 171 | Yageo AC0805FR-07220KL |
| 6 | MCU | Espressif ESP32-S3-DevKitC-1-N8R8 (chính hãng, module ESP32-S3-WROOM-1-N8R8, hai cổng Micro-USB) | ESP32-S3-DEVKITC-1-N8R8 | 1965-ESP32-S3-DEVKITC-1-N8R8-ND | 1 | $15,00 | Kiểm khi đặt | Cùng mã ở nhà phân phối khác (chưa tra) |

- Không nhầm BMI270 với bản SEN-22398 ("Micro", 0,75" × 0,30"); footprint bo cổ
  tay theo bản SEN-22397.
- **MCU (dòng 6, chốt 2026-10-24):** chỉ dùng bản chính hãng, vì footprint U1 của bo
  đế theo DevKitC-1 (hai hàng chân cách 22,86 mm) và bo OEM bán trong nước không
  công bố kích thước hay pinout. Theo
  [hướng dẫn DevKitC-1 v1.1](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html),
  cổng USB-to-UART là Micro-USB và cáp đi kèm hướng dẫn là USB-A – Micro-B. Flash
  8 MB đủ cho firmware (khoảng 208 KB); GPIO47 chạy 3,3 V với WROOM-1-N8R8
  (custom_board_proposal.md A.6 mục 4).
- Tạm tính: $70,82 + phí ship $25 (đơn dưới $150) = **$95,82**, chưa gồm thuế
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
| 8 | Kết nối | Cáp USB-A – Micro-USB (Micro-B), có dây dữ liệu, khoảng 1 m | Chưa chọn nơi bán | 2 | Chưa tra | — | Cáp Micro-USB có dữ liệu bất kỳ (không dùng cáp chỉ sạc) |
| 9 | Bench | [Header đực 1×40, 2,54 mm](https://hshop.vn/rao-duc-don-chon-thang-40chon) | hshop | 2 | 2.000 đ | Còn hàng | — |
| 10 | Bench | [Dây Dupont cái–cái 20 cm, 40 sợi](https://hshop.vn/day-cam-breadboard-cai-cai-20cm-cap-det-40-soi-f-f-jumper-wire) | hshop | 1 | 30.000 đ | Còn hàng | — |
| 11 | Bench | [Dây Dupont đực–cái 20 cm, 40 sợi](https://hshop.vn/day-cam-breadboard-duc-cai-20cm-cap-det-40-soi-m-f-jumper-wire) | hshop | 1 | 30.000 đ | Còn hàng | — |

Tạm tính mua trong nước: **214.000 đ** cộng 2 cáp Micro-USB (chưa tra giá), chưa
gồm phí ship.

- MCU mua qua DigiKey (dòng 6, mục 1.1). Bo OEM "ESP32-S3-DevKitC N16R8" (thegioiic,
  mã IC42459) trong bản trước của danh sách không mua nữa (2026-10-24): trang bán
  không ghi module, kích thước hay pinout, nên không bảo đảm cắm vừa bo đế.
- Hai cáp Micro-USB dùng cho bench: một vào cổng USB native (packet), một vào cổng
  UART (log). Khi đo trên người chỉ nối một cáp
  ([an toàn buổi đo](../../docs/ethics/session_safety_stopping_v0.1.md)).

### 1.4. Đồ dựng kích thích cho phép đo 10 phút

Theo [sync_10min_test_plan.md](../test_reports/sync_10min_test_plan.md) mục 3.
Kiểm đồ có sẵn ở lab trước, chỉ mua phần thiếu; chưa tra giá.

| Linh kiện | SL | Dùng cho |
| --- | --- | --- |
| Breadboard 830 lỗ | 1 | Bench nối dây |
| Điện trở chân cắm 1 MΩ và 1 kΩ | Vài cái mỗi loại | Mạch chia áp đưa xung GPIO 3,3 V xuống vài mV vào đầu vào ECG |
| LED 5 mm và điện trở hạn dòng | 2 | Kích thích quang trên cửa sổ MAX30101 |
| Dây kẹp cá sấu | 4 | Nối mạch chia áp vào đầu bấm của cáp ECG |
| Hộp tối nhỏ | 1 | Che MAX30101 khi đo |

## 2. Đợt 2: mua cùng PCB V1 (chưa mua)

Chỉ đặt sau khi đối chiếu module thật với footprint (A.6 mục 2) và có số đo bench
đầu tiên. Danh sách lấy từ schematic KiCad V1-module
(`hardware/kicad/v1_module/`).

| Bo | Ký hiệu | Linh kiện | SL |
| --- | --- | --- | --- |
| Đế | U1 | Socket cái 1×22, 2,54 mm, cho DevKitC | 2 |
| Đế | J1 | Socket cái 1×10, 2,54 mm, cho header SV1 của breakout MAX30001 | 1 |
| Đế | J2 | Box header IDC 2×8, 2,54 mm, đứng | 1 |
| Cổ tay | J1 | Box header IDC 2×8, 2,54 mm, cong 90°, có khóa | 1 |
| Cáp | — | Cáp dẹt 16 dây + 2 socket IDC 2×8 có gờ khóa, dài 20–30 cm | 1 |
| Đế | SW1 | Nút nhấn 6 × 6 mm chân cắm | 1 |
| Đế | D1 | LED 3 mm | 1 |
| Đế | R2 / R3 / R8 | Điện trở 0805: 10 kΩ / 1 kΩ / 100 kΩ | 1 / 1 / 1 |
| Đế | R9–R11 | Điện trở 0805 33 Ω | 3 |
| Đế + cổ tay | C3, C5, C7; C2 cổ tay | Tụ 0805 10 µF | 4 |
| Đế + cổ tay | C2, C4, C6, C8, C9 (mặt dưới, sát J2); C3 cổ tay | Tụ 0805 100 nF | 6 |
| Cả hai | — | Spacer nylon M3 kèm vít/đai ốc: 3 lỗ ở bo cổ tay, 1 lỗ bắt vít breakout ở bo đế | 4 |
| Đế | — | Chân cao su dán (mặt dưới có R9–R11 và C9) | 4 |
| Cả hai | — | Gia công PCB bo đế và bo cổ tay | 1 bộ |

## 3. Kiểm tra khi nhận hàng

Trình tự đầy đủ, kể cả bước cấp nguồn:
[v1_bringup_procedure.md](../test_reports/v1_bringup_procedure.md).

1. **ESP32-S3-DevKitC-1-N8R8:**
   - Đo khoảng cách hai hàng chân (footprint KiCad: 22,86 mm).
   - So từng chân với bảng A.7, đặc biệt GPIO47 (`ECG_INT2B`), 3V3 và GND.
   - Ký hiệu trên vỏ module phải là ESP32-S3-WROOM-1-N8R8; đọc loại chip và eFuse
     VDD_SPI bằng lệnh chỉ đọc của esptool, đo INT2B ở phía MCU: GPIO47 phải chạy
     3,3 V (A.6 mục 4).
   - Đọc nhãn hai cổng (UART và USB) để biết cổng nào gửi packet (firmware README).
2. **Breakout MAX30001:** kiểm revision so với `pc_max30001_brk_v1.0` và cỡ của R3,
   R7, R8. Theo file Eagle ở commit `99705eb` (2022-10-11) của repo
   `Protocentral/protocentral_max30001`: R3 10 kΩ cỡ 0805, R7/R8 0 Ω cỡ 0402.
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
