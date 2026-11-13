# Kế hoạch Tuần 8 — chuẩn bị bring-up, mốc và PAT ở tần số thiết bị, phân tích RQ1 trên SYNTHETIC

> Lập ngày 2026-11-13, sau [báo cáo Tuần 7](../../reports/weekly/week_07/README.md). Module
> dự kiến về đủ đầu tuần sau. Tuần này làm những việc phải xong trước khi hàng về, và những việc
> không cần phần cứng mà bring-up và G5 sẽ cần.

## Mục tiêu và ranh giới

- **Đường găng vẫn là phần cứng.** Hàng về là vào bring-up ngay, nên phần A của
  [checklist bring-up](../../hardware/test_reports/v1_bringup_checklist.md) phải xong trước.
- **Tiêu chí đo phải được duyệt và commit trước khi có số đo.** Checklist bring-up, kế hoạch
  dòng rò/nhiệt/VLED và tiêu chí đồng bộ A1–A9 đang chờ duyệt; duyệt sau khi đo thì không còn
  là tiêu chí viết trước.
- **Không đo trên người**, kể cả thành viên nhóm, cho tới khi có biên bản dòng rò đạt, có chữ
  ký người có chuyên môn và có phê duyệt phù hợp.
- Luật chọn độ rộng xung LED (411 hay 215 µs) đã viết trước từ 2026-10-29
  ([interface_power_sampling_v0.md](../../configs/hardware/interface_power_sampling_v0.md)
  mục 6); không thêm tiêu chí nào khác.
- Không mở thêm thí nghiệm PulseDB mới ngoài RQ2a.

| Hạng mục | Trạng thái đầu Tuần 8 |
| --- | --- |
| Phần cứng | KiCad V1-draft5; module dự kiến về đầu tuần sau. Checklist bring-up, kế hoạch dòng rò/nhiệt/VLED, tiêu chí A1–A9 đã viết, chờ duyệt. Giới hạn dòng rò chưa đối chiếu nguyên văn IEC 60601-1, chưa có người có chuyên môn duyệt |
| Logger | Ghi theo dòng, hiển thị kết quả lệnh và mức DC (phần hiển thị chờ duyệt), hạn `MARK_EVENT`; RAM đo trên luồng tổng hợp, chưa đo trên laptop dùng cho buổi đo |
| Mốc, PAT, SQI | Chạy trên PulseDB (125 Hz, ECG và PPG cùng trục thời gian). Chưa chạy trên dữ liệu dạng thiết bị (ECG 512 sps, PPG 200 sps ba khe, timestamp riêng từng kênh). Luồng giả `packet_simulation_v3` chỉ có payload ngẫu nhiên, không có dạng sóng |
| Phân tích RQ1 | SAP v1 và SQI v1 có commit; mô phỏng `rq1_holm_loso` có Ridge, LOSO, Holm, baseline theo pha; chưa nối với dữ liệu dạng phiên thiết bị |
| Mốc R/foot | Lần 1 bắt đầu lại từ 0/80 đoạn (phiên 2026-10-25 bị bỏ); chưa chạy `gate`; B4 vẫn bị chặn |

## Phân công và tiêu chí kiểm tra

| Phụ trách | Việc | Đầu ra và nghiệm thu |
| --- | --- | --- |
| Đức&nbsp;Anh | **Phần A của checklist bring-up:** dụng cụ, dây đo, build sẵn bốn env firmware, bản in PCB 1:1, dựng sẵn mạch đo dòng rò MD, tạo mẫu `hardware/test_reports/<ngày>_v1_bringup.md` | Mọi ô phần A đã tick, có commit |
| Đức&nbsp;Anh | **Dòng rò:** đối chiếu giới hạn ở [leakage_thermal_test_plan_v1.md](../../hardware/test_reports/leakage_thermal_test_plan_v1.md) mục 2 và 4 với nguyên văn IEC 60601-1; tìm người có chuyên môn duyệt phương pháp, giới hạn và biên bản | Giới hạn ghi kèm điều khoản nguồn; có tên người duyệt và ngày hẹn |
| Linh | **RAM logger trên laptop dùng cho buổi đo:** `record` luồng SYNTHETIC 120 phút | Đỉnh RAM và thời gian giải mã cuối buổi ghi vào [packet_logger.md](../protocol/packet_logger.md); nếu không đủ RAM thì có phương án trước bring-up |
| Linh | **Pipeline dữ liệu thiết bị** (giai đoạn B, làm sớm): ingest phiên từ output logger, kiểm metadata, cắt cửa sổ quanh lần cuff, tóm tắt phiên | Chạy được trên luồng SYNTHETIC, có test |
| Linh | **RQ2a trên PulseDB** (train ∪ val): chia theo cửa sổ so với chia theo người, cùng mô hình và đặc trưng. Không nằm trên đường găng; không kịp thì chuyển tuần | Bảng chênh MAE có CI bootstrap theo người |
| Huy | **Duyệt và commit** checklist bring-up, kế hoạch dòng rò/nhiệt/VLED, tiêu chí đồng bộ A1–A9; duyệt phần hiển thị mức DC của `live_monitor.py` cho protocol 6.1 | Commit duyệt trước khi hàng về; các tài liệu bỏ nhãn "chờ duyệt" |
| Huy | **Đánh dấu tay:** đủ 80 đoạn lần 1 trong tuần; lần 2 (16 đoạn) sau ít nhất 2 ngày; chạy `gate` | Kết quả `gate`; B4 chỉ khi `B4_ALLOWED` |
| Huy | **Mốc, PAT, cờ SQI ở tần số thiết bị:** ghép hai trục thời gian (ECG 512 sps, PPG 200 sps ba khe) trước khi tính PAT; tạo dạng sóng SYNTHETIC ECG + PPG có PAT biết trước để kiểm | Test có đáp án: PAT tính ra khớp giá trị đặt trong sai số lượng tử hóa; chạy được trên output của pipeline ingest |
| Linh, Huy | **Code phân tích RQ1 trên SYNTHETIC:** nối mô hình của `rq1_holm_loso` (zero-change, PAT-only, PPG-only, PPG + PAT, baseline theo pha, LOSO, Holm) với dữ liệu dạng phiên thiết bị | Test có đáp án; G5 chỉ còn là một lần chạy |

## Phụ thuộc giữa các việc

- Pipeline ingest của Linh là đầu vào cho việc mốc/PAT của Huy. Hai người chốt định dạng đầu
  ra (tên cột, đơn vị timestamp, metadata) trước khi làm riêng, ghi vào
  [data_convention.md](../data_convention.md).
- Hàng về lẻ từng phần thì làm trước các bước không cần đủ module: bo Waveshare về trước thì
  làm bước 2 (nạp env khung, `record` 10 phút, có Linh); PCB về trước thì làm bước 3 (thông
  mạch, chập).

## Khi hàng về

1. Ngày đầu: kiểm khi nhận, chưa hàn, chưa cấp nguồn (bước 1); bo Waveshare đứng riêng với
   logger (bước 2). Đức Anh và Linh.
2. Tiếp theo: PCB trần, sửa module, hàn lắp, bo đế, MAX30001, bo cổ tay; đo VLED; chọn độ
   rộng xung theo luật đã viết (bước 3–9).
3. Sau khi chọn độ rộng xung: đo đồng bộ (thử 1 phút, 5 lần 10 phút, 1 lần 120 phút), chạy
   cả hệ 120 phút kèm thử nhiệt, đo dòng rò (bước 11–14).
4. Huy chạy mốc, PAT và cờ SQI trên log thật đầu tiên.

## Bàn giao và review chéo

1. Mỗi bàn giao kèm commit hoặc PR và người review.
2. Quyết định trong tuần ghi vào tài liệu tương ứng kèm ngày, trước khi xem kết quả.
3. Review chéo: Huy review pipeline ingest và RAM logger; Linh review code mốc/PAT ở tần số
   thiết bị.
4. Trước khi merge: `ruff check .`, `pytest -q`, `python scripts/check_environment.py`,
   `python -m pip check`.
5. **Mốc đóng tuần:** phần A checklist xong; tiêu chí phần cứng có commit duyệt; giới hạn dòng
   rò có điều khoản nguồn; RAM đo trên laptop buổi đo; pipeline ingest và mốc/PAT chạy trên
   SYNTHETIC có test; đủ 80 đoạn lần 1. Phần nào chưa đạt ghi người xử lý và tuần chuyển sang.
