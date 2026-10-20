# Khung Protocol Nghiên cứu Thực nghiệm (Protocol Outline) - Phiên bản v0.1

> **Phiên bản:** v0.1
> **Người biên soạn:** Nguyễn Đức Huy
> **Vai trò:** Xử lý tín hiệu, PAT, thống kê, xây dựng protocol nghiên cứu
> **Ngày lập:** 2026-09-22; **cập nhật:** 2026-10-14 (đồng bộ với RQ v0.2, yêu cầu phần cứng V0 và nguồn bổ sung).
> **Lưu ý:** TUYỆT ĐỐI CHƯA THU THẬP DỮ LIỆU THẬT TRONG TUẦN 1.

---

## 1. Tuyên bố phạm vi và tính chất nghiên cứu

> [!IMPORTANT]
> **Tuyên bố pháp lý và y đức:**
> 1. Thiết bị đang phát triển trong dự án này là **nguyên mẫu nghiên cứu học thuật (exploratory research prototype)**, hoàn toàn **không phải thiết bị y tế** và không được sử dụng cho bất kỳ mục đích chẩn đoán lâm sàng, sàng lọc hay can thiệp điều trị y tế nào.
> 2. Tài liệu này là **khung phác thảo phương pháp luận (protocol outline)** phục vụ thiết kế kỹ thuật. **Tuyệt đối không tiến hành tuyển tình nguyện viên hoặc thu thập dữ liệu trên người trong Tuần 1.** Hoạt động thu thập dữ liệu chỉ được phép triển khai sau khi đề cương đạo đức hoàn chỉnh được phê duyệt chính thức.

---

## 2. Mục tiêu nghiên cứu (Research Objectives)

1. **Mục tiêu kỹ thuật:** Thiết lập quy trình chuẩn hóa nhằm thu nhận đồng thời tín hiệu ECG và PPG tại cổ tay có đồng bộ thời gian chính xác, kết hợp đo huyết áp đối chứng bằng máy đo bắp tay đạt chuẩn lâm sàng.
2. **Mục tiêu khoa học:**
   - Đánh giá khả năng ước lượng biến thiên huyết áp ($\Delta\text{SBP}$, $\Delta\text{DBP}$) qua các phiên đo độc lập (cross-session) sau khi đã hiệu chuẩn cá nhân ban đầu.
   - So sánh định lượng giá trị đóng góp của việc bổ sung ECG/PAT so với việc chỉ sử dụng đặc trưng hình thái PPG.
   - Kiểm chứng thực nghiệm tính bền vững của mô hình dưới các phương pháp phân chia dữ liệu nghiêm ngặt (chống rò rỉ dữ liệu).

---

## 3. Thiết kế nghiên cứu (Study Design)

- **Hình thức:** Nghiên cứu thực nghiệm quan sát (observational prospective study), đo lặp lại theo chuỗi thời gian (repeated-measures longitudinal design).
- **Cấu trúc phiên đo:** Mỗi người tham gia sẽ thực hiện ít nhất 3 phiên đo độc lập (`session_id`), phân bố qua tối thiểu 2–3 ngày khác nhau:
  - **Phiên 1 (Calibration Session):** Thu nhận mốc huyết áp chuẩn ban đầu ($\text{BP}_0$) và tín hiệu nền để thiết lập tham số hiệu chuẩn cá nhân.
  - **Phiên 2 & Phiên 3 (Evaluation Sessions):** Thu nhận tín hiệu và huyết áp ở các thời điểm khác nhau (ví dụ: sáng/chiều, khác ngày) theo cùng quy trình nghỉ ổn định ở mục 6.1 để đánh giá khả năng theo dõi $\Delta\text{BP}$ ở phiên sau. Các can thiệp làm thay đổi huyết áp (ví dụ vận động nhẹ) chưa thuộc protocol v0.1; chỉ thêm khi đã được duyệt đạo đức (xem mục 11).
- **Hệ quả cần lưu ý:** Ở người trẻ khỏe mạnh đo lúc nghỉ, $\Delta\text{BP}$ giữa các phiên có thể nhỏ. Khi đó baseline zero-change (dự đoán $\Delta\text{BP} = 0$) đã có sai số thấp, và mô hình khó thể hiện khác biệt. Mukkamala et al. (2021, [10.1161/HYPERTENSIONAHA.121.17747](https://doi.org/10.1161/HYPERTENSIONAHA.121.17747)) chỉ ra rằng thiết bị có hiệu chuẩn có thể trông chính xác chỉ vì BP ít thay đổi, nên phải báo cáo sai số của baseline chỉ dùng BP hiệu chuẩn và độ lệch chuẩn của $\Delta\text{BP}$ tham chiếu cùng với sai số mô hình.

---

## 4. Đối tượng tham gia dự kiến và Tiêu chí lựa chọn

### 4.1. Cỡ mẫu dự kiến
- Dự kiến $N = 15 - 20$ tình nguyện viên khỏe mạnh (sinh viên/cán bộ tại trường, độ tuổi 18–35).
- Đây là cỡ mẫu khả thi cho giai đoạn thử nghiệm nguyên mẫu (feasibility), chưa dựa trên phân tích power. Với 3 phiên mỗi người và ít nhất 2 lần cuff hợp lệ mỗi phiên ([RQ v0.2](../research_questions_v0.1.md), mục 4.G), dự kiến có tối thiểu $15 \times 3 \times 2 = 90$ đến $20 \times 3 \times 2 = 120$ lần đo cuff hợp lệ, với giả định mọi người hoàn thành đủ 3 phiên; các lần đo này lặp trong cùng người nên **không phải 90–120 quan sát độc lập**. Đơn vị cho kiểm định cặp là người ($n = 15 - 20$). Cỡ mẫu chính thức cần được tính lại từ dữ liệu pilot.

### 4.2. Tiêu chí lựa chọn (Inclusion Criteria)
- Độ tuổi từ 18 đến 35 tuổi, có đầy đủ năng lực hành vi dân sự.
- Tự nguyện ký vào phiếu đồng thuận tham gia nghiên cứu (Informed Consent).
- Nhịp tim xoang bình thường, không có tiền sử bệnh lý tim mạch đã được chẩn đoán.

### 4.3. Tiêu chí loại trừ (Exclusion Criteria)
- Người có tiền sử tăng huyết áp bệnh lý, hạ huyết áp tư thế, loạn nhịp tim (rung nhĩ, ngoại tâm thu dày) hoặc đang sử dụng thuốc tác động đến hệ tim mạch/hệ thần kinh giao cảm (thuốc chẹn beta, giãn mạch, an thần).
- Người có vết thương hở, viêm da, dị ứng hoặc kích ứng tiếp xúc tại vùng cổ tay đeo thiết bị; người có tiền sử dị ứng kim loại (niken) nếu điện cực được chọn có chứa niken.
- Người mang máy tạo nhịp tim hoặc thiết bị cấy ghép điện tử trong cơ thể.
- Phụ nữ đang mang thai hoặc nghi ngờ có thai.

---

## 5. Bố trí thiết bị, điện cực và tư thế đo

### 5.1. Vị trí đeo thiết bị và bố trí điện cực ECG
- **Vòng đeo nguyên mẫu:** Đeo ở mặt lưng cổ tay của **tay không thuận** (thường là tay trái), vị trí cách mỏm trâm trụ khoảng $1.5 - 2.0\text{ cm}$, dây đeo được siết với lực vừa phải (đủ chặt để cảm biến quang học áp sát da, không làm gián đoạn tuần hoàn mao mạch, tránh xê dịch).
- **Cảm biến PPG:** Cụm phát LED quang học và photodiode hướng về mặt lưng cổ tay để bắt tín hiệu thể tích mạch vi tuần hoàn.
- **Bố trí điện cực ECG (Cấu hình Lead I sửa đổi):**
  - *Điện cực 1 & 2 (Mặt đáy thiết bị):* Tiếp xúc trực tiếp với da mặt lưng cổ tay tay đeo (tay trái).
  - *Điện cực 3 (Mặt trên thiết bị):* Khi đo, người tham gia dùng ngón trỏ hoặc ngón cái của **tay đối diện (tay phải)** chạm nhẹ lên điện cực kim loại mặt trên của vỏ thiết bị để tạo thành vòng dẫn truyền qua tim (Lead I khép kín).

### 5.2. Vị trí vòng bít đo đối chứng (Reference Cuff)
- Sử dụng máy đo huyết áp bắp tay tự động có kết quả validation lâm sàng đã công bố theo protocol AAMI/ESH/ISO cho đúng model sử dụng. Model cụ thể chưa chốt (xem checklist mục 12); không coi "cùng hãng" là đã được validate.
- Sai số của máy cuff truyền thẳng vào nhãn và vào mốc hiệu chuẩn $\text{BP}_0$; AHA scientific statement về thiết bị cuffless (Cohen et al., 2025, [10.1161/HYP.0000000000000254](https://doi.org/10.1161/HYP.0000000000000254)) nhấn mạnh độ chính xác của thiết bị cuffless phụ thuộc mạnh vào cuff dùng để hiệu chuẩn.
- **Bố trí chính:** prototype đeo ở cổ tay trái; cuff đối chứng đặt ở bắp tay phải. Sau khi khóa protocol, không đổi bên tùy từng lượt đo. Quy trình đo hai tay và tiêu chí chọn bên/loại trừ phải chốt trước khi thu dữ liệu chính.
- Kích thước vòng bít phải phù hợp với chu vi bắp tay của người tham gia.

### 5.3. Tư thế người tham gia
- Ngồi tựa lưng thoải mái trên ghế có tựa, hai bàn chân đặt phẳng trên sàn, hai chân không bắt chéo.
- Cả hai cẳng tay đặt thả lỏng trên mặt bàn có đệm êm, giữ cho cổ tay đeo thiết bị và vùng đo bắp tay nằm **ngang mức tim**.
- Không nói chuyện, không cử động ngón tay hay thay đổi tư thế trong suốt quá trình ghi tín hiệu và bơm xả cuff.

```
                  [ Vị trí tim ]
                        |
     [Cánh tay phải]          [Cánh tay trái]
            |                        |
   (Bắp tay: Cuff chuẩn)     (Cổ tay: Thiết bị đeo ECG+PPG)
            |                        |
     [Bàn tay phải]           [Bàn tay trái]
            \                        /
             --> Chạm nhẹ ngón tay --
                 lên điện cực ECG
                 mặt trên thiết bị
```

---

## 6. Quy trình thu thập dữ liệu và Đồng bộ tín hiệu

### 6.1. Quy trình nghỉ ổn định trước khi đo
1. Người tham gia đến phòng đo, ngồi nghỉ ngơi yên tĩnh trong môi trường nhiệt độ phòng ổn định ($24 - 26^\circ\text{C}$) trong tối thiểu **10 phút**.
2. Giải thích lại quy trình thao tác và kiểm tra độ vừa vặn của thiết bị.
3. Không uống cà phê, trà, hút thuốc hoặc vận động mạnh trong vòng 2 giờ trước phiên đo.

### 6.2. Trình tự một lượt đo (Measurement Event)
Mỗi sự kiện đo (`event_id`) kéo dài khoảng $2.5 - 3\text{ phút}$, gồm 3 giai đoạn:
1. **Giai đoạn 1 - Ghi tín hiệu trước đo cuff (Baseline Signal Window - $60\text{s}$):**
   - Thiết bị thu nhận tín hiệu PPG và ECG đồng bộ liên tục trong 60 giây trước khi bắt đầu bơm cuff. Toàn bộ 60 giây được lưu để kiểm soát chất lượng và phân tích độ nhạy.
   - Đây là **cửa sổ tín hiệu ứng viên trước cuff**, không phải phép đo huyết áp đồng thời. Cửa sổ phân tích chính dự kiến là 20–30 giây ngay trước thời điểm bơm cuff và chỉ được chấp nhận khi SQI đạt yêu cầu, nhịp tim/xung tương đối ổn định và không có chuyển động. Phải lưu độ lệch thời gian giữa cuối cửa sổ tín hiệu và thời điểm máy cuff trả kết quả.
2. **Giai đoạn 2 - Bơm đo huyết áp đối chứng bằng Cuff ($45 - 60\text{s}$):**
   - Kích hoạt máy đo bắp tay. Ghi nhận thời điểm bắt đầu bơm và kết thúc xả.
   - Tín hiệu thu được trong giai đoạn này được gắn cờ cuff_inflating = True; không dùng làm đầu vào chính cho mô hình. Dữ liệu chỉ được giữ cho kiểm soát chất lượng và phân tích độ nhạy vì cuff, thao tác chạm điện cực và độ trễ nhãn có thể làm thay đổi trạng thái đo.
3. **Giai đoạn 3 - Ghi nhãn và nghỉ hồi phục ($30\text{s}$):**
   - Ghi nhận kết quả SBP, DBP và Pulse Rate từ màn hình máy đo đối chứng vào biểu mẫu nghiên cứu.
   - Nghỉ tối thiểu 2 phút trước khi lặp lại lượt đo tiếp theo.

- **Phân tích độ nhạy ghép nhãn:** So sánh kết quả khi dùng cửa sổ 10, 20, 30 và 60 giây trước cuff, đồng thời loại riêng các lượt không đạt tiêu chí plateau. Nếu kết quả thay đổi đáng kể theo cửa sổ, phải báo cáo đây là bất định do nhãn không đồng thời, không được chọn hậu nghiệm cửa sổ cho kết quả đẹp nhất.

### 6.3. Đồng bộ thời gian phần cứng giữa ECG và PPG
- ECG và PPG cần cùng quy chiếu thời gian hoặc ánh xạ clock được kiểm chứng; không mặc định hai AFE lấy mẫu đồng thời chỉ vì dùng cùng MCU.
- Tần số lấy mẫu chưa chốt. Protocol v0.1 ban đầu đề xuất PPG 100–250 Hz, ECG 250–500 Hz; [yêu cầu phần cứng V0](../../configs/hardware/hardware_requirements_for_V0.md) dùng MAX30001 cho ECG, đặt mục tiêu 500 Hz cho cả hai kênh, còn linh kiện PPG (MAX30101 hay MAX30102) chưa chốt. Bảng tốc độ mà từng AFE cấu hình được và phương án dự kiến (ECG 512 sps; PPG 100 hoặc 200 sps) nằm ở [interface_power_sampling_v0.md, mục 4](../../configs/hardware/interface_power_sampling_v0.md); [packet schema V0.1](../../configs/hardware/Packet_Schema_V0.1.md) vẫn để mở ECG 500 hay 512 sps (mục 15). Tần số cuối cùng phải là giá trị mà từng AFE hỗ trợ theo datasheet và phải được đo lại trên thiết bị. Đây là điểm chưa chốt, không phải cấu hình đã khóa.
- Với độ phân giải thời gian, mỗi mẫu ở 500 Hz là 2 ms; sai số định vị R peak và PPG foot cộng với sai số đồng bộ hai kênh đi thẳng vào PAT, nên cần đo jitter/offset thực tế trước khi diễn giải các thay đổi PAT cỡ vài ms.
- Phải phân biệt timestamp **lấy mẫu**, timestamp **đọc FIFO** và thời điểm **nhận gói tại PC**. Counter MCU không tự loại bỏ độ trễ sensor/FIFO, sai lệch clock hoặc jitter. Cần ghi clock, đơn vị, tần số theo kênh, mất mẫu và cách suy ra thời điểm từng mẫu từ timestamp mẫu đầu gói.
- Marker bắt đầu bơm cuff (`t0`) phải cùng clock hoặc có ánh xạ có thể kiểm tra. Không dịch PPG để trùng đỉnh R vì sẽ mất độ trễ cần tính PAT.

---

## 7. Quy tắc phân đoạn, Gán nhãn và Kiểm soát chất lượng (SQI)

### 7.1. Định nghĩa mẫu độc lập (Independent Sample)
> [!CAUTION]
> **Nguyên tắc cốt lõi chống thổi phồng dữ liệu:**
> - **Mỗi lần đo bằng cuff đối chứng chỉ tạo ra DUY NHẤT 1 nhãn huyết áp độc lập ($\text{SBP}_i, \text{DBP}_i$).**
> - Tuyệt đối **KHÔNG** được cắt đoạn tín hiệu 60 giây trước đó thành 12 cửa sổ nhỏ (mỗi cửa sổ 5 giây) rồi gán cùng giá trị $(\text{SBP}_i, \text{DBP}_i)$ cho cả 12 cửa sổ và coi đó là 12 mẫu độc lập. Cách làm sai lầm này sẽ gây rò rỉ dữ liệu nghiêm trọng và thổi phồng sai lệch kích thước mẫu.
> - Đề xuất tổng hợp đặc trưng bằng trung vị trong cửa sổ chính dự kiến 20–30 giây trước cuff; chưa khóa độ dài hoặc quy tắc tổng hợp. Các ứng viên độ nhạy 10/20/30/60 giây lấy `[t0 - L, t0)`, phải chọn/khóa trên pilot/validation trước khi xem test. Mỗi `event_id` vẫn chỉ đóng góp tối đa một cặp nhãn cuff độc lập.

### 7.2. Định danh cấu trúc dữ liệu phân cấp
Mỗi bản ghi phải chứa khóa định danh duy nhất theo cấu trúc (định dạng ID theo [quy ước dữ liệu](../quy_uoc_du_lieu.md)):
- `subject_id`: Mã người tham gia (ví dụ: `SUB001`, `SUB002`), không chứa thông tin định danh cá nhân.
- `session_id`: Mã phiên đo theo ngày/thời điểm (ví dụ: `S001`, `S002`).
- `event_id`: Mã lượt đo trong phiên (ví dụ: `E01`, `E02`).
- `window_id`: Mã cửa sổ tín hiệu thành phần bên trong một event.

### 7.3. Tiêu chí kiểm tra chất lượng tín hiệu (SQI) và Loại bỏ cửa sổ
Các tiêu chí và con số dưới đây là **đề xuất chưa khóa**, không phải ngưỡng đã kiểm chứng hay quy tắc đang triển khai. Phải kiểm tra căn cứ, cực tính/lọc tín hiệu và kiểm tra trên pilot/validation trước khi áp dụng; không tuning theo test. Dự kiến gắn `flag_reject = True` khi vi phạm tiêu chí đã khóa:
1. **Nhiễu bão hòa quang học (Clipping/Saturation):** Tín hiệu PPG chạm ngưỡng kịch trần ADC ($V_{\text{max}}$ hoặc $V_{\text{min}}$) quá 5% thời gian cửa sổ.
2. **Chỉ số Skewness SQI ($s\text{SQI}$):** Ứng viên $s\text{SQI} < 0$; dấu phụ thuộc cực tính và xử lý tín hiệu, không mặc định mọi PPG hợp lệ đều có độ lệch dương.
3. **Mất tín hiệu ECG:** Không phát hiện được phức bộ QRS rõ ràng hoặc biên độ đỉnh R nhỏ hơn $3\times$ độ lệch chuẩn đường nền.
4. **Biến thiên nhịp tim bất thường:** Khoảng cách giữa các đỉnh R liên tiếp biến động $> 30\%$ trong cửa sổ tĩnh (ngoại trừ hiện tượng loạn nhịp sinh lý khi hô hấp đã kiểm soát).
5. **Cử động mạnh:** Cảm biến gia tốc IMU (nếu tích hợp) phát hiện gia tốc biến thiên $> 0.15\text{g}$ trong thời gian ghi tín hiệu nền.

---

## 8. Phương pháp tính toán đại lượng PAT và Cảnh báo vật lý

### 8.1. Công thức xác định PAT
$$\mathrm{PAT} = t_{\mathrm{PPG,foot}} - t_{\mathrm{ECG,Rpeak}}$$
- $t_{\mathrm{ECG,Rpeak}}$: Thời điểm đỉnh sóng R của phức bộ QRS. Pan–Tompkins hiệu chỉnh là một thuật toán ứng viên; phương pháp phát hiện R peak, cấu hình lọc và quy tắc xử lý đỉnh giả/bỏ sót phải được kiểm tra trên pilot/validation trước khi khóa.
- $t_{\mathrm{PPG,foot}}$: Thời điểm chân sóng (foot) của nhịp PPG tương ứng. Tiếp tuyến giao cắt (intersecting tangent method) và đạo hàm bậc hai cực đại ($d^2\text{PPG}/dt^2$) là các phương pháp ứng viên; phương pháp foot và quy tắc ghép nhịp vẫn chưa khóa, phải khóa trên pilot/validation, không điều chỉnh theo test.

### 8.2. Cảnh báo phương pháp luận: $\text{PAT} \neq \text{PTT}$
- Nhóm nghiên cứu ghi nhận rõ ràng:
  $$\text{PAT} = \text{PEP} + \text{PTT}$$
  Đây là cách viết gọn. PEP thường bắt đầu ở Q/QRS, không phải R peak; khoảng R đến lúc tống máu có thể khác PEP. Cần khai báo các mốc; ECG + PPG dự kiến chỉ đo PAT, không đo riêng PEP/PTT. Xem [glossary Tuần 2](week_02_sample_label_glossary.md).
- **Quy tắc bắt buộc:**
  - Không được áp dụng trực tiếp các phương trình vật lý sóng mạch thuần túy của PTT (như Bramwell-Hill hay Hughes) cho PAT mà bỏ qua PEP.
  - Đề xuất kiểm tra HR và hình thái PPG trong ablation; chưa có bằng chứng các đặc trưng đó bù trừ được biến thiên PEP trong dự án.

---

## 9. Kế hoạch phân chia dữ liệu và Đánh giá thống kê

### 9.1. Chiến lược phân chia (Data Splitting)
1. **Subject-independent Split (Leave-One-Subject-Out Cross-Validation - LOSO):**
   - Toàn bộ dữ liệu của đối tượng $k$ được dành riêng cho tập Test.
   - Mô hình được huấn luyện trên $N-1$ đối tượng còn lại.
   - Lặp lại cho tất cả $N$ đối tượng để thu được phân phối sai số khách quan trên người chưa từng gặp.
2. **Temporal Cross-Session Split (Đánh giá hiệu chuẩn cá nhân):**
   - Với mỗi người trong tập Test:
     - `Session 1`: Dùng làm mốc hiệu chuẩn cá nhân ($\text{BP}_0, \text{PAT}_0, \text{Features}_0$).
     - `Session 2 & Session 3`: Dùng để kiểm tra dự đoán $\Delta\text{SBP}$ và $\Delta\text{DBP}$.
   - Tuyệt đối không xáo trộn ngẫu nhiên dữ liệu giữa các phiên đo.

### 9.2. Kế hoạch thống kê và Kiểm định giả thuyết
- **Chỉ số sai số:** $\text{MAE}$, $\text{RMSE}$, $\text{ME} \pm \text{STD}$ (tính riêng biệt cho SBP và DBP).
- **Bootstrap theo đối tượng (Subject-level Bootstrapping):**
  - Khi ước lượng khoảng tin cậy 95% (95% CI) cho MAE, phải tiến hành lấy mẫu lại có hoàn lại **theo từng người tham gia (`subject_id`)**, sau đó tính sai số trên toàn bộ các mẫu của người đó.
  - Tuyệt đối **KHÔNG bootstrap theo từng cửa sổ đo riêng rẽ**, vì điều đó vi phạm giả định độc lập quan sát (i.i.d).
- **Kiểm định giả thuyết (chưa khóa):**
  - Phép so sánh chính của RQ1 là mô hình PPG-only với mô hình PPG + PAT, cùng thuật toán và trên **cùng tập lần đo** có cả ECG và PPG đạt chất lượng (xem [RQ v0.2](../research_questions_v0.1.md), mục 4.C).
  - Hiệu ứng chính là chênh lệch MAE theo từng người; báo cáo trung bình và CI 95% bootstrap theo người. Wilcoxon signed-rank cặp theo người ($\alpha = 0.05$) là phân tích hỗ trợ.
  - SBP và DBP là hai phép kiểm định; cách hiệu chỉnh đa kiểm định (ví dụ Holm) phải chọn trước khi mở test.
  - Luôn báo cáo kèm baseline zero-change và SD của $\Delta\text{BP}$ tham chiếu.

---

## 10. Quản lý dữ liệu thiếu và Dữ liệu suy hao

- Trường hợp một lượt đo bị mất nhãn cuff (do lỗi máy đo bắp tay): Toàn bộ lượt đo đó bị hủy, không đưa vào tập huấn luyện hay kiểm thử.
- Trường hợp tín hiệu ECG bị nhiễu không bắt được đỉnh R nhưng PPG đạt chuẩn: lượt đo bị loại khỏi phép so sánh chính PPG-only vs PPG + PAT (để hai mô hình được đánh giá trên cùng tập), nhưng được giữ cho phân tích phụ PPG-only trên toàn bộ lượt đo. Ghi rõ tỷ lệ lượt đo mất ECG theo từng người, vì mất ECG không ngẫu nhiên có thể làm lệch kết quả.
- Không áp dụng phương pháp tự điền nhãn huyết áp bằng trung bình (imputation) cho biến đầu ra.

---

## 11. Rủi ro thực nghiệm và Phương án dự phòng

| Rủi ro kỹ thuật | Khả năng | Mức độ | Biện pháp phòng ngừa và xử lý |
|---|---|---|---|
| ECG cổ tay–ngón tay nhiễu, SNR thấp | Cao | Cao | Dùng ngón tay của tay đối diện chạm điện cực mặt trên để tạo đạo trình Lead I qua hai tay (tín hiệu mạnh hơn nhiều so với ECG lấy trên cùng một tay); thiết kế lọc dải thông khoảng $0.5 - 40\text{ Hz}$ và khuếch đại vi sai có CMRR cao (thông số cụ thể theo AFE được chọn); so sánh điện cực khô với Ag/AgCl dùng gel theo [yêu cầu phần cứng V0](../../configs/hardware/hardware_requirements_for_V0.md). |
| Nhiễu trôi đường nền PPG do lỏng dây đeo | Trung bình | Trung bình | Bổ sung cơ chế hiển thị SQI trực quan trên giao diện thu thập; hướng dẫn kỹ thuật viên siết chặt vòng vừa đủ trước khi bắt đầu đếm ngược 60 giây. |
| Biên độ biến thiên huyết áp tự nhiên giữa các phiên quá nhỏ ($< 5\text{ mmHg}$) | Trung bình | Cao | Bổ sung bài test kích hoạt sinh lý nhẹ trong protocol (ví dụ: tư thế ngồi xổm đứng dậy nhẹ nhàng hoặc ngâm tay nước ấm) ở các tuần sau khi đã được duyệt đạo đức. |
| Người tham gia cử động tay trong khi đo | Cao | Trung bình | Tích hợp thuật toán tự động hủy lượt đo và yêu cầu đo lại nếu SQI tụt dưới ngưỡng cho phép. |

---

## 12. Danh mục việc cần nhóm và giảng viên xác nhận

> [!IMPORTANT]
> **Checklist trước khi hoàn thiện protocol v1.0:**
> 1. [ ] Đức Anh xác nhận vị trí tiếp xúc và vật liệu điện cực ECG (điện cực khô thép không gỉ hay mạ vàng) trên vỏ hộp vòng đeo.
> 2. [ ] Linh xác nhận cấu trúc gói dữ liệu nhị phân/JSON truyền từ thiết bị vào máy tính có trường lưu `subject_id`, `session_id`, `event_id` và timestamp vi giây.
> 3. [ ] Thống nhất nhãn hiệu và model máy đo huyết áp bắp tay đối chứng dùng trong phòng thí nghiệm.
> 4. [ ] Xin ý kiến giảng viên hướng dẫn về quy trình làm việc với hội đồng đạo đức trước khi tuyển tình nguyện viên.
> 5. [ ] Đối chiếu khác biệt sampling, timestamp lấy mẫu/FIFO/nhận gói, clock và marker cuff với packet schema; ghi commit và quyết định trước khi khóa giao diện.
> 6. [ ] Kiểm tra căn cứ cỡ mẫu, cửa sổ, SQI, kiểm định và mọi tiêu chí an toàn/vận động dự thảo; không dùng outline để tự triển khai đo trên người.
