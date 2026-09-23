# Yêu cầu phần cứng
## 1. Mục đích
Mục tiêu của V0 là:

Kiểm chứng khả năng thu nhận tín hiệu ECG.
Kiểm chứng khả năng thu nhận tín hiệu PPG.
Kiểm tra chất lượng tín hiệu và mức độ nhiễu của ECG và PPG.
Kiểm tra khả năng lấy mẫu và truyền dữ liệu ổn định.
Kiểm chứng khả năng đồng bộ thời gian giữa ECG và PPG.
Thu thập dữ liệu ECG và PPG phục vụ các bước xử lý tín hiệu, trích xuất đặc trưng và phát triển mô hình AI dự đoán huyết áp.

V0 là prototype phục vụ kiểm chứng nguyên lý và chất lượng tín hiệu, chưa phải thiết bị wearable hoàn chỉnh và chưa phải thiết bị y tế.

## 2. Phạm vi phiên bản V0

V0 tập trung vào các chức năng chính:
Thu nhận tín hiệu ECG.
Thu nhận tín hiệu PPG.
Điều khiển và thu thập dữ liệu bằng ESP32-S3 DevKitC-1 N16R8.
Gắn timestamp cho dữ liệu ECG và PPG.
Truyền dữ liệu từ ESP32-S3 sang laptop để kiểm thử và lưu trữ.
Kiểm tra chất lượng tín hiệu và phổ nhiễu.
Kiểm tra tính ổn định của quá trình thu thập và truyền dữ liệu.
Đánh giá hai phương án điện cực ECG.

## 3. Yêu cầu phần cứng thu nhận tín hiệu
### 3.1 ECG
Hệ thống ECG của V0 sử dụng:
Điện cực ECG.
MAX30001 làm ECG AFE.
ESP32-S3 DevKitC-1 N16R8 làm MCU.
Luồng dữ liệu:
Điện cực ECG
      ↓
  MAX30001
      ↓ SPI
  ESP32-S3
      ↓ USB
    Laptop

Yêu cầu:
Thu được tín hiệu ECG một kênh.
Tín hiệu phải đủ chất lượng để quan sát dạng sóng ECG.
Có khả năng xác định R-peak trong dữ liệu đạt chất lượng.
Kiểm tra mức nhiễu và các thành phần nhiễu trong tín hiệu.
### 3.2 PPG
Hệ thống PPG của V0 sử dụng:
MAX30101 làm cảm biến PPG.
ESP32-S3 DevKitC-1 N16R8 làm MCU.

Luồng dữ liệu:
MAX30101
    ↓ I²C
ESP32-S3
    ↓ USB
  Laptop

Yêu cầu:
Thu được tín hiệu PPG ổn định.
Quan sát được dạng sóng PPG.
Kiểm tra mức nhiễu và chất lượng tín hiệu.
Dữ liệu PPG phải có thông tin thời gian tương ứng với dữ liệu ECG.
## 4. Yêu cầu lấy mẫu và đồng bộ
### 4.1 Tần số lấy mẫu
Mục tiêu của hệ thống V0 là 500 Hz cho ECG và PPG nhằm có độ phân giải thời gian đủ tốt khi phân tích quan hệ thời gian giữa ECG và PPG.
Tần số lấy mẫu thực tế phải được xác nhận theo khả năng và cấu hình của MAX30001, MAX30101 và firmware.
Dữ liệu có thể được downsample ở các bước xử lý sau nếu cần, ví dụ khi so sánh với các bộ dữ liệu có tần số lấy mẫu thấp hơn như PulseDB.
Không sử dụng trực tiếp mệnh đề “125 Hz → sai số 5–10 mmHg” như một quan hệ cố định, vì sai số huyết áp không chỉ phụ thuộc vào độ phân giải thời gian của tín hiệu.

### 4.2 Đồng bộ PPG và ECG
ECG và PPG phải được ghi nhận với mốc thời gian nhất quán.
Hệ thống phải duy trì thông tin thời gian của hai tín hiệu để phục vụ việc xác định:
R-peak của ECG.
Mốc đặc trưng của PPG.
Pulse Arrival Time (PAT).

Yêu cầu:
ECG và PPG phải được thu trong cùng phiên đo.
Dữ liệu phải có timestamp.
Phải kiểm tra độ lệch thời gian và jitter giữa hai luồng dữ liệu.
Không được làm mất thông tin về độ trễ sinh lý giữa ECG và PPG trong quá trình thu thập và truyền dữ liệu.
## 5. Yêu cầu MCU
ESP32-S3 DevKitC-1 N16R8 là MCU chính của prototype V0.
MCU có các nhiệm vụ:

Nhận dữ liệu ECG từ MAX30001 thông qua SPI.
Nhận dữ liệu PPG từ MAX30101 thông qua I²C.
Gắn thông tin timestamp cho dữ liệu.
Đảm bảo việc thu thập ECG và PPG được thực hiện ổn định.
Đóng gói và truyền dữ liệu sang laptop thông qua USB.
Hỗ trợ kiểm tra và đánh giá dữ liệu thu được.
## 6. Yêu cầu truyền và lưu dữ liệu
Trong V0, dữ liệu được truyền trực tiếp từ ESP32-S3 sang laptop:
ECG ─────────┐
             │
             ▼
          ESP32-S3
             │
PPG ─────────┘
             │
            USB
             ↓
          Laptop
             ↓
       Lưu dữ liệu thô

Yêu cầu:
Dữ liệu ECG và PPG phải được truyền ổn định.
Dữ liệu phải giữ được timestamp.
Dữ liệu phải có thể lưu thành file để phục vụ phân tích.
Dữ liệu thô phải được giữ lại để phục vụ các bước xử lý tín hiệu và huấn luyện AI sau này.
## 7. Yêu cầu về nguồn và an toàn thử nghiệm
Prototype V0 phải ưu tiên sử dụng nguồn pin khi thực hiện phép đo có tiếp xúc với cơ thể.
Yêu cầu:
Thiết bị prototype sử dụng nguồn pin phù hợp.
Khi thu ECG trên người, laptop nên hoạt động bằng pin.
Không sử dụng trực tiếp nguồn điện lưới cho hệ thống đang kết nối với điện cực trên cơ thể.
Kiểm tra hệ thống trước khi thử nghiệm trên người.
Ưu tiên kiểm tra bằng nguồn tín hiệu/ECG simulator trước khi kết nối điện cực với người.

V0 chỉ phục vụ nghiên cứu và kiểm chứng nguyên lý, không được xem là thiết bị đo huyết áp hoặc thiết bị y tế đã được chứng nhận.

## 8. Yêu cầu về điện cực ECG

V0 cần đánh giá hai phương án điện cực:

Phương án A — Điện cực Ag/AgCl dùng gel

Điện cực Ag/AgCl được sử dụng làm phương án tham chiếu trong kiểm thử prototype.

Mục đích:

Kiểm chứng khả năng thu ECG của MAX30001.
Có cơ sở tham chiếu khi đánh giá chất lượng tín hiệu.
So sánh với phương án điện cực khô.
Phương án B — Điện cực khô (Dry electrode)

Điện cực khô được nghiên cứu để đánh giá khả năng sử dụng cho thiết bị đeo trong các phiên bản sau.

Cần đánh giá:

Chất lượng tín hiệu ECG.
Mức nhiễu.
Ảnh hưởng của chuyển động.
Độ ổn định tiếp xúc với da.
Khả năng tích hợp cơ khí.

V0 không mặc định loại bỏ một trong hai phương án; cả hai được đưa vào quá trình kiểm thử và so sánh.

## 9. Tiêu chí kiểm chứng V0
Prototype V0 cần chứng minh được các khả năng sau:

MAX30001 thu được ECG.
MAX30101 thu được PPG.
ESP32-S3 nhận được dữ liệu từ cả hai cảm biến.
ECG và PPG được gắn timestamp.
Dữ liệu được truyền ổn định sang laptop.
Có thể lưu dữ liệu thô.
Có thể kiểm tra dạng sóng và phổ nhiễu.
Có thể xác định R-peak ECG trên dữ liệu đạt chất lượng.
Có thể xác định mốc đặc trưng của PPG.
Có thể sử dụng dữ liệu ECG–PPG để tính/đánh giá PAT.
Có thể thực hiện thử nghiệm so sánh giữa Ag/AgCl gel electrode và dry electrode.

