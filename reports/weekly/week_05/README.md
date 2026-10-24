# Báo cáo tiến độ Tuần 5

> **Giai đoạn:** Tuần 5 / 28 tuần (2026-10-20 → 2026-10-24; phần ngày 2026-10-24 ở
> cuối mục 3)
>
> **Thành viên:** Linh, Trương Đức Anh, Nguyễn Đức Huy

## 1. Tóm tắt công việc của tuần (mục tiêu)

Theo [kế hoạch Tuần 5](../../../docs/plans/WEEK_05.md), tuần này khắc phục G1 và
kéo các việc nằm trên đường găng của giai đoạn thu dữ liệu lên trước:

1. Đóng phần mềm G1: chạy B0/B3 trên raw PulseDB, đánh giá bằng bootstrap theo người.
2. Gỡ nút thắt phần cứng: danh sách mua module V1-module, pin map chuẩn, ERC/DRC,
   firmware khung.
3. Logger phía máy tính và mô phỏng packet đủ trường (kéo từ Tuần 8).
4. Hồ sơ đạo đức (kéo từ Tuần 6); phân bổ tay/điện cực và nghiệm pháp tạo ΔBP
   (kéo từ Tuần 10).
5. Phương pháp mốc R/foot thứ hai, định nghĩa PAT hợp lệ, so với đánh dấu tay.
6. Phác thảo ba kịch bản bài báo P A/P B/P C.

Không đo trên người trong tuần này.

## 2. Thành viên phụ trách và phân công công việc

| Thành viên | Công việc Tuần 5 |
| --- | --- |
| Linh | Logger packet V0.1 phía máy tính (decoder, kiểm tra, ghi raw, replay); mô phỏng `synthetic-packet-v3`; chuẩn bị chạy B0/B3 trên raw và phương án chọn pool PulseDB |
| Đức Anh | Danh sách mua module V1-module |
| Phần cứng và firmware | Firmware khung; pin map chuẩn theo KiCad; phân bổ điện cực; chốt các điểm mở của packet schema và review logger theo spec; trình tự bring-up; sơ đồ khối V1 |
| Huy | Trạng thái G1; hồ sơ đạo đức; protocol v0.2 (phân bổ tay, nghiệm pháp, tiêu chí pilot); mốc R/foot thứ hai, PAT hợp lệ, công cụ so với đánh dấu tay; kịch bản bài báo |

## 3. Tóm tắt công việc đã hoàn thành của từng người

### Linh

- **Codec packet V0.1** (`packet_wire.py`): CRC-16/CCITT-FALSE, đóng gói,
  `StreamDecoder` dò `SYNC` theo luồng; CRC sai hoặc header vô lý thì bỏ 1 byte và
  dò tiếp, không nhảy theo độ dài khai báo.
- **Kiểm tra packet** (`packet_receiver.py`) theo từng phiên/kênh: mất, trùng, xung
  đột, đảo thứ tự; mở rộng `SEQ`/`FIRST_SAMPLE_INDEX` qua 2³²; index liên tục đối
  chiếu `STATUS`; `T_ANCHOR_US` kiểm hai chiều với dung sai tốc độ ±3%; đổi
  `SESSION_ID` là phiên mới; `chain_id` tăng khi neo lại hoặc đổi Fs.
- **Logger** (`packet_logger.py`): `record` ghi raw bằng exclusive-create, ghi `t_rx`
  ra file riêng, decode trực tiếp rồi decode lại từ raw trên đĩa; ghi
  `session_manifest.json` sau cùng kèm hash; `replay --expect` so hash với manifest.
- **Mô phỏng `synthetic-packet-v3`**: luồng byte đúng schema (SYNC, VERSION,
  CHANNEL_ID, SESSION_ID, SEQ, FIRST_SAMPLE_INDEX, T_ANCHOR_US, FS_NOMINAL_MHZ,
  SAMPLE_COUNT ≤ 32, STATUS, DATA int32, CRC16), 13 case lỗi, packet sự kiện `0xC1`;
  v2 giữ nguyên.
- Bảng đối chiếu schema (mục 14.1) trong Packet Schema V0.1.
- Soạn hai phương án chọn pool PulseDB và các bước chạy B0/B3 khi có file raw.

### Đức Anh

- Lập danh sách mua V1-module: ESP32-S3-DevKitC-1 N16R8, MAX30001, BMI270, điện cực
  3M Red Dot 2228, điện cực khô BIOPAC, FSR 402, kèm phương án thay thế và link.

### Huy

- **Trạng thái G1** có ngày và bằng chứng (mục 5.1).
- **Hồ sơ đạo đức v0.1** (5 file): phiếu thông tin, phiếu đồng thuận, tiêu chuẩn
  chọn/loại L1–L10 và phiếu sàng lọc, an toàn buổi đo và quy tắc dừng, kế hoạch
  quản lý và giả danh hóa dữ liệu. Sửa mâu thuẫn trong khung v0.1 (nối USB với
  laptop chạy pin, không có đường nối người tham gia với điện lưới).
- **Protocol v0.2:** phân bổ tay phương án A; kiểm tra xung đột K1–K6;
  nghiệm pháp M0–M4 kèm nguồn; tiêu chí biên độ ΔBP pilot P1–P4; xác nhận module PPG
  MAX30101 (SparkFun SEN-16474).
- **Mốc thứ hai:** R bằng `derivative_energy`; foot bằng `d2_max` và `valley_min`,
  nội suy parabol dưới một mẫu có kiểm chiều cong; chọn qua `SignalConfig`, output
  mặc định `features-sqi-v1` không đổi.
- **PAT hợp lệ** (`pat_validity.py`): ghép R–foot trong khoảng R–R rồi gắn nhãn;
  giới hạn 80–400 ms, outlier MAD k = 3, sàn 10 ms, tối thiểu 3 cặp; không dùng BP;
  nhịp không hợp lệ được gắn nhãn, không xóa.
- **So với đánh dấu tay** (`fiducial_agreement.py`, `week05_fiducials.py`): các lệnh
  synth/export/plot/annotate/detect/compare, ghép một–một tối ưu, mọi lệnh ghi
  provenance, `compare` chỉ chạy với đúng config của `detect`, chặn split test, không
  tự sinh nhãn tay; mẫu CSV đánh dấu tay.
- **Kịch bản bài báo P A/P B/P C**: điều kiện kích hoạt, thông điệp chính, RQ trả lời
  được, bảng/hình chính.

### Phần cứng và firmware

- **Danh sách mua dạng Markdown** thay file Excel: đợt 1 gồm MAX30001 (breakout
  ProtoCentral), MAX30101 (SparkFun SEN-16474), BMI270 (SparkFun SEN-22397),
  ESP32-S3 DevKitC, điện cực 3M 2228; đợt 2 là linh kiện hàn cùng PCB V1; mục kiểm
  tra khi nhận hàng. Bỏ FSR 402 (V1 không dùng FSR), điện cực khô BIOPAC để đợt sau.
- **KiCad V1-module:** bỏ FSR, dùng box header có khóa ở bo cổ tay, thêm R9–R11 và C9.
- **Pin map chuẩn:** bảng A.7 trong `custom_board_proposal.md` lấy từ KiCad V1-module
  và thay các bảng chân cũ; A.6 ghi trạng thái từng mục.
- **Phân bổ điện cực:** 3 điện cực, LA cổ tay trái và RA cổ tay phải (mặt lòng), RL
  cẳng tay trái; LA → ECGP, RA → ECGN, RL → VCM qua R3; tắt lead bias nội. Cập nhật
  protocol v0.2 mục 5.2 và hồ sơ đạo đức theo cách đặt này.
- **Firmware khung** (ESP32-S3, PlatformIO + ESP-IDF 5.5.3): gửi packet V0.1 qua USB
  Serial/JTAG từ nguồn AFE giả; `SEQ` gán lúc gửi; hàng đợi MCU đầy thì packet bị bỏ
  trước khi có `SEQ` và packet kế của kênh bật bit 1 của `STATUS` (bit 1 chuyển tiếp
  nếu firmware gửi chính packet đó thất bại; từ 2026-10-23 chuyển cả bit 0); packet sự kiện `0xC1` từ nút t0; tự kiểm
  known-answer khi khởi động. Chưa có driver AFE thật, chưa chạy trên bo.
- **Test tương thích firmware–logger:** known-answer 50 byte trong header C khớp
  codec Python; encoder C biên dịch trên máy tính cho cùng byte với codec Python
  trên packet ngẫu nhiên (`test_firmware_c_encoder.py`, cần trình biên dịch C);
  luồng dựng theo quy ước firmware trong 10 phút đi qua `analyze_stream` của logger
  với đúng số lỗi chờ đợi. Các test này không chạy code ISR/task của firmware.
- **Chốt packet schema V0.1** (2026-10-23): giữ `VERSION = 0x01` và tên
  `FS_NOMINAL_MHZ`; định nghĩa lại mốc SAMP/INT2B của MAX30001 (cạnh xung đánh dấu
  lúc mẫu vào FIFO, không phải lúc lấy mẫu analog; ghi chú ADI cho MAX30003 đo trễ
  20,839 ms khi bỏ DLPF hoặc 32,558 ms khi DLPF 40 Hz ở 512 sps, chưa kiểm trên
  MAX30001); trả lời D1–D10 và xác nhận R1–R6 trong review logger.
- **Trình tự bring-up V1-module** thay file Word: kiểm khi nhận hàng, DevKitC đứng
  riêng, PCB trần, sửa module, hàn lắp, MAX30001, bo cổ tay, đo 10 phút.
- **Sơ đồ khối V1** (SVG) thay `Hardware_Diagram.png`.

### Cập nhật ngày 2026-10-24

**Dữ liệu và phần mềm**

- **Chốt pool PulseDB:** `VitalDB_Train_Subset.mat`, lấy mẫu con 400 người chỉ theo
  trường `Subject` (seed 20261024), để chia train/val/test;
  `VitalDB_CalFree_Test_Subset.mat` làm tập kiểm tra ngoài; không dùng CalBased Test
  (cùng người với Train) và hai subset AAMI (test của AAMI Cal đã bị chấm trong
  notebook Tuần 3–4). Pin `h5py==3.16.0` để đọc từng phần file `.mat` v7.3; reader
  đọc từng phần chưa viết, B0/B3 chưa chạy trên raw.
- **Quy tắc QC nhãn**, khóa trước khi đọc nhãn: chỉ loại dòng DBP ≥ SBP, ở mọi split,
  tại bước mô hình (config mới `b3-pipeline-v1`, mới có kế hoạch; `b3-pipeline-v0`
  giữ hành vi cũ).
- `features-sqi-v2` ghi `None` kèm lý do khi chưa ghép được PAT; split v2 từ chối khi
  ECG/PPG trùng giữa các split hoặc sai thứ tự kênh; bootstrap theo người gắn
  `few_subjects` khi dưới 10 người (vẫn tính CI) và API mặc định chỉ chấm val; CI cho
  hiệu ghép cặp và cho B3 − B0 trong runner.
- `motion-sqi-v0`: cờ cử động mạnh từ IMU ở cổ tay đeo PPG (định nghĩa chốt, ngưỡng
  0,15 g / 20 °/s chưa khóa; protocol v0.2).
- Gỡ hai CSV nhãn/MAE test của pool AAMI Cal khỏi Git (lấy lại được từ lịch sử Git).

**Phần cứng**

- Bỏ bản V0 nối dây, đi thẳng PCB V1-module; MCU chốt ESP32-S3-DevKitC-1-N8R8 chính
  hãng; bỏ các dòng mua chỉ dùng cho bản nối dây.
- Lấy mẫu chốt: ECG 512 sps (`EFIT = 15`, đọc FIFO tới EOF); PPG MAX30101 ba khe
  (xanh, đỏ, IR) 200 sps mỗi khe, `SMP_AVE = 1`, đọc khi FIFO có 8 mẫu và đọc hết;
  giữ VLED 5,1 V (đo ở bring-up). Độ rộng xung LED (411 hay 215 µs) còn mở.
- KiCad V1-draft4: thứ tự chân cáp mới có GND xen giữa các đường tín hiệu, header J3
  cho xung kích thích (GPIO6), bỏ TP7–TP10, không thêm điện trở kéo I²C, giữ C2/C3 ở
  bo cổ tay. ERC/DRC chỉ còn cảnh báo thư viện như trước khi sửa. Đặt gia công PCB
  ngay sau ERC/DRC.
- Bật xung `SAMP` của MAX30001 luôn và dùng làm mốc thời gian ECG (mục 5.8).

**Packet, logger và firmware**

- **Packet Schema V0.2** (`VERSION = 0x02`): IMU BMI270 sáu trục `0xA1`–`0xA6` ở
  100 Hz, phần tồn đọng (bit 7), FIFO đầy rồi neo lại (bit 5), packet thông tin thiết
  bị `0xD1`, mốc `SAMP` cho ECG (bit 8).
- **Logger** đọc V0.1 và V0.2, ghi được thẳng từ cổng serial (`--port`, pyserial 3.5),
  kiểm mốc ECG theo nguồn mốc (mục 5.8), ghi manifest theo từng phiên khi một raw có
  nhiều lần khởi động lại.
- **Firmware khung gửi V0.2:** packet `0xD1` mỗi 10 s; IMU giả có chia phần tồn đọng
  và neo lại sau FIFO đầy; mốc `SAMP` với xung giả; PPG đọc khi FIFO có 8 mẫu. MCPWM
  capture thật đã viết nhưng tắt và chưa chạy trên chip. Ngoài bản thường có ba bản
  build cố ý tạo lỗi để kiểm khi có bo: dừng đọc IMU, lỗi xung `SAMP`, đọc PPG trễ.
  Vẫn chưa có driver AFE thật và chưa chạy trên bo.

## 4. Danh mục sản phẩm đầu ra và đường dẫn

| STT | Sản phẩm | Người làm | Đường dẫn |
| --- | --- | --- | --- |
| 1 | Codec packet V0.1 | Linh | [packet_wire.py](../../../software/data_io/packet_wire.py) |
| 2 | Kiểm tra packet, metadata phiên | Linh | [packet_receiver.py](../../../software/data_io/packet_receiver.py) |
| 3 | Logger | Linh | [packet_logger.py](../../../scripts/packet_logger.py), [packet_logger.json](../../../configs/hardware/packet_logger.json) |
| 4 | Mô phỏng v3 | Linh | [packet_simulation_v3.py](../../../software/data_io/packet_simulation_v3.py), [packet_simulation_v3.json](../../../configs/hardware/packet_simulation_v3.json), [simulate_packets.py](../../../scripts/simulate_packets.py) |
| 5 | Test logger và đáp án | Linh | [test_packet_logger.py](../../../tests/test_packet_logger.py), [packet_v3_expected.json](../../../tests/fixtures/packet_v3_expected.json) |
| 6 | Hướng dẫn logger và mô phỏng | Linh | [packet_logger.md](../../../docs/protocol/packet_logger.md), [packet_simulation.md](../../../docs/protocol/packet_simulation.md) |
| 7 | Bảng đối chiếu schema (mục 14.1) | Linh | [Packet_Schema_V0.1.md](../../../configs/hardware/Packet_Schema_V0.1.md) |
| 8 | Danh sách mua (Excel) | Đức Anh | [Danh sách mua.xlsx](https://github.com/ndhuy1127/ppg-ecg-blood-pressure/blob/225832dce33c08f1d6c2468dc3b2bf1ac0afe6e1/hardware/bom/Danh%20s%C3%A1ch%20mua.xlsx) (nhánh `dev/ducanh`, commit `225832d`); bản hiện hành ở dòng 19 |
| 9 | Hồ sơ đạo đức v0.1 | Huy | [docs/ethics/](../../../docs/ethics/README.md) |
| 10 | Protocol v0.2 | Huy | [protocol_outline_v0.2.md](../../../docs/protocol/protocol_outline_v0.2.md) |
| 11 | Mốc ứng viên, `detect` | Huy | [fiducials.py](../../../software/signal_processing/fiducials.py) |
| 12 | PAT hợp lệ | Huy | [pat_validity.py](../../../software/signal_processing/pat_validity.py) |
| 13 | So với đánh dấu tay | Huy | [fiducial_agreement.py](../../../software/evaluation/fiducial_agreement.py), [week05_fiducials.py](../../../scripts/week05_fiducials.py), [mẫu CSV](../../../docs/protocol/templates/manual_fiducials_template.csv) |
| 14 | Config Tuần 5 | Huy | [week05_huy.json](../../../configs/data/week05_huy.json) |
| 15 | Tài liệu phương pháp | Huy | [week05_fiducials_pat_validity.md](../../../docs/protocol/week05_fiducials_pat_validity.md) |
| 16 | Test mốc Tuần 5 | Huy | [test_week05_fiducials.py](../../../tests/test_week05_fiducials.py) |
| 17 | Kết quả SYNTHETIC | Huy | [synthetic_fiducials/](synthetic_fiducials/agreement_synthetic.json) (thêm biến thể [refractory_040/](synthetic_fiducials/refractory_040/agreement_synthetic.json)) |
| 18 | Kịch bản bài báo | Huy | [paper_scenarios_v0.1.md](../../../docs/paper_scenarios_v0.1.md) |
| 19 | Danh sách mua V1-module | Phần cứng | [purchase_list_v1_module.md](../../../hardware/bom/purchase_list_v1_module.md) |
| 20 | KiCad V1-module (bo đế, bo cổ tay) | Phần cứng | [hardware/kicad/v1_module/](../../../hardware/kicad/v1_module/) |
| 21 | Pin map chuẩn A.7, trạng thái A.6 | Phần cứng | [custom_board_proposal.md](../../../configs/hardware/custom_board_proposal.md) |
| 22 | Phân bổ điện cực | Phần cứng | [protocol_outline_v0.2.md](../../../docs/protocol/protocol_outline_v0.2.md) mục 5.2 |
| 23 | Firmware khung V1-module | Firmware | [firmware/](../../../firmware/README.md) |
| 24 | Test firmware–logger | Firmware | [test_firmware_packet_kat.py](../../../tests/test_firmware_packet_kat.py), [test_firmware_c_encoder.py](../../../tests/test_firmware_c_encoder.py), [test_firmware_stream_compat.py](../../../tests/test_firmware_stream_compat.py) |
| 25 | Chốt packet schema V0.1, review logger | Firmware | [Packet_Schema_V0.1.md](../../../configs/hardware/Packet_Schema_V0.1.md) mục 2, 5, 6, 9, [packet_logger.md](../../../docs/protocol/packet_logger.md) |
| 26 | Trình tự bring-up V1-module | Phần cứng | [v1_bringup_procedure.md](../../../hardware/test_reports/v1_bringup_procedure.md) |
| 27 | Sơ đồ khối V1 | Phần cứng | [hardware_diagram_v1.svg](../../../configs/hardware/hardware_diagram_v1.svg) |
| 28 | Quyết định pool PulseDB, quy tắc QC nhãn (2026-10-24) | Huy | [pulsedb_provenance.md](../../../docs/pulsedb_provenance.md), [run_b3_pulsedb.md](../../../docs/protocol/run_b3_pulsedb.md) |
| 29 | `motion-sqi-v0` | Huy | [motion_sqi.py](../../../software/feature_extraction/motion_sqi.py), [protocol v0.2](../../../docs/protocol/protocol_outline_v0.2.md) mục 7.3 |
| 30 | Packet Schema V0.2 | Phần cứng và firmware | [Packet_Schema_V0.2.md](../../../configs/hardware/Packet_Schema_V0.2.md) |
| 31 | Logger và mô phỏng V0.2 | Huy | [packet_receiver.py](../../../software/data_io/packet_receiver.py), [packet_simulation_v3_v02.json](../../../configs/hardware/packet_simulation_v3_v02.json), [test_packet_v02.py](../../../tests/test_packet_v02.py) |
| 32 | Firmware V0.2 (encoder, `0xD1`, IMU giả, `SAMP`, PPG) | Firmware | [firmware/](../../../firmware/README.md) |
| 33 | Test firmware V0.2 | Firmware | [test_firmware_imu_plan.py](../../../tests/test_firmware_imu_plan.py), [test_firmware_samp_map.py](../../../tests/test_firmware_samp_map.py), [test_firmware_c_encoder.py](../../../tests/test_firmware_c_encoder.py) |
| 34 | KiCad V1-draft4 | Phần cứng | [hardware/kicad/v1_module/](../../../hardware/kicad/v1_module/), [custom_board_proposal.md](../../../configs/hardware/custom_board_proposal.md) A.2, A.3, A.7 |

## 5. Tóm tắt các nội dung chuyên môn chính

### 5.1. Trạng thái G1 (đánh giá ngày 2026-10-21)

| Hạng mục | Trạng thái | Bằng chứng |
| --- | --- | --- |
| Pipeline tái lập (reader, inventory, provenance) | Có | `reader.py`, `split_manifest.py` (split v2), hash không phụ thuộc CRLF |
| Split theo người có test rò rỉ | Có | `pulsedb-split-v2`, `tests/test_split_manifest.py` |
| Baseline đầu tiên | Gần đạt | B0/B1/metrics, B3 + runner split v2, test SYNTHETIC; chưa chạy trên raw PulseDB |
| Đặc trưng/SQI/bootstrap | Có (SYNTHETIC) | `features-sqi-v1`, `subject_bootstrap.py`, mốc thứ hai Tuần 5 |
| PPG–ECG đồng bộ, báo cáo phần cứng v0 | Chưa đạt | Có KiCad V1-draft4 qua ERC/DRC, pin map A.7, trình tự bring-up, kế hoạch đo 10 phút, firmware khung gửi Packet Schema V0.2 build được và logger đọc được (cập nhật 2026-10-24); chưa có module, chưa chạy firmware trên bo, chưa có bản ghi trên phần cứng |
| Hồ sơ đạo đức | Bản nháp v0.1 | `docs/ethics/` |

G1 phần mềm gần đạt; G1 phần cứng chưa đạt.

### 5.2. Logger và packet V0.1 (Linh)

- Packet little-endian dài 42 + 4N byte; CRC-16/CCITT-FALSE (known-answer
  `"123456789"` → `0x29B1`).
- Quy tắc logger R1–R5: `0xC1` bỏ kiểm index/timestamp nhưng vẫn kiểm `SEQ`/CRC; bit
  0/1/5 của `STATUS` giải thích nhảy index; kiểm `VERSION` trước CRC; `SAMPLE_COUNT = 0`
  là vô lý; dung sai timestamp 1 chu kỳ + 500 µs cộng dung sai tốc độ ±3%.
- Không nội suy, không ghép ECG–PPG theo index, không dịch kênh; offset giữa kênh
  không phải PAT.
- 13 case mô phỏng: `valid`, `missing`, `duplicate`, `reordered`, `timestamp`,
  `timestamp_first`, `offset`, `crc`, `byte_loss`, `index_jump`, `reanchor`,
  `version`, `session_restart`.

### 5.3. Phương án chọn pool PulseDB (Linh)

| | A (nối tiếp lịch sử) | B (pool lớn) |
| --- | --- | --- |
| Pool chia train/val/test | `VitalDB_AAMI_Cal_Subset.mat` (116 người) | `VitalDB_Train_Subset.mat` (1 293 người) |
| Không dùng vì trùng người | `VitalDB_AAMI_Test_Subset.mat` | `VitalDB_CalBased_Test_Subset.mat` |
| Held-out ngoài | `VitalDB_CalFree_Test_Subset.mat` (144 người) | `VitalDB_CalFree_Test_Subset.mat` |
| Số người theo split (seed 72) | 92/11/13 | — |

**Chốt 2026-10-24 (Huy): phương án B**, lấy mẫu con 400 người của Train (khoảng
320/40/40 người theo 0,8/0,1/0,1), CalFree Test làm tập kiểm tra ngoài. Lý do: test
của AAMI Cal đã bị chấm trong notebook Tuần 3–4, Train chưa bị chạm; 400 người vừa
RAM máy làm việc khi đọc từng phần ([pulsedb_provenance.md](../../../docs/pulsedb_provenance.md)).

### 5.4. Phân bổ tay và nghiệm pháp (Huy)

- **Phương án A:** PPG cổ tay trái, cuff bắp tay phải, ECG đạo trình I với điện cực
  dán Ag/AgCl ở mặt lòng hai cổ tay (LA trái, RA phải) và RL ở cẳng tay trái (cập
  nhật 2026-10-23, protocol v0.2 mục 5.2).
- Kiểm tra xung đột: K1 (cuff khác tay PPG) đạt; K2 (không làm chuyển động tay PPG)
  đạt trên giấy cho M0–M2; K3 loại nghiệm pháp bóp tay tĩnh vì đạo trình I có điện
  cực ở cả hai tay.
- **Nghiệm pháp:** M0 nghỉ; M1 thở chậm (giảm BP, Adler 2019); M2 tính nhẩm (tăng,
  Carroll 2012, Jern 1991); M3 ngâm chân nước lạnh (tăng SBP/DBP, Korhonen 2006,
  Velasco 1997); M4 đạp xe ngồi (tăng khi gắng sức, Stergiou 2023). 9/9 DOI đã đối
  chiếu metadata qua OpenAlex/Europe PMC.
- Tiêu chí biên độ ΔBP pilot P1–P4, ngưỡng 15 mmHg lấy từ kế hoạch 28 tuần.

### 5.5. Mốc thứ hai và PAT hợp lệ (Huy)

- `derivative_energy`: đạo hàm bình phương, trung bình trượt, dời về cực đại tín
  hiệu (không phải Pan–Tompkins).
- `d2_max`: cực đại đạo hàm bậc hai trước sườn lên; `valley_min`: cực tiểu trước
  peak; cả hai nội suy parabol dưới một mẫu.
- PAT ngoài 80–400 ms vẫn được ghép rồi gắn nhãn `out_of_range`; `r_status` là
  `paired`/`no_foot`/`ambiguous`/`edge` (từ `pat-validity-v1`, 2026-10-23: R sát
  biên cửa sổ mà foot nằm ngoài khoảng PPG phát hiện được là `edge`, không tính là
  R không ghép, như `features-sqi-v1`).
- Dung sai so khớp với đánh dấu tay chốt trước khi đánh dấu: R 50 ms, foot 100 ms.

### 5.6. Kịch bản bài báo (Huy)

Ba kịch bản P A/P B/P C kích hoạt theo G4/R2/R3/R5 của kế hoạch 28 tuần; mỗi kịch
bản có thông điệp chính, RQ trả lời được, bảng/hình chính và phần bỏ.

### 5.7. Phần cứng và firmware

- Pin map A.7: ECG SPI GPIO7/15/16/17, INTB GPIO21, INT2B GPIO47; PPG I²C GPIO8/9,
  INT GPIO18; BMI270 SPI GPIO10–13, INT1 GPIO14; nút t0 GPIO4; LED GPIO5. GPIO47 chạy
  3,3 V trên module WROOM-1 N8R8/N16R8 (chip R16V chạy 1,8 V); kiểm ký hiệu module
  và eFuse VDD_SPI trước khi dùng (bring-up mục 1, 2).
- Packet đi qua cổng USB Serial/JTAG gốc của ESP32-S3; log chữ đi riêng qua UART0
  để không lẫn vào luồng byte của logger.
- Mốc SAMP/INT2B của MAX30001 là lúc mẫu vào FIFO, không phải lúc lấy mẫu analog;
  phân tích offline trừ độ trễ hiệu dụng `L_us` đo ở bench, không dùng thẳng bảng
  datasheet (Packet Schema mục 5.2, 5.3). Từ 2026-10-24 `SAMP` bật luôn và làm mốc
  ECG (mục 5.8).
- Firmware chỉ phát dữ liệu giả, nên mọi kết quả hiện có chỉ kiểm đường packet
  MCU → USB → logger, không nói gì về chất lượng tín hiệu ECG/PPG.

### 5.8. Packet Schema V0.2 và mốc `SAMP` (2026-10-24)

- **Bit 8 (chỉ ECG):** `T_ANCHOR_US` là thời điểm cạnh `SAMP` của mẫu cuối packet,
  chốt bằng MCPWM capture; bit 8 = 0 là mốc đọc FIFO như V0.1. Firmware chỉ bật bit 8
  khi mọi cạnh từ mẫu cuối packet trước tới mẫu cuối packet này đều có, cách nhau
  1 953,125 µs ± 22 µs (tạm), và cạnh cuối tới trong hai chu kỳ sau lúc đọc FIFO. Lỗi
  thì dùng mốc đọc FIFO, sau 1 s khởi động lại ánh xạ (tối đa 1 lần mỗi 10 s; chỉ số
  mẫu về 0, bit 5).
- **Logger** kiểm hai nguồn mốc riêng, không bao giờ so chéo (chúng lệch nhau một
  khoảng chưa biết): mốc `SAMP` dung sai 200 µs, tốc độ ECG ±1 000 ppm (giá trị tạm,
  chỉnh sau bring-up), để lệch một mẫu (1,953 ms) bị bắt. Phép kiểm qua từ 398 mẫu
  (khoảng 0,78 s) không còn phân biệt được lệch một mẫu nên được báo
  `anchor_check_weak`. Lệch cố định một mẫu ngay từ đầu phiên logger không bắt được;
  chỉ phép đo kích thích 10 phút bắt được.
- **Độ trễ:** `L_ECG,SAMP` (từ lúc lấy mẫu analog tới cạnh `SAMP`) khác `L_ECG` của
  mốc đọc FIFO; metadata ghi riêng, PAT trừ đúng độ trễ của nguồn mốc.
- **PPG** vẫn dùng mốc đọc FIFO ở 200 sps, nên sai số thời gian phía PPG vẫn là phần
  đóng góp chính vào sai số PAT.

## 6. Kết quả kiểm tra kỹ thuật

### 6.1. Kiểm tra toàn repo

Chạy từ Git root bằng `.venv` (Python 3.13.12):

| Lệnh | Kết quả |
| --- | --- |
| `python -m pytest -q -p no:cacheprovider` (phần Huy, 2026-10-22) | **379 passed** (gồm 50 test Tuần 5 của Huy) |
| `python -B -m pytest -q -p no:cacheprovider` (phần Linh, 2026-10-22) | **416 passed** (gồm test `test_packet_logger.py`; test v2 không đổi) |
| `python -m pytest -q -p no:cacheprovider` (toàn repo, 2026-10-23) | **471 passed** (gồm test known-answer và tương thích firmware–logger) |
| `pio run -d firmware` (2026-10-23) | Build đạt, RAM 4,5 %, flash 19,8 % của phân vùng 1 MB; chưa nạp lên bo |
| `python -m pytest -q -p no:cacheprovider` (toàn repo, Python 3.11 có trình biên dịch C, 2026-10-25) | **666 passed** (gồm test C của encoder, `imu_plan`, `samp_map`); `.venv` Python 3.13 không có trình biên dịch C: 622 passed, 44 skipped |
| `pio run -d firmware -j 1`, bốn env (2026-10-24) | Build đạt, không cảnh báo; RAM 4,9 %, flash 20,4–20,5 %; build song song có lúc GCC lỗi nội bộ do thiếu RAM trống, build tuần tự thì qua |
| CI trên PR #25 (2026-10-24, commit `ede2629`) | Đạt (ruff và pytest, Python 3.11) |
| `python -m ruff check .` | Đạt |
| `python -m ruff check --select E501` trên file `.py` mới | Đạt (≤ 88 ký tự) |
| `python -m pip check` | Đạt |
| `git diff --check` | Đạt |
| `python scripts/check_environment.py` | Exit 1 do lệch pin đã biết (Python 3.13.12 so với `<3.12`, numpy/pandas/scipy khác pin) |

Mutation test: logger của Linh bắt 33/33 mutant; test mốc Tuần 5 của Huy bắt 33/33
mutant nhắm vào các phần đã sửa.

### 6.2. Logger trên 13 case SYNTHETIC (Linh)

Mỗi case: `simulate_packets.py` chạy hai lần cho cùng SHA-256 `stream.bin`;
`packet_logger.py record` cho `raw.bin` trùng hash; `replay --expect` exit 0.

| Tiêu chí | Kết quả |
| --- | --- |
| Gói hợp lệ | `valid`: 26/26 packet, 0 lỗi |
| Mất / trùng / đảo thứ tự | `missing_packets` 1 / `duplicate` 1 / `out_of_order` 1 |
| Timestamp bất thường | `timestamp_anomaly` 1, chỉ packet sai bị cách ly (kể cả anchor sai ở packet đầu) |
| Lệch kênh | `channel_offset` 1: +19 862,875 µs so với 20 000 µs chèn vào, trong giới hạn jitter |
| CRC sai, mất byte | `crc_mismatch` 1 + `skipped_bytes` 1 + `missing_packets` 1; bắt lại `SYNC` ở packet kế |
| Index nhảy, version lạ, đổi phiên | `sample_gap_status` 1, `sample_index_reanchored` 1, `unsupported_version` 1, `session_change` 1 |
| Không ghi đè raw | Test `FileExistsError`; manifest có SHA-256 raw và mọi output |
| Replay offline | 13/13 case khớp hash |

### 6.3. Mốc R/foot trên SYNTHETIC (Huy)

**Bản v1 (2026-10-25)**, sau bốn quyết định về mốc (tách refractory PPG 0,35 s, ngưỡng
năng lượng theo phân vị, không nội suy foot, đỉnh T giả lập theo nhịp tim; tài liệu
phương pháp mục 8): 6 bản ghi `SYN_*` (thêm bản ghi biên T ở R + 0,25 s),
[agreement_synthetic.json](synthetic_fiducials_v1/agreement_synthetic.json).

| Phương pháp | Kết quả v1 |
| --- | --- |
| R `derivative_energy` | 64/64 TP, 7 FP (đều ở bản ghi nhiễu) |
| R `prominence` (refractory 0,25 s) | 64/64 TP, 44 FP (bắt đỉnh T ở mọi bản ghi HR 60) |
| Foot `tangent` | 63/63; lệch +27,4 ms (do hình dạng xung) |
| Foot `d2_max` | 59/63, MAE 13,0 ms |
| Foot `valley_min` | 57/63, MAE 2,7 ms (bản ghi sạch lệch 0 chỉ vì onset rơi đúng lưới mẫu) |

**Bản v0 (2026-10-21/22, lịch sử)**, 5 bản ghi `SYN_*`, đáp án do mã sinh
([agreement_synthetic.json](synthetic_fiducials/agreement_synthetic.json)):

| Phương pháp | Kết quả |
| --- | --- |
| R `derivative_energy` (refractory 0,25 s) | 55/55 TP, 2 FP |
| R `prominence` (refractory 0,25 s) | 55/55 TP, 29 FP (bắt sóng T) |
| R ở refractory 0,4 s | `prominence` 0 FP, `derivative_energy` 1 FP |
| Foot `tangent` | 54/54; lệch +27,2 ms ở bản ghi sạch (giải tích 27,25 ms), +18,8 ms ở HR 143, +47,4 ms ở bản ghi nhiễu |
| Foot `d2_max` | 50/54 |
| Foot `valley_min` | 48/54, hỏng chủ yếu ở bản ghi nhiễu |

Sóng T SYNTHETIC đặt đúng R + 0,25 s, trùng biên refractory, nên bảng này chỉ kiểm
chứng code, không xếp hạng phương pháp. Output mặc định `features-sqi-v1` giống
từng byte với bảng fixture Tuần 4 và giống HEAD trên 240 cửa sổ × 2 config.
