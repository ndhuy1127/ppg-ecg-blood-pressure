# Kế hoạch đo dòng rò, thử nhiệt và nghiệm thu VLED trên V1-module

> **Trạng thái: đề xuất ngày 2026-11-07; phương pháp, ánh xạ phép đo, quy tắc đạt và quy tắc VLED
> duyệt ngày 2026-11-14.** Giá trị giới hạn số vẫn chờ đối chiếu nguyên văn và người có chuyên
> môn duyệt (gạch đầu dòng thứ hai dưới đây).
>
> - Chi tiết hóa [an toàn buổi đo](../../docs/ethics/session_safety_stopping_v0.1.md) mục 9 và
>   [bring-up](v1_bringup_procedure.md) mục 8 bước 3 và mục 10, để làm được ngay khi nhận
>   hàng (dự kiến Tuần 8).
> - **Giới hạn số ở mục 2 và 4 chưa được đối chiếu với nguyên văn IEC 60601-1.** Trước khi đo
>   phải đối chiếu từng con số với bản tiêu chuẩn và ghi số trang. Người có chuyên môn phải
>   duyệt phương pháp, giới hạn và biên bản trước khi gắn điện cực lên bất kỳ ai.
> - Không đo trên người, kể cả thành viên nhóm, cho tới khi có biên bản đạt và có phê duyệt phù
>   hợp.

## 1. Cấu hình đo

- Đúng cấu hình buổi đo: PCB V1 đã lắp đủ (bo đế, cáp, bo cổ tay), bo Waveshare, một cáp USB-C,
  laptop đo chạy pin. **Sạc rút ra, không cắm thiết bị nào khác vào laptop.**
- Firmware buổi đo (env và commit ghi vào biên bản), `record` đang ghi, mã LED ở trần `0x7F`
  (trường hợp xấu nhất về dòng).
- Điện cực: ba dây ECG (LA, RA, RL) nối vào miếng kim loại nhỏ thay cho điện cực dán, để nối
  được với mạch đo. Bo cổ tay đặt trên tấm kim loại cách điện với bàn, thay cho da.
- **Không nối oscilloscope hay thiết bị dùng điện lưới vào hệ trong lúc đo dòng rò.** Dây đất của
  chúng tạo thêm đường dòng.

## 2. Dòng rò

**Dụng cụ.**

- Ưu tiên mượn máy phân tích an toàn điện y tế, có phép đo dòng rò bệnh nhân và dòng phụ.
- Nếu không mượn được: dựng mạch đo MD theo IEC 60601-1 Hình 12 (**chưa đối chiếu nguyên
  văn**):
  - giữa hai đầu vào là điện trở 1 kΩ, song song với nhánh 10 kΩ nối tiếp tụ 15 nF;
  - đồng hồ đo **điện áp trên tụ 15 nF**, không phải trên điện trở 1 kΩ. Theo cách đọc này, 1 mV
    tương ứng 1 µA ở tần số thấp, và nhánh RC làm trọng số giảm dần theo tần số. Đo trên điện trở
    1 kΩ thì mất trọng số tần số đó;
  - đồng hồ true-RMS, trở kháng vào lớn (ít nhất 1 MΩ), dải tần đủ rộng. Ghi dải tần của đồng hồ
    trong biên bản.
- **Trước khi đo**, kiểm mạch MD bằng dòng đã biết ở DC và ở vài tần số (50 Hz, 1 kHz, 10 kHz).
  So số đọc với đáp ứng tính từ linh kiện và ghi sai số. Kiểm bằng DC thôi thì không phát hiện được
  việc đặt đồng hồ sai chỗ.

**Phép đo, ở điều kiện bình thường, máy đang ghi:**

1. **Dòng rò bệnh nhân:** nối chung LA, RA, RL làm một bộ phận ứng dụng, đo qua MD tới:
   (a) vỏ kim loại và vỏ cổng USB của laptop; (b) tấm kim loại dưới bo cổ tay; (c) đất bảo vệ
   của ổ điện trong phòng (đất tham chiếu).
2. **Dòng phụ bệnh nhân:** đo qua MD theo hai cách, ghi rõ các điện cực còn lại đang nối gì:
   - giữa từng cặp: LA–RA, LA–RL, RA–RL; giữa từng điện cực và tấm dưới bo cổ tay;
   - giữa **một đầu nối với người và mọi đầu nối còn lại nối chung**, kể cả tấm dưới bo cổ tay
     (tính cùng bộ phận ứng dụng, xem phần ánh xạ): LA–(RA+RL+bo), RA–(LA+RL+bo),
     RL–(LA+RA+bo), bo–(LA+RA+RL). Dòng từ một đầu nối tới các đầu nối khác có thể cộng lại dù
     từng cặp riêng đều đạt.
3. **Kiểm thêm (không phải điều kiện lỗi đơn của tiêu chuẩn):** lặp lại phép 1 khi cắm sạc
   laptop, để biết điều gì xảy ra nếu ai đó cắm sạc. Kết quả không dùng để cho phép cắm sạc lúc
   đo người.
4. **Phép thử đặt điện áp lưới lên bộ phận ứng dụng kiểu F:** chỉ làm bằng máy phân tích an toàn.
   Không làm bằng mạch tự dựng. Nếu không có máy thì ghi là **chưa đo**.

Mỗi phép đo ghi giá trị AC và DC, thang đo và độ bất định của đồng hồ.

**Giới hạn đề xuất, bộ phận ứng dụng kiểu BF** (IEC 60601-1:2005 + AMD1:2012, Bảng 3 và 4;
chưa đối chiếu nguyên văn; giá trị chờ đối chiếu và người có chuyên môn duyệt):

| Đại lượng | Bình thường, AC | Bình thường, DC | Lỗi đơn, AC | Lỗi đơn, DC |
| --- | --- | --- | --- | --- |
| Dòng rò bệnh nhân | 100 µA | 10 µA | 500 µA | 50 µA |
| Dòng phụ bệnh nhân | 100 µA | 10 µA | 500 µA | 50 µA |

**Ánh xạ phép đo với giới hạn (duyệt 2026-11-14):**

- **Một bộ phận ứng dụng.** Ba điện cực ECG và mặt bo cổ tay tiếp xúc da được coi là **một** bộ
  phận ứng dụng kiểu BF. Phép đo 1, với mọi đầu nối với người nối chung, so với giới hạn **dòng
  rò bệnh nhân** ở trên (100 µA AC, 10 µA DC).
- **Dòng phụ.** Mọi phép đo ở mục 2 so với giới hạn dòng phụ bệnh nhân.
- **Dòng rò bệnh nhân tổng** (500 µA AC ở điều kiện bình thường) chỉ dùng khi thiết bị có
  **nhiều bộ phận ứng dụng** riêng. Không dùng giới hạn này cho ba điện cực của một chức năng ECG.
  Áp nhầm thì ngưỡng nghiệm thu rộng gấp năm.
- Coi bo cổ tay là cùng bộ phận ứng dụng hay bộ phận riêng: người có chuyên môn quyết. Nếu là
  bộ phận riêng thì mỗi bộ phận đo riêng theo phép 1, và đo thêm dòng tổng.

**Quy tắc đạt (duyệt 2026-11-14):**

- mọi giá trị đo ở điều kiện bình thường, kể cả cộng độ bất định của mạch tự dựng, **không quá
  50 %** giới hạn bình thường tương ứng;
- phép thử nào chưa làm được thì ghi "chưa đo";
- người có chuyên môn quyết phần đã đo có đủ không (an toàn buổi đo mục 9).

Lý do lấy 50 %: mạch tự dựng và đồng hồ vạn năng có độ bất định lớn ở mức µA.

## 3. Nguồn LED VLED+ (quy tắc nghiệm thu, duyệt 2026-11-14)

**Bối cảnh.** Bo SparkFun tạo VLED+ bằng boost PAM2401 với chia áp R1 750 kΩ / R4 100 kΩ, tức
5,1 V danh định. Nhóm chốt ngày 2026-10-24 giữ nguyên, không sửa bo
([custom_board_proposal.md](../../configs/hardware/custom_board_proposal.md) A.6 mục 3).

Theo MAX30101 Rev 2, tr. 2:

- LED xanh cần 4,5–5,5 V;
- đỏ/IR được bảo đảm PSRR ở 3,1–5,0 V;
- giới hạn tuyệt đối là 6,0 V.

Tiêu chí cũ "4,5–5,0 V cho cả ba LED" (bring-up mục 8 bước 3,
[interface_power_sampling_v0.md](../../configs/hardware/interface_power_sampling_v0.md) mục
6) vì vậy luôn trượt với bo danh định. Quy tắc dưới đây thay tiêu chí cũ.

Đo tại net 5V của bo SparkFun bằng oscilloscope, đất tại GND của bo:

| # | Điều kiện | Đạt | Không đạt |
| --- | --- | --- | --- |
| V1 | Không tải (LED tắt), trung bình 1 s | 4,9–5,3 V (5,1 V ± 4 %, suy từ sai số của tham chiếu boost và điện trở 1 %, **chưa đối chiếu datasheet PAM2401**) | Ngoài dải |
| V2 | Lúc khởi động, đỉnh quá áp | ≤ 5,5 V (cách giới hạn tuyệt đối 0,5 V, cũng là trần dải LED xanh) | > 5,5 V |
| V3 | LED chạy xung ở mã cao nhất định dùng (`0x7F`), giá trị nhỏ nhất và lớn nhất trong xung | ≥ 4,5 V và ≤ 5,5 V | Ngoài dải |
| V4 | Đỏ/IR khi VLED+ ở 5,0–5,3 V | **Đạt có ghi chú:** ngoài dải bảo đảm PSRR nhưng dưới giới hạn tuyệt đối; không phải lỗi an toàn. Ở G2, ghi nhiễu nền PPG đỏ/IR lúc ngồi yên để xem có ảnh hưởng không | — |

Không đạt V1–V3 thì không dùng bo đó, tìm nguyên nhân (boost, tụ, nguồn USB) trước khi đi
tiếp. Đo 3V3 tại bo cổ tay cùng lúc với V3, như bring-up mục 8 bước 3.

## 4. Thử nhiệt

- **Cách làm:** chạy liên tục 120 phút (bằng buổi đo dài nhất) với mã LED `0x7F`, `record` đang
  ghi.
- **Cấu hình phải giống lúc đeo, không đặt trần trên bàn:**
  - bo cổ tay áp mặt cảm biến vào một khối giả da, **giữ ở 32–34 °C suốt 120 phút**, không để tự
    nguội. Ví dụ: hộp nước có bộ ổn nhiệt (sous-vide, bể ổn nhiệt), mặt trên là một tấm mỏng
    đặt bo lên. Ghi vật liệu và độ dày của tấm, ghi nhiệt độ khối giả da ở mọi mốc đo. Mốc nào
    lệch khỏi 32–34 °C thì ghi rõ và thử lại phần đó;
  - dây đeo quấn đúng nấc dùng thật, lớp vỏ hoặc băng che như khi đeo. Bo đặt trần trên bàn tản
    nhiệt tốt hơn lúc bị dây và da che;
  - nhiệt độ phòng ở **mức cao nhất dự kiến** của phòng đo: 26 °C theo protocol 6.1. Phòng thấp
    hơn thì ghi rõ và cộng chênh lệch vào kết quả, hoặc thử lại.
- **Đo:**
  - nhiệt độ ở mặt tiếp xúc giữa bo cổ tay và khối giả da, bằng cặp nhiệt dán (ưu tiên), mỗi 10
    phút. Nhiệt kế hồng ngoại không đo được mặt bị che;
  - nhiệt độ phòng và khối giả da ở cùng các mốc 10 phút;
  - độ bất định của cặp nhiệt (ghi theo nhà sản xuất), cộng vào giá trị cao nhất khi so với giới
    hạn.
- **Giới hạn đề xuất (chưa đối chiếu nguyên văn IEC 60601-1, Bảng 24):** bề mặt tiếp xúc da
  ≥ 10 phút không quá **43 °C**. Mức dừng nội bộ là **41 °C**, thấp hơn để có biên.
- **Quy tắc đạt:** nhiệt độ cao nhất trong 120 phút, cộng độ bất định của cặp nhiệt, ≤ 41 °C.
- **Ghi thêm:**
  - đỉnh RAM và kết quả cuối của `record` (đủ file và manifest), để dùng chung làm lần chạy cả
    hệ 120 phút ở bring-up;
  - mức pin laptop đầu và cuối.

## 5. Biên bản

File `hardware/test_reports/<YYYY-MM-DD>_v1_leakage_thermal.md` gồm:

- ngày, cấu hình (revision bo, commit firmware, ELF SHA-256);
- dụng cụ (tên, số hiệu, thang đo, độ bất định), sơ đồ mạch đo, ảnh;
- bảng giá trị từng phép đo, và so với giới hạn đã đối chiếu (ghi số trang của tiêu chuẩn);
- phép thử chưa làm được;
- kết luận và chữ ký của người có chuyên môn.

Dữ liệu thô ngoài Git (`runs/`), báo cáo ghi đường dẫn và SHA-256.
