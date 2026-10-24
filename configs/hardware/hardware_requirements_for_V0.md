# Yêu cầu phần cứng

> **Cập nhật 2026-10-24:** không làm bản V0 nối dây; dùng thẳng PCB V1-module
> ([custom_board_proposal.md](custom_board_proposal.md) Phần A). Các yêu cầu và
> tiêu chí dưới đây áp dụng cho V1-module. Tên file giữ `V0` để không đổi liên kết.
## 1. Mục đích
Mục tiêu của V1-module là:
Kiểm chứng khả năng thu nhận tín hiệu ECG.
Kiểm chứng khả năng thu nhận tín hiệu PPG.
Kiểm tra chất lượng tín hiệu và mức độ nhiễu của ECG và PPG.
Kiểm tra khả năng lấy mẫu và truyền dữ liệu ổn định.
Kiểm chứng khả năng đồng bộ thời gian giữa ECG và PPG.
Thu thập dữ liệu ECG và PPG phục vụ các bước xử lý tín hiệu, trích xuất đặc trưng và phát triển mô hình AI dự đoán huyết áp.

V1-module là prototype phục vụ kiểm chứng nguyên lý và chất lượng tín hiệu, chưa phải thiết bị wearable hoàn chỉnh và chưa phải thiết bị y tế.
## 2. Phạm vi phiên bản V1-module
V1-module tập trung vào các chức năng chính:
Thu nhận tín hiệu ECG.
Thu nhận tín hiệu PPG.
Điều khiển và thu thập dữ liệu bằng ESP32-S3-DevKitC-1-N8R8.
Gắn timestamp cho dữ liệu ECG và PPG.
Truyền dữ liệu từ ESP32-S3 sang laptop để kiểm thử và lưu trữ.
Kiểm tra chất lượng tín hiệu và phổ nhiễu.
Kiểm tra tính ổn định của quá trình thu thập và truyền dữ liệu.
Đánh giá hai phương án điện cực ECG.
## 3. Yêu cầu phần cứng thu nhận tín hiệu
### 3.1 ECG
Hệ thống ECG của V1-module sử dụng:
Điện cực ECG.
MAX30001 làm ECG AFE.
ESP32-S3-DevKitC-1-N8R8 làm MCU.
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
Hệ thống PPG của V1-module sử dụng:
MAX30101 làm cảm biến PPG.
> Ghi chú: linh kiện PPG đã chốt ngày 2026-10-22 là MAX30101 trên bo SparkFun SEN-16474 (`custom_board_proposal.md` A.3–A.4). BOM V1 và schematic V1 cũ trên nhánh `dev/ducanh` ghi MAX30102 và không dùng nữa. Chế độ LED và tốc độ PPG: mục 4.1; độ rộng xung còn mở: `interface_power_sampling_v0.md` mục 6.
ESP32-S3-DevKitC-1-N8R8 làm MCU.

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
Tần số lấy mẫu của V1-module:
ECG: 512 sps (MAX30001 FMSTR 00, chốt 2026-10-23; `custom_board_proposal.md` A.2). Khoảng thời gian giữa hai mẫu liên tiếp:

$$
T_s = \frac{1}{512}\,\text{s} \approx 1{,}953\,\text{ms}
$$

PPG: 200 sps mỗi khe, MAX30101 multi-LED ba khe (`SLOT1` xanh, `SLOT2` đỏ, `SLOT3` IR), `SMP_AVE = 1` (không lấy trung bình trên chip); chốt 2026-10-24 (`custom_board_proposal.md` A.6 mục 3). Khoảng thời gian giữa hai mẫu của một khe:

$$
T_s = \frac{1}{200}\,\text{s} = 5\,\text{ms}
$$

Độ rộng xung (411 hay 215 µs) còn mở, chọn bằng số đo bring-up ([interface_power_sampling_v0.md](interface_power_sampling_v0.md) mục 4 và 6). Các khe của một mẫu không phát LED cùng lúc: khe sau lệch khe trước 1 107 µs (411 µs) hoặc 720 µs (215 µs), receiver cộng độ lệch này khi dựng thời gian từng khe (`Packet_Schema_V0.1.md` mục 7).

Tần số ghi trong packet là giá trị danh định; tốc độ thực của từng kênh phải đo (mục 4.4). Phát hiện R-peak và chân sóng PPG trên mẫu gốc của từng kênh. Đổi tần số (ví dụ về 125 Hz để so với PulseDB) là một thí nghiệm riêng, ghi trong cấu hình phân tích, không thay dữ liệu gốc.
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
### 4.3 Cơ chế timestamp
ESP32-S3 là MCU trung tâm thu thập dữ liệu.
Mỗi mẫu hoặc mỗi gói dữ liệu phải chứa thông tin thời gian.
Dạng dữ liệu tối thiểu:
timestamp
ECG sample
PPG sample
sequence number
status/error flag
Nếu hai AFE không cung cấp dữ liệu đồng thời tuyệt đối, firmware phải lưu:
ECG timestamp
PPG timestamp
theo cùng một mốc thời gian của MCU hoặc theo một cơ chế đồng bộ đã được xác minh.
Không được đồng bộ bằng cách dịch tín hiệu PPG để R-peak ECG và PPG trùng nhau, vì thao tác đó sẽ làm mất độ trễ sinh lý cần dùng để tính PAT.
Cũng không dùng R-peak và chân sóng PPG để *kiểm tra* đồng bộ: khoảng giữa hai mốc này là PAT, không phải lệch clock. Kiểm tra đồng bộ bằng kích thích chung theo `hardware/test_reports/sync_10min_test_plan.md`; định dạng timestamp theo `Packet_Schema_V0.1.md`.
### 4.4 Jitter và drift

V1-module phải kiểm tra ba vấn đề:
#### 4.4.1 Sample interval
Kiểm tra khoảng thời gian giữa các mẫu:

$$
\Delta t_n = t_n - t_{n-1}
$$

và so sánh với chu kỳ danh định $T_s = 1/f_s$ của từng kênh (ECG: $1/512$ s ≈ 1,953 ms; PPG: $1/200$ s = 5 ms).

#### 4.4.2 Jitter
Jitter được hiểu là biến thiên ngắn hạn của thời điểm lấy mẫu so với thời điểm lý tưởng.
V1-module phải đo và ghi nhận jitter thực tế thay vì tự đặt một giới hạn chưa có cơ sở đo.
#### 4.4.3 Clock drift
Khi thời gian thu tăng lên, clock của các thiết bị có thể lệch nhau.
Do đó cần kiểm tra:

$$
\Delta t(t) = t_{\text{ECG}}(t) - t_{\text{PPG}}(t)
$$

theo thời gian.
Nếu độ lệch thay đổi theo thời gian, phải ghi nhận drift và xác định phương pháp hiệu chỉnh trước khi sử dụng dữ liệu để tính PAT.
Ở V1-module chưa chốt một con số jitter/drift cứng nếu chưa có phép đo và yêu cầu nghiên cứu cụ thể. Giá trị giới hạn sẽ được xác định sau khi thực hiện thử nghiệm đồng bộ.
## 5. Yêu cầu MCU
ESP32-S3-DevKitC-1-N8R8 chính hãng (chốt 2026-10-24) là MCU chính của prototype V1-module.
MCU có các nhiệm vụ:

Nhận dữ liệu ECG từ MAX30001 thông qua SPI.
Nhận dữ liệu PPG từ MAX30101 thông qua I²C.
Gắn thông tin timestamp cho dữ liệu.
Đảm bảo việc thu thập ECG và PPG được thực hiện ổn định.
Đóng gói và truyền dữ liệu sang laptop thông qua USB.
Hỗ trợ kiểm tra và đánh giá dữ liệu thu được.
## 6. Yêu cầu truyền và lưu dữ liệu
Trong V1-module, dữ liệu được truyền trực tiếp từ ESP32-S3 sang laptop:
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
Prototype V1-module phải ưu tiên sử dụng nguồn pin khi thực hiện phép đo có tiếp xúc với cơ thể.
Yêu cầu:
Thiết bị prototype sử dụng nguồn pin phù hợp.
Khi thu ECG trên người, laptop phải hoạt động bằng pin.
Không sử dụng trực tiếp nguồn điện lưới cho hệ thống đang kết nối với điện cực trên cơ thể.
Kiểm tra hệ thống trước khi thử nghiệm trên người.
Ưu tiên kiểm tra bằng nguồn tín hiệu/ECG simulator trước khi kết nối điện cực với người.

V1-module chỉ phục vụ nghiên cứu và kiểm chứng nguyên lý, không được xem là thiết bị đo huyết áp hoặc thiết bị y tế đã được chứng nhận.
## 8. Yêu cầu về điện cực ECG
V1-module cần đánh giá hai phương án điện cực:
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
V1-module không mặc định loại bỏ một trong hai phương án; cả hai được đưa vào quá trình kiểm thử và so sánh.
## 9. Tiêu chí kiểm chứng
Tiêu chí nghiệm thu V1-module
V1-module được coi là đạt khi:
ECG
Thu được waveform ECG ổn định.
Không bị saturation trong điều kiện thử nghiệm.
Có thể phát hiện R-peak trên dữ liệu đạt chất lượng.
Sampling rate thực tế được xác minh.
Không có mất mẫu ngoài giới hạn đã xác định.
PPG
Thu được waveform PPG.
Không bị saturation.
Có thể xác định mốc PPG.
Sampling rate thực tế được xác minh.
ECG–PPG
Hai kênh có timestamp nhất quán.
Có thể xác định quan hệ thời gian giữa hai kênh.
Đo được PAT trên dữ liệu thử nghiệm.
Jitter và drift được đo và ghi nhận.
Truyền dữ liệu
Dữ liệu truyền ổn định về laptop.
Có sequence number.
Có timestamp.
Có thể phát hiện mất mẫu/gói.
An toàn
Hoàn thành kiểm tra bằng ECG simulator trước khi xem xét thử trên người.
Có cấu hình nguồn phù hợp cho thử nghiệm trên người.
Không sạc khi đang đeo.
Laptop chạy pin khi thực hiện phép đo trên người.
Đường ECG có phương án bảo vệ đầu vào.
Hoàn thành protocol/ethics cần thiết trước khi thu dữ liệu người tham gia.
