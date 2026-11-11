# Báo cáo tiến độ Tuần 7

## 1. Tóm tắt công việc của tuần (mục tiêu)

Theo [kế hoạch Tuần 7](../../../docs/plans/WEEK_07.md):

1. Đường găng vẫn là phần cứng: ghi đủ đơn hàng và ngày giao, chuẩn bị
   bring-up (checklist, dòng rò, VLED).
2. Sửa logger theo review ngày 2026-11-07 (RAM, kết quả lệnh, mức DC khi chỉnh LED,
   `MARK_EVENT` trễ) trước lần chạy cả hệ 120 phút.
3. B5: tái lập một mô hình đã công bố trên PulseDB ECG + PPG, cùng split và quy trình đánh
   giá của B0–B3.
4. SQI specification v1 và SAP v1 cho RQ1, kèm mô phỏng độ nhạy.
5. Đánh dấu tay mốc R/foot lần 1 và chạy `gate`.
6. Gặp thầy về các đề xuất sửa protocol và hồ sơ đạo đức.

Không đo trên người.

## 2. Thành viên phụ trách và phân công công việc

| Thành viên | Công việc Tuần 7 |
| --- | --- |
| Linh | B5 trên PulseDB; sửa logger theo review 2026-11-07 |
| Đức Anh | Ghi đủ đơn hàng, ngày giao; chuẩn bị bring-up: checklist, đo dòng rò, thử nhiệt, quy tắc VLED; tiêu chí đo đồng bộ ECG–PPG |
| Huy | SQI v1, SAP v1, mô phỏng độ nhạy RQ1; đánh dấu tay và `gate`; gặp thầy; review B5; rà soát tài liệu |

## 3. Tóm tắt công việc đã hoàn thành của từng người

### Linh

- **Logger theo review 2026-11-07** (e96308d, 2026-11-10; vẫn `packet-logger-v3`):
  - `record` không giữ packet trong lúc ghi; ghi `rx_chunks.csv`, `t_rx_packets.csv` và ba
    file output theo dòng; cuối buổi giải mã `raw.bin` một lần từ đĩa. Output trùng từng byte
    với bản trước khi sửa trên 98 luồng mô phỏng (fixture hash từ `a7e0ea1`) và một luồng
    100.103 packet;
  - `live_monitor.py`: in kết quả từng lệnh khác `ok`, so mã LED MAX30101 trong `0xD2` với
    `ppg_led_lock`, và mức DC của PPG (% thang đo, cờ `LOW`/`HIGH`, số mẫu chạm trần) khi bật
    `--dc-every-s`, cho quy trình chỉnh LED ở protocol 6.1 (phần hiển thị chờ duyệt);
  - `MARK_EVENT` quá 1,0 s thì không gửi và báo;
  - thư mục người/buổi trong `data/raw/` là liên kết sang người/buổi khác thì bị từ chối.
  - RAM đo lại ở mục 6.2. Test trên máy tính, chưa chạy với thiết bị.
- **B5** (3761b1b, 2026-11-10): ResNet-18 1D của chính bài PulseDB (Wang và cộng sự 2023),
  2 kênh ECG + PPG, hai mô hình SBP/DBP, MSE, Adam lr 10⁻⁶, 100 epoch; dựng lại theo mô tả vì
  bài không công bố code hay MAE từng tập con
  ([định nghĩa B5](../../../docs/protocol/b5_pulsedb_definition.md)). Config
  `PENDING_REVIEW`; runner từ chối chế độ `val` khi chưa có commit duyệt. PyTorch 2.6.0 là
  dependency tùy chọn (`requirements-dl.txt`), chờ duyệt. Đã chạy chế độ `inner` chỉ trên
  train (mục 6.4); chưa có số trên val. Review rò rỉ xong ngày 2026-11-11; chờ commit duyệt
  để chạy val.

### Đức Anh

- **Checklist bring-up** và **kế hoạch đo dòng rò, thử nhiệt, nghiệm thu VLED** (c8ebb03,
  2026-11-10; chờ duyệt):
  - checklist chia "chuẩn bị trước khi hàng về" (dụng cụ, dây đo, nạp qua USB native, build
    sẵn bốn env firmware, logger) và "khi hàng về";
  - dòng rò đo đúng cấu hình buổi đo (laptop chạy pin, mã LED `0x7F`); giới hạn số **chưa đối
    chiếu nguyên văn IEC 60601-1**, cần người có chuyên môn duyệt trước khi gắn điện cực lên
    bất kỳ ai;
  - quy tắc VLED mới V1–V4 thay tiêu chí cũ 4,5–5,0 V (luôn trượt với 5,1 V danh định):
    không tải 4,9–5,3 V, quá áp khởi động ≤ 5,5 V, trong xung `0x7F` 4,5–5,5 V; đỏ/IR ở
    5,0–5,3 V "đạt có ghi chú".
- **Tiêu chí đo đồng bộ ECG–PPG viết trước khi đo** (eafec93, 2026-11-11; chờ duyệt):
  A1–A9 ở [kế hoạch đo đồng bộ](../../../hardware/test_reports/sync_10min_test_plan.md)
  mục 9 (toàn vẹn dữ liệu, tốc độ thực, mô hình thời gian tuyến tính, offset ECG–PPG trong một
  lần đo ≤ 0,15 ms nửa CI, lặp lại qua 10 lần khởi động ≤ 0,3 ms, trôi trong 120 phút
  ≤ 0,4 ms, độ trễ ECG so với 32,558 ms, độ phủ pha kích thích); ngân sách sai số PAT ở mục 10.
  Firmware `stim_plan`: test mới cho thấy 600 cạnh kích thích phủ đều cả chu kỳ mẫu PPG 5 ms,
  kể cả khi tốc độ PPG lệch ± 3 %. Checklist thêm ba phép kiểm chặn đường thời gian.
- **Đơn hàng:** chưa ghi thêm nơi bán, ngày giao, mã đơn
  ([danh sách mua](../../../hardware/bom/purchase_list_v1_module.md) mục 5). Hàng dự kiến về
  Tuần 8.

### Huy

- **SAP v1, SQI v1 và mô phỏng độ nhạy RQ1** (f85d4d5, 2026-11-10; sửa a8f21a8 và e0e6912,
  2026-11-11; chờ duyệt):
  - [SAP v1](../../../docs/protocol/sap_v1.md): estimand và endpoint, Ridge α = 1, CI chính
    là khoảng bao của bootstrap-t và Student t (đổi từ percentile ngày 2026-11-10), đa kiểm định
    phương án A (Holm giữa SBP và DBP), đọc theo δ, quy tắc δ chốt sau pilot, dữ liệu thiếu;
  - [SQI v1](../../../docs/protocol/sqi_specification_v1.md): gộp `features-sqi-v2`,
    `motion-sqi-v0` và cờ phần cứng V1; ngưỡng chưa có nguồn, khóa trên bản ghi G2;
  - mô phỏng chỉ dùng giả định (mục 5.1, 6.3); ngày 2026-11-11 thêm hai mô phỏng còn thiếu:
    SBP và DBP chung một nghiên cứu với Holm, và Ridge huấn luyện thật trong LOSO (mục 6.5);
    SAP thêm thang trọng số của Ridge;
  - `mean_intervals.py`: năm kiểu CI (percentile, BCa, bootstrap-t, Student t, khoảng bao) cho
    hiệu MAE trung bình đều theo người, dùng chung cho phân tích thật và mô phỏng, có test đáp
    án biết trước.
- **Đánh dấu tay:** bỏ phiên ngày 2026-10-25 vì bấm nhầm (87dc563, 2026-11-11): 62 mốc trên 28
  đoạn, 27 đoạn chỉ có 1 đỉnh R và 1 chân sóng. File được chuyển nguyên trạng sang
  `discarded_2026-11-11/`, không dùng cho `compare`, `repeat` hay `gate`. Lần 1 bắt đầu lại từ
  0/80 đoạn theo quy tắc chốt 2026-10-29
  ([tài liệu mốc](../../../docs/protocol/week05_fiducials_pat_validity.md) mục 9). Chưa chạy
  `gate`; B4 vẫn bị chặn.
- **Gặp thầy:** ngày 2026-11-10 thầy cho biết hồ sơ đạo đức chưa cần làm gấp. Chưa có biên bản
  trong repo; các đề xuất 2.1–2.8 ở
  [đề xuất Tuần 7](../../../docs/meetings/week_07_de_xuat_sua_protocol_va_ho_so.md) chưa có
  trả lời ghi lại.
- **Rà soát tài liệu** (9887b26, b26c9a5, 0cd69ad, 6aa76bf, 2026-11-10):
  - bỏ tên người trong tài liệu kỹ thuật, config và comment (báo cáo và kế hoạch tuần giữ
    tên); đổi `week04_huy.json` → `week04_features_sqi.json`, `week05_huy.json` →
    `week05_fiducials.json`, `demo_week04_huy.py` → `demo_week04.py`;
  - sửa câu chữ vượt quá bằng chứng: B2 "không thêm gì" → "chưa thấy thêm thông tin (CI chứa
    0)"; PPG trễ so với ECG trên PulseDB là "giả thuyết, chưa kiểm chứng"; MAE B3 nằm trong
    khoảng của y văn nhưng B0 hằng số cũng vậy;
  - sửa trích dẫn (Meziane 2015), tên nhánh `dev/ngoclinh`, README trạng thái Tuần 7.
- **Review B5** về rò rỉ và so sánh công bằng (2026-11-11, kèm một phản biện độc lập): không
  có lỗi chặn. Sửa trọng số của phần học (chuẩn hóa trên 288 người học thay vì cả 320 người
  rồi cắt; trên split v2 mọi trọng số vẫn bằng 1 nên lần chạy `inner` không đổi), thêm test;
  viết lại mục chống rò rỉ cho đúng (nhãn và dạng sóng val/test vẫn được đọc để băm và QC,
  không vào mô hình); ghi rõ B5 − B0/B3 là so sánh quy trình
  ([định nghĩa B5](../../../docs/protocol/b5_pulsedb_definition.md) mục 5, 6, 9).

## 4. Danh mục sản phẩm đầu ra và đường dẫn

| STT | Sản phẩm | Người làm | Đường dẫn |
| --- | --- | --- | --- |
| 1 | Logger ghi theo dòng, hiển thị khi đang ghi | Linh | [packet_logger.md](../../../docs/protocol/packet_logger.md), [packet_logger.py](../../../scripts/packet_logger.py), [live_monitor.py](../../../software/data_io/live_monitor.py), [command_desk.py](../../../software/data_io/command_desk.py) |
| 2 | Test logger | Linh | [test_packet_streaming.py](../../../tests/test_packet_streaming.py), [test_live_monitor.py](../../../tests/test_live_monitor.py), [test_command_desk.py](../../../tests/test_command_desk.py), [packet_outputs_a7e0ea1.json](../../../tests/fixtures/packet_outputs_a7e0ea1.json) |
| 3 | Định nghĩa B5 (chờ duyệt) | Linh | [b5_pulsedb_definition.md](../../../docs/protocol/b5_pulsedb_definition.md), [b5_pulsedb_v0.json](../../../configs/models/b5_pulsedb_v0.json) |
| 4 | Code và test B5 | Linh | [resnet1d.py](../../../software/models/resnet1d.py), [pipeline_b5.py](../../../software/pulsedb/pipeline_b5.py), [run_b5_pulsedb.py](../../../scripts/run_b5_pulsedb.py), [test_b5_pipeline.py](../../../tests/test_b5_pipeline.py), [requirements-dl.txt](../../../requirements-dl.txt) |
| 5 | Checklist bring-up | Đức Anh | [v1_bringup_checklist.md](../../../hardware/test_reports/v1_bringup_checklist.md) |
| 6 | Kế hoạch dòng rò, thử nhiệt, VLED | Đức Anh | [leakage_thermal_test_plan_v1.md](../../../hardware/test_reports/leakage_thermal_test_plan_v1.md) |
| 7 | Tiêu chí đo đồng bộ A1–A9, ngân sách sai số PAT | Đức Anh | [sync_10min_test_plan.md](../../../hardware/test_reports/sync_10min_test_plan.md) mục 9–10 |
| 8 | Test độ phủ pha PPG của kích thích | Đức Anh | [stim_plan.h](../../../firmware/include/stim_plan.h), [test_firmware_stim_plan.py](../../../tests/test_firmware_stim_plan.py) |
| 9 | SAP v1 | Huy | [sap_v1.md](../../../docs/protocol/sap_v1.md) |
| 10 | SQI specification v1 | Huy | [sqi_specification_v1.md](../../../docs/protocol/sqi_specification_v1.md) |
| 11 | Mô phỏng độ nhạy RQ1 | Huy | [rq1_sensitivity.py](../../../software/evaluation/rq1_sensitivity.py), [simulate_rq1_sensitivity.py](../../../scripts/simulate_rq1_sensitivity.py), [rq1_sensitivity_v2.json](../../../configs/analysis/rq1_sensitivity_v2.json), [test_rq1_sensitivity.py](../../../tests/test_rq1_sensitivity.py) |
| 12 | Kết quả mô phỏng v2 (khoảng bao) và v1 (percentile) | Huy | [rq1_sensitivity_v2/](rq1_sensitivity_v2/summary.md), [rq1_sensitivity/](rq1_sensitivity/summary.md) |
| 13 | Năm kiểu CI cho hiệu MAE theo người | Huy | [mean_intervals.py](../../../software/evaluation/mean_intervals.py), [subject_bootstrap.py](../../../software/evaluation/subject_bootstrap.py), [test_subject_bootstrap.py](../../../tests/test_subject_bootstrap.py) |
| 14 | Ghi nhận bỏ phiên đánh dấu tay 2026-10-25 | Huy | [week05_fiducials_pat_validity.md](../../../docs/protocol/week05_fiducials_pat_validity.md) |
| 15 | Mô phỏng Holm chung SBP–DBP và Ridge trong LOSO | Huy | [rq1_holm_loso.py](../../../software/evaluation/rq1_holm_loso.py), [simulate_rq1_holm_loso.py](../../../scripts/simulate_rq1_holm_loso.py), [rq1_holm_loso_v1.json](../../../configs/analysis/rq1_holm_loso_v1.json), [test_rq1_holm_loso.py](../../../tests/test_rq1_holm_loso.py), [kết quả](rq1_holm_loso/summary.md) |
| 16 | Review B5, sửa trọng số phần học | Huy | [b5_pulsedb_definition.md](../../../docs/protocol/b5_pulsedb_definition.md) mục 9, [pipeline_b5.py](../../../software/pulsedb/pipeline_b5.py), [test_b5_pipeline.py](../../../tests/test_b5_pipeline.py) |

## 5. Tóm tắt các nội dung chuyên môn chính

### 5.1. SAP v1: các đề xuất chính (chờ duyệt)

- **Kết luận chính** cho một đầu ra cần cả hai CI, của trung bình d_s (PPG + PAT so với
  PPG-only) và d⁰_s (so với zero-change), nằm dưới 0. Holm giữa SBP và DBP: bước 1 ở 97,5 %,
  bước 2 ở 95 %.
- **CI chính đổi từ percentile sang khoảng bao của bootstrap-t và Student t** (2026-11-10).
  Trong mô phỏng khi PAT không thêm gì, percentile cho CI nằm dưới 0 ở 3,7 % nghiên cứu (danh
  nghĩa 2,5 %); khoảng bao 2,3 %, tối đa 4,1 % ở các dạng phân bố đã thử. Cái giá là CI rộng
  hơn 9–23 %.
- **δ** = max(1 mmHg; 0,5 × SD lặp lại của cuff), chốt sau pilot, không đổi sau khi thấy dữ liệu
  chính.
- **P2 mới:** trung vị ΔSBP có dấu ở M2, ngưỡng báo động 10 mmHg; R3 chỉ để mô tả.
- **Hai mô phỏng còn thiếu đã chạy ngày 2026-11-11** (mục 6.5). Việc còn lại trước khi khóa
  SAP: quyết định baseline mạnh hơn zero-change (trung bình ΔBP theo nghiệm pháp, hoặc
  "static" của S4).

### 5.2. Bring-up: điều cần biết trước khi hàng về

- Giới hạn dòng rò chưa đối chiếu nguyên văn IEC 60601-1; người có chuyên môn phải duyệt
  phương pháp, giới hạn và biên bản. Không đo trên người, kể cả thành viên nhóm, cho tới khi có
  biên bản đạt và phê duyệt phù hợp.
- Phía PPG không có giá trị trễ thiết kế, nên lệch cố định một khe hay một mẫu PPG không có
  phép kiểm độc lập trong kế hoạch: PAT tuyệt đối từ thiết bị có thể lệch cố định tới 5 ms.
  ΔPAT không bị ảnh hưởng bởi phần cố định này.
- Nếu A5 và A6 đạt, sai số hệ thống của ΔPAT giữa hai phiên do thiết bị khoảng 0,5–0,7 ms
  (ước lượng, không phải cận trên đã chứng minh); chưa quy ra mmHg được.

### 5.3. B5

Chọn mô hình mẫu của chính bài PulseDB vì cùng dataset, cùng dạng đoạn 10 s, 125 Hz, đầu vào
ECG + PPG. Giới hạn: bài không công bố MAE từng tập con hay code huấn luyện, nên không có con số
đích để so; Hình 4 (sơ đồ lớp) chưa được đối chiếu. Sau khi thấy số trên val không đổi kiến
trúc, quy trình học hay cách chọn epoch; nếu đổi thì tạo version mới và báo cả hai.

## 6. Kết quả kiểm tra kỹ thuật

### 6.1. Kiểm tra toàn repo

Ngày 2026-11-11, sau mọi thay đổi của mục 3 (kể cả review B5 và mô phỏng mục 6.5): `ruff
check .` sạch; `pytest -q` 1.299 đạt, 1 bỏ qua (tạo
symlink cần quyền trên Windows), test firmware chạy bằng trình dịch C `ziglang`;
`scripts/check_environment.py` và `pip check` đạt. Không có trình dịch C thì 105 test firmware
tự bỏ qua.

### 6.2. RAM của logger sau khi sửa (2026-11-07, luồng SYNTHETIC)

Luồng theo nhịp V1 (ECG 512 Hz, ba khe PPG 200 Hz, sáu kênh IMU 100 Hz, khoảng 114 packet/s),
`record --source-file` trên Windows. Trong lúc ghi, bộ nhớ không tăng theo độ dài buổi (khoảng
2 MB sau 120 phút dữ liệu sạch). Phần giải mã cuối buổi vẫn tăng theo số packet:

| Buổi | Packet | Đỉnh RAM | Thời gian |
| --- | --- | --- | --- |
| 30 phút | 205.024 | 254 MB | 10 s |
| 75 phút | 512.554 | 598 MB | 25 s |
| 120 phút | 820.084 | 921–936 MB (hai lần đo) | 40–42 s |

Trước khi sửa, luồng 100.103 packet cần 993 MB (ước khoảng 9 GB cho 120 phút); nay cần 120 MB.
Đây là số đo trên luồng tổng hợp, chưa đo trên laptop dùng cho buổi đo hay với thiết bị thật;
nghiệm thu bằng lần chạy cả hệ 120 phút ở bring-up.

### 6.3. Mô phỏng độ nhạy RQ1 (2026-11-10, chỉ giả định)

Config `rq1_sensitivity_v2.json` (SHA-256 `7f6f0cd8…`), 2.000 nghiên cứu mỗi kịch bản, CI khoảng
bao; chạy trên bản chưa commit, hash của code ghi trong
[report.json](rq1_sensitivity_v2/report.json). Mọi tham số là giả định; số mô hình là kịch bản
tự đặt, không phải ước lượng.

- Cùng số buổi, 2 phiên và 3 phiên mỗi người cho CI gần như bằng nhau (chênh 2–4 %), nên theo
  quy tắc ở SAP mục 9, cách nhiều người hơn được ưu tiên. Bản v1 (percentile) cho 3 phiên lợi
  hơn rõ (7–8 %); kết luận này chốt sau pilot.
- Dải ΔBP và năng lực mô hình cùng quyết định khả năng đạt kết luận chính. Tỷ lệ đạt (mức 95 %,
  từ 15 người):

  | Kịch bản M2 | SBP "benefit" | SBP "strong" | DBP "benefit" | DBP "strong" |
  | --- | --- | --- | --- | --- |
  | Hẹp | 0 % | 3–6 % | 0 % | 2–5 % |
  | Vừa | 3–6 % | 20–66 % | 0–1 % | 10–35 % |
  | Rộng | 38–94 % | 84–100 % | 8–27 % | 54–98 % |

- Cách đọc "giảm ít nhất δ" gần như ngoài tầm (chỉ 8–10 % ở kịch bản SBP rộng, "strong"). Khi
  PAT giúp ở mức vừa, kết quả dễ gặp nhất là "tương đương trong δ": bài báo khi đó phải viết lợi
  ích, nếu có, nhỏ hơn δ, không viết PAT không có tác dụng.
- R3 hiện tại gần như không phân biệt được dải ΔBP (3,7 → 4,5 mmHg khi M2 tăng từ +3 lên +15
  mmHg), nên đề xuất thay bằng P2.

### 6.4. B5 chế độ `inner`, chỉ train (2026-11-07)

`runs/b5_pulsedb_inner/20261107T095840Z/` (ngoài Git), GPU RTX 4050 Laptop, PyTorch
2.6.0+cu124. Phần học 288 người (103.680 đoạn), tập kiểm tra trong 32 người (11.520 đoạn), đều
thuộc train.

| Đầu ra | Epoch tốt nhất / đã chạy | MAE trung bình đều theo người, tập trong | B0 trên cùng 32 người | Thời gian học |
| --- | --- | --- | --- | --- |
| SBP | 16 / 31 | 13,42 mmHg | 14,41 mmHg | 18,7 phút |
| DBP | 6 / 21 | 8,39 mmHg | 9,06 mmHg | 12,5 phút |

Chỉ kiểm mô hình học được với lr của bài. Các MAE này lạc quan vì chính chúng được dùng để chọn
epoch; không so được với B0/B3 trên val. Không đổi điểm nào của định nghĩa sau lần chạy này.

### 6.5. Mô phỏng Holm chung SBP–DBP và Ridge trong LOSO (2026-11-11, chỉ giả định)

Config `rq1_holm_loso_v1.json` (SHA-256 `a2b4aac7…`), 2.000 nghiên cứu mỗi kịch bản, CI khoảng
bao; chạy trên bản chưa commit, hash của code trong [report.json](rq1_holm_loso/report.json),
bảng đầy đủ ở [summary.md](rq1_holm_loso/summary.md). Code và cách đọc đã qua một phản biện độc
lập; theo đó đã thêm nhiễu cho nền đặc trưng, kịch bản một đầu ra không có hiệu ứng, θ lấy từ
mô phỏng riêng 20.000 nghiên cứu, và phép xáo cột để tách ảnh hưởng của phụ thuộc.

- **Holm:** khi PAT không thêm gì ở cả hai đầu ra, cận trên của sai lầm là 1,5–2,8 % (danh nghĩa
  2,5 %); khi chỉ một đầu ra có hiệu ứng, đầu ra kia bị tuyên bố nhầm ≤ 0,6 %. Ví dụ M2 vừa,
  "strong", 25 người × 2 phiên: tuyên bố SBP 26,7 % (một mình 36,6 %), DBP 13,3 %.
- **LOSO:** tương quan d giữa hai người gần 0 và sai số chuẩn không bị đánh giá thấp (tỷ số
  0,82–1,03), nhưng trung bình d của mỗi nghiên cứu lệch trái. CI khoảng bao nằm hẳn dưới θ ở
  0,4–2,1 % nghiên cứu (phía kết luận nhầm là PAT có lợi, trong mức 2,5 %), nằm hẳn trên θ ở
  0,6–8,1 % (đánh giá thấp lợi ích). Xáo cột đưa cả hai phía về khoảng 1–3 %, nên phần trượt
  thêm là do các mô hình LOSO học trên gần cùng tập người. Percentile và BCa trượt phía dưới tới
  3,8 % và 4,3 %, nên giữ khoảng bao; SAP ghi độ phủ hai phía khoảng 92–95 % là giới hạn.

## 7. Mốc đóng Tuần 7 và việc chuyển sang Tuần 8

Đánh giá ngày 2026-11-11 theo mục "Mốc đóng tuần" của
[kế hoạch Tuần 7](../../../docs/plans/WEEK_07.md).

| Mốc đóng tuần | Trạng thái | Người xử lý | Chuyển sang |
| --- | --- | --- | --- |
| Mọi đơn có ngày giao | **Chưa:** nơi bán, ngày giao, mã đơn chưa ghi | Đức Anh | Tuần 8, trước khi hàng về |
| Chuẩn bị bring-up, tiêu chí dòng rò và VLED | **Đạt phần viết** (chờ duyệt): checklist, kế hoạch dòng rò/nhiệt/VLED, tiêu chí đồng bộ A1–A9. Giới hạn IEC 60601-1 chưa đối chiếu nguyên văn; chưa có người có chuyên môn duyệt | Đức Anh | Tuần 8: đối chiếu IEC, tìm người duyệt; bring-up khi hàng về |
| Logger qua các test mới | **Đạt trên máy tính:** ghi theo dòng, hiển thị khi đang ghi, hạn `MARK_EVENT`, RAM đo lại (mục 6.2). Chưa chạy với thiết bị | Linh | Bring-up: chạy 120 phút cả hệ |
| B5 trên val trong bảng tổng hợp | **Chưa:** định nghĩa, code, test, lần chạy `inner` và review rò rỉ (2026-11-11) có; chờ commit duyệt rồi chạy val | Linh, Huy (review) | Khi có commit duyệt |
| SQI v1 và SAP v1 có commit | **Đạt một phần:** có commit, chờ thầy duyệt; hai mô phỏng còn thiếu đã chạy 2026-11-11; còn quyết định baseline mạnh hơn zero-change (mục 5.1) | Huy | Tuần 8 và trước pilot |
| Kết quả `gate` lần 1 | **Chưa:** phiên 2026-10-25 bị bỏ, lần 1 bắt đầu lại từ 0/80 đoạn | Huy | Tuần 8: xong 80 đoạn; lần 2 (16 đoạn) sau ít nhất 2 ngày; rồi `gate` |
| Biên bản gặp thầy | **Chưa có biên bản:** ngày 2026-11-10 thầy cho biết hồ sơ đạo đức chưa cần làm gấp; các đề xuất 2.1–2.8 chưa có trả lời ghi lại | Huy | Tuần 8: ghi biên bản và các mục đã chốt |

**Đường găng** vẫn là phần cứng: hàng dự kiến về Tuần 8 nhưng chưa ghi ngày giao, nên chưa xếp
được ngày cho bring-up, đo đồng bộ, đo dòng rò và G2. Chưa có phê duyệt đạo đức nên chưa có dữ
liệu người, và do đó chưa có kết quả RQ1; các việc không phụ thuộc phê duyệt (B5, SAP, mô phỏng,
bring-up trên bàn) tiếp tục.
