# Kịch bản bài báo P A / P B / P C — phác thảo v0.3

> 2026-10-21; sửa 2026-10-22 (tiêu chí G5 theo RQ mục E); v0.2 ngày 2026-10-29 (định nghĩa R3
> thống nhất với P2, nghĩa của "test khóa tới G5" theo LOSO lồng); v0.3 ngày 2026-10-29 (tiêu chí
> G5, cách đọc kết quả âm tính và hàng "RQ trả lời" theo RQ v0.4; đề xuất, chờ thầy; cùng ngày ghi
> hệ quả của việc bỏ M3, M4 đối với R3); 2026-11-12 (R3 chỉ để mô tả, bỏ khỏi điều kiện kích
> hoạt P A; phương án đa kiểm định A; thêm baseline trung bình theo pha vào bảng chính; theo
> [SAP v1](protocol/sap_v1.md), chốt, báo thầy).
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
chốt 2026-10-29). Phiên sau mang cờ `led_readjusted` (protocol 6.1) không vào phân tích chính, nên
không được tính là phiên sau đạt (sửa 2026-11-07, để mọi người đạt chuẩn đều đóng góp cho endpoint
chính). Các phiên còn lại không đạt hay bị thiếu cũng không làm người đó mất chuẩn, và các lần cuff
hợp lệ của những phiên đó vẫn được đưa vào phân tích, trừ phiên `led_readjusted` chỉ vào phân tích
độ nhạy. Người có dữ liệu đã dùng ở pilot để
khóa các lựa chọn thì không được tính ([protocol v0.3](protocol/protocol_outline_v0.2.md) mục 9.1).

**R3 (định nghĩa chốt 2026-10-29, vai trò chốt 2026-11-12):** với mỗi người đạt chuẩn $s$, tính
$m_s$ = median của |ΔSBP| trên mọi lần cuff hợp lệ ở phiên ≥ 2 (M0, M1, M2), so với
$\text{BP}_0$ = trung bình M0 phiên 1. Chỉ số R3 là median của $m_s$ trên tất cả những người đạt
chuẩn. Từ 2026-11-12, R3 **chỉ để mô tả** ở G4, báo kèm SD của ΔBP tham chiếu, và không còn là
điều kiện kích hoạt P A ([SAP v1](protocol/sap_v1.md) mục 9). Lý do: khi chỉ còn M1, M2, mô
phỏng cho R3 khoảng 4–5 mmHg ở mọi kịch bản, nên ngưỡng 15 mmHg không bao giờ đạt, và không có
ngưỡng R3 nào bảo đảm được kết luận chính; độ nhạy của RQ1 đã thể hiện ở độ rộng CI. Vì vậy cũng
không cần nhánh "đủ người nhưng R3 dưới ngưỡng". P2 ở pilot đổi sang ΔSBP có dấu của M2, ngưỡng
báo động 10 mmHg ([protocol](protocol/protocol_outline_v0.2.md) mục 6.5).

| | **P A — đủ dữ liệu** | **P B — thiếu dữ liệu** | **P C — kết quả âm tính** |
| --- | --- | --- | --- |
| Kích hoạt | G4: ≥ 15 người đạt chuẩn; G5 đạt kết luận chính của [RQ v0.4](research_questions_v0.1.md) mục 4.E, tức là với từng đầu ra, CI bootstrap theo người ở mức sau hiệu chỉnh đa kiểm định (95% trước hiệu chỉnh; sửa 2026-11-07) của trung bình $d^{0}_s$ (PPG + PAT so với zero-change) và của trung bình $d_s$ = MAE(PPG + PAT) − MAE(PPG-only) đều nằm **hoàn toàn dưới 0**. Đa kiểm định theo phương án A ([SAP v1](protocol/sap_v1.md) mục 6, chốt 2026-11-12); δ tính sau pilot theo quy tắc của SAP mục 8, trước khi chạy vòng ngoài | G4: < 15 người đạt chuẩn (cảnh báo sớm R2: < 12 người ở Tuần 18), hoặc có quá ít người có phiên sau để ước lượng CI | Đủ dữ liệu như P A, nhưng G5 không đạt kết luận chính: CI của trung bình $d_s$ không nằm hoàn toàn dưới 0 (chứa 0 hoặc nằm trên 0), hoặc CI của $d^{0}_s$ không nằm hoàn toàn dưới 0. Hoặc R5: r giữa ΔBP dự đoán và ΔBP tham chiếu < 0,3, hay mô hình không vượt B1 (zero-change). Khi CI của $d_s$ không đạt, kết quả được phân loại tiếp theo RQ mục 4.E thành: tương đương trong phạm vi $[-\delta; \delta]$, chưa kết luận, hoặc sai số tăng |
| Thông điệp chính | Trên dữ liệu cổ tay nhiều phiên, thêm PAT vào PPG làm giảm sai số ΔBP so với PPG-only ở mức [số đo được], kèm dải ΔBP tham chiếu. Nói rõ lợi ích có đạt mức δ hay không; chỉ gọi là đáng quan tâm khi cận trên của CI < −δ | Nguyên mẫu thu đồng bộ ECG–PPG ở cổ tay, quy trình đánh giá chống rò rỉ và dữ liệu khả thi ban đầu; không kết luận về RQ1 | Sau hiệu chuẩn, chưa chứng minh được rằng thêm PAT cải thiện so với PPG-only, hoặc mô hình không vượt zero-change (R5), tùy điều kiện nào đã kích hoạt; hai phép so sánh này được báo riêng. Phân biệt rõ "tương đương trong phạm vi δ" (kết quả âm tính có thông tin) với "chưa kết luận" (CI rộng, thiếu độ nhạy); chỉ trường hợp đầu mới cho phép nói rằng thêm PAT không cải thiện đáng kể. Báo độ rộng CI, dải ΔBP, các nguồn sai số và điều kiện cần để phép so sánh có độ nhạy |
| RQ trả lời | RQ1 (chính), RQ2b (cùng phiên so với khác phiên), RQ2a ở phụ lục, RQ3 thăm dò nếu có đủ đoạn nhiễu tự nhiên | RQ2a (phần PulseDB); RQ1 chỉ mô tả, không kiểm định; RQ3 thăm dò | RQ1 (kết quả âm tính có CI và δ), RQ2b, RQ2a ở phụ lục, RQ3 thăm dò nếu đủ dữ liệu |
| Bảng/hình chính | Bảng MAE/bias/SD theo SBP, DBP cho zero-change, độ lệch hằng số, trung bình theo pha, PPG-only, PAT-only, PPG + PAT, kèm CI theo người; hiệu so với trung bình theo pha ([SAP v1](protocol/sap_v1.md) mục 3, 7); hình chênh lệch MAE theo người; phân bố ΔBP theo nghiệm pháp | Sơ đồ thiết bị và đồng bộ; bảng jitter/offset/mất gói; bảng SQI và tỷ lệ dữ liệu bị loại; bảng RQ2a trên PulseDB (chia theo cửa sổ so với chia theo người) | Như P A, nhấn mạnh SD của ΔBP tham chiếu và hình sai số theo dải ΔBP; phân tích độ nhạy theo cửa sổ và theo phương pháp xác định mốc |
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
- giá trị δ, tính sau pilot theo quy tắc đã chốt ở [SAP v1](protocol/sap_v1.md) mục 8, khóa
  trước vòng ngoài.

Đã chốt 2026-11-12: phương án đa kiểm định A; R3 chỉ để mô tả và P2 mới (nên không cần nhánh
"đủ người nhưng R3 dưới ngưỡng").

P2 ở pilot và R3 ở G4 là hai thống kê khác nhau: P2 theo đáp ứng M2 trong một buổi, R3 tính cả
M0 của các phiên sau so với phiên 1.
