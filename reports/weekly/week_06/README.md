# Báo cáo tiến độ Tuần 6

> **Giai đoạn:** Tuần 6 / 28 tuần (2026-10-26 → 2026-11-01; các việc còn lại hoàn thiện
> ngày 2026-11-07, mục 3 "Hoàn thiện ngày 2026-11-07")
>
> **Thành viên:** Linh, Trương Đức Anh, Nguyễn Đức Huy

## 1. Tóm tắt công việc của tuần (mục tiêu)

Theo [kế hoạch Tuần 6](../../../docs/plans/WEEK_06.md) (bảng "Việc còn lại thật" của mục
cập nhật 2026-10-29):

1. Phần cứng là đường găng: đặt nốt module, nhận PCB V1 và bo Waveshare, bring-up khi có hàng.
2. Firmware không cần bo: sự kiện mã 2/4 bằng lệnh `MARK_EVENT`, quy trình chỉnh và khóa dòng
   LED theo người.
3. Theo dõi thí nghiệm và lần chạy nhiều seed (chỉ kiểm tính tất định).
4. Duyệt rồi chạy B2 trên val; đăng ký trước cách chấm test/CalFree.
5. Đánh dấu tay 80 + 16 đoạn rồi chạy `gate`.
6. Hồ sơ đạo đức: thiết kế nghiên cứu (protocol v0.3), các file hồ sơ, mang tới thầy.

Không đo trên người.

## 2. Thành viên phụ trách và phân công công việc

| Thành viên | Công việc Tuần 6 |
| --- | --- |
| Linh | Theo dõi thí nghiệm, bảng nhiều seed; logger với bo Waveshare khi nhận hàng |
| Phần cứng và firmware | Đặt module, PCB V1; `MARK_EVENT`, logger v3, env `all_real`; ước lượng dòng; bring-up khi có hàng |
| Huy | Hồ sơ đạo đức và protocol v0.3; RQ v0.4 và tổng quan tài liệu; duyệt và chạy B2; đánh dấu tay và `gate` |

## 3. Tóm tắt công việc đã hoàn thành

### Phần cứng và firmware

- KiCad V1-draft5 (9a10274, 2026-10-28): bo MCU Waveshare ESP32-S3-DEV-KIT-N8R8-M, footprint
  đối chiếu với file CAD và bản vẽ của nhà sản xuất, lưu ý lắp ráp. ERC/DRC chạy lại ngày
  2026-11-07 bằng KiCad 10: 0 lỗi ở cả hai bo (mục 6.2).
- Đặt hàng: bo Waveshare đặt 2026-10-27; PCB V1 đặt ở CXT từ 2026-10-28, 5 tấm mỗi mạch. Ngày
  2026-11-07 nhóm báo đã đặt đủ các đơn còn lại (DigiKey, kit MAX30001, điện cực, cáp); nơi bán,
  ngày giao và mã đơn chưa ghi vào
  [danh sách mua](../../../hardware/bom/purchase_list_v1_module.md). Gói Gerber gửi CXT chưa
  có commit và SHA-256.
- Firmware và logger (e7336ea, 2026-10-29): lệnh `MARK_EVENT` (CMD_ID `0x03`) phát sự kiện mã
  2 `CUFF_END` và mã 4 từ PC; PC chặn mã LED > `0x7F` và chờ `SET_PPG_LED` 2,5 s, ghi
  `late_ack`; `packet-logger-v3` với metadata phiên `packet-session-metadata-v1` (`subject_id`,
  `session_id`, `ppg_led_lock`, `cuff_log`), dữ liệu người chỉ ghi vào
  `data/raw/<subject>/<session>/`; env `esp32s3_devkitc_all_real`. Test trên máy tính, chưa
  chạy trên chip.
- [Ước lượng dòng](../../../configs/hardware/power_budget_v1.md) theo bo Waveshare
  (2026-10-29); dòng hub CH334 và `bMaxPower` chờ bo thật. Ngày 2026-11-07 nâng lần chạy cả hệ
  ở [bring-up](../../../hardware/test_reports/v1_bringup_procedure.md) mục 8 bước 9 từ 75 lên
  120 phút, bằng buổi đo dài nhất trong hồ sơ đạo đức.

### Linh: theo dõi thí nghiệm

- Hoàn thiện ngày 2026-11-07 (69089de): mỗi `report.json` của runner thành dòng truy vết được
  (commit, hash config/raw/split, seed, metrics và CI), bảng tổng hợp sinh tự động trong
  `runs/registry/`, quy ước tên thí nghiệm và artifact, và lần chạy B3 ba seed kiểm tính tất
  định ([hướng dẫn](../../../docs/protocol/experiment_tracking.md)). Không thêm dependency.
  Kết quả ở mục 6.4.
- Logger với bo Waveshare: chờ nhận hàng.

### Huy

- **Thiết kế nghiên cứu và hồ sơ đạo đức:**
  - Protocol v0.3 (8e32b06, 2026-10-29): M0–M2 (bỏ M3, M4), endpoint RQ1, LOSO lồng, 3 phiên
    (tối thiểu 2) trong 4 tuần; trần tuyển 35, mục tiêu ≥ 25 người đạt chuẩn và luật dừng
    tuyển (7234430, 2026-10-30).
  - Hồ sơ đạo đức viết lại sau rà soát cuối (a946373, 2026-10-31): đơn đề nghị, đề cương nộp
    hội đồng, phiếu thông tin, phiếu đồng thuận, sàng lọc, phiếu ghi buổi đo, an toàn và quy
    tắc dừng, quản lý dữ liệu, thông báo tuyển; bộ Word gửi thầy ngày 2026-10-31. Chưa nộp
    ([README hồ sơ](../../../docs/ethics/README.md), mục "Còn thiếu trước khi nộp").
  - Đề xuất sửa protocol và hồ sơ cho buổi gặp thầy Tuần 7
    ([đề xuất](../../../docs/meetings/week_07_de_xuat_sua_protocol_va_ho_so.md)).
- **RQ v0.4 và tổng quan tài liệu** (f7803c5, 862ade6, 71b648f): estimand RQ1, tiêu chí kết
  luận có CI cho cả phép so với zero-change, δ, đa kiểm định; tra có hệ thống ngày 2026-10-29,
  đọc toàn văn N6 và S4; khoảng trống của RQ1 hẹp lại.
- **Mốc tay Tuần 5** (6511926): `compare` từ chối mốc tay trên val, `gate` chỉ nhận dòng
  train. Đánh dấu tay lần 1 mới xong 28/80 đoạn (phiên dở ngày 2026-10-25), nên chưa chạy
  `gate` và B4 vẫn bị chặn.
- **B2:** định nghĩa được review trước khi có số (hai review độc lập, 2026-11-07), sửa năm điểm
  (19fc432), duyệt nguyên trạng bằng commit riêng (1c708df). v0 dừng đúng chốt kiểm trước khi
  fit; v1 chỉ đổi quy tắc nhân khẩu học (450302b), duyệt bằng commit riêng (a215f07), chạy trên
  val ngày 2026-11-07 (mục 6.5).

### Review cuối tuần (2026-11-07)

Toàn bộ 16 commit của tuần được review hai vòng (chờ duyệt). Các lỗi tài liệu đã sửa
(c1c4b48):

- an toàn buổi đo mục 8: bản trước cho ép tim cả khi người tham gia chưa tỉnh nhưng vẫn thở
  bình thường; nay tách ba nhánh. Mục 6 thêm cách xử lý khi BP ≥ 180/110 có và không có triệu
  chứng (chờ đầu mối y tế duyệt);
- quyền xóa sau mốc khóa và trần tiêu hủy 05 năm thống nhất giữa phiếu thông tin, đề cương
  và DMP;
- "người đạt chuẩn" không tính phiên phải chỉnh lại LED; kịch bản bài báo dùng CI sau hiệu
  chỉnh đa kiểm định;
- N6: chỉ hai trong ba mô hình "PTT" dùng PAT (đối chiếu bản PDF); Koba 2004; lưu ý hai số
  đọc từ hình của S4.

Bộ Word hồ sơ ngày 2026-10-31 phải dựng lại theo các file nguồn đã sửa.

## 4. Danh mục sản phẩm đầu ra và đường dẫn

| Sản phẩm | Đường dẫn |
| --- | --- |
| KiCad V1-draft5 | `hardware/kicad/v1_module/` |
| Danh sách mua và trạng thái đơn | [purchase_list_v1_module.md](../../../hardware/bom/purchase_list_v1_module.md) |
| Packet Schema V0.2 mục 13 (`MARK_EVENT`) | [Packet_Schema_V0.2.md](../../../configs/hardware/Packet_Schema_V0.2.md) |
| Logger v3, metadata phiên v1 | [packet_logger.md](../../../docs/protocol/packet_logger.md) |
| Protocol v0.3 | [protocol_outline_v0.2.md](../../../docs/protocol/protocol_outline_v0.2.md) |
| Hồ sơ đạo đức | [docs/ethics/](../../../docs/ethics/README.md) |
| RQ v0.4 | [research_questions_v0.1.md](../../../docs/research_questions_v0.1.md) |
| Tổng quan tài liệu 2026-10-29 | [literature_update_2026-10-29.md](../../../docs/literature/literature_update_2026-10-29.md) |
| Đăng ký trước cách chấm test | [pulsedb_test_scoring_preregistration.md](../../../docs/protocol/pulsedb_test_scoring_preregistration.md) |
| Định nghĩa B2 (đã duyệt) | [b2_pulsedb_definition.md](../../../docs/protocol/b2_pulsedb_definition.md) |
| Theo dõi thí nghiệm | [experiment_tracking.md](../../../docs/protocol/experiment_tracking.md) |
| Bảng và report B2 v1 trên val | [pulsedb_b2_v1/](pulsedb_b2_v1/README.md) |
| Bảng nhiều seed và bảng tổng hợp | [experiment_tracking/](experiment_tracking/README.md) |

## 5. Tóm tắt các nội dung chuyên môn chính

### 5.1. Hồ sơ đạo đức chưa nộp được

Điều kiện nộp ở kế hoạch Tuần 6 chưa đủ: thầy chưa trả lời các mục "đề xuất của nhóm, chờ
thầy"; chưa có model máy cuff, đầu mối y tế, nguồn chi trả khi có tổn hại; chưa biết hội đồng
có cần biên bản đo dòng rò trên bo thật trước khi nộp hay không. Nếu cần biên bản thì sớm nhất
nộp khoảng Tuần 9–10 ([đề xuất Tuần 7](../../../docs/meetings/week_07_de_xuat_sua_protocol_va_ho_so.md)).

### 5.2. Phát hiện kỹ thuật cần sửa trước khi đo trên người

Từ review ngày 2026-11-07, chuyển sang Tuần 7:

- Logger giữ mọi packet trong RAM rồi giải mã lại ở cuối buổi (mục 6.3).
- Quy trình chỉnh LED ở protocol 6.1 cần đọc mức DC (% thang đo) khi đang ghi, nhưng chưa có
  công cụ; việc so `0xD2` với mã đã khóa chỉ chạy sau buổi; kết quả lệnh chỉ nằm trong
  `commands_sent.jsonl`.
- `MARK_EVENT` có thể bị trễ vài giây nếu xếp hàng sau một `SET_PPG_LED` mất ACK.
- Tiêu chí nghiệm thu VLED (4,5–5,0 V) chưa có quy tắc cho mức danh định 5,1 V.

## 6. Kết quả kiểm tra kỹ thuật

### 6.1. Kiểm tra toàn repo

Ngày 2026-11-07 trên nhánh review (sau mọi commit của mục 3): `ruff check .` sạch;
`pytest -q` 1.076 đạt, 1 bỏ qua (tạo symlink cần quyền trên Windows), test firmware chạy bằng
trình dịch C `ziglang`; `scripts/check_environment.py` và `pip check` đạt. Trước các sửa đổi
ngày 2026-11-07, ở a946373: 1.058 đạt, 1 bỏ qua.

### 6.2. ERC/DRC KiCad V1-draft5 (chạy lại 2026-11-07)

KiCad 10 `kicad-cli`, trên 9a10274: ERC 0 lỗi ở cả hai bo (cảnh báo chỉ vì thư viện `ppg_v1`
không nằm trong repo); DRC 0 lỗi, 0 pad chưa nối, 0 lỗi footprint, schematic khớp PCB. Bo cổ
tay có 21 cảnh báo courtyard đã ghi là dự kiến
([custom_board_proposal.md](../../../configs/hardware/custom_board_proposal.md)).

### 6.3. RAM của logger trên luồng SYNTHETIC (2026-11-07)

Luồng SYNTHETIC lớn nhất mà simulator cho phép (10.000 packet mỗi kênh: ECG 512 Hz, ba khe
PPG 200 Hz, sáu kênh IMU 100 Hz; 1,4 triệu dòng mẫu, 100.103 packet), ghi bằng
`packet_logger.py record` từ file trên Windows: đỉnh working set khoảng 993 MB. Ngoại suy
tuyến tính theo số mẫu, ước lượng thô: khoảng 2 / 5,5 / 9 GB cho buổi 30 / 75 / 120 phút.
`raw.bin` được ghi dần nên không mất, nhưng file đầu ra, manifest và `replay` có thể không
chạy xong trên laptop đo. Đây là một điểm đo, payload ngẫu nhiên, không phải số đo trên thiết
bị; phải sửa và nghiệm thu bằng lần chạy cả hệ 120 phút trước G2.

### 6.4. B3 nhiều seed trên val (kiểm tính tất định)

`scripts/run_b3_multiseed.py`, seed 42, 43, 44, config `b3_pulsedb_v1.json` chỉ khác
`b3.seed`, cùng split v2 và seed bootstrap; commit `1c708df`, worktree sạch. Kết quả
**DETERMINISTIC**: dự đoán val trùng từng byte ở ba seed, mọi metrics điểm có SD = 0 và trùng
số B3 của Tuần 5 (MAE trung bình đều theo người SBP 14,58, DBP 10,12 mmHg; B0 15,11 và 10,40).
Đúng như dự kiến vì B3 v1 không lấy mẫu con; độ bất định của B3 là CI bootstrap theo người.
Bảng tổng hợp sinh tự động có 5 lần chạy, 30 dòng, không lần chạy nào bị bỏ qua. Chi tiết và
hash: [experiment_tracking/](experiment_tracking/README.md).

### 6.5. B2 trên PulseDB Train 400 người, val (2026-11-07)

B2 v1 (nhân khẩu học theo từng đoạn), duyệt nguyên trạng bằng commit riêng `a215f07` rồi mới
chạy; report ghi `approval_committed` đủ ba phần (config, định nghĩa, mã), worktree sạch. Val
40 người, 14.400 đoạn; MAE/bias trung bình đều theo người, CI 95% bootstrap theo người (2.000
lượt, seed 20261013). HR đo được ở 14.376/14.400 đoạn val, không người nào mất hẳn HR. Chi tiết
và hash: [pulsedb_b2_v1/](pulsedb_b2_v1/README.md).

| Bảng | Model | SBP MAE [CI 95%] | DBP MAE [CI 95%] |
| --- | --- | --- | --- |
| `full` | B0 | 15,11 [13,47; 16,88] | 10,40 [9,12; 11,80] |
| `full` | B2a | 16,40 [14,26; 18,88] | 11,15 [9,61; 12,97] |
| `full` | B3 | 14,58 [12,89; 16,49] | 10,12 [8,94; 11,44] |
| `hr_available` | B2a | 16,46 [14,35; 18,90] | 10,83 [9,26; 12,57] |
| `hr_available` | B2b | 16,51 [14,39; 18,73] | 10,82 [9,33; 12,67] |
| `hr_available` | B3 | 14,57 [12,87; 16,47] | 10,14 [8,97; 11,46] |

Hiệu ghép cặp định trước (mmHg, âm là sai số thấp hơn):

- B2a − B0 (`full`): SBP +1,29 [−0,39; 3,07], DBP +0,74 [−0,81; 2,30]: với cấu hình
  này chưa thấy B2a tốt hơn trung bình train (CI chứa 0).
- B2b − B2a (`hr_available`): SBP +0,05 [−0,89; 1,09], DBP −0,01 [−0,61; 0,61]: chưa thấy
  ước lượng HR thêm thông tin (CI chứa 0; bộ dò R chưa qua cổng nghiệm thu). Sửa câu chữ
  2026-11-10: bản trước ghi "không thêm gì", trong khi chưa có biên tương đương định trước.
- B3 − B2a (`full`): SBP −1,82 [−3,52; −0,07], DBP −1,03 [−2,70; 0,66]; B3 − B2b
  (`hr_available`): SBP −1,94 [−3,76; −0,18], DBP −0,68 [−2,21; 0,91]. Đây là so hai bộ đặc
  trưng khác nhau, không phải phần lợi thêm của dạng sóng so với nhân khẩu học.

Trước đó, B2 v0 (duyệt `1c708df`) dừng đúng chốt kiểm "nhân khẩu học khác nhau trong một
người" trước khi fit, nên không có số. Chẩn đoán chỉ trên train: 4/320 người có hai bộ giá trị
(tuổi lệch ≤ 1 năm, cân nặng ≤ 2,1 kg); v1 dùng giá trị của từng đoạn
([định nghĩa](../../../docs/protocol/b2_pulsedb_definition.md) mục 9). Nhãn là ABP công khai
của bệnh nhân gây mê, không phải cuff; test split và CalFree chưa chấm.

## 7. Mốc đóng Tuần 6 và việc chuyển sang Tuần 7

Đánh giá ngày 2026-11-07 theo mục "Mốc đóng tuần" của
[kế hoạch Tuần 6](../../../docs/plans/WEEK_06.md).

| Mốc đóng tuần | Trạng thái | Người xử lý | Chuyển sang |
| --- | --- | --- | --- |
| Module và PCB đã đặt, có ngày giao | **Đạt một phần:** mọi đơn đã đặt (báo 2026-11-07); chưa ghi ngày giao, mã đơn, nơi bán; Gerber gửi CXT chưa có commit/SHA-256 | Phần cứng | Tuần 7: ghi đủ đơn và ngày giao; bring-up khi nhận hàng |
| Hồ sơ đạo đức đã nộp, hoặc đã báo giám sát viên | **Chưa nộp;** bộ Word đã gửi thầy 2026-10-31; điều kiện nộp chưa đủ (mục 5.1) | Huy | Tuần 7: gặp thầy; nộp khi đủ điều kiện |
| B2 trên val có CI | **Đạt:** B2 v1 trên val có CI (mục 6.5); v0 dừng trước khi fit, không có số | Huy | — |
| Bảng nhiều seed sinh tự động | **Đạt:** bảng tổng hợp và bảng nhiều seed sinh tự động; B3 `DETERMINISTIC` (mục 6.4) | Linh | — |
| Kết quả cổng mốc lần 1 | **Chưa:** đánh dấu tay 28/80 đoạn | Huy | Tuần 7: xong 80 đoạn; lần 2 (16 đoạn) sau ít nhất 2 ngày; rồi `gate` |
| Lệnh PC→thiết bị, packet cấu hình AFE, sự kiện mã 3 có test | Đạt trên máy tính (từ Tuần 5; `MARK_EVENT` thêm 2026-10-29). Chưa chạy trên chip | Phần cứng và firmware | Khi bring-up |

**Đường găng** vẫn là phần cứng: chưa có ngày giao của module và PCB, nên chưa xếp được tuần
cho bring-up, đo đồng bộ 10 phút, đo dòng rò và G2 (thu liên tục 30 phút trên 3 người, kế
hoạch 28 tuần Tuần 5–8).
