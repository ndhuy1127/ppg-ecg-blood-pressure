# Báo cáo tiến độ Tuần 8

## 1. Tóm tắt công việc của tuần (mục tiêu)

Theo [kế hoạch Tuần 8](../../../docs/plans/WEEK_08.md):

1. Đường găng vẫn là phần cứng: xong phần A của checklist bring-up và duyệt tiêu chí phần cứng
   trước khi hàng về.
2. Đối chiếu giới hạn dòng rò với IEC 60601-1, tìm người có chuyên môn duyệt.
3. Đo RAM của logger trên laptop dùng cho buổi đo.
4. Pipeline dữ liệu thiết bị; mốc, PAT, cờ SQI ở tần số thiết bị (ECG 512 sps, PPG 200 sps ba
   khe); code phân tích RQ1 chạy trên dữ liệu dạng phiên thiết bị (SYNTHETIC).
5. RQ2a trên PulseDB (train ∪ val).
6. Đánh dấu tay mốc R/foot lần 1 và chạy `gate`.

Không đo trên người.

## 2. Thành viên phụ trách và phân công công việc

| Thành viên | Công việc Tuần 8 |
| --- | --- |
| Đức Anh | Phần A của checklist bring-up; đối chiếu IEC 60601-1, tìm người duyệt |
| Linh | RAM logger trên laptop đo; pipeline dữ liệu thiết bị; RQ2a trên PulseDB |
| Huy | Duyệt tiêu chí phần cứng và phần hiển thị DC; đánh dấu tay và `gate`; mốc, PAT, cờ SQI ở tần số thiết bị |
| Linh, Huy | Code phân tích RQ1 trên SYNTHETIC |

## 3. Tóm tắt công việc đã hoàn thành của từng người

### Đức Anh

- **Chuẩn bị bring-up** (8eb833a, 2026-11-13; chờ duyệt):
  - [checklist bring-up](../../../hardware/test_reports/v1_bringup_checklist.md): bảng firmware
    build sẵn bốn env kèm SHA-256 của ELF (build ở commit `0df0ba6`), metadata buổi đo, nơi ghi
    output `runs/bringup_v1/<YYYY-MM-DD>_<bước>/`, kết quả chạy thử logger không cần thiết bị;
  - [mẫu báo cáo bring-up](../../../hardware/test_reports/YYYY-MM-DD_v1_bringup.md) và metadata
    env khung;
  - `firmware/README.md`: build sạch trước khi ghi hash.
- **Breakout MAX30001 nhận về là bản v2** (2dcf770, 2026-11-14; cách xử lý chờ duyệt): bo in
  `v2`, `03/24`, khác file công khai duy nhất của ProtoCentral (v1.0, `03/22`); bố trí linh kiện
  khác, điện trở đầu vào in `4992` (49,9 kΩ) thay vì 51 kΩ. Trình tự bring-up mục 1 và 4 thêm
  cách xác định R3, R7, R8 bằng đo thông mạch; chưa tháo hay thay linh kiện nào cho tới khi có
  schematic v2 hoặc kết quả đo được duyệt. Footprint breakout trên bo đế mới đối chiếu với file
  v1.0 nên bước 1 phải đo header và lỗ vít của bo thật.
- **Chưa xong:** các ô làm tay của phần A (dụng cụ, dây đo, cáp USB-C đã thử, nút BOOT/RESET,
  bản in 1:1, dựng và kiểm mạch đo MD); đối chiếu nguyên văn IEC 60601-1; người duyệt.

### Linh

- **RAM logger trên laptop dùng cho buổi đo** (8eb833a, 2026-11-13; đề xuất chờ duyệt): luồng
  SYNTHETIC 120 phút, ba lần đo; đỉnh 894–895 MB ở khâu giải mã cuối buổi, lúc ghi chỉ khoảng
  24 MB. RAM trống của máy chỉ còn 9–15 % ngay trước khi chạy vì ứng dụng đang mở
  ([packet_logger.md](../../../docs/protocol/packet_logger.md)). Đề xuất đưa vào protocol 5.1
  bước đóng ứng dụng, `wsl --shutdown` và chỉ dừng ghi khi còn ≥ 2 GB (e9af9a6, 2026-11-14,
  chờ duyệt). Chưa đo trên máy đã đóng ứng dụng.
- **Pipeline dữ liệu thiết bị** (4630bc1, 2026-11-13; chờ duyệt):
  [device_session.py](../../../scripts/device_session.py) ingest bản ghi `packet-logger-v3`,
  kiểm metadata, cắt cửa sổ quanh lần cuff, tính đặc trưng, PAT, cờ SQI và tóm tắt phiên;
  định dạng `cuff_log.csv` và `cuff_features.csv` ghi ở
  [data_convention.md](../../../docs/data_convention.md) mục 4. Quy tắc `source_type`: DEVICE
  khi byte đến từ MCU thật, SYNTHETIC chỉ cho luồng sinh trên PC (8eb833a, chờ duyệt).
- **RQ2a trên PulseDB** (định nghĩa và code b5a2f00, 2026-11-13; duyệt nguyên trạng bằng
  commit riêng 6f6372b, 2026-11-14; chạy cùng ngày; kết quả a08eaea): mục 6.2.

### Huy

- **Mốc, PAT, cờ SQI ở tần số thiết bị** (4630bc1, 2026-11-13): ghép hai trục thời gian ECG
  512 sps và PPG 200 sps ba khe trước khi tính PAT; bộ sinh dạng sóng SYNTHETIC có PAT biết
  trước; test có đáp án ([device_session_pipeline.md](../../../docs/protocol/device_session_pipeline.md)).
- **Duyệt RQ2a** (6f6372b, 2026-11-14): duyệt nguyên trạng định nghĩa trước khi chạy.
- **Chưa xong:** duyệt checklist bring-up, kế hoạch dòng rò/nhiệt/VLED, tiêu chí A1–A9 và phần
  hiển thị DC; đánh dấu tay lần 1 (chưa có file đánh dấu mới sau khi bỏ phiên 2026-10-25, kiểm
  2026-11-14), nên chưa chạy `gate`.

### Linh, Huy

- **Phân tích RQ1 trên SYNTHETIC** (4630bc1, 2026-11-13; sửa sau rà soát độc lập trước commit):
  [run_rq1_analysis.py](../../../scripts/run_rq1_analysis.py) nối mô hình của `rq1_holm_loso`
  (zero-change, PAT-only, PPG-only, PPG + PAT, baseline theo pha, LOSO, Holm) với bảng đặc trưng
  theo lần cuff; `pilot` và `led_readjusted` bắt buộc với dữ liệu không phải SYNTHETIC; phiên
  chỉnh LED ra khỏi cả tập chính và tập học; kết luận chính cần cả d và d⁰; độ nhạy theo kiểu CI.
- **Endpoint 5 và 7 giữ hiệu chuẩn của phân tích chính** (75aa449, 2026-11-14; chờ duyệt, kèm
  một phản biện độc lập): mục 5.1.
- **Cổng khóa cho dữ liệu thật** (a163e33, 2026-11-14; chờ duyệt): khóa cả code của bước tính
  đặc trưng và config của nó; mỗi bảng đặc trưng phải có `provenance.json` khớp code đang khóa;
  bảng thiết bị bị gắn nhầm SYNTHETIC bị từ chối. Test so danh sách khóa với đồ thị import.

## 4. Danh mục sản phẩm đầu ra và đường dẫn

| STT | Sản phẩm | Người làm | Đường dẫn |
| --- | --- | --- | --- |
| 1 | Checklist bring-up: firmware build sẵn, metadata, mẫu báo cáo | Đức Anh | [v1_bringup_checklist.md](../../../hardware/test_reports/v1_bringup_checklist.md), [YYYY-MM-DD_v1_bringup.md](../../../hardware/test_reports/YYYY-MM-DD_v1_bringup.md), [v1_bringup_s2_default_env.json](../../../hardware/test_reports/metadata/v1_bringup_s2_default_env.json) |
| 2 | Ghi nhận breakout MAX30001 v2, cách xác định R3/R7/R8 | Đức Anh | [v1_bringup_procedure.md](../../../hardware/test_reports/v1_bringup_procedure.md) mục 1, 4; [custom_board_proposal.md](../../../configs/hardware/custom_board_proposal.md) A.2, A.6 |
| 3 | RAM logger trên laptop đo, bước RAM trước buổi đo | Linh | [packet_logger.md](../../../docs/protocol/packet_logger.md), [protocol_outline_v0.2.md](../../../docs/protocol/protocol_outline_v0.2.md) mục 5.1 |
| 4 | Quy tắc `source_type` | Linh | [Packet_Schema_V0.2.md](../../../configs/hardware/Packet_Schema_V0.2.md) |
| 5 | Pipeline dữ liệu thiết bị | Linh | [device_session.py](../../../scripts/device_session.py), [session_ingest.py](../../../software/device/session_ingest.py), [device_session_v1.json](../../../configs/data/device_session_v1.json), [data_convention.md](../../../docs/data_convention.md) mục 4, [test_device_ingest.py](../../../tests/test_device_ingest.py) |
| 6 | Mốc, PAT, cờ SQI ở tần số thiết bị; dạng sóng SYNTHETIC có PAT biết trước | Huy | [features.py](../../../software/device/features.py), [synthetic_session.py](../../../software/device/synthetic_session.py), [test_device_features.py](../../../tests/test_device_features.py) |
| 7 | Phân tích RQ1 theo SAP v1, endpoint 5/7, cổng khóa | Linh, Huy | [rq1_analysis.py](../../../software/evaluation/rq1_analysis.py), [run_rq1_analysis.py](../../../scripts/run_rq1_analysis.py), [rq1_analysis_v1.json](../../../configs/analysis/rq1_analysis_v1.json), [test_rq1_analysis.py](../../../tests/test_rq1_analysis.py), [device_session_pipeline.md](../../../docs/protocol/device_session_pipeline.md), [sap_v1.md](../../../docs/protocol/sap_v1.md) mục 3 |
| 8 | Định nghĩa, code và kết quả RQ2a | Linh | [rq2a_pulsedb_definition.md](../../../docs/protocol/rq2a_pulsedb_definition.md), [rq2a.py](../../../software/pulsedb/rq2a.py), [run_rq2a_pulsedb.py](../../../scripts/run_rq2a_pulsedb.py), [rq2a_pulsedb_v0.json](../../../configs/models/rq2a_pulsedb_v0.json), [test_rq2a.py](../../../tests/test_rq2a.py), [pulsedb_rq2a_v0/](pulsedb_rq2a_v0/README.md) |

## 5. Tóm tắt các nội dung chuyên môn chính

### 5.1. Endpoint 5 và 7 của SAP (đề xuất 2026-11-14, chờ duyệt)

SAP chưa nói lần cuff hiệu chuẩn (M0 phiên 1) có bị bỏ theo bộ lọc của endpoint 5 (cờ SQI) và
7 (cờ dừng an toàn) hay không. Bản đầu chạy lại toàn bộ nên BP₀ và đặc trưng nền đổi, kéo theo
nhãn ΔBP của mọi lần cuff của người đó. Đã chọn: giữ BP₀, đặc trưng nền và tư cách đạt chuẩn của
phân tích chính; bộ lọc chỉ bỏ lần cuff khỏi tập học và tập đánh giá; người không còn lần cuff
đánh giá thì không có d_s trong endpoint đó và được báo. Không chọn cách tính lại đặc trưng nền
từ lần cuff qua lọc vì BP₀ và đặc trưng nền sẽ lệch mốc với nhau. Ghi ở
[SAP v1](../../../docs/protocol/sap_v1.md) mục 3.

### 5.2. Breakout MAX30001 v2

Vị trí linh kiện của file v1.0 không dùng được cho bo v2. Trong khi chờ ProtoCentral gửi
schematic hoặc BOM v2, R3, R7, R8 chỉ xác định bằng đo thông mạch và coi là ứng viên; chân
BIN/BIP của MAX30001 nằm dưới thân chip nên không đo thẳng được.

## 6. Kết quả kiểm tra kỹ thuật

### 6.1. Kiểm tra toàn repo

Ngày 2026-11-14, sau mọi thay đổi của mục 3: `ruff check .` sạch; `pytest -q` 1.368 đạt, 1 bỏ
qua (tạo symlink cần quyền trên Windows), test firmware chạy bằng trình dịch C `ziglang`;
`scripts/check_environment.py` và `pip check` đạt.

### 6.2. RQ2a trên PulseDB train ∪ val (2026-11-14)

360 người, 129 600 đoạn, 5 lần lặp × 36 người đánh giá; A = chia ngẫu nhiên theo cửa sổ, B =
chia theo người, cùng tập đánh giá; B3 v1 nguyên trạng. Report ghi commit `6f6372b`,
`workspace_has_changes: false`. Chi tiết: [pulsedb_rq2a_v0/](pulsedb_rq2a_v0/README.md).

| Mô hình | Đầu ra | MAE A | MAE B | ΔMAE = B − A [CI 95 %] | % suy giảm [CI 95 %] |
| --- | --- | --- | --- | --- | --- |
| B0 | SBP | 14,99 | 14,99 | 0,01 [−0,00; 0,02] | 0,06 [−0,03; 0,16] |
| B0 | DBP | 9,33 | 9,35 | 0,01 [−0,00; 0,02] | 0,12 [−0,02; 0,26] |
| B3 | SBP | 13,86 | 14,81 | 0,95 [0,64; 1,34] | 6,82 [4,66; 9,54] |
| B3 | DBP | 8,51 | 9,20 | 0,69 [0,50; 0,92] | 8,09 [5,97; 10,74] |

Chia theo cửa sổ làm B3 trông tốt hơn khoảng 1 mmHg (7–8 %), CI trên 0 ở cả SBP và DBP; B0 gần
0 như kỳ vọng. Đây là cận dưới tương đối của hiệu ứng rò rỉ với mô hình yếu, báo ở phụ lục; không
phải hiệu năng huyết áp.

## 7. Mốc đóng Tuần 8 và việc chuyển sang Tuần 9

Đánh giá ngày 2026-11-14 theo mục "Mốc đóng tuần" của
[kế hoạch Tuần 8](../../../docs/plans/WEEK_08.md).

| Mốc đóng tuần | Trạng thái | Người xử lý | Chuyển sang |
| --- | --- | --- | --- |
| Phần A checklist xong | **Chưa:** phần viết và firmware build sẵn xong; các ô làm tay và mạch đo MD chưa làm | Đức Anh | Tuần 9, trước bước 1 bring-up |
| Tiêu chí phần cứng có commit duyệt | **Chưa:** checklist, kế hoạch dòng rò/nhiệt/VLED, A1–A9, phần hiển thị DC vẫn chờ duyệt | Huy | Tuần 9, trước khi đo PCB trần |
| Giới hạn dòng rò có điều khoản nguồn | **Chưa:** chưa đối chiếu nguyên văn IEC 60601-1, chưa có người duyệt | Đức Anh | Tuần 9, trước bước 13 |
| RAM đo trên laptop buổi đo | **Đạt phần đo:** đo 2026-11-13; đề xuất bước RAM trước buổi đo chờ duyệt; chưa đo trên máy đã đóng ứng dụng | Linh | Tuần 9: đo lại khi đã đóng ứng dụng |
| Pipeline ingest và mốc/PAT chạy trên SYNTHETIC, có test | **Đạt** (chờ duyệt định dạng và các mục tự chốt) | Linh, Huy | — |
| RQ2a | **Đạt:** duyệt, chạy, có bảng và CI (mục 6.2) | Linh | — |
| Đủ 80 đoạn đánh dấu lần 1 | **Chưa:** chưa bắt đầu lại | Huy | Tuần 9; `gate` rồi B4 sau đó |

**Đường găng** vẫn là phần cứng. Bo Waveshare ESP32-S3, MAX30101 và BMI270 chưa về; breakout
MAX30001 đã về nhưng là bản v2, đang chờ schematic. Các bước không cần ba module này (PCB trần,
sửa và hàn một phần) làm được sau khi duyệt checklist. Chưa có phê duyệt đạo đức nên chưa có dữ
liệu người.
