# Yêu cầu phần cứng
## 1.Mục đích
Xác định các yêu cầu phần cứng cho prototype V0
Mục tiêu của V0 là:

1. Kiểm chứng khả năng thu nhận tín hiệu ECG.
2. Kiểm chứng khả năng thu nhận tín hiệu PPG.
3. Kiểm tra chất lượng và mức nhiễu của tín hiệu.
4. Kiểm tra khả năng lấy mẫu và truyền dữ liệu ổn định.
5. Kiểm chứng khả năng đồng bộ thời gian giữa ECG và PPG.
## 2.Phạm vi phiên bản V0
V0 tập trung vào các chức năng chính:

1. Thu nhận ECG.
2. Thu nhận PPG.
3. Điều khiển và thu thập dữ liệu bằng MCU.
4. Kiểm tra chất lượng tín hiệu và phổ nhiễu.
## 3. Yêu cầu lấy mẫu và đồng bộ
### 3.1. Tần số lấy mẫu
	Tần số lấy mẫu 500 Hz cho PPG và ECG. Cao hơn mức 125 Hz thông dụng, vì độ phân giải thời gian của PTT quyết định độ chính xác: ở 125 Hz, một mẫu ≈ 8 ms ≈ sai số 5–10 mmHg. Sau đó hạ mẫu xuống khi cần so với PulseDB.
### 3.2. Đồng bộ ECG và PPG
ECG và PPG phải được ghi với mốc thời gian nhất quán.
Hệ thống phải duy trì thông tin thời gian của hai tín hiệu để phục vụ việc xác định các khoảng thời gian như:
- R-peak ECG.
- Mốc đặc trưng của PPG.
- Pulse Arrival Time (PAT).    
## 4. Yêu cầu MCU
ESP32-S3 là MCU chính của prototype 
MCU có các nhiệm vụ:
1. Nhận dữ liệu PPG,ECG 
2. Gắn thông tin thời gian cho dữ liệu.
3. Truyền dữ liệu phục vụ kiểm thử.
## 5. Yêu cầu về điện cực ECG
V0 cần đánh giá hai phương án điện cực:
- Điện cực Ag/AgCl dùng gel.
- Điện cực khô (dry electrode).

Điện cực Ag/AgCl được sử dụng làm phương án tham chiếu cho kiểm thử prototype.
Điện cực khô được nghiên cứu cho định hướng tích hợp vào thiết bị đeo.



