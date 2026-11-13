# Định nghĩa RQ2a trên PulseDB: chia theo cửa sổ so với chia theo người

> **Trạng thái: đề xuất ngày 2026-11-13, duyệt nguyên trạng ngày 2026-11-14** bằng commit riêng
> đổi `status` của [rq2a_pulsedb_v0.json](../../configs/models/rq2a_pulsedb_v0.json) từ
> `PROPOSED_NOT_RUN` thành `APPROVED_NOT_RUN`, **trước** khi chạy bất kỳ số nào (mục 8). Runner từ chối chạy nếu chính
> file config truyền vào, file này hoặc một file code chưa được Git theo dõi, khác HEAD hay là
> symlink (`committed_unchanged`, như B2 và B5), hoặc nếu split khác split đã ghim (mục 2).
> Trước commit duyệt chưa chạy lần nào trên dữ liệu thật. Sau khi thấy số thì không đổi gì; nếu phải đổi thì
> tạo version mới và báo cả hai.
>
> **Sửa 2026-11-13 (duyệt 2026-11-14), sau rà soát độc lập, trước mọi lần chạy:** nhãn A/B đổi cho khớp
> [câu hỏi nghiên cứu](../research_questions_v0.1.md) mục 5.B (A = chia ngẫu nhiên theo cửa sổ,
> B = chia theo người; bản đầu dùng ngược lại); hiệu vẫn là MAE(theo người) − MAE(theo cửa sổ),
> tức B − A; thêm chỉ số theo mục 5.D (RMSE, ME ± SD, % suy giảm, CI cho từng MAE và cho hiệu
> của B0); ghim hash split; cổng Git kiểm đúng file config đã truyền; thêm giới hạn về tính độc
> lập (mục 7).

## 1. Mục đích và vị trí

RQ2a ([research_questions_v0.1.md](../research_questions_v0.1.md), mục 5) hỏi: cùng mô hình
và đặc trưng, MAE thay đổi bao nhiêu khi chia ngẫu nhiên theo cửa sổ thay vì chia theo người.
Đây là **phép kiểm tra rò rỉ** báo ở phụ lục, không phải phát hiện mới: hiệu ứng đã có trong y
văn (Yoshizawa 2023, Mehta 2024, Moulaeifard 2025). Chênh lệch sai số không chứng minh nguyên
nhân duy nhất là mô hình nhận dạng người.

## 2. Dữ liệu và rào chắn

- Pool: người của `train` ∪ `val` của split v2 (pool VitalDB Train 400 người, seed 72), tức 360
  người. Với 360 đoạn mỗi người là 129 600 đoạn, trước QC nhãn.
- **Không bao giờ dùng test split và CalFree.** Config chỉ nhận `pool_splits = ["train", "val"]`;
  `make_designs` từ chối mọi dòng có `split` khác; runner không featurize đoạn test (như B3,
  `verify_inputs` vẫn đọc lại raw để băm, mọi dòng, nhưng không giá trị nào đi vào mô hình).
- QC nhãn như B3 v1: loại dòng có DBP ≥ SBP (trên split v2 là 0 dòng).
- **Split ghim** (thêm 2026-11-13, duyệt 2026-11-14): `split_sha256` của config ghi SHA-256 của raw,
  inventory, manifest và config của split. Runner so bốn giá trị này trước khi đọc đoạn nào;
  lệch là dừng. Giá trị là của split v2 `data/processed/pulsedb_train400_split_run01`: ba hash
  inventory, manifest, config tính lại từ file ngày 2026-11-13 và khớp `report.json` của split;
  hash raw lấy từ `report.json` đó (không băm lại file .mat). Bốn giá trị trùng `split_sha256`
  của [B5](b5_pulsedb_definition.md) (split của B3 v1).
- Theo [đăng ký trước](pulsedb_test_scoring_preregistration.md), mục này không chạm test.
  Dùng val làm một phần pool là hợp lệ vì RQ2a không chọn hay chỉnh mô hình.

## 3. Mô hình và đặc trưng: nguyên B3 v1

**Chọn:** B3 XGBoost với đúng [b3_pulsedb_v1.json](../../configs/models/b3_pulsedb_v1.json)
(300 cây, độ sâu 4, learning rate 0,05, seed 42, `n_jobs` 1), đặc trưng
`pulsedb-simple-stats-v0` (12 thống kê ECG/PPG), trọng số `inverse_subject_rows`. Config RQ2a ghim
SHA-256 (LF) của config B3; runner từ chối nếu khác.

**Lý do:** rẻ, tất định, đã khóa nên không cần tune lại, và
B3 đã là mô hình RQ2a nêu ở mục C của câu hỏi. B5 tốn khoảng 20 phút mỗi lần học mỗi đầu ra
và có bước chọn epoch, nên không hợp với nhiều lần lặp. B0 chạy kèm để biết sai số khi không dùng
tín hiệu.

**Trọng số** `1/n_s` được tính lại trên chính tập huấn luyện của từng cách chia. Vì vậy hai cách
chia có cùng quy tắc, không cùng vector trọng số (xem mục 7).

## 4. Thiết kế: cùng tập đánh giá, khác tập huấn luyện

**Chọn:** cả hai cách chia chấm trên **đúng cùng các cửa sổ đánh giá** E. Chỉ tập huấn luyện khác.
Một lần lặp (một seed) làm như sau, trên pool đã QC:

1. Chọn ngẫu nhiên `k = round(0,1 × số người)` người đánh giá (36 người với 360 người).
2. Với mỗi người đánh giá, chọn ngẫu nhiên `round(0,2 × n_s)` cửa sổ của người đó (72 trong 360),
   luôn chừa ít nhất một cửa sổ khác. Hợp các cửa sổ này là E.
3. **B (theo người):** huấn luyện trên mọi cửa sổ của các người **không** được đánh giá. Không
   có người chung với E.
4. **A (ngẫu nhiên theo cửa sổ):** huấn luyện trên một mẫu ngẫu nhiên, **đúng bằng số cửa sổ của
   B**, rút từ mọi cửa sổ của pool nằm ngoài E. Mẫu này gồm cả các cửa sổ khác của người đánh giá
   (khoảng 264 cửa sổ mỗi người, gần như là rò rỉ của chia ngẫu nhiên 80/20 trong từng người).

Nhãn A, B theo [câu hỏi nghiên cứu](../research_questions_v0.1.md) mục 5.B. Trong code và output:
`train_A`, `train_B`, `A_window`, `B_subject`.

Kích thước huấn luyện bằng nhau chính xác (324 × 360 = 116 640 đoạn với dữ liệu đủ). E không
nằm trong tập huấn luyện nào.

**Lý do chọn thiết kế này:**

- Chênh lệch MAE chỉ do tập huấn luyện, vì tập đánh giá, mô hình, đặc trưng, trọng số và chỉ số
  đều như nhau. Có thể ghép cặp theo từng người đánh giá.
- Chia ngẫu nhiên cổ điển chấm trên cửa sổ của mọi người, còn chia theo người chấm trên người
  khác nên hai tập đánh giá khác nhau, và phép trừ hai MAE trộn lẫn "khó hơn vì người khác" với
  "rò rỉ". Thiết kế trên tránh việc đó.

**Hạn chế:**

- Chỉ khoảng 10 % người được đánh giá mỗi lần lặp, và A chỉ rò rỉ cho những người đó. Đây không
  phải mô phỏng nguyên văn chia ngẫu nhiên 80/20 trên toàn pool, nhưng mức rò rỉ trên mỗi người
  đánh giá tương đương.
- Tập huấn luyện của A có mật độ cửa sổ của người đánh giá (khoảng 9 % tập huấn luyện) cao hơn
  B (0 %); đó chính là rò rỉ cần đo.
- Nếu hai cách chia khác nhau chỉ vì tập huấn luyện B thiếu người đánh giá, thì ΔMAE gộp cả
  tác dụng "có dữ liệu của chính người này" và "có dữ liệu gần về thời gian". Không tách được
  hai nguyên nhân này.
- Dữ liệu không có chronology đáng tin trong code hiện tại, nên không kiểm được ảnh hưởng của khoảng
  cách thời gian giữa cửa sổ huấn luyện và cửa sổ đánh giá.

## 5. Seed và lặp

- 5 seed cố định trước: 20261113, 20261114, 20261115, 20261116, 20261117 (config). Mỗi seed
  quyết định cả người đánh giá, cửa sổ E và mẫu huấn luyện của A. XGBoost dùng seed 42 như B3.
- Lý do lặp: một lần rút chỉ có 36 người, nên kết quả dao động. Năm lần lặp cho khoảng 180 cặp
  (lần lặp, người). Mỗi lần lặp fit 2 lần B3 và 2 lần B0, nên tổng 10 lần fit B3.
- Trọng số `1/n_s` tính lại trên chính tập huấn luyện của từng cách chia trong từng lần lặp
  (mục 3).
- Số seed và seed không đổi sau khi thấy kết quả.

## 6. Chỉ số và so sánh

Theo [câu hỏi nghiên cứu](../research_questions_v0.1.md) mục 5.D, riêng SBP và DBP, cho B3 và B0,
cho từng cách chia, trên E (sai số = dự đoán − tham chiếu):

- **MAE chính:** trung bình đều theo người (`evaluate_bp`, `subject_balanced`): MAE của từng người
  đánh giá, rồi trung bình đều trên mọi cặp (lần lặp, người). Mọi lần lặp có cùng số người đánh
  giá, nên giá trị này bằng trung bình MAE theo người của các lần lặp.
- **Hiệu định trước:** `ΔMAE = MAE_B − MAE_A = MAE(theo người) − MAE(theo cửa sổ)`. Dương nghĩa là
  chia theo cửa sổ trông tốt hơn.
- **% suy giảm tương đối:** `100 × (MAE_B − MAE_A) / MAE_A` (RQ: MAE nghiêm so với ngẫu nhiên).
- **RMSE, ME ± SD:** trên các cửa sổ của E, của từng lần lặp, rồi trung bình qua các lần lặp. Chỉ
  mô tả, không có CI.
- **CI:** bootstrap theo người (`cluster_draw`), seed 20261113, 2 000 lần, mức 95 %, percentile,
  cho MAE_A, MAE_B, ΔMAE và % suy giảm, của cả B3 và B0. Mỗi lượt rút lấy lại người của pool
  theo cụm (mọi cặp của người đó ở mọi lần lặp) rồi tính mọi trung bình trên **cùng** các hàng,
  nên A và B ghép cặp (cùng người, cùng cửa sổ). Người xuất hiện ở nhiều lần lặp vẫn là một cụm.
- Δ của B0 kỳ vọng gần 0 vì B0 không dùng đặc trưng; chỉ khác chút do trọng số. Không chạy so
  sánh nào khác.
- Báo thêm `between_replicate_se` của ΔMAE: SD của Δ giữa các lần lặp chia √(số lần lặp), đặt
  cạnh SE bootstrap (mục 7).
- Không đặt ngưỡng đạt hay không đạt; báo Δ kèm CI, riêng SBP và DBP, như mục 5.E của câu hỏi.

## 7. Giới hạn

- Nhãn là ABP xâm lấn công khai của bệnh nhân phẫu thuật VitalDB, đặc trưng là 12 thống kê đơn
  giản (nhiều thống kê min/max/range gần hằng vì ECG/PPG được chuẩn hóa từng đoạn). Một mô hình
  yếu như vậy có thể ít tận dụng rò rỉ hơn mô hình mạnh; Δ trên B3 là cận dưới tương đối của
  hiệu ứng rò rỉ, không phải của mô hình học sâu.
- Trọng số `1/n_s` tính lại theo từng tập huấn luyện, nên vector trọng số của A và B khác nhau.
  Đã xét việc dùng trọng số chung nhưng không thể: tập huấn luyện khác nhau.
- Chỉ có một pool 360 người từ một tập con VitalDB. Kết luận chỉ cho pool này.
- Kết quả báo ở phụ lục như kiểm tra rò rỉ; không dùng để chọn mô hình hay báo hiệu năng chính.
- Mỗi người đánh giá chỉ có 72 cửa sổ trong E; MAE theo người của một lần lặp nhiễu, nên cần
  CI theo người.
- **Tính độc lập (thêm 2026-11-13).** Mọi người được đánh giá trong một lần lặp dùng chung một mô
  hình A và một mô hình B. Bootstrap theo người coi d_s của họ là độc lập, nên bỏ qua phần dao
  động do chính lần fit (cùng một mô hình tốt hay kém cho cả 36 người). CI vì vậy có thể hẹp hơn
  mức danh nghĩa. Ước lượng ảnh hưởng: report ghi `between_replicate_se` (SD của Δ giữa các lần
  lặp chia √5), phần SE có tính dao động giữa các lần fit, cạnh `bootstrap_se`. Nếu
  `between_replicate_se` lớn hơn rõ `bootstrap_se` thì CI bootstrap đánh giá thấp độ bất định.
  Với 5 lần lặp, chính ước lượng này rất thô (4 bậc tự do), nên chỉ dùng để nêu giới hạn, không
  thay CI.

## 8. Duyệt bằng commit riêng trước khi chạy

**Duyệt ngày 2026-11-14, nguyên trạng,** bằng commit riêng đổi `status` của config thành
`APPROVED_NOT_RUN`, trước khi chạy. Các điểm tự chốt được duyệt:

1. Chọn B3 v1 làm mô hình duy nhất (mục 3).
2. Thiết kế cùng E, khác tập huấn luyện; 10 % người, 20 % cửa sổ mỗi người (mục 4).
3. 5 seed, bootstrap 2 000 lần seed 20261113, mức 95 % (mục 5 và 6).
4. Trọng số tính lại theo từng tập huấn luyện (mục 3).
5. Chỉ số của mục 6 (RMSE, ME ± SD trên cửa sổ, không CI; CI cho MAE, ΔMAE, % suy giảm) và
   `between_replicate_se` (mục 7), thêm 2026-11-13.
6. Split ghim `split_sha256` (mục 2), thêm 2026-11-13.

Test đã có đáp án trên dữ liệu SYNTHETIC (`tests/test_rq2a.py`): có thành phần riêng từng người
thì Δ > 0 và cận dưới CI > 0; không có thì Δ gần 0 và CI chứa 0; hai tập huấn luyện bằng nhau
về kích thước; E không nằm trong tập huấn luyện; chia theo người không có người chung; tất
định theo seed; runner từ chối ghi đè và config chưa duyệt. Thêm 2026-11-13: trọng số tính lại
trên đúng tập huấn luyện của A và của B; MAE là trung bình đều theo người (khác MAE gộp cửa sổ khi
số cửa sổ khác nhau); bootstrap ghép cặp (B − A cố định 0,5 cho mọi người thì CI của hiệu là
[0,5; 0,5]); config duyệt chép ra ngoài repo bị từ chối; một file code đổi bị từ chối; split khác
split ghim bị từ chối; runner chạy hết trên một file raw SYNTHETIC nhỏ (split dựng bằng
`build_pulsedb_split.py`). Lưu ý: seed dữ liệu của test "không có thành phần riêng người" được
chọn sau khi thấy seed đầu cho cận dưới CI +0,002; đây chỉ là test code. Test chỉ kiểm code,
không nói gì về hiệu năng huyết áp.

## 9. Code và chạy

- Module: `software/pulsedb/rq2a.py` (dùng lại `evaluate_bp`, `cluster_draw`, `XGBoostBaseline`,
  `PopulationMeanBaseline`, `subject_weights`). Runner: `scripts/run_rq2a_pulsedb.py`. Config:
  `configs/models/rq2a_pulsedb_v0.json`.
- Lệnh chạy, **chỉ sau khi duyệt** (không chạy trước đó):

```powershell
.\.venv\Scripts\python.exe scripts/run_rq2a_pulsedb.py --raw data/raw/pulsedb/VitalDB_Train_Subset.mat --split-dir data/processed/pulsedb_train400_split_run01
```

- Output `runs/rq2a_pulsedb/<UTC>/`: `rq2a_table.md`, `report.json` (provenance: commit,
  `workspace_has_changes`, `approval_committed`, SHA-256 đầu vào và mã, phiên bản thư viện,
  `source_type`). Runner từ chối ghi đè thư mục output.

## 10. Kết quả (chạy 2026-11-14)

Chạy một lần sau commit duyệt `6f6372b`; report ghi `workspace_has_changes: false` và
`approval_committed` đủ config, định nghĩa và code. Không đổi điểm nào của định nghĩa sau khi
thấy số. Bảng, report và hash:
[reports/weekly/week_08/pulsedb_rq2a_v0/](../../reports/weekly/week_08/pulsedb_rq2a_v0/README.md).

| Mô hình | Đầu ra | MAE A (theo cửa sổ) | MAE B (theo người) | ΔMAE = B − A [CI 95 %] | % suy giảm [CI 95 %] |
| --- | --- | --- | --- | --- | --- |
| B0 | SBP | 14,99 | 14,99 | 0,01 [−0,00; 0,02] | 0,06 [−0,03; 0,16] |
| B0 | DBP | 9,33 | 9,35 | 0,01 [−0,00; 0,02] | 0,12 [−0,02; 0,26] |
| B3 | SBP | 13,86 | 14,81 | 0,95 [0,64; 1,34] | 6,82 [4,66; 9,54] |
| B3 | DBP | 8,51 | 9,20 | 0,69 [0,50; 0,92] | 8,09 [5,97; 10,74] |

- Cả 5 lần lặp đều cho ΔMAE của B3 dương (SBP 0,70–1,29; DBP 0,55–0,76 mmHg).
- `between_replicate_se` nhỏ hơn `bootstrap_se` (B3 SBP 0,10 so với 0,18; DBP 0,04 so với
  0,11), nên ước lượng thô ở mục 7 không cho thấy CI bị hẹp do dùng chung mô hình.
- Đọc: với B3, chia theo cửa sổ cho MAE thấp hơn chia theo người khoảng 1 mmHg (7–8 %), CI trên
  0 ở cả SBP và DBP. Đây là cận dưới tương đối của hiệu ứng rò rỉ cho mô hình yếu (mục 7), báo
  ở phụ lục; không dùng để chọn mô hình hay báo hiệu năng.
