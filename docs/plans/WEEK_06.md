# Kế hoạch Tuần 6 — đặt hàng phần cứng, nộp hồ sơ đạo đức, B2 và theo dõi thí nghiệm

## Cập nhật 2026-10-29

Phần còn lại của file là kế hoạch lúc lập, giữ nguyên làm bản chụp. Khi khác nhau
thì theo mục này.

**Đã xong trước hoặc đầu Tuần 6** (không làm lại):

- Firmware mục 3: lệnh PC → thiết bị `ping` và `set-ppg-led`, packet cấu hình AFE
  `0xD2`, xác nhận lệnh `0xD3`, sự kiện mã 3 cho phép đo đồng bộ. Đều có spec ở
  Packet Schema V0.2 mục 12–13, codec và logger Python, firmware và test trên máy
  tính (Tuần 5, PR #25). Spec chỉ có `PING` và `SET_PPG_LED`; không có lệnh "bắt
  đầu hiệu chuẩn" hay "khóa cho các buổi sau". PC tự gửi lại mã đã khóa ở đầu mỗi
  buổi (protocol mục 6.1).
- Firmware mục 4: ước lượng dòng ở
  [power_budget_v1.md](../../configs/hardware/power_budget_v1.md), sửa theo bo
  Waveshare ngày 2026-10-29.
- KiCad V1-draft5 (2026-10-27) qua ERC/DRC, footprint đối chiếu với file CAD và bản
  vẽ của nhà sản xuất. Bo MCU là bo Waveshare ESP32-S3-DEV-KIT-N8R8-M, đặt
  2026-10-27; PCB V1 đang đặt ở CXT từ 2026-10-28, 5 tấm mỗi mạch.
- Thiết kế nghiên cứu và đạo đức (2026-10-29): protocol v0.3 và năm file hồ sơ đã
  có phương án cho mọi mục còn mở (xem [docs/ethics/README.md](../ethics/README.md)).

**Việc còn lại thật của Tuần 6:**

| Phụ trách | Việc | Tiêu chí xong |
| --- | --- | --- |
| Phần cứng | Đặt nốt MAX30001, MAX30101, BMI270, cáp và điện cực ([danh sách mua](../../hardware/bom/purchase_list_v1_module.md)) | Đơn đã đặt, có ngày giao |
| Phần cứng | Nhận PCB V1 và bo Waveshare; bring-up theo [trình tự V1-module](../../hardware/test_reports/v1_bringup_procedure.md) khi có hàng | Có ngày giao; bring-up mục 0–2 khi nhận bo |
| Firmware | Sự kiện mã 2 (`CUFF_END`) và mã 4 (đánh dấu của người vận hành) bằng lệnh PC `MARK_EVENT` (chốt 2026-10-29) | Spec Packet Schema V0.2 mục 13, firmware, logger, `device_command.py`, có test; chưa chạy trên chip |
| Firmware, Huy | Quy trình chỉnh và khóa dòng LED theo người: đã viết ở protocol mục 6.1 (2026-10-29); PC chặn mã > `0x7F` | Chưa chạy trên người |
| Linh | Theo dõi thí nghiệm; lần chạy nhiều seed chỉ là kiểm tính tất định (bảng dưới, sửa 2026-10-29); logger với bo Waveshare khi nhận hàng | Như bảng dưới |
| Linh, Huy | Duyệt B2 (chốt 2026-10-29), trong Tuần 6: Linh review [định nghĩa B2](../protocol/b2_pulsedb_definition.md) khi chưa có số nào; Huy duyệt nguyên trạng bằng commit riêng đổi `status`, ghi ngày; sau đó mới chạy trên val. Commit [đăng ký trước cách chấm test/CalFree](../protocol/pulsedb_test_scoring_preregistration.md) trước khi chạy | Bảng B0/B2/B3 trên val có CI |
| Huy | Đánh dấu tay 80 + 16 đoạn (đã có một phiên dở ngày 2026-10-25), rồi chạy `gate`. Quy tắc chốt 2026-10-29, trước khi chạy compare/gate: chỉ dùng train; ra `B4_NOT_ALLOWED` thì là kết luận cuối, không làm B4 trên PulseDB; độ lặp lại vẫn đòi khớp 100%, nhịp sát biên vùng review xử lý bằng quy tắc click ở [Tuần 5](../protocol/week05_fiducials_pat_validity.md) mục 9.2. Annotate cần `.venv` mới (Python 3.11.9 có tkinter) | Như bảng dưới |
| Huy | Hồ sơ đạo đức: mang các mục "đề xuất của nhóm, chờ thầy" của protocol v0.3 và hồ sơ tới buổi gặp thầy, mỗi mục có phương án mặc định; thầy xác nhận xong thì nộp | Xem điều kiện nộp dưới |

**Điều kiện nộp hồ sơ đạo đức (thay câu "sau khi thầy trả lời bốn câu hỏi"):**

1. Thầy trả lời bốn câu mang từ Tuần 5.
2. Thầy xác nhận các mục protocol tự ghi phải quyết trước khi nộp:
   - endpoint RQ1 và trục thời gian M2–M4 (protocol 6.4);
   - tiêu chí chọn/loại thống nhất với L1–L10 và đo hai tay (mục 4);
   - điện cực trên người (5.1);
   - trần tuyển 25 người;
   - ngưỡng BP dừng phiên và đầu mối y tế;
   - phương pháp đo dòng rò;
   - mốc khóa dữ liệu khi rút lui.
3. Chọn model máy cuff và có nguồn cho trần thời lượng ngâm M3.

Thầy không duyệt kịp trục thời gian trong tuần thì nộp bộ nghiệm pháp thu gọn (bỏ
M2, M4, và M3 nếu thiếu nguồn), bổ sung bằng sửa đổi. Không nộp bản còn ghi "chưa
quyết định".

## Mục tiêu và ranh giới

- **Đường găng là phần cứng.** Việc đầu tiên của tuần: đặt mua module và đặt gia
  công PCB V1. Cả hai chuyển từ Tuần 5, chưa đạt (báo cáo Tuần 5 mục 7).
- Nộp hồ sơ đạo đức (việc gốc Tuần 6) sau khi thầy trả lời bốn câu hỏi mang theo từ
  Tuần 5. Chưa nộp được thì báo giám sát viên và giữ nhánh benchmark công khai.
- Phần mềm theo việc gốc Tuần 6: Linh dựng hệ thống theo dõi thí nghiệm nhiều seed;
  Huy làm B2 (nhân khẩu học cộng HR). **B4 chỉ làm khi lệnh `gate` cho
  `B4_ALLOWED`**: trước đó phải có đánh dấu tay lần 1 (80 đoạn) và lần 2 (16 đoạn, sau
  ít nhất 2 ngày).
- Firmware không cần bo: lệnh từ PC xuống thiết bị (đặt dòng LED PPG theo người),
  ghi cấu hình AFE vào luồng dữ liệu, packet sự kiện mã 3 cho phép đo đồng bộ 10 phút.
- **Chưa có phần cứng và chưa có phê duyệt đạo đức: không đo trên người.** Test của
  split PulseDB và CalFree chưa chấm; chỉ chấm khi model đã khóa.

| Hạng mục | Trạng thái khi lập kế hoạch |
| --- | --- |
| Baseline | B0/B3 trên val PulseDB Train 400 người, có CI bootstrap theo người (báo cáo Tuần 5 mục 6.4). B1 cần dữ liệu hiệu chuẩn theo người; B2, B4 chưa có |
| Mốc R/foot | Cổng chấp nhận (`fiducials-week05-v2`) và bộ 80 đoạn sẵn; chưa đánh dấu tay |
| Phần cứng | KiCad V1-draft4 qua ERC/DRC, có gói file gia công và tờ kiểm footprint 1:1. Chưa mua module, chưa đặt PCB |
| Firmware | Packet Schema V0.2 kể cả kênh nhiệt độ `0xB1`; driver MAX30001, MAX30101, BMI270 đã viết, test trên máy tính, **chưa chạy trên chip** |
| Logger | Đọc V0.1/V0.2, record/replay, kiểm theo phiên; chưa đọc luồng từ MCU thật |
| Đạo đức | Bản nháp v0.1 đủ năm file, còn các ô chờ thầy/hội đồng |

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
      <th scope="col" width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Nhiệm vụ Tuần 6</th>
      <th scope="col" width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Đầu ra và nghiệm thu</th>
      <th scope="col" width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Đầu vào và phụ thuộc</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td width="10%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Linh</td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;"><strong>1. Theo dõi thí nghiệm</strong> (việc gốc Tuần 6). Mỗi lần chạy ghi config, seed, commit, hash raw/split và metrics vào một cấu trúc log thống nhất (MLflow hoặc thư mục JSON tương đương trong <code style="white-space: normal; overflow-wrap: anywhere;">runs/</code>, không thêm dependency khi chưa được duyệt). Khóa quy ước tên thí nghiệm và artifact.</p><p style="margin: 0 0 8px;"><strong>2. Nhiều seed.</strong> Chạy B0/B3 với ít nhất ba seed của model trên cùng split v2; script tổng hợp log thành bảng, không chép tay. <em>Sửa 2026-10-29:</em> B0 không có seed; B3 v1 không lấy mẫu con nên seed không có tác dụng. Lần chạy nhiều seed chỉ là kiểm tính tất định: kiểm metrics trùng nhau, kỳ vọng SD = 0. Độ bất định lấy từ bootstrap theo người đã có. Không đổi seed split 72. Không thêm subsample để có phương sai.</p><p style="margin: 0 0 8px;"><strong>3. Logger với MCU thật</strong> khi có DevKitC: đọc luồng 10 phút không tải theo bring-up mục 2.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Mỗi kết quả truy ngược được tới commit, config, split và seed; bảng nhiều seed sinh tự động và xác nhận các seed cho cùng metrics (sửa 2026-10-29: bỏ tiêu chí "có độ lệch giữa các seed"). Có test và hướng dẫn trong <code style="white-space: normal; overflow-wrap: anywhere;">docs/protocol/</code>.</p><p style="margin: 0 0 8px;">Chỉ dùng val; test không được trích đặc trưng.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Danh sách metrics của Huy (<code style="white-space: normal; overflow-wrap: anywhere;">evaluate_bp</code>, bootstrap theo người). Raw PulseDB và split v2 sẵn trên máy.</p><p style="margin: 0 0 8px;">Mục 3 chờ DevKitC.</p></td>
    </tr>
    <tr>
      <td width="10%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Phần cứng và firmware</td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;"><strong>1. Đặt mua module (việc đầu tiên).</strong> Duyệt <a href="../../hardware/bom/purchase_list_v1_module.md">danh sách mua</a> rồi đặt; ghi ngày giao dự kiến và phương án thay thế.</p><p style="margin: 0 0 8px;"><strong>2. Đặt gia công PCB V1.</strong> In tờ kiểm footprint tỉ lệ 1:1, so với bản vẽ kích thước của từng module; đạt thì đặt bo đế và bo cổ tay.</p><p style="margin: 0 0 8px;"><strong>3. Firmware không cần bo.</strong> Lệnh từ PC xuống thiết bị (bắt đầu hiệu chuẩn, đặt dòng LED PPG theo người, khóa cho các buổi sau); packet cấu hình AFE trong luồng dữ liệu để logger ghi vào phiên; packet sự kiện mã 3 cho phép đo đồng bộ 10 phút; thống nhất cách thử lại khi khởi động chip.</p><p style="margin: 0 0 8px;"><strong>4. Ước lượng dòng</strong> từng khối (ESP32-S3, MAX30001, MAX30101 khi LED chạy xung, BMI270) so với giới hạn cổng USB của laptop trong buổi đo 75 phút.</p><p style="margin: 0 0 8px;"><strong>5. Bring-up</strong> theo <a href="../../hardware/test_reports/v1_bringup_procedure.md">trình tự V1-module</a> khi nhận hàng.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Đơn mua module và đơn gia công PCB đã đặt, có ngày giao.</p><p style="margin: 0 0 8px;">Lệnh PC→thiết bị, packet cấu hình AFE và sự kiện mã 3 có spec (Packet Schema V0.2), codec và logger Python, firmware, test trên máy tính; chưa cần chạy trên chip.</p><p style="margin: 0 0 8px;">Bảng ước lượng dòng có nguồn số liệu (datasheet, trang).</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Duyệt mua theo quy định repo. Linh review packet và lệnh mới theo spec; Huy review quy trình hiệu chuẩn LED theo protocol v0.2 mục 6.1.</p><p style="margin: 0 0 8px;">Không gắn điện cực lên người.</p></td>
    </tr>
    <tr>
      <td width="10%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Huy</td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;"><strong>1. Hồ sơ đạo đức</strong> (việc gốc Tuần 6). Hỏi thầy bốn câu từ báo cáo Tuần 5 mục 7; điền các ô <code style="white-space: normal; overflow-wrap: anywhere;">[...]</code>; nộp hoặc chuyển hồ sơ theo quy trình của đơn vị; lập bảng theo dõi phản hồi hội đồng và người trả lời.</p><p style="margin: 0 0 8px;"><strong>2. B2 nhân khẩu học cộng HR</strong> (việc gốc Tuần 6). Đầu vào: tuổi, giới, chiều cao, cân nặng, BMI của PulseDB và HR từ ECG (khoảng R–R); fit trên train của split v2, chấm val, bootstrap theo người. Ghi định nghĩa và mô hình vào <code style="white-space: normal; overflow-wrap: anywhere;">docs/protocol/</code> trước khi chạy.</p><p style="margin: 0 0 8px;"><strong>3. Đánh dấu tay</strong> 80 đoạn (lần 1), 16 đoạn lặp lại sau ít nhất 2 ngày, rồi chạy <code style="white-space: normal; overflow-wrap: anywhere;">gate</code>. Chỉ khi <code style="white-space: normal; overflow-wrap: anywhere;">B4_ALLOWED</code>: chốt cách ghép R–foot và giới hạn PAT cho PulseDB (PPG trễ khoảng 300 ms so với ECG), rồi làm B4 PAT tuyến tính.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Bằng chứng đã nộp hồ sơ, hoặc ghi chú đã báo giám sát viên kèm lý do.</p><p style="margin: 0 0 8px;">Bảng B0/B2/B3 trên cùng split và cùng quy trình đánh giá, có CI; không tuyên bố vượt phạm vi PulseDB (nhãn ABP công khai, không phải cuff).</p><p style="margin: 0 0 8px;">Kết quả <code style="white-space: normal; overflow-wrap: anywhere;">gate</code> lần 1 trong báo cáo Tuần 6; B4 chỉ có khi cổng cho phép.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Thầy trả lời về hội đồng, máy cuff, nghiệm pháp M0–M4, các ô còn trống. Đức Anh cung cấp mô tả an toàn thiết bị cho hồ sơ.</p><p style="margin: 0 0 8px;">Không chọn đặc trưng, mô hình hay ngưỡng trên test.</p></td>
    </tr>
  </tbody>
</table>

**Vị trí đầu ra dự kiến:**

- **Linh:** log thí nghiệm và script tổng hợp ở `scripts/` và `software/`, output ở
  `runs/` ngoài Git, hướng dẫn tại `docs/protocol/`.
- **Phần cứng và firmware:** đơn mua tại `hardware/bom/`; spec lệnh và packet mới tại
  `configs/hardware/Packet_Schema_V0.2.md`; codec và logger tại `software/data_io/`;
  firmware tại `firmware/`; ước lượng dòng tại `configs/hardware/`.
- **Huy:** hồ sơ đạo đức tại `docs/ethics/`; B2 tại `software/pulsedb/`
  (`pipeline_b2.py`, `features_b2.py`) và `scripts/run_b2_pulsedb.py`; kết quả đánh dấu tay ngoài Git (có mã người), chỉ số tổng hợp trong
  báo cáo Tuần 6.

## Bàn giao và review chéo

1. Nhóm làm việc trực tiếp trong lab. Mỗi bàn giao kèm commit hoặc PR và tên người
   review.
2. Các quyết định trong tuần (thông số lệnh và packet mới, định nghĩa B2, kết quả
   cổng mốc) ghi vào tài liệu tương ứng kèm ngày, trước khi xem kết quả.
3. Review chéo: Linh review lệnh và packet mới theo spec; Huy review hệ thống theo dõi
   thí nghiệm và bảng nhiều seed; Linh review B2.
4. Trước khi merge: `ruff check .`, `pytest -q`, `python scripts/check_environment.py`,
   `python -m pip check`; CI Python 3.11 trên PR.
5. **Mốc đóng tuần:** module và PCB đã đặt, có ngày giao; hồ sơ đạo đức đã nộp (hoặc
   đã báo giám sát viên); B2 trên val có CI; bảng nhiều seed sinh tự động; kết quả
   cổng mốc lần 1; lệnh PC→thiết bị, packet cấu hình AFE và sự kiện mã 3 có test.
   Phần nào chưa đạt ghi người xử lý và tuần chuyển sang.
