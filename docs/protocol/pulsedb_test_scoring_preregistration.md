# Đăng ký trước: chấm test split và CalFree trên PulseDB

> **Trạng thái:** chốt 2026-10-29. Phải commit **trước khi chạy B2 trên val** và
> trước khi xem bất kỳ con số nào của test split hay CalFree. Chưa có script chấm
> và chưa chấm lần nào. Đổi bất cứ điều gì dưới đây sau khi đã chấm thì phải nâng
> version và báo là phân tích hậu kiểm.

## 1. Hai tập kiểm tra

Hai tập trả lời hai câu hỏi khác nhau, nên báo riêng, không gộp:

| Tập | Nội dung | Câu hỏi |
| --- | --- | --- |
| Test split | 40 người `test` của `pulsedb-split-v2` (pool VitalDB Train, 400 người, seed 72; [run_pulsedb_split.md](run_pulsedb_split.md)) | Sai số trên người mới, cùng pool và cùng cách lấy mẫu với train |
| CalFree | `VitalDB_CalFree_Test_Subset.mat` (144 người theo bài báo PulseDB, đếm lại khi đọc; SHA-256 trong [provenance](../pulsedb_provenance.md)) | Sai số trên tập ngoài, người không có trong Train |

CalBased Test không dùng (cùng người với Train; quyết định pool 2026-10-24).

## 2. "Model đã khóa"

Một model được coi là đã khóa khi đủ các điều sau:

- Config của nó đã commit; với B2 là trạng thái đã duyệt, đổi bằng commit riêng
  ([b2_pulsedb_definition.md](b2_pulsedb_definition.md)).
- Model đã fit **chỉ trên train** của split v2 và đã chấm val bằng đúng commit đó.
- Bảng dự đoán val, và file model nếu runner có lưu, có SHA-256 ghi trong provenance
  của lần chạy.

Khi chấm test, không fit lại trên train ∪ val. Runner nào đã lưu file model thì
dùng đúng file đó (kiểm hash). Runner nào chưa lưu (hiện `run_b2_pulsedb.py` chỉ lưu
dự đoán) thì fit lại trên train bằng đúng commit, config và seed, rồi chứng minh tái
lập: dự đoán val của lần fit lại phải trùng hash với lần chấm val trước khi đọc nhãn
test.

## 3. Model được chấm

**Mọi** model đã khóa của benchmark PulseDB đều được chấm, mỗi model **đúng một
lần** trên mỗi tập:

- B0 và B3 của `b3-pipeline-v1`;
- B2a và B2b, nếu định nghĩa B2 được duyệt và đã chạy trên val;
- B4, chỉ khi lệnh `gate` cho `B4_ALLOWED` và B4 đã khóa
  ([Tuần 5](week05_fiducials_pat_validity.md) mục 9).

Không chọn một "model tốt nhất" trên val rồi chỉ chấm model đó. Cách đó vẫn hợp lệ
nếu test độc lập, nhưng val chỉ có 40 người nên CI rộng và lựa chọn dễ phụ thuộc
may rủi; chấm mọi model đã khóa thì báo đủ các phép so sánh.
Sau khi chấm không bỏ, thêm hay chỉnh model nào.

## 4. Nhãn và chỉ số

- QC nhãn giống lần chấm val: loại dòng có `DBP ≥ SBP` (`exclude_dbp_ge_sbp`,
  [provenance](../pulsedb_provenance.md)). Báo số dòng và số người bị loại ở mỗi tập.
- SBP và DBP báo riêng. Sai số = dự đoán − tham chiếu.
- Chỉ số chính: MAE trung bình đều theo người (`evaluate_bp`, subject-balanced).
  Báo kèm bias, SD, MAE theo mẫu.
- CI 95 %: bootstrap percentile theo người, 2 000 lượt, seed 20261013, như
  `configs/models/b3_pulsedb_v1.json`.
- Các phép so sánh ghép cặp theo người đã định trước cho val (B3 − B0; với B2 là các
  hiệu ở [b2_pulsedb_definition.md](b2_pulsedb_definition.md) mục 5) được báo y hệt
  trên từng tập, chỉ để mô tả, không dùng để chọn model.
- Kết quả là BP tuyệt đối trên ABP công khai, không phải cuff, không dùng để nói về
  RQ1.

## 5. Thời điểm và cách chạy

- Chấm một lần, sau khi mọi model dự kiến của benchmark đã khóa: B2 đã duyệt và chạy
  trên val, cổng mốc đã ra kết quả.
- Script chấm riêng (chưa viết) phải:
  - đọc test và CalFree bằng reader h5py lazy;
  - kiểm hash của raw, split và model trước khi đọc nhãn;
  - từ chối chạy lần hai khi đã có output (không ghi đè);
  - ghi provenance như các runner khác.
- Trước lúc đó, test split vẫn không được trích đặc trưng, CalFree không được đọc lại.
