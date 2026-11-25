# Kế hoạch Tuần 10 — chuẩn bị G2 trên bàn, C2 và M6, Aurora-BP

>Tuần 10 là 23/11–29/11/2026. Mốc chi phối: **G2 trên bàn
> 06/12** (muộn nhất 27/12). Quyết đi tiếp hay dừng với Aurora-BP ngày 11/12.
>
> Ngày 2026-11-25 bỏ khỏi tuần này: hồ sơ đạo đức, hỏi hội đồng đạo đức, hỏi chuyên gia ngoài
> nhóm và bác sĩ, đo dòng rò, tìm 2 người trực. Ngày 2026-11-26 bỏ đầu chuyển ECG (cáp cắm thẳng
> vào breakout, `custom_board_proposal.md` A.2).

## Mục tiêu và ranh giới

- **Đường găng là G2 trên bàn:** hàn bo cổ tay, nguồn breakout MAX30001, mạch chia áp cho xung kích thích.
- **Không chạy phép thử MAX30001 có cấp điện** cho tới khi rõ nguồn AVDD/DVDD của breakout v2
  ([báo cáo bring-up](../../hardware/test_reports/2026-11-20_v1_bringup.md) mục 9.2, 9.3).
- Quyết định về trần δ, đo lặp cuff (C2) và M6 dựa trên bảng của
  [mô phỏng độ nhạy v3](../../reports/weekly/week_09/rq1_sensitivity_v3/summary.md) và quy tắc
  R1–R4 viết trước; không chọn phương án vì nó làm kết luận chính dễ đạt hơn. Hạn quyết 04/12.
- Aurora-BP: chưa mở biến huyết áp trước khi có SAP-Aurora đăng ký.

| Hạng mục | Trạng thái đầu Tuần 10 |
| --- | --- |
| Mô phỏng độ nhạy v3 (C1) | Đã chạy (commit `0f5595a`); R1 đạt ở thiết kế dự kiến. Còn: nhóm đọc bảng, quyết trần δ, C2, M6 |
| ESP32 và logger | Bo Waveshare đạt BU mục 2. Mốc đọc FIFO cho ECG: A2, A3, A10 đạt trên hai lượt dài; phân tích đồng bộ `sync-analysis-v2` có mô hình theo đoạn 60 s |
| MAX30001 | `PLLINT` kẹt, không có `SAMP`; cờ lead-off bật ở 0,65 V; không tìm thấy nút 1,8 V trên breakout. Đã hỏi hãng trong issue GitHub ngày 2026-11-22, chưa có trả lời |
| MAX30101, BMI270 | Chạy được khi nối thẳng ESP32 bằng dây (mục 10 báo cáo bring-up): PPG ngón tay rõ, trục BMI270 đúng. Chưa hàn lên bo cổ tay |
| Dụng cụ | Chưa có máy hàn, oscilloscope, USB tester |
| Aurora-BP | Theo lộ trình: đọc DUA, gửi yêu cầu truy cập từ Tuần 9 |

## Phân công và tiêu chí kiểm tra

| Phụ trách | Việc | Đầu ra và nghiệm thu |
| --- | --- | --- |
| Huy | **C2 và trần δ:** từ bảng mô phỏng v3, chuẩn bị 1–2 phương án đo lặp cuff (đo lặp ở plateau hay lặp chu kỳ nghiệm pháp), kèm thời lượng buổi và thời điểm bơm, kết thúc từng lần đo; đề xuất trần δ nếu cần (R4) | Phương án ghi kèm thời lượng, sẵn để quyết 04/12 |
| Huy | **MAX30001:** theo dõi trả lời của hãng về nguồn AVDD/DVDD, VCC thiết kế, schematic v2. Hạn 27/11: chưa có trả lời thì nhóm quyết cách đi tiếp | Câu trả lời hoặc quyết định ghi vào báo cáo bring-up kèm ngày |
| Huy | Báo cáo Tuần 9 (`reports/weekly/week_09/README.md`) | Có commit |
| Đức&nbsp;Anh | **Bo cổ tay:** hàn J1, header M1 và M3, C2, C3 theo [trình tự V1-module](../../hardware/test_reports/v1_bringup_procedure.md) mục 5; làm BU mục 8 (I²C, SPI, PPG, IMU, VLED+, nhiễu đèn) | BU mục 8 có số đo trong báo cáo bring-up |
| Đức&nbsp;Anh | **Mạch chia áp** cho xung kích thích ([kế hoạch đo đồng bộ](../../hardware/test_reports/sync_10min_test_plan.md) mục 3); chưa dùng với MAX30001 cho tới khi rõ nguồn | Mạch có giá trị điện trở thực tế và số đo |
| Đức&nbsp;Anh | **Dụng cụ:** máy hàn, oscilloscope, USB tester (mượn hoặc mua) | Dụng cụ có ở bàn đo |
| Đức&nbsp;Anh | Việc nhỏ không cần điện: ghi mã MAX30101, BMI270 và jumper (mục 3 báo cáo bring-up); bắt vít M2; đọc lại `01C` thứ hai; thử uốn cáp ECG; điện trở 3V3–GND bo đế; mã LDO 3,3 V bo Waveshare | Ghi vào báo cáo bring-up |
| Đức&nbsp;Anh, Huy | **M6:** dụng cụ, cách đo và giữ lực, thời lượng, tiêu chí dừng, tiêu chí vào endpoint chính; thử trên bàn | Bản mô tả và một lần thử trên bàn, sẵn để quyết 04/12 |
| Đức&nbsp;Anh, Huy | **Máy đo huyết áp:** đúng model có validation đã công bố, đủ cỡ vòng bít; mua hoặc mượn; kiểm vận hành cùng logger | Tên model ghi lại kèm ngày |
| Linh | **Aurora-BP:** đọc DUA và mô tả dữ liệu, gửi yêu cầu truy cập (nếu chưa gửi), lập bảng đối sánh biến, đếm số cặp dùng được, ước lượng công sức | Bảng đối sánh biến và số cặp; sẵn để quyết ngày 11/12 |

## Phụ thuộc giữa các việc

- Phương án C2 và mô tả M6 phải sẵn trước ngày quyết 04/12.
- **G2 ngày 06/12 phụ thuộc ba thứ chưa có:** máy hàn, oscilloscope và câu trả lời về nguồn
  của breakout MAX30001. Hết Tuần 10 mà vẫn thiếu cả ba thì báo sớm rằng G2 trễ, nhắm muộn
  nhất 27/12.

## Bàn giao và review chéo

1. Mỗi bàn giao kèm commit hoặc PR và người review.
2. Quyết định trong tuần ghi vào tài liệu tương ứng kèm ngày, trước khi xem kết quả.
3. Review chéo: Linh đọc phương án C2; Huy review số đo bo cổ tay và bảng
   đối sánh biến Aurora-BP.
4. Trước khi merge: `ruff check .`, `pytest -q`, `python scripts/check_environment.py`,
   `python -m pip check`.
5. **Mốc đóng tuần:** phương án C2 và mô tả M6 sẵn để quyết 04/12; có tên model máy đo huyết
   áp; quyết định về MAX30001 ghi kèm ngày; bo cổ tay đã hàn và có số đo BU mục 8 (nếu có máy
   hàn); bảng đối sánh biến Aurora-BP. Phần nào chưa đạt ghi người xử lý
   và tuần chuyển sang.
