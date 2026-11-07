# Kế hoạch Tuần 7 — B5, đường găng phần cứng, SQI và SAP, gặp thầy về hồ sơ đạo đức

> Lập ngày 2026-11-07, sau [báo cáo Tuần 6](../../reports/weekly/week_06/README.md). Kế
> hoạch 28 tuần ghi Tuần 7 là "Baseline SOTA, đặt PCB và khóa kế hoạch thống kê"; bản này
> thêm các việc chuyển từ Tuần 6 và các phát hiện của review ngày 2026-11-07.

## Mục tiêu và ranh giới

- **Đường găng vẫn là phần cứng.** Mọi đơn đã đặt (Huy báo 2026-11-07) nhưng chưa có ngày
  giao. Việc đầu tiên: ghi đủ đơn và ngày giao, rồi xếp tuần cho bring-up, đo đồng bộ 10 phút,
  đo dòng rò và G2.
- **Chưa có phê duyệt đạo đức và chưa có phần cứng: không đo trên người**, kể cả thành viên
  nhóm, cho tới khi hội đồng hoặc đơn vị có thẩm quyền trả lời bằng văn bản
  ([đề xuất Tuần 7](../meetings/week_07_de_xuat_sua_protocol_va_ho_so.md) mục 2.6).
- Benchmark PulseDB: chỉ val. Test split và CalFree chỉ chấm theo
  [đăng ký trước](../protocol/pulsedb_test_scoring_preregistration.md), sau khi mọi model đã
  khóa. B4 chỉ làm khi `gate` cho `B4_ALLOWED`.
- Logger phải sửa các điểm của review trước khi chạy cả hệ 120 phút ở bring-up.

| Hạng mục | Trạng thái đầu Tuần 7 |
| --- | --- |
| Baseline | Trên val: B0, B3 (Tuần 5); B3 ba seed `DETERMINISTIC`; B2 v1, nhân khẩu học và HR không tốt hơn B0 ([báo cáo Tuần 6](../../reports/weekly/week_06/README.md) mục 6.4–6.5). B4 bị chặn; B5 chưa có |
| Mốc R/foot | Đánh dấu tay lần 1: 28/80 đoạn |
| Phần cứng | KiCad V1-draft5, ERC/DRC 0 lỗi; mọi đơn đã đặt, chưa có ngày giao; Gerber gửi CXT chưa có commit/SHA-256 |
| Firmware, logger | Packet V0.2, `MARK_EVENT`, logger v3; chưa chạy trên chip. Review 2026-11-07: RAM logger, chưa có hiển thị mức DC khi chỉnh LED, kết quả lệnh không hiện lên màn hình, marker có thể trễ |
| Đạo đức | Bộ hồ sơ viết lại 2026-10-31, sửa 2026-11-07; chưa nộp |

## Phân công và tiêu chí kiểm tra

| Phụ trách | Việc | Đầu ra và nghiệm thu |
| --- | --- | --- |
| Linh | **B5 (kế hoạch 28 tuần):** chọn một mô hình đã công bố trên PulseDB ECG + PPG, tái lập trên đúng split v2, cùng QC nhãn, trọng số và quy trình đánh giá của B0–B3; ghi phần bám bài gốc và phần chỉnh vì dữ liệu. Thêm thư viện học sâu (PyTorch chưa là dependency) phải được duyệt trước | B5 trên val có CI bootstrap theo người, nằm trong bảng `collect_runs.py`; so footprint, thời gian, metrics với B0–B3; test chặn mọi đường đọc nhãn test khi tuning |
| Linh | **Logger theo review 2026-11-07:** bộ nhớ không tăng theo độ dài buổi (ghi CSV theo dòng, không giữ mọi packet); in ra màn hình kết quả mỗi lệnh khác `ok`; cảnh báo ngay khi `0xD2` của MAX30101 khác mã khóa; công cụ đọc mức DC (% thang đo) từng màu trong lúc ghi cho protocol 6.1; `MARK_EVENT` quá hạn tuổi thì không gửi và báo | Test SYNTHETIC cho từng điểm; đỉnh RAM đo lại trên luồng dài; [packet_logger.md](../protocol/packet_logger.md) cập nhật |
| Đức&nbsp;Anh | Ghi đủ nơi bán, ngày đặt, ngày giao, mã đơn ở [danh sách mua](../../hardware/bom/purchase_list_v1_module.md); ghi commit và SHA-256 của gói Gerber đã gửi CXT (nếu không truy được thì ghi rõ và xuất lại từ 9a10274); phương án thay thế cho kit MAX30001 (một nguồn) | Mỗi đơn có ngày giao; gói gia công truy được tới commit |
| Đức&nbsp;Anh | Chuẩn bị bring-up: dây đo, jig nạp, checklist; quy tắc nghiệm thu VLED khi đo được khoảng 5,1 V; phương pháp đo dòng rò và giới hạn so sánh viết đủ trước khi đo ([an toàn buổi đo](../ethics/session_safety_stopping_v0.1.md) mục 9) | Checklist bring-up; mục 9 không còn ô tiêu chí trống ngoài phần chờ người có chuyên môn ký |
| Huy | Đánh dấu tay nốt 52 đoạn của lần 1; lần 2 (16 đoạn) sau ít nhất 2 ngày; chạy `gate` | Kết quả `gate` lần 1; B4 chỉ khi `B4_ALLOWED` |
| Huy | **Gặp thầy:** các đề xuất 2.1–2.8 ở [đề xuất Tuần 7](../meetings/week_07_de_xuat_sua_protocol_va_ho_so.md); các mục "đề xuất của nhóm, chờ thầy"; chọn hội đồng; hỏi hội đồng có cần biên bản dòng rò trước khi nộp. Nhờ đầu mối y tế duyệt mục 6 và mục 8 của an toàn buổi đo. Dựng lại bộ Word từ các file nguồn đã sửa | Biên bản gặp thầy; danh sách mục đã chốt; protocol và hồ sơ sửa theo; nộp khi đủ điều kiện |
| Huy | **SQI specification v1 và SAP v1 (kế hoạch 28 tuần):** endpoint chính và phụ của RQ1, estimand, đa kiểm định (chọn phương án A hay B), cách tính δ từ độ lặp lại của cuff, ngưỡng P2/R3, quy tắc dữ liệu thiếu và lượt dừng, định nghĩa "người đạt chuẩn"; mô phỏng độ nhạy sơ bộ (2 phiên so với 3 phiên cùng số buổi, dải ΔBP của M0–M2) | SAP v1 khóa trước pilot, có commit và ngày; không phụ thuộc kết quả nào trên người |
| Huy | Review B5 về rò rỉ và so sánh công bằng | Ghi review vào tài liệu của B5 |

## Bàn giao và review chéo

1. Mỗi bàn giao kèm commit hoặc PR và người review.
2. Quyết định trong tuần ghi vào tài liệu tương ứng kèm ngày, trước khi xem kết quả.
3. Review chéo: Huy review B5 và logger; Linh review SAP (phần triển khai được trong code).
4. Trước khi merge: `ruff check .`, `pytest -q`, `python scripts/check_environment.py`,
   `python -m pip check`.
5. **Mốc đóng tuần:** mọi đơn có ngày giao và gói Gerber truy vết được; B5 trên val trong bảng
   tổng hợp; logger qua các test mới; SQI v1 và SAP v1 có commit; kết quả `gate` lần 1 (nếu đủ
   ngày cho lần 2) hoặc ghi tuần chuyển; biên bản gặp thầy. Phần nào chưa đạt ghi người xử lý
   và tuần chuyển sang.
