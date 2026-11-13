# RQ2a trên PulseDB: chia theo cửa sổ so với chia theo người (2026-11-14)

Bảng và report do `scripts/run_rq2a_pulsedb.py` sinh ra, chép nguyên từ
`runs/rq2a_pulsedb/20261113T210602Z/` (ngoài Git; `report.json` đổi tên thành
`rq2a_report.json`). Report không có ID người.

| File | Nội dung | SHA-256 |
| --- | --- | --- |
| [rq2a_table.md](rq2a_table.md) | B0, B3: MAE của A (theo cửa sổ) và B (theo người), hiệu B − A, % suy giảm, CI 95 % bootstrap theo người; RMSE, ME ± SD không CI | `fd083322e1afd92cfbc23c545c8aff2d5927ebccd595f196491432e0334f5415` |
| [rq2a_report.json](rq2a_report.json) | Report đầy đủ: config, hash raw/split, `approval_committed`, QC nhãn, kết quả từng lần lặp, provenance | `bd7437feed60ef1686a0339573b0ecb8b3b1713ddb3fde9431acfd637fe1bfda` |

## Điều kiện chạy

- [Định nghĩa RQ2a](../../../../docs/protocol/rq2a_pulsedb_definition.md), config
  `configs/models/rq2a_pulsedb_v0.json`, duyệt nguyên trạng bằng commit riêng `6f6372b` trước
  khi chạy. Report ghi commit `6f6372b`, `workspace_has_changes: false`, `approval_committed`
  đủ config, định nghĩa và 14 file code.
- Split v2 của B3 v1 (`pulsedb_train400_split_run01`, bốn hash ghim khớp). Pool train ∪ val:
  360 người, 129 600 đoạn. Đoạn test không vào mô hình hay được chấm. QC `DBP ≥ SBP` không loại
  dòng nào.
- 5 lần lặp (seed 20261113–20261117), mỗi lần 36 người đánh giá, 2 592 cửa sổ đánh giá chung
  cho A và B, 116 640 cửa sổ học cho mỗi cách chia; 180 cặp (lần lặp, người). Bootstrap theo
  người 2 000 lần, seed 20261113. Python 3.11.9, XGBoost 3.2.0; cả lần chạy khoảng 3 phút.

## Kết quả

ΔMAE = MAE(B, theo người) − MAE(A, theo cửa sổ), mmHg; dương nghĩa là chia theo cửa sổ trông tốt hơn.

| Mô hình | Đầu ra | MAE A [CI 95 %] | MAE B [CI 95 %] | ΔMAE [CI 95 %] | % suy giảm [CI 95 %] |
| --- | --- | --- | --- | --- | --- |
| B0 | SBP | 14,99 [14,02; 16,09] | 14,99 [14,03; 16,11] | 0,01 [−0,00; 0,02] | 0,06 [−0,03; 0,16] |
| B0 | DBP | 9,33 [8,64; 10,11] | 9,35 [8,66; 10,12] | 0,01 [−0,00; 0,02] | 0,12 [−0,02; 0,26] |
| B3 | SBP | 13,86 [12,99; 14,82] | 14,81 [13,79; 15,96] | 0,95 [0,64; 1,34] | 6,82 [4,66; 9,54] |
| B3 | DBP | 8,51 [7,90; 9,20] | 9,20 [8,51; 10,01] | 0,69 [0,50; 0,92] | 8,09 [5,97; 10,74] |

- ΔMAE của B3 theo từng lần lặp: SBP 1,29 / 0,70 / 1,01 / 0,76 / 0,97; DBP 0,72 / 0,74 / 0,67 /
  0,55 / 0,76 mmHg. Cả 10 giá trị đều dương.
- `between_replicate_se` của ΔMAE B3 (SBP 0,10; DBP 0,04) nhỏ hơn `bootstrap_se` (0,18; 0,11),
  nên theo ước lượng thô của định nghĩa mục 7, CI bootstrap không có dấu hiệu hẹp hơn mức
  danh nghĩa do dùng chung mô hình trong một lần lặp.
- B0 có ΔMAE gần 0, đúng kỳ vọng vì B0 không dùng đặc trưng.

## Đọc kết quả

Với B3 (12 thống kê đơn giản, XGBoost), chia ngẫu nhiên theo cửa sổ cho MAE thấp hơn chia theo
người khoảng 0,95 mmHg SBP (6,8 %) và 0,69 mmHg DBP (8,1 %); CI của cả hai nằm trên 0. Hiệu nhỏ
so với MAE khoảng 9–15 mmHg. Theo định nghĩa mục 7, đây là cận dưới tương đối của hiệu ứng rò
rỉ, vì mô hình yếu khó tận dụng rò rỉ; không phải số cho mô hình học sâu. Kết quả chỉ cho pool
360 người này, báo ở phụ lục như kiểm tra rò rỉ, không dùng để chọn mô hình.
