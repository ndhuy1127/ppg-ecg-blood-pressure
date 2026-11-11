# Định nghĩa B5 trên PulseDB: ResNet-18 1D của bài PulseDB (ECG + PPG)

> **Trạng thái: đề xuất ngày 2026-11-07, review ngày 2026-11-11 (mục 9), duyệt nguyên trạng
> ngày 2026-11-11** bằng commit riêng đổi `status` của `configs/models/b5_pulsedb_v0.json`
> thành `APPROVED_NOT_TEST_EVALUATED`, **trước** khi tính bất kỳ số B5 nào trên val. Runner từ chối
> chế độ `val` nếu config, file này và code chưa commit hoặc đã đổi. Trước khi duyệt chỉ
> chạy chế độ `inner` (mục 7): chỉ dùng người của train, không có số nào trên val hay test.
> Thêm PyTorch (`requirements-dl.txt`, tùy chọn, chỉ cho B5) được duyệt cùng commit đó. Sau khi đã thấy
> số trên val thì không đổi kiến trúc, quy trình học, cách chọn epoch hay phép so sánh; nếu
> phải đổi thì tạo version mới và báo cả hai.

## 1. Chọn mô hình

Kế hoạch Tuần 7 cần một mô hình đã công bố trên PulseDB, đầu vào ECG + PPG, tái lập trên
đúng split v2 với cùng QC nhãn, trọng số và quy trình đánh giá của B0–B3.

**Chọn:** mô hình mẫu trong chính bài công bố PulseDB: Wang W, Mohseni P, Kilgore KL,
Najafirad L. *PulseDB: A large, cleaned dataset based on MIMIC-III and VitalDB for
benchmarking cuff-less blood pressure estimation methods.* Front Digit Health
2023;4:1090854, doi:10.3389/fdgth.2022.1090854 (toàn văn PMC9944565, đọc ngày 2026-11-07).
Theo phần chữ của bài:

- ResNet-18 đổi thành 1D bằng cách thay các lớp tích chập, chuẩn hóa batch và pooling 2D
  bằng bản 1D;
- lớp đầu nhận 2 kênh (ECG và PPG của đoạn 10 s), lớp cuối là một đầu ra hồi quy;
- hai mô hình riêng cho SBP và DBP, cùng khởi tạo tham số với một seed cố định;
- hàm mất mát MSE, Adam với learning rate 10⁻⁶, 100 epoch.

**Lý do chọn:** cùng dataset, cùng dạng đoạn (10 s, 125 Hz, 1 250 mẫu), đúng đầu vào
ECG + PPG, và mô tả đủ để dựng lại. Benchmark học sâu trên PulseDB gần nhất trong tổng quan
(S8, Moulaeifard và cộng sự 2025) chỉ dùng PPG.

**Giới hạn của lựa chọn:**

- Bài không công bố MAE của mô hình này trên từng tập con, chỉ có đường cong theo epoch (Hình 5).
- Bài không công bố code huấn luyện; repo `pulselabteam/PulseDB` chỉ có script MATLAB tạo subset.

Vì vậy "tái lập" ở đây là dựng lại kiến trúc và quy trình theo mô tả, không có con số đích để
so. Hình 4 (sơ đồ lớp) chưa được đối chiếu. Bố cục lớp chi tiết ở mục 2 là của ResNet-18 gốc,
chờ duyệt.

## 2. Phần bám bài gốc

| Hạng mục | Bài PulseDB | B5 v0 |
| --- | --- | --- |
| Đầu vào | ECG và PPG của đoạn 10 s, 2 kênh | `ECG_F`, `PPG_F`, 1 250 mẫu ở 125 Hz, 2 kênh theo thứ tự đó |
| Kiến trúc | ResNet-18 đổi mọi lớp 2D thành 1D, 2 kênh vào, 1 đầu ra | Bố cục ResNet-18 gốc (He 2016, như `torchvision.resnet18`) đổi 1D. Gốc: tích chập 7 tap, stride 2, 64 bộ lọc → max pool 3 tap, stride 2. Thân: 4 tầng, mỗi tầng 2 khối cơ bản, 64/128/256/512 bộ lọc, stride 2 từ tầng 2. Đuôi: trung bình theo thời gian → 1 lớp tuyến tính. Khởi tạo như torchvision. 3,85 triệu tham số mỗi mô hình (`software/models/resnet1d.py`) |
| Đầu ra | Hai mô hình riêng SBP, DBP, cùng khởi tạo | Như bài; cùng seed khởi tạo cho cả hai |
| Mất mát, tối ưu | MSE; Adam, learning rate 10⁻⁶ | MSE có trọng số theo người (mục 3); Adam, learning rate 10⁻⁶ |
| Số epoch | 100 | Tối đa 100; chọn epoch bằng tập kiểm tra trong (mục 3) |

## 3. Phần chỉnh vì dữ liệu và quy trình của dự án

Bài không nêu hoặc khác dữ liệu ở các điểm dưới. Mỗi điểm là đề xuất, chờ duyệt.

- **Dữ liệu và split:** đúng split `pulsedb-split-v2` của B3 v1 (pool VitalDB Train 400
  người, seed 72); config ghim bốn hash, runner từ chối split khác. Bài huấn luyện trên tập
  Train của cả PulseDB (khoảng 900 nghìn đoạn từ MIMIC-III và VitalDB), còn ở đây 320 người
  train với 115 200 đoạn, nên dữ liệu ít hơn khoảng 8 lần. Learning rate 10⁻⁶ giữ nguyên
  theo bài, dù có thể học chậm hơn trên ít dữ liệu; kết quả kiểm trên train ở mục 7.
- **QC nhãn và trọng số:** như B3 v1, `exclude_dbp_ge_sbp` và `inverse_subject_rows` (mỗi
  người cùng tổng trọng số, trung bình 1). Bài không có trọng số.
- **Chọn epoch (bài không có):** 10 % số người train (32 người, chọn ngẫu nhiên theo người
  với seed của config) làm tập kiểm tra trong. Mô hình học trên 288 người còn lại. Sau mỗi
  epoch tính MAE trung bình đều theo người trên tập trong. Giữ epoch có MAE thấp nhất (sớm
  nhất nếu bằng nhau), dừng khi 15 epoch liền không tốt hơn hoặc hết 100 epoch. Bài thấy sai
  số calibration-free tăng sau khoảng 20 epoch nhưng vẫn chạy đủ 100. Không học lại trên cả
  320 người, nên B5 học trên ít người hơn B0/B3 (B0/B3 học trên cả 320).
- **Batch:** 64 đoạn (bài không nêu). Thứ tự xáo theo seed.
- **Chuẩn hóa đầu vào (bài không nêu):** mỗi kênh trừ trung bình và chia độ lệch chuẩn tính
  trên toàn bộ đoạn của phần học (288 người). Không chuẩn hóa từng đoạn, để giữ biên độ.
- **Chuẩn hóa nhãn (bài không nêu):** SBP và DBP chuẩn hóa theo trung bình và độ lệch chuẩn
  của phần học; dự đoán đổi lại mmHg.
- **Tất định:** seed cố định, `torch.use_deterministic_algorithms(True)`,
  `CUBLAS_WORKSPACE_CONFIG=:4096:8`, cuDNN deterministic. Chạy trên GPU nếu có (report ghi
  thiết bị, tên GPU, phiên bản PyTorch và CUDA). Trọng số trên GPU và CPU có thể khác chút ít.
- **Môi trường:** `torch==2.6.0` (bản CUDA 12.4 trên máy có GPU NVIDIA), trong
  `requirements-dl.txt` và mục `dl` của `pyproject.toml`. Phần còn lại của repo không cần
  PyTorch; test B5 tự bỏ qua khi thiếu.

## 4. Đánh giá

- Chỉ val (40 người, 14 400 đoạn), như B0–B3. Test và CalFree chỉ chấm theo
  [đăng ký trước](pulsedb_test_scoring_preregistration.md). B5 chỉ được đưa vào lần chấm đó
  nếu đăng ký trước được sửa và duyệt trước khi chấm.
- Trong cùng lần chạy, B0 và B3 được học lại đúng như B3 v1 trên cả 320 người train. Kết quả
  tất định nên trùng số của Tuần 5. Ba mô hình được chấm cùng nhau: MAE và bias trung bình
  đều theo người, CI 95 % bootstrap theo người (seed 20261013, 2 000 lần).
- So sánh định trước, ghép cặp trên cùng các lần bootstrap: **B5 − B0** và **B5 − B3**
  (hiệu MAE trung bình đều theo người, âm là B5 sai ít hơn). Không có so sánh nào khác.
- Footprint ghi trong report: số tham số, kích thước `state_dict`, thời gian học từng mô
  hình, thời gian cả lần chạy, ms suy luận mỗi đoạn trên val, thiết bị.
- Bảng tổng hợp: `scripts/collect_runs.py` đọc `runs/b5_pulsedb/` (`b5-pipeline-v0`).

## 5. Chống rò rỉ

- Mọi thống kê dùng để chuẩn hóa, và trọng số của phần học, chỉ tính trên phần học. Tập kiểm
  tra trong là người của train, tách theo người.
- **Đầu vào của mô hình:** dạng sóng của đoạn train (chế độ `inner`), hoặc train và val (chế
  độ `val`, val chỉ để dự đoán sau khi mô hình đã chốt). Đoạn test không bao giờ vào mô hình
  hay được chấm.
- **Các lần đọc khác, không vào mô hình** (sửa 2026-11-11 sau review; bản trước ghi "nhãn val
  chỉ được đọc khi chấm"):
  - như B2/B3, `verify_inputs` đọc lại mọi dòng của raw, kể cả nhãn và dạng sóng của val và
    test, chỉ để băm và so với inventory;
  - QC nhãn (`exclude_dbp_ge_sbp`, chốt trước) chạy trên train và val trước khi học, như B3
    v1; report của cả hai chế độ ghi số dòng bị loại ở train và val (trên split v2: 0 dòng;
    test không áp QC, ghi `None`).

  Không giá trị nào từ hai bước này đi vào việc học, chuẩn hóa hay chọn epoch.

`tests/test_b5_pipeline.py` kiểm bằng dữ liệu SYNTHETIC rằng `waveforms()` (đường vào mô
hình) chỉ đọc đoạn train (chế độ `inner`) hoặc train và val (chế độ `val`), không bao giờ
test, và trọng số của phần học có trung bình 1, mỗi người cùng tổng trọng số. Test không chặn
các lần đọc để băm ở trên.

## 6. Giới hạn

- Nhãn là ABP xâm lấn công khai của bệnh nhân phẫu thuật VitalDB, không phải cuff, không
  phải ΔBP qua phiên, không phải thiết bị của nhóm.
- Đây là BP tuyệt đối của người chưa thấy (calibration-free), khác bài toán chính của dự án.
- B5 học trên ít người hơn B0/B3 (288 so với 320), nhưng được chọn epoch trên 32 người còn
  lại, còn B3 có số cây cố định (mục 3). Vì vậy B5 − B0 và B5 − B3 là so sánh hai **quy
  trình** hoàn chỉnh, không phải so sánh kiến trúc có kiểm soát; không nói trước được chênh
  lệch dữ liệu này làm B5 thiệt hay lợi.
- Không tinh chỉnh siêu tham số. Learning rate theo bài; batch, chuẩn hóa và cách dừng
  chọn trước khi có số val.
- Kết luận chỉ cho val PulseDB.

## 7. Kiểm tra trên train (`--mode inner`, 2026-11-07)

**Mục đích:** kiểm mô hình có học được với learning rate của bài hay không, trước khi duyệt. Chỉ
dùng người của train; không có số nào trên val hay test.

**Lần chạy:** `runs/b5_pulsedb_inner/20261107T095840Z/` (ngoài Git).

- Config như mục 3, mã chưa commit, trên `a7e0ea1`; `report.json` có SHA-256 từng file mã.
- GPU RTX 4050 Laptop, PyTorch 2.6.0+cu124.
- SHA-256 `report.json` `7d280fbb…`, `model_sbp.pt` `f4d31082…`, `model_dbp.pt` `2d8677aa…`.
- Phần học: 288 người, 103 680 đoạn. Tập kiểm tra trong: 32 người, 11 520 đoạn. QC nhãn không
  loại dòng nào.

| Đầu ra | Epoch tốt nhất / đã chạy | MAE trung bình đều theo người trên tập kiểm tra trong | B0 (trung bình của phần học) trên cùng 32 người | Thời gian học |
| --- | --- | --- | --- | --- |
| SBP | 16 / 31 | 13,42 mmHg | 14,41 mmHg | 18,7 phút |
| DBP | 6 / 21 | 8,39 mmHg | 9,06 mmHg | 12,5 phút |

- Với learning rate 10⁻⁶ của bài, mô hình học được: sai số của phần học giảm đều, và MAE trên
  tập kiểm tra trong thấp hơn B0 khoảng 1,0 (SBP) và 0,7 (DBP) mmHg.
- MAE trên tập trong ngừng cải thiện sớm: epoch 16 với SBP, epoch 6 với DBP. Điều này giống
  nhận xét của bài rằng sai số calibration-free tăng sau khoảng 20 epoch.
- Các MAE này lạc quan, vì chính chúng được dùng để chọn epoch. Không so được với B0/B3 trên
  val.
- Không đổi điểm nào ở mục 3 sau lần chạy này.

## 8. Code và chạy

- Mô hình: `software/models/resnet1d.py`. Pipeline: `software/pulsedb/pipeline_b5.py`.
  Runner: `scripts/run_b5_pulsedb.py`. Config: `configs/models/b5_pulsedb_v0.json`.
- Kiểm trên train: `scripts/run_b5_pulsedb.py --raw <file .mat> --split-dir <thư mục split
  v2> --mode inner`, output `runs/b5_pulsedb_inner/<UTC>/`.
- Chạy chính sau khi duyệt: bỏ `--mode inner`, output `runs/b5_pulsedb/<UTC>/` gồm
  `b5_table.md`, `report.json`, `predictions_val.csv`, `history_sbp.csv`, `history_dbp.csv`,
  `model_sbp.pt`, `model_dbp.pt`, có SHA-256 trong report.

## 9. Review

**Review về rò rỉ và so sánh công bằng (2026-11-11, rà soát và một phản biện độc lập):**
không có lỗi chặn trên đường học và chấm. Đã kiểm: chuẩn hóa chỉ từ phần học; dự đoán ở chế
độ `eval`; checkpoint tốt nhất giữ cả trạng thái batch norm; dự đoán đổi lại mmHg; B0/B3/B5
được ghép theo `sample_id` và chấm trên cùng các lượt bootstrap theo người; tập kiểm tra trong
tách theo người, chỉ từ train. Các điểm đã xử lý:

1. Mục 5 trước đây nói quá: nhãn và dạng sóng của val/test vẫn được đọc để băm
   (`verify_inputs`) và để QC nhãn, dù không vào mô hình. Đã viết lại mục 5.
2. So sánh với B0/B3 là so sánh quy trình, không phải kiến trúc (mục 6, đã ghi rõ).
3. Trọng số của phần học trước đây được chuẩn hóa trên cả 320 người rồi mới cắt ra 288 người,
   nên khi số đoạn mỗi người khác nhau thì trung bình khác 1. Đã sửa: tính trên phần học
   (`pipeline_b5.py`), thêm test. Trên split v2 mỗi người 360 đoạn và QC không loại dòng nào,
   nên mọi trọng số vẫn bằng 1: lần chạy `inner` ở mục 7 không đổi.
4. Lần chạy `inner` ở mục 7 là bằng chứng phát triển, không phải bằng chứng hiệu năng độc lập:
   đã ghi ở mục 7, và không điểm nào của mục 3 đổi sau lần chạy đó.

**Duyệt:** ngày 2026-11-11, nguyên trạng, bằng commit riêng đổi `status` của config thành
`APPROVED_NOT_TEST_EVALUATED`, trước khi chạy chế độ `val`.
