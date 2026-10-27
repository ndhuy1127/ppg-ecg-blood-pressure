# Kế hoạch Tuần 2 — dữ liệu công khai và chuẩn bị hệ v0

## Mục tiêu và ranh giới

- Linh xây dựng, kiểm thử pipeline đọc phần PulseDB được phép dùng và khảo sát ít nhất 1.000 đoạn ECG, PPG, ABP.
- Đức Anh chốt phương án phần cứng v0 trên tài liệu: BOM, sơ đồ khối, pin map, nguồn/mức logic, cấu hình lấy mẫu dự kiến và kế hoạch mua/mượn, lắp ráp, bring-up.
- Huy và Linh thống nhất định nghĩa mẫu, nhãn, cửa sổ và schema dữ liệu; Huy tổng hợp PAT/PTT/PEP/PWA và giới hạn diễn giải PAT.
- Cả ba thống nhất giao diện bàn giao dữ liệu dự kiến giữa logger và pipeline phần mềm.
- **Chưa có phần cứng PPG/ECG.** Tuần này chỉ nghiệm thu đầu ra dữ liệu công khai và thiết kế trên tài liệu; không coi PulseDB là bản ghi thiết bị của nhóm. Chưa tuyển người hoặc đo trên người bằng prototype khi chưa có phê duyệt đạo đức và kiểm tra an toàn cần thiết.

## Phân công và tiêu chí kiểm tra

| Phụ trách | Việc Tuần 2 | Đầu ra cần có để nghiệm thu tạm thời | Phụ thuộc / trạng thái lúc lập kế hoạch |
| --- | --- | --- | --- |
| Linh | Xác nhận quyền sử dụng, ghi nguồn, phiên bản và checksum phần PulseDB sử dụng; viết reader cho metadata, waveform ECG/PPG/ABP và nhãn; kiểm tra `subject_id`, kênh, đơn vị, tần số lấy mẫu; làm notebook vẽ tín hiệu, thống kê độ dài và missing values trên ít nhất 1.000 đoạn; test file thiếu, metadata trùng, sai kênh. | Code reader, notebook, test và hướng dẫn chạy lại; bằng chứng số đoạn đọc đúng và ánh xạ metadata/nhãn. Không commit toàn bộ dataset lên Git. | **Chưa xác nhận:** phiên bản PulseDB được phép dùng, checksum manifest và reader. Cần kiểm tra schema trên đúng phần dữ liệu được phép truy cập. |
| Đức Anh | Rà BOM Tuần 1; xác định linh kiện/board có thể mua hoặc mượn và phương án thay thế; đọc datasheet, lập bảng nguồn, điện áp logic, I2C/SPI, pin map, cấu hình và tần số lấy mẫu **dự kiến**; cập nhật sơ đồ khối, packet schema dự kiến và kế hoạch mua/mượn, lắp ráp, bring-up, kiểm tra khi nhận phần cứng. | BOM/phương án linh kiện, sơ đồ khối, bảng nguồn/giao tiếp/pin map, cấu hình lấy mẫu dự kiến, packet schema và quy trình bring-up đủ rõ để bắt đầu lắp khi có thiết bị. | **Đã có BOM v0.1 trong repo; chưa có phần cứng PPG/ECG.** Mọi thông số ở đây là thiết kế dự kiến, chưa phải số đo nguồn, waveform, timestamp hoặc tần số lấy mẫu thực. Chưa tự ý đặt mua khi chưa được duyệt. |
| Huy | Hoàn thiện tài liệu PAT/PTT/PEP/PWA: khoảng R peak ECG đến PPG foot là **PAT**, `PAT = PEP + PTT` theo cách viết gọn và PEP có thể biến đổi; định nghĩa một đối tượng, phiên đo, lần đo cuff, một quan sát và nhiều cửa sổ dùng chung nhãn; đề xuất cửa sổ 10/20/30/60 giây, quy tắc chia theo người và thứ tự thời gian; chốt schema nhãn/metadata với Linh, yêu cầu timestamp/định dạng gói với Đức Anh. | [Tài liệu định nghĩa mẫu, nhãn và glossary](../protocol/week_02_sample_label_glossary.md) được cập nhật và có quyết định review chéo về schema/cửa sổ. Có thể minh họa lỗi tín hiệu bằng PulseDB nếu ghi rõ đó là dữ liệu công khai, không phải tín hiệu thiết bị nhóm thu. | **Đã có bản thảo v0.1, chưa được review.** Không thể kiểm tra R peak, nhiễu, PPG foot hoặc đồng bộ trên thiết bị v0 trước khi có phần cứng và bản ghi hợp lệ. |

## Việc chung và mốc đóng tuần

1. Linh và Huy đối chiếu metadata/nhãn PulseDB với schema nhãn cuff dự kiến. PulseDB có ABP waveform; không xem đoạn ABP là một lần đo cuff độc lập, không gán nhiều cửa sổ cùng `event_id` thành nhiều nhãn độc lập.
2. Linh, Đức Anh và Huy thống nhất giao diện bàn giao logger → pipeline: định danh bản ghi/phiên/lần cuff, kênh và đơn vị, clock và timestamp hoặc chỉ số mẫu, tần số lấy mẫu dự kiến, trạng thái mất mẫu, phiên bản packet và cách liên kết nhãn. Ghi quyết định, người xác nhận và điểm còn mở trong [báo cáo Tuần 2](../../reports/weekly/week_02/README.md) hoặc PR liên quan; chưa coi packet dự kiến là schema đã kiểm chứng trên thiết bị.
3. Review chéo notebook PulseDB và tài liệu thiết kế phần cứng/phương pháp; ghi người review, commit hoặc phiên bản file, lỗi và quyết định. Nghiệm thu **tạm thời** khi reader/notebook chạy lại được trên ít nhất 1.000 đoạn có test và bằng chứng; BOM, sơ đồ khối, pin map, cấu hình dự kiến và kế hoạch bring-up đủ rõ; định nghĩa mẫu/nhãn/cửa sổ và packet schema được cả ba thống nhất.
4. Chỉ cập nhật trạng thái hoàn thành trong báo cáo tuần khi có đường dẫn đầu ra và bằng chứng kiểm tra. Review chéo và CI theo quy trình repo; ghi rõ phụ thuộc còn chờ phần cứng trước Tuần 3.

## Blocker và việc chuyển tiếp

- **Blocker: chưa có phần cứng PPG/ECG.** Chưa thể lắp hệ v0, đo nguồn hoặc giao tiếp thực, thu ECG–PPG, kiểm tra nhiễu/bão hòa/tiếp xúc điện cực/timestamp, hay bàn giao bản ghi thô v0.
- Theo dõi các việc trên để thực hiện ngay sau khi nhận phần cứng, theo kế hoạch bring-up và sau khi đáp ứng điều kiện an toàn/phê duyệt cần thiết cho mọi phép đo trên người.
- **Không đánh dấu đạt điểm kiểm soát gốc “có tín hiệu v0 đầu tiên”.** Nghiệm thu tạm thời Tuần 2 không thay thế mốc này; PulseDB không thay cho bản ghi thiết bị thật.

## Vấn đề cần nhóm quyết định

- Bản PulseDB, điều khoản sử dụng, nơi lưu và checksum manifest; schema thật phải được kiểm tra trên tệp được phép dùng trước khi khóa reader.
- Phương án linh kiện/board, mua hay mượn và phê duyệt mua; pin map, nguồn/mức logic và tần số lấy mẫu chỉ là dự kiến cho đến khi kiểm tra trên phần cứng.
- Trường logger, đơn vị tín hiệu, clock chung, timestamp và cách lưu thời điểm bắt đầu bơm cuff; schema nhãn/metadata cần Linh, Đức Anh và Huy cùng xác nhận.
- Cửa sổ phân tích chính và ngưỡng SQI chỉ được khóa trước trên pilot/validation; 10/20/30/60 giây hiện là ứng viên phân tích độ nhạy. Chia tập theo người, hiệu chuẩn trước kiểm tra theo thời gian; không dùng test set để chọn cửa sổ hoặc ngưỡng.
- Tài liệu phân công đề cập sáu giai đoạn và G1–G6. Các mốc đó vẫn là đề xuất của tài liệu ngoài repo, chưa phải kế hoạch đã khóa.

## Nguồn đối chiếu

- Mục “Tuần 2 — Dữ liệu công khai và tín hiệu v0 đầu tiên” (tệp do người dùng cung cấp, không commit vì nằm ngoài repo); mốc tín hiệu v0 được chuyển tiếp do thiếu phần cứng.
- [Protocol v0.1](../protocol/protocol_outline_v0.1.md), [chính sách dữ liệu](../DATA_POLICY.md), [câu hỏi nghiên cứu](../research_questions_v0.1.md).
- [Bài công bố PulseDB](https://doi.org/10.3389/fdgth.2022.1090854) và [repository của tác giả](https://github.com/pulselabteam/PulseDB).
