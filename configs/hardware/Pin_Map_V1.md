# Pin Map — ESP32-S3-DevKitC-1 N16R8
- **Phiên bản tài liệu:** V1.0
- **Trạng thái:** Draft — cần kiểm tra lại với schematic, datasheet và module thực tế trước khi chế tạo
- **MCU:** ESP32-S3-DevKitC-1 N16R8
- **Các cảm biến trong schematic:** MAX30001 (ECG), MAX30102 (PPG), BMI270 (IMU)

## 1. Bảng Pin Map tổng thể

| Khối | Thiết bị | Chân/tín hiệu thiết bị | Net label | GPIO ESP32-S3 | Chức năng |
|---|---|---|---|---:|---|
| ECG | MAX30001 | SCK | `SPI_SCK` | GPIO11 | Clock SPI dùng chung |
| ECG | MAX30001 | MOSI | `SPI_MOSI` | GPIO10 | Dữ liệu từ MCU tới cảm biến |
| ECG | MAX30001 | MISO | `SPI_MISO` | GPIO13 | Dữ liệu từ cảm biến tới MCU |
| ECG | MAX30001 | CS0/CS | `ECG_CS` | GPIO14 | Chọn MAX30001 trên bus SPI |
| ECG | MAX30001 | INT1 | `ECG_INT` | GPIO5 | Báo ngắt/sự kiện ECG |
| PPG | MAX30102 module | SDA | `PPG_SDA` | GPIO8 | Dữ liệu I²C |
| PPG | MAX30102 module | SCL | `PPG_SCL` | GPIO9 | Clock I²C |
| PPG | MAX30102 module | INT | `PPG_INT` | **GPIO6** | Báo ngắt từ MAX30102 |
| IMU | BMI270 | SCX/SCK | `SPI_SCK` | GPIO11 | Clock SPI dùng chung |
| IMU | BMI270 | SDX/MOSI | `SPI_MOSI` | GPIO10 | Dữ liệu từ MCU tới IMU |
| IMU | BMI270 | SDO/MISO | `SPI_MISO` | GPIO13 | Dữ liệu từ IMU tới MCU |
| IMU | BMI270 | CSB/CS | `BMI_CS` | GPIO12 | Chọn BMI270 trên bus SPI |
| IMU | BMI270 | INT1 | `BMI_INT` | GPIO4 | Báo ngắt từ IMU |
## 2. Ánh xạ GPIO theo net label
| Net label | GPIO ESP32-S3 | Thiết bị sử dụng |
|---|---:|---|
| `BMI_INT` | GPIO4 | BMI270 INT1 |
| `ECG_INT` | GPIO5 | MAX30001 INT1 |
| `PPG_INT` | GPIO6 | MAX30102 INT |
| `PPG_SDA` | GPIO8 | MAX30102 SDA |
| `PPG_SCL` | GPIO9 | MAX30102 SCL |
| `SPI_MOSI` | GPIO10 | MAX30001 + BMI270 |
| `SPI_SCK` | GPIO11 | MAX30001 + BMI270 |
| `BMI_CS` | GPIO12 | BMI270 CS |
| `SPI_MISO` | GPIO13 | MAX30001 + BMI270 |
| `ECG_CS` | GPIO14 | MAX30001 CS |
## 3. Giao tiếp giữa MCU và cảm biến
### 3.1. Bus SPI dùng chung cho MAX30001 và BMI270
Ba đường dữ liệu/clock được dùng chung:
- `SPI_SCK` — GPIO11
- `SPI_MOSI` — GPIO10
- `SPI_MISO` — GPIO13
Mỗi thiết bị có chân chip-select riêng:
- `ECG_CS` — GPIO14 cho MAX30001
- `BMI_CS` — GPIO12 cho BMI270
Firmware phải chỉ kích hoạt CS của thiết bị đang được giao tiếp. Cần xác minh SPI mode, tần số clock và timing yêu cầu trong datasheet của từng IC/module.
### 3.2. Bus I²C cho MAX30102
- `PPG_SDA` — GPIO8
- `PPG_SCL` — GPIO9
- `PPG_INT` — GPIO6
Kiểm tra module MAX30102 thực tế có điện trở kéo lên I²C hay chưa và xác minh mức điện áp logic của chân `INT`. Không thêm điện trở kéo lên hoặc thay đổi cấu hình điện áp khi chưa kiểm tra mạch breakout.
## 4. Khai báo GPIO tham khảo trong firmware
```cpp
// ESP32-S3-DevKitC-1 N16R8
// ECG: MAX30001
// PPG: MAX30102
// IMU: BMI270
// Shared SPI bus: MAX30001 + BMI270
#define SPI_MOSI_PIN  10
#define SPI_MISO_PIN  13
#define SPI_SCK_PIN   11
// ECG - MAX30001
#define ECG_CS_PIN    14
#define ECG_INT_PIN    5
// PPG - MAX30102, I2C
#define PPG_SDA_PIN    8
#define PPG_SCL_PIN    9
#define PPG_INT_PIN    6
// IMU - BMI270, SPI
#define BMI_CS_PIN    12
#define BMI_INT_PIN    4
```
Đây là bảng khai báo chân tham khảo, chưa phải firmware hoàn chỉnh. Khi viết chương trình, cần khởi tạo SPI/I²C và driver đúng với cảm biến, đồng thời xác minh GPIO thực tế trên đúng phiên bản bo mạch.
## 5. Nguồn và mass
| Net | Ý nghĩa | Yêu cầu kiểm tra |
|---|---|---|
| `3V3` | Nguồn 3,3 V cho các khối theo schematic | Xác minh dải điện áp của từng IC/module và khả năng cấp dòng |
| `GND` | Mass chung | Đảm bảo MCU và các module có chung tham chiếu mass |
| `5V`/net nguồn tại chân 21 | Nguồn vào bo mạch nếu được sử dụng | **Xác minh tên net và ký hiệu nguồn trên schematic trước khi cấp điện** |
Không cấp nguồn cho mạch thật chỉ dựa vào bảng Pin Map; cần kiểm tra toàn bộ đường nguồn và sơ đồ breakout thực tế trước.
## 6. Các điểm cần xác minh trước khi chốt
- [ ] Kiểm tra tên net nguồn đang nối với chân 5V của symbol ESP32-S3; bảo đảm không có nhầm lẫn về cực tính/tên nguồn.
- [ ] Đối chiếu tên chân của symbol MAX30001 và BMI270 với datasheet hoặc module breakout thực tế.
- [ ] Kiểm tra điện áp logic, điện trở kéo lên I²C và cách cấu hình chân ngắt của MAX30102.
- [ ] Kiểm tra SPI mode, clock tối đa và timing CS của MAX30001 và BMI270.
- [ ] Chạy ERC/compile trong Altium, xử lý các lỗi kết nối và xác nhận lại netlist.
- [ ] Kiểm tra Pin Map với đúng bo mạch ESP32-S3-DevKitC-1 N16R8 trước khi nối dây hoặc chế tạo PCB.
## 7. Lịch sử phiên bản
| Phiên bản | Nội dung |
|---|---|
| v1.0 | Tổng hợp Pin Map từ schematic hiện tại; đề xuất GPIO6 cho `PPG_INT` của MAX30102. |
