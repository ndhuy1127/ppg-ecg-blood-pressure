# Kế hoạch Tuần 5 — khắc phục G1 phần cứng và kéo việc đường găng lên trước

## Mục tiêu và ranh giới

- Đóng phần phần mềm của G1: chạy B0/B3 trên raw PulseDB thật bằng runner split v2 và đánh giá bằng bootstrap theo người.
- Gỡ nút thắt phần cứng: đặt mua bộ module của V1-module, đóng các điểm mở của thiết kế, có firmware khung trên ESP32-S3 để phần mềm thử với packet thật từ MCU.
- Kéo lên trước các việc nằm trên đường găng của giai đoạn thu dữ liệu: logger phía máy tính (gốc Tuần 8), hồ sơ đạo đức (gốc Tuần 6) và phân bổ tay/điện cực/nghiệm pháp trong protocol (gốc Tuần 10).
- Giữ việc gốc Tuần 5 còn phù hợp: ERC/pin map V1 của Đức Anh, phương pháp mốc R/foot thứ hai của Huy. Hoãn 1D CNN của Linh sang sau G2 vì không nằm trên đường găng.
- **Chưa có phần cứng PPG/ECG và chưa có phê duyệt đạo đức.** Không đo trên người trong tuần này. Kết quả PulseDB là BP tuyệt đối trên nhãn ABP công khai, không phải đánh giá cuff, ΔBP cross-session hay thiết bị.

**Đầu vào kế thừa đã đối chiếu:** `dev/huy@cebe5c3`, ngày 2026-10-20.

| Hạng mục G1 (tài liệu phân công gốc) | Trạng thái khi lập kế hoạch |
| --- | --- |
| Pipeline tái lập, split theo người, test rò rỉ | Có: reader, `pulsedb-split-v2` có inventory, validator, CI |
| Baseline đầu tiên | B0/B1/metrics, bootstrap, `features-sqi-v1` có test. Runner B0/B3 split v2 có test SYNTHETIC nhưng **chưa chạy trên raw thật** ([run_b3_pulsedb.md](../protocol/run_b3_pulsedb.md)). Notebook cũ đã báo MAE trên test, phải ghi là sai lệch |
| PPG–ECG đồng bộ, báo cáo phần cứng v0 | **Chưa có.** Có BOM V0.1, Packet Schema V0.1, thiết kế KiCad V1-module (bo đế + bo cổ tay), kế hoạch đo 10 phút. Chưa mua module, `firmware/` chưa có mã, chưa có bản ghi bench |
| Hồ sơ đạo đức | Mới có [khung v0.1](../ethics/ethics_outline_v0.1.md) |

Kết luận: G1 phần mềm gần đạt (còn B0/B3 trên raw), G1 phần cứng chưa đạt. Tuần 5 thực hiện kế hoạch khắc phục dưới đây thay vì chuyển lỗi sang tuần sau mà không có quyết định.

## Phân công và tiêu chí kiểm tra

<table width="100%" style="display: table; width: 100%; table-layout: fixed;">
  <colgroup>
    <col width="10%" style="width: 10%;">
    <col width="30%" style="width: 30%;">
    <col width="30%" style="width: 30%;">
    <col width="30%" style="width: 30%;">
  </colgroup>
  <thead>
    <tr>
      <th scope="col" width="10%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Phụ trách</th>
      <th scope="col" width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Nhiệm vụ Tuần 5</th>
      <th scope="col" width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Đầu ra và nghiệm thu</th>
      <th scope="col" width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Đầu vào và phụ thuộc</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td width="10%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Linh</td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;"><strong>1. Đóng phần mềm G1.</strong> Cùng Huy chốt <code style="white-space: normal; overflow-wrap: anywhere;">pool_decision</code> (<code style="white-space: normal; overflow-wrap: anywhere;">VitalDB_AAMI_Cal_Subset</code> trùng người với AAMI Test). Tạo split v2 từ raw <code style="white-space: normal; overflow-wrap: anywhere;">.mat</code> bằng <code style="white-space: normal; overflow-wrap: anywhere;">scripts/build_pulsedb_split.py</code>, chạy <code style="white-space: normal; overflow-wrap: anywhere;">scripts/run_b3_pulsedb.py</code>, bàn giao bảng dự đoán val cho Huy.</p><p style="margin: 0 0 8px;"><strong>2. Logger phía máy tính (kéo từ Tuần 8).</strong> V1-module ghi dữ liệu qua USB lên laptop, chưa cần BLE/flash. Đọc packet từ USB serial theo Packet Schema V0.1; kiểm tra <code style="white-space: normal; overflow-wrap: anywhere;">SYNC</code>, <code style="white-space: normal; overflow-wrap: anywhere;">CRC16</code>, sequence, <code style="white-space: normal; overflow-wrap: anywhere;">FIRST_SAMPLE_INDEX</code>, <code style="white-space: normal; overflow-wrap: anywhere;">T_ANCHOR_US</code>; báo mất/trùng/đảo thứ tự; ghi raw bất biến kèm session manifest và hash.</p><p style="margin: 0 0 8px;"><strong>3. Mô phỏng đủ trường.</strong> Bổ sung vào generator các trường còn thiếu so với schema (<code style="white-space: normal; overflow-wrap: anywhere;">FIRST_SAMPLE_INDEX</code>, <code style="white-space: normal; overflow-wrap: anywhere;">STATUS</code>, <code style="white-space: normal; overflow-wrap: anywhere;">SYNC</code>, <code style="white-space: normal; overflow-wrap: anywhere;">CRC16</code>) với version schema mới, để test logger trước khi có firmware.</p><p style="margin: 0 0 8px;"><strong>Hoãn:</strong> 1D CNN sang sau G2. Không thêm MLflow; dùng provenance JSON hiện có trong <code style="white-space: normal; overflow-wrap: anywhere;">runs/</code>.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Bảng B0/B3 trên val từ raw thật kèm provenance (commit, hash raw/split/config, môi trường). Chạy lại cùng input cho cùng kết quả; test không bị trích đặc trưng. Báo cáo ghi sai lệch notebook cũ đã báo MAE trên test.</p><p style="margin: 0 0 8px;">Logger nhận đúng gói hợp lệ, phát hiện đủ năm trường hợp lỗi của mô phỏng (mất, trùng, đảo thứ tự, timestamp bất thường, lệch kênh) và lỗi CRC; không ghi đè raw; mỗi session có hash. Có test và hướng dẫn chạy trong <code style="white-space: normal; overflow-wrap: anywhere;">docs/protocol/</code>.</p><p style="margin: 0 0 8px;">Đức Anh review logger theo spec packet.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Raw <code style="white-space: normal; overflow-wrap: anywhere;">.mat</code> được phép dùng và quyết định pool (Linh–Huy). Packet Schema V0.1 (Đức Anh). Firmware khung của Đức Anh để thử logger với packet thật từ MCU, nếu có trong tuần.</p><p style="margin: 0 0 8px;">Chưa có raw thì giữ bảng B0/B3 ở trạng thái chờ, không dùng CSV 1.000 đoạn lịch sử thay thế.</p></td>
    </tr>
    <tr>
      <td width="10%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Đức Anh</td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;"><strong>1. Mua module (ưu tiên số một).</strong> Lập danh sách theo Phần A của <a href="../../configs/hardware/custom_board_proposal.md">custom_board_proposal.md</a>: ESP32-S3-DevKitC-1 N16R8, breakout ProtoCentral MAX30001, SparkFun MAX30101 (SEN-16474), SparkFun BMI270, FSR 402, điện cực Ag/AgCl; ghi giá, nơi mua, thời gian giao, phương án thay thế. Xin duyệt rồi đặt ngay. Cùng bộ module dùng cho bench v0 (nối dây) và cắm vào bo đế V1.</p><p style="margin: 0 0 8px;"><strong>2. Đóng điểm mở A.6.</strong> Chọn một pin map chuẩn (KiCad V1-module hay bản trong <a href="../../configs/hardware/interface_power_sampling_v0.md">interface_power_sampling_v0.md</a>); xác định chip của DevKitC N16R8 và mức điện áp GPIO47; xin thầy xác nhận MAX30101 dùng I²C bus riêng; kiểm VLED cho LED xanh. Sửa các tài liệu còn ghi PPG AFE "chưa chốt".</p><p style="margin: 0 0 8px;"><strong>3. ERC/DRC V1-module</strong> (việc gốc Tuần 5) cho bo đế và bo cổ tay; Linh review giao diện, Huy review vị trí cảm biến/điện cực. Chưa đặt gia công.</p><p style="margin: 0 0 8px;"><strong>4. Firmware khung trên DevKitC</strong> (chưa cần AFE): <code style="white-space: normal; overflow-wrap: anywhere;">esp_timer</code>, packet schema V0.1 với payload giả qua USB serial, packet sự kiện <code style="white-space: normal; overflow-wrap: anywhere;">0xC1</code> từ nút <code style="white-space: normal; overflow-wrap: anywhere;">t0</code>.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Đơn mua được duyệt và đã đặt, có ngày giao dự kiến.</p><p style="margin: 0 0 8px;">Mục A.6 không còn điểm chưa có quyết định hoặc chưa có người xử lý; chỉ còn một pin map chuẩn.</p><p style="margin: 0 0 8px;">Log ERC/DRC của hai bo, không còn lỗi chưa giải thích.</p><p style="margin: 0 0 8px;">Firmware build được theo hướng dẫn trong <code style="white-space: normal; overflow-wrap: anywhere;">firmware/README.md</code> (board, toolchain, lệnh build). Logger của Linh đọc được packet từ MCU thật; sequence và timestamp tăng đơn điệu trong 10 phút chạy không tải.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Duyệt mua theo quy định repo. Linh góp ý giao diện packet; Huy góp ý vị trí cảm biến, điện cực và phân bổ tay.</p><p style="margin: 0 0 8px;"><strong>Không đặt gia công PCB V1</strong> trước khi đối chiếu module thật với footprint (A.6 mục 2) và có số đo bench đầu tiên. Không gắn điện cực lên người.</p></td>
    </tr>
    <tr>
      <td width="10%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Huy</td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;"><strong>1. Ghi trạng thái G1</strong> vào báo cáo Tuần 5 theo bảng ở mục Mục tiêu, kèm kế hoạch khắc phục.</p><p style="margin: 0 0 8px;"><strong>2. Hồ sơ đạo đức (kéo từ Tuần 6).</strong> Từ khung v0.1, hoàn thiện phiếu đồng thuận, tiêu chuẩn chọn/loại, quy tắc dừng, quản lý dữ liệu. Hỏi thầy: hội đồng nào xét và mất bao lâu; đo thử trên thành viên nhóm (G2) có cần phê duyệt không; có mượn được máy cuff đã kiểm định hoặc thiết bị đo huyết áp liên tục không.</p><p style="margin: 0 0 8px;"><strong>3. Phân bổ tay và nghiệm pháp (kéo một phần từ Tuần 10).</strong> Cùng Đức Anh chốt cổ tay đeo PPG, tay đo cuff, vị trí điện cực đạo trình I (cổ tay và ngón tay), chi dùng cho từng nghiệm pháp. Liệt kê nghiệm pháp tạo ΔBP và tiêu chí biên độ ΔBP sẽ kiểm ở pilot.</p><p style="margin: 0 0 8px;"><strong>4. Mốc R/foot phương pháp thứ hai</strong> (việc gốc Tuần 5): thêm ít nhất một phương pháp ứng viên cho mỗi mốc; định nghĩa PAT hợp lệ, giới hạn sinh lý, quy tắc outlier; so với đánh dấu thủ công trên một tập nhỏ train/val PulseDB.</p><p style="margin: 0 0 8px;"><strong>5. Đánh giá B0/B3</strong> bằng <code style="white-space: normal; overflow-wrap: anywhere;">evaluate_prediction_table</code> khi Linh bàn giao.</p><p style="margin: 0 0 8px;"><strong>6. Phác P A/P B/P C</strong> (một trang): bài báo trông thế nào ở từng kịch bản.</p><p style="margin: 0 0 8px;">Ưu tiên mục 1–3; mục 4–6 chuyển Tuần 6 nếu thiếu đầu vào.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Báo cáo Tuần 5 ghi trạng thái G1 có ngày và đường dẫn bằng chứng.</p><p style="margin: 0 0 8px;">Bộ hồ sơ đạo đức đủ để nộp, kèm câu trả lời của thầy về hội đồng và thời gian xét.</p><p style="margin: 0 0 8px;">Sơ đồ phân bổ được Đức Anh xác nhận: cuff không cùng tay đeo PPG; không nghiệm pháp nào làm chuyển động tay đeo PPG hoặc gây nhiễu cơ trên chi gắn điện cực.</p><p style="margin: 0 0 8px;">Module mốc có test với nhịp sạch, nhiễu, mất nhịp; bảng sai số so với đánh dấu thủ công. Bảng B0/B3 có CI bootstrap theo người.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Thầy trả lời về hội đồng đạo đức và thiết bị tham chiếu. Raw và split v2 của Linh cho mục 4–5. Phương án điện cực của Đức Anh cho mục 3.</p><p style="margin: 0 0 8px;">Không thêm dependency khi chưa được duyệt; không chọn phương pháp, cửa sổ hay ngưỡng trên test.</p></td>
    </tr>
  </tbody>
</table>

**Vị trí đầu ra dự kiến:**

- **Linh:** logger và decoder trong `software/data_io/`, runner ở `scripts/`, config tại `configs/hardware/`, test tại `tests/`, hướng dẫn tại `docs/protocol/`. Output B0/B3 ở `runs/b3_pulsedb/` ngoài Git.
- **Đức Anh:** danh sách mua và pin map tại `configs/hardware/` và `hardware/bom/`; log ERC/DRC tại `hardware/test_reports/`; firmware khung tại `firmware/`.
- **Huy:** hồ sơ đạo đức tại `docs/ethics/`; phân bổ tay và nghiệm pháp cập nhật vào [protocol](../protocol/protocol_outline_v0.1.md); mốc R/foot tại `software/signal_processing/`; trạng thái G1 tại `reports/weekly/week_05/README.md`.

Kế thừa file cùng chức năng nếu đã có; báo cáo ghi đường dẫn thực và lệnh đã chạy.

## Bàn giao và review chéo

1. Nhóm làm việc trực tiếp trong lab, không đặt lịch họp riêng. Mỗi bàn giao kèm commit hoặc PR và tên người review.
2. Các quyết định trong tuần (pool PulseDB, pin map chuẩn, phân bổ tay/điện cực, trạng thái G1) ghi vào báo cáo Tuần 5 kèm ngày. Ngày ghi là bằng chứng quy tắc được khóa trước khi xem dữ liệu.
3. Review chéo: Đức Anh review logger theo spec packet; Linh review firmware khung và pin map; Huy review bảng B0/B3 và vị trí cảm biến; Đức Anh xác nhận sơ đồ phân bổ tay.
4. Trước khi merge: `ruff check .`, `pytest -q`, `python scripts/check_environment.py`, `python -m pip check`; CI Python 3.11 trên PR.
5. **Mốc đóng tuần:** bảng B0/B3 trên raw có CI; module đã đặt mua; A.6 đóng; firmware khung gửi packet tới logger; hồ sơ đạo đức sẵn sàng nộp; sơ đồ phân bổ tay được xác nhận. Phần nào chưa đạt ghi người xử lý và tuần chuyển sang.
