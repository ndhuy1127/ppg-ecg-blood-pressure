# BÁO CÁO TIẾN ĐỘ TUẦN 1

**Giai đoạn:** Tuần 1 / 28 tuần  
**Người báo cáo:** Trương Đức Anh  
**Vai trò:** Phần cứng, firmware, BOM, thiết kế prototype, data acquisition và định dạng dữ liệu truyền từ thiết bị  
**Ngày báo cáo:** 2026-09-22  
**Ngày rà soát tài liệu:** 2026-10-08  

> Báo cáo tập trung vào phạm vi công việc của Đức Anh trong Tuần 1. Các tài liệu có trạng thái Draft / v0.1 chỉ thể hiện mức độ hoàn thành tài liệu, chưa đồng nghĩa với việc đã được nhóm hoặc giảng viên nghiệm thu/phê duyệt.

---

# 1. Mục tiêu tuần 1

Theo kế hoạch Tuần 1, phần công việc phụ trách của Đức Anh tập trung vào việc xây dựng nền tảng phần cứng và định dạng dữ liệu cho prototype ECG + PPG.

Các mục tiêu chính gồm:

1. **Xác định yêu cầu phần cứng v0.1** cho hệ thống đo ECG + PPG phục vụ nghiên cứu ước lượng huyết áp.
2. **Xác định kiến trúc phần cứng prototype V0**, sử dụng board rời và các module/breakout để ưu tiên kiểm chứng chức năng trước khi thiết kế PCB tích hợp.
3. **Lập BOM V0.1**, xác định các linh kiện chính, số lượng, trạng thái Primary/Alternative và các phương án thay thế.
4. **Đề xuất các phương án điện cực ECG**, tập trung vào khả năng đo ECG ổn định trong prototype và khả năng phát triển lên thiết bị đeo.
5. **Xây dựng sơ đồ khối phần cứng**, làm rõ các khối ECG, PPG, MCU, IMU, nguồn và giao tiếp.
6. **Xác định nền tảng MCU cho prototype**, chốt ESP32-S3-DevKitC-1 N16R8 làm MCU chính trong phạm vi hiện tại.
7. **Xây dựng Packet Schema V0.1** cho dữ liệu ECG/PPG truyền từ thiết bị về máy tính, bao gồm version, session/channel, sequence, timestamp, sample count và Fs.
8. **Xây dựng khung Generator/Replay** có `config` và `seed` để phục vụ kiểm thử packet hợp lệ và các lỗi truyền dữ liệu như mất gói, trùng gói, đảo thứ tự, timestamp bất thường và lệch thời gian giữa ECG/PPG.

---

# 2. Thành viên phụ trách và phân công công việc

| Công việc | Người phụ trách chính | Reviewer dự kiến | Trạng thái ghi nhận |
|---|---|---|---|
| Xác định yêu cầu phần cứng | Đức Anh | Huy, Linh | Đã xây dựng bản v0.1 |
| Xây dựng sơ đồ khối phần cứng | Đức Anh | Huy, Linh | Đã có bản sơ đồ khối |
| Xây dựng BOM V0.1 | Đức Anh | Huy, Linh | Đã có bản BOM V0.1 |
| Đề xuất phương án điện cực ECG | Đức Anh | Huy, Linh | Đã nghiên cứu và đề xuất |
| Xác định MCU prototype | Đức Anh | Huy, Linh | Đã chốt ESP32-S3-DevKitC-1 N16R8 |
| Xây dựng Packet Schema V0.1 | Đức Anh | Huy, Linh | Đã hoàn thành bản thảo |
| Xây dựng Generator/Replay test specification | Đức Anh | Huy, Linh | Đã hoàn thành bản thảo |
| Kiểm tra và cập nhật tài liệu lên GitHub | Đức Anh | Huy, Linh | Đã commit trên nhánh `dev/ducanh` |

---

# 3. Công việc đã hoàn thành của Đức Anh

## 3.1. Xác định yêu cầu phần cứng

Đã xây dựng yêu cầu phần cứng ban đầu cho prototype ECG + PPG.

Phạm vi được xác định theo hướng:

```text
ECG
 ↓
ECG AFE
 ↓
ESP32-S3
 ↓
USB / Serial
 ↓
PC
```

và:

```text
PPG
 ↓
PPG AFE
 ↓
ESP32-S3
 ↓
USB / Serial
 ↓
PC
```

Các khối phụ trợ gồm IMU và các khối nguồn/nguồn cấp khi cần thiết.

Một nguyên tắc quan trọng được xác định là **V0 chưa phải thiết bị đeo hoàn chỉnh**. V0 ưu tiên sử dụng board rời, module/breakout và dây nối để kiểm chứng:

- khả năng giao tiếp với AFE;
- khả năng lấy mẫu;
- chất lượng tín hiệu;
- phổ nhiễu;
- độ ổn định truyền dữ liệu;
- khả năng phát hiện mất packet/mất mẫu.

Do đó, chưa chuyển ngay sang thiết kế PCB tích hợp.

---

## 3.2. Xác định MCU prototype

MCU được sử dụng cho prototype là:

**ESP32-S3-DevKitC-1 N16R8, pre-soldered headers.**

ESP32-S3 đảm nhiệm các chức năng chính:

- giao tiếp với ECG AFE;
- giao tiếp với PPG AFE;
- thu thập dữ liệu;
- quản lý timestamp;
- đóng gói dữ liệu thành packet;
- truyền dữ liệu về máy tính;
- hỗ trợ quá trình kiểm thử và debug.

Trong phạm vi hiện tại **không sử dụng nRF5340 trong kiến trúc prototype/BOM chính**.

---

## 3.3. Xác định ECG AFE

ECG AFE được lựa chọn cho prototype là:

**MAX30001**

Thông qua breakout board của ProtoCentral.

Giao tiếp giữa MAX30001 và ESP32-S3 sử dụng **SPI**.

ECG sampling rate được xác định trong phạm vi hiện tại là:

\[
F_{s,ECG}=512\;Hz
\]

Do đó chu kỳ lấy mẫu ECG:

\[
T_{s,ECG}
=
\frac{1}{512}
=
1.953125\;ms
\]

Timestamp của từng mẫu ECG có thể được tái dựng từ timestamp của mẫu đầu tiên trong packet:

\[
t_i=t_0+\frac{i}{F_{s,ECG}}
\]

---

## 3.4. Xây dựng BOM V0.1

Đã xây dựng BOM V0.1 cho hệ thống prototype.

BOM được tổ chức theo các khối chức năng như:

| Khối | Linh kiện/giải pháp |
|---|---|
| MCU | ESP32-S3-DevKitC-1 N16R8 |
| ECG AFE | MAX30001 |
| PPG | AFE/module PPG – tiếp tục chốt |
| IMU | Module IMU phục vụ đánh giá chuyển động |
| ECG electrode | Các phương án điện cực ECG |
| Prototype | Board rời + dây + breakout |
| Giao tiếp PC | USB/Serial |

BOM V0.1 được xác định là **tài liệu phục vụ review**, chưa phải BOM đặt hàng chính thức.

Nguyên tắc được giữ là:

> **Không tự ý mua linh kiện trước khi BOM được nhóm/giảng viên duyệt.**

---

## 3.5. Đề xuất phương án điện cực ECG

Đã nghiên cứu các phương án điện cực ECG phục vụ hai mục tiêu:

- kiểm chứng tín hiệu trong prototype V0;
- đánh giá khả năng phát triển lên thiết bị wearable.

Các phương án được xem xét gồm:

### Phương án A – điện cực Ag/AgCl có gel

Ưu điểm:

- tiếp xúc da tốt;
- trở kháng tiếp xúc tương đối thấp;
- phù hợp để kiểm chứng tín hiệu ECG ở giai đoạn đầu;
- dễ tìm và dễ sử dụng.

Nhược điểm:

- không phù hợp hoàn toàn với thiết bị đeo dài hạn;
- có thể gây khó khăn khi tích hợp cơ khí dạng watch.

### Phương án B – dry electrode

Ưu điểm:

- không cần gel;
- phù hợp hơn với định hướng wearable;
- có thể tái sử dụng;
- thuận lợi cho việc tích hợp cơ khí.

Nhược điểm:

- nhạy với chuyển động;
- chất lượng tiếp xúc phụ thuộc lực ép và vị trí tiếp xúc;
- yêu cầu thiết kế cơ khí và xử lý tín hiệu tốt hơn.

Việc lựa chọn cuối cùng cần được kiểm chứng thực tế trên prototype.

---

## 3.6. Xây dựng Packet Schema V0.1

Đã xây dựng tài liệu **Packet Schema V0.1 – ECG/PPG Data Acquisition**.

Mục tiêu là chuẩn hóa dữ liệu từ ESP32-S3 gửi về máy tính, đồng thời cho phép kiểm tra:

- mất packet;
- trùng packet;
- đảo thứ tự packet;
- mất mẫu;
- timestamp bất thường;
- sai lệch thời gian giữa ECG và PPG.

Cấu trúc packet dự kiến:

```text
ECG_PACKET =
[HEADER]
[SEQ]
[TIMESTAMP]
[SAMPLE_COUNT]
[ECG_DATA[]]
[STATUS]
```

và:

```text
PPG_PACKET =
[HEADER]
[SEQ]
[TIMESTAMP]
[SAMPLE_COUNT]
[PPG_DATA[]]
[STATUS]
```

Các trường quan trọng được xác định:

| Trường | Ý nghĩa |
|---|---|
| Version | Phiên bản của packet schema |
| Session ID | Xác định một phiên đo |
| Channel | ECG hoặc PPG |
| SEQ | Số thứ tự packet |
| TIMESTAMP | Thời điểm lấy mẫu của sample đầu tiên |
| SAMPLE_COUNT | Số sample thực tế trong packet |
| Fs | Tần số lấy mẫu của từng kênh |
| DATA | Dữ liệu tín hiệu thô |
| STATUS | Trạng thái/lỗi của packet |

Đối với ECG:

\[
F_{s,ECG}=512\;Hz
\]

Trong khi `Fs` của PPG chưa được khóa do PPG AFE và cấu hình lấy mẫu vẫn đang được hoàn thiện.

Một điểm quan trọng được xác định là:

> **Timestamp phải đại diện cho thời điểm lấy mẫu, không phải thời điểm đọc FIFO hoặc thời điểm truyền packet.**

Điều này cần thiết để có thể sử dụng timestamp khi đồng bộ ECG và PPG và tính các đại lượng thời gian như PAT.

---

## 3.7. Xây dựng Generator / Replay Test

Đã xây dựng tài liệu kiểm thử cho **Packet Generator/Replay**.

Công cụ dự kiến có cấu hình và `seed` để bảo đảm test có thể tái lập.

Các trường cấu hình chính gồm:

- `session_id`;
- `channel`;
- `Fs`;
- `sequence`;
- `timestamp`;
- `sample_count`;
- sample data;
- loại lỗi;
- vị trí chèn lỗi;
- `seed`.

Các kịch bản kiểm thử:

| STT | Test case | Nội dung |
|---|---|---|
| 1 | Packet hợp lệ | Packet đúng schema và timeline |
| 2 | Mất packet | Chủ động bỏ packet |
| 3 | Packet trùng | Phát lại cùng packet |
| 4 | Đảo thứ tự | Hoán đổi thứ tự packet |
| 5 | Timestamp bất thường | Timestamp sai hoặc nhảy bất thường |
| 6 | Lệch ECG–PPG | Chủ động tạo offset giữa hai kênh |

Ví dụ tạo lệch thời gian:

\[
t_{PPG}=t_{ECG}+\Delta t
\]

với:

\[
\Delta t=20\;ms
\]

Receiver phải phát hiện và định lượng được độ lệch này thay vì giả định hai kênh luôn có timestamp giống nhau.

---

# 4. Danh mục sản phẩm đầu ra và đường dẫn

| STT | Tên sản phẩm | Đường dẫn tương đối | Trạng thái |
|---|---|---|---|
| 1 | Hardware Requirements | `configs/hardware/` | Có bản v0.1 |
| 2 | BOM V0.1 | `hardware/bom/` | Có bản v0.1 |
| 3 | Sơ đồ khối phần cứng | `hardware/schematics/` | Có bản sơ bộ |
| 4 | Phương án điện cực ECG | `hardware/` | Có bản đề xuất |
| 5 | Packet Schema V0.1 | `configs/hardware/Packet_Schema_V0.1_Metadata_Table.docx` | Đã hoàn thành |
| 6 | Packet Generator/Replay | `configs/hardware/packet_generator_replay.md` | Đã hoàn thành |
| 7 | Git commit phần Packet Schema | Commit `4d4380f` | Đã commit |
| 8 | Git commit Generator/Replay | Commit `bbd2d3c` | Đã commit |

Các tài liệu phần cứng V0.1 được xây dựng theo định hướng ban đầu là **Draft / FOR REVIEW**, chưa xem là cấu hình phần cứng cuối cùng.

---

# 5. Tóm tắt các nội dung chuyên môn chính

## 5.1. Kiến trúc phần cứng V0

Kiến trúc V0 được định hướng:

```text
        ECG ELECTRODE
              │
              ▼
        ┌────────────┐
        │ MAX30001   │
        │  ECG AFE   │
        └─────┬──────┘
              │ SPI
              ▼
        ┌────────────┐
        │ ESP32-S3   │
        │  N16R8     │
        └─────┬──────┘
              │ USB / Serial
              ▼
             PC
```

PPG được thiết kế theo nguyên tắc tương tự:

```text
        PPG SENSOR / AFE
              │
              ▼
        ┌────────────┐
        │ ESP32-S3   │
        └─────┬──────┘
              │
              ▼
             PC
```

ECG và PPG có thể có **Fs khác nhau**, do đó không được giả định rằng mỗi sample ECG tương ứng trực tiếp với một sample PPG.

---

## 5.2. Timestamp và đồng bộ ECG–PPG

Để tính các đại lượng thời gian giữa ECG và PPG, timestamp phải gắn với **thời điểm lấy mẫu**.

Với ECG:

\[
t_{ECG,i}
=
t_{ECG,0}
+
\frac{i}{F_{s,ECG}}
\]

Tương tự đối với PPG:

\[
t_{PPG,j}
=
t_{PPG,0}
+
\frac{j}{F_{s,PPG}}
\]

Việc đồng bộ hai tín hiệu được thực hiện dựa trên timeline/timestamp thay vì dựa đơn thuần vào chỉ số sample.

Điều này đặc biệt quan trọng khi:

- ECG và PPG có Fs khác nhau;
- packet có số sample khác nhau;
- có packet bị mất;
- dữ liệu được truyền theo batch.

---

## 5.3. Sequence và phát hiện mất packet

`SEQ` được sử dụng để xác định thứ tự packet.

Ví dụ:

```text
100 → 101 → 102 → 103
```

là chuỗi bình thường.

Nếu nhận:

```text
100 → 101 → 103
```

có khả năng packet `102` đã bị mất.

Nếu nhận:

```text
100 → 101 → 101 → 102
```

có packet `101` bị trùng.

Nếu nhận:

```text
100 → 101 → 103 → 102
```

có packet bị đảo thứ tự.

Tuy nhiên `SEQ` chỉ kiểm tra được vấn đề ở **mức packet**. Việc kiểm tra mất sample còn phải kết hợp:

- `SAMPLE_COUNT`;
- `TIMESTAMP`;
- `Fs`;
- dữ liệu thực tế.

---

# 6. Kết quả kiểm tra kỹ thuật (Verification Results)

Trong phạm vi công việc Tuần 1, việc kiểm tra tập trung vào tính nhất quán của tài liệu, cấu trúc dữ liệu và trạng thái Git.

| Hạng mục kiểm tra | Kết quả | Chi tiết |
|---|---|---|
| Hardware requirements | PASS – bản v0.1 | Đã xác định các khối phần cứng chính |
| BOM V0.1 | PASS – bản draft | Có danh sách linh kiện và trạng thái |
| Packet Schema | PASS – bản v0.1 | Đã xác định các trường metadata chính |
| ECG Fs | PASS | 512 SPS |
| PPG Fs | TBD | Chưa khóa |
| Timestamp | PASS – định nghĩa | Timestamp đại diện thời điểm sample đầu tiên |
| Sequence | PASS – định nghĩa | Sequence riêng theo channel |
| Generator/Replay specification | PASS – bản v0.1 | Có config, seed và 6 nhóm test |
| Git commit Packet Schema | PASS | Commit `4d4380f` |
| Git commit Generator/Replay | PASS | Commit `bbd2d3c` |

Các kiểm tra trên chủ yếu xác nhận **tài liệu và cấu trúc thiết kế**, chưa phải kiểm chứng cuối cùng trên phần cứng thực tế.

---

# 7. Khó khăn, rủi ro và vướng mắc kỹ thuật

## 7.1. Chất lượng tín hiệu ECG tại cổ tay

Đo ECG trên cổ tay có thể gặp:

- biên độ tín hiệu nhỏ;
- nhiễu chuyển động;
- thay đổi trở kháng tiếp xúc;
- ảnh hưởng của vị trí và lực ép điện cực.

Do đó cần kiểm tra thực tế nhiều loại điện cực trước khi chốt thiết kế wearable.

---

## 7.2. Chưa khóa PPG AFE và Fs PPG

ECG đã xác định:

\[
F_{s,ECG}=512\;Hz
\]

nhưng PPG AFE và Fs PPG chưa được khóa.

Điều này ảnh hưởng trực tiếp đến:

- packet size;
- buffer;
- timestamp;
- đồng bộ ECG–PPG;
- thiết kế firmware;
- xử lý dữ liệu trên PC.

Do đó các thông số liên quan đến PPG trong Packet Schema hiện được đánh dấu **TBD** thay vì cố định sớm.

---

## 7.3. Đồng bộ hai kênh

ECG và PPG không nhất thiết có cùng Fs và không nhất thiết được đọc FIFO cùng thời điểm.

Nếu sử dụng thời điểm đọc FIFO làm timestamp thì có thể tạo ra sai lệch thời gian giả.

Do đó cần bảo đảm timestamp phản ánh thời điểm acquisition và cần có cơ chế kiểm tra timeline ở phía receiver.

---

## 7.4. Chưa có kiểm thử packet trên firmware thực tế

Packet Schema và Generator/Replay hiện mới tạo nền tảng cho kiểm thử.

Bước tiếp theo cần kết nối:

```text
ESP32-S3 firmware
       ↓
Real packet
       ↓
Receiver
       ↓
Validator
       ↓
Generator/Replay test
```

để kiểm tra schema trên dữ liệu thực tế thay vì chỉ trên dữ liệu mô phỏng.

---

# 8. Các vấn đề cần nhóm và giảng viên xác nhận

1. Chốt chính thức kiến trúc phần cứng V0.
2. Chốt ESP32-S3-DevKitC-1 N16R8 là MCU prototype.
3. Chốt cấu hình PPG AFE và Fs PPG.
4. Xác nhận yêu cầu timestamp phần cứng và độ chính xác cần thiết cho việc tính PAT.
5. Xác nhận Packet Schema V0.1 trước khi triển khai firmware chính thức.
6. Xác nhận có cần bổ sung:
   - CRC;
   - schema version field;
   - session ID;
   - channel ID;
   - các bit STATUS;
   - checksum/error detection khác.
7. Xác nhận phương án điện cực ECG dùng cho thử nghiệm V0.
8. Xác nhận BOM V0.1 trước khi mua linh kiện.
9. Xác nhận tiêu chí kiểm thử packet và tiêu chí PASS/FAIL.

---

# 9. Kế hoạch chuyển giao sang Tuần 2

## 9.1. Phần cứng

- Hoàn thiện và review BOM V0.1.
- Chốt các linh kiện được sử dụng trong prototype V0.
- Chốt phương án điện cực ECG thử nghiệm.
- Kiểm tra khả năng kết nối MAX30001 với ESP32-S3.
- Chuẩn bị wiring cho prototype V0.

## 9.2. Firmware

- Xây dựng firmware giao tiếp MAX30001 qua SPI.
- Thiết lập ECG sampling ở 512 SPS.
- Thu dữ liệu và kiểm tra FIFO.
- Xây dựng timestamp cho dữ liệu ECG.
- Đóng gói ECG theo Packet Schema V0.1.

## 9.3. Data acquisition

- Xây dựng receiver trên PC.
- Kiểm tra:
  - packet hợp lệ;
  - mất packet;
  - packet trùng;
  - packet đảo thứ tự;
  - timestamp bất thường.
- Đưa Generator/Replay vào regression test.

## 9.4. ECG–PPG synchronization

Sau khi Fs PPG được chốt:

- xác định timeline ECG;
- xác định timeline PPG;
- kiểm tra lệch timestamp;
- xây dựng phép kiểm tra đồng bộ hai kênh;
- chuẩn bị dữ liệu cho bước tính PAT.

## 9.5. Chuyển tiếp sang thiết kế PCB

Chưa chuyển ngay sang PCB cuối cùng.

Trình tự dự kiến:

```text
Yêu cầu
   ↓
BOM V0.1
   ↓
Prototype V0
   ↓
Kiểm chứng AFE
   ↓
Kiểm chứng tín hiệu
   ↓
Kiểm chứng sampling
   ↓
Kiểm chứng data packet
   ↓
Chốt thiết kế
   ↓
Schematic
   ↓
PCB
```

Mục tiêu của Tuần 2 là chuyển từ **tài liệu thiết kế** sang **prototype V0 có khả năng thu dữ liệu ECG thực tế và truyền dữ liệu về PC theo schema đã thống nhất**.

---

# Kết luận

Trong Tuần 1, phần việc của Đức Anh đã hình thành được nền tảng ban đầu cho hệ thống acquisition:

**Hardware Requirements → BOM V0.1 → Block Diagram → ECG Electrode Options → ESP32-S3 + MAX30001 → Packet Schema → Generator/Replay Test.**

Các tài liệu hiện tại chủ yếu ở mức **v0.1 / Draft**, do đó bước tiếp theo cần tập trung vào **review, chốt thông số còn TBD và kiểm chứng trên phần cứng thực tế**, thay vì tiếp tục mở rộng thiết kế khi các yêu cầu nền tảng chưa được khóa.
