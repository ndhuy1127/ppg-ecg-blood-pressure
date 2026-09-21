# Khung Protocol Nghiên cứu Thực nghiệm (Protocol Outline) - Phiên bản v0.1

> **Phiên bản:** v0.1
> **Người biên soạn:** Nguyễn Đức Huy
> **Vai trò:** Xử lý tín hiệu, PAT, thống kê, xây dựng protocol nghiên cứu
> **Ngày cập nhật:** 2026-09-22
> **Trạng thái:** Bản thảo đề xuất phương pháp luận (TUYỆT ĐỐI CHƯA THU THẬP DỮ LIỆU THẬT TRONG TUẦN 1)

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
  - **Phiên 2 & Phiên 3 (Evaluation Sessions):** Thu nhận tín hiệu và huyết áp ở các thời điểm khác nhau (ví dụ: sáng/chiều, sau nghỉ ngơi, sau vận động nhẹ) để đánh giá khả năng theo dõi biến thiên $\Delta\text{BP}$ trong tương lai.

---

## 4. Đối tượng tham gia dự kiến và Tiêu chí lựa chọn

### 4.1. Cỡ mẫu dự kiến
- Dự kiến $N = 15 - 20$ tình nguyện viên khỏe mạnh (sinh viên/cán bộ tại trường, độ tuổi 18–35).
- Cỡ mẫu này phù hợp cho giai đoạn thử nghiệm nguyên mẫu kỹ thuật (feasibility phase), đủ cung cấp $60 - 100$ lượt đo đối chứng độc lập phục vụ kiểm định thống kê cặp.

### 4.2. Tiêu chí lựa chọn (Inclusion Criteria)
- Độ tuổi từ 18 đến 40 tuổi, có đầy đủ năng lực hành vi dân sự.
- Tự nguyện ký vào phiếu đồng thuận tham gia nghiên cứu (Informed Consent).
- Nhịp tim xoang bình thường, không có tiền sử bệnh lý tim mạch đã được chẩn đoán.

### 4.3. Tiêu chí loại trừ (Exclusion Criteria)
- Người có tiền sử tăng huyết áp bệnh lý, hạ huyết áp tư thế, loạn nhịp tim (rung nhĩ, ngoại tâm thu dày) hoặc đang sử dụng thuốc tác động đến hệ tim mạch/hệ thần kinh giao cảm (thuốc chẹn beta, giãn mạch, an thần).
- Người có vết thương hở, viêm da, dị ứng hoặc kích ứng tiếp xúc tại vùng cổ tay đeo thiết bị.
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
- Sử dụng máy đo huyết áp bắp tay tự động đạt chuẩn chứng nhận y tế (Omron HEM-series đã kiểm định theo chuẩn AAMI/ESH/ISO).
- Vòng bít (cuff) được đặt ở **bắp tay đối diện (tay phải)**, hoặc cùng tay nhưng đo so le tuần tự (ưu tiên đo tay đối diện để có thể ghi tín hiệu liên tục ở tay đeo vòng mà không bị cản trở bởi lực ép dồn máu của cuff).
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
   - Thiết bị thu nhận tín hiệu PPG và ECG đồng bộ liên tục trong 60 giây ở trạng thái người tham gia ngồi yên tĩnh tuyệt đối.
   - Đây là **cửa sổ vàng** dùng để ghép cặp với nhãn huyết áp, vì lúc này huyết động hoàn toàn tự nhiên, không bị biến dạng do áp lực bẹp mạch máu của vòng bít.
2. **Giai đoạn 2 - Bơm đo huyết áp đối chứng bằng Cuff ($45 - 60\text{s}$):**
   - Kích hoạt máy đo bắp tay. Ghi nhận thời điểm bắt đầu bơm và kết thúc xả.
   - Tín hiệu thu được trong giai đoạn này được gắn cờ `cuff_inflating = True` và KHÔNG dùng để huấn luyện mô hình (do áp lực cuff làm xáo trộn tuần hoàn hệ thống).
3. **Giai đoạn 3 - Ghi nhãn và nghỉ hồi phục ($30\text{s}$):**
   - Ghi nhận kết quả SBP, DBP và Pulse Rate từ màn hình máy đo đối chứng vào biểu mẫu nghiên cứu.
   - Nghỉ tối thiểu 2 phút trước khi lặp lại lượt đo tiếp theo.

### 6.3. Đồng bộ thời gian phần cứng giữa ECG và PPG
- Tín hiệu ECG và PPG phải được lấy mẫu trên cùng một bộ vi điều khiển (MCU) sử dụng chung một khối định thời phần cứng (Hardware Timer).
- Tần số lấy mẫu:
  - PPG: $100\text{ Hz} - 250\text{ Hz}$.
  - ECG: $250\text{ Hz} - 500\text{ Hz}$.
- Từng mẫu dữ liệu được đóng gói kèm timestamp nguyên bản từ vi điều khiển (microsecond counter), loại bỏ hoàn toàn độ trễ truyền thông qua Bluetooth/Serial (UART).

---

## 7. Quy tắc phân đoạn, Gán nhãn và Kiểm soát chất lượng (SQI)

### 7.1. Định nghĩa mẫu độc lập (Independent Sample)
> [!CAUTION]
> **Nguyên tắc cốt lõi chống thổi phồng dữ liệu:**
> - **Mỗi lần đo bằng cuff đối chứng chỉ tạo ra DUY NHẤT 1 nhãn huyết áp độc lập ($\text{SBP}_i, \text{DBP}_i$).**
> - Tuyệt đối **KHÔNG** được cắt đoạn tín hiệu 60 giây trước đó thành 12 cửa sổ nhỏ (mỗi cửa sổ 5 giây) rồi gán cùng giá trị $(\text{SBP}_i, \text{DBP}_i)$ cho cả 12 cửa sổ và coi đó là 12 mẫu độc lập. Cách làm sai lầm này sẽ gây rò rỉ dữ liệu nghiêm trọng và thổi phồng sai lệch kích thước mẫu.
> - Các đặc trưng hình thái PPG và đại lượng PAT trong cửa sổ 30–60 giây trước đo cuff phải được tính toán trung bình hoặc trung vị (median) để đại diện cho trạng thái huyết động của lượt đo đó.

### 7.2. Định danh cấu trúc dữ liệu phân cấp
Mỗi bản ghi phải chứa khóa định danh duy nhất theo cấu trúc:
- `subject_id`: Mã người tham gia (ví dụ: `SUBJ_001`, `SUBJ_002`), không chứa thông tin định danh cá nhân.
- `session_id`: Mã phiên đo theo ngày/thời điểm (ví dụ: `SESS_01`, `SESS_02`).
- `event_id`: Mã lượt đo trong phiên (ví dụ: `EVT_01`, `EVT_02`).
- `window_id`: Mã cửa sổ tín hiệu thành phần bên trong một event.

### 7.3. Tiêu chí kiểm tra chất lượng tín hiệu (SQI) và Loại bỏ cửa sổ
Một cửa sổ tín hiệu bị loại bỏ (`flag_reject = True`) nếu vi phạm một trong các điều kiện:
1. **Nhiễu bão hòa quang học (Clipping/Saturation):** Tín hiệu PPG chạm ngưỡng kịch trần ADC ($V_{\text{max}}$ hoặc $V_{\text{min}}$) quá 5% thời gian cửa sổ.
2. **Chỉ số Skewness SQI ($s\text{SQI}$):** $s\text{SQI} < 0$ (dạng sóng PPG bình thường luôn có độ lệch dương).
3. **Mất tín hiệu ECG:** Không phát hiện được phức bộ QRS rõ ràng hoặc biên độ đỉnh R nhỏ hơn $3\times$ độ lệch chuẩn đường nền.
4. **Biến thiên nhịp tim bất thường:** Khoảng cách giữa các đỉnh R liên tiếp biến động $> 30\%$ trong cửa sổ tĩnh (ngoại trừ hiện tượng loạn nhịp sinh lý khi hô hấp đã kiểm soát).
5. **Cử động mạnh:** Cảm biến gia tốc IMU (nếu tích hợp) phát hiện gia tốc biến thiên $> 0.15\text{g}$ trong thời gian ghi tín hiệu nền.

---

## 8. Phương pháp tính toán đại lượng PAT và Cảnh báo vật lý

### 8.1. Công thức xác định PAT
$$\text{PAT} = t_{\text{PPG\_foot}} - t_{\text{ECG\_Rpeak}}$$
- $t_{\text{ECG\_Rpeak}}$: Thời điểm đỉnh sóng R của phức bộ QRS (xác định bằng thuật toán Pan-Tompkins hiệu chỉnh).
- $t_{\text{PPG\_foot}}$: Thời điểm chân sóng (foot) của nhịp PPG tương ứng, xác định bằng phương pháp tiếp tuyến giao cắt (intersecting tangent method) hoặc đạo hàm bậc hai cực đại ($d^2\text{PPG}/dt^2$).

### 8.2. Cảnh báo phương pháp luận: $\text{PAT} \neq \text{PTT}$
- Nhóm nghiên cứu ghi nhận rõ ràng:
  $$\text{PAT} = \text{PEP} + \text{PTT}$$
  Trong đó $\text{PEP}$ là thời gian tiền tống máu của tim.
- **Quy tắc bắt buộc:**
  - Không được áp dụng trực tiếp các phương trình vật lý sóng mạch thuần túy của PTT (như Bramwell-Hill hay Hughes) cho PAT mà bỏ qua PEP.
  - Mô hình học máy phải kết hợp đặc trưng nhịp tim (HR) và đặc trưng hình thái PPG để phần nào bù trừ sự biến thiên của PEP.

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
- **Kiểm định giả thuyết:**
  - So sánh mô hình kết hợp ECG+PPG với mô hình PPG-only bằng kiểm định phi tham số Wilcoxon signed-rank test cặp trên từng đối tượng. Ngưỡng ý nghĩa thống kê là $\alpha = 0.05$.

---

## 10. Quản lý dữ liệu thiếu và Dữ liệu suy hao

- Trường hợp một lượt đo bị mất nhãn cuff (do lỗi máy đo bắp tay): Toàn bộ lượt đo đó bị hủy, không đưa vào tập huấn luyện hay kiểm thử.
- Trường hợp tín hiệu ECG bị nhiễu không bắt được đỉnh R nhưng PPG đạt chuẩn: Lượt đo được giữ lại cho nhánh phân tích *PPG-Only*, nhưng bị loại khỏi nhánh phân tích *ECG+PPG/PAT* (ghi nhận rõ tỷ lệ mẫu mất kênh).
- Không áp dụng phương pháp tự điền nhãn huyết áp bằng trung bình (imputation) cho biến đầu ra.

---

## 11. Rủi ro thực nghiệm và Phương án dự phòng

| Rủi ro kỹ thuật | Khả năng | Mức độ | Biện pháp phòng ngừa và xử lý |
|---|---|---|---|
| Biên độ ECG tại cổ tay quá nhỏ, SNR thấp | Cao | Cao | Bố trí điện cực ngón tay đối diện (chạm mặt trên) để tăng diện tích đạo trình Lead I; thiết kế bộ lọc phần cứng dải thông $0.5 - 40\text{ Hz}$ kết hợp bộ khuếch đại đo lường có CMRR $> 100\text{ dB}$. |
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
