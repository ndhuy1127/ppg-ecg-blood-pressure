# Đặc tả ứng dụng buổi đo (`session-app-v0`)

> **Trạng thái: đề xuất 2026-11-26, sửa 2026-11-27 sau phản biện độc lập, chờ duyệt. Chưa có
> code.** Mọi con số và quy tắc ở đây chép từ tài liệu đã chốt (đường dẫn ghi cạnh). Ứng dụng
> không tự đặt quy tắc khoa học mới. Chỗ nào protocol hay SAP chưa rõ thì ghi ở mục 10, không tự
> chọn trong code.

## 1. Mục đích và phạm vi

Một buổi đo hiện cần 2–3 cửa sổ dòng lệnh: `packet_logger.py record --commands`,
`device_command.py` (LED, `cuff_end`, `operator`), sau buổi điền tay `cuff_log.csv` (kể cả ba cột
`*_event_ordinal` đọc từ `decode.json`) rồi chạy `device_session.py`. Các bước tay này dễ gây lỗi:
gõ sai `--subject-id`/`--session-id`, quên `cuff_end`, chép nhầm ordinal, quên gửi lại mã LED khi
MCU khởi động lại.

Ứng dụng gom các bước đó vào một cửa sổ có nút bấm, cho **người vận hành đã được tập huấn** theo
protocol và quy trình an toàn. Nó không thay tập huấn, không thay phiếu sàng lọc, không thay người
trực thứ hai, và không cho người tham gia tự đo.

**Trong phạm vi:** chuẩn bị buổi, ghi, xem trực tiếp, nhập nhãn cuff, nhật ký buổi, kiểm tra sau
buổi, danh sách các buổi.

**Ngoài phạm vi:** huấn luyện hay dự đoán BP; sửa raw; chọn hay đổi ngưỡng SQI; quyết định lần
cuff nào vào tập phân tích hay người nào đạt chuẩn (việc của `rq1_analysis.py` theo
[SAP v1](sap_v1.md)); lưu họ tên hay thông tin định danh (chỉ mã giả danh `SUB###`,
[DATA_POLICY](../DATA_POLICY.md)).

## 2. Nguyên tắc bắt buộc

1. **Mọi byte đều được lưu, kể cả lần đo hỏng.** Không có nút "bỏ lần đo này" hay "xóa bản ghi".
   Kiểm tra chất lượng chỉ **gắn nhãn**, không quyết định có lưu hay không. Lý do: phân tích chính
   của RQ1 không loại theo SQI ([SQI v1](sqi_specification_v1.md) mục 1). Phân tích phụ và RQ3
   cần cả lần đo xấu, và báo cáo phải nêu số lần bị loại cùng lý do (SAP mục 2, 11).
2. **Logger là nơi duy nhất ghi raw.** Ứng dụng không mở cổng serial và không ghi `raw.bin`. Nó
   chạy `packet_logger.py record --commands` như một tiến trình con, giữ nguyên đường ghi đã kiểm
   (`packet-logger-v3`: raw bất biến, manifest có hash, quy tắc `data/raw/`). Lệnh tới thiết bị
   đi qua `command_inbox.jsonl` như `device_command.py`.
3. **Tín hiệu trực tiếp chỉ để xem.** Hình và chỉ báo lúc đo được tính từ bản đọc song song của
   `raw.bin`, có độ trễ và không giống hệt cờ tính sau buổi. Nguồn của mọi kết quả vẫn là
   `decode.json` và đầu ra của `device_session.py`.
4. **Không dùng BP để đánh giá tín hiệu.** Chỉ báo không nhận SBP/DBP. Không hiện PAT hay đặc trưng
   cạnh SBP/DBP trong lúc đo, để người vận hành không bị ảnh hưởng khi ghi nhãn.
5. **Lúc bấm cuff theo lịch, không theo chất lượng tín hiệu.** Nếu người vận hành chờ tín hiệu
   "đẹp" rồi mới bấm cuff, mẫu sẽ nghiêng về các cửa sổ yên tĩnh. Ở M2, chờ còn làm thay đổi thời
   lượng nghiệm pháp. Cả hai đều làm lệch kết quả của PAT và coverage của RQ3. Ứng dụng chỉ chặn
   hay nhắc khi có **lỗi lắp đặt** hoặc **điều kiện protocol** chưa đủ (mục 6.1). Mọi chỉ số chất
   lượng khác chỉ để mô tả.
6. **Đo lại chỉ theo protocol.** Protocol 6.4 ("Số lần bơm") chỉ cho đo lại khi máy xả bình thường
   mà không ra số, hoặc khi lượt bị cử động. Không gợi ý đo lại vì PAT hay SQI xấu, và không gợi ý
   thêm buổi vì buổi trước "không đạt" (mục 9).
7. **Không ghi đè, có provenance.** Mỗi đầu ra mới ghi version schema, commit git, hash đầu vào và
   `source_type`, theo quy ước chung của các script.
8. **Không tự sửa khi lệch.** Khi ordinal, hash hay số packet không khớp, ứng dụng dừng ở bước đó và
   báo lỗi, giống `IngestError`. Mọi lần sửa tay đều được ghi vào nhật ký: giá trị cũ, giá trị mới,
   lý do, thời điểm.

## 3. Kiến trúc

```
┌────────────── session_app (Tk + matplotlib) ───────────────┐
│ màn hình: Chuẩn bị → Ghi → Sau buổi → Danh sách buổi        │
│                                                             │
│  tiến trình con ──► packet_logger.py record --commands      │
│                       (mở cổng, ghi raw.bin, manifest)      │
│  ghi dòng JSON ───► <recording>/command_inbox.jsonl         │
│  đọc song song ◄─── <recording>/raw.bin (chỉ đọc)           │
│  đọc ◄───────────── commands_sent.jsonl, stderr của logger  │
│  ghi ─────────────► nhật ký buổi + cuff_log.csv (mục 7)      │
│  sau buổi ────────► device_session.py → data/interim/...    │
└─────────────────────────────────────────────────────────────┘
```

- Code thuần đặt trong `software/session_app/`: trạng thái buổi, máy trạng thái lượt cuff, quy tắc
  đếm lần bơm, ghép ordinal, kiểm nhãn và an toàn. Code này không mở file, không vẽ hình, nên test
  được bằng SYNTHETIC. Phần giao diện và tiến trình nằm ở `scripts/session_app.py`.
- Giao diện dùng Tk (có sẵn trong `.venv`) và matplotlib (đã có trong `requirements.txt`), nên
  không thêm thư viện mới. Máy đo RAM thấp, nên hình chỉ giữ cửa sổ 10 s gần nhất của mỗi kênh.
- Giải mã trực tiếp dùng lại bộ giải mã của logger (`software/data_io/packet_wire.py`) và
  `LiveMonitor` (`software/data_io/live_monitor.py`, đã có phần mã LED và DC). Không viết bộ giải
  mã thứ hai.
- `scripts/live_viewer.html` vẫn giữ làm công cụ bring-up, không dùng trong buổi có người tham gia.
- Chọn tiến trình con thay vì chạy logger trong cùng tiến trình: nếu giao diện treo hay lỗi thì
  việc ghi raw không bị ảnh hưởng. Đổi lại phải giải mã hai lần (logger và ứng dụng), chi phí nhỏ.

### 3.1. Đọc song song `raw.bin`

- Logger mở `raw.bin` bằng `xb`. `x` chỉ là "tạo mới, không ghi đè", không khóa đọc. Tiến trình
  khác vẫn mở được file đó bằng `rb` trên ổ cục bộ Windows (theo tài liệu CPython và Windows; **chưa
  thử trên laptop đo**, phải thử ở bước 2 của mục 12).
- Ứng dụng giữ một bộ giải mã và một vị trí đọc. Gặp cuối file thì coi là "chờ thêm", không phải
  lỗi. Packet bị cắt ở cuối file được giữ lại cho lần đọc sau.
- stderr của logger được đọc trong một luồng riêng, để Tk không bị chặn và logger không bị đứng vì
  đầy ống.

### 3.2. Thay đổi cần có ở logger (nhỏ, có test)

Logger hiện chỉ dừng bằng Ctrl+C hay `--duration-s`, và ghi `raw.bin` qua bộ đệm của Python.
Ứng dụng cần thêm hai thứ:

- **L1. Yêu cầu dừng từ ngoài:** `record --stop-file <path>`. File này được kiểm ở cả hai chỗ: sau
  mỗi lần đọc có byte, và trong vòng chờ lúc rảnh của `SerialSource.read()`. Thấy file thì kết thúc
  như hết `--duration-s`, với `stopped_by = "stop_file"`. Trên Windows không gửi Ctrl+C cho tiến
  trình con một cách tin cậy, nên cần cách này.
- **L2. Đẩy raw ra đĩa đều đặn:** `raw.flush()` sau mỗi chunk (khoảng 14 kB/s, chi phí không đáng
  kể). Không `fsync` mỗi chunk; `fsync` vẫn chỉ ở cuối như hiện nay. Hash và nội dung `raw.bin`
  không đổi.

Hai thay đổi này không đổi định dạng đầu ra, nên `packet-logger-v3` giữ nguyên version. Ghi thêm vào
[packet_logger.md](packet_logger.md).

**Thứ tự khi dừng:** ứng dụng ngừng ghi vào `command_inbox.jsonl` trước (manifest có hash của hộp
thư), rồi mới tạo stop-file. Sau đó chờ logger thoát với mã 0 và có `session_manifest.json`. Chỉ khi
đó mới được ingest.

## 4. Chế độ và an toàn chung

- **Ba chế độ**, chọn ở màn hình 1, màu nền khác nhau:
  - *SYNTHETIC*: nguồn giả, ghi vào `runs/`.
  - *Bring-up / trên bàn*: không có người đeo, ghi vào `runs/packet_logger/`.
  - *Người tham gia*: ghi vào `data/raw/`. Thành viên nhóm đeo bo cũng là đo trên người, nên dùng chế
    độ này với checklist an toàn đầy đủ.
- Chế độ người tham gia chỉ mở được khi file checklist (mục 5) là bản **đã được duyệt** theo
  [an toàn buổi đo](../ethics/session_safety_stopping_v0.1.md) và hồ sơ đạo đức. Version và hash của
  checklist được ghi vào nhật ký buổi.
- **Hai nút dừng**, luôn hiện và bấm được ở mọi bước, kể cả trước `cuff_end` hay trước khi nhập
  nhãn:
  - *Dừng nghiệm pháp*: kết thúc M1 hay M2 đang làm, buổi vẫn tiếp tục;
  - *Dừng buổi*: dừng mọi lượt còn lại, hiện quy trình xử lý triệu chứng, theo dõi và biên bản sự cố
    theo tài liệu an toàn, rồi dừng ghi (mục 3.2).
  Lượt đã có nhãn đầy đủ trước khi dừng được giữ với `safety_stop = 1` (SAP mục 10). Lượt bị bỏ dở
  không có nhãn phải có lý do ghi rõ trong nhật ký buổi; không ghi là `no_result`, vì `no_result` chỉ
  dùng cho "máy xả bình thường nhưng không ra số".
- Đồng hồ buổi: trần 120 phút (protocol 6.4). Ứng dụng nhắc ở 100 phút và khi chạm trần.

## 5. Màn hình 1: Chuẩn bị buổi

1. **Chọn người và buổi.** Chọn `SUB###` từ danh sách đã có hoặc tạo mã kế tiếp. `S###` được gợi ý
   là buổi kế tiếp của người đó. Ứng dụng chặn mã sai định dạng và chặn buổi đã có bản ghi. Với buổi
   2, ứng dụng hiện khoảng cách tới buổi 1 và nhắc nếu nằm ngoài 7 ngày tới 4 tuần (protocol mục 3).
   Không cho tạo buổi 3.
2. **Metadata phiên.** Sinh `packet-session-metadata-v1` từ một mẫu có sẵn, với mã người, mã buổi và
   `ppg_led_lock` (mục 6.2). Ở buổi sau, mã khóa lấy từ metadata của bản ghi đo buổi 1 và hiện ra để
   người vận hành xác nhận.
3. **Checklist trước đo** (tick đủ mới bật nút "Bắt đầu ghi"), đọc từ file config có version, không
   viết cứng trong code. Nội dung lấy từ protocol 6.1 và tài liệu an toàn: đã qua sàng lọc (buổi 1);
   đủ người trực theo quy trình; kiểm điện và nhiệt đã ký; laptop chạy pin và mọi thiết bị ngoại vi
   cắm nguồn lưới đã rút; điện cực, vị trí bo cổ tay; không cà phê, thuốc lá, vận động mạnh trong
   2 giờ.
4. **Chọn cổng COM**, rồi bấm "Bắt đầu ghi". Ứng dụng chạy logger và chờ `0xD1`, `0xD2` đầu tiên.
5. **Tự kiểm thiết bị** (đèn xanh/đỏ):
   - `0xD1`: hash ELF firmware, version ứng dụng và version IDF khớp bản firmware của nghiên cứu (chặn
     nếu khác). `0xD1` không mang mã bo vật lý, nên mã bo được người vận hành chọn từ danh sách và
     ghi vào nhật ký;
   - `ping` có `0xD3`;
   - tốc độ thực ECG và PPG so với 512 và 200 sps danh định, tính trên đồng hồ thiết bị;
   - gói mất, cờ `STATUS` (FIFO tràn, lead-off, lỗi AFE, `ALC_OVF`);
   - `SPO2_ADC_RGE` trong `0xD2` đúng hằng số của nghiên cứu (protocol 6.1, "Dải ADC").

## 6. Màn hình 2: Ghi và lượt cuff

### 6.1. Hiển thị trực tiếp

- ECG, PPG xanh/đỏ/IR, IMU (độ lớn gia tốc), cửa sổ 10 s, cập nhật khoảng 5 lần mỗi giây.
- Thanh trạng thái: thời gian ghi, đồng hồ buổi, packet mất, tốc độ thực, mã LED đang chạy so với mã
  khóa, cờ `STATUS` mới nhất.
- **Điều kiện bấm cuff** (chặn nút "Bắt đầu lượt" cho tới khi đủ; mỗi lần chặn đều ghi lý do):
  - mã LED đã khóa có hiệu lực (`0xD3` báo xong, `0xD2` mang đúng mã);
  - đã nghỉ ≥ 2 phút từ `cuff_end` trước (protocol 6.2);
  - còn trong số lần bơm cho phép (mục 6.5).
- **Lỗi lắp đặt** (nhắc, không chặn): ECG tuột điện cực (|thô| ≥ 35 mV, quy tắc chốt 2026-11-24),
  khoảng trống packet, PPG chạm trần ADC. Protocol mục 11 cho phép xem tín hiệu và chỉnh dây **trước**
  khi bắt đầu đếm giờ của lượt, nên các lỗi này được xử lý trước lúc đếm, không phải lúc sắp bấm cuff.
- **Cử động:** chỉ hiện hình IMU để mô tả. Không có chỉ báo cử động kiểu "đạt/không đạt" trong buổi có
  người tham gia, kể cả sau khi khóa ngưỡng G2. Ingest hiện không đọc IMU (`DATA_CHANNELS` của
  `session_ingest.py` chỉ có ECG và PPG), nên cờ cử động sau buổi là `not_evaluable` cho tới khi
  ingest có IMU.
- Các chỉ báo trực tiếp **không** được gọi bằng tên cờ SQI. Cờ SQI có định nghĩa riêng (ví dụ lead-off
  theo ETAG hợp lệ và giữ 30 s, bão hòa theo từng màu > 5% thời gian, trên đồng hồ thiết bị), mà bản
  đọc trực tiếp có độ trễ không tái tạo đúng được.

### 6.2. Chỉnh và khóa LED

**Buổi 1** dùng **hai bản ghi**:
1. *Bản ghi chỉnh LED*: nút "Chỉnh LED" chạy đúng quy trình protocol 6.1 (mã khởi đầu, đọc DC trung
   bình 10 s, bước `0x08` cho đỏ và IR, `0x04` mỗi nhánh cho xanh, giới hạn `0x04`/`0x02` … `0x7F`,
   tối đa 6 vòng, `outside_dc_range`). Ứng dụng đề xuất mã cho từng vòng; người vận hành bấm "Gửi"
   cho từng lệnh, vì mỗi lệnh tạo một ranh giới chuỗi trong dữ liệu. Bản ghi này cũng được giữ.
2. *Bản ghi đo*: bắt đầu sau khi khóa mã, với `ppg_led_lock` và `outside_dc_range` đã nằm trong
   metadata **trước khi ghi**.

Lý do: logger chép và tính hash metadata trước khi đọc byte đầu tiên. Nếu sửa metadata sau đó thì
bản ghi không còn qua được kiểm tra hash. Nếu chỉ sửa file mẫu thì bản ghi đo không có mã khóa, và
mọi lần cuff M0 của buổi 1 sẽ mang `ppg:led_not_locked`, tức mất hiệu chuẩn (SAP mục 2). Metadata của
bản ghi đo buổi 1 là nguồn mã khóa của người đó cho các buổi sau.

**Mọi bản ghi đo:** ngay khi logger báo `SESSION_ID` mới (MCU khởi động hay khởi động lại), ứng dụng
tự xếp lệnh gửi lại mã khóa. Nó chỉ coi mã có hiệu lực khi có `0xD3` thành công **và** `0xD2` của chip
mang đúng mã.

**Buổi sau lệch thang** (protocol 6.1): nếu cửa sổ M0 đầu tiên chạm trần quá 5% thời gian thì hiện nút
"Chỉnh lại một lần". Bấm nút này đặt `led_readjusted = 1` cho cả buổi và ghi là sai lệch protocol. Mã
khóa gốc của người đó không đổi; mã chỉnh lại được ghi riêng cho buổi đó.

### 6.3. Trình tự một buổi

Bảng bên trái hiện kế hoạch của buổi theo protocol 6.4, với lượt đang làm được tô đậm:
- buổi 1: 2 lần đo hai tay khi sàng lọc;
- M0 ×2 → M1 → nghỉ ≥ 5 phút → M2.

Đồng hồ đếm:
- nghỉ ổn định ≥ 10 phút trước M0 (protocol 6.1);
- nghỉ ≥ 2 phút giữa hai lần bơm;
- M1: nút "Bắt đầu thở chậm" gửi `operator` (mã 4) và phát âm hướng dẫn (mục 10, Q6); nhắc bấm cuff
  ở phút cuối của 15 phút;
- M2: nút "Đọc số bắt đầu" gửi mã 4 và lưu số bắt đầu; nhắc bấm cuff sau 90 s; sau khi xả, ô nhập số
  người tham gia nói ra.

Với mỗi lượt, nhật ký buổi ghi **giờ bấm cuff theo kế hoạch** và **giờ bấm thật**. Nếu lệch quá 30 s
thì người vận hành chọn lý do từ danh sách (an toàn, lỗi lắp đặt, người tham gia cần nghỉ, khác).
Đồng hồ chỉ nhắc, không tự gửi lệnh nào ngoài những lệnh ghi ở trên.

### 6.4. Một lượt cuff

Mỗi lúc chỉ có **một lượt đang mở**. Lượt mở khi bấm "Bắt đầu lượt" và đóng khi đã nhập nhãn.

1. **Trước khi bấm cuff**, nếu thấy người tham gia cử động trong cửa sổ trước cuff, người vận hành bấm
   "Cử động" (gửi mã 4, loại "cử động"). Nút này khóa lại khi lượt đã có nhãn, để việc đánh dấu
   không bị ảnh hưởng bởi số đo.
2. Người vận hành **bấm nút `t0` trên bo đế**, rồi bấm máy đo bắp tay (protocol 6.2). Ứng dụng thấy sự
   kiện mã 1 trong luồng và gán nó cho lượt đang mở.
3. Khi cuff xả xong, bấm nút lớn **"Cuff xả xong"**: gửi `mark --event cuff_end` (mã 2). Nếu sau 120 s
   chưa bấm thì ứng dụng nhắc.
4. Ô nhập nhãn: `status` (`valid` / `no_result` / `device_error`), SBP, DBP, nhịp từ màn hình máy
   cuff, giờ máy cuff hiện kết quả (protocol 6.2 yêu cầu lưu độ lệch từ cuối cửa sổ tới lúc có kết
   quả), ghi chú. Ứng dụng kiểm: số nguyên, DBP < SBP; `valid` thì bắt buộc có SBP/DBP, khác `valid`
   thì không được có. Giá trị ngoài khoảng gõ thường gặp (đọc từ config) chỉ bị **hỏi xác nhận**, không
   bị từ chối, để một số đo cực trị thật vẫn được lưu và kích hoạt quy tắc an toàn.
5. **Kiểm an toàn ngay khi nhập**, áp cho **mọi** lần cuff, kể cả lần đo hai tay khi sàng lọc
   (tài liệu an toàn mục 6, protocol 6.4):
   - SBP ≥ 180 **hoặc** DBP ≥ 110 mmHg: hiện quy trình dừng buổi, đặt `safety_stop` cho lượt đó;
   - trung bình M0 có SBP ≥ 140 **hoặc** DBP ≥ 90 mmHg: ẩn M1, M2 trong kế hoạch buổi.
   Ứng dụng hiện quy tắc; người vận hành quyết định và xác nhận, và quyết định đó được ghi lại.
6. **`device_error`** (bơm không xả, bơm quá mức, lỗi phần cứng): hiện quy trình dừng buổi theo tài
   liệu an toàn mục 4, không cho đo lại.

### 6.5. Đếm lần bơm

Theo protocol 6.4 ("Số lần bơm"), đếm **mọi lần bơm thật**, kể cả lần hỏng, xuyên qua mọi bản ghi và
mọi lần MCU khởi động lại của buổi:

| Buổi | Theo kế hoạch | Trần |
| --- | --- | --- |
| Đủ M0–M2, buổi ≥ 2 | 4 | 6 |
| Đủ M0–M2, buổi 1 (thêm 2 lần sàng lọc) | 6 | 8 |
| Chỉ M0, buổi ≥ 2 | 2 | 4 |
| Chỉ M0, buổi 1 | 4 | 6 |

- Tối đa 2 lần đo lại mỗi buổi. Chỉ cho thêm lượt đo lại khi lượt trước là `no_result` hoặc đã được
  đánh dấu "Cử động" trước khi có nhãn (mục 6.4 bước 1). Lượt đo lại được nối với lượt gốc trong nhật
  ký buổi (cùng một "vị trí" trong kế hoạch). Cách dùng hai lượt này trong phân tích: mục 10, Q1.
- Lần sàng lọc tính vào số lần bơm và vào quy tắc an toàn, nhưng không vào hiệu chuẩn M0.
- Một lần bấm `t0` nhầm mà không bơm cuff không tính là một lần bơm (mục 7).
- Chạm trần thì nút "Bắt đầu lượt" bị khóa. Ứng dụng không ngăn được việc bấm máy cuff bằng tay, nên
  nếu vẫn có lần bơm vượt trần thì người vận hành ghi nó là sai lệch protocol.

### 6.6. Khi MCU khởi động lại hay mất cổng

- `SESSION_ID` đổi: báo đỏ, tự gửi lại mã khóa (mục 6.2), xóa mọi gán ghép đang chờ của lượt đang mở
  (mục 7). Ordinal sự kiện được đếm theo từng `device_session_id`, đúng như `cuff_log.csv` yêu cầu.
- Logger thoát bất thường: báo lỗi, giữ nguyên thư mục bản ghi. Bản ghi dở này không có manifest nên
  không ingest được, nhưng vẫn được giữ. Người vận hành có thể bắt đầu một **bản ghi mới trong cùng
  buổi**: nhật ký buổi, số lần bơm và số `event_id` vẫn liên tục qua các bản ghi.

## 7. Nhật ký buổi và nhật ký cuff

**Nhật ký buổi** (`session-app-journal-v0`, JSONL, một file mỗi buổi, chỉ ghi thêm, đặt cạnh các thư
mục bản ghi) giữ mọi thao tác: nút đã bấm và loại sự kiện mã 4 (packet mã 4 không mang chữ), dòng đã
ghi vào hộp thư, kết quả lệnh từ `commands_sent.jsonl`, packet `0xC1` đã thấy, giờ kế hoạch và giờ
thật của mỗi lượt, quyết định an toàn, lần sửa tay, lý do dừng.

**Ghép sự kiện với lượt.** `0xD3` thành công chỉ nghĩa là sự kiện đã vào hàng đợi firmware; packet
`0xC1` vẫn có thể mất ([packet_logger.md](packet_logger.md), mục `mark`). Vì vậy mỗi mốc do ứng dụng
gửi được đối chiếu ba bước: thao tác trong nhật ký → kết quả lệnh → packet `0xC1` thấy trong luồng.
- `t0` (mã 1): sự kiện mã 1 đầu tiên sau khi mở lượt. Mã 1 xuất hiện khi không có lượt mở thì ghi là
  "t0 ngoài lượt" trong nhật ký và không gán cho lượt nào. Nút "t0 nhầm" cho phép đánh dấu một `t0`
  trong lượt là nhầm, có lý do.
- Mốc pha (mã 4): **chỉ** lấy mã 4 do nút "Bắt đầu thở chậm" hoặc "Đọc số bắt đầu" gửi, nhận ra qua
  dòng hộp thư và kết quả lệnh. Mã 4 của nút "Cử động" hay "Sự kiện" không bao giờ thành mốc pha.
- `cuff_end` (mã 2): mã 2 đầu tiên sau `t0` của lượt, trước `t0` của lượt sau hay lần khởi động lại.
  Mỗi mốc chỉ dùng cho một lượt.
- Thiếu mốc không bắt buộc (`cuff_end`, mốc pha) thì để trống; ingest tự gắn cờ `cuff_end_missing`,
  `phase_mark_missing`. Một lần bơm thật mà thiếu `t0` thì không đưa vào `cuff_log.csv` (ingest bắt
  buộc `t0`), mà ghi vào danh sách ngoại lệ của nhật ký buổi kèm nhãn.

**`cuff_log.csv`** được sinh từ nhật ký buổi, đúng định dạng đã duyệt
([data_convention.md](../data_convention.md) mục 4.4). Dòng tiêu đề lấy thẳng từ `CUFF_COLUMNS` của
`session_ingest.py`, không gõ lại. `led_readjusted` và `pilot` giống nhau trên mọi dòng.

**Kiểm chéo sau buổi (bắt buộc trước ingest):** khi logger đã viết `decode.json`, ứng dụng đối chiếu
mọi ordinal với `decode.json`: tồn tại, đúng mã, đúng `device_session_id`. Lệch thì dừng, hiện chỗ lệch
và cho sửa tay có ghi lại. Chỉ khi khớp, `cuff_log.csv` mới được khóa (hash ghi vào nhật ký buổi).

## 8. Màn hình 3: Sau buổi

1. **Ingest đủ mọi phiên MCU.** `device_session.py` hiện chỉ xử lý một `session_index` mỗi lần chạy
   (mặc định 0) và lọc dòng cuff theo phiên đó, nên một lần chạy "thành công" có thể bỏ sót các lượt
   sau một lần MCU khởi động lại. Ứng dụng liệt kê mọi phiên trong `decode.json` của từng bản ghi, chạy
   ingest cho từng `session_index` vào một thư mục mới riêng, rồi kiểm mỗi `event_id` của `cuff_log.csv`
   xuất hiện **đúng một lần** trong các đầu ra.
2. **Bảng theo lượt cuff**, chỉ gồm các cột đã có trong `cuff_features.csv`/`session_summary.json`,
   chia ba nhóm, **không gộp thành một chữ "Đạt" chung**:
   - *Nhãn:* `status`, có SBP/DBP hay không, `safety_stop`.
   - *Tính được* ([SQI v1](sqi_specification_v1.md) mục 4): có đủ đặc trưng PPG không, PAT có tính được
     không, kèm lý do (`pat:*`, `ppg:*`, `ecg:absent`); `ppg:led_not_locked`.
   - *Cờ SQI* (mục 3, chỉ mô tả, không loại khỏi phân tích chính).
3. **Tóm tắt buổi:** thời lượng, tỷ lệ mất packet theo kênh, tốc độ thực và ppm, số lần bơm theo
   `status`, số lượt có `t0` lệch kế hoạch, sai lệch protocol. Không hiện "người đạt chuẩn": điều đó
   còn phụ thuộc sàng lọc, pilot, buổi khác và đặc trưng nền của buổi 1, và là việc của phân tích.
4. **Báo cáo buổi** (HTML, một file): các số ở trên, hình mẫu 10 s của mỗi kênh trước mỗi `t0`, danh
   sách sự kiện, lệnh và `0xD3`, provenance. Ghi vào thư mục đầu ra mới, không ghi đè.

## 9. Màn hình 4: Danh sách buổi

- Bảng mọi người và buổi: ngày, số bản ghi, số lần bơm theo `status`, đã ingest chưa, cờ
  `led_readjusted`/`pilot`, khoảng cách giữa các buổi. Lịch buổi đi theo **kế hoạch của protocol**
  (mục 3, chốt 2026-11-19: mỗi người đúng 2 buổi, buổi 2 cách buổi 1 từ 7 ngày tới 4 tuần, không có
  buổi 3), không theo kết quả "tính được" của buổi trước. Hiện một
  buổi "thiếu lượt tính được" như lý do để đo thêm sẽ là chọn người theo chất lượng tín hiệu.
- Bảng tổng hợp chỉ để **xem**. Phân tích RQ1 vẫn đọc thẳng các `cuff_features.csv` gốc cùng file
  provenance của từng cái (`run_rq1_analysis.py` kiểm từng bảng), không đọc một bảng đã ghép.
- Xem lại một bản ghi: mở `raw.bin` đã ghi trong màn hình xem, bằng một bộ đọc theo nhịp thời gian
  riêng của ứng dụng. `replay` của logger chỉ sinh file giải mã một lần, không phát theo thời gian.

## 10. Câu hỏi mở (cần chốt trước khi code)

- **Q1. Lượt cử động có nhãn hợp lệ và lượt đo lại của nó.** Protocol 6.4 cho đo lại khi "lượt đo bị
  cử động"; SAP mục 2 viết "lần đo lại thay cho lần hỏng, không thêm nhãn"; protocol mục 11 giữ mọi
  lượt kèm cờ. Hiện `rq1_analysis.py` nhận mọi dòng `valid`, nên lượt gốc và lượt đo lại đều thành
  nhãn chính mà không gì cho biết chúng là một vị trí trong kế hoạch. Đề xuất kỹ thuật: lượt `valid`
  đầu tiên vào endpoint chính; lượt hỏng không có nhãn được thay bằng lượt đo lại hợp lệ; lượt đo lại
  sau một lượt cử động có nhãn chỉ vào phân tích độ nhạy. Áp dụng như nhau cho M0 hiệu chuẩn. Quy tắc
  này phải được ghi vào SAP **trước khi thu dữ liệu**, và cần một cột liên kết lượt (đổi schema
  `cuff_log`, tăng version) để phân tích đọc được.
- **Q2. Thứ tự bấm (đã có đề xuất).** Nhắc "bo đế trước, máy cuff sau"; nếu người vận hành biết mình
  bấm sai thứ tự thì ghi sai lệch sau lượt. Không thêm bước xác nhận chen giữa hai lần bấm, vì làm vậy
  đổi khoảng thời gian giữa `t0` và lúc bơm mà vẫn không kiểm được thứ tự.
- **Q3. Quy tắc buổi đạt trong phân tích (đã sửa 2026-11-27).** `rq1_analysis.py` từng nhận "buổi 1
  đạt và **có một** buổi ≥ 2 đạt", trái SAP mục 2 (sửa 2026-11-21: "buổi 1 đạt và **buổi 2** đạt").
  Đã sửa trong `prepare` (lý do loại `session2_not_passing`) và có test cho S001 đạt, S002 trượt, S003
  đạt. Ứng dụng không hiện quy tắc này (mục 8, 9).
- **Q4. Nơi ghi mã LED khóa (đã có đề xuất).** Metadata của bản ghi đo buổi 1 (mục 6.2), không phải
  file riêng.
- **Q5. Chỉ báo cử động (đã có đề xuất).** Không có chỉ báo đạt/không đạt trong buổi có người tham gia;
  chỉ hiện hình IMU (mục 6.1).
- **Q6. Âm thanh thở chậm.** Dùng đúng nguồn âm thanh ghi trong hồ sơ được duyệt cho M1. Nếu quy trình
  cho phát từ ứng dụng thì ghi hash của file âm thanh, lúc bắt đầu phát thật và mọi lần ngắt vào nhật
  ký buổi, rồi đối chiếu với mốc pha.

## 11. Kiểm thử

- Code thuần (`software/session_app/`): test SYNTHETIC cho máy trạng thái lượt (một lượt mở mỗi lúc),
  đếm lần bơm theo bảng ở mục 6.5 (xuyên bản ghi và khởi động lại, tối đa 2 lần đo lại, `device_error`
  không cho đo lại, `t0` nhầm không tính), ghép sự kiện (mã 4 của "Cử động" không thành mốc pha,
  `cuff_end` thiếu không mượn của lượt sau, `0xD3` có mà `0xC1` mất), kiểm nhãn, quy tắc an toàn
  180/110 và 140/90 kể cả lần sàng lọc.
- Đường lệnh: `--source-file` dừng ở cuối file và không đi được với `--commands`, nên dùng một nguồn
  giả hai chiều có nhịp thời gian (đọc byte SYNTHETIC, nhận lệnh, trả `0xD3`) để test hết hạn lệnh, mất
  mốc, khởi động lại và dừng lúc rảnh. Giải mã cố định thì vẫn dùng file.
- Đầu cuối: nguồn giả → logger → ứng dụng không giao diện → `cuff_log.csv` → `device_session.py`
  cho mọi `session_index`; so `cuff_log.csv` với một file viết tay.
- Logger: test cho `--stop-file` (cả lúc có byte và lúc rảnh), và test rằng flush sau mỗi chunk vẫn
  cho cùng hash.
- Trên laptop đo: đọc song song `raw.bin` trong lúc ghi 10 phút, rồi so hash cuối.

## 12. Thứ tự làm đề xuất

1. Chốt Q1, Q6.
2. Thêm L1, L2 vào logger, có test; thử đọc song song trên laptop đo.
3. `software/session_app/`: máy trạng thái lượt, đếm lần bơm, ghép sự kiện, kiểm nhãn và an toàn,
   nhật ký buổi, có test.
4. Màn hình Ghi (xem trực tiếp, nút cuff, nhập nhãn, hai nút dừng), chạy được với nguồn giả.
5. Màn hình Chuẩn bị, chỉnh LED hai bản ghi.
6. Màn hình Sau buổi (ingest mọi phiên MCU) và Danh sách buổi.
7. Buổi giả trên bàn ở chế độ bring-up, rồi sửa đặc tả theo những gì thấy được.
