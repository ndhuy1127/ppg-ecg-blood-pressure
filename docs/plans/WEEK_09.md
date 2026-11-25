# Kế hoạch Tuần 9 — bring-up V1 khi hàng về, mô phỏng độ nhạy v3, hồ sơ đạo đức theo các mục chốt

> Tuần 9 là 16/11–22/11/2026, sau [báo cáo Tuần 8](../../reports/weekly/week_08/README.md). Module
> về trong tuần: bo Waveshare ESP32-S3, MAX30101 và BMI270; breakout MAX30001 đã về (bản v2).
> Hàng về là vào bring-up ngay; song song là các việc không cần phần cứng mà hồ sơ đạo đức và G5 cần.

## Mục tiêu và ranh giới

- **Đường găng là phần cứng.** Làm bring-up theo
  [trình tự V1-module](../../hardware/test_reports/v1_bringup_procedure.md) theo thứ tự hàng về;
  bước nào thiếu module thì làm bước khác không cần module đó.
- **Không đo trên người**, kể cả thành viên nhóm, cho tới khi có biên bản dòng rò đạt, có chữ
  ký người có chuyên môn và có phê duyệt phù hợp.
- **Quyết định thiết kế nghiên cứu dựa trên mô phỏng có luật đọc viết trước.** Số phiên mỗi người,
  trần δ, điều kiện để M6 vào endpoint chính và đo lặp cuff quyết từ bảng của mô phỏng độ nhạy v3,
  với luật đọc R1–R4 ghi trong config trước khi chạy; không chọn phương án vì nó làm kết luận chính
  dễ đạt hơn.
- **Không sửa module khi chưa có bằng chứng ở cả hai đầu linh kiện** (điều kiện ghi ở báo cáo Tuần 8
  mục 5.2); nếu không có schematic v2 thì nhóm quyết cách thay thế.
- Không mở thí nghiệm PulseDB mới. Đánh dấu tay PulseDB: nếu định nghĩa foot không vận hành được
  nhất quán thì dừng và ghi sai lệch, không sửa quy tắc giữa chừng để cho qua `gate`.

| Hạng mục | Trạng thái đầu Tuần 9 |
| --- | --- |
| Phần cứng | Bo Waveshare, MAX30101, BMI270 về trong tuần; breakout MAX30001 v2, chưa có schematic v2. Phần A checklist: phần viết và firmware build sẵn xong, các ô làm tay và mạch đo MD chưa làm |
| Dòng rò | Giới hạn chưa đối chiếu nguyên văn IEC 60601-1; chưa có người có chuyên môn duyệt |
| Logger | RAM đo trên laptop buổi đo ngày 2026-11-13; chưa đo khi đã đóng ứng dụng |
| Pipeline thiết bị, mốc, PAT, RQ1 | Chạy trên SYNTHETIC, có test; định dạng và cổng khóa duyệt 2026-11-14 |
| Đánh dấu tay PulseDB | Lần 1 dở dang; định nghĩa foot gặp trường hợp đáy có gờ, đáy phẳng; chưa chạy `gate` |
| Mô phỏng độ nhạy RQ1 | v1, v2 đã chạy; chưa có M6, đo lặp cuff, nhiễu cuff nhiều mức |
| Hồ sơ đạo đức | Bản v0.1 đủ thành phần; còn các mục chờ nhóm chốt (số phiên, thời gian đề tài, người trực, chia sẻ dữ liệu, thiết bị) |
| Aurora-BP | Theo lộ trình: đọc DUA, gửi yêu cầu truy cập từ Tuần 9 |

## Phân công và tiêu chí kiểm tra

| Phụ trách | Việc | Đầu ra và nghiệm thu |
| --- | --- | --- |
| Đức&nbsp;Anh | **Bring-up khi hàng về:** kiểm khi nhận (BU mục 1), bo Waveshare đứng riêng với logger (BU mục 2), bo đế và MAX30001 (BU mục 5–7) | Báo cáo bring-up có số đo từng bước; bước không đạt ghi cách xử lý |
| Đức&nbsp;Anh | **Firmware chẩn đoán** khi một bước bring-up không đạt (env riêng, không đổi bản nghiên cứu) | Env có test, ghi trong `firmware/README.md` |
| Đức&nbsp;Anh | **MAX30101, BMI270:** thử nhanh nối thẳng ESP32 nếu bo cổ tay chưa hàn được | Kết quả ghi vào báo cáo bring-up |
| Đức&nbsp;Anh | **Phần A checklist:** các ô làm tay còn lại | Ô đã tick, có commit |
| Đức&nbsp;Anh | **Dòng rò:** đối chiếu IEC 60601-1, tìm người duyệt (chuyển từ Tuần 8) | Giới hạn ghi kèm điều khoản nguồn; tên người duyệt |
| Đức&nbsp;Anh | **Phép đo đồng bộ:** định nghĩa tải cho tiêu chí offset theo tải và công cụ tạo lịch tải | Định nghĩa duyệt trước khi đo; script có test |
| Linh | **RAM logger** trên laptop đã đóng ứng dụng (chuyển từ Tuần 8) | Số đo ghi vào [packet_logger.md](../protocol/packet_logger.md) |
| Linh | **Ingest dữ liệu thiết bị:** thống kê phần dư mốc theo khối như A3; đưa các quy tắc thời gian mới của kế hoạch đo đồng bộ vào `device_session` khi có | Có test; tài liệu pipeline cập nhật |
| Linh | **Phân tích RQ1:** sửa theo rà soát (đếm mô hình lỗi, endpoint còn thiếu) | Có test |
| Linh | **Aurora-BP:** đọc DUA và mô tả dữ liệu, gửi yêu cầu truy cập | Ngày gửi yêu cầu; ghi chú điều kiện sử dụng |
| Huy | **Rà soát toàn dự án sau Tuần 8:** code, test, SAP, SQI, protocol, tài liệu pipeline | Sửa có commit; tài liệu khớp code |
| Huy | **Đánh dấu tay PulseDB:** tiếp lần 1 hoặc dừng nếu định nghĩa foot không vận hành được | Quyết định ghi kèm ngày và sai lệch ở [tài liệu mốc Tuần 5](../protocol/week05_fiducials_pat_validity.md) |
| Huy | **Mô phỏng độ nhạy RQ1 v3:** thêm M6, đo lặp cuff, nhiễu cuff nhiều mức, so với BP thật; luật đọc ghi trước khi chạy | Bảng kết quả; các quyết định ghi vào SAP kèm ngày |
| Huy | **Hồ sơ đạo đức, protocol, SAP** theo các mục nhóm chốt trong tuần | Có commit; README hồ sơ có bảng thay đổi |
| Huy | **Thời gian ECG–PPG:** chốt cách lấy mốc thời gian ECG nếu breakout không cho `SAMP`; tiêu chí và công cụ chấm phép đo đồng bộ | Quyết định ghi vào kế hoạch đo đồng bộ kèm ngày; công cụ có test |
| Huy | **Định nghĩa foot cho dữ liệu thiết bị** trước pilot (chuyển từ Tuần 8) | Định nghĩa có quy tắc cho đáy có gờ, đáy phẳng, có hình ví dụ |
| Huy | Kế hoạch Tuần 10 | Có commit |

## Phụ thuộc giữa các việc

- Mốc thời gian ECG phụ thuộc kết quả bring-up MAX30001 (có xung `SAMP` hay không); công cụ chấm
  phép đo đồng bộ và quy tắc trong `device_session` đi theo quyết định đó.
- Mô phỏng v3 là đầu vào cho các mục chốt của hồ sơ đạo đức (số phiên, thời gian đề tài).
- Hàng về lẻ từng phần thì làm trước các bước không cần đủ module, như Tuần 8.

## Bàn giao và review chéo

1. Mỗi bàn giao kèm commit hoặc PR và người review.
2. Quyết định trong tuần ghi vào tài liệu tương ứng kèm ngày, trước khi xem kết quả.
3. Review chéo: Huy review số đo bring-up và firmware chẩn đoán; Linh review công cụ phân tích đồng
   bộ; Đức Anh review phần thiết bị của hồ sơ đạo đức.
4. Trước khi merge: `ruff check .`, `pytest -q`, `python scripts/check_environment.py`,
   `python -m pip check`.
5. **Mốc đóng tuần:** bo Waveshare, bo đế, MAX30001 có số đo bring-up; mô phỏng v3 chạy và các mục
   chốt ghi vào SAP; hồ sơ đạo đức sửa theo các mục chốt; quyết định về đánh dấu tay PulseDB và về
   mốc thời gian ECG ghi kèm ngày; định nghĩa foot cho dữ liệu thiết bị; RAM logger đo lại; yêu cầu
   truy cập Aurora-BP đã gửi. Phần nào chưa đạt ghi người xử lý và tuần chuyển sang.
