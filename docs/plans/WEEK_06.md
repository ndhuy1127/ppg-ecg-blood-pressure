# Kế hoạch Tuần 6 — đặt hàng phần cứng, nộp hồ sơ đạo đức, B2 và theo dõi thí nghiệm

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
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;"><strong>1. Theo dõi thí nghiệm</strong> (việc gốc Tuần 6). Mỗi lần chạy ghi config, seed, commit, hash raw/split và metrics vào một cấu trúc log thống nhất (MLflow hoặc thư mục JSON tương đương trong <code style="white-space: normal; overflow-wrap: anywhere;">runs/</code>, không thêm dependency khi chưa được duyệt). Khóa quy ước tên thí nghiệm và artifact.</p><p style="margin: 0 0 8px;"><strong>2. Nhiều seed.</strong> Chạy B0/B3 với ít nhất ba seed của model trên cùng split v2; script tổng hợp log thành bảng, không chép tay.</p><p style="margin: 0 0 8px;"><strong>3. Logger với MCU thật</strong> khi có DevKitC: đọc luồng 10 phút không tải theo bring-up mục 2.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Mỗi kết quả truy ngược được tới commit, config, split và seed; bảng nhiều seed sinh tự động, có độ lệch giữa các seed. Có test và hướng dẫn trong <code style="white-space: normal; overflow-wrap: anywhere;">docs/protocol/</code>.</p><p style="margin: 0 0 8px;">Chỉ dùng val; test không được trích đặc trưng.</p></td>
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
- **Huy:** hồ sơ đạo đức tại `docs/ethics/`; B2 tại `software/models/` và
  `scripts/`; kết quả đánh dấu tay ngoài Git (có mã người), chỉ số tổng hợp trong
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
