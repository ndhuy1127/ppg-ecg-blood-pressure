# Changelog

Ghi các thay đổi đã merge vào `develop`, nhóm theo tuần của lộ trình. Nguồn: lịch
sử Git (PR #1–#25 và ba commit đẩy thẳng ngày 2026-10-28) và báo cáo tuần trong
`reports/weekly/`. Ngày là ngày merge PR, hoặc ngày commit với commit không qua PR.
Changelog không ghi kết quả hiệu năng; test và demo trên dữ liệu SYNTHETIC chỉ
kiểm tra code. Ngày tính theo giờ Việt Nam (UTC+7).

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
  (`software/feature_extraction/week04.py`, `configs/data/week04_huy.json`);
  bootstrap theo người (`software/evaluation/subject_bootstrap.py`); demo
  SYNTHETIC `scripts/demo_week04_huy.py` và test; tổng quan y văn bổ sung, RQ
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
