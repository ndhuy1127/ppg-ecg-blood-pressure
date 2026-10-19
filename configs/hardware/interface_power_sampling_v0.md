# Nguồn, mức logic, giao tiếp và cấu hình lấy mẫu dự kiến — V0

> Mọi thông số là thiết kế
> trên giấy, chưa đo trên phần cứng. Không dùng tài liệu này để cấp nguồn hay nối
> dây khi chưa đối chiếu module thực tế nhận về.

Tài liệu gom các đầu ra Tuần 2 còn thiếu dạng văn bản: bảng nguồn và mức logic,
giao tiếp, pin map, khả năng lấy mẫu của từng linh kiện và sơ đồ khối đã sửa.
Nguồn thông số xem [datasheets/README.md](../../hardware/datasheets/README.md).
Trích dẫn dạng "MAX30001 tr. 26, Bảng 4" là trang/bảng của datasheet gốc đã đọc;
**[BRK]** là theo schematic breakout của ProtoCentral.

## 1. Sơ đồ khối (bản văn bản, thay cho các điểm sai trong PNG)

```mermaid
flowchart LR
    E["Điện cực ECG<br/>Ag/AgCl gel hoặc điện cực khô"] -->|analog, qua jack 3,5 mm| ECG["Breakout MAX30001<br/>LDO 1,8 V + TXB0108 + dao động 32,768 kHz"]
    PPGM["Module PPG MAX30101 hoặc MAX30102<br/>(LED + photodiode + ADC tích hợp)"]
    ECG -->|SPI + INTB (+ INT2B nếu dùng SAMP)| MCU["ESP32-S3-DevKitC-1 N16R8<br/>clock thời gian chung: esp_timer µs"]
    PPGM -->|I²C + INT| MCU
    MCU -->|USB| PC["Laptop chạy pin<br/>ghi packet + thời điểm nhận"]
    USB5["5 V từ USB laptop"] --> MCU
    MCU -->|3V3 từ LDO DevKitC| ECG
    MCU -->|3V3 hoặc 5V tùy module| PPGM
```

V0 dùng nguồn USB từ laptop chạy pin (không cắm sạc). Khối pin LiPo, bảo vệ pin
và DC-DC trong PNG **chưa có trong BOM V0.1 hay schematic**; nếu giữ, phải bổ sung
linh kiện cụ thể.

### Các điểm cần sửa trong `Hardware_Diagram.png`

| Vị trí trong hình | Vấn đề | Sửa đề xuất |
| --- | --- | --- |
| Khối "Cảm biến PPG – LED + Photodiode" đưa "tín hiệu PPG (analog)" vào MAX30101 | MAX30101/MAX30102 là module tích hợp LED, photodiode, ADC và FIFO (MAX30101 tr. 1, tr. 10); không có đầu vào analog từ cảm biến ngoài | Gộp thành một khối module PPG, nối I²C và INT tới MCU |
| Nhãn bước sóng 940 nm | LED IR: 870 / 880 / 900 nm (min / điển hình / max) (MAX30101 tr. 4; MAX30102 tr. 4) | Ghi 880 nm |
| Nhãn 530 nm (LED xanh) | LED xanh MAX30101: 530 / 537 / 545 nm (tr. 4), nên 530 nm chưa sai nhưng thiếu chính xác. **MAX30102 không có LED xanh** (tr. 4, tr. 9) | Ghi "≈537 nm, chỉ MAX30101" hoặc bỏ nếu chọn MAX30102 |
| "1.8 V (Analog) cho MAX30101 – LED/PD" | 1,8 V (1,7–2,0 V) là nguồn VDD của IC; LED cần nguồn VLED+ riêng: 3,1–5,0 V cho đỏ/IR, 4,5–5,5 V cho LED xanh (MAX30101 tr. 2) | Tách VDD 1,8 V và VLED+; ghi rõ do module tạo hay lấy từ ngoài |
| Bảng "MAX30001 3.3 V (VDD, VIO)" | Ở mức IC: AVDD/DVDD 1,1–2,0 V, OVDD 1,65–3,6 V (MAX30001 tr. 8). Breakout ProtoCentral nhận 3,3 V ở header rồi hạ xuống 1,8 V bằng LDO [BRK] | Ghi "breakout: 3,3 V tại header; IC: 1,8 V qua LDO onboard" |
| "Kiểm tra đồng bộ bằng … so sánh mốc đặc trưng (R-peak, chân sóng PPG)" | Khoảng R-peak → chân PPG là PAT, chứa độ trễ sinh lý; dùng nó để kiểm tra đồng bộ là đánh đồng PAT với lệch clock | Kiểm tra đồng bộ bằng kích thích chung đã biết thời điểm (xem kế hoạch đo 10 phút) |
| "Lấy mẫu 500 Hz" có dấu ✓ | MAX3010x không có tốc độ 500 sps (MAX30102 tr. 19, Bảng 6); dấu ✓ dễ hiểu nhầm là đã đạt | Ghi "mục tiêu, chờ chốt"; bỏ dấu ✓ cho các mục chưa kiểm chứng |
| Khối nguồn pin LiPo → OVP/OCP → Buck | Không có trong BOM V0.1 | Ghi "đề xuất, chưa có trong BOM" hoặc bỏ khỏi V0 |

## 2. Bảng nguồn và mức logic

| Khối | Linh kiện / module | Cấp vào module | Rail bên trong IC | Mức logic tại MCU | Nguồn |
| --- | --- | --- | --- | --- | --- |
| MCU | ESP32-S3-DevKitC-1 N16R8 | USB 5 V, hoặc chân 5V, hoặc chân 3V3 — **ba cách loại trừ nhau**, không cấp đồng thời | 3,3 V qua LDO trên DevKitC | GPIO 3,3 V; VIH ≥ 0,75·VDD ≈ 2,48 V; VIL ≤ 0,25·VDD ≈ 0,83 V | DevKitC User Guide v1.1; ESP32-S3 datasheet v2.2 |
| ECG AFE | ProtoCentral MAX30001 breakout | VDD 3,3 V tại header [BRK] | AVDD = DVDD 1,1–2,0 V; OVDD 1,65–3,6 V (MAX30001 tr. 8); breakout cấp 1,8 V từ LDO AP2112K-1.8 [BRK] | SPI qua TXB0108, logic theo VDD = 3,3 V [BRK]. Ở chân IC: VIH ≥ 0,7·OVDD (tr. 8) | MAX30001 tr. 8; [BRK] |
| PPG AFE | MAX30101 hoặc MAX30102 (**chưa chốt**, BOM V0.1 để trống) | Phụ thuộc module mua | VDD 1,7–2,0 V. VLED+: MAX30102 3,1–5,0 V (điển hình 3,3 V); MAX30101 3,1–5,0 V cho đỏ/IR và **4,5–5,5 V cho LED xanh** (MAX30102 tr. 2; MAX30101 tr. 2) | SDA, INT open-drain; SCL/SDA của IC có VIH ≥ 0,7·VDD và chịu được tới 6 V (tuyệt đối tối đa "All other pins", tr. 2), nên kéo lên 3,3 V được. Một số module kéo I²C lên 1,8 V, thấp hơn VIH của ESP32 → **phải đo** | MAX30102 tr. 2, 4, 8; MAX30101 tr. 2, 5, 9 |
| IMU (tùy chọn) | BMI270 | 3V3 | VDD 1,71–3,6 V; VDDIO 1,2–3,6 V, **bắt buộc cấp** cho giao tiếp; tụ 100 nF tại VDDIO và VDD | Theo VDDIO | BST-BMI270-DS000-08 |

Lưu ý:

- Nếu cần LED xanh của MAX30101 (thường dùng cho PPG cổ tay), VLED+ phải 4,5–5,5 V,
  tức phải lấy từ 5 V chứ không từ 3V3.
- MAX3010x cần tụ bypass ≥ 1 µF sát chân VLED+ và đường cấp có trở kháng ≪ 1 Ω, để
  xung dòng LED không thành nhiễu quang (MAX30102 tr. 23).
- IMU **chưa chốt là bắt buộc** cho V0. Nếu không dùng, bỏ khỏi pin map và
  BOM; nếu dùng, phải cấp VDDIO và thêm tụ decoupling.

## 3. Giao tiếp và pin map

Pin map dưới đây lấy từ `configs/hardware/Pin_Map_V1.md` trên nhánh
`dev/ducanh` (commit `9073aa8`). Bảng này khớp với netlist dựng lại từ
`hardware/schematics/V1.SchDoc` (commit `bb6605b`). Mọi GPIO đều có trên header
DevKitC và không trùng chân strapping (0, 3, 45, 46), PSRAM octal (35–37), USB
(19, 20) hay UART0 (43, 44).

| Tín hiệu | GPIO | Thiết bị | Ghi chú |
| --- | ---: | --- | --- |
| `SPI_SCK` | 11 | MAX30001, BMI270 | Không phải chân IOMUX gốc của FSPI (GPIO12), đi qua GPIO matrix; chấp nhận được ở vài MHz. MAX30001 cho SCLK tới 12 MHz, SPI mode 0 hoặc 3 (MAX30001 tr. 10, tr. 36) |
| `SPI_MOSI` | 10 | MAX30001, BMI270 | Như trên (IOMUX gốc là GPIO11) |
| `SPI_MISO` | 13 | MAX30001, BMI270 | **Rủi ro:** SDO của MAX30001 tự chuyển trở kháng cao khi CSB mức cao (tr. 19), nhưng trên breakout tín hiệu đi qua TXB0108 luôn bật [BRK], có thể không nhả đường MISO → cần đo, hoặc tách bus |
| `ECG_CS` | 14 | MAX30001 CSB | |
| `ECG_INT` | 5 | MAX30001 INTB | Tích cực mức thấp. Mặc định open-drain kéo lên nội 125 kΩ; chọn được CMOS bằng `INTB_TYPE` (tr. 43). Đi qua TXB0108 nên nên kiểm tra và cân nhắc CMOS |
| — (đề xuất) | trống | MAX30001 INT2B | Mang xung `SAMP` tại thời điểm lấy mẫu ECG (tr. 42, tr. 44). V1 để trống chân này; đề xuất nối vào một GPIO rảnh (mục 5) |
| `BMI_CS` | 12 | BMI270 CSB | Chỉ khi dùng IMU |
| `BMI_INT` | 4 | BMI270 INT1 | Chỉ khi dùng IMU |
| `PPG_SDA` | 8 | MAX3010x SDA | I²C tối đa 400 kHz; địa chỉ ghi/đọc 0xAE/0xAF (MAX30102 tr. 5) |
| `PPG_SCL` | 9 | MAX3010x SCL | Kiểm tra mức pull-up |
| `PPG_INT` | 6 | MAX3010x INT | Open-drain, tích cực mức thấp; cần pull-up (ví dụ 4,7 kΩ) tới điện áp ≤ 5 V (MAX30102 tr. 24) |

**Khác biệt với kế hoạch chân trong `BOM_V0.1.xlsx`:** V0.1 dùng SCK/MOSI/MISO =
12/11/13, CS = 9/14, I²C = 1/2, INT MAX30001/BMI270 = 5/6, INT PPG = 4 và một dòng
"SYNCH của MAX30001" ở GPIO7. **MAX30001 không có chân SYNCH**: danh sách chân
(tr. 18–19) không có chân này; `SYNCH` là lệnh ghi qua SPI vào thanh ghi 0x09
(tr. 46). Chân phần cứng có ích cho đồng bộ là INT2B (xung `SAMP`).

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
- **Muốn 500 Hz ở SpO2 mode** (1000 sps, trung bình 2) thì độ rộng xung chỉ được
  69 hoặc 118 µs, tức ADC 15–16 bit.
- **Độ trễ trong AFE:**
  - MAX30001: tr. 26, Bảng 4. Ví dụ 512 sps: 19,836 ms không LPF, 31,555 ms có
    LPF; 128 sps: 102,844 / 149,719 ms; 125 sps: 105,313 / 153,313 ms. Độ trễ này
    cùng bậc với PAT, phải ghi theo cấu hình và hiệu chỉnh.
  - MAX3010x: datasheet không cho độ trễ; lấy trung bình N mẫu thêm trễ ước lượng
    (N−1)/2 chu kỳ lấy mẫu gốc. Phải đo.
- **Tốc độ cấu hình khác tốc độ thực.** MAX30001 chạy theo dao động 32,768 kHz (cả
  FMSTR 01 cũng suy ra từ đó, tr. 27, Bảng 6). MAX3010x dùng dao động nội; clock
  ADC 10,2–10,8 MHz (MAX30101 tr. 3) hoặc 10,32–10,64 MHz (MAX30102 tr. 3), và
  datasheet không nêu sai số tốc độ lấy mẫu. Tốc độ thực của từng kênh phải đo
  (xem kế hoạch đo 10 phút).

**Phương án dự kiến (chưa chốt):** ECG 512 sps (FMSTR 00, đúng tần số dao động trên
breakout); PPG 100 hoặc 200 sps ở chế độ được chốt, không lấy trung bình hoặc lấy
trung bình có ghi độ trễ. Mục tiêu 500 Hz cho PPG trong
`hardware_requirements_for_V0.md` chỉ đạt được bằng lấy trung bình và giới hạn độ
rộng xung như trên.

`configs/hardware/packet_simulation.json` (mô phỏng SYNTHETIC) dùng PPG
128 Hz. Đây là tham số mô phỏng, **không có trong bảng tốc độ MAX3010x**; nên đổi
sang tốc độ đã chốt khi cập nhật mô phỏng.

## 5. Clock, ngắt và đồng bộ

- Clock tham chiếu duy nhất: bộ đếm `esp_timer` (µs, 64 bit, tính từ lúc MCU
  khởi động) trên ESP32-S3. Mọi timestamp trong packet theo clock này.
- MAX30001 báo FIFO ECG đạt ngưỡng `EFIT` qua INTB → GPIO5 (tr. 41, tr. 44).
  MAX3010x báo FIFO gần đầy (`A_FULL`) hoặc có mẫu mới (`PPG_RDY`) qua INT → GPIO6
  (MAX30102 tr. 12). Cách chốt số mẫu và ghi mốc thời gian: packet schema mục 5.
- Không có clock chung giữa hai AFE. Drift giữa hai kênh là chắc chắn có; độ lớn
  phải đo.
- **Đề xuất:** nối INT2B của MAX30001 vào một GPIO rảnh và bật xung `SAMP`
  (`EN_INT2`, `SAMP_IT`; tr. 42–44). MCU chụp `esp_timer` tại cạnh xung, được mốc
  lấy mẫu ECG trực tiếp. MAX3010x không có chân tương đương; phía PPG vẫn dựa vào
  mốc đọc FIFO và phép đo bench.
- Không dùng PAT hay mốc sinh lý để ước lượng lệch clock.

## 6. Quyết định còn mở

1. Linh kiện PPG: MAX30101 hay MAX30102, và module cụ thể (mức pull-up, nguồn VLED+).
2. Chế độ LED, độ rộng xung, tốc độ lấy mẫu PPG và có lấy trung bình hay không.
3. Tốc độ ECG: 500 hay 512 sps (cùng FMSTR tương ứng); xem
   `custom_board_proposal.md`.
4. IMU BMI270 có trong phạm vi V0/V1 không.
5. Có nối INT2B (xung `SAMP`) vào GPIO không.
6. Nguồn V0: USB từ laptop chạy pin, hay thêm khối pin riêng.
