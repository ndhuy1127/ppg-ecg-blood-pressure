# Báo cáo tiến độ Tuần 5 — phần Huy

> **Giai đoạn:** Tuần 5 / 28 tuần
>
> **Người tổng hợp:** Nguyễn Đức Huy
>
> **Ngày cập nhật:** 2026-10-21; sửa 2026-10-22 theo review độc lập (mục 8)
>
> **Nhánh/commit nền:** dev/huy @ 3ff44f2; thay đổi Tuần 5 commit trên `dev/huy` ngày 2026-10-22, sau review
>
> **Trạng thái:**
> - Mục 1–4 và 6 có đầu ra. Mục 5 (đánh giá B0/B3) bị chặn chờ Linh.
> - G1 phần mềm gần đạt, G1 phần cứng chưa đạt.
> - Hồ sơ đạo đức là bản nháp, chưa nộp.
> - Phân bổ tay/điện cực chờ Đức Anh xác nhận. Chưa đo trên người.
> - Hai tiêu chí nghiệm thu của mục 2 và 3 trong WEEK_05 **chưa đạt**: chưa có câu
>   trả lời của thầy, chưa có xác nhận của Đức Anh.

## 1. Mục tiêu và phạm vi

Theo hàng "Huy" của [WEEK_05.md](../../../docs/plans/WEEK_05.md): (1) trạng thái
G1 và kế hoạch khắc phục; (2) hồ sơ đạo đức; (3) phân bổ tay/điện cực và nghiệm
pháp; (4) mốc R/foot thứ hai, PAT hợp lệ, so với đánh dấu tay; (5) đánh giá B0/B3;
(6) phác thảo P A/P B/P C. Không làm thay việc của Linh (logger, B0/B3 trên raw)
hay Đức Anh (mua module, A.6, ERC/DRC, firmware). Không sửa
`hardware/kicad/v1_module/wrist/v1_wrist.kicad_pro` (thay đổi có trước, không
thuộc việc này). Push và PR theo quyết định của nhóm.

**Đầu vào đã kiểm 2026-10-21** sau `git fetch origin`: `origin/dev/ducanh` mới
nhất `9073aa8` (2026-10-14), `origin/dev/ngoclinh` mới nhất `acc8b8b`
(2026-10-17), `origin/develop` `c23e2e0`. Khi đó chưa có bàn giao Tuần 5 nào của
Linh hay Đức Anh.

**Kiểm lại 2026-10-22:**

- `origin/dev/ducanh` mới nhất là `1e95d29` "Them danh sach mua" (2026-10-21
  23:06), chỉ thêm `hardware/bom/Danh sách mua.xlsx`.
  - Danh sách liệt kê ESP32-S3-DevKitC-1 N16R8, MAX30001, BMI270, điện cực 3M
    Red Dot 2228, điện cực khô BIOPAC và FSR 402, kèm phương án thay thế và link.
  - Chưa có giá, ngày giao hay dấu hiệu đã duyệt/đặt.
  - **Không có module PPG**: dòng "PPG AFE" ghi BMI270.
- `origin/dev/ngoclinh` vẫn ở `acc8b8b`.
- Linh có bản nháp Tuần 5 (logger, mô phỏng v3, `linh.md`), lúc đó chưa commit và
  chưa có trên remote. Ngày 2026-10-22, bản đã sửa theo review được commit trên
  `dev/huy`.

## 2. Trạng thái G1

G1 theo kế hoạch 28 tuần (tài liệu ngoài repo): *pipeline tái lập; split theo
người có test; baseline đầu tiên; PPG–ECG đồng bộ và báo cáo v0*. Thời điểm cổng
gốc là Tuần 4; đánh giá lại ngày 2026-10-21.

| Hạng mục | Trạng thái | Bằng chứng |
| --- | --- | --- |
| Pipeline tái lập (reader, inventory, provenance) | **Có** | `software/pulsedb/reader.py` (`6ad1954`), `software/data_io/split_manifest.py` (split v2 từ `6c3c210`, làm chặt ở `96c8d7a`), hash không phụ thuộc CRLF (`dbd8c5a`), runner kiểm bàn giao split (`d4b7a2b`) |
| Split theo người có test rò rỉ | **Có** | `pulsedb-split-v2`, `tests/test_split_manifest.py`; pytest cục bộ 379 passed sau sửa đổi 2026-10-22 (mục 5) |
| Baseline đầu tiên | **Gần đạt** | B0/B1/metrics (`9f0ab5b`), B3 + runner split v2 (`937205e`, `36649de`), test SYNTHETIC. **Chưa chạy B0/B3 trên raw PulseDB thật**: không có `runs/b3_pulsedb/` (kiểm 2026-10-21). Chờ Linh |
| Đặc trưng/SQI/bootstrap | **Có** (SYNTHETIC) | `features-sqi-v1` (`645df5d`), `subject_bootstrap.py`; mốc thứ hai Tuần 5 (mục 3.4) |
| PPG–ECG đồng bộ, báo cáo phần cứng v0 | **Chưa đạt** | Chưa mua module; `firmware/` chỉ có `README.md` và `.gitkeep`; `hardware/test_reports/` chỉ có kế hoạch đo 10 phút (`sync_10min_test_plan.md`, "chưa thực hiện"). Có thiết kế KiCad V1-module (`1dc0eba`, `e6ca81b`) |
| Hồ sơ đạo đức | **Bản nháp** | Mục 3.2; chưa nộp |

**Kết luận:** G1 phần mềm **gần đạt** (còn B0/B3 trên raw thật, Linh). G1 phần
cứng **chưa đạt** (chưa có module, firmware, bản ghi bench). Không đánh dấu G1 đạt.

**Kế hoạch khắc phục** (theo [WEEK_05.md](../../../docs/plans/WEEK_05.md), người
xử lý ghi theo kế hoạch, chưa có cập nhật tiến độ của họ):

| Việc | Người | Mốc kiểm | Trạng thái 2026-10-21 |
| --- | --- | --- | --- |
| Chốt `pool_decision` (VitalDB_AAMI_Cal_Subset trùng người với AAMI Test), tạo split v2 từ raw, chạy `run_b3_pulsedb.py`, bàn giao bảng dự đoán val | Linh (pool: Linh + Huy) | Bảng B0/B3 val có provenance | Chưa có; **pool chưa chốt** |
| Logger phía máy tính, generator đủ trường | Linh | Test 5 lỗi + CRC | 2026-10-22: sửa theo review và commit trên `dev/huy` (decoder, logger, mô phỏng v3, 13 case); chưa có review của Đức Anh |
| Danh sách mua và đặt module Phần A | Đức Anh | Đơn đã đặt, ngày giao | 2026-10-22: có danh sách (`1e95d29`), chưa giá, ngày giao hay duyệt; **thiếu module PPG MAX30101** |
| Đóng A.6, một pin map chuẩn | Đức Anh | A.6 không còn điểm mở | Chưa có. `Pin_Map_V1.md` còn ghi MAX30102, trong khi nhóm đã chọn MAX30101 (2026-10-22) |
| ERC/DRC V1-module | Đức Anh | Log ERC/DRC | Chưa có |
| Firmware khung DevKitC gửi packet | Đức Anh | Logger đọc packet MCU 10 phút | Chưa có |
| Phần Huy (mục 3) | Huy | Báo cáo này | Có đầu ra, chờ review |

Phần nào chưa đạt ở cuối tuần chuyển sang Tuần 6 với cùng người xử lý; hoãn tiếp
cần quyết định ghi vào báo cáo Tuần 6.

## 3. Việc đã làm

### 3.1. Nhật ký quyết định (ngày ghi là bằng chứng khóa trước khi xem dữ liệu)

Không có dữ liệu PulseDB raw hay dữ liệu người trên máy khi ra các quyết định này
(kiểm 2026-10-21). Bằng chứng Git: các commit Tuần 5 trên `dev/huy` ngày 2026-10-22.

| Ngày | Quyết định | Ai | Nơi ghi |
| --- | --- | --- | --- |
| 2026-10-21 | Output mặc định `features-sqi-v1` không đổi; phương pháp mốc mới chỉ chọn qua `SignalConfig`; `extract_window` từ chối phương pháp khác mặc định | Huy | `fiducials.py`, `week04.py` |
| 2026-10-21 | PAT hợp lệ: 80–400 ms, MAD k = 3, sàn 10 ms, tối thiểu 3 cặp; không loại theo BP | Huy, `NOT_TEST_TUNED` | `configs/data/week05_huy.json` |
| 2026-10-21 | Dung sai so khớp với đánh dấu tay: R 50 ms, foot 100 ms (chốt trước khi đánh dấu) | Huy | Như trên |
| 2026-10-21 | Phân bổ tay phương án A (PPG cổ tay trái, cuff bắp tay phải, ECG cổ tay trái – ngón trỏ phải) | Huy **đề xuất**, chờ Đức Anh | Protocol v0.2 mục 5 |
| 2026-10-21 | Nghiệm pháp M1–M4 (thở chậm, tính nhẩm, ngâm chân nước lạnh, đạp xe ngồi) | Huy **đề xuất**, chờ thầy/hội đồng và Đức Anh | Protocol v0.2 mục 6.4 |
| 2026-10-21 | Loại nghiệm pháp bóp tay tĩnh (M5) và đổi tư thế vì xung đột tay đeo PPG/điện cực | Huy, chờ Đức Anh | Protocol v0.2 mục 5.4, 6.4 |
| 2026-10-21 | Tiêu chí biên độ ΔBP pilot P1–P4 | Huy **đề xuất, khóa trước pilot** | Protocol v0.2 mục 6.5 |
| 2026-10-22 | Module PPG là **MAX30101** (SparkFun SEN-16474) | Huy xác nhận (nhóm đã chọn) | Protocol v0.2 mục 5.1; Đức Anh cập nhật pin map, BOM, danh sách mua |
| 2026-10-22 | `pat_beats` ghép R–foot trong khoảng R–R (`pair_between_r`) rồi mới gắn nhãn; 80–400 ms không còn là cổng ghép | Huy (sửa lỗi review C1) | `pat_validity.py`, tài liệu Tuần 5 mục 3 |
| 2026-10-22 | `compare` chỉ chạy với đúng config mà `detect` đã dùng | Huy (sửa lỗi review C2) | `week05_fiducials.py`, tài liệu Tuần 5 mục 4 |
| — | `pool_decision` PulseDB | **Chưa quyết**, Linh + Huy | — |
| — | Các điểm chờ quyết định ở mục 8.2 | **Chưa quyết** | Mục 8.2 |

### 3.2. Hồ sơ đạo đức (mục 2)

Bộ bản nháp trong `docs/ethics/` mô tả V1-module theo đề xuất Phần A:

- bo cổ tay MAX30101/BMI270 gắn velcro; MAX30101 là module nhóm đã chọn, Huy xác
  nhận 2026-10-22;
- cáp dẹt tới bo đế ESP32-S3 + MAX30001;
- USB tới laptop chạy pin, rút sạc;
- điện cực dán Ag/AgCl đạo trình I (cổ tay và ngón tay);
- cuff bắp tay phải.

**Còn chờ** (đã đánh dấu `[...]` trong phiếu):

- số điện cực: hai, hoặc ba nếu cần bias;
- điện cực khô dùng trên người hay chỉ bench;
- bên tay theo phân bổ được Đức Anh xác nhận;
- cách trả lời trong M2.

- Phiếu thông tin: `participant_information_sheet_v0.1.md`
- Phiếu đồng thuận, mẫu trống: `consent_form_v0.1.md`
- Tiêu chuẩn chọn/loại L1–L10 và phiếu sàng lọc: `eligibility_screening_v0.1.md`
- An toàn buổi đo, quy tắc dừng, nhật ký sự cố: `session_safety_stopping_v0.1.md`
- Quản lý và giả danh hóa dữ liệu: `data_management_plan_v0.1.md`
- Danh mục cập nhật: `docs/ethics/README.md`

Sửa mâu thuẫn trong `ethics_outline_v0.1.md`: v0.1 cấm nối máy tính khi đeo, còn
V1-module nối USB với laptop; đã thêm ghi chú ngày 2026-10-21 (với V1: không có
đường nào nối người tham gia với điện lưới). Con số LED "< 15 mW" trong v0.1 được
ghi là **chưa có nguồn**. Ngưỡng BP dừng phiên (SBP > 180 / DBP > 110 trong v0.1)
cũng **chưa có nguồn**, để chờ thầy/hội đồng.

Ngày 2026-10-22, outline có thêm bảng các chỗ đã cũ hoặc mâu thuẫn với 5 file
mới, như chạm ngón tay vào điện cực, 20–30 phút, xóa toàn bộ dữ liệu khi rút lui
và câu tự phân loại "minimal risk". Khi khác nhau thì theo 5 file. Hồ sơ **chưa đủ
để nộp** cho tới khi có câu trả lời ở mục 3.7, biên bản đo dòng rò trên bo thật và
các mục còn thiếu ở `docs/ethics/README.md`.

### 3.3. Phân bổ tay/điện cực và nghiệm pháp (mục 3) — **chờ Đức Anh xác nhận**

`docs/protocol/protocol_outline_v0.2.md` (changelog ở đầu file; v0.1 giữ làm
lịch sử, có dòng trỏ sang v0.2).

- 5.2: bảng phân bổ phương án A và dự phòng B; bảng chi dùng cho từng nghiệm pháp.
- 5.4: kiểm tra xung đột trên giấy. Quy tắc đổi tên thành K1–K6 ngày 2026-10-22
  để không trùng R2/R3/R5 của kế hoạch 28 tuần.
  - **K1** (cuff khác tay PPG): **đạt**.
  - **K2** (không làm chuyển động tay PPG): **đạt trên giấy** cho M0–M2,
    **chưa kiểm chứng** cho M3, **có điều kiện** cho M4.
  - **K3** (tránh nhiễu cơ trên chi gắn điện cực): đạo trình I có điện cực ở cả
    hai tay nên **loại M5 bóp tay**. M3 và lúc cuff bơm **chưa kiểm chứng**; M1,
    M2, M4 **chưa đánh giá**.
  - **K4**: tay đeo cuff luôn mang một điện cực; chưa kiểm chứng.
  - **K5**: chưa kiểm.
  - Kết luận 2026-10-22: **chưa thể nói** phương án A hết xung đột.
- 5.3 và 6.4 ghi rõ hai mâu thuẫn chưa giải quyết: M2 (đo cuff khi đang làm mà
  không được nói) và M4 (cửa sổ 60 s trước cuff rơi vào lúc đang đạp).
- 6.4: các nghiệm pháp và nguồn về hướng thay đổi BP. Nguồn đọc ở mức abstract
  (Europe PMC, 2026-10-21), có DOI trong file; 9/9 DOI đã đối chiếu metadata qua
  OpenAlex/Europe PMC ngày 2026-10-22. Thời lượng/cường độ phần lớn **chưa có
  nguồn**.
  - **M0** nghỉ.
  - **M1** thở chậm: giảm BP (Adler 2019).
  - **M2** tính nhẩm: tăng (Carroll 2012, Jern 1991). Hai nguồn này chỉ **ủng hộ
    gián tiếp**.
  - **M3** nước lạnh ở bàn chân: tăng SBP/DBP (Korhonen 2006, Velasco 1997). Có
    thêm yếu tố nhiễu co mạch ngoại vi.
  - **M4** đạp xe ngồi, đo khi hồi phục: tăng khi gắng sức (Stergiou 2023, trước
    đây ghi "ESH 2023"). Ở pha hồi phục **chưa chắc**: toàn văn Mukkamala 2021 ghi
    BP sau gắng sức có thể thấp hơn trước gắng sức.
  - Bỏ Fu 2002 (nguồn yếu, M5 đã loại).
- 6.5: tiêu chí pilot P1–P4, **đề xuất, khóa trước pilot**.
  - Ngưỡng 15 mmHg lấy từ dấu hiệu R3 của kế hoạch 28 tuần (nội bộ, không phải
    nguồn khoa học).
  - Định nghĩa P2 khác câu trong kịch bản bài báo: **chờ thống nhất**.
- 5.1 khôi phục hai ý của v0.1 bị mất khi viết lại mục 5: Cohen 2025 về sai số
  cuff, và yêu cầu chốt quy trình đo hai tay.

### 3.4. Mốc R/foot thứ hai, PAT hợp lệ, so với đánh dấu tay (mục 4)

Chi tiết: [week05_fiducials_pat_validity.md](../../../docs/protocol/week05_fiducials_pat_validity.md).

- R: thêm `derivative_energy` (đạo hàm bình phương, trung bình trượt, dời về cực
  đại tín hiệu). **Không phải Pan–Tompkins.**
- Foot: thêm `d2_max` và `valley_min`, nội suy parabol dưới một mẫu.
- Chọn qua `SignalConfig(r_method=..., foot_method=...)`. Output mặc định
  `features-sqi-v1` không đổi (so lại 2026-10-22 sau sửa đổi):
  - bảng fixture Tuần 4 tạo lại giống từng byte với blob đã commit của
    `reports/weekly/week_04/fixture_features.csv` (file working copy chỉ khác CRLF);
  - 240 cửa sổ SYNTHETIC × 2 config cho output giống hệt HEAD.
- PAT hợp lệ, giới hạn và outlier MAD: `software/signal_processing/pat_validity.py`.
  - Nhịp không hợp lệ được gắn nhãn, không xóa; không dùng BP.
  - Từ 2026-10-22, ghép R–foot trong khoảng R–R (`pair_between_r`). PAT ngoài
    80–400 ms được ghép rồi gắn `out_of_range`, thay vì biến mất như trước.
- So với đánh dấu tay: `software/evaluation/fiducial_agreement.py`, script
  `scripts/week05_fiducials.py` (synth/export/plot/annotate/detect/compare), mẫu
  CSV trống `docs/protocol/templates/manual_fiducials_template.csv`.
  - Script **không tự sinh nhãn thủ công**; đáp án SYNTHETIC mang annotator riêng
    và bị từ chối nếu không có cờ.
  - Từ 2026-10-22:
    - mọi lệnh ghi provenance;
    - `compare` kiểm cùng config với `detect`;
    - ghép một–một tối ưu;
    - `annotate` không mất buổi đánh dấu khi `--out` đã tồn tại.
- Test có đáp án: nhịp sạch, nhiễu, ngừng nhịp, mất xung PPG, HR 143 bpm, ECG
  125 Hz, nội suy dưới mẫu, PAT ngoài giới hạn, MAD, ghép một–một, chặn split test
  và ghi đè (`tests/test_week05_fiducials.py`, **50 test**; trước sửa đổi là 26).

Hai lỗi phát hiện nhờ test, đã sửa trước khi chốt config:

1. Không có sàn tuyệt đối, nên quy tắc MAD gắn outlier cho PAT gần như hằng chỉ vì
   lượng tử hóa 1 mẫu → thêm `mad_floor_ms`.
2. `agreement` không báo lỗi khi một loại mốc đã đánh dấu tay mà không có phương
   pháp nào chạy → nay báo lỗi.

Các lỗi do review độc lập 2026-10-22 phát hiện và việc đã sửa: mục 8.

### 3.5. Đánh giá B0/B3 (mục 5) — **bị chặn**

Không có `runs/b3_pulsedb/` trên máy (2026-10-21) và chưa có bàn giao trên remote.
**Chờ Linh bàn giao** thư mục output `run_b3_pulsedb.py` (report.json,
predictions_val.csv) cùng split v2 (inventory, manifest, config, report). Không
dùng CSV 1.000 đoạn lịch sử thay thế. Khi có: kiểm provenance (commit, SHA-256
raw/split/config), B0 và B3 cùng tập dòng val và cùng lượt bootstrap, rồi tóm tắt
MAE/bias/SD và CI 95% theo người cho SBP và DBP riêng bằng `evaluate_prediction_table`.

**Sai lệch cần ghi:** bản cũ của pipeline đã chạy và báo MAE trên **test**
(`docs/testing.md`, `notebooks/metrics_all_splits.csv`,
`notebooks/week4-train-xgboost.ipynb`, commit `acc8b8b`). Các số đó không được
dùng để chọn mô hình, đặc trưng hay ngưỡng, và không được trích trong báo cáo.

### 3.6. Kịch bản P A/P B/P C (mục 6)

`docs/paper_scenarios_v0.1.md`: điều kiện kích hoạt theo G4/R2/R3/R5 của kế hoạch
28 tuần, thông điệp chính, RQ trả lời được, bảng/hình chính, phần bỏ. Không tuyên
bố tính mới hay hạng tạp chí.

### 3.7. Câu hỏi cho thầy (chưa có câu trả lời; nhóm không tự trả lời)

1. Hội đồng đạo đức nào xét đề tài này, cần mẫu biểu riêng nào, và thời gian xét
   dự kiến bao lâu?
2. Đo thử trên thành viên nhóm (thu 30 phút trên 3 người cho G2) có cần phê duyệt
   của hội đồng không? Nếu có, có thủ tục rút gọn không?
3. Nhóm có mượn được máy đo huyết áp bắp tay đã được kiểm định/validation, hoặc
   thiết bị đo huyết áp liên tục (ví dụ dạng kẹp ngón) không?
4. Các nghiệm pháp M1–M4 (thở chậm, tính nhẩm, ngâm chân nước lạnh, đạp xe nhẹ
   tư thế ngồi) có được phép đưa vào hồ sơ không? Có cần nhân viên y tế có mặt
   không?
5. Ai quyết định ngưỡng huyết áp dừng phiên và đầu mối y tế khi số đo vượt ngưỡng;
   có thông báo số đo cuff cho người tham gia không?
6. Thời hạn lưu dữ liệu (đề xuất 03 năm sau công bố) và nơi lưu có phù hợp quy
   định của trường không? Có bồi dưỡng người tham gia không?

### 3.8. Câu hỏi cho Đức Anh

1. Xác nhận phân bổ phương án A (protocol v0.2 mục 5.2) hay chọn B; điện cực
   Ag/AgCl loại nào dán được lên ngón tay.
2. Ánh xạ ECGP/ECGN của breakout MAX30001 cho đạo trình I và có cần điện cực
   bias/RLD thứ ba không.
3. Khi có module: thử K3–K5 (nhiễu cơ, ECG lúc cuff bơm ở tay có điện cực, dây
   không kéo bo PPG) trên bench, chưa gắn lên người.
4. Kế hoạch và ngày đo dòng rò trên bo V1 thật; cách đo nhiệt độ bo cổ tay.
5. Đầu nối Qwiic trên bo MAX30101: tháo hay làm giá đỡ để không chạm da (A.3).
6. (2026-10-22) Nhóm đã chọn MAX30101: cập nhật `Pin_Map_V1.md` và `BOM_V1.xlsx`,
   hiện còn ghi MAX30102. Thêm MAX30101 (SEN-16474) vào `Danh sách mua.xlsx`, hiện
   chưa có dòng PPG; dòng "PPG AFE" ghi BMI270. Ghi giá, ngày giao và trạng thái
   duyệt.
7. Điện cực 3M Red Dot 2228 trong danh sách mua có cỡ khoảng 4 × 3,3 cm theo trang
   nhà bán (chưa kiểm datasheet): có dán được ở đốt gần ngón trỏ không?

## 4. File đầu ra

| Sản phẩm | Đường dẫn |
| --- | --- |
| Báo cáo này | `reports/weekly/week_05/README.md` |
| Hồ sơ đạo đức (5 file + README, sửa outline) | `docs/ethics/` |
| Protocol v0.2 (mục 5, 6.4, 6.5 mới) | `docs/protocol/protocol_outline_v0.2.md` |
| Mốc ứng viên, `detect`, nội suy kiểm chiều cong | `software/signal_processing/fiducials.py` |
| Chặn phương án không mặc định trong v1 | `software/feature_extraction/week04.py` |
| PAT hợp lệ | `software/signal_processing/pat_validity.py` |
| So với đánh dấu tay | `software/evaluation/fiducial_agreement.py` |
| Script Tuần 5 | `scripts/week05_fiducials.py` |
| Config | `configs/data/week05_huy.json` |
| Mẫu CSV đánh dấu tay | `docs/protocol/templates/manual_fiducials_template.csv` |
| Tài liệu phương pháp | `docs/protocol/week05_fiducials_pat_validity.md` |
| Kết quả SYNTHETIC (records, đáp án, detections, agreement và các file provenance; biến thể `refractory_040/`) | `reports/weekly/week_05/synthetic_fiducials/` |
| Test | `tests/test_week05_fiducials.py` |
| Kịch bản bài báo | `docs/paper_scenarios_v0.1.md` |
| Cập nhật danh mục | `docs/protocol/README.md`, `docs/protocol/week04_features_sqi_bootstrap.md`, `software/README.md`, `software/evaluation/README.md`, `scripts/README.md`, `tests/README.md` |

## 5. Kết quả kiểm tra và môi trường

Chạy lại từ Git root ngày 2026-10-22, sau các sửa đổi ở mục 8, bằng
`.venv/Scripts/python.exe`. Ngày 2026-10-21 ra 355 passed, gồm 26 test Tuần 5.

| Lệnh | Kết quả |
| --- | --- |
| `python -m ruff check .` | exit 0, không cảnh báo. `--select E501` trên 4 file .py mới: exit 0 |
| `python -m pytest -q -p no:cacheprovider` | **379 passed**, exit 0 (gồm 50 test Tuần 5) |
| `python scripts/check_environment.py` | **exit 1**: lệch pin đã biết (Python 3.13.12 so với `<3.12`; numpy 2.5.3, pandas 3.0.6, scipy 1.18.1, matplotlib 3.11.2, pytest 9.1.1, scikit-learn 1.9.1, PyYAML 6.0.3 khác pin). Không sửa pin |
| `python -m pip check` | exit 0, No broken requirements found |
| `git diff --check` | exit 0 (chỉ cảnh báo CRLF/LF của working copy); file mới kiểm riêng: không có khoảng trắng cuối dòng hay CRLF |

Môi trường không phải Python 3.11 của CI, nên kết quả trên chưa thay cho CI Python
3.11 trên PR.

## 6. SYNTHETIC và dữ liệu công khai — không trộn kết quả

**SYNTHETIC** (`reports/weekly/week_05/synthetic_fiducials/agreement_synthetic.json`,
5 bản ghi `SYN_*`, đáp án do mã sinh; tạo lại 2026-10-22, số liệu không đổi):

- **R:** `derivative_energy` 55/55 TP, 2 FP; `prominence` 55/55 TP, 29 FP (bắt
  sóng T khi refractory 0,25 s). Ở refractory 0,4 s (`refractory_040/`):
  `prominence` 0 FP, `derivative_energy` 1 FP. Sóng T SYNTHETIC đặt đúng
  R + 0,25 s, trùng biên refractory, nên không kết luận phương pháp nào tốt hơn.
- **Foot `tangent`:** 54/54. Con số gộp +27,5 ms **không phải** phép kiểm giải
  tích. Theo từng bản ghi:
  - sạch, ngừng nhịp, mất PPG: +27,2 ms (giải tích 27,25 ms với thời gian lên
    150 ms);
  - HR143 (lên 100 ms): +18,8 ms;
  - nhiễu: +47,4 ms.

  Lệch thay đổi theo thời gian lên của xung.
- **Foot `d2_max`** 50/54; **`valley_min`** 48/54, hỏng chủ yếu ở bản ghi nhiễu.

Chỉ kiểm chứng code; không nói gì về độ chính xác trên người hay PulseDB. Không
có số nào ở đây là kết quả đánh dấu tay.

**PulseDB:** không có `data/raw/` hay file `.mat` trên máy (2026-10-21). Chưa xuất
tập train/val, chưa đánh dấu tay, chưa có bảng sai số. **Bị chặn chờ Linh** bàn
giao raw + split v2. B0/B3: xem 3.5.

## 7. Bàn giao, hạn chế và chuyển tiếp

| Đầu vào cần nhận | Người bàn giao | Dùng cho |
| --- | --- | --- |
| Raw PulseDB `.mat` được phép dùng + thư mục split v2 (sau khi chốt pool) | Linh | Xuất tập nhỏ train/val, Huy đánh dấu tay, bảng sai số mốc |
| Output `runs/b3_pulsedb/<run>/` (report.json, predictions_val.csv) | Linh | Đánh giá B0/B3, CI theo người |
| Xác nhận phân bổ tay/điện cực, câu hỏi 3.8 | Đức Anh | Đóng protocol v0.2 mục 5 |
| Câu trả lời 3.7 | Thầy | Hoàn thiện và nộp hồ sơ đạo đức |
| Review code mốc Tuần 5 | Linh | Trước khi dùng trong pipeline. `linh.md` mục 7.1 có 8 phát hiện; review độc lập xác nhận cả 8, đã xử lý ở mục 8. Cần Linh review lại bản đã sửa trên PR |

Hạn chế:

- Chưa có đánh dấu tay nên chưa có độ nhạy/PPV thật.
- R chưa nội suy dưới mẫu; `d2_max`/`valley_min` chưa làm mượt.
- Nhiều ngưỡng chưa có nguồn (ghi rõ trong config và tài liệu).
- Các giới hạn và điểm chờ quyết định ở mục 8.2.

Chuyển Tuần 6, cùng người xử lý:

- đánh dấu tay khi có raw;
- đánh giá B0/B3 khi có output;
- nộp hồ sơ đạo đức khi có câu trả lời của thầy;
- xác nhận phân bổ tay khi Đức Anh trả lời mục 3.8.

Không tuyên bố thiết bị y tế, thay thế cuff hay đạt ISO/AAMI.

## 8. Review độc lập 2026-10-22: đã sửa và chờ quyết định

Review chỉ đọc ngày 2026-10-22 chạy lại mọi kiểm tra, tái lập SYNTHETIC từng byte,
thử luồng biên và mutation. Sau đó Huy yêu cầu sửa những lỗi không cần quyết định
phương pháp. Mọi số bên dưới chạy trên Python 3.13.12; **chưa thay được CI Python
3.11**.

### 8.1. Đã sửa (2026-10-22)

| Lỗi | Sửa | Bằng chứng |
| --- | --- | --- |
| C1: PAT ngoài 80–400 ms biến mất thành "R không ghép", trái quy tắc "gắn nhãn, không xóa"; config `pat_validity` không có tác dụng | `pair_between_r`: ghép trong khoảng R–R rồi gắn nhãn; `r_status` (`paired`/`no_foot`/`ambiguous`); biên 80/400 có dung sai float; test khóa giá trị config | `test_pat_beats_labels_out_of_range_instead_of_dropping` và các test liên quan |
| C2: `synth`/`plot`/`annotate`/`detect` không ghi provenance; `compare` có thể ghi sai config đã dùng | Mỗi lệnh ghi provenance (git, hash code/input, numpy/scipy/pandas/matplotlib, `source_type`); `detect` ghi `<out>.provenance.json`; `compare` từ chối khi config khác `detect`, thiếu provenance hoặc CSV đã đổi | `test_compare_refuses_other_config_or_missing_detect_provenance` |
| `annotate` kiểm `--out` ở cuối buổi | Kiểm trước cửa sổ đầu, ghi từng bản ghi; toolbar không bắt buộc | `test_annotate_refuses_existing_output_before_any_window` |
| Ghép greedy bỏ sót cặp; biên float; vùng review bất đối xứng phạt phương pháp có bias | Ghép một–một tối ưu (quy hoạch động); dung sai float; detection ở mép trong một dung sai được ghép nhưng không tính FP | `test_match_events_maximises_pairs_and_never_reuses`, `test_agreement_edge_match_is_tp_and_unmatched_margin_is_not_fp` |
| Chặn đáp án SYNTHETIC lách được bằng chữ thường/khoảng trắng | Chặn trong chính `agreement`, không phân biệt hoa thường hay khoảng trắng; trộn với mốc tay bị từ chối | `test_agreement_refuses_synthetic_truth_however_written` |
| Nội suy parabol dời ngược hướng khi parabol cong sai chiều | Kiểm chiều cong (`_vertex_offset(..., "min"/"max")`) | `test_vertex_offset_needs_the_right_curvature` |
| Test yếu: 31/56 mutant sống | 50 test (trước là 26). 33/33 mutant nhắm vào các sửa đổi bị bắt, gồm tắt hoặc đảo dấu nội suy, MAD k/scale, dung sai R, `load_records` bỏ chặn test, `_new_dir` cho ghi đè, ECG 125 Hz | `tests/test_week05_fiducials.py` |
| Tài liệu sai hoặc thiếu: nội suy ở góc nhọn, `export` đọc toàn bộ raw, ngưỡng `derivative_energy`, refractory áp cho PPG, +27,5 ms "đúng giải tích", bảng chỉ có refractory 0,25 s | Sửa `week05_fiducials_pat_validity.md` mục 2–8 và config `sources`; thêm biến thể `refractory_040/` | Mục 6 ở trên |
| Đạo đức/protocol: xem mục 3.2, 3.3 | Đánh dấu chờ, ghi mâu thuẫn, viết lại kết luận 5.4, khôi phục ý v0.1 bị mất, sửa trích dẫn | `docs/ethics/`, protocol v0.2 changelog 2026-10-22 |
| README danh mục chưa có file mới | Cập nhật `software/`, `software/evaluation/`, `scripts/`, `tests/` | — |

Output mặc định `features-sqi-v1` vẫn không đổi sau các sửa đổi (mục 3.4).

### 8.2. Chờ Huy quyết định (chưa đổi code hoặc quy trình)

1. Nội suy parabol ở góc nhọn bất đối xứng: giữ, bỏ hay chỉ nội suy khi gần đối
   xứng. Probe: `valley_min` MAE 6,28 ms có nội suy so với 3,56 ms không nội suy.
2. Ngưỡng robust cho `derivative_energy`. Hiện một nhịp ×2,5 làm mất 8/9 nhịp.
3. `ppg_refractory_s` riêng cho PPG và giá trị của nó; thêm ca SYNTHETIC có sóng
   tâm trương.
4. Dời sóng T SYNTHETIC khỏi biên refractory (R + 0,25 s). Việc này đổi đáp án và
   bảng kết quả.
5. Protocol:
   - trục thời gian M2 (cách và lúc trả lời) và M4 (cửa sổ so với cuff sau khi
     dừng đạp);
   - một định nghĩa ngưỡng 15 mmHg dùng chung cho P2 và kịch bản bài báo;
   - quy tắc dùng lượt đo bị dừng (mục 10);
   - thống nhất mục 4 với L1–L10.
6. Thiết bị trong hồ sơ: số điện cực (cùng Đức Anh); điện cực khô dùng trên người
   hay chỉ bench.
7. Có tạo lại artifact Tuần 4 không. `reports/weekly/week_04/fixture_checks.json`
   còn ghi `features-sqi-v0` và hash bảng của bản CRLF (cũ từ trước `645df5d`).
8. `hardware/kicad/v1_module/wrist/v1_wrist.kicad_pro`: khối `erc` do KiCad tự
   ghi lúc 2026-10-20 15:05, không thuộc việc Tuần 5. Bỏ thay đổi hay giao Đức
   Anh; **không** đưa vào commit Tuần 5.
