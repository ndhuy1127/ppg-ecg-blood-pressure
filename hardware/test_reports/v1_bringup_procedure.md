# Trình tự bring-up V1-module

> **Chưa thực hiện**: chưa có module và PCB. Áp dụng cho KiCad V1-module (bo đế
> V1-draft3, bo cổ tay V1-draft3), pin map chuẩn ở
> [custom_board_proposal.md](../../configs/hardware/custom_board_proposal.md) mục
> A.7 và [firmware khung](../../firmware/README.md).
>
> **An toàn:** bring-up chỉ dùng tín hiệu nhân tạo. **Không gắn điện cực lên
> người** cho tới khi có phê duyệt đạo đức và biên bản đo dòng rò
> ([hồ sơ đạo đức](../../docs/ethics/README.md)). Laptop chạy pin, rút sạc. Đeo vòng
> chống tĩnh điện hoặc chạm đất trước khi cầm module.

Đi lần lượt từng bước. Bước nào không đạt thì dừng, ghi lại và xử lý trước khi
sang bước sau. Giá trị đo ghi vào báo cáo theo mục 10.

## 0. Dụng cụ

- Đồng hồ vạn năng, oscilloscope ít nhất 2 kênh, thước kẹp, kính lúp.
- USB tester cắm giữa laptop và DevKitC để đọc điện áp và dòng.
- Máy hàn, thiếc, flux, bấc hút thiếc, nhíp, dao rọc giấy (cắt jumper).
- Laptop chạy pin, cài PlatformIO theo [firmware/README.md](../../firmware/README.md).
- Bản in PCB tỉ lệ 1:1 của hai bo (KiCad: Plot hoặc Print, tỉ lệ 1:1).

## 1. Kiểm khi nhận hàng (chưa hàn, chưa cấp nguồn)

| Module | Kiểm | Đạt khi |
| --- | --- | --- |
| DevKitC | Đo khoảng cách tâm hai hàng chân bằng thước kẹp; đặt lên bản in 1:1 của bo đế | **22,86 mm**, khớp footprint U1 (bo chính hãng ESP32-S3-DevKitC-1-N8R8, danh sách mua dòng 6) |
| DevKitC | Đọc ký hiệu trên vỏ module | ESP32-S3-WROOM-1-N8R8 (A.6 mục 4). Bản N16R16VA hoặc chip R16V thì dừng: GPIO47 chạy 1,8 V |
| DevKitC | Đối chiếu nhãn từng chân với bảng A.7 (đủ kích thước chưa đủ: phải đúng vị trí) | Pad U1 1–2 là 3V3, 21 là 5V, 22–24 và 44 là GND; các GPIO ở đúng pad như A.7 |
| Breakout MAX30001 | So với `pc_max30001_brk_v1.0` | Có R3 (10 kΩ, cỡ 0805) nối sleeve của jack với VCM; R7, R8 (0 Ω, cỡ 0402); header SV1 10 chân (A.2) |
| Cáp ECG của kit | Đếm số dây; đo thông mạch từng đầu bấm với tip/ring/sleeve của giắc 3,5 mm | Ba dây: LA ↔ ring, RA ↔ tip, RL ↔ sleeve (protocol v0.2 mục 5.2). Khác thì dán nhãn lại theo kết quả đo, không theo màu nắp. Chỉ có hai dây hoặc không có dây nối sleeve: dừng cấu hình 3 điện cực cho tới khi có cáp 3 dây (danh sách mua mục 3) |
| SparkFun MAX30101 | Mã và vị trí jumper | SEN-16474; có JP1 (LED nguồn), hàng chân GND, 3.3V, SDA, SCL, INT, 1.8V |
| SparkFun BMI270 | Mã và kích thước | SEN-22397 (1" × 1"), không phải SEN-22398; có jumper `I2C` và `ADR` |
| Cả bốn module | Đặt lên bản in 1:1 của hai bo | Lỗ bắt vít, hàng chân và lỗ spacer trùng footprint (A.6 mục 2) |

## 2. DevKitC đứng riêng (chỉ cắm USB)

1. Cắm cổng UART (cổng qua chip cầu USB–UART) vào laptop. Trong Device Manager,
   ghi cổng COM của từng cổng USB. Cổng USB native của ESP32-S3 có VID:PID
   `303A:1001` (USB Serial/JTAG).
2. Đọc loại chip và eFuse, **chỉ đọc**. Không bao giờ chạy lệnh `burn_*` của
   espefuse: ghi eFuse không đảo ngược được.

   ```powershell
   $py = "$env:USERPROFILE\.platformio\penv\Scripts\python.exe"
   $tool = "$env:USERPROFILE\.platformio\packages\tool-esptoolpy"
   & $py "$tool\esptool.py" --chip esp32s3 --port COM5 chip_id
   & $py "$tool\espefuse.py" --chip esp32s3 --port COM5 summary
   ```

   Đạt khi chip là ESP32-S3, và `VDD_SPI_FORCE = 1`, `VDD_SPI_TIEH = 1` (VDD_SPI nối
   VDD3P3_RTC_IO, tức 3,3 V). Ghi nguyên văn kết quả vào báo cáo.
3. Nạp firmware khung (`pio run -d firmware -t upload --upload-port COMx`). Mở log
   UART0 (115 200 baud): thấy `packet self-test passed`, `SESSION_ID`, ELF SHA-256.
4. Đo chân 3V3–GND của DevKitC: khoảng 3,3 V. Ghi giá trị đo và dòng đọc trên USB
   tester khi firmware khung đang chạy (mốc so sánh cho mục 6–8).
5. Ghi luồng packet từ cổng USB native 10 phút không tải, chạy logger theo
   [packet_logger.md](../../docs/protocol/packet_logger.md): chỉ có `skipped_bytes`
   ở offset 0 (chữ ROM), `SEQ` và `T_ANCHOR_US` tăng đơn điệu, `DATA` khớp công
   thức trong firmware README. Bước này cần cách ghi cổng serial ra file, chưa chốt.

## 3. PCB trần (chưa hàn)

1. Soi bằng kính lúp: không có cầu nối đồng, khe phay 3 × 22 mm ở bo cổ tay đúng
   kích thước.
2. Đo điện trở 3V3–GND trên cả hai bo: không chập.
3. Đo thông mạch theo bảng A.7: mỗi chân của J2 (bo đế) tới pad U1 tương ứng, mỗi
   chân của J1 (bo cổ tay) tới pad M1/M3 tương ứng; GND ở chân 2, 4, 7, 9, 14, 15, 16.

## 4. Sửa module (trước khi lắp)

| Module | Việc | Đạt khi |
| --- | --- | --- |
| Breakout MAX30001 | Thay R3 bằng 220 kΩ ±1 %, cỡ 0805 (datasheet yêu cầu ≥ 200 kΩ, A.2) | Đo R3 trước khi hàn lên bo: 220 kΩ ±1 % |
| Breakout MAX30001 | Gỡ R7, R8 (0 Ω, cỡ 0402): ngắt jack khỏi BIP/BIN của BioZ; đường ECG đi qua R4, R5 51 kΩ vẫn giữ nguyên | Pad R7, R8 hở mạch |
| Breakout MAX30001 | Hàn header SV1 10 chân (có trong kit) | Chân thẳng, không cầu thiếc |
| SparkFun MAX30101 | Cắt JP1 để tắt LED nguồn đỏ (LED cùng mặt với cảm biến, A.3) | Khi cấp nguồn, LED nguồn không sáng |
| SparkFun BMI270 | Cắt jumper `I2C` và `ADR` để chạy SPI (A.3) | Hai jumper hở mạch |

## 5. Hàn và lắp

**Bo đế:**

1. Hàn linh kiện dán trước: R2 10 kΩ, R3 1 kΩ, R8 100 kΩ, R9–R11 33 Ω (mặt dưới);
   C2, C4, C6, C8 100 nF; C9 100 nF (mặt dưới, sát J2.1/J2.2); C3, C5, C7 10 µF.
2. Hàn linh kiện chân cắm: SW1, D1 (đúng cực), hai socket 1×22, socket 1×10, J2
   (khe khóa theo silkscreen).
3. Dán 4 chân cao su ở mặt dưới: R9–R11 và C9 nằm ở mặt dưới, không được tì lên
   mặt bàn (A.2).
4. Đo lại 3V3–GND: không chập.

**Bo cổ tay** (theo A.3):

1. Hàn J1 (box header cong) ở **mặt dưới**. Hàn nhầm sang mặt trên sẽ đưa chân 1
   vào lỗ GND.
2. Hàn header của M1 và M3, C2 10 µF, C3 100 nF. Cắt sát đuôi chân, dán kapton lên
   mối hàn ở mặt trên (mặt áp vào da).
3. Lắp M1 (MAX30101) ở mặt trên, M3 (BMI270) ở mặt dưới, spacer nylon M3 ở ba lỗ,
   miếng đệm dán ở góc thứ tư.
4. Đo lại 3V3–GND: không chập.

## 6. Bo đế với DevKitC (chưa có breakout và bo cổ tay)

1. Kiểm hướng DevKitC theo silkscreen (đầu USB, đầu anten) **trước khi cắm**: cắm
   ngược 180° làm chập 3V3–GND (A.2).
2. Cấp nguồn qua USB tester. Ghi dòng lúc cắm và dòng ổn định; so với dòng của
   DevKitC đứng riêng ở mục 2. Rút USB ngay nếu dòng cao bất thường, điện áp USB
   sụt, hoặc có linh kiện nóng. Đo TP1–TP2: khoảng 3,3 V.
3. LED D1 nháy theo nhịp 0,5 s của firmware khung.
4. TP6 ở mức cao khi nhả SW1, mức thấp khi nhấn. Mỗi lần nhấn SW1, log UART0 in
   `t0 event` và luồng packet có một packet `0xC1`.

## 7. MAX30001 trên bo đế

Bước 2–5 cần driver MAX30001, chưa có trong firmware khung.

1. Rút cả hai cáp USB, cắm breakout vào socket SV1, bắt vít vào lỗ NPTH 3,2 mm.
   Cấp nguồn lại qua USB tester, theo dõi dòng như mục 6: 3V3 vẫn khoảng 3,3 V;
   đầu ra LDO 1,8 V của breakout (AP2112K-1.8) khoảng 1,8 V.
2. Đọc thanh ghi `INFO` (0x0F): nửa byte cao bằng `0x5`, như thư viện ProtoCentral
   dùng để nhận chip (`protocentral_max30001_arduino_library`, `src/protocentral_max30001.cpp`).
3. Cấu hình theo A.2: 512 sps, gain và bộ lọc cố định, `EN_BIOZ = 0`, **tắt lead
   bias nội** (cấu hình 3 điện cực, VCM qua R3), `INTB_TYPE = 01` (CMOS) ở `EN_INT`
   và `EN_INT2`, `EFIT`, `SAMP_IT`. Đọc lại từng thanh ghi đã ghi.
4. Oscilloscope:
   - INTB (GPIO21): xung theo ngưỡng `EFIT`, ví dụ 32 Hz khi đọc 16 mẫu một lần;
   - INT2B (GPIO47): xung `SAMP` 512 Hz khi `SAMP_IT = 00`, biên độ khoảng 3,3 V
     phía MCU (A.6 mục 4). Cạnh xung ứng với lúc mẫu vào FIFO, không phải lúc lấy
     mẫu analog (schema mục 5.2).
5. Tín hiệu nhân tạo qua cáp ECG (mạch chia áp ở
   [sync_10min_test_plan.md](sync_10min_test_plan.md) mục 3), không gắn người. Trước
   khi nối: chốt nút tham chiếu của mạch chia áp (GND của bo hay VCM/sleeve, việc còn
   mở ở mục 8 của kế hoạch đó), vẽ sơ đồ đấu nối, đo mức vi sai và mức chung ở đầu
   vào bằng oscilloscope. Chưa chốt thì không nối.
   - xung dương đưa vào LA (ring) so với RA (tip) cho mẫu ECG dương;
   - ETAG của mẫu hợp lệ;
   - bật phát hiện lead-off DC rồi tháo một đầu bấm: có cờ `DCLOFFINT`, packet
     mang `STATUS` bit 2.

## 8. Bo cổ tay qua cáp

1. Rút cả hai cáp USB. Đo thông mạch cáp 16 dây: chân n ↔ chân n; GND ở chân 2,
   4, 7, 9, 14, 15, 16; chân 1 (3V3) không chập GND.
2. Cắm cáp vào J2 và J1 (đúng khe khóa), cấp nguồn lại qua USB tester, theo dõi
   dòng như mục 6. Đo 3V3 tại chân C2 của bo cổ tay (bo cổ tay không có test point).
3. Nguồn LED của MAX30101 (net 5V trên bo SparkFun), theo A.6 mục 3:
   - khi không tải: khoảng 5,1 V danh định;
   - lúc khởi động: quá áp, chụp bằng oscilloscope;
   - khi LED xanh chạy xung dòng cao nhất đã chọn: gợn, đo cùng lúc với 3V3 tại bo
     cổ tay;
   - so với dải 4,5–5,0 V dùng chung cho cả ba LED.
4. I²C bus 1 (GPIO8 SDA, GPIO9 SCL, 400 kHz):
   - quét bus chỉ thấy địa chỉ 7 bit `0x57`;
   - đọc `PART_ID` (0xFF) = `0x15` (MAX30101 Rev 2, tr. 12);
   - chụp sườn lên của SCL tại TP4 (bo đế); quá chậm qua cáp thì lùi 100 kHz (A.2).
5. SPI bus 2 (GPIO10 CS, GPIO11 MOSI, GPIO12 SCK, GPIO13 MISO, bắt đầu 1 MHz):
   - BMI270 khởi động ở I²C; một lần đọc giả chuyển sang SPI; mỗi lần đọc SPI có
     một byte giả trước dữ liệu (BST-BMI270-DS000-08, tr. 17, 123, 125);
   - đọc `CHIP_ID` (0x00) = `0x24` (tr. 75);
   - khởi tạo theo tr. 18: `PWR_CONF` (0x7C) = 0x00, chờ ≥ 450 µs, `INIT_CTRL`
     (0x59) = 0x00, ghi file cấu hình của Bosch vào `INIT_DATA` (0x5E), `INIT_CTRL`
     = 0x01, rồi kiểm trạng thái khởi tạo theo datasheet;
   - chụp SCK tại TP5 (phía cáp): dội nhiều thì chỉnh R9–R11; ổn mới lên 2 MHz (A.2).
6. Tốc độ PPG (A.6 mục 3): multi-LED ba khe (xanh, đỏ, IR) ở ≤ 200 sps,
   `SMP_AVE = 1`. Đọc lại `SPO2_SR` và đo tốc độ ra từng khe: phải bằng tốc độ cấu
   hình trong sai số dao động; còn một nửa hay bội số khác nghĩa là chip đã đổi tốc
   độ.
7. Dây cáp và dây điện cực không kéo hay đè bo PPG khi đặt cẳng tay lên bàn, đo
   trên bench (protocol v0.2 mục 5.4, K5).
8. Nguồn và tín hiệu khi cả hệ chạy (`custom_board_proposal.md` mục 7, ý 14), với
   cáp dài nhất:
   - 3V3 tại DevKitC, VDD/1,8 V của breakout và 3V3 tại M1 khi LED PPG chạy xung
     cao nhất (và radio nếu có bật);
   - nhiễu trên ECG khi bật/tắt LED PPG;
   - SCK, MOSI, CS tại BMI270 và MISO tại MCU ở 1 rồi 2 MHz;
   - sườn lên I²C ≤ 300 ns ở cả hai phía bộ chuyển mức trên bo SparkFun;
   - sườn giả trên `PPG_SCL`, `T0_BTN`, `ECG_CS` khi `BMI_SCK` và `LED_STAT` đảo
     liên tục.

## 9. Đo đồng bộ 10 phút

Theo [sync_10min_test_plan.md](sync_10min_test_plan.md), sau khi bước 7 và 8 đạt.

## 10. Ghi kết quả

Mỗi lần bring-up ghi một file `hardware/test_reports/<YYYY-MM-DD>_v1_bringup.md`:

- ngày, người làm, revision hai bo (theo title block KiCad, hiện cả hai là V1-draft3);
- ký hiệu module, kết quả `chip_id` và `espefuse summary` (các trường VDD_SPI),
  revision breakout MAX30001, kết quả đo thông mạch cáp ECG;
- commit firmware và ELF SHA-256, `SESSION_ID` của mỗi lần ghi;
- giá trị đo ở từng bước, ảnh oscilloscope; ghi riêng "giá trị thiết kế/datasheet"
  và "giá trị đo được";
- bước không đạt, cách xử lý.

Dữ liệu thô và ảnh dung lượng lớn lưu ngoài Git (`runs/`) theo chính sách dữ liệu;
báo cáo ghi đường dẫn và SHA-256.

## Ngoài phạm vi bring-up

Trước khi đo trên người: phê duyệt đạo đức, biên bản đo dòng rò trên bo V1 thật,
kiểm K3–K5 của protocol v0.2 mục 5.4.
