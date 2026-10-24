# Kịch bản bài báo P A / P B / P C — phác thảo v0.1

> Huy, 2026-10-21; sửa 2026-10-22 (tiêu chí G5 theo RQ mục E). R2/R3/R5 ở đây là
> dấu hiệu của kế hoạch 28 tuần, không phải quy tắc K1–K6 của protocol v0.2 mục
> 5.4. Phác thảo để chuẩn bị cổng G4 (Tuần 20); **chưa có dữ liệu
> người**, chưa chọn kịch bản. Ngưỡng kích hoạt lấy từ kế hoạch 28 tuần (tài liệu
> nội bộ ngoài repo: G4, dấu hiệu R2, R3, R5) và [RQ v0.2](research_questions_v0.1.md);
> đó là quy ước nội bộ, không phải tiêu chuẩn khoa học. Quyết định ở G4/G5 dựa
> trên số liệu đã khóa, không chọn kịch bản theo kết quả đẹp.

Đếm "người đạt chuẩn" theo snapshot G4: qua sàng lọc, có phiên hiệu chuẩn và ít
nhất một phiên sau (RQ1 cần ≥ 2 phiên/người), mỗi phiên có ≥ 2 lần cuff hợp lệ
có ECG và PPG đạt SQI đã khóa.

| | **P A — đủ dữ liệu** | **P B — thiếu dữ liệu** | **P C — kết quả âm tính** |
| --- | --- | --- | --- |
| Kích hoạt | G4: ≥ 15 người đạt chuẩn; median ΔSBP theo người ≥ 15 mmHg (R3; định nghĩa phải trùng P2 của [protocol v0.2](protocol/protocol_outline_v0.2.md) mục 6.5, **chờ thống nhất**); G5 theo [RQ v0.2](research_questions_v0.1.md) mục E: PPG + PAT có MAE thấp hơn zero-change, và CI 95% bootstrap theo người của trung bình $d_s$ = MAE(PPG + PAT) − MAE(PPG-only) nằm **hoàn toàn dưới 0**, hướng nhất quán; SBP và DBP đánh giá riêng, cách hiệu chỉnh đa kiểm định chọn trước khi mở test | G4: < 15 người đạt chuẩn (cảnh báo sớm R2: < 12 người ở Tuần 18), hoặc quá ít người có phiên sau để ước lượng CI | Đủ dữ liệu như P A, nhưng G5: CI của trung bình $d_s$ chứa 0 hoặc nằm trên 0 (nghiêng về PPG-only), hoặc R5: r giữa ΔBP dự đoán và tham chiếu < 0,3 hay không vượt B1 (zero-change) |
| Thông điệp chính | Trên dữ liệu cổ tay nhiều phiên, thêm PAT vào PPG thay đổi sai số ΔBP so với PPG-only ở mức [số đo được], kèm dải ΔBP tham chiếu | Nguyên mẫu thu ECG–PPG đồng bộ ở cổ tay, quy trình đánh giá chống rò rỉ và dữ liệu khả thi ban đầu; không kết luận về RQ1 | Sau hiệu chuẩn, chưa chứng minh được thêm PAT cải thiện so với PPG-only (CI của $d_s$ chứa 0 hoặc nằm trên 0), hoặc mô hình không vượt zero-change (R5), tùy điều kiện đã kích hoạt; hai so sánh này báo riêng. CI chứa 0 chỉ là không chứng minh được lợi ích, không phải bằng chứng không có lợi ích; báo độ rộng CI, dải ΔBP, nguồn sai số và điều kiện cần để phép so sánh có độ nhạy |
| RQ trả lời | RQ1 (chính), RQ2 (PulseDB + theo phiên), RQ3 nếu có đủ đoạn nhiễu tự nhiên | RQ2 phần PulseDB; RQ1 chỉ mô tả, không kiểm định; RQ3 thăm dò | RQ1 (kết quả âm tính có CI), RQ2, RQ3 nếu đủ dữ liệu |
| Bảng/hình chính | Bảng MAE/bias/SD theo SBP, DBP cho zero-change, PPG-only, PAT-only, PPG + PAT, CI theo người; hình chênh lệch MAE theo người; phân bố ΔBP theo nghiệm pháp | Sơ đồ thiết bị và đồng bộ; bảng jitter/offset/mất gói; bảng SQI và tỷ lệ dữ liệu bị loại; bảng RQ2 trên PulseDB (window vs subject split) | Như P A, nhấn SD ΔBP tham chiếu, hình sai số theo dải ΔBP; phân tích độ nhạy cửa sổ và phương pháp mốc |
| Bỏ | Triển khai trên MCU nếu chưa xong | Mọi tuyên bố về giá trị gia tăng của PAT; phân tích cross-session suy luận | Tuyên bố hiệu năng; mô hình phức tạp hơn baseline đã định trước |

Chung cho cả ba: SBP và DBP báo riêng; mỗi lần cuff là một nhãn; bootstrap theo
người; test khóa tới G5; không tuyên bố y tế, thay thế cuff hay đạt ISO/AAMI/ESH;
nêu rõ PAT = PEP + PTT, PAT không phải PTT. Kết quả PulseDB là BP tuyệt đối trên
ABP công khai, không thay được dữ liệu cuff cổ tay.

Việc còn mở: định nghĩa "đạt chuẩn" chính thức (khóa ở protocol v1, Tuần 10),
quy tắc hiệu chỉnh đa kiểm định SBP/DBP (Holm hay khác) trước khi mở test.
