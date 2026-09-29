# Packet Schema V0.1 – ECG/PPG Data Acquisition

## 1. Mục đích
Quy định cấu trúc dữ liệu ESP32-S3 xuất ra khi thu ECG/PPG V0. Mục tiêu là truyền dữ liệu ổn định về PC, phát hiện mất gói/mất mẫu, giữ timestamp để kiểm tra sampling và đồng bộ, đồng thời giữ raw data cho preprocessing/dataset.

> Trạng thái: **DỰ KIẾN / V0.1**. PPG AFE và sampling PPG chưa được chốt.

## 2. Kiến trúc
Do ECG và PPG có thể có sampling rate khác nhau, V0.1 không giả định 1 ECG sample = 1 PPG sample.
ECG_PACKET = [HEADER][SEQ][TIMESTAMP][SAMPLE_COUNT][ECG_DATA[]][STATUS]
PPG_PACKET = [HEADER][SEQ][TIMESTAMP][SAMPLE_COUNT][PPG_DATA[]][STATUS]
## 3. ECG Packet

| Trường | Kiểu đề xuất | Ý nghĩa |
| HEADER | uint8 | `0xE1`, nhận diện ECG packet |
| SEQ | uint32 | Số thứ tự packet |
| TIMESTAMP | uint64 | Thời điểm sample đầu tiên, µs |
| SAMPLE_COUNT | uint16 | Số sample trong packet |
| ECG_DATA[] | int32[] | Raw ECG samples |
| STATUS | uint16 | Cờ trạng thái/lỗi |
ECG sampling dự kiến: **512 SPS**.
\[
T_s = 1/512 = 1.953125\ ms
\]
Timestamp của packet là timestamp của sample đầu tiên. Các sample tiếp theo có thể suy ra từ `Ts`.
## 4. PPG Packet
| Trường | Kiểu đề xuất | Ý nghĩa |
| HEADER | uint8 | `0xF1`, nhận diện PPG packet |
| SEQ | uint32 | Số thứ tự packet PPG |
| TIMESTAMP | uint64 | Thời điểm sample đầu tiên, µs |
| SAMPLE_COUNT | uint16 | Số sample trong packet |
| PPG_DATA[] | int32[] | Raw PPG samples |
| STATUS | uint16 | Cờ trạng thái/lỗi |
Sampling rate và định dạng raw PPG **chưa chốt** vì PPG AFE chưa được xác nhận.
## 5. Ý nghĩa các trường
### SEQ
Sequence number dùng để phát hiện mất packet.
Ví dụ: nhận `100, 101, 102, 104` → packet `103` bị mất.
ECG và PPG dùng sequence riêng.
### TIMESTAMP
Timestamp dùng đơn vị µs và đại diện cho sample đầu tiên trong packet. Dùng để kiểm tra sampling và đồng bộ ECG/PPG.
### SAMPLE_COUNT
Cho biết packet có bao nhiêu sample. Ví dụ `16` → `DATA[0] ... DATA[15]`.
### STATUS
V0.1 chỉ quy hoạch trường này. Có thể dành bit cho:
- bit 0: packet/data error
- bit 1: FIFO overflow
- bit 2: sensor/AFE warning
- các bit còn lại: reserved
Chi tiết bit chưa chốt.
## 6. Ví dụ ECG packet
HEADER       = 0xE1
SEQ          = 1024
TIMESTAMP    = 125000000 us
SAMPLE_COUNT = 4
ECG_DATA     = [12340, 12352, 12348, 12360]
STATUS       = 0
## 7. Truyền USB/Serial
V0 ưu tiên binary packet để thu raw data. Có thể có text/log riêng để debug, nhưng dataset chính nên dùng format có cấu trúc rõ ràng.
## 8. Kiểm tra dữ liệu
Receiver kiểm tra:
1. HEADER hợp lệ.
2. SEQ liên tục.
3. SAMPLE_COUNT hợp lệ.
4. STATUS không báo lỗi.
5. Timestamp tăng hợp lý.
6. Sampling interval gần giá trị dự kiến.
Với ECG 512 SPS:
\[
\Delta t \approx 1.953125\ ms
\]
## 9. Đồng bộ ECG và PPG
Không ghép theo chỉ số sample nếu hai sensor có sampling rate khác nhau. Dùng timestamp:
ECG: SEQ | TIMESTAMP | ECG
PPG: SEQ | TIMESTAMP | PPG
Sau khi thu, PC dùng timestamp để đồng bộ hai tín hiệu.
## 10. Phiên bản
Schema hiện tại: **V0.1**.
Nếu thay đổi cấu trúc packet, tăng version:
V0.1 → V0.2 → V1.0
## 11. Trạng thái
### Đã xác định
- MCU: ESP32-S3-DevKitC-1 N16R8.
- ECG AFE: ProtoCentral MAX30001 breakout.
- ECG interface: SPI.
- ECG sampling dự kiến: 512 SPS.
- ECG/PPG có thể có sampling rate khác nhau.
- Cần SEQ để phát hiện mất packet.
- Cần TIMESTAMP để kiểm tra sampling và đồng bộ.

### Chưa chốt
- PPG AFE.
- PPG sampling rate.
- Kích thước packet tối ưu.
- Binary byte-level layout cuối cùng.
- CRC/checksum.
- Chi tiết STATUS.
