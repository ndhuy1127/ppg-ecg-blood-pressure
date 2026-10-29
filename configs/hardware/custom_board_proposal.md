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
- **Không có TMP117 ở V1** (chốt 2026-10-16) để bo cổ tay nhỏ bằng một nửa;
  nhiệt độ lấy tạm từ cảm biến nhiệt trong chip MAX30101 (chỉ xu hướng).

### A.2. Bo đế (đặt trên bàn)

| Khối | Linh kiện | Giao tiếp, ghi chú |
| --- | --- | --- |
| MCU | Waveshare ESP32-S3-DEV-KIT-N8R8-M, module Espressif ESP32-S3-WROOM-1-N8R8 (đã đặt 2026-10-27; thay bản DevKitC-1-N8R8 chốt 2026-10-24). Bo 63,30 × 25,40 mm (chốt 2026-10-27, bản vẽ Waveshare; nhô 3,3 mm quá mép trên bo đế). Hai hàng 1×22 cách 22,86 mm, thứ tự chân giống DevKitC-1, khớp footprint U1; một cổng USB-C (hub CH334 + CH343) | Cấp nguồn và truyền dữ liệu qua USB với laptop **đang chạy pin, không cắm sạc**. Một cáp USB-C cho hai cổng COM: USB native `303A:1001` (packet) và CH343 (log UART0), chọn theo VID:PID ([bring-up](../../hardware/test_reports/v1_bringup_procedure.md) mục 2) |
| ECG | Breakout ProtoCentral MAX30001 | **Bus SPI ECG (`SPI2_HOST`), dùng riêng.** Oscillator 32,768 kHz, LDO 1,8 V và TXB0108 có sẵn trên breakout. Thiết lập V1 chốt ngày 2026-10-23: 512 sps, gain/DHPF/DLPF cố định (độ trễ ECG phụ thuộc các thiết lập này, Table 4 tr. 26, nên bản hoàn chỉnh phải giữ cùng thiết lập). Giá trị chốt ngày 2026-10-25: `ECG_GAIN = 00` (20 V/V, thang ±50 mV, tr. 53), `ECG_DLPF = 01` (40,96 Hz, FIR pha tuyến tính, độ trễ 31,555 ms theo Table 4 tr. 26), `ECG_DHPF = 0` (tắt; lọc thông cao 0,5 Hz zero-phase làm offline), phát hiện rời điện cực DC bật: `EN_DCLOFF = 01`, `IMAG = 010` (10 nA), `VTH = 01` (VMID ± 400 mV), `DCLOFF_IPOL = 0` (tr. 48–49); fast recovery tự động (`FAST = 10`, `FAST_TH` mặc định 0x3F, tr. 45); SPI MAX30001 4 MHz; SPI BMI270 bắt đầu 1 MHz, lên 2 MHz sau khi đo scope; I²C MAX30101 400 kHz (lùi 100 kHz nếu sườn lên qua cáp quá chậm). Chốt 2026-10-24: `EFIT = 15` (ngắt INTB khi có 16 mẫu; đọc tới EOF, nên mỗi packet thường 16 mẫu, tối đa 32 = độ sâu FIFO); xung `SAMP` trên INT2B bật luôn và làm mốc thời gian ECG, chốt cạnh bằng MCPWM capture (Packet Schema V0.2 mục 7) |
| Điện cực ECG | Ba điện cực dán Ag/AgCl (10 miếng kèm kit, hoặc 3M Red Dot 2228) qua cáp 3 điện cực LA/RA/RL kèm kit | Qua jack 3,5 mm của breakout. Đạo trình I, 3 điện cực theo Figure 17c của datasheet MAX30001 (tr. 84), chốt 2026-10-23 (protocol v0.2 mục 5.2): LA → ring → ECGP ở **mặt lòng** cổ tay trái (mặt lưng đã có bo PPG); RA → tip → ECGN ở mặt lòng cổ tay phải; RL → sleeve → R3 → VCM ở cẳng tay trái, cách LA khoảng 5 cm. Ánh xạ jack theo schematic `pc_max30001_brk_v1.0`: ring → R4 51 kΩ → ECGP, tip → R5 51 kΩ → ECGN, sleeve → R3 → VCM. Tắt lead bias nội. Hồ sơ đạo đức v0.1 và pilot chỉ dùng cấu hình 3 điện cực Ag/AgCl này trên người (chốt 2026-10-29); cấu hình 2 điện cực (bật lead bias nội) và điện cực khô BIOPAC chỉ thử trên bàn, không người, hoặc sau pilot qua sửa đổi hồ sơ đạo đức. Màu nắp đầu bấm khác nhau tùy lô: đo thông mạch trước khi dùng |
| Sửa trên breakout | R3 (VCM → sleeve của jack) 10 kΩ thay bằng 220 kΩ ±1% (datasheet yêu cầu ≥ 200 kΩ, tr. 22, 31, 35, 84); gỡ R7, R8 (0 Ω nối điện cực vào BIP/BIN) | Làm trước khi đo trên người, sau khi đối chiếu bo thật với `pc_max30001_brk_v1.0`. BioZ không dùng (`EN_BIOZ = 0`). Firmware đặt `INTB_TYPE = 01` (CMOS) ở `EN_INT` (0x02) và `EN_INT2` (0x03) vì INTB/INT2B đi qua TXB0108 (mặc định là open-drain, Table 14, tr. 43) |
| Sự kiện | Nút bấm `t0` (SW1) vào GPIO4, kéo lên 10 kΩ (R2) và tụ 100 nF (C2); LED trạng thái D1 qua 1 kΩ (R3) ở GPIO5 | Đánh dấu bắt đầu bơm cuff trên cùng đồng hồ `esp_timer` |
| SPI BMI270 qua cáp | R9, R10, R11 33 Ω ở mặt dưới bo đế, nối tiếp `BMI_SCK`, `BMI_MOSI`, `BMI_CS` (net phía MCU mang hậu tố `_MCU`) | Giảm chấn ở đầu phát cho cáp 20–30 cm; giá trị chỉnh theo đo scope. `BMI_MISO` không có điện trở ở bo cổ tay vì không còn chỗ ngoài courtyard của M1/M3 |
| Phụ | Socket cho U1 (2 hàng 1×22, thứ tự chân DevKitC-1) và breakout MAX30001 (header 10 chân SV1); R8 100 kΩ kéo `ECG_CS` lên 3V3; lỗ NPTH 3,2 mm tại (23,37; 2,97) trùng lỗ bắt vít của breakout (V1-draft5 dời breakout 0,5 mm sang trái, 2026-10-27) | Tụ 3V3–GND trên bo đế: C3, C5, C7 (10 µF), C4, C6, C8 (100 nF) và C9 100 nF ở mặt dưới, sát J2.1/J2.2 (đầu vào nguồn của cáp). Từ V1-draft5 (2026-10-27) 3V3 chia hai nhánh từ U1: C3, C4, C6–C8 ở nhánh ECG (U1.1 → J1.2), C5 và C9 ở nhánh cáp (U1.2 → J2.1), xem A.3. Mặt dưới bo đế có R9–R11 và C9 nên phải kê chân cao su. Test point (pad 1,0 mm, có nhãn silkscreen): TP1 `3V3`, TP2 `GND`, TP4 `PPG_SCL`, TP5 `BMI_SCK` (phía cáp), TP6 `T0_BTN`. Header J3 1×2 (chân 1 `STIM` = GPIO6, chân 2 GND) phát xung kích thích cho phép đo đồng bộ 10 phút; J3 nằm trên dải 4 mm thêm ở mép dưới (V1-draft4, 2026-10-24), bên trái cổng USB-C của bo Waveshare, nên bo đế nay 53 × 67,3 mm. Các đường INT, bus SPI ECG, `PPG_SDA`, `BMI_MOSI/MISO/CS` không có test point: đo ở mối hàn chân header mặt trên bo Waveshare hoặc breakout (bỏ TP7–TP10 ngày 2026-10-24: pad 1 mm không móc kẹp được, lại thêm nhánh dây dài trên đường INT). Silkscreen có viền bo Waveshare (hở phía trên vì bo nhô quá mép trên) và viền breakout, dấu đầu USB và đầu anten (cắm ngược 180° sẽ chập 3V3–GND), bảng chân cáp ở mặt dưới. Vùng anten (30–49,5 × 0–5 mm) cấm cả đổ đồng, track và via. GPIO6 nối J3.1 (`STIM`) |

### A.3. Bo cảm biến cổ tay (gắn trên dây đeo)

| Khối | Linh kiện | Giao tiếp, ghi chú |
| --- | --- | --- |
| PPG | SparkFun Photodetector Breakout MAX30101 (Qwiic), SEN-16474 | **Bus I²C PPG (`I2C_NUM_0`), dùng riêng.** Chỉ cần cấp 3,3 V (A.4). Không chọn bo có chip MAX32664 (chỉ xuất nhịp tim/SpO2 đã tính). Chốt 2026-10-24: multi-LED ba khe (`SLOT1` xanh, `SLOT2` đỏ, `SLOT3` IR) ở 200 sps mỗi khe, `SMP_AVE = 1`; firmware xóa ngắt `PPG_RDY` sau mỗi mẫu, tới mẫu thứ 8 thì đọc hết FIFO (thường 8 mẫu; Packet Schema V0.2 mục 7.6); độ rộng xung 411 hay 215 µs chọn ở bring-up (A.6 mục 3). Chốt 2026-10-25: dải ADC `SPO2_ADC_RGE = 11` (16 384 nA, LSB 62,5 pA; MAX30101 tr. 19, Bảng 5); dòng LED **hiệu chuẩn theo người**: buổi đầu chỉnh để mức DC mỗi màu khoảng 30–70% thang đo rồi khóa cho người đó ở mọi buổi sau (protocol v0.2 mục 6.1); dòng xanh là tổng của LED3 và LED4 vì khe `011` bật cả hai (tr. 22), nên mỗi nhánh nhận một nửa (mặc định bring-up 7,2 mA mỗi màu: đỏ/IR `0x24`, xanh `0x12` mỗi nhánh); nhiệt độ trong chip đo mỗi 1 s, gửi qua kênh mới `0xB1` của Packet Schema V0.2, mỗi packet một giá trị (chốt 2026-10-25; V0.2 mục 11) |
| IMU | SparkFun Qwiic 6DoF BMI270 (bản 1×1), mặt dưới bo, **mặt chip quay ra ngoài** (xa bo cổ tay) | **Bus SPI IMU (`SPI3_HOST`)**, tách khỏi bus của MAX30001. Phải cắt jumper `I2C` và `ADR` để dùng SPI. Giá trị thanh ghi chốt 2026-10-25 (Packet Schema V0.2 mục 3): gia tốc và con quay ở chế độ hiệu năng, INT1 push-pull mức cao không chốt, microcode Bosch chép vào repo. Footprint M3 đã lật cho cách lắp mặt chip quay ra ngoài; lắp chip quay vào bo thì sơ đồ chân bị gương (chân 3V3 của module rơi vào pad OCS, GND vào OSDO). Silkscreen mặt dưới ghi `CHIP SIDE OUT` (V1-draft5, 2026-10-27). Trục: quy ước trục bo cổ tay X sang phải, Y về phía mép J1, Z hướng ra mặt trên (mặt áp da); khi đó trục bo = (−X, +Y, −Z) của BMI270 (suy từ hình trục trong file Eagle SparkFun ngày 2026-10-27; kiểm bằng trọng lực khi bring-up) |
| Áp lực | Không dùng FSR ở V1 (nhóm chốt 2026-10-23) | Dây cáp 15–16 chuyển thành GND ở V1-draft3; từ V1-draft4 hai chân này là `BMI_MOSI`/`BMI_MISO` (A.7) |
| Cơ khí | Hai khe 3 × 22 mm trên PCB cho dây velcro 20 mm; tấm kính hoặc acrylic che | Bo 40,4 × 31,5 mm theo Edge.Cuts (bản V1-draft3 bỏ tab giữ cáp). Thân nhựa của J1 (box header cong) nằm hoàn toàn ngoài mép trên: theo footprint KiCad, thân bắt đầu cách mép 0,42 mm và sâu khoảng 9,1 mm, chỉ được giữ bằng 16 chân hàn; nhóm chốt giữ nguyên, không nới PCB (2026-10-23): khi cắm/rút luôn giữ thân header và buộc cáp vào dây đeo để lực kéo không dồn vào mối hàn; nếu chân cong hoặc mối hàn nứt khi thử thì xét nới PCB dưới thân header (khoảng 28 × 9,5 mm). Ba lỗ 3,2 mm tại (30,36; 8,14), (10,04; 28,46), (30,36; 28,46) trùng lỗ standoff của M1 và M3, dùng vít, đai ốc và spacer nylon M2 (spacer tròn Ø ≤ 4,5 mm hoặc lục giác 4 mm giữa hai cạnh), mỗi lỗ hai spacer cao bằng thân nhựa header (chốt 2026-10-27: tâm lỗ chỉ cách góc thân nhựa header gần nhất 2,54 mm, nên spacer lục giác cỡ M3, 5,5 mm giữa hai cạnh, lấn vào thân nhựa ít nhất 0,2 mm; [danh sách mua](../../hardware/bom/purchase_list_v1_module.md) mục 2); góc thứ tư (10,04; 8,14) nằm trên đường đi dây chính nên dùng miếng đệm dán. Theo ảnh sản phẩm, hai đầu nối Qwiic cao hơn chip cảm biến nên da cổ tay chạm đầu nối trước: tháo đầu nối Qwiic hoặc làm giá đỡ |
| Lắp ráp | Hàn J1 và cả hai header module vào bo cổ tay trước, cắt sát đuôi chân, dán kapton, sau đó mới lắp M1 và M3 lên header. J1 đặt ở mặt dưới nên mối hàn nằm ở mặt trên, là mặt áp vào da | Chân M3 nằm dưới thân M1 và ngược lại, nên DRC báo 18 cảnh báo `pth_inside_courtyard` (pad 1–6 của M1 trong courtyard M3; pad 1–12 của M3 trong courtyard M1) và 3 `npth_inside_courtyard` (ba lỗ NPTH của M1 trong courtyard M3), tổng 21, đều là dự kiến (DRC chạy lại 2026-10-29 trên 9a10274, KiCad 10). Trên M1 cắt JP1 để tắt LED nguồn đỏ, vì LED này nằm cùng mặt với cảm biến |
| Phụ | C2 10 µF + C3 100 nF trên 3V3–GND ở mặt trên, sát chân cáp J1.1 (đầu vào nguồn; nhìn từ mặt trên là đầu phải hàng chân), dùng chung cho M1 (MAX30101) và M3 (BMI270); giữ nguyên (chốt 2026-10-24): bring-up mục 8 đo 3V3 tại M1 khi LED chạy xung, sụt thì hàn thêm tụ | Không có test point trên bo cổ tay. Bảng chân cáp chỉ in ở mặt dưới bo đế; bo cổ tay chỉ có số 1 cạnh J1.1 |

**Cáp nối hai bo (theo KiCad):**

- Đầu bo đế: J2, box header IDC 2×8 bước 2,54 mm
  (`Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical`, DIN 41651), cắm socket IDC
  bấm trên cáp dẹt 16 dây.
- Đầu bo cổ tay: J1, box header IDC 2×8 cong 90°, có khóa
  (`Connector_IDC:IDC-Header_2x08_P2.54mm_Horizontal`), đặt ở mặt dưới. Cửa cắm quay
  ra ngoài mép trên, cáp chạy song song mặt bo. Footprint chuẩn lật xuống mặt dưới
  nên chân 1 nằm ở hàng chân trong, đầu phải khi nhìn từ mặt trên (đầu trái khi nhìn
  từ mặt dưới, mặt lắp J1). Hàn J1 nhầm sang mặt trên làm đảo thứ tự cột: chân 1
  (3V3) của cáp rơi vào lỗ J1.15 (`BMI_MOSI`) (sửa 2026-10-27 theo thứ tự cáp
  V1-draft4). Footprint này giả định **khe khóa ở vách xa mặt PCB** (nét khe vẽ trên
  mặt thân nhìn từ phía lắp), tức hàng chân lẻ nằm ở hàng lỗ xa thân; chỉ mua loại đó.
  Loại có khe ở vách sát PCB buộc socket cắm xoay 180°, đảo cả cáp: chân n của cáp vào
  pad 17 − n, 3V3 rơi vào `BMI_MISO` (chốt 2026-10-27). Bản V1-draft2 dùng 16 lỗ hàn dây,
  đánh số theo chiều mặt trên; nếu cắm một đầu nối cứng vào đó thì chân 1 rơi vào lỗ
  GND.
- Cáp: IDC–IDC 16 dây, hai đầu cái có gờ khóa, sọc đỏ ở chân 1 cả hai đầu, nối
  thẳng (chân n ↔ chân n). Đo thông mạch từng chân trước lần cấp nguồn đầu tiên.
  Socket IDC chỉ giữ bằng ma sát: dán băng keo hoặc buộc cáp vào dây đeo khi đeo.
- Chiều dài dự kiến 20–30 cm (KiCad không thể hiện).
- GND ở chân 2, 4, 6, 8, 10, 12, 14 (V1-draft4). Mỗi tín hiệu có GND hai bên, trừ
  cặp `BMI_MOSI`–`BMI_MISO` ở chân 15–16. Chân 1–2 là 3V3 và GND đặt kề nhau.
- Tín hiệu: 3V3, GND, PPG SDA/SCL/INT, BMI270 SCK/MOSI/MISO/CS/INT. Không cần dây
  5 V vì bo MAX30101 tự tạo 5 V.

**Lý do thứ tự chân cáp (chốt 2026-10-24, vẽ ở V1-draft4).** Giữ 3V3–GND kề nhau ở
chân 1–2 để vòng dòng nguồn nhỏ; mỗi tín hiệu có GND hai bên, trừ cặp `BMI_MOSI`–
`BMI_MISO` ở chân 15–16 (cùng bus SPI, đổi trạng thái đồng bộ theo SCK). Hai đường INT
có GND hai bên vì dễ nhận xung giả nhất (`PPG_INT` open-drain, kéo lên 4,7 kΩ).

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
chưa tính điện cảm; V1-draft5 đã tách riêng nguồn ECG, xem dưới). Các phép đo kiểm trên bo thật nằm ở
[trình tự bring-up](../../hardware/test_reports/v1_bringup_procedure.md) mục 8.

V1-draft4 (2026-10-24, rà soát cùng Codex): đổi thứ tự chân cáp, đi lại sáu đường
tín hiệu cáp trên cả hai bo, gỡ các đoạn GND cũ cắm vào chân nay là tín hiệu (GND vẫn
nối qua vùng đổ hai mặt); `BMI_SCK` mặt dưới bo đế đi khe J2.8/J2.10, không chồng dưới
`BMI_INT`; `BMI_MOSI` mặt dưới bo cổ tay dời sang x = 12,6, không chồng dưới `BMI_SCK`;
thêm via GND (32,0; 20,0) ở bo đế và (9,3; 9,2) ở bo cổ tay để nối lại vùng đổ đối
diện đường tín hiệu; J2.10 nối đặc với vùng đổ như J2.2/4/14. ERC 0 lỗi, DRC (kèm so
khớp schematic) chỉ còn cảnh báo thư viện `ppg_v1` và chân nằm trong courtyard đã biết.

V1-draft5 (2026-10-27, sửa theo đợt rà soát footprint so với module thật cùng ngày, có
Codex; Codex rà lại bản sửa cùng ngày: không có lỗi Critical/Major, đã sửa UUID trùng
của ghi chú M3 và hai câu dưới; sau khi chuyển cụm tụ trái sang nhánh ECG, Codex rà lần
2: không có phát hiện mới):

- **Breakout MAX30001 (J1 bo đế) dời 0,5 mm sang trái.** Khe giữa mép breakout và mép
  bo Waveshare (hai bo cùng độ cao trên socket) tăng từ 0,53 lên 1,03 mm; pad 1 cách mép
  bo 0,59 mm. Dây vào J1 kéo dài theo đúng hướng 45° của nó nên khe hở giữa các dây hầu
  như không đổi; riêng cặp `ECG_MOSI`–`ECG_MISO` gần J1.9/J1.10 giảm từ 0,60 xuống
  0,39 mm (vẫn trên mức tối thiểu 0,2 mm). `T0_BTN` (giữa J1.3/J1.4) và `LED_STAT`
  (giữa J1.7/J1.8) dời theo; bỏ via GND (5,75; 29,15) vì quá sát J1.3 mới.
- **3V3 hình sao.** Dây 0,4 mm riêng từ U1.1 tới J1.2 (VCC breakout ECG, khoảng 39,7 mm)
  đi trong khe giữa dây chéo 3V3 cũ và hàng via GND (khe hở khoảng 0,31 mm mỗi bên).
  Từ J1.2 nối xuống cụm tụ bên trái, nên **nhánh ECG** gồm J1.2, C3, C7 (10 µF), C4, C6,
  C8 (100 nF), R2 và TP1 (J1.2 → C7 khoảng 6,2 mm). Dây chéo cũ từ U1.2 không đi qua J1.2
  nữa mà xuống giữa J1.2 và J1.3; **nhánh cáp** chỉ còn R8, C5 (10 µF), C9 (100 nF) và
  J2.1 (U1.2 → J2.1 khoảng 56,8 mm). Hai nhánh chỉ gặp nhau ở U1: bỏ được đoạn dây 3V3
  dùng chung dài 36 mm (khoảng 44 mΩ) trên bo đế; phần dùng chung còn lại trên bo đế chỉ
  là đoạn nối U1.1–U1.2 dài 2,54 mm (khoảng 3 mΩ). Hai nhánh vẫn chung mặt 3V3, LDO của
  bo Waveshare và đường GND. Không chọn dây riêng U1 → J2.1 vì phải cắt qua khoảng tám dây
  chéo hoặc xẻ mặt GND dưới các dây ECG. Cụm tụ trái được chuyển sang nhánh ECG theo gợi
  ý của Codex (bản đầu của V1-draft5 để J1.2 cách tụ lớn gần nhất 86 mm). TP1 nay đo 3V3
  của nhánh ECG. Bring-up: đo J1.2–J1.3 bằng oscilloscope khi LED PPG chạy xung.
- **U1 vẽ theo bo Waveshare:** viền Fab 63,30 × 25,40 mm (x 27,03–52,43, y −3,31…59,99),
  module WROOM-1, một USB-C, 4 lỗ Ø2 mm; vị trí USB-C, BOOT, RESET ước từ ảnh. Courtyard
  theo viền mới. Số pad, net và tên footprint giữ nguyên (value vẫn ghi DevKitC-1, chân
  trùng).
- **Silkscreen:** `USB END` thay `DevKitC-1  USB END`, viền module hở phía trên, viền
  breakout dời theo J1, `V1 BASE rev E`, `V1-draft5 2026-10-27`; bo cổ tay `rev E` và
  ghi chú M3 `CHIP SIDE OUT` / `cut I2C+ADR jumpers` ở mặt dưới. Title block schematic
  hai bo: `V1-draft5`, 2026-10-27.
- DRC (kèm so khớp schematic) và ERC không đổi so với V1-draft4: bo đế 0 lỗi (2 cảnh báo
  thư viện), bo cổ tay 0 lỗi (18 cảnh báo `pth_inside_courtyard`: pad 1–6 của M1 trong
  courtyard M3, pad 1–12 của M3 trong courtyard M1; 3 `npth_inside_courtyard`: ba lỗ NPTH
  của M1 trong courtyard M3; tổng 21, xem A.3 "Lắp ráp"; 2 cảnh báo thư viện). DRC chạy
  lại 2026-10-29 trên 9a10274, KiCad 10: 0 pad chưa nối, 0 lệch schematic. Gerber V1-draft5 đã xuất ngày 2026-10-27 (không lưu trong repo); bản xuất
  V1-draft4 ngày 2026-10-25 không dùng nữa.

### A.4. Bo SparkFun MAX30101: điều đã kiểm trong schematic

Nguồn: `Hardware/SparkFun_MAX30101_Qwiic.sch` (Eagle) trong repo
`sparkfun/SparkFun_Photodetector_Breakout_MAX30101_Qwiic`, nhánh `master`, đọc
ngày 2026-10-16.

| Chức năng | Trên bo | Hệ quả cho bo đế |
| --- | --- | --- |
| Nguồn vào | Chỉ 3,3 V (chân 3.3V và Qwiic) | Cấp 3V3 từ LDO của bo Waveshare (U1) qua cáp |
| VDD 1,8 V của MAX30101 | LDO SP6214 1,8 V/100 mA từ 3,3 V | **Chân header "1.8V" là đầu ra LDO**; không nối nguồn vào |
| VDD_LED (VLED+) | Boost PAM2401 từ 3,3 V lên net 5V | LED xanh có nguồn 5 V ngay trên bo |
| I²C | Chuyển mức bằng 2 MOSFET kênh N; kéo lên 2,2 kΩ ở cả phía 1,8 V và phía 3,3 V (phía 3,3 V qua jumper `I2C PU`) | Bus I²C PPG không cần thêm kéo lên. Không thêm footprint kéo lên I²C trên bo nào (chốt 2026-10-24): với 2,2 kΩ và tổng điện dung ước khoảng 50 pF (cáp 20–30 cm, chân, bộ chuyển mức), thời gian lên 30–70% ≈ 0,85 × 2,2 kΩ × 50 pF ≈ 0,1 µs, dưới 0,3 µs của chế độ 400 kHz. Chưa đo; nếu sườn lên chậm thì chạy 100 kHz (A.2) |
| INT | Kéo lên 4,7 kΩ lên 3,3 V (jumper `INT`) | Nối thẳng GPIO |

### A.5. Không dùng ở V1

LiPo, BQ25180, TPS62840, W25Q128, LDO 1,8 V và oscillator riêng: dữ liệu ghi trên
laptop; nguồn, clock và chuyển mức đã có trên module. Các linh kiện này thuộc
Phần B.

### A.6. Đối chiếu tài liệu và việc kiểm khi nhận hàng

Trạng thái ngày 2026-10-27. Mục còn lại chỉ làm được khi có hàng; bước kiểm khi
nhận hàng ở
[danh sách mua](../../hardware/bom/purchase_list_v1_module.md) mục 3.

1. **Đã xong trên thiết kế.** Header breakout MAX30001 đưa INT2B ra chân 4 của SV1
   (`pc_max30001_brk_v1.0.brd`); KiCad V1-module nối vào GPIO47 (net
   `/ECG_INT2B`, U1 pad 28). **Khi nhận hàng:** kiểm revision breakout thật.
2. **Đã đối chiếu trên tài liệu (2026-10-27):** bốn footprint khớp bước chân, khoảng
   cách hàng và thứ tự chân với bản vẽ kích thước Waveshare, file Eagle của SparkFun
   (MAX30101, BMI270 1×1), file `pc_max30001_brk_v1.0.brd` của ProtoCentral (silkscreen
   trong file là `pc_max30001/3/4_brk 03/22`, giống bo đã mua) và ảnh sản phẩm; chân 6
   in `FCLK` nhưng trong file nối net `PACE_OUT1`, FCLK của chip lấy từ dao động trên
   bo, thiết kế để hở chân này. **Khi nhận hàng:** vẫn đối chiếu module thật với
   footprint (khoảng cách hai hàng chân 22,86 mm, pinout, lỗ bắt vít). PCB được đặt gia
   công trước khi có module (chốt 2026-10-24), nên nếu lệch footprint thì phải làm lại
   PCB.
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
     chọn độ rộng xung 411 hay 215 µs theo luật viết trước ở
     `interface_power_sampling_v0.md` mục 6 (chốt 2026-10-29: giữ 411 µs khi
     `SPO2_SR` đúng, mỗi khe đủ 200 sps và nguồn LED, 3V3 không sụt ở mã LED cao
     nhất; sai một điều thì 215 µs).
   - VLED: bo SparkFun tạo VLED+ bằng boost PAM2401 (A.4) với chia áp phản hồi
     R1 750 kΩ / R4 100 kΩ, tức 0,6 × (1 + 7,5) = **5,1 V danh định** (công thức
     VOUT = 0,6 (1 + R1/R2), Diodes DS37285 Rev 1-2, tr. 5). Mức này nằm trong dải
     4,5–5,5 V của LED xanh nhưng vượt 0,1 V dải 3,1–5,0 V mà datasheet bảo đảm
     PSRR cho LED đỏ/IR; giới hạn tuyệt đối là 6,0 V (MAX30101 Rev 2, tr. 2).
     Datasheet PAM2401 ghi dòng ra tới 1 000 mA ở VIN 3 V, VOUT 5 V (tr. 1), sơ đồ
     ứng dụng MAX30101 ghi nguồn +5 V "200 mA MAX" (tr. 32); hai số này không
     chứng minh bo đủ dòng, vì còn phụ thuộc cuộn cảm, nguồn 3V3 vào (dòng vào
     ≈ 5,1 × I_out / (3,3 × hiệu suất), cộng tải của MCU, ECG và IMU) và LDO 3V3
     của bo Waveshare (mã chưa xác định). Chốt 2026-10-24: giữ nguyên 5,1 V, không sửa bo SparkFun.
     **Khi có bo:** đo VLED+ khi không tải, quá áp lúc khởi động
     và gợn khi LED xanh chạy xung dòng cao nhất đã chọn, so với dải chung
     4,5–5,0 V của cả ba LED; đo 3V3 tại bo cổ tay cùng lúc, vì 3V3 đi qua cáp
     20–30 cm từ bo đế.
4. **Đã đối chiếu tài liệu module.** Module ESP32-S3-WROOM-1-N16R8 có flash 16 MB
   Quad SPI và PSRAM 8 MB Octal SPI (datasheet WROOM-1/1U v1.8, Bảng 1-1, tr. 3);
   VDD_SPI 1,8 V chỉ có ở bản N16R16VA (chú thích 7, tr. 4), và GPIO47/48 chạy
   1,8 V chỉ ở module dùng chip ESP32-S3R16V (chú thích c, tr. 12). Với module có
   PSRAM, VDD_SPI được cố định bằng eFuse lúc xuất xưởng, không theo mức GPIO45
   (tr. 39). Vậy với WROOM-1-N16R8 và N8R8 chính hãng, GPIO47 (`ECG_INT2B`) chạy
   3,3 V như các GPIO khác; kết luận này chỉ áp dụng cho họ module WROOM-1.
   **Khi nhận hàng:** bo Waveshare ESP32-S3-DEV-KIT-N8R8-M (đặt 2026-10-27, module
   Espressif WROOM-1-N8R8), vẫn đọc ký hiệu trên vỏ module, đọc
   loại chip và cấu hình eFuse VDD_SPI bằng lệnh chỉ đọc của esptool, và đo
   INT2B ở phía MCU (sau TXB0108 của breakout) lên 3,3 V. Nếu GPIO47 chạy 1,8 V
   thì không dùng được với thiết kế này.

### A.7. Bảng chân của KiCad V1-module

Bảng dưới lấy từ `hardware/kicad/v1_module/base/v1_base.kicad_pcb` (pad → net
của U1) và tên chân trong symbol `ESP32-S3-DevKitC-1` của
`v1_base.kicad_sch`; cáp lấy từ J1 của `v1_wrist.kicad_pcb` và J2 của
`v1_base.kicad_pcb` (V1-draft4; không đổi ở V1-draft5). Đây là **pin map chuẩn của V1** (chốt 2026-10-23); firmware
dùng cùng bảng này trong `firmware/boards/board_v1_module.h`. Pin map V1 cũ
(`Pin_Map_V1.md`, `V1.SchDoc` trên nhánh `dev/ducanh`: MAX30001 và BMI270 chung SPI,
không nối INT2B) không dùng nữa.

**GPIO của U1 (bo Waveshare; symbol `ESP32-S3-DevKitC-1`):**

| Net | GPIO | U1 pad | Thiết bị | Ghi chú |
| --- | ---: | ---: | --- | --- |
| `/ECG_CS` | 7 | 7 | MAX30001 CSB (J1 bo đế = SV1 chân 7) | R8 100 kΩ kéo lên 3V3 |
| `/ECG_SCLK` | 15 | 8 | MAX30001 SCLK (J1 bo đế = SV1 chân 8) | Bus SPI ECG. GPIO15 cũng là XTAL_32K_P (mục 7 Việc còn mở) |
| `/ECG_MOSI` | 16 | 9 | MAX30001 MOSI (J1 bo đế = SV1 chân 9) | GPIO16 cũng là XTAL_32K_N (mục 7 Việc còn mở) |
| `/ECG_MISO` | 17 | 10 | MAX30001 MISO (J1 bo đế = SV1 chân 10) | |
| `/ECG_INTB` | 21 | 27 | MAX30001 INTB (J1 bo đế = SV1 chân 5) | |
| `/ECG_INT2B` | 47 | 28 | MAX30001 INT2B (J1 bo đế = SV1 chân 4) | Xung `SAMP`, bật luôn và làm mốc thời gian ECG (chốt 2026-10-24; Packet Schema V0.2 mục 7); bản hoàn chỉnh cũng phải nối INT2B. Chạy 3,3 V với module WROOM-1-N16R8/N8R8; 1,8 V chỉ ở chip ESP32-S3R16V (A.6 mục 4) |
| `/PPG_SDA` | 8 | 12 | MAX30101 SDA (cáp chân 3) | Bus I²C PPG |
| `/PPG_SCL` | 9 | 15 | MAX30101 SCL (cáp chân 5) | TP4 |
| `/PPG_INT` | 18 | 11 | MAX30101 INT (cáp chân 7) | |
| `/BMI_CS_MCU` | 10 | 16 | BMI270 CS qua R11 33 Ω (`/BMI_CS`, cáp chân 13) | Bus SPI IMU |
| `/BMI_MOSI_MCU` | 11 | 17 | BMI270 SDA (= SDI) qua R10 33 Ω (`/BMI_MOSI`, cáp chân 15) | |
| `/BMI_SCK_MCU` | 12 | 18 | BMI270 SCL (= SCK) qua R9 33 Ω (`/BMI_SCK`, cáp chân 11) | TP5 nằm trên `/BMI_SCK` (phía cáp) |
| `/BMI_MISO` | 13 | 19 | BMI270 ADR (= SDO) (cáp chân 16) | |
| `/BMI_INT` | 14 | 20 | BMI270 INT1 (cáp chân 9) | |
| `/T0_BTN` | 4 | 4 | SW1 | R2 10 kΩ kéo lên, C2 100 nF, TP6 |
| `/LED_STAT` | 5 | 5 | D1 qua R3 1 kΩ | |
| `/STIM` | 6 | 6 | J3 chân 1 | Xung kích thích cho phép đo đồng bộ 10 phút; J3 chân 2 là GND |
| `/+3V3` | — | 1, 2 | Nguồn 3V3 từ LDO của bo Waveshare | Chân 5V (pad 21) không nối |
| `/GND` | — | 22, 23, 24, 44 | | |

Không nối: EN và GPIO0, 1, 2, 3, 19, 20, 35–42, 43, 44, 45, 46, 48.

**Tên bus và host ESP-IDF:** tài liệu dùng tên logic. Bus SPI ECG = `SPI2_HOST`
(`firmware/drivers/max30001_esp.c`), bus SPI IMU = `SPI3_HOST` (`bmi270_esp.c`, có DMA),
bus I²C PPG = `I2C_NUM_0` (`max30101_esp.c`). Chân nối vào host qua GPIO matrix.

**Cáp 16 dây (J2 bo đế ↔ J1 bo cổ tay, cùng số chân, V1-draft4; không đổi ở V1-draft5):**

| Chân | Net | Chân | Net |
| ---: | --- | ---: | --- |
| 1 | `/+3V3` | 2 | `/GND` |
| 3 | `/PPG_SDA` | 4 | `/GND` |
| 5 | `/PPG_SCL` | 6 | `/GND` |
| 7 | `/PPG_INT` | 8 | `/GND` |
| 9 | `/BMI_INT` | 10 | `/GND` |
| 11 | `/BMI_SCK` | 12 | `/GND` |
| 13 | `/BMI_CS` | 14 | `/GND` |
| 15 | `/BMI_MOSI` | 16 | `/BMI_MISO` |

Bo cổ tay: M1 MAX30101 (mặt trên) dùng chân 1–5 (GND, 3.3V, SDA, SCL, INT);
chân 6 `1.8V` (đầu ra LDO) không nối. M3 BMI270 (mặt dưới) dùng GND, 3V3, SDA (= SDI),
SCL (= SCK), ADR (= SDO), CS, INT1 (ASDx, ASCx, INT2, OCS, OSDO không nối). Không còn J2
(FSR đã bỏ).

**Tên chân trong KiCad (đổi 2026-10-27):** tên chân của bốn module trong symbol và
`pinfunction` của pad lấy đúng nhãn in trên bo thật để dễ đối chiếu: DevKitC theo nhãn
bo Waveshare (`3V3`, `RST`, `4`…`48`, `TX`, `RX`, `5V`, `G`); breakout MAX30001 bản
03/22 `GND, VCC, GND, INT2, INT1, FCLK, CSB, SCK, MOSI, MISO` (chân 6 trước ghi `PACE`
theo bản v1.0); MAX30101 `GND, 3.3V, SDA, SCL, INT, 1.8V`; BMI270 `GND, 3V3, SDA, SCL,
ADR, CS` và `ASDx, ASCx, INT1, INT2, OCS, OSDO`. Số chân, net và vị trí pad không đổi.

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
| PPG | 200 sps, 3 khe (xanh + đỏ + IR), N = 8 (74 B/packet) | ≈ 5,6 kB/s |
| IMU | Packet schema V0.2: 6 trục 100 Hz, N = 10 (82 B/packet) | ≈ 4,9 kB/s |

ECG + PPG theo schema ≈ 9,0 kB/s, nên W25Q128 (16 MiB) chứa khoảng **31 phút**
ghi thô; thêm IMU (≈ 13,9 kB/s) thì khoảng **20 phút**. Nếu ghi theo định dạng nén
3 B mỗi mẫu, không có header từng packet, thì thời lượng khoảng gấp đôi. Với đo theo
cửa sổ vài chục giây, tổng thời gian ghi mỗi buổi thường dưới mức này. `N` là số
firmware V1 dùng (ECG 16, PPG 8, IMU 10; cập nhật 2026-10-25); tính lại nếu bản hoàn
chỉnh đổi `N` hay bỏ IMU.

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
5. Ngủ giữa các cửa sổ (thêm thạch anh 32 kHz) hay giữ MCU thức suốt phiên.
6. Xung đột chân: KiCad V1-module dùng GPIO15/16 cho `ECG_SCLK`/`ECG_MOSI`, trùng
   XTAL_32K_P/N của ESP32-S3 (mục 5). V1 không có thạch anh 32 kHz nên không bị
   ảnh hưởng. Nếu bản hoàn chỉnh giữ pin map này thì phải bỏ thạch anh 32 kHz hoặc
   đổi chân SPI ECG.
7. Độ rộng xung LED 411 hay 215 µs: chờ số đo bring-up, theo luật đã viết trước ở
   `interface_power_sampling_v0.md` mục 6 (2026-10-29).
