# Kế hoạch Tuần 10 — hồ sơ đạo đức nháp đủ, chuẩn bị G2 trên bàn, Aurora-BP

> Lập ngày 2026-11-22, cuối Tuần 9. Tuần 10 là 23/11–29/11/2026. Hai mốc chi phối: **nộp hồ sơ
> đạo đức 11/12** (cuối tuần này phải có bản nháp đủ) và **G2 trên bàn 06/12** (muộn nhất 27/12).
> Quyết đi tiếp hay dừng với Aurora-BP ngày 11/12.

## Mục tiêu và ranh giới

- **Đường găng là hồ sơ đạo đức.** Việc phần cứng chạy song song, nhưng không được làm chậm bản
  hồ sơ nháp.
- **Không đo trên người**, kể cả thành viên nhóm, cho tới khi có biên bản dòng rò đạt, có chữ
  ký người có chuyên môn và có phê duyệt phù hợp.
- **Không chạy phép thử MAX30001 có cấp điện** cho tới khi rõ nguồn AVDD/DVDD của breakout v2
  ([báo cáo bring-up](../../hardware/test_reports/2026-11-20_v1_bringup.md) mục 9.2, 9.3).
- Quyết định về trần δ, đo lặp cuff (C2) và M6 dựa trên bảng của
  [mô phỏng độ nhạy v3](../../reports/weekly/week_09/rq1_sensitivity_v3/summary.md) và quy tắc
  R1–R4 viết trước; không chọn phương án vì nó làm kết luận chính dễ đạt hơn. Hạn quyết 04/12.
- Aurora-BP: chưa mở biến huyết áp trước khi có SAP-Aurora đăng ký.

| Hạng mục | Trạng thái đầu Tuần 10 |
| --- | --- |
| Hồ sơ đạo đức | Đã sửa theo các mục chốt 2026-11-19 (hồ sơ, protocol, SAP, RQ, kịch bản bài báo), commit `7f295c8` trên `dev/huy`. Bản Word ngoài repo có hai file đổi ngày 21/11, chưa đối chiếu với file `.md` |
| Mô phỏng độ nhạy v3 (C1) | Đã chạy (commit `0f5595a`); R1 đạt ở thiết kế dự kiến. Còn: nhóm đọc bảng, quyết trần δ, C2, M6 |
| ESP32 và logger | Bo Waveshare đạt BU mục 2. Mốc đọc FIFO cho ECG: A2, A3, A10 đạt trên hai lượt dài; phân tích đồng bộ `sync-analysis-v2` có mô hình theo đoạn 60 s |
| MAX30001 | `PLLINT` kẹt, không có `SAMP`; cờ lead-off bật ở 0,65 V; không tìm thấy nút 1,8 V trên breakout. Đã hỏi hãng trong issue GitHub ngày 2026-11-22, chưa có trả lời |
| MAX30101, BMI270 | Chạy được khi nối thẳng ESP32 bằng dây (mục 10 báo cáo bring-up): PPG ngón tay rõ, trục BMI270 đúng. Chưa hàn lên bo cổ tay |
| Dụng cụ | Chưa có máy hàn, oscilloscope, USB tester; chưa có dụng cụ và người có chuyên môn cho đo dòng rò |
| Aurora-BP | Theo lộ trình: đọc DUA, gửi yêu cầu truy cập từ Tuần 9 |

## Phân công và tiêu chí kiểm tra

| Phụ trách | Việc | Đầu ra và nghiệm thu |
| --- | --- | --- |
| Huy | **Hồ sơ đạo đức:** rà bản trên `dev/huy` (`docs/ethics/`, protocol, SAP); đối chiếu hai file Word sửa ngày 21/11 với file `.md`, sửa ở `.md` rồi xuất lại | Bản hồ sơ nháp đủ; file `.md` và bản Word khớp nhau |
| Huy | **Hội đồng đạo đức** (nếu Tuần 9 chưa hỏi): đơn vị xét, điều kiện tiếp nhận, có cần biên bản dòng rò trước khi nhận hồ sơ, lịch họp, thời gian xét; việc dùng Aurora-BP có cần quyết định miễn xét | Câu trả lời ghi lại kèm ngày |
| Huy | **C2 và trần δ:** từ bảng mô phỏng v3, chuẩn bị 1–2 phương án đo lặp cuff (đo lặp ở plateau hay lặp chu kỳ nghiệm pháp), kèm thời lượng buổi và thời điểm bơm, kết thúc từng lần đo; đề xuất trần δ nếu cần (R4) | Phương án ghi kèm thời lượng, sẵn để quyết 04/12 |
| Huy | **MAX30001:** theo dõi trả lời của hãng về nguồn AVDD/DVDD, VCC thiết kế, schematic v2. Hạn 27/11: chưa có trả lời thì nhóm quyết cách đi tiếp | Câu trả lời hoặc quyết định ghi vào báo cáo bring-up kèm ngày |
| Huy | Báo cáo Tuần 9 (`reports/weekly/week_09/README.md`) | Có commit |
| Đức&nbsp;Anh | **Bo cổ tay:** hàn J1, header M1 và M3, C2, C3 theo [trình tự V1-module](../../hardware/test_reports/v1_bringup_procedure.md) mục 5; làm BU mục 8 (I²C, SPI, PPG, IMU, VLED+, nhiễu đèn) | BU mục 8 có số đo trong báo cáo bring-up |
| Đức&nbsp;Anh | **Đầu chuyển ECG và mạch chia áp** cho xung kích thích ([kế hoạch đo đồng bộ](../../hardware/test_reports/sync_10min_test_plan.md) mục 3); chưa dùng với MAX30001 cho tới khi rõ nguồn | Mạch có giá trị điện trở thực tế và số đo |
| Đức&nbsp;Anh | **Dụng cụ:** máy hàn, oscilloscope, USB tester (mượn hoặc mua) | Dụng cụ có ở bàn đo |
| Đức&nbsp;Anh | **Đo dòng rò:** dụng cụ, người có chuyên môn duyệt phương pháp và ký biên bản ([kế hoạch dòng rò và nhiệt](../../hardware/test_reports/leakage_thermal_test_plan_v1.md)) | Có tên người và ngày đo |
| Đức&nbsp;Anh | Việc nhỏ không cần điện: ghi mã MAX30101, BMI270 và jumper (mục 3 báo cáo bring-up); bắt vít M2; đọc lại `01C` thứ hai; thử uốn cáp ECG; điện trở 3V3–GND bo đế; mã LDO 3,3 V bo Waveshare | Ghi vào báo cáo bring-up |
| Đức&nbsp;Anh | **Tìm 2 người trực** cho buổi đo | Danh sách người trực |
| Đức&nbsp;Anh, Huy | **M6:** dụng cụ, cách đo và giữ lực, thời lượng, tiêu chí dừng, tiêu chí vào endpoint chính; thử trên bàn | Bản mô tả và một lần thử trên bàn, sẵn để quyết 04/12 |
| Đức&nbsp;Anh, Huy | **Máy đo huyết áp:** đúng model có validation đã công bố, đủ cỡ vòng bít; mua hoặc mượn; kiểm vận hành cùng logger | Tên model ghi vào hồ sơ |
| Linh | **Aurora-BP:** đọc DUA và mô tả dữ liệu, gửi yêu cầu truy cập (nếu chưa gửi), lập bảng đối sánh biến, đếm số cặp dùng được, ước lượng công sức | Bảng đối sánh biến và số cặp; sẵn để quyết ngày 11/12 |

## Phụ thuộc giữa các việc

- Tên model máy đo huyết áp, phương án C2 và mô tả M6 phải vào hồ sơ trước 11/12; ba việc này
  nằm trên đường găng của hồ sơ dù làm cùng phần cứng.
- Nếu hội đồng cần biên bản dòng rò trước khi nhận hồ sơ, việc đo dòng rò lên đường găng của hồ
  sơ; nộp ngay khi có biên bản, muộn nhất 24/12.
- **G2 ngày 06/12 phụ thuộc ba thứ chưa có:** máy hàn, oscilloscope và câu trả lời về nguồn
  của breakout MAX30001. Hết Tuần 10 mà vẫn thiếu cả ba thì báo sớm rằng G2 trễ, nhắm muộn
  nhất 27/12.
- Câu trả lời của hội đồng về Aurora-BP (miễn xét hay không) là đầu vào cho việc của Linh.

## Bàn giao và review chéo

1. Mỗi bàn giao kèm commit hoặc PR và người review.
2. Quyết định trong tuần ghi vào tài liệu tương ứng kèm ngày, trước khi xem kết quả.
3. Review chéo: Linh đọc bản hồ sơ nháp và phương án C2; Huy review số đo bo cổ tay và bảng
   đối sánh biến Aurora-BP.
4. Trước khi merge: `ruff check .`, `pytest -q`, `python scripts/check_environment.py`,
   `python -m pip check`.
5. **Mốc đóng tuần:** bản hồ sơ nháp đủ, `.md` và Word khớp nhau; phương án C2 và mô tả M6 sẵn
   để quyết 04/12; có tên model máy đo huyết áp;
   quyết định về MAX30001 ghi kèm ngày; bo cổ tay đã hàn và có số đo BU mục 8 (nếu có máy hàn);
   có tên người duyệt dòng rò; bảng đối sánh biến Aurora-BP. Phần nào chưa đạt ghi người xử lý
   và tuần chuyển sang.
