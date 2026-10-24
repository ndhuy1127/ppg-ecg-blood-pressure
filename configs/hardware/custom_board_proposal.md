# Phần cứng: V1 dùng module và bản hoàn chỉnh dùng chip trần

> Chưa đo trên phần cứng.
>
> **Phạm vi:** tài liệu có hai phần. **Phần A** là V1 dùng module và kit có sẵn,
> mục đích thu tín hiệu để xử lý. **Phần B** là bản hoàn chỉnh dạng đeo tay, hàn
> chip trần. Cả hai **khác** `hardware/bom/BOM_V1.xlsx` và
> `hardware/schematics/V1.SchDoc` hiện tại trên nhánh `dev/ducanh` (`9073aa8`):
> bản đó dùng MAX30102 và cho BMI270 chung bus SPI với MAX30001. Không làm bản V0
> nối dây: dùng thẳng PCB V1-module (chốt 2026-10-24). Nguồn, giao tiếp và lấy
> mẫu: [interface_power_sampling_v0.md](interface_power_sampling_v0.md).
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
- **Ưu tiên SPI.** MAX30101 chỉ có I²C, nên dùng một bus I²C riêng, không chung
  với cảm biến khác.
- **Không có TMP117 ở V1** (Huy chốt 2026-10-16) để bo cổ tay nhỏ bằng một nửa;
  nhiệt độ lấy tạm từ cảm biến nhiệt trong chip MAX30101 (chỉ xu hướng).

### A.2. Bo đế (đặt trên bàn)

| Khối | Linh kiện | Giao tiếp, ghi chú |
| --- | --- | --- |
| MCU | ESP32-S3-DevKitC-1-N8R8 chính hãng (chốt 2026-10-24; không dùng bo OEM vì không bảo đảm hàng chân 22,86 mm) | Cấp nguồn và truyền dữ liệu qua USB với laptop **đang chạy pin, không cắm sạc** |
| ECG | Breakout ProtoCentral MAX30001 | **SPI bus 1, dùng riêng.** Oscillator 32,768 kHz, LDO 1,8 V và TXB0108 có sẵn trên breakout. Thiết lập V1 chốt ngày 2026-10-23: 512 sps, gain/DHPF/DLPF cố định (độ trễ ECG phụ thuộc các thiết lập này, Table 4 tr. 26, nên bản hoàn chỉnh phải giữ cùng thiết lập); SPI MAX30001 4 MHz; SPI BMI270 bắt đầu 1 MHz, lên 2 MHz sau khi đo scope; I²C MAX30101 400 kHz (lùi 100 kHz nếu sườn lên qua cáp quá chậm) |
| Điện cực ECG | Ba điện cực dán Ag/AgCl (10 miếng kèm kit, hoặc 3M Red Dot 2228) qua cáp 3 điện cực LA/RA/RL kèm kit | Qua jack 3,5 mm của breakout. Đạo trình I, 3 điện cực theo Figure 17c của datasheet MAX30001 (tr. 84), chốt 2026-10-23 (protocol v0.2 mục 5.2): LA → ring → ECGP ở **mặt lòng** cổ tay trái (mặt lưng đã có bo PPG); RA → tip → ECGN ở mặt lòng cổ tay phải; RL → sleeve → R3 → VCM ở cẳng tay trái, cách LA khoảng 5 cm. Ánh xạ jack theo schematic `pc_max30001_brk_v1.0`: ring → R4 51 kΩ → ECGP, tip → R5 51 kΩ → ECGN, sleeve → R3 → VCM. Tắt lead bias nội. Cấu hình 2 điện cực (bật lead bias nội) và điện cực khô BIOPAC chỉ để so sánh trên bench. Màu nắp đầu bấm khác nhau tùy lô: đo thông mạch trước khi dùng |
| Sửa trên breakout | R3 (VCM → sleeve của jack) 10 kΩ thay bằng 220 kΩ ±1% (datasheet yêu cầu ≥ 200 kΩ, tr. 22, 31, 35, 84); gỡ R7, R8 (0 Ω nối điện cực vào BIP/BIN) | Làm trước khi đo trên người, sau khi đối chiếu bo thật với `pc_max30001_brk_v1.0`. BioZ không dùng (`EN_BIOZ = 0`). Firmware đặt `INTB_TYPE = 01` (CMOS) ở `EN_INT` (0x02) và `EN_INT2` (0x03) vì INTB/INT2B đi qua TXB0108 (mặc định là open-drain, Table 14, tr. 43) |
| Sự kiện | Nút bấm `t0` (SW1) vào GPIO4, kéo lên 10 kΩ (R2) và tụ 100 nF (C2); LED trạng thái D1 qua 1 kΩ (R3) ở GPIO5 | Đánh dấu bắt đầu bơm cuff trên cùng đồng hồ `esp_timer` |
| SPI BMI270 qua cáp | R9, R10, R11 33 Ω ở mặt dưới bo đế, nối tiếp `BMI_SCK`, `BMI_MOSI`, `BMI_CS` (net phía MCU mang hậu tố `_MCU`) | Giảm chấn ở đầu phát cho cáp 20–30 cm; giá trị chỉnh theo đo scope. `BMI_MISO` không có điện trở ở bo cổ tay vì không còn chỗ ngoài courtyard của M1/M3 |
| Phụ | Socket cho DevKitC (2 hàng 1×22) và breakout MAX30001 (header 10 chân SV1); R8 100 kΩ kéo `ECG_CS` lên 3V3; lỗ NPTH 3,2 mm tại (23,87; 2,97) trùng lỗ bắt vít của breakout | Tụ 3V3–GND trên bo đế: C3, C5, C7 (10 µF), C4, C6, C8 (100 nF) và C9 100 nF ở mặt dưới, sát J2.1/J2.2 (đầu vào nguồn của cáp). Mặt dưới bo đế có R9–R11 và C9 nên phải kê chân cao su. Test point (pad 1,0 mm, có nhãn silkscreen): TP1 `3V3`, TP2 `GND`, TP4 `PPG_SCL`, TP5 `BMI_SCK` (phía cáp), TP6 `T0_BTN`. Chốt thêm ngày 2026-10-24, **chưa vẽ trên KiCad**: test point cho bốn đường INT (`ECG_INTB`, `ECG_INT2B`, `PPG_INT`, `BMI_INT`) để kẹp đầu dò suốt phép đo timing, và header J3 1×2 (GPIO6, GND) phát xung kích thích cho phép đo đồng bộ 10 phút. Bus SPI ECG, `PPG_SDA`, `BMI_MOSI/MISO/CS` không có test point: đo tạm ở mối hàn chân header mặt trên DevKitC hoặc breakout. Silkscreen có viền DevKitC/breakout, dấu đầu USB và đầu anten (cắm ngược 180° sẽ chập 3V3–GND), bảng chân cáp ở mặt dưới. Vùng anten (30–49,5 × 0–5 mm) cấm cả đổ đồng, track và via. GPIO6 dành cho J3 (chưa vẽ) |

### A.3. Bo cảm biến cổ tay (gắn trên dây đeo)

| Khối | Linh kiện | Giao tiếp, ghi chú |
| --- | --- | --- |
| PPG | SparkFun Photodetector Breakout MAX30101 (Qwiic), SEN-16474 | **I²C bus 1, dùng riêng.** Chỉ cần cấp 3,3 V (A.4). Không chọn bo có chip MAX32664 (chỉ xuất nhịp tim/SpO2 đã tính) |
| IMU | SparkFun Qwiic 6DoF BMI270 (bản 1×1), mặt dưới bo | **SPI bus 2**, tách khỏi bus của MAX30001. Phải cắt jumper `I2C` và `ADR` để dùng SPI |
| Áp lực | Không dùng FSR ở V1 (nhóm chốt 2026-10-23) | Dây cáp 15–16 chuyển thành GND |
| Cơ khí | Hai khe 3 × 22 mm trên PCB cho dây velcro 20 mm; tấm kính hoặc acrylic che | Bo 40,4 × 31,5 mm theo Edge.Cuts (bản V1-draft3 bỏ tab giữ cáp). Thân nhựa của J1 (box header cong) nằm hoàn toàn ngoài mép trên: theo footprint KiCad, thân bắt đầu cách mép 0,42 mm và sâu khoảng 9,1 mm, chỉ được giữ bằng 16 chân hàn; nhóm chốt giữ nguyên, không nới PCB (2026-10-23): khi cắm/rút luôn giữ thân header và buộc cáp vào dây đeo để lực kéo không dồn vào mối hàn; nếu chân cong hoặc mối hàn nứt khi thử thì xét nới PCB dưới thân header (khoảng 28 × 9,5 mm). Ba lỗ 3,2 mm tại (30,36; 8,14), (10,04; 28,46), (30,36; 28,46) trùng lỗ standoff của M1 và M3, dùng spacer nylon M3; góc thứ tư (10,04; 8,14) nằm trên đường đi dây chính nên dùng miếng đệm dán. Theo ảnh sản phẩm, hai đầu nối Qwiic cao hơn chip cảm biến nên da cổ tay chạm đầu nối trước: tháo đầu nối Qwiic hoặc làm giá đỡ |
| Lắp ráp | Hàn J1 và cả hai header module vào bo cổ tay trước, cắt sát đuôi chân, dán kapton, sau đó mới lắp M1 và M3 lên header. J1 đặt ở mặt dưới nên mối hàn nằm ở mặt trên, là mặt áp vào da | Chân M3 nằm dưới thân M1 và ngược lại (18 cảnh báo `pth_inside_courtyard` là dự kiến). Trên M1 cắt JP1 để tắt LED nguồn đỏ, vì LED này nằm cùng mặt với cảm biến |
| Phụ | C2 10 µF + C3 100 nF trên 3V3–GND ở mặt trên, sát chân cáp J1.1 (đầu vào nguồn; nhìn từ mặt trên là đầu phải hàng chân), dùng chung cho M1 (MAX30101) và M3 (BMI270) | Không có test point trên bo cổ tay. Bảng chân cáp chỉ in ở mặt dưới bo đế; bo cổ tay chỉ có số 1 cạnh J1.1 |

**Cáp nối hai bo (theo KiCad):**

- Đầu bo đế: J2, box header IDC 2×8 bước 2,54 mm
  (`Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical`, DIN 41651), cắm socket IDC
  bấm trên cáp dẹt 16 dây.
- Đầu bo cổ tay: J1, box header IDC 2×8 cong 90°, có khóa
  (`Connector_IDC:IDC-Header_2x08_P2.54mm_Horizontal`), đặt ở mặt dưới. Cửa cắm quay
  ra ngoài mép trên, cáp chạy song song mặt bo. Footprint chuẩn lật xuống mặt dưới
  nên chân 1 nằm ở hàng chân trong, đầu phải khi nhìn từ mặt trên (đầu trái khi nhìn
  từ mặt dưới, mặt lắp J1). Hàn J1 nhầm sang mặt trên cũng đưa chân 1 vào lỗ GND. Bản V1-draft2 dùng 16 lỗ hàn dây,
  đánh số theo chiều mặt trên; nếu cắm một đầu nối cứng vào đó thì chân 1 rơi vào lỗ
  GND.
- Cáp: IDC–IDC 16 dây, hai đầu cái có gờ khóa, sọc đỏ ở chân 1 cả hai đầu, nối
  thẳng (chân n ↔ chân n). Đo thông mạch từng chân trước lần cấp nguồn đầu tiên.
  Socket IDC chỉ giữ bằng ma sát: dán băng keo hoặc buộc cáp vào dây đeo khi đeo.
- Chiều dài dự kiến 20–30 cm (KiCad không thể hiện).
- GND ở chân 2, 4, 7, 9, 14, 15, 16. Các dây tín hiệu kề nhau không có GND xen
  giữa: 5–6 (`PPG_SCL`, `PPG_INT`), 10–13 (`BMI_MOSI`, `BMI_MISO`, `BMI_CS`,
  `BMI_INT`). Chân 1–2 là 3V3 và GND đặt kề nhau.
- Tín hiệu: 3V3, GND, PPG SDA/SCL/INT, BMI270 SCK/MOSI/MISO/CS/INT. Không cần dây
  5 V vì bo MAX30101 tự tạo 5 V.

Bảng chân từng dây: A.7. Schematic và PCB (đã đi dây) của hai bo:
`hardware/kicad/v1_module/base/` và `hardware/kicad/v1_module/wrist/`. Sơ đồ khối:
[hardware_diagram_v1.svg](hardware_diagram_v1.svg).

Rà soát đi dây V1-draft3 (cùng Codex, 2026-10-23): không có lỗi nghiêm trọng. Đã
thêm C9 100 nF tại J2; trên đoạn chéo dài chạy song song, khe hở mép
`T0_BTN`–`ECG_INT2B` tăng từ 0,28 lên khoảng 1,0 mm và `ECG_CS`–`LED_STAT` từ 0,40
lên khoảng 0,9 mm; thêm via GND trên cả hai bo. Giữ nguyên nhánh TP4 (`PPG_SCL`) và
TP5 (`BMI_SCK`) chạy song song 11 mm cách 0,4 mm (pad vuông của D1 chặn đường dời),
và đoạn 3V3 dài khoảng 36 mm (khoảng 44 mΩ) mà dòng xung LED PPG đi chung với VDD
breakout ECG (ước tính sụt áp điện trở 4–9 mV khi dòng bo cổ tay nhảy 100–200 mA,
chưa tính điện cảm). Các phép đo kiểm trên bo thật nằm ở
[trình tự bring-up](../../hardware/test_reports/v1_bringup_procedure.md) mục 8.

### A.4. Bo SparkFun MAX30101: điều đã kiểm trong schematic

Nguồn: `Hardware/SparkFun_MAX30101_Qwiic.sch` (Eagle) trong repo
`sparkfun/SparkFun_Photodetector_Breakout_MAX30101_Qwiic`, nhánh `master`, đọc
ngày 2026-10-16.

| Chức năng | Trên bo | Hệ quả cho bo đế |
| --- | --- | --- |
| Nguồn vào | Chỉ 3,3 V (chân 3.3V và Qwiic) | Cấp 3V3 từ DevKitC |
| VDD 1,8 V của MAX30101 | LDO SP6214 1,8 V/100 mA từ 3,3 V | **Chân header "1.8V" là đầu ra LDO**; không nối nguồn vào |
| VDD_LED (VLED+) | Boost PAM2401 từ 3,3 V lên net 5V | LED xanh có nguồn 5 V ngay trên bo |
| I²C | Chuyển mức bằng 2 MOSFET kênh N; kéo lên 2,2 kΩ ở cả phía 1,8 V và phía 3,3 V (phía 3,3 V qua jumper `I2C PU`) | Bus 1 không cần thêm kéo lên. Không thêm footprint kéo lên I²C trên bo nào (chốt 2026-10-24): với 2,2 kΩ và tổng điện dung ước khoảng 50 pF (cáp 20–30 cm, chân, bộ chuyển mức), thời gian lên 30–70% ≈ 0,85 × 2,2 kΩ × 50 pF ≈ 0,1 µs, dưới 0,3 µs của chế độ 400 kHz. Chưa đo; nếu sườn lên chậm thì chạy 100 kHz (A.2) |
| INT | Kéo lên 4,7 kΩ lên 3,3 V (jumper `INT`) | Nối thẳng GPIO |

### A.5. Không dùng ở V1

LiPo, BQ25180, TPS62840, W25Q128, LDO 1,8 V và oscillator riêng: dữ liệu ghi trên
laptop; nguồn, clock và chuyển mức đã có trên module. Các linh kiện này thuộc
Phần B.

### A.6. Cần kiểm tra trước khi vẽ

Trạng thái ngày 2026-10-24. Mục còn lại chỉ làm được khi có hàng; bước kiểm khi
nhận hàng ở
[danh sách mua](../../hardware/bom/purchase_list_v1_module.md) mục 3.

1. **Đã xong trên thiết kế.** Header breakout MAX30001 đưa INT2B ra chân 4 của SV1
   (`pc_max30001_brk_v1.0.brd`); KiCad V1-module nối vào GPIO47 (net
   `/ECG_INT2B`, U1 pad 28). **Khi nhận hàng:** kiểm revision breakout thật.
2. **Khi nhận hàng:** đối chiếu module thật với footprint (khoảng cách hai hàng
   chân DevKitC 22,86 mm, pinout, lỗ bắt vít). PCB được đặt gia công trước khi có
   module (chốt 2026-10-24), nên nếu lệch footprint thì phải làm lại PCB.
3. **LED MAX30101.**
   - Tổ hợp tốc độ × độ rộng xung: datasheet Rev 2 (19-8453, 10/18, bản SparkFun
     lưu) chỉ có bảng tổ hợp được phép cho chế độ SpO2 và HR (Bảng 11–12, tr. 24),
     không có bảng cho multi-LED. Bảng 15–16 của Rev 3 (tr. 29–30) chép ở
     `interface_power_sampling_v0.md` mục 4 cũng chỉ có SpO2 và HR; chưa kiểm lại
     phần còn lại của Rev 3. Với multi-LED chỉ có khoảng cách cạnh lên giữa hai khe
     427 / 525 / 720 / 1 107 µs ứng với độ rộng xung 69 / 118 / 215 / 411 µs
     (Rev 2: Bảng 14, tr. 26). V1 chốt ba khe (`SLOT1` xanh, `SLOT2` đỏ, `SLOT3` IR) ở
     **200 sps** mỗi khe, `SMP_AVE = 1` (2026-10-24). Ở 200 sps, với độ rộng xung 411 µs, từ cạnh lên của khe đầu
     tới cạnh xuống của khe cuối là 2 × 1 107 + 411 = 2 625 µs, khoảng nửa chu kỳ
     5 000 µs. Con số này chỉ tính thời gian phát xung theo giá trị danh định,
     chưa gồm thời gian xử lý sau khe cuối, nên không chứng minh tổ hợp được hỗ
     trợ. Không dùng 400 sps với 411 µs (2 625 µs > 2 500 µs). Chip tự đổi sang
     tốc độ hợp lệ nếu tổ hợp không được phép (`interface_power_sampling_v0.md`
     mục 4). **Khi có bo:** đọc lại thanh ghi `SPO2_SR` và đo tốc độ ra từng khe;
     chọn độ rộng xung 411 hay 215 µs bằng số đo này.
   - VLED: bo SparkFun tạo VLED+ bằng boost PAM2401 (A.4) với chia áp phản hồi
     R1 750 kΩ / R4 100 kΩ, tức 0,6 × (1 + 7,5) = **5,1 V danh định** (công thức
     VOUT = 0,6 (1 + R1/R2), Diodes DS37285 Rev 1-2, tr. 5). Mức này nằm trong dải
     4,5–5,5 V của LED xanh nhưng vượt 0,1 V dải 3,1–5,0 V mà datasheet bảo đảm
     PSRR cho LED đỏ/IR; giới hạn tuyệt đối là 6,0 V (MAX30101 Rev 2, tr. 2).
     Datasheet PAM2401 ghi dòng ra tới 1 000 mA ở VIN 3 V, VOUT 5 V (tr. 1), sơ đồ
     ứng dụng MAX30101 ghi nguồn +5 V "200 mA MAX" (tr. 32); hai số này không
     chứng minh bo đủ dòng, vì còn phụ thuộc cuộn cảm, nguồn 3V3 vào (dòng vào
     ≈ 5,1 × I_out / (3,3 × hiệu suất), cộng tải của MCU, ECG và IMU) và LDO 3V3
     của DevKitC. **Khi có bo:** đo VLED+ khi không tải, quá áp lúc khởi động
     và gợn khi LED xanh chạy xung dòng cao nhất đã chọn, so với dải chung
     4,5–5,0 V của cả ba LED; đo 3V3 tại bo cổ tay cùng lúc, vì 3V3 đi qua cáp
     20–30 cm từ DevKitC.
4. **Đã đối chiếu tài liệu module.** Module ESP32-S3-WROOM-1-N16R8 có flash 16 MB
   Quad SPI và PSRAM 8 MB Octal SPI (datasheet WROOM-1/1U v1.8, Bảng 1-1, tr. 3);
   VDD_SPI 1,8 V chỉ có ở bản N16R16VA (chú thích 7, tr. 4), và GPIO47/48 chạy
   1,8 V chỉ ở module dùng chip ESP32-S3R16V (chú thích c, tr. 12). Với module có
   PSRAM, VDD_SPI được cố định bằng eFuse lúc xuất xưởng, không theo mức GPIO45
   (tr. 39). Vậy với WROOM-1-N16R8 và N8R8 chính hãng, GPIO47 (`ECG_INT2B`) chạy
   3,3 V như các GPIO khác; kết luận này chỉ áp dụng cho họ module WROOM-1.
   **Khi nhận hàng:** dùng bản chính hãng DevKitC-1-N8R8 (chốt 2026-10-24), vẫn đọc ký hiệu trên vỏ module, đọc
   loại chip và cấu hình eFuse VDD_SPI bằng lệnh chỉ đọc của esptool, và đo
   INT2B ở phía MCU (sau TXB0108 của breakout) lên 3,3 V. Nếu GPIO47 chạy 1,8 V
   thì không dùng được với thiết kế này.

### A.7. Bảng chân của KiCad V1-module

Bảng dưới lấy từ `hardware/kicad/v1_module/base/v1_base.kicad_pcb` (pad → net
của U1) và tên chân trong symbol `ESP32-S3-DevKitC-1` của
`v1_base.kicad_sch`; cáp lấy từ J1 của `v1_wrist.kicad_pcb` và J2 của
`v1_base.kicad_pcb`. Đây là **pin map chuẩn của V1** (chốt 2026-10-23); firmware
dùng cùng bảng này trong `firmware/boards/board_v1_module.h`. Pin map V1 cũ
(`Pin_Map_V1.md`, `V1.SchDoc` trên nhánh `dev/ducanh`: MAX30001 và BMI270 chung SPI,
không nối INT2B) không dùng nữa.

**GPIO của DevKitC (U1):**

| Net | GPIO | U1 pad | Thiết bị | Ghi chú |
| --- | ---: | ---: | --- | --- |
| `/ECG_CS` | 7 | 7 | MAX30001 CSB (J1 bo đế = SV1 chân 7) | R8 100 kΩ kéo lên 3V3 |
| `/ECG_SCLK` | 15 | 8 | MAX30001 SCLK (J1 bo đế = SV1 chân 8) | SPI bus 1. GPIO15 cũng là XTAL_32K_P (mục 7 Việc còn mở) |
| `/ECG_MOSI` | 16 | 9 | MAX30001 MOSI (J1 bo đế = SV1 chân 9) | GPIO16 cũng là XTAL_32K_N (mục 7 Việc còn mở) |
| `/ECG_MISO` | 17 | 10 | MAX30001 MISO (J1 bo đế = SV1 chân 10) | |
| `/ECG_INTB` | 21 | 27 | MAX30001 INTB (J1 bo đế = SV1 chân 5) | |
| `/ECG_INT2B` | 47 | 28 | MAX30001 INT2B (J1 bo đế = SV1 chân 4) | Xung `SAMP` nếu firmware bật (mục 7 Việc còn mở). Chạy 3,3 V với module WROOM-1-N16R8/N8R8; 1,8 V chỉ ở chip ESP32-S3R16V (A.6 mục 4) |
| `/PPG_SDA` | 8 | 12 | MAX30101 SDA (cáp chân 3) | I²C bus 1 |
| `/PPG_SCL` | 9 | 15 | MAX30101 SCL (cáp chân 5) | TP4 |
| `/PPG_INT` | 18 | 11 | MAX30101 INT (cáp chân 6) | |
| `/BMI_CS_MCU` | 10 | 16 | BMI270 CS qua R11 33 Ω (`/BMI_CS`, cáp chân 12) | SPI bus 2 |
| `/BMI_MOSI_MCU` | 11 | 17 | BMI270 SDA/PICO qua R10 33 Ω (`/BMI_MOSI`, cáp chân 10) | |
| `/BMI_SCK_MCU` | 12 | 18 | BMI270 SCL/SCK qua R9 33 Ω (`/BMI_SCK`, cáp chân 8) | TP5 nằm trên `/BMI_SCK` (phía cáp) |
| `/BMI_MISO` | 13 | 19 | BMI270 ADR/POCI (cáp chân 11) | |
| `/BMI_INT` | 14 | 20 | BMI270 INT1 (cáp chân 13) | |
| `/T0_BTN` | 4 | 4 | SW1 | R2 10 kΩ kéo lên, C2 100 nF, TP6 |
| `/LED_STAT` | 5 | 5 | D1 qua R3 1 kΩ | |
| `/+3V3` | — | 1, 2 | Nguồn 3V3 của DevKitC | Chân 5V (pad 21) không nối |
| `/GND` | — | 22, 23, 24, 44 | | |

Không nối: EN và GPIO0, 1, 2, 3, 6 (trước là FSR; sẽ nối J3, chưa vẽ), 19, 20, 35–42, 43, 44, 45, 46, 48.

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
| 15 | `/GND` | 16 | `/GND` |

Bo cổ tay: M1 MAX30101 (mặt trên) dùng chân 1–5 (GND, 3.3V, SDA, SCL, INT);
chân 6 `1.8V_OUT` không nối. M3 BMI270 (mặt dưới) dùng GND, 3.3V, PICO, SCK, POCI, CS,
INT1 (ASDX, ASCX, INT2, OCS, OSDO không nối). Không còn J2 (FSR đã bỏ).

Định dạng file: PCB lưu bằng KiCad 10.0, schematic bằng KiCad 9.0; mở
`.kicad_pcb` bằng KiCad ≥ 10.

## Phần B — bản hoàn chỉnh dùng chip trần

Các mục 1–6 dưới đây áp dụng cho bản hoàn chỉnh. Mục 7 (Việc còn mở) gom việc
còn mở của cả Phần A và Phần B.

## 1. Danh sách linh kiện

| Khối | Linh kiện | Ghi chú |
| --- | --- | --- |
| MCU | Module ESP32-S3 (ví dụ WROOM-1 N16R8) | Dùng module có anten và chứng nhận RF, không dùng chip trần. PSRAM octal chiếm GPIO35–37 (datasheet WROOM-1/1U v1.8, chú thích b, tr. 12) |
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

- **ECG 512 sps, FMSTR 00**, FCLK = 32,768 kHz (MAX30001 tr. 49, Bảng 26). Chốt
  cho V1 ngày 2026-10-23 (A.2) và bản hoàn chỉnh giữ cùng thiết lập để dữ liệu V1
  dùng lại được; khớp `FS_NOMINAL_MHZ = 512 000` trong packet schema (đơn vị mHz, tức
  512 Hz).
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
| PPG | 200 sps, 3 khe (xanh + đỏ + IR), N = 16 (106 B/packet) | ≈ 4,0 kB/s |
| IMU | Packet schema V0.2: 6 trục 100 Hz, N = 10 (82 B/packet) | ≈ 4,9 kB/s |

ECG + PPG theo schema ≈ 7,4 kB/s, nên W25Q128 (16 MiB) chứa khoảng **38 phút**
ghi thô; thêm IMU (≈ 12,3 kB/s) thì khoảng **23 phút**. Nếu ghi theo định dạng nén
3 B mỗi mẫu, không có header từng packet, thì thời lượng khoảng gấp đôi. Với đo theo
cửa sổ vài chục giây, tổng thời gian ghi mỗi buổi thường dưới mức này. `N` mỗi
packet còn mở; tính lại khi chốt `N` và khi bản hoàn chỉnh chốt có giữ IMU không.

Bản hoàn chỉnh (Phần B) dự kiến truyền qua BLE hoặc ghi flash, nên mục 13 "Truyền
USB/Serial" của packet schema sẽ cần cập nhật khi làm bản này. V1-module (Phần A)
vẫn truyền qua USB tới laptop.

### 6.3. Pin

- Dòng trung bình khi truyền BLE ước khoảng 50–70 mA [chưa đối chiếu]. LiPo
  150 mAh đủ cho buổi 1–2 giờ chỉ khi MCU tiêu thụ thấp giữa các cửa sổ; cách
  ngủ phải theo mục 5. **Phải đo dòng trên bo thật** trước khi chốt.
- Nếu bật WiFi, dòng đỉnh 300–500 mA (2–3C với pin 150 mAh) có thể gây
  brownout: kiểm tra dòng xả tối đa của cell và thêm tụ bulk 22–47 µF ở 3V3
  [chưa đối chiếu].

## 7. Việc còn mở

1. Kênh LED chính của PPG (chọn từ dữ liệu ba kênh của V1).
2. Bản hoàn chỉnh có giữ BMI270, TMP117 và FSR 402 không (V1 có BMI270, không có
   TMP117 và FSR).
3. ADC cho FSR ở bản hoàn chỉnh (nếu giữ FSR): ADC nội ESP32 hay ADC ngoài.
4. Có jack điện cực dán Ag/AgCl để lấy ECG tham chiếu không.
5. Firmware có bật xung `SAMP` của MAX30001 (`EN_INT2`, `SAMP_IT`) hay không. V1 đã
   nối INT2B vào GPIO47 (A.7); bản hoàn chỉnh có nối INT2B không.
6. Ngủ giữa các cửa sổ (thêm thạch anh 32 kHz) hay giữ MCU thức suốt phiên.
7. Xung đột chân: KiCad V1-module dùng GPIO15/16 cho `ECG_SCLK`/`ECG_MOSI`, trùng
   XTAL_32K_P/N của ESP32-S3 (mục 5). V1 không có thạch anh 32 kHz nên không bị
   ảnh hưởng. Nếu bản hoàn chỉnh giữ pin map này thì phải bỏ thạch anh 32 kHz hoặc
   đổi chân SPI ECG.
8. Thứ tự dây cáp: mô tả ban đầu là GND xen giữa các dây tín hiệu, nhưng chân
   10–13 (`BMI_MOSI`, `BMI_MISO`, `BMI_CS`, `BMI_INT`) và 5–6 kề nhau không có GND
   (A.3); 15–16 nay là GND. Đổi thứ tự chân hay giữ nguyên.
9. Tụ: mô tả ban đầu là 100 nF + 10 µF cho mỗi module; bo cổ tay chỉ có một cặp
   C2/C3 dùng chung cho M1 và M3 (A.3). Có bổ sung không.
