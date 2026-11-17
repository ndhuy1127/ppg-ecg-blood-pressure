# B5 trên PulseDB Train 400 người, val (2026-11-11)

Bảng, report và đường học do `scripts/run_b5_pulsedb.py` sinh ra, chép nguyên từ
`runs/b5_pulsedb/20261111T152945997271Z/` (ngoài Git; `report.json` đổi tên thành
`b5_report.json`). Không có ID người. Dự đoán theo dòng (`predictions_val.csv`) và hai file
trọng số `.pt` ở lại trong `runs/`.

| File | Nội dung | SHA-256 |
| --- | --- | --- |
| [b5_table.md](b5_table.md) | B0, B3, B5 trên val: MAE/bias trung bình đều theo người, CI 95 % bootstrap theo người, hai hiệu ghép cặp định trước | `f6146adb5b341eb8fff3507bead79f5254cbe85f3953a2d3b8899d27c36a14c5` |
| [b5_report.json](b5_report.json) | Report đầy đủ: config, hash raw/split, `approval_committed`, QC nhãn, tập kiểm tra trong, footprint, môi trường, provenance | `2bfa7d6222342f5ef34ae001d0e67ed98c3dad5b1ec0ff868bbf8133dea5bc4a` |
| [history_sbp.csv](history_sbp.csv), [history_dbp.csv](history_dbp.csv) | MSE học và MAE trên tập kiểm tra trong theo epoch | `279d1d8d…`, `f0272677…` |

Trọng số: `model_sbp.pt` `f4d310827bce…`, `model_dbp.pt` `2d8677aa4c02…`, trùng từng byte với
lần chạy `inner` ngày 2026-11-07 (định nghĩa mục 7).

## Điều kiện chạy

- [Định nghĩa B5](../../../../docs/protocol/b5_pulsedb_definition.md), config
  `configs/models/b5_pulsedb_v0.json`, review về rò rỉ ngày 2026-11-11 (mục 9), duyệt nguyên
  trạng bằng commit riêng `38f23fe` trước khi chạy. Report ghi commit `38f23fe`,
  `workspace_has_changes: false`, `approval_committed`: config, định nghĩa và mã đều đã commit.
- Split v2 của B3 v1 (`pulsedb_train400_split_run01`, bốn hash ghim trong config). B5 học trên
  288 người train (103.680 đoạn), chọn epoch trên 32 người train còn lại; B0/B3 học lại trên cả
  320 người. Chấm val (40 người, 14.400 đoạn). Đoạn test không vào mô hình hay được chấm. QC
  `DBP ≥ SBP` không loại dòng nào.
- GPU RTX 4050 Laptop, PyTorch 2.6.0+cu124. Thời gian học SBP 21,3 phút (dừng ở epoch 31, chọn
  epoch 16), DBP 12,2 phút (dừng ở 21, chọn 6); cả lần chạy 41,7 phút; suy luận 0,27 ms mỗi đoạn.
  3,84 triệu tham số mỗi mô hình (15,5 MB).

## Kết quả

| Model | SBP MAE [CI 95 %] | DBP MAE [CI 95 %] |
| --- | --- | --- |
| B0 | 15,11 [13,47; 16,88] | 10,40 [9,12; 11,80] |
| B3 | 14,58 [12,89; 16,49] | 10,12 [8,94; 11,44] |
| B5 | 13,24 [11,84; 14,64] | 9,76 [8,56; 11,20] |

Hiệu ghép cặp định trước (mmHg, âm là B5 sai ít hơn):

- B5 − B0: SBP −1,87 [−3,23; −0,45], DBP −0,64 [−1,35; 0,15];
- B5 − B3: SBP −1,34 [−2,53; −0,16], DBP −0,36 [−0,91; 0,18].

B0 và B3 trùng số của Tuần 5 (tất định). Với SBP, CI của cả hai hiệu nằm dưới 0; với DBP, CI
chứa 0.

## Giới hạn

- Nhãn ABP xâm lấn công khai của bệnh nhân gây mê phẫu thuật, không phải cuff, không phải ΔBP,
  không phải thiết bị của nhóm. Đây là BP tuyệt đối của người chưa thấy.
- Val chỉ có 40 người; CI percentile theo người, chưa áp các kiểu CI của SAP.
- So sánh hai quy trình hoàn chỉnh, không phải hai kiến trúc có kiểm soát (B5 học trên ít
  người hơn nhưng được chọn epoch; định nghĩa mục 6).
- Test split và CalFree chưa chấm. B5 chỉ vào lần chấm đó nếu
  [đăng ký trước](../../../../docs/protocol/pulsedb_test_scoring_preregistration.md) được sửa và
  duyệt trước khi chấm.
