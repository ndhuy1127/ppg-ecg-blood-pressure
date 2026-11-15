# Changelog

Ghi các thay đổi đã vào `develop`, nhóm theo tuần của lộ trình; commit chỉ mới có trên
`dev/huy` được ghi rõ. Nguồn: lịch sử Git (PR #1–#25, ba commit đẩy thẳng ngày 2026-10-28,
từ Tuần 7 là commit trực tiếp) và báo cáo tuần trong `reports/weekly/`. Ngày là ngày merge
PR, hoặc ngày commit với commit không qua PR.
Changelog không ghi kết quả hiệu năng; test và demo trên dữ liệu SYNTHETIC chỉ
kiểm tra code. Ngày tính theo giờ Việt Nam (UTC+7).

## Tuần 8 (commit trực tiếp, 2026-11-13 → 2026-11-14)

Chi tiết: [báo cáo Tuần 8](reports/weekly/week_08/README.md).

- `0df0ba6` (2026-11-13): kế hoạch Tuần 8.
- `8eb833a` (2026-11-13): chuẩn bị bring-up (checklist, mẫu báo cáo, metadata env khung),
  đo RAM logger trên laptop dùng cho buổi đo, quy tắc `source_type` (DEVICE khi byte đến từ
  MCU thật, SYNTHETIC chỉ cho luồng sinh trên PC).
- `4630bc1` (2026-11-13): pipeline dữ liệu thiết bị (`scripts/device_session.py`,
  `software/device/`, `device-session-v1`), mốc và PAT ở ECG 512 sps, PPG 200 sps ba khe,
  bộ sinh dạng sóng SYNTHETIC có PAT biết trước; phân tích RQ1 trên SYNTHETIC
  (`scripts/run_rq1_analysis.py`, `software/evaluation/rq1_analysis.py`).
- `b5a2f00`, `6f6372b`, `a08eaea` (2026-11-13 → 2026-11-14): RQ2a trên PulseDB
  (`software/pulsedb/rq2a.py`, `scripts/run_rq2a_pulsedb.py`); định nghĩa duyệt nguyên trạng
  bằng commit riêng rồi mới chạy trên train ∪ val; kết quả ở
  `reports/weekly/week_08/pulsedb_rq2a_v0/`.
- `2dcf770` (2026-11-14): ghi nhận breakout MAX30001 nhận về là bản v2 03/24, cách xác định
  R3, R7, R8 trước khi sửa.
- `75aa449`, `a163e33` (2026-11-14): endpoint 5 và 7 giữ hiệu chuẩn của phân tích chính; cổng
  khóa cho dữ liệu thật khóa cả code bước tính đặc trưng, kiểm `provenance.json` của từng bảng
  đặc trưng.
- `e9af9a6` (2026-11-14): bước RAM trước buổi đo vào protocol 5.1.
- `9c078bb` (2026-11-14): báo cáo Tuần 8.
- Chỉ mới có trên `dev/huy`, chưa vào `develop`:
  - `bc58308` (2026-11-14): duyệt tiêu chí phần cứng (checklist bring-up, kế hoạch dòng
    rò/nhiệt/VLED, tiêu chí A1–A9, phần hiển thị DC) và các mục tự chốt của tuần 8;
  - `c62c901` (2026-11-14): ràng buộc `provenance.json` với bảng đặc trưng, khóa package cha,
    kiểm commit có thật;
  - commit ngày 2026-11-16 (một commit, sửa sau rà soát toàn dự án): khóa LED theo cửa sổ
    cuff và cờ `ppg:led_not_locked`, cờ thời gian theo tiêu chí A3, lọc zero-phase, endpoint
    10 của RQ1, timeout I²C của MAX30101 theo kích thước giao dịch; nhãn duyệt, số lần đo
    đồng bộ và liên kết trong tài liệu; dừng đánh dấu tay PulseDB ở 69/80 đoạn, không làm B4
    PulseDB ([tài liệu mốc Tuần 5](docs/protocol/week05_fiducials_pat_validity.md) mục 9.7).

## Tuần 7 (commit trực tiếp, 2026-11-07 → 2026-11-12)

Chi tiết: [báo cáo Tuần 7](reports/weekly/week_07/README.md).

- `a7e0ea1`, `c18e1d1` (2026-11-07 → 2026-11-08): kế hoạch Tuần 7, cập nhật phân công.
- `e96308d` (2026-11-10): logger ghi theo dòng (vẫn `packet-logger-v3`), `live_monitor`
  cảnh báo kết quả lệnh và mức DC của PPG, giới hạn trễ `MARK_EVENT`.
- `3761b1b`, `76c8f0f` (2026-11-10 → 2026-11-11): B5 (ResNet-18 1D, ECG + PPG;
  `scripts/run_b5_pulsedb.py`, PyTorch tùy chọn trong `requirements-dl.txt`); review rò rỉ và
  sửa trọng số của phần học.
- `38f23fe`, `7ed59a8` (2026-11-11): duyệt định nghĩa B5 nguyên trạng bằng commit riêng rồi
  chạy trên val.
- `f85d4d5`, `a8f21a8`, `e0e6912` (2026-11-10 → 2026-11-11): SAP v1, SQI v1, mô phỏng độ nhạy
  RQ1 (`scripts/simulate_rq1_sensitivity.py`), năm kiểu CI cho hiệu MAE theo người
  (`software/evaluation/mean_intervals.py`).
- `ac1c051`, `edbe46d` (2026-11-11 → 2026-11-12): mô phỏng Holm chung SBP–DBP và Ridge trong
  LOSO (`scripts/simulate_rq1_holm_loso.py`), thêm baseline theo pha.
- `e027ca5`, `c5c87b3` (2026-11-12): chốt các mục SAP v1 (chưa khóa), sửa protocol 6.5 và
  kịch bản bài báo.
- `c8ebb03`, `eafec93` (2026-11-10 → 2026-11-11): checklist bring-up, kế hoạch dòng rò, thử
  nhiệt, VLED, tiêu chí đo đồng bộ A1–A9 và test độ phủ pha PPG của kích thích.
- `9887b26` → `6aa76bf` (2026-11-10): rà soát tài liệu, bỏ tên người trong tài liệu kỹ thuật,
  đổi tên config và demo tuần 4–5, sửa câu chữ vượt quá bằng chứng.
- `480b968`, `30310c7` (2026-11-11): báo cáo Tuần 7.

## Tuần 6 (commit trực tiếp, 2026-10-29 → 2026-11-07)

Chi tiết: [báo cáo Tuần 6](reports/weekly/week_06/README.md).

- `e7336ea`, `6511926` (2026-10-29): lệnh `MARK_EVENT`, `packet-logger-v3` với
  metadata phiên v1, env `esp32s3_devkitc_all_real`; chọn mốc tay Tuần 5 chỉ trên train.
- `8e32b06` → `862ade6` (2026-10-29 → 2026-10-30, đẩy lên `develop`/`main`): protocol
  v0.3, hồ sơ đạo đức, RQ v0.4, tổng quan tài liệu 2026-10-29, đăng ký trước cách chấm
  test; bỏ M3, M4.
- `7234430` → `a946373` (2026-10-30 → 2026-10-31): trần tuyển 35, toàn văn S4, đề xuất
  cho buổi gặp thầy Tuần 7, hồ sơ đạo đức viết lại sau rà soát cuối.
- `c1c4b48` (2026-11-07): sửa lỗi tài liệu sau review Tuần 6 (cấp cứu, BP cao, quyền
  xóa, người đạt chuẩn, N6, bring-up 120 phút, trạng thái đơn hàng).
- `19fc432`, `1c708df`, `450302b`, `a215f07` (2026-11-07): B2 khóa cả mã trước khi chạy;
  v0 duyệt rồi dừng đúng chốt kiểm trước khi fit; v1 (nhân khẩu học theo từng đoạn) duyệt
  và chạy trên val.
- `69089de` (2026-11-07): theo dõi thí nghiệm (`run_registry`, `collect_runs.py`) và B3
  nhiều seed (`run_b3_multiseed.py`).
- Báo cáo Tuần 6 và kế hoạch Tuần 7.

## Tuần 5 (PR #25 và commit trực tiếp, 2026-10-26 → 2026-10-28)

- #25 (2026-10-26): phần cứng V1, firmware khung và Packet Schema.
  - Packet: Packet Schema V0.1 chốt, bản bổ sung V0.2
    (`configs/hardware/Packet_Schema_V0.2.md`, `VERSION 0x02`: IMU, mốc `SAMP`
    bit 8, `0xD1`, `0xB1`, `0xD2`, `0xD3`); logger `packet-logger-v2`
    (`scripts/packet_logger.py`, đọc file hoặc cổng serial, thêm `pyserial==3.5`),
    lệnh PC → thiết bị (`scripts/device_command.py`), mô phỏng
    `synthetic-packet-v3`.
  - Firmware ESP32-S3 khung (`firmware/`): gửi packet V0.2 từ nguồn AFE giả, nút
    `t0`, xung kích thích mã 3; driver MAX30001, MAX30101, BMI270 test trên máy
    tính, chưa chạy trên chip.
  - Tín hiệu: mốc R/foot thứ hai, PAT hợp lệ
    (`software/signal_processing/pat_validity.py`), so với đánh dấu tay và cổng
    chấp nhận (`fiducials-week05-v2`, `scripts/week05_fiducials.py`);
    `features-sqi-v2`; `motion-sqi-v0`.
  - PulseDB: reader `h5py` đọc từng phần (thêm `h5py==3.16.0`), `subject_subsample`
    của split, split Train 400 người (`configs/data/pulsedb_train400_split.json`),
    `b3-pipeline-v1` (QC DBP ≥ SBP, trọng số 1/n_s) và kết quả B0/B3 trên val
    (`reports/weekly/week_05/pulsedb_b3_v1/`); builder từ chối ECG/PPG trùng giữa
    split và sai thứ tự kênh; B2 có code và test SYNTHETIC, chưa chạy, chờ duyệt
    định nghĩa. Gỡ khỏi Git CSV nhãn và MAE test của pool AAMI Cal.
  - Phần cứng: KiCad V1-draft4, pin map, danh sách mua, trình tự bring-up, ước
    lượng dòng (`configs/hardware/power_budget_v1.md`); bỏ bản V0 nối dây.
  - Tài liệu: protocol v0.2, hồ sơ đạo đức bản nháp v0.1 (`docs/ethics/`), kịch bản
    bài báo v0.1, báo cáo Tuần 1–5 theo mẫu chung, kế hoạch Tuần 6.
- `9a10274` (2026-10-28, không qua PR): KiCad V1-draft5 theo bo Waveshare
  ESP32-S3-DEV-KIT-N8R8 (U1 63,3 × 25,4 mm, breakout ECG dời 0,5 mm, 3V3 hình sao);
  danh sách mua và bring-up cập nhật; so sánh điện cực ECG chuyển từ PDF sang
  Markdown.
- `18a4a63` (2026-10-28, không qua PR): bỏ ghi chú chờ duyệt theo người trong kế
  hoạch tuần, biên bản kickoff, protocol, Packet Schema, hướng dẫn logger, quy ước dữ
  liệu, `firmware/README.md` và định nghĩa B2; giữ các việc còn mở thật. B2 vẫn chưa
  duyệt, runner vẫn bị chặn.
- `4ee3e6d` (2026-10-28, không qua PR): báo cáo Tuần 5 cập nhật tới 2026-10-28.

## #24: làm chặt pipeline Tuần 4 và thêm kế hoạch Tuần 5 (2026-10-20)

- Kế hoạch Tuần 5 (`docs/plans/WEEK_05.md`).
- SQI `features-sqi-v1`: nhịp không ghép vì nằm sát biên cửa sổ không còn bị đếm
  là `pat:unmatched_beats` (v0 gắn cờ nhầm 89/200 cửa sổ sạch); ghi lại độ lệch
  foot +5,7 ms của lọc `zero_phase` trên fixture.
- `run_b3_pulsedb.py`: kiểm tra `source_sha256` của inventory với raw,
  `schema_version`, hash `config.json` và `pool_decision` của split; ghi
  `report.json` sau cùng kèm hash output.
- Hash code/config tính trên nội dung LF (`software/_provenance.py`); output ghi LF.
- Report split không còn thống kê nhãn của test; chia tỷ lệ bằng làm tròn thập
  phân chính xác; từ chối masked array và Subject nhiều giá trị.
- `scripts/check_environment.py` so Python và mọi pin với `pyproject.toml`/
  `requirements.txt`; CI kiểm tra conflict marker bằng `git grep -I`;
  `.gitignore` thêm `outputs/`, `evidence/`, `data/results/` và file phụ KiCad.
- Cập nhật README, RQ, provenance, protocol, quy ước dữ liệu và tài liệu phần cứng
  cho khớp code hiện tại.

## Tuần 4 (PR #20–#23, 2026-10-11 → 2026-10-20)

- #20 (2026-10-11): kế hoạch Tuần 4 (`docs/plans/WEEK_04.md`).
- #21 (2026-10-15): fiducial ECG/PPG và ghép PAT
  (`software/signal_processing/fiducials.py`); đặc trưng và SQI `features-sqi-v0`
  (`software/feature_extraction/week04.py`, `configs/data/week04_features_sqi.json`);
  bootstrap theo người (`software/evaluation/subject_bootstrap.py`); demo
  SYNTHETIC `scripts/demo_week04.py` và test; tổng quan y văn bổ sung, RQ
  v0.2, cập nhật protocol; báo cáo Tuần 4.
- #22 (2026-10-17): bản đầu pipeline huấn luyện PulseDB (`software/pulsedb/`
  `train.py`, `evaluate.py`, `features.py`, `pipeline.py`), notebook và
  `docs/testing.md`. Bản này có chấm điểm trên test; #23 thay bằng luồng chỉ
  đánh giá val.
- #23 (2026-10-20): B3 `XGBoostBaseline` (`software/models/xgboost_baseline.py`)
  và pipeline B0/B3 trên split v2, fit trên train, chỉ đánh giá val
  (`software/pulsedb/pipeline.py`, `scripts/run_b3_pulsedb.py`,
  `configs/models/b3_pulsedb_v0.json`, `docs/protocol/run_b3_pulsedb.md`); cố
  định `xgboost==3.2.0`; làm chặt reader và validator PulseDB; tài liệu phần
  cứng V1 (`configs/hardware/Packet_Schema_V0.1.md`,
  `configs/hardware/interface_power_sampling_v0.md`,
  `configs/hardware/custom_board_proposal.md`, thiết kế KiCad V1,
  `hardware/test_reports/sync_10min_test_plan.md`).

## Tuần 3 (PR #16–#19, 2026-10-03 → 2026-10-10)

- #16 (2026-10-03): kế hoạch Tuần 3.
- #17 (2026-10-08): B0 `PopulationMeanBaseline` và B1 `PersonalMeanBaseline`
  (`software/models/constant_baselines.py`); `evaluate_bp` cho MAE/bias/SD
  (`software/evaluation/bp_metrics.py`); validator dùng chung
  `software/_bp_validation.py`; demo SYNTHETIC `scripts/demo_week_03_baselines.py`,
  test và `docs/protocol/week_03_baselines_metrics.md`; báo cáo Tuần 3.
- #18 (2026-10-08): notebook split/hash PulseDB 1.000 đoạn
  (`notebooks/week3-split-hash.ipynb`, `notebooks/pulsedb_manifest_1000.csv`).
- #19 (2026-10-10): split theo người `pulsedb-split-v2` có inventory
  (`software/data_io/split_manifest.py`, `scripts/build_pulsedb_split.py`);
  runner B0 trên CSV PulseDB (`scripts/run_b0_pulsedb_csv.py`,
  `configs/data/b0_pulsedb_validation.json`); generator/replay packet SYNTHETIC
  `synthetic-packet-v2` (`software/data_io/packet_simulation.py`,
  `scripts/simulate_packets.py`); test và hướng dẫn chạy trong `docs/protocol/`.

## Tuần 2 (PR #11–#15, 2026-09-27 → 2026-10-01)

- #11 (2026-09-27): sửa BOM V0.1.
- #13 (2026-09-30): reader, validator và visualizer PulseDB (`software/pulsedb/`),
  notebook EDA, `docs/pulsedb_provenance.md`, thêm dependency `mat73`.
- #14 (2026-09-30): reader kiểm tra giới tính và schema kênh.
- #15 (2026-10-01): glossary mẫu/nhãn
  (`docs/protocol/week_02_sample_label_glossary.md`), báo cáo Tuần 2, đồng bộ
  RQ, protocol, ethics và literature matrix.

## Tuần 1 (PR #1–#10, 2026-09-18 → 2026-09-24)

- #1, #2 (2026-09-18): khung repository: cây thư mục, package `software`, smoke
  test, `scripts/check_environment.py`, CI, template Issue/PR, chính sách dữ
  liệu và kế hoạch Tuần 1.
- #3 (2026-09-19): chuẩn hóa CI, `.gitattributes` và `docs/WORKFLOW.md`.
- #4 (2026-09-22): bản thảo v0.1 của câu hỏi nghiên cứu, literature matrix,
  protocol outline, ethics outline, chương trình họp khởi động và báo cáo
  Tuần 1.
- #5, #6 (2026-09-22): sửa dữ liệu literature matrix và lỗi ký tự trong RQ.
- #8 (2026-09-23): môi trường venv/requirements, test môi trường,
  `docs/data_convention.md` và `docs/quy_uoc_du_lieu.md`.
- #9 (2026-09-23): xóa conflict marker, cập nhật CI và cấu hình môi trường, thêm
  dependency scikit-learn và PyYAML.
- #7 (2026-09-24): yêu cầu phần cứng V0, BOM V0.1, sơ đồ khối và hai phương án
  điện cực ECG.
- #10 (2026-09-24): đồng bộ literature matrix và tiêu chí tuổi trong protocol.
