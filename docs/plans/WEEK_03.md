# Kế hoạch Tuần 3 — chia dữ liệu, timestamp và baseline B0/B1

## Mục tiêu và ranh giới

- Linh kế thừa reader PulseDB Tuần 2, chia train/validation/test theo người và kiểm thử chống rò rỉ dữ liệu.
- Đức Anh hoàn thiện quy ước timestamp/packet và kiểm thử cơ chế đồng bộ ECG–PPG bằng dữ liệu giả lập trên máy tính.
- Huy xây baseline B0/B1, thống nhất chỉ số đánh giá và quy tắc hiệu chuẩn với Linh.
- Cả ba bàn giao dữ liệu, cấu hình, test và hướng dẫn chạy để chuẩn bị pipeline baseline Tuần 4.
- **Chưa có phần cứng PPG/ECG.** Tuần này chỉ nghiệm thu phần mềm, dữ liệu công khai và mô phỏng; phân biệt các kết quả đó với số đo thiết bị thật, hiện chưa có. Chưa đo trên người bằng prototype khi chưa đáp ứng điều kiện an toàn/phê duyệt cần thiết.

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
      <th scope="col" width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Nhiệm vụ Tuần 3</th>
      <th scope="col" width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Đầu ra và nghiệm thu</th>
      <th scope="col" width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Đầu vào và phụ thuộc</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td width="10%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Linh</td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Kế thừa reader; xác nhận file/nguồn/quyền sử dụng và checksum.</p><p style="margin: 0 0 8px;">Kiểm tra số người trước khi đề xuất tỷ lệ chia; chia theo <code style="white-space: normal; overflow-wrap: anywhere;">subject_id</code> với config/seed cố định.</p><p style="margin: 0 0 8px;">Sinh manifest có ID mẫu/người, nguồn, record/cửa sổ gốc nếu có, split và hash.</p><p style="margin: 0 0 8px;">Validator kiểm tra giao người, trùng record/cửa sổ, mất/nhân đôi mẫu; negative tests phải xác nhận dữ liệu lỗi bị từ chối.</p><p style="margin: 0 0 8px;">Thống kê số người/đoạn, SBP/DBP theo split; tuổi/giới chỉ khi có metadata thật.</p><p style="margin: 0 0 8px;">Tham số tiền xử lý chỉ fit trên train.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Chạy lại cùng input/config/seed cho cùng hash; không giao người, số mẫu đối chiếu khớp và negative tests đạt.</p><p style="margin: 0 0 8px;">Có bảng phân bố, log và lệnh chạy thực.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Linh cung cấp reader/metadata; Huy cung cấp quy tắc mẫu/nhãn và review split. <strong>Đã có code ở ref cục bộ, chưa xác nhận chạy lại/nghiệm thu.</strong> Nếu dữ liệu chỉ có trên Kaggle, chạy tại đó và ghi môi trường/commit/checksum.</p><p style="margin: 0 0 8px;">Thiếu ID hoặc quá ít người thì bổ sung pool được phép hoặc chỉ test giả lập, ghi giới hạn phần công khai.</p></td>
    </tr>
    <tr>
      <td width="10%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Đức Anh</td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Kế thừa packet schema: làm rõ version, phiên/kênh, sequence, timestamp/đơn vị, sample count và fs từng kênh.</p><p style="margin: 0 0 8px;">Phân biệt thời điểm lấy mẫu với đọc FIFO/nhận gói; mô tả thời gian từng mẫu trong batch và clock chung/ánh xạ clock.</p><p style="margin: 0 0 8px;">Viết generator hoặc replay có config/seed; test gói hợp lệ, mất, trùng, đảo thứ tự, timestamp bất thường và lệch hai kênh có chủ đích.</p><p style="margin: 0 0 8px;">Chuẩn bị kế hoạch đo 10 phút khi có thiết bị: offset, jitter, drift và mất gói.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Linh/Huy replay được fixture, kết quả khớp mô tả mong đợi; lỗi được phát hiện và gap không bị che mất.</p><p style="margin: 0 0 8px;">Có log/lệnh chạy; chỉ tiêu đo thật ghi là đề xuất.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Đức Anh cung cấp schema/bring-up; Linh review đọc gói, Huy review ý nghĩa thời gian. <strong>Chưa có thiết bị; PPG AFE/fs chưa chốt.</strong> Dùng fs cấu hình riêng cho mô phỏng, không coi là thông số phần cứng đã xác nhận.</p><p style="margin: 0 0 8px;">Không làm lại BOM/PCB hoặc yêu cầu driver hoàn chỉnh tuần này.</p></td>
    </tr>
    <tr>
      <td width="10%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;">Huy</td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Cài B0 hằng số quần thể từ nhãn train, B1 hằng số cá nhân từ phần hiệu chuẩn riêng có trước phần đánh giá.</p><p style="margin: 0 0 8px;">Tách người mới chưa hiệu chuẩn và cá nhân hóa; không dùng nhãn đánh giá để tính B1.</p><p style="margin: 0 0 8px;">Thống nhất MAE, bias, SD riêng SBP/DBP, đơn vị/chiều sai số và tổng hợp theo người; test có đáp án biết trước.</p><p style="margin: 0 0 8px;">Ghi cách tính/dữ liệu cần cho beta, tương quan ΔBP, Bland–Altman và coverage; không sinh chỉ số thiếu căn cứ.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">B0/B1 và metric khớp đáp án test; có bảng B0 công khai khi manifest đủ điều kiện.</p><p style="margin: 0 0 8px;">B1 thiếu chronology/calibration chỉ nghiệm thu công thức bằng giả lập.</p></td>
      <td width="30%" valign="top" style="vertical-align: top; text-align: left; overflow-wrap: anywhere; padding: 10px;"><p style="margin: 0 0 8px;">Linh bàn giao manifest/nhãn; Đức Anh bàn giao fixture thời gian.</p><p style="margin: 0 0 8px;">Huy chịu trách nhiệm chính, Linh review code baseline/metrics. <strong>Chưa có baseline triển khai trong các ref đã kiểm tra; thời gian/phiên và calibration PulseDB chưa xác nhận.</strong> Nếu manifest chưa sẵn, làm module/test giả lập trước và ghi phần công khai bị chặn.</p></td>
    </tr>
  </tbody>
</table>

**Vị trí đầu ra dự kiến:**

- **Linh:** Logic split trong `software/data_io/`, script/config tại `scripts/` và `configs/data/`, test tại `tests/`; manifest/hash ngoài Git tại `data/processed/`.
- **Đức Anh:** Cập nhật `configs/hardware/Packet_Schema_V0.1.md` đang có; công cụ/config tại `scripts/` và `configs/hardware/`, fixture giả lập nhỏ tại `data/sample/`, test tại `tests/`, kế hoạch đo tại `hardware/test_reports/`.
- **Huy:** Module tại `software/models/`, metrics tại `software/evaluation/`, test tại `tests/`; quy tắc hiệu chuẩn và đánh giá trong `docs/protocol/`, kế thừa [tài liệu mẫu/nhãn](../protocol/week_02_sample_label_glossary.md).

Các đường dẫn trên là vị trí **dự kiến**, chưa phải sản phẩm đã tạo. Kế thừa file cùng chức năng nếu đã có; ghi đường dẫn thực và lệnh đã chạy trong báo cáo, không tạo bản trùng.

## Việc chung và mốc đóng tuần

1. **Đầu tuần:** Linh–Huy chốt pool, đơn vị quan sát, tỷ lệ/seed split và quy tắc B0/B1; Đức Anh lấy review schema/clock từ hai người. Linh chọn file đầu vào rõ ràng, checksum phải đúng file được đọc; bổ sung test gọi validator thật. Ghi quyết định, reviewer, commit và điểm còn mở trong báo cáo chung hoặc PR.
2. **Giữa tuần:** Linh bàn giao manifest/hash và phân bố; Đức Anh bàn giao fixture cùng kết quả mong đợi để Linh/Huy kiểm tra. Không tự tạo ID người/timestamp để bù thiếu; cùng người/cùng BP chưa chứng minh trùng đoạn. Kiểm tra ID liên nguồn và ghi giới hạn nếu chưa xác minh; không gộp lại holdout có sẵn hoặc dùng test để chọn split/model/ngưỡng.
3. **Quy tắc đánh giá:** B0/B1 tuần này kiểm tra BP tuyệt đối, không thay kết quả `ΔSBP/ΔDBP` cross-session. B0 dùng trung bình train; B1 dùng nhãn hiệu chuẩn riêng, trước và không trùng phần đánh giá. Nhãn ABP PulseDB không phải nhãn cuff; nhiều cửa sổ cùng `event_id` cuff không tạo nhiều nhãn độc lập. Sai số là `prediction - reference` (mmHg); MAE/bias tổng hợp đều theo người, SD ghi rõ cách tính và điều kiện đủ mẫu. Thiếu thời gian/phiên hoặc calibration thì B1 công khai và ΔBP chưa đủ điều kiện; không bịa chronology từ thứ tự dòng/file.
4. **Cuối tuần:** chạy lại split/hash, replay timestamp và baseline/metrics; review chéo, xử lý lỗi. Đầu ra chung gồm script/config/manifest và test chống leakage; schema/fixture/test timestamp cùng kế hoạch đo 10 phút; module/test B0/B1 và quy tắc đánh giá. Huy tổng hợp tại `reports/weekly/week_03/README.md` (dự kiến); Linh/Đức Anh cung cấp nguồn, config/seed, hash, commit, môi trường, lệnh/log, reviewer và trạng thái phần mình.
5. Nghiệm thu **tạm thời** khi đầu ra bắt buộc chạy lại được và có bằng chứng theo bảng; chạy kiểm tra phù hợp bằng `ruff check .`, `pytest -q`, `python scripts/check_environment.py`, cùng CI/review theo quy trình repo. Test giả lập không thay kết quả công khai hoặc số đo prototype. Thiếu đầu vào thì chỉ ghi đạt phần đã kiểm chứng, nêu người phụ trách và việc cần bổ sung trước Tuần 4.
6. **Nếu còn thời gian:** Huy minh họa R peak, PPG foot và PAT trên vài đoạn PulseDB đã xác minh kênh, fs và căn chỉnh; hình phải tái tạo bằng mã và ghi dữ liệu công khai. PAT không gọi PTT, không ép dịch hai đỉnh trùng nhau. Không đưa CNN, XGBoost, bootstrap hoàn chỉnh hoặc thuật toán PAT đầy đủ vào Tuần 3.

## Blocker và việc chuyển tiếp

- **Blocker: chưa có phần cứng PPG/ECG.** Thu ECG–PPG thật, đo offset/jitter/drift, nhiễu, dòng điện, mất gói và thử điện cực vẫn **chờ phần cứng**, dù mô phỏng đạt. Đức Anh thực hiện sau bring-up và điều kiện an toàn/phê duyệt cần thiết; Linh/Huy review bản ghi và log.
- Thiếu chronology/calibration hợp lệ thì **B1 trên dữ liệu công khai chưa đủ điều kiện đánh giá**. Bàn giao module/test giả lập và yêu cầu đầu vào còn thiếu cho Tuần 4.
- **G1 Tuần 4 chưa có định nghĩa/tiêu chí được khóa trong repo.** Huy xin nhóm xác nhận nguồn và yêu cầu G1. Nếu cổng cần bằng chứng thiết bị, phần đó chưa thể nghiệm thu; split/replay/baseline đạt không thay bản ghi thật. Nhóm quyết định lịch/phạm vi nghiệm thu, không tự ghi đạt G1.
- Tuần 4 bắt đầu pipeline baseline từ manifest/interface và quy tắc đã review. Giữ raw bất biến, lưu dữ liệu/manifest chi tiết ngoài Git theo chính sách; không cam kết đánh giá thiết bị hoặc cross-session cuff từ PulseDB.

## Vấn đề cần nhóm quyết định

- Pool PulseDB, quyền sử dụng, file/checksum, số người và tỷ lệ chia; ID liên nguồn, quan hệ với subset có sẵn và giới hạn kiểm tra record/cửa sổ gốc.
- Version packet, clock, timestamp lấy mẫu/FIFO/nhận gói và fs từng kênh. ECG 512 SPS trong packet mới khác đề xuất 500 Hz ở tài liệu cũ; PPG chưa chốt, không tự thay cấu hình cuối.
- Nguồn/quy tắc calibration B1, trọng số nhãn train B0, cách tổng hợp metric và định nghĩa beta/các chỉ số mở rộng; thiếu căn cứ thì ghi chưa tính được.
- Cửa sổ chính/SQI chỉ khóa trên pilot/validation, không lựa chọn trên test; protocol/ethics và kiểm tra an toàn trước đo người.
- Định nghĩa, tiêu chí và lịch G1 Tuần 4; phân biệt đầu ra phần mềm với phần đo thật còn chờ thiết bị.

## Nguồn đối chiếu

**Cập nhật đầu ra hỗ trợ Linh/Đức Anh, 2026-10-10:** đã có pipeline split v2
với inventory và công cụ generator/replay packet SYNTHETIC v2 trong workspace,
có test cục bộ; xem [báo cáo mục 6.6](../../reports/weekly/week_03/README.md#66-bản-sửa-hỗ-trợ-phần-linh-và-đức-anh-ngày-2026-10-10).
Fixture expected thực tế ở `tests/fixtures/`, packet/config/replay/report sinh
qua runner vào output mới ngoài Git. Vị trí `data/sample/` trong bảng đầu ra là
dự kiến ban đầu. Chưa xác nhận chạy raw/nguồn/pool, schema firmware được khóa,
review chéo, CI hoặc phép đo thiết bị thật; các mục đó vẫn chờ bàn giao riêng.

**Cập nhật phần Huy, 2026-10-03:** đã triển khai B0/B1, MAE/bias/SD và test/demo
SYNTHETIC, có kiểm thử cục bộ; xem [báo cáo Huy](../../reports/weekly/week_03/README.md)
và [quy ước/API](../protocol/week_03_baselines_metrics.md). Chờ Linh review code,
manifest/split và metadata calibration; chờ Đức Anh bàn giao fixture thời gian
và waveform xác minh. Đoạn trạng thái baseline trong bảng trên mô tả lần lập
kế hoạch trước triển khai; không còn mô tả code trong workspace hiện tại.
Chưa chạy PulseDB/PAT/thiết bị thật, chưa xác nhận CI Python 3.11 hoặc nghiệm thu
toàn bộ Tuần 3; trạng thái phần Linh/Đức Anh giữ theo bằng chứng bàn giao riêng.

- [Kế hoạch Tuần 2](WEEK_02.md), [báo cáo Tuần 2](../../reports/weekly/week_02/README.md), [phân công nhóm](../TEAM.md).
- [Tài liệu mẫu/nhãn](../protocol/week_02_sample_label_glossary.md), [protocol v0.1](../protocol/protocol_outline_v0.1.md), [câu hỏi nghiên cứu](../research_questions_v0.1.md), [chính sách dữ liệu](../DATA_POLICY.md).
- Rà soát ngày 2026-10-03: workspace `dev/huy@171e951`; reader/notebook/test/provenance tại `origin/develop@e8915f6`; packet/BOM/pin map/bring-up tại `origin/dev/ducanh@e13d669`. Đây là ref cục bộ, có file chưa nằm trong workspace; chưa fetch, chạy PulseDB hoặc xác nhận CI online trong lần lập kế hoạch.
- Yêu cầu Tuần 3 do người dùng cung cấp: chưa có phần cứng, dùng PulseDB/Kaggle, chuẩn bị split/timestamp/B0/B1 và đầu vào Tuần 4. Kế hoạch không phải bằng chứng nghiệm thu.
