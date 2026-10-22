# Báo cáo tiến độ Tuần 5 — phần Linh

> **Giai đoạn:** Tuần 5 / 28 tuần
>
> **Phụ trách:** Linh (phần mềm, dữ liệu/pipeline, baseline)
>
> **Ngày cập nhật:** 2026-10-22 (sửa theo review độc lập Tuần 5, tóm tắt ở mục 11)
>
> **Nhánh/commit nền:** `dev/ngoclinh`, fast-forward lên `origin/develop`
> `c23e2e0`; thay đổi **chưa commit** (chờ review). Làm trong git worktree cục bộ
> `tmp/linh_week05` để không đụng thay đổi chưa commit của Huy trên `dev/huy`.
>
> **Trạng thái:**
> - Việc 1 (B0/B3 trên raw): **chờ raw và `pool_decision`**.
> - Việc 3 (mô phỏng đủ trường) và Việc 2 (logger, decoder, replay offline): **có
>   đầu ra và test**.
> - Đọc serial trực tiếp: **chờ duyệt `pyserial`**. Chạy 10 phút với MCU: **chờ
>   firmware**.
> - Mọi kết quả trong báo cáo này là SYNTHETIC. Chưa có dữ liệu thiết bị hay dữ
>   liệu người.

## 1. Mục tiêu và phạm vi

Theo hàng "Linh" của [WEEK_05.md](../../../docs/plans/WEEK_05.md):

1. Đóng phần mềm G1: B0/B3 trên raw PulseDB thật, bàn giao cho Huy.
2. Logger phía máy tính qua USB serial theo Packet Schema V0.1.
3. Mô phỏng đủ trường với version schema mới.

Hoãn 1D CNN sang sau G2; không thêm MLflow. Không sửa `hardware/kicad/` hay code
của Huy. Trong tài liệu phần cứng, chỉ sửa Packet Schema V0.1 ở hai chỗ: mục 14.1
(mới) và một ghi chú ở cuối mục 15. Schema là tài liệu của Đức Anh, nên cần Đức
Anh review cả hai chỗ trong PR. Không commit/push/PR.

## 2. Nhật ký quyết định (ngày ghi là bằng chứng khóa trước khi xem dữ liệu)

| Ngày | Quyết định | Ai | Nơi ghi |
| --- | --- | --- | --- |
| 2026-10-21 | Version mô phỏng mới `synthetic-packet-v3` (module, config, fixture riêng). **v2 vẫn được hỗ trợ**, không đổi code/config/đáp án; v1 vẫn bị từ chối; không đổi tên version trên artifact cũ | Linh | `docs/protocol/packet_simulation.md` |
| 2026-10-21 | Quy tắc tạm R1–R5 của logger. R1: `0xC1` bỏ bước 4 và 6, vẫn kiểm `SEQ`/CRC. R2: bit 0/1/5 ở packet trước hoặc sau chỗ nhảy. R3: bit 1 giải thích nhảy index. R4: kiểm `VERSION` trước CRC, CRC16 little-endian, `SAMPLE_COUNT = 0` là vô lý. R5: dung sai 1 chu kỳ + 500 µs | Linh, **chờ Đức Anh** | `docs/protocol/packet_logger.md` |
| 2026-10-21 | Không thêm `pyserial`. Bàn giao decoder + replay offline + giao diện nguồn byte; serial trực tiếp ở trạng thái chờ. Đề xuất pin `pyserial==3.5` (cần nhóm xác nhận trên PyPI và cài thử trên Python 3.11 trước khi thêm; chưa kiểm trong tuần này) | Linh đề xuất, **chờ nhóm duyệt** | Mục 5.3 |
| — | `pool_decision` PulseDB | **Chưa quyết**, Linh + Huy (phương án ở mục 3.2) | — |
| 2026-10-22 | Sửa theo review: kiểm `T_ANCHOR_US` hai chiều; dung sai tốc độ ±3 %; cột `chain_id`, giữ `packet-logger-v0`; bảng 14.1 sửa theo code cho `FIRST_SAMPLE_INDEX` của `0xC1` | Dung sai tốc độ **chờ Đức Anh** (D10) | Mục 11, `docs/protocol/packet_logger.md` |

## 3. Việc 1 — B0/B3 trên raw PulseDB: **chờ raw và pool**

### 3.1. Đầu vào

Ngày 2026-10-21 tôi tìm `*.mat` trên ổ chứa repo và trong các thư mục người dùng
(Downloads/Documents/Desktop) của máy làm việc. **Không có file PulseDB nào**; chỉ
có `.mat` test của scipy trong `.venv` và một file MATLAB không liên quan. `data/raw/` không tồn tại. Không tự tải
dataset.

Vì vậy chưa tạo config split, chưa chạy `build_pulsedb_split.py` hay
`run_b3_pulsedb.py`, và **chưa có bảng B0/B3**. Không dùng CSV 1.000 đoạn lịch sử
để thay thế.

### 3.2. Phương án `pool_decision` (soạn để Linh và Huy chọn; chưa chọn)

Quan hệ người giữa các subset lấy theo bài báo PulseDB
([provenance](../../../docs/pulsedb_provenance.md) mục 5), **chưa kiểm bằng ID trên
raw**. Chưa có kết quả mô hình nào trên raw, nên lựa chọn này không thể dựa trên
kết quả.

| | A (nối tiếp lịch sử) | B (pool lớn) |
| --- | --- | --- |
| Pool chia train/val/test | `VitalDB_AAMI_Cal_Subset.mat` (nhóm C, 116 người, 70 212 đoạn theo output notebook) | `VitalDB_Train_Subset.mat` (nhóm A, 1 293 người) |
| Không dùng ở **bất kỳ** bước nào vì trùng người | `VitalDB_AAMI_Test_Subset.mat` (cùng 116 người) | `VitalDB_CalBased_Test_Subset.mat` (cùng người với Train) |
| Held-out ngoài, để dành tới khi model khóa | `VitalDB_CalFree_Test_Subset.mat` (nhóm B, 144 người) | `VitalDB_CalFree_Test_Subset.mat` (nhóm B). Nhóm C chỉ được dùng **một** file (AAMI Cal hoặc AAMI Test) |
| Không dùng trong G1 | Train và CalBased Test (nhóm A) | — |
| Số người theo split (seed 72, 0,8/0,1/0,1) | 92/11/13, theo công thức trong `run_pulsedb_split.md` | Chưa tính |
| Ưu | Có SHA-256 lịch sử (`bc68fc23…`); file nhỏ hơn; nối tiếp bằng chứng Tuần 2–4 | Nhiều người, CI hẹp hơn |
| Nhược | Val chỉ 11 người nên CI rộng | File lớn hơn nhiều; reader nạp cả file vào RAM; chưa có checksum |

Khi chọn cần ghi kèm: `license` và `permission_basis` (provenance mục 2 ghi CC
BY-NC-SA 4.0, nhưng cần người kiểm trang phân phối và ghi bằng chứng),
`source_version` (version gói Kaggle **chưa ghi**), `subject_identity_review`
(hậu tố `_1` của ID chưa kiểm trên toàn file, provenance mục 7). Tôi **không**
điền các trường này thay Linh/Huy.

### 3.3. Các bước khi có raw (theo `run_pulsedb_split.md`, `run_b3_pulsedb.md`)

1. Tính `Get-FileHash -Algorithm SHA256`, viết thường. Tạo
   `data/processed/linh_split_config.json` (ngoài Git) với đúng 12 trường.
2. Chạy `build_pulsedb_split.py` hai lần ra hai thư mục mới. So SHA-256
   `inventory.csv`/`manifest.csv`. Đối chiếu số dòng raw–reader–inventory và số
   người/đoạn mỗi split; không xem nhãn test.
3. Trên vài đoạn **train**, so max/min kênh 2 với SBP/DBP để kiểm thứ tự kênh
   (provenance mục 6). Chỉ ghi nhận; sửa reader thì bàn với Huy trước.
4. Chạy `run_b3_pulsedb.py` hai lần. `predictions_val.csv`, `xgboost_sbp.json`,
   `xgboost_dbp.json` và metrics phải giống từng byte.
5. Bàn giao Huy `runs/b3_pulsedb/<UTC>/` và thư mục split (ngoài Git; có ID).

**Ghi chú về "test không bị trích đặc trưng":** trong `report.json`, dòng "Test
rows not featurized…" là chuỗi cố định trong `validation_log`, không phải số đếm.
Bằng chứng là code (`software/pulsedb/pipeline.py` chỉ trích đặc trưng các dòng
train/val) và test SYNTHETIC trong `tests/test_b3_pipeline.py` (đổi waveform hoặc
nhãn test thì dự đoán không đổi). Đề xuất, **chưa làm**: ghi số dòng đã trích đặc
trưng theo split vào report.

### 3.4. Sai lệch của bản cũ

Bản cũ của pipeline đã chạy và báo MAE trên **test**: `docs/testing.md`,
`notebooks/metrics_all_splits.csv`, `notebooks/week4-train-xgboost.ipynb`, commit
`acc8b8b`. Các số đó không được trích ở đây và không được dùng để chọn model, đặc
trưng, ngưỡng hay pool. Kết quả B0/B3 sau này sẽ là BP tuyệt đối trên nhãn ABP
công khai của một subset PulseDB, không phải cuff, ΔBP cross-session hay thiết bị.

## 4. Việc 3 — mô phỏng đủ trường `synthetic-packet-v3`

- Code: `software/data_io/packet_simulation_v3.py`. Config:
  `configs/hardware/packet_simulation_v3.json` (seed `20261021`, `source_type`
  `SYNTHETIC`). Runner: `scripts/simulate_packets.py` (nhận config v3; nhánh v2
  giữ nguyên).
- Luồng byte đúng mục 6 của schema: `SYNC`, `VERSION` `0x01`, `CHANNEL_ID`
  (`0xE1`, `0xF1`, `0xF2`, `0xC1`), `SESSION_ID`, `SEQ`, `FIRST_SAMPLE_INDEX`,
  `T_ANCHOR_US`/`T_FIRST_US`, `FS_NOMINAL_MHZ` (mHz), `SAMPLE_COUNT` ≤ 32,
  `STATUS` (bit 4 bật), `DATA` int32, CRC-16/CCITT-FALSE. Little-endian, 42 + 4N
  byte. fs, N, độ trễ, jitter là **thông số mô phỏng**, không chốt fs phần cứng.
- 13 case: `valid`, `missing`, `duplicate`, `reordered`, `timestamp`,
  `timestamp_first` (anchor sai ở packet đầu; thêm 2026-10-22), `offset`,
  `crc`, `byte_loss`, `index_jump` (bit 0, `SEQ` liên tục), `reanchor` (bit 0+5),
  `version`, `session_restart`. Có packet sự kiện `0xC1`.
- Đáp án độc lập: `tests/fixtures/packet_v3_expected.json`, suy tay từ định nghĩa
  case. Packet ví dụ 50 byte ghép từng trường, CRC tính bằng `binascii.crc_hqx`
  (`0xFD43`). Known-answer `"123456789"` → `0x29B1`.

## 5. Việc 2 — logger phía máy tính

### 5.1. Đầu ra

- `software/data_io/packet_wire.py`: CRC, đóng gói, `StreamDecoder` theo luồng,
  dò `SYNC`; CRC sai hoặc header vô lý thì bỏ 1 byte và dò tiếp, không nhảy theo
  độ dài khai báo.
- `software/data_io/packet_receiver.py`: mục 12 theo từng phiên/kênh. Gồm mất,
  trùng, xung đột (cách ly), đảo thứ tự; mở rộng `SEQ`/`FIRST_SAMPLE_INDEX` qua
  2³²; index liên tục đối chiếu `STATUS`; `T_ANCHOR_US` tăng và khớp index/fs
  trong dung sai; đổi `SESSION_ID` thì là phiên mới; đếm `STATUS`; lệch kênh chỉ
  với SYNTHETIC.
- `scripts/packet_logger.py`:
  - `record` ghi raw bằng exclusive-create và ghi `t_rx` ra file riêng.
  - Decode trực tiếp, rồi decode lại từ raw trên đĩa; hai kết quả phải giống nhau.
  - `session_manifest.json` ghi sau cùng, có trường mục 11 và provenance.
  - `replay --expect` so hash với manifest.
- `configs/hardware/packet_logger.json` (`NOT_HARDWARE_VALIDATED`), hướng dẫn
  [packet_logger.md](../../../docs/protocol/packet_logger.md).
- Không nội suy, không ghép ECG–PPG theo index, không dịch kênh. Offset kênh
  không phải PAT.

### 5.2. Đối chiếu Definition of Done (SYNTHETIC)

| Tiêu chí | Kết quả |
| --- | --- |
| Nhận đúng gói hợp lệ | `valid`: 26/26 packet, 0 issue |
| Mất / trùng / đảo thứ tự | `missing_packets` 1 / `duplicate` 1 / `out_of_order` 1; mẫu của `duplicate`/`reordered` giống hệt `valid` |
| Timestamp bất thường | `timestamp_anomaly` 1, packet bị cách ly. Anchor đầu chuỗi sai (`timestamp_first`): chỉ packet đó bị cách ly (2026-10-22; trước khi sửa thì 7/8 packet đúng bị cách ly) |
| Lệch kênh | `channel_offset` 1 (+19 862,875 µs so với 20 000 µs chèn vào; chênh trong giới hạn jitter). Không báo cho `DEVICE` |
| Lỗi CRC, mất byte giữa luồng | `crc_mismatch` 1 + `skipped_bytes` 1 + `missing_packets` 1; bắt lại `SYNC` ở packet kế tiếp |
| Index nhảy kèm STATUS, version lạ, đổi phiên | `sample_gap_status` 1, `sample_index_reanchored` 1, `unsupported_version` 1, `session_change` 1 |
| Không ghi đè raw; mỗi session có hash | Test `FileExistsError`; manifest có SHA-256 raw và mọi output |
| Replay offline cho cùng kết quả | 12/12 case (2026-10-21); 13/13 case sau khi sửa (2026-10-22): `replay --expect` exit 0, không lệch hash |

### 5.3. Chưa đạt

- **Serial trực tiếp:** chờ nhóm duyệt `pyserial` (đề xuất `pyserial==3.5`).
  `record` đã nhận object `read(n)`; còn thiếu điều kiện dừng theo thời lượng.
- **10 phút với MCU thật:** `origin/dev/ducanh` (mới nhất `1e95d29`, 2026-10-21)
  chưa có firmware; `firmware/` chỉ có `README.md` và `.gitkeep`. Chờ Đức Anh.
- **Đức Anh review logger:** danh sách kiểm ở cuối `packet_logger.md`.

## 6. Lệnh đã chạy và kết quả

Chạy trong `tmp/linh_week05` bằng Python của venv repo (`.venv`, Python 3.13.12),
ngày 2026-10-21 và chạy lại ngày 2026-10-22 sau khi sửa theo review:

| Lệnh | Kết quả |
| --- | --- |
| `python -B -m pytest -q -p no:cacheprovider` (trước khi sửa) | 329 passed, exit 0 |
| `python -B -m pytest -q -p no:cacheprovider` (sau khi sửa) | **376 passed**, exit 0 (47 test mới trong `test_packet_logger.py`; `test_packet_simulation.py` v2 không đổi, vẫn đạt) |
| Như trên, sau khi sửa theo review (2026-10-22) | **416 passed**, exit 0 (thêm 40 test, mục 11) |
| `python -m ruff check .` | exit 0 (cả hai lần) |
| `python -m ruff check --select E501` trên 5 file mới | exit 0 (≤ 88 ký tự) |
| `python -m ruff check --preview --select E501,E225 scripts/simulate_packets.py scripts/packet_logger.py` (2026-10-22) | Không còn dòng mới nào vi phạm. Còn 7 dòng E501 có sẵn ở `HEAD` (`c23e2e0`), không sửa |
| `python scripts/check_environment.py` | **exit 1**: lệch pin đã biết (Python 3.13.12 so với `<3.12`; numpy 2.5.3, pandas 3.0.6, scipy 1.18.1, matplotlib 3.11.2, pytest 9.1.1, scikit-learn 1.9.1, PyYAML 6.0.3). Không sửa pin. Lần chạy 2026-10-22 cho cùng kết quả |
| `python -m pip check` | exit 0 (cả hai lần) |
| `git diff --check` | exit 0 (cả hai lần) |
| Mutation (vá lúc chạy, không sửa file): bỏ bit giải thích, bỏ bit 5, bỏ mở rộng 2³², nới `SAMPLE_COUNT` lên 64, tắt kiểm thời gian, tắt offset, CRC init 0 | 7/7 mutant bị test bắt (1–2 test fail mỗi mutant) |
| Mutation của review độc lập (2026-10-22, trên bản sao) | Trước khi sửa: **7 mutant khác sống**, gồm M8a (`"xb"` → `"wb"`), M12 (`T_FIRST_US` lệch 1 mẫu), M13 (tin kênh lạ trước CRC), M14 (bỏ kiểm dải dữ liệu), M15 (bỏ kiểm bit STATUS dự trữ), M16 (đếm mất sai 1), M17 (manifest không ghi sau cùng). Sau khi sửa: cả 7 đều bị test bắt. Trên tổng 33 mutant (22 mutant cũ của review, M11/M19 viết lại theo dòng code mới, 9 mutant mới cho phần sửa), test bắt được 33/33 |

Máy không có Python 3.11, nên các kết quả trên **chưa thay cho CI** Python 3.11
trên PR.

**Chạy end-to-end bằng CLI** (output ngoài Git trong
`tmp/linh_week05/runs/week05_linh/`; code chưa commit nên manifest ghi
`workspace_has_changes: true`, commit nền `c23e2e0`). Ngày 2026-10-22 chạy lại
13 case với code đã sửa, output trong `tmp/linh_week05/runs/week05_review_fix/`.
`stream.bin` và `issue_counts` của 12 case cũ không đổi. `decode.json`,
`packets.csv` và `samples.csv` có đổi (cột `chain_id`, trường
`sync_candidates_rejected`), nên `replay --expect` code mới trên các manifest cũ
trong `runs/week05_linh/` sẽ báo lệch hash ba file đó. Với mỗi case:

1. `simulate_packets.py --config configs/hardware/packet_simulation_v3.json
   --case <case>` chạy hai lần → cùng SHA-256 `stream.bin`.
2. `packet_logger.py record` → exit 0, SHA-256 `raw.bin` = `stream.bin`.
3. `packet_logger.py replay --expect` → exit 0, không lệch hash.

| Case | SHA-256 `stream.bin` = `raw.bin` | `issue_counts` |
| --- | --- | --- |
| valid | `09f380599a5e8f88d00fa1803490e104b56481270a0867da5267e58cf9823f54` | {} |
| missing | `5439a2dbeea0c0be7636c1690cbd06e12c31b78351a8bcb18b6fd928ae3ca663` | missing_packets 1 |
| duplicate | `be591e780d8f132b3014531bd46cdac8c7988fba361febe831d0c442354c2051` | duplicate 1 |
| reordered | `2ffd4896752e15e5af85841502d3d39275eb46b0e74ec9a27010abaf7ccb8254` | out_of_order 1 |
| timestamp | `f5856e85f2e5e7df10460ba8c070d5c924b0b8af0dd3ec71e5bd22792ba6efcd` | timestamp_anomaly 1 |
| timestamp_first (thêm 2026-10-22) | `4a5b11b1bce5a7af680db4a5f7d698f59dd9500bbbaf56e40c4ce73dee8876d7` | timestamp_anomaly 1 |
| offset | `2cb8dcba5cc8425e4a8a6562a270009b1870921449574178816ac9cd0b073125` | channel_offset 1 |
| crc | `aa87de6b2197e7e627867ce6006b6f181b8741b50d33ca058f9ff97a4946d137` | crc_mismatch 1, missing_packets 1, skipped_bytes 1 |
| byte_loss | `71734ceb701df703cacb92e874a2730e1baa359ee1a99a396b5d1db439e2ef2a` | crc_mismatch 1, missing_packets 1, skipped_bytes 1 |
| index_jump | `b9cab131ddd4913975b9395c68cf6a381ae07010cfa327223c42b96350bbfeaf` | sample_gap_status 1 |
| reanchor | `d3457c0c821dda3904bdafea2dd9041a7bf1bf433cd501620fa44b7f36efcf12` | sample_index_reanchored 1 |
| version | `d8ebf85a40835bba441b2fe392b75c017cc03fcff76c960dea03c8428ee3a108` | missing_packets 1, skipped_bytes 1, unsupported_version 1 |
| session_restart | `0effae0cbf1dc169c306fe8e5f7beba8511ab3f7397eeb254ab638c849c6be37` | session_change 1 |

## 7. Review chéo

### 7.1. Code mốc Tuần 5 của Huy (chưa commit trên `dev/huy`)

Review chỉ đọc, 2026-10-21. Phát hiện 3 tôi kiểm lại bằng cách đọc
`pair_pat`/`pat_beats`. Các phát hiện còn lại được tái hiện bằng script thăm dò
và mutation lúc chạy, không sửa file repo. Pytest `test_week05_fiducials.py`: 26
passed; toàn repo trên `dev/huy`: 355 passed.

| Mức | Vị trí | Phát hiện | Đề xuất |
| --- | --- | --- | --- |
| Trung bình | `fiducials.py` (`valley_min`/`d2_max`, nội suy parabol) | Góc nhọn bất đối xứng vẫn là cực tiểu chặt nên vẫn bị nội suy, làm sai số tăng: `valley_min` MAE 6,28 ms so với 3,56 ms khi không nội suy (PPG 125 Hz). Doc ghi "góc nhọn không nội suy". Bỏ hoặc đổi dấu `_vertex_offset`, 26 test vẫn đạt | Chỉ nội suy khi gần đối xứng (hoặc bỏ); thêm test dưới mẫu ≤ 0,25 mẫu |
| Trung bình | `fiducials.py` (`derivative_energy`) | Ngưỡng 0,2·ptp trên năng lượng bình phương: một spike 1 mẫu 0,8×R ở 500 Hz làm mất 0/9 R (`prominence` vẫn 9/9) | Ngưỡng robust (percentile/median); ghi giới hạn |
| Trung bình | `pat_validity.py` (`pat_beats`) | `pair_pat` đã lọc theo [`pat_min_s`, `pat_max_s`] = 80–400 ms, nên nhãn `out_of_range` không bao giờ xuất hiện; PAT 450 ms thành `unpaired_r`, trái nguyên tắc "gắn nhãn, không xóa" | Ghép trong cửa sổ rộng rồi để `classify_pat` gắn nhãn, hoặc kiểm hai bộ giới hạn bằng nhau |
| Trung bình | `configs/data/week05_huy.json` (`refractory_s` 0,25) | Refractory áp cho cả đỉnh PPG: PPG có sóng tâm trương, HR 75 → 21 foot thay vì 11. SYNTHETIC không có sóng tâm trương nên không thấy | Refractory riêng cho PPG (ví dụ 0,4 s) |
| Trung bình | `scripts/week05_fiducials.py` | `synth`/`detect` không ghi provenance; `compare` thiếu `source_type`, phiên bản thư viện, hash config đã dùng để detect | Ghi `detect.json` có config, SHA `records.csv`, git, thư viện; `compare` kiểm nó |
| Thấp | `scripts/week05_fiducials.py` (`annotate`) | Chỉ kiểm `--out` tồn tại ở cuối buổi: có thể mất cả buổi đánh dấu tay | Mở `"x"` từ đầu, ghi theo từng bản ghi |
| Thấp | `tests/test_week05_fiducials.py` | `MAD_SCALE` = 0 hoặc 1 vẫn đạt (sàn 10 ms luôn quyết định); không có test R ở 125 Hz, biên dung sai, `annotate` | Thêm test |
| Thấp | `fiducial_agreement.py` | Vùng review bất đối xứng (mốc tay 4,49 s trong vùng, detection 4,51 s ngoài vùng → FN); biên float (1,05 − 1,0 > 0,05); ghép greedy không tối ưu khi hai mốc cách nhau < 2·dung sai | Nới vùng theo dung sai; so biên có epsilon |

Điểm tốt: output mặc định `features-sqi-v1` không đổi (400 tín hiệu ngẫu nhiên ở
125/250/500/512 Hz trùng HEAD). `extract_window` từ chối phương pháp không mặc
định. `classify_pat` không dùng BP. Gọi là PAT, không PTT. `select_review_rows`,
`load_records`, `agreement` đều chặn split test. `compare` từ chối đáp án
SYNTHETIC khi không có cờ. Ghi file dùng `"x"`.

### 7.2. Đức Anh

- Firmware khung, log ERC/DRC: **chưa có** trên `origin/dev/ducanh`; chờ.
- `configs/hardware/Pin_Map_V1.md` (`9073aa8`, bản Draft), góp ý về giao diện:
  1. Không có INT2B/`SAMP`, trong khi KiCad V1-module nối INT2B vào GPIO47 (schema
     mục 5.2, `custom_board_proposal.md` A.7). Cần chốt một pin map (A.6).
  2. Ghi PPG là MAX30102, nhưng WEEK_05 mua SparkFun MAX30101. Ánh xạ khe
     `0xF1`–`0xF4` và LED xanh phụ thuộc chip nào được dùng.
  3. BMI270 có trong pin map, nhưng schema mục 7 **không có `CHANNEL_ID` cho
     IMU**. Gửi IMU thì logger báo `unknown_channel`; cần mã kênh mới và tăng
     version schema.
  4. MAX30001 và BMI270 chung bus SPI: giao dịch IMU có thể chen vào burst FIFO
     ECG, nên giới hạn `d_word_us` ở mục 5.2 cần đo lại.
  5. Chưa có GPIO cho nút `t0` (packet `0xC1`) và cho xung kích thích của kế hoạch
     đo 10 phút. Chưa ghi cổng USB nào (UART bridge hay native USB) mang packet,
     và log debug đi đâu (schema mục 13).

## 8. Câu hỏi

**Cho Đức Anh:** D1–D10 trong [packet_logger.md](../../../docs/protocol/packet_logger.md):

- byte order CRC16;
- `VERSION` khác `0x01`;
- packet nào mang bit 0/5, `SEQ` gán trước hay sau bộ đệm MCU;
- khi nào bật/tắt bit 4;
- `SEQ`/index có bắt đầu từ 0 mỗi phiên không;
- giá trị các trường của `0xC1`;
- `SAMPLE_COUNT = 0`;
- `d_ptr_us`/`d_word_us`;
- cổng USB và log debug;
- (thêm 2026-10-22) tốc độ mẫu thật lệch bao nhiêu so với danh định, để thay giả
  định ±3 % của dung sai tốc độ.

Cùng với các điểm pin map ở 7.2.

**Cho Huy:**

- Chọn phương án `pool_decision` (3.2) cùng Linh.
- Ai kiểm và ghi `license`/`permission_basis`/`source_version`?
- Xem phát hiện review 7.1 trước khi dùng mốc Tuần 5 trong pipeline.

**Cho nhóm:** duyệt `pyserial==3.5` hay không.

## 9. Phần chưa đạt và chuyển tiếp

| Việc | Người xử lý | Chuyển sang | Điều kiện |
| --- | --- | --- | --- |
| Bảng B0/B3 val từ raw, chạy lại, bàn giao Huy | Linh (pool: Linh + Huy) | Tuần 6 | Raw `.mat` được phép dùng, `pool_decision` và các trường quyền dùng đã ghi |
| Logger đọc serial trực tiếp | Linh | Tuần 6 | Nhóm duyệt `pyserial` |
| Logger 10 phút với MCU thật | Linh + Đức Anh | Tuần 6 | Firmware khung gửi packet V0.1 |
| Đức Anh review logger; trả lời D1–D10 | Đức Anh | Tuần 6 | — |
| Review firmware khung, ERC/DRC | Linh | Khi Đức Anh bàn giao | — |
| CI Python 3.11 trên PR | Linh | Khi được yêu cầu mở PR | — |

## 10. File đầu ra

| Sản phẩm | Đường dẫn |
| --- | --- |
| Báo cáo này | `reports/weekly/week_05/linh.md` |
| Codec byte V0.1, decoder | `software/data_io/packet_wire.py` |
| Kiểm tra mục 12, metadata phiên | `software/data_io/packet_receiver.py` |
| Generator `synthetic-packet-v3` | `software/data_io/packet_simulation_v3.py`, `configs/hardware/packet_simulation_v3.json` |
| Runner logger | `scripts/packet_logger.py`, `configs/hardware/packet_logger.json` |
| Runner mô phỏng (thêm v3) | `scripts/simulate_packets.py` |
| Test và đáp án | `tests/test_packet_logger.py`, `tests/fixtures/packet_v3_expected.json` |
| Hướng dẫn | `docs/protocol/packet_logger.md`, `docs/protocol/packet_simulation.md` (mục v3), `docs/protocol/README.md` |
| Bảng đối chiếu schema | `configs/hardware/Packet_Schema_V0.1.md` mục 14.1 và một ghi chú ở mục 15 |
| Danh mục | `software/README.md`, `scripts/README.md`, `tests/README.md` |

## 11. Sửa theo review độc lập Tuần 5 (2026-10-22)

**Nguồn:** review độc lập (`tmp/review_week05/review.md`) và danh sách sửa
(`tmp/review_week05/linh_fix_list.md`), cả hai ngoài Git. Chưa commit, chưa push,
chưa mở PR.

### 11.1. Quyết định (chốt 2026-10-22)

| Mục | Quyết định | Lý do / ảnh hưởng |
| --- | --- | --- |
| A3 | Kiểm `T_ANCHOR_US` **xuôi và ngược** theo từng chuỗi. Giữ chiều cách ly ít packet hơn; bằng nhau thì giữ chiều xuôi | Không chọn "so hàng xóm", vì cách đó không báo bước nhảy kéo dài hay 2 packet sai liền nhau. Không thêm ngưỡng. Bước nhảy kéo dài nay cách ly **phía ngắn hơn**, trước đây là mọi packet phía sau |
| A4 | Thêm `anchor_rate_tolerance_ppm` = 30 000 (±3 %), áp cho mọi kênh | Nguồn: clock ADC MAX30101 10,2–10,8 MHz (schema mục 4). Giả định tốc độ mẫu tỉ lệ với clock và danh định ở giữa dải; **chưa đo**. Câu hỏi D10 |
| A5 | Thêm `chain_id` vào `packets.csv`, `samples.csv`; giữ `packet-logger-v0` | Code chưa từng commit, nên chưa có artifact chính thức dùng v0. Hash output khác lần chạy 2026-10-21 |
| A6 | Tài liệu theo code: bảng 14.1 ghi `FIRST_SAMPLE_INDEX` của `0xC1` là thứ tự sự kiện | `stream.bin` và fixture không đổi. D6 vẫn chờ Đức Anh |
| A1 | Chưa commit | Chờ review |
| A7, A8 | Không đổi | Chờ raw `.mat` / nhóm duyệt `pyserial` |

### 11.2. Thay đổi và test

| Mục | Thay đổi | Test mới (`tests/test_packet_logger.py`) |
| --- | --- | --- |
| B1 | Kiểm hai chiều (A3). Offset kênh tính từ packet được nhận đầu tiên. Generator có case `timestamp_first`; fixture thêm đáp án | Anchor đầu ±20 ms ở ECG và PPG, anchor cuối +20 ms: đúng 1 packet bị cách ly. Bước nhảy kéo dài từ SEQ 5 và SEQ 3. Case `timestamp_first` |
| B2 | Dung sai cộng thêm `anchor_rate_tolerance_ppm`·10⁻⁶·\|Δk\|·T; `validate_config` kiểm trường mới; bỏ câu "drift cỡ ppm" | Tốc độ −3/+1/+3 % × mất 10/50 packet: không cách ly packet đúng. Anchor ±20 ms ngay sau khoảng mất vẫn bị bắt, và chỉ packet đó |
| B3 | `chain_id` tăng khi neo lại hoặc đổi FS; phiên mới bắt đầu từ 0; `samples.csv` sắp theo (phiên, kênh, `chain_id`, index); tóm tắt kênh có `chains` | Neo lại lùi: khóa duy nhất, hai chuỗi không xen kẽ, index tăng trong từng chuỗi |
| C1 | Packet `FS_NOMINAL_MHZ = 0` bị cách ly (`fs_invalid`), không cắt chuỗi, không sinh `fs_changed`; hết `ZeroDivisionError` | ECG toàn FS 0 (SYNTHETIC): không lỗi, 8 packet bị cách ly, offset `null` kèm lý do. Một packet PPG FS 0 |
| C2 | Mỗi packet hỏng là một lỗi; ứng viên `SYNC` bên trong đếm ở `decode.sync_candidates_rejected` | Packet hỏng chứa 3 `SYNC` giả: `crc_mismatch` 1, rejected 3, chunk 1 và 4096 |
| C3 | Bảng 14.1 của schema (A6) | — |
| C4 | `sample_index_inconsistent` khi số mẫu mất > 32 × số packet vắng mà không có bit 0/1 | Mất 1 packet, index nhảy 316: báo; có bit 0: không báo |
| C5 | Byte `0xA5` lẻ ở cuối là `truncated_packet`; đuôi cụt nhiều `SYNC` chỉ một lỗi | Hai ca, chunk 1 và 4096 |
| C6 | Ngắt dòng dài, sửa `code =(`, `started =datetime` | `ruff` (mục 6) |
| C7 | Sửa câu ở mục 1 | — |
| D | Test cho M8a, M12–M17; ca M3 mạnh hơn (độ dài khai báo phủ packet thật) | Mutation: 33/33 bị bắt (mục 6) |

**Probe đối kháng của review** (`adv.py`, `adv2.py`, chạy lại trên code đã sửa):

- x1, x1b: 7/8 packet được nhận.
- x2: mọi ô của lưới drift 0–3 % × mất 5–50 packet giữ đủ packet.
- x3, x15: không còn `ZeroDivisionError`.
- x14: 112/112 khóa duy nhất.
- x16: có `sample_index_inconsistent`.
- x17: `crc_mismatch` 1 và không còn `unsupported_version` 3.
- `b_truncated_tail`: đạt.
- x4 (bước nhảy từ packet 4 của 10): nay cách ly 4 packet trước bước nhảy, thay
  vì 6 packet sau.
- `d_seq_and_index_wrap` và x14 đọc tuple mẫu theo vị trí cũ, nên chỉ đạt khi đổi
  vị trí cột theo `chain_id` mới.
- x6 (kênh có trong metadata nhưng không có packet) vẫn không có issue. Ca này
  không nằm trong danh sách sửa.

**Chưa làm, vẫn bị chặn:** B0/B3 trên raw (G1), serial trực tiếp (G2) và logger 10
phút với MCU (G3) như mục 9.
