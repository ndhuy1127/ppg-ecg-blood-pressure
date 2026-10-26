# Báo cáo tiến độ Tuần 3

> **Giai đoạn:** Tuần 3 / 28 tuần (2026-10-01 → 2026-10-10)
>
> **Thành viên:** Linh, Trương Đức Anh, Nguyễn Đức Huy

## 1. Tóm tắt công việc của tuần (mục tiêu)

Theo [kế hoạch Tuần 3](../../../docs/plans/WEEK_03.md):

1. Chia PulseDB train/validation/test theo người, có manifest, seed và kiểm thử
   chống rò rỉ.
2. Hoàn thiện quy ước timestamp/packet; generator/replay kiểm thử đồng bộ ECG–PPG
   bằng dữ liệu giả lập; kế hoạch đo 10 phút.
3. Baseline B0 (trung bình train) và B1 (trung bình hiệu chuẩn từng người); chỉ số
   MAE/bias/SD riêng SBP/DBP.
4. Bàn giao code, config, test để chuẩn bị pipeline baseline Tuần 4.

## 2. Thành viên phụ trách và phân công công việc

| Thành viên | Công việc Tuần 3 |
| --- | --- |
| Linh | Split PulseDB theo người, manifest có hash, notebook kiểm tra split |
| Đức Anh | Làm rõ packet schema (bảng metadata), đặc tả generator/replay, schematic V1, BOM V1 |
| Huy | B0/B1, validation dùng chung, metrics, test và demo; runner B0 trên CSV PulseDB; hỗ trợ split v2 có inventory và generator/replay packet v2 |

## 3. Tóm tắt công việc đã hoàn thành của từng người

### Linh

- Notebook `week3-split-hash.ipynb`: chia 1.000 đoạn PulseDB theo `subject_id`
  với seed 72, tính hash từng mẫu.
- Manifest 1.000 đoạn (`pulsedb_manifest_1000.csv`) gồm ID mẫu/người, split và hash.

### Đức Anh

- Bảng metadata packet schema V0.1 (Word) làm rõ từng trường.
- Đặc tả generator/replay: config + seed, sáu kịch bản (hợp lệ, mất gói, trùng gói,
  đảo thứ tự, timestamp bất thường, lệch ECG–PPG 20 ms).
- Vẽ schematic V1 (Altium `V1.SchDoc`), lập BOM V1 thay BOM V0.1 kèm pin map.

### Huy

- **B0** `PopulationMeanBaseline`: trung bình SBP/DBP từ nhãn train; predict không
  nhận nhãn đánh giá.
- **B1** `PersonalMeanBaseline`: trung bình hiệu chuẩn từng người; báo lỗi
  `UncalibratedSubjectError` khi người chưa hiệu chuẩn, không fallback sang B0.
- **Validation dùng chung** `_bp_validation.py`: từ chối input rỗng, sai shape,
  bool, NaN/Inf, ID lỗi và overflow; không tự bỏ mẫu.
- **Metrics** `evaluate_bp`: MAE/bias/SD riêng SBP/DBP, tổng hợp theo mẫu, theo
  người và trung bình đều theo người.
- Test có đáp án tính tay, demo SYNTHETIC seed cố định, tài liệu API/công thức.
- **Runner B0 trên CSV PulseDB** của Linh: dùng nhãn train/val, không đọc nhãn
  test; cấu hình mặc định kiểm SHA-256 của CSV; ghi JSON kết quả kèm provenance.
- **Hỗ trợ phần Linh:** pipeline split `pulsedb-split-v2` có inventory, hash
  waveform độc lập ID/nhãn, kiểm tra bảo toàn mẫu và rò rỉ giữa các split.
- **Hỗ trợ phần Đức Anh:** generator/replay `synthetic-packet-v2` theo đặc tả của
  Đức Anh, sáu case lỗi, có seed/hash/commit truy vết.
- Runner B0 từ chối `waveform_hash` trùng giữa các split.

## 4. Danh mục sản phẩm đầu ra và đường dẫn

| STT | Sản phẩm | Người làm | Đường dẫn |
| --- | --- | --- | --- |
| 1 | Notebook split + hash | Linh | [week3-split-hash.ipynb](../../../notebooks/week3-split-hash.ipynb) |
| 2 | Manifest 1.000 đoạn | Linh | `notebooks/pulsedb_manifest_1000.csv` (gỡ khỏi Git ngày 2026-10-24; còn ở commit `1f218eb`) |
| 3 | Bảng metadata packet schema | Đức Anh | [Packet_Schema_V0.1_Metadata_Table.docx](https://github.com/ndhuy1127/ppg-ecg-blood-pressure/blob/4d4380f4328be23ab1ff391e475fec7570cdbed3/configs/hardware/Packet_Schema_V0.1_Metadata_Table.docx) (nhánh `dev/ducanh`, commit `4d4380f`); bản hiện hành: [Packet_Schema_V0.1.md](../../../configs/hardware/Packet_Schema_V0.1.md) mục 6, 11 |
| 4 | Đặc tả generator/replay | Đức Anh | [packet_generator_replay.md](https://github.com/ndhuy1127/ppg-ecg-blood-pressure/blob/bbd2d3c5ece7603615f5c9faa3dff290c5b4117d/configs/hardware/packet_generator_replay.md) (nhánh `dev/ducanh`, commit `bbd2d3c`); phần cài đặt ở dòng 15 |
| 5 | Schematic V1 | Đức Anh | [V1.SchDoc](https://github.com/ndhuy1127/ppg-ecg-blood-pressure/blob/ac9d21b52aa1d822723a52234c74103b8ff27d3b/hardware/schematics/V1.SchDoc) (Altium; nhánh `dev/ducanh`, commit `ac9d21b`); bản hiện hành: [KiCad V1-module](../../../hardware/kicad/v1_module/) |
| 6 | BOM V1 | Đức Anh | [BOM_V1.xlsx](https://github.com/ndhuy1127/ppg-ecg-blood-pressure/blob/40ede49172a475230d9f6ef236e297e2cdaff405/hardware/bom/BOM_V1.xlsx) (nhánh `dev/ducanh`, commit `40ede49`); bản hiện hành: [danh sách mua](../../../hardware/bom/purchase_list_v1_module.md) |
| 7 | B0/B1 | Huy | [constant_baselines.py](../../../software/models/constant_baselines.py) |
| 8 | Metrics MAE/bias/SD | Huy | [bp_metrics.py](../../../software/evaluation/bp_metrics.py) |
| 9 | Validation dùng chung | Huy | [_bp_validation.py](../../../software/_bp_validation.py) |
| 10 | Test baseline và metrics | Huy | [test_week_03_baselines.py](../../../tests/test_week_03_baselines.py), [test_bp_metrics.py](../../../tests/test_bp_metrics.py) |
| 11 | Demo SYNTHETIC | Huy | [demo_week_03_baselines.py](../../../scripts/demo_week_03_baselines.py) |
| 12 | Quy ước B0/B1 và metrics | Huy | [week_03_baselines_metrics.md](../../../docs/protocol/week_03_baselines_metrics.md) |
| 13 | Runner B0 trên CSV PulseDB | Huy | [run_b0_pulsedb_csv.py](../../../scripts/run_b0_pulsedb_csv.py), [b0_pulsedb_validation.json](../../../configs/data/b0_pulsedb_validation.json), [test_b0_pulsedb_csv.py](../../../tests/test_b0_pulsedb_csv.py), [hướng dẫn](../../../docs/protocol/run_b0_pulsedb_csv.md) |
| 14 | Split v2 có inventory | Huy (hỗ trợ Linh) | [split_manifest.py](../../../software/data_io/split_manifest.py), [build_pulsedb_split.py](../../../scripts/build_pulsedb_split.py), [test_split_manifest.py](../../../tests/test_split_manifest.py), [hướng dẫn](../../../docs/protocol/run_pulsedb_split.md) |
| 15 | Generator/replay packet v2 | Huy (hỗ trợ Đức Anh) | [packet_simulation.py](../../../software/data_io/packet_simulation.py), [simulate_packets.py](../../../scripts/simulate_packets.py), [packet_simulation.json](../../../configs/hardware/packet_simulation.json), [test_packet_simulation.py](../../../tests/test_packet_simulation.py), [hướng dẫn](../../../docs/protocol/packet_simulation.md) |

## 5. Tóm tắt các nội dung chuyên môn chính

### 5.1. Split theo người và chống rò rỉ (Linh, Huy)

- Chia theo `subject_id` với seed 72, tỷ lệ 0,8/0,1/0,1.
- `pulsedb-split-v2`: inventory giữ mọi dòng reader với
  `sample_id = <source_sha256>:<raw_index>`, `sample_hash`, `waveform_hash`.
- Validator từ chối mẫu thiếu/thừa/bị sửa và rò rỉ giữa split theo người, hash mẫu,
  hash waveform, record hoặc cửa sổ.

### 5.2. Packet và mô phỏng (Đức Anh, Huy)

- Sáu kịch bản: hợp lệ, mất gói, trùng gói, đảo thứ tự, timestamp bất thường, lệch
  hai kênh có chủ đích (t_PPG = t_ECG + 20 ms).
- Receiver phải định lượng được độ lệch giữa hai kênh, không giả định hai kênh cùng
  timestamp. Generator giữ gap và thời gian phân số chính xác.
- Fs dùng trong mô phỏng là thông số mô phỏng, chưa phải thông số phần cứng.

### 5.3. Baseline và chỉ số đánh giá (Huy)

- BP dạng `[SBP, DBP]`, tuyệt đối, mmHg; `error = prediction − reference`.
- SD mẫu `ddof=1`, trả `None` khi n = 1.
- `sample_weighted` mô tả mọi dòng; `by_subject` từng người; `subject_balanced`
  trung bình đều MAE/bias theo người (chỉ số chính). Không lấy trung bình SD từng
  người làm SD chung.
- B1 thuộc kịch bản cá nhân hóa có hiệu chuẩn, không phải người mới.
- Beta, Pearson ΔBP, Bland–Altman và coverage được đặc tả công thức, chưa cài.
- B0 trên CSV PulseDB chỉ mô tả nhãn ABP công khai, không phải cuff hay ΔBP.

## 6. Kết quả kiểm tra kỹ thuật

Python 3.13.12, NumPy 2.5.3, chạy bằng `.venv`:

| Ngày | Kiểm tra | Kết quả |
| --- | --- | --- |
| 2026-10-03 | `pytest -q tests/test_week_03_baselines.py tests/test_bp_metrics.py` | 67 passed |
| 2026-10-03 | `pytest -q` toàn repo | 74 passed |
| 2026-10-03 | `python -m scripts.demo_week_03_baselines` | Exit 0, in JSON `SYNTHETIC` |
| 2026-10-05 | Chạy demo trực tiếp từ `scripts/` | Exit 0, kết quả khớp `run_demo()` |
| 2026-10-08 | `pytest -q -p no:cacheprovider` | 75 passed |
| 2026-10-08 | `python scripts/run_b0_pulsedb_csv.py` (không đối số) | Exit 0, ghi `runs/b0_pulsedb/<UTC>/metrics.json`; ba lần chạy cho cùng kết quả |
| 2026-10-09 | `pytest -q` toàn repo | 91 passed |
| 2026-10-10 | `pytest -q` sau khi thêm split v2 và packet v2 | **199 passed in 2.08s** |
| Mọi lần | `ruff check .`, `git diff --check`, `pip check` | Đạt |

Test đã bao phủ: hằng số B0/B1 đúng, thứ tự dự đoán, thay nhãn đánh giá chỉ đổi
metrics, B1 không fallback, input lỗi, predict trước fit, fit lỗi giữ state; metrics
khớp đáp án tính tay (SBP `[-2, 0, 2]`, DBP `[1, -1, 3]`); split v2 từ chối rò rỉ;
generator v2 đủ sáu case với đáp án trong `tests/fixtures/packet_simulation_expected.json`.
