# Kịch bản bài báo P A / P B / P C — phác thảo v0.3

> Huy, 2026-10-21; sửa 2026-10-22 (tiêu chí G5 theo RQ mục E); v0.2 ngày 2026-10-29 (định nghĩa R3
> thống nhất với P2, nghĩa của "test khóa tới G5" theo LOSO lồng); v0.3 ngày 2026-10-29 (tiêu chí
> G5, cách đọc kết quả âm tính và hàng "RQ trả lời" theo RQ v0.4; đề xuất, chờ thầy; cùng ngày ghi
> hệ quả của việc bỏ M3, M4 đối với R3).
>
> Tên file vẫn giữ `v0.1` để các liên kết cũ không bị gãy. R2/R3/R5 ở đây là dấu hiệu của kế hoạch
> 28 tuần, không phải quy tắc K1–K6 của protocol mục 5.4. Bản phác thảo này dùng để chuẩn bị cho
> cổng G4 (Tuần 20). Hiện **chưa có dữ liệu người** và chưa chọn kịch bản nào. Các ngưỡng kích hoạt
> lấy từ kế hoạch 28 tuần (G4 và các dấu hiệu R2, R3, R5) và từ
> [RQ v0.4](research_questions_v0.1.md). Kế hoạch này là tài liệu nội bộ, nằm ngoài repo. Các ngưỡng
> kích hoạt là quy ước nội bộ, không phải tiêu chuẩn khoa học. Quyết định ở G4/G5 dựa trên số liệu
> đã khóa; không chọn kịch bản theo kết quả đẹp.

Số "người đạt chuẩn" được đếm theo snapshot ở G4. Một người đạt chuẩn khi đã qua sàng lọc, có phiên
hiệu chuẩn đạt và ít nhất một phiên sau đạt (RQ1 cần ≥ 2 phiên/người). Một phiên đạt khi có ≥ 2 lần
cuff hợp lệ tính được PAT và đặc trưng PPG; phân tích chính không lọc theo SQI (protocol mục 7.3,
chốt 2026-10-29). Các phiên còn lại không đạt hay bị thiếu cũng không làm người đó mất chuẩn, và các
lần cuff hợp lệ của những phiên đó vẫn được đưa vào phân tích. Người có dữ liệu đã dùng ở pilot để
khóa các lựa chọn thì không được tính ([protocol v0.3](protocol/protocol_outline_v0.2.md) mục 9.1).

**R3 (chốt 2026-10-29):** với mỗi người đạt chuẩn $s$, tính $m_s$ = median của |ΔSBP| trên mọi lần
cuff hợp lệ ở phiên ≥ 2 (M0, M1, M2), so với $\text{BP}_0$ = trung bình M0 phiên 1. Chỉ số R3 là
median của $m_s$ trên tất cả những người đạt chuẩn. P2 ở protocol mục 6.5 dùng cùng thống kê này
nhưng so với M0 của cùng buổi ở pilot. Ngưỡng 15 mmHg được đặt từ trước, cho câu chữ cũ; ngưỡng này
phải được xem lại trước khi khóa vì median chặt hơn max. Từ 2026-10-29, bộ nghiệm pháp chỉ còn M0–M2
(đã bỏ M3 ngâm chân nước lạnh và M4 đạp xe; protocol 6.4). Vì vậy R3 ≥ 15 mmHg rất khó đạt, và nếu
giữ ngưỡng này thì P A gần như không thể kích hoạt (suy luận, chưa có số liệu). Ngưỡng R3 và nhánh
"R3 dưới ngưỡng" phải chốt cùng thầy trước pilot.

| | **P A — đủ dữ liệu** | **P B — thiếu dữ liệu** | **P C — kết quả âm tính** |
| --- | --- | --- | --- |
| Kích hoạt | G4: ≥ 15 người đạt chuẩn; R3 (định nghĩa ở trên) ≥ 15 mmHg; G5 đạt kết luận chính của [RQ v0.4](research_questions_v0.1.md) mục 4.E, tức là với từng đầu ra, CI 95% bootstrap theo người của trung bình $d^{0}_s$ (PPG + PAT so với zero-change) và của trung bình $d_s$ = MAE(PPG + PAT) − MAE(PPG-only) đều nằm **hoàn toàn dưới 0**. Phương án đa kiểm định và δ được chọn trước khi chạy vòng ngoài | G4: < 15 người đạt chuẩn (cảnh báo sớm R2: < 12 người ở Tuần 18), hoặc có quá ít người có phiên sau để ước lượng CI | Đủ dữ liệu như P A, nhưng G5 không đạt kết luận chính: CI của trung bình $d_s$ không nằm hoàn toàn dưới 0 (chứa 0 hoặc nằm trên 0), hoặc CI của $d^{0}_s$ không nằm hoàn toàn dưới 0. Hoặc R5: r giữa ΔBP dự đoán và ΔBP tham chiếu < 0,3, hay mô hình không vượt B1 (zero-change). Khi CI của $d_s$ không đạt, kết quả được phân loại tiếp theo RQ mục 4.E thành: tương đương trong phạm vi $[-\delta; \delta]$, chưa kết luận, hoặc sai số tăng |
| Thông điệp chính | Trên dữ liệu cổ tay nhiều phiên, thêm PAT vào PPG làm giảm sai số ΔBP so với PPG-only ở mức [số đo được], kèm dải ΔBP tham chiếu. Nói rõ lợi ích có đạt mức δ hay không; chỉ gọi là đáng quan tâm khi cận trên của CI < −δ | Nguyên mẫu thu đồng bộ ECG–PPG ở cổ tay, quy trình đánh giá chống rò rỉ và dữ liệu khả thi ban đầu; không kết luận về RQ1 | Sau hiệu chuẩn, chưa chứng minh được rằng thêm PAT cải thiện so với PPG-only, hoặc mô hình không vượt zero-change (R5), tùy điều kiện nào đã kích hoạt; hai phép so sánh này được báo riêng. Phân biệt rõ "tương đương trong phạm vi δ" (kết quả âm tính có thông tin) với "chưa kết luận" (CI rộng, thiếu độ nhạy); chỉ trường hợp đầu mới cho phép nói rằng thêm PAT không cải thiện đáng kể. Báo độ rộng CI, dải ΔBP, các nguồn sai số và điều kiện cần để phép so sánh có độ nhạy |
| RQ trả lời | RQ1 (chính), RQ2b (cùng phiên so với khác phiên), RQ2a ở phụ lục, RQ3 thăm dò nếu có đủ đoạn nhiễu tự nhiên | RQ2a (phần PulseDB); RQ1 chỉ mô tả, không kiểm định; RQ3 thăm dò | RQ1 (kết quả âm tính có CI và δ), RQ2b, RQ2a ở phụ lục, RQ3 thăm dò nếu đủ dữ liệu |
| Bảng/hình chính | Bảng MAE/bias/SD theo SBP, DBP cho zero-change, PPG-only, PAT-only, PPG + PAT, kèm CI theo người; hình chênh lệch MAE theo người; phân bố ΔBP theo nghiệm pháp | Sơ đồ thiết bị và đồng bộ; bảng jitter/offset/mất gói; bảng SQI và tỷ lệ dữ liệu bị loại; bảng RQ2a trên PulseDB (chia theo cửa sổ so với chia theo người) | Như P A, nhấn mạnh SD của ΔBP tham chiếu và hình sai số theo dải ΔBP; phân tích độ nhạy theo cửa sổ và theo phương pháp xác định mốc |
| Bỏ | Triển khai trên MCU nếu chưa xong | Mọi tuyên bố về giá trị gia tăng của PAT; phân tích cross-session mang tính suy luận | Tuyên bố về hiệu năng; mô hình phức tạp hơn baseline đã định trước |

Áp dụng chung cho cả ba kịch bản:

- SBP và DBP được báo riêng.
- Mỗi lần cuff là một nhãn.
- Bootstrap lấy mẫu lại theo người.
- Test khóa tới G5, nghĩa là dự đoán vòng ngoài của LOSO lồng chỉ được sinh đúng một lần, sau commit
  khóa mọi lựa chọn (protocol mục 9.1).
- Không đưa ra tuyên bố y tế, không tuyên bố thay thế được cuff hay đạt ISO/AAMI/ESH.
- Nêu rõ PAT = PEP + PTT, và PAT không phải PTT.
- Kết quả PulseDB là BP tuyệt đối trên dữ liệu ABP công khai, không thay được dữ liệu cuff cổ tay.

Việc còn mở:

- định nghĩa chính thức của "đạt chuẩn", khóa ở protocol v1 (Tuần 10);
- phương án đa kiểm định (A hay B) và giá trị δ theo RQ v0.4 mục 4.E, khóa trước vòng ngoài;
- ngưỡng R3/P2 theo thống kê median và nhánh "≥ 15 người đạt chuẩn nhưng R3 dưới ngưỡng" (bảng chưa
  có nhánh này), khóa trước pilot.

Đạt P2 ở pilot không bảo đảm đạt R3, vì P2 chỉ tính cuff nghiệm pháp, còn R3 tính cả M0 của các
phiên sau.
