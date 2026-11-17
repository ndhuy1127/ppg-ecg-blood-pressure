# B2 v1 trên PulseDB Train 400 người, val (2026-11-07)

Bảng và report do `scripts/run_b2_pulsedb.py` sinh ra, chép nguyên từ
`runs/b2_pulsedb/20261107T064556Z/` (ngoài Git). Không có ID người. Dự đoán theo dòng và
`hr_mask.csv` ở lại trong `runs/`.

| File | Nội dung | SHA-256 |
| --- | --- | --- |
| [b2_table.md](b2_table.md) | Hai bảng `full` và `hr_available`, MAE/bias trung bình đều theo người, CI 95% bootstrap theo người, các hiệu ghép cặp định trước | `a4bc34ffbca1bdfc7af84ba84006f5a4dc244ed5e7f140806866fc8bc920f290` |
| [b2_report.json](b2_report.json) | Report đầy đủ: config, hash raw/split, `approval_committed`, `demographics_variation`, `hr_coverage`, `label_qc`, provenance | `786a551aec38dfb493eb3db6a9fda31a6d180ff1220354174e9e11cf0b11d5bf` |

## Điều kiện chạy

- Định nghĩa [B2 v1](../../../../docs/protocol/b2_pulsedb_definition.md), config
  `configs/models/b2_pulsedb_v1.json`, duyệt nguyên trạng bằng commit riêng `a215f07` trước khi
  chạy. Report ghi commit `a215f07`, `workspace_has_changes: false`, `approval_committed`:
  config, định nghĩa và mã đều đã commit.
- Split v2 của lần chạy B3 v1 (`pulsedb_train400_split_run01`, bốn hash ghim trong config).
  Fit trên train (320 người, 115.200 đoạn), chấm val (40 người, 14.400 đoạn). Đoạn test không
  được trích đặc trưng, dự đoán hay chấm. QC `DBP ≥ SBP` không loại dòng nào.
- HR đo được ở 115.078/115.200 đoạn train và 14.376/14.400 đoạn val; không người nào mất hẳn HR.
- `demographics_variation`: 4/320 người train có hai bộ nhân khẩu học; val 0/40.
- B2 v0 chạy trước đó cùng ngày (commit `1c708df`) đã dừng ở chốt "nhân khẩu học khác nhau
  trong một người" trước khi fit, nên không có số và không có thư mục kết quả
  ([định nghĩa](../../../../docs/protocol/b2_pulsedb_definition.md) mục 9).

## Đọc kết quả

- Nhân khẩu học không dự đoán BP tuyệt đối tốt hơn trung bình train trên val: B2a − B0 là
  SBP +1,29 [−0,39; 3,07], DBP +0,74 [−0,81; 2,30] mmHg (bảng `full`).
- Ước lượng HR từ ECG không thêm gì: B2b − B2a là SBP +0,05 [−0,89; 1,09], DBP −0,01
  [−0,61; 0,61] mmHg (bảng `hr_available`).
- B3 có sai số SBP thấp hơn B2: B3 − B2a SBP −1,82 [−3,52; −0,07]; B3 − B2b SBP −1,94
  [−3,76; −0,18] mmHg. Với DBP, CI chứa 0. Đây là so hai bộ đặc trưng khác nhau, không phải
  phần lợi thêm của dạng sóng so với nhân khẩu học (định nghĩa mục 5).

## Giới hạn

Nhãn ABP xâm lấn công khai của bệnh nhân gây mê phẫu thuật, không phải cuff, không phải ΔBP,
không phải thiết bị của nhóm; val chỉ có 40 người; siêu tham số là của B3 v1, không tinh
chỉnh; HR là ước lượng tốc độ đỉnh ECG chưa nghiệm thu; CI có điều kiện trên model đã fit.
Test split và CalFree chưa chấm, chỉ chấm theo
[đăng ký trước](../../../../docs/protocol/pulsedb_test_scoring_preregistration.md).
