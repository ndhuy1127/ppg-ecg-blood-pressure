# Đặc tả ứng dụng buổi đo (`session-app-v0`)

> **Trạng thái: đề xuất 2026-11-26, sửa 2026-11-27 sau phản biện độc lập; các quyết định ở mục 10
> chốt 2026-11-27. Chưa có code.** Mọi con số và quy tắc ở đây chép từ tài liệu đã chốt (đường dẫn
> ghi cạnh). Ứng dụng không tự đặt quy tắc khoa học mới; chỗ nào protocol hay SAP chưa rõ thì ghi ở
> mục 10, không tự chọn trong code.

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
6. **Đo lại chỉ theo protocol.** Chỉ ở M0, chỉ khi lượt trước là `no_result` hoặc người vận hành đã
   ghi cử động **trước `t0`** của lượt đó ([SAP v1](sap_v1.md) mục 2, protocol 6.4, chốt 2026-11-27).
   Không gợi ý đo lại vì số huyết áp, PAT hay SQI, và không gợi ý thêm buổi vì buổi trước "không
   đạt" (mục 9).
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
- Giao diện tiếng Việt, chạy hoàn toàn không cần mạng, cửa sổ tối thiểu 1366 × 768. Không có ô nào
  nhận họ tên người tham gia; chỉ mã `SUB###` (chốt 2026-11-27).
- Mọi danh sách và tham số vận hành đọc từ config có version trong `configs/session_app/`, không viết
  cứng trong code: checklist, mã người trực, firmware và bo, máy cuff, âm thanh thở chậm, khoảng giá
  trị nhãn hay gặp (mục 10).
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
- Chế độ người tham gia chỉ mở được khi file checklist (mục 5) ghi số phiên bản đề cương **đã được
  hội đồng duyệt**. Trước lúc đó ứng dụng chỉ chạy SYNTHETIC và bring-up. Version và hash của checklist
  được ghi vào nhật ký buổi (chốt 2026-11-27).
- **Người trực:** đầu buổi phải chọn đủ hai mã, người vận hành và người theo dõi, từ danh sách người
  được phép trong config (tài liệu an toàn mục 1, phiếu ghi buổi đo mục A). Hai mã phải khác nhau.
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
3. **Checklist trước đo** (tick đủ mới bật nút "Bắt đầu ghi"), đọc từ file config có version. Nội
   dung chép **nguyên văn** mục 2 của [an toàn buổi đo](../ethics/session_safety_stopping_v0.1.md),
   cộng các điều kiện của protocol 6.1 (nghỉ ≥ 10 phút; không cà phê, thuốc lá, vận động mạnh trong
   2 giờ). Khi tài liệu an toàn đổi thì tạo version checklist mới, không sửa bản cũ. Ứng dụng cũng ghi
   nhiệt độ phòng (phiếu mục A). Checklist có thêm một dòng "đồng hồ máy đo đúng giờ" (mục 9.1):
   ứng dụng hiện giờ hệ thống của máy kèm múi giờ để người vận hành so với đồng hồ chuẩn, và ghi
   kết quả vào nhật ký buổi.
4. **Chọn cổng COM**, rồi bấm "Bắt đầu ghi". Ứng dụng chạy logger và chờ `0xD1`, `0xD2` đầu tiên.
5. **Tự kiểm thiết bị** (đèn xanh/đỏ):
   - `0xD1`: hash ELF firmware, version ứng dụng và version IDF khớp một bản trong
     `configs/hardware/research_firmware.json` (chặn ở chế độ người tham gia nếu khác). `0xD1` không
     mang mã bo vật lý, nên mã bo được người vận hành chọn từ danh sách trong cùng file và ghi vào nhật
     ký;
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
- **Đèn mô tả** (chốt 2026-11-27, khớp protocol mục 11): cử động từ IMU, tuột điện cực, bão hòa PPG.
  Đèn chỉ để người vận hành nhìn: không có chỉ báo "sẵn sàng", không chặn nút, và **không phải căn cứ
  để đo lại**; căn cứ duy nhất là người vận hành tự thấy cử động (mục 6.4 bước 1). Ngưỡng cử động
  trước khi khóa trên G2 mang nhãn "tạm" và đèn cử động chỉ hiện ở chế độ bring-up (mục 10.1, điểm 17). Ingest hiện không đọc IMU (`DATA_CHANNELS` của
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
- M1: nút "Bắt đầu thở chậm" gửi `operator` (mã 4) và cho ứng dụng tự phát tiếng hướng dẫn: hít
  vào 4 s, thở ra 6 s, 15 phút, khớp hồ sơ đạo đức ("âm thanh hướng dẫn từ máy tính"). Tham số âm
  thanh có version trong config; nhật ký buổi ghi lúc bắt đầu phát thật, mỗi lần ngắt và lúc dừng,
  rồi đối chiếu với mốc pha. Nhắc bấm cuff ở phút cuối của 15 phút;
- M2: nút "Đọc số bắt đầu" gửi mã 4 và lưu số bắt đầu; nhắc bấm cuff sau 90 s; sau khi xả, ô nhập số
  người tham gia nói ra.

Với mỗi lượt, nhật ký buổi ghi **giờ bấm cuff theo kế hoạch** và **giờ bấm thật**. Nếu lệch quá 30 s
thì người vận hành chọn lý do từ danh sách (an toàn, lỗi lắp đặt, người tham gia cần nghỉ, khác).
Đồng hồ chỉ nhắc, không tự gửi lệnh nào ngoài những lệnh ghi ở trên.

### 6.4. Một lượt cuff

Mỗi lúc chỉ có **một lượt đang mở**. Lượt mở khi bấm "Bắt đầu lượt" và đóng khi đã nhập nhãn.

1. **Trước khi bấm cuff**, nếu thấy người tham gia cử động trong 60 s trước cuff, người vận hành bấm
   "Cử động" (gửi mã 4, loại "cử động", kèm một dòng mô tả ngắn). Nút này **khóa ngay khi thấy `t0`**
   của lượt, vì sau đó máy cuff có thể đã hiện số. Bấm muộn hơn chỉ ghi được sai lệch, không mở quyền
   đo lại (SAP mục 2).
2. Người vận hành **bấm nút `t0` trên bo đế**, rồi bấm máy đo bắp tay (protocol 6.2). Ứng dụng thấy sự
   kiện mã 1 trong luồng và gán nó cho lượt đang mở.
3. Khi cuff xả xong, bấm nút lớn **"Cuff xả xong"**: gửi `mark --event cuff_end` (mã 2). Nếu sau 120 s
   chưa bấm thì ứng dụng nhắc.
4. Khi máy cuff hiện số, bấm **"Máy đã ra kết quả"**: ghi giờ theo đồng hồ PC, đủ chính xác cỡ giây
   cho độ lệch từ cuối cửa sổ tới lúc có kết quả mà protocol 6.2 yêu cầu. Model máy cuff đọc từ
   config (hồ sơ đạo đức chưa chốt model). Ô nhập nhãn: `status` (`valid` / `no_result` /
   `device_error`), SBP, DBP, nhịp từ màn hình máy cuff, ghi chú. Ứng dụng kiểm: số nguyên, DBP < SBP; `valid` thì bắt buộc có SBP/DBP, khác `valid`
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

- Tối đa 2 lần đo lại mỗi buổi, **chỉ ở M0**. Nút "Đo lại" chỉ bật khi lượt M0 trước là `no_result`
  hoặc có đánh dấu "Cử động" trước `t0` (mục 6.4 bước 1). Ở M1, M2 không có nút này; lượt không ra số
  thì vị trí đó thiếu nhãn. Lượt đo lại mang `repeat_of_event_id` (lượt ngay trước ở cùng vị trí) và
  `repeat_reason` (`no_result` / `observed_motion`) theo `cuff-log-v2`. Việc chọn nhãn của mỗi vị trí
  là việc của phân tích ([SAP v1](sap_v1.md) mục 2), ứng dụng chỉ ghi đủ liên kết.
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

**`cuff_log.csv`** được sinh từ nhật ký buổi, theo `cuff-log-v2`
([data_convention.md](../data_convention.md) mục 4.4, chốt 2026-11-27): các cột cũ cộng
`repeat_of_event_id`, `repeat_reason`. Dòng tiêu đề lấy thẳng từ hằng số cột của
`session_ingest.py` (`CUFF_COLUMNS_V2`), không gõ lại.
`led_readjusted` và `pilot` giống nhau trên mọi dòng.

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
5. **Phiếu ghi buổi đo** ([mẫu](../ethics/session_record_form_v0.1.md)) vẫn là hồ sơ chính thức có chữ
   ký (chốt 2026-11-27). Ứng dụng in sẵn phiếu A4 đã điền mục A và C (mã người, buổi, người trực, các
   lượt, đo lại với lượt gốc và lý do) để người trực đối chiếu và ký. Chỗ nào sửa tay trên giấy thì
   nhập lại vào ứng dụng kèm lý do (nhật ký ghi giá trị cũ và mới).

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

### 9.1. Đo ở máy này, xử lý ở máy khác (chốt 2026-11-27)

Máy đo (laptop đặt ở phòng đo) và máy xử lý (máy của thành viên nhóm chạy ingest và phân tích) có
thể là hai máy khác nhau.

- **Luôn ghi vào ổ của máy đo.** Logger và nhật ký buổi ghi vào `data/raw/...` trên ổ cục bộ của máy
  đo. Không ghi thẳng ra ổ mạng hay thư mục đồng bộ trong lúc đo: mạng chập chờn hay ổ mạng treo sẽ
  làm hỏng một bản ghi không đo lại được. Checklist an toàn cũng yêu cầu laptop đo không cắm cáp mạng.
- **Thư mục buổi là đơn vị chuyển.** Một thư mục mỗi buổi gồm mọi thư mục bản ghi (`raw.bin`,
  manifest, đầu ra của logger), nhật ký buổi, `cuff_log.csv` đã khóa và `session_index.json` (mục
  10.1, điểm 12). Thiếu một trong các thứ này thì máy xử lý không ingest hay đối chiếu được.
- **Chuyển sau khi buổi đã đóng** (đã sao lưu, mục 10.1, điểm 18), bằng ổ cứng ngoài mã hóa hoặc mạng
  LAN của phòng thí nghiệm. Không chuyển qua dịch vụ đám mây công cộng hay ứng dụng nhắn tin
  ([kế hoạch quản lý dữ liệu](../ethics/data_management_plan_v0.1.md) mục 4).
- **Nút "Nhập buổi đo" trên máy xử lý:** chọn thư mục buổi nguồn, chép sang `data/raw/` của máy xử lý
  (không ghi đè buổi đã có), so SHA-256 của `raw.bin` và mọi file trong manifest của từng bản ghi,
  cùng hash của `cuff_log.csv` ghi trong `session_index.json`. Lệch một file thì dừng, không nhập phần
  nào. Nhập xong thì buổi hiện trong Danh sách buổi, ghi máy nguồn và thời điểm nhập. Ingest trên máy
  xử lý vẫn tự kiểm hash như hiện nay.
- **Điều kiện với máy đo:**
  - đồng hồ đúng giờ, bật đồng bộ giờ tự động: `session_start_utc` lấy từ đồng hồ máy đo và được
    dùng để kiểm thứ tự phiên và khoảng 7–28 ngày (SAP mục 2);
  - chạy đúng commit code của nghiên cứu và cùng môi trường Python (3.11, `requirements.txt`), vì
    provenance ghi commit và hash code và phân tích từ chối dữ liệu thật khi code không khớp bản đã
    khóa.
- **Điều kiện với mọi máy và ổ chứa dữ liệu người tham gia:** của thành viên nhóm có tên trong hồ sơ,
  mã hóa toàn ổ. Windows 11 **Home** không có BitLocker đầy đủ (chỉ "Device encryption" trên một số
  phần cứng, không tạo được BitLocker To Go cho ổ ngoài). Trước buổi đo người tham gia đầu tiên phải
  kiểm từng máy và ổ ngoài; máy hay ổ không mã hóa được thì không chứa dữ liệu người tham gia, và cách
  mã hóa ổ sao lưu ở điểm 18 phải chọn lại nếu cần.
- **Chỉ xem lại** thì không cần Python: `scripts/live_viewer.html` mở bằng Chrome hoặc Edge phát lại
  được một `raw.bin`. Dữ liệu SYNTHETIC và bản ghi bring-up không chịu các điều kiện trên.

## 10. Quyết định đã chốt (2026-11-27)

Điểm 1–2 qua phản biện độc lập; điểm 1–3 ghi ở [SAP v1](sap_v1.md) mục 2, 3, 13 và protocol 6.4, 11.

1. **Đo lại cuff:** chỉ ở M0; khi `no_result`, hoặc khi người vận hành thấy cử động và ghi **trước
   `t0`**. Mỗi vị trí trong lịch một nhãn: lượt `valid` đầu tiên. Hai phân tích độ nhạy (chỉ lượt
   gốc; thay lượt cử động). `cuff-log-v2` thêm `repeat_of_event_id`, `repeat_reason`; phiếu giấy ghi
   lượt gốc và lý do ở ô "Đo lại". Phương án kéo dài thở chậm để đo lại M1 không chọn (đổi thời lượng
   đã nộp hội đồng).
2. **Mã phiên lạ, phiên 2 ngoài 7–28 ngày:** hai người xét (người quản lý dữ liệu và một thành viên
   không vận hành buổi đó) trước khi xem kết quả, ghi bảng xét duyệt có version; raw không sửa. Gõ
   nhầm thì ánh xạ khi đủ bằng chứng; buổi thứ ba thật thì loại khỏi RQ1; phiên 2 ngoài khoảng thì ra
   khỏi phân tích chính, có endpoint phụ đưa vào lại.
3. **Đèn chất lượng:** có đèn mô tả cử động, tuột điện cực, bão hòa; không chặn, không làm căn cứ đo
   lại (mục 6.1).
4. **Checklist:** chép nguyên tài liệu an toàn mục 2; chế độ người tham gia chỉ mở khi checklist mang
   số bản đề cương đã duyệt (mục 4, 5).
5. **Phiếu giấy là hồ sơ chính thức;** ứng dụng in sẵn để ký (mục 8).
6. **Người trực:** chọn đủ hai mã từ danh sách trong config (mục 4).
7. **Âm thanh thở chậm:** ứng dụng tự phát, tham số có version, ghi lúc phát và ngắt (mục 6.3).
8. **Firmware và bo:** `configs/hardware/research_firmware.json` (mục 5).
9. **Máy cuff:** model đọc từ config; nút "Máy đã ra kết quả" ghi giờ PC (mục 6.4).
10. **Giao diện:** tiếng Việt, không cần mạng, tối thiểu 1366 × 768, chỉ mã `SUB###` (mục 3).
11. **Lịch buổi:** khi tạo buổi 2 kiểm 7–28 ngày; ngoài khoảng thì cảnh báo, ghi sai lệch, vẫn cho đo;
    không cho tạo buổi 3 (mục 5).

Đã chốt từ trước trong đặc tả này: thứ tự bấm "bo đế trước, máy cuff sau", sai thứ tự thì ghi sai
lệch sau lượt, không chen bước xác nhận (mục 6.4); mã LED khóa nằm trong metadata của bản ghi đo
buổi 1 (mục 6.2). Phần phân tích đòi phiên 2 đạt đã sửa trong `rq1_analysis.py` ngày 2026-11-27.

### 10.1. Chốt đợt hai (2026-11-27)

12. **Đối chiếu bảng đặc trưng với nhật ký cuff.** Sau khi ingest, ứng dụng ghi
    `session_index.json` (`session-index-v1`) cho mỗi buổi: mã người, mã buổi, SHA-256 của
    `cuff_log.csv` đã khóa, các bản ghi, các `session_index` đã ingest của từng bản ghi cùng thư mục
    đầu ra, và các `event_id` của nhật ký. `run_rq1_analysis.py` nhận `--session-indexes` (bắt buộc
    với dữ liệu thật) và dừng khi một `event_id` của nhật ký không nằm trong đúng một bảng đặc trưng
    đã truyền, hay một bảng đặc trưng không có trong file nào. Lý do: thiếu bảng của một lượt đo lại
    thì endpoint 12, 13 đổi mà không báo (rà soát 2026-11-27). Đã cài cùng ngày:
    `scripts/build_session_index.py` (ứng dụng gọi cùng code), `software/device/session_index.py`.
13. **Bảng xét duyệt phiên:** lưu ở `data/processed/session_adjudication.csv` (không commit). Khi khóa,
    ghi SHA-256 và ngày khóa vào `configs/data/session_adjudication_lock.json` rồi commit file này
    trước khi chạy RQ1; file khóa không chứa mã người. Giá trị truyền cho `--adjudication-sha256` lấy
    từ file khóa. Đã cài cùng ngày (`run_rq1_analysis.py --adjudication-lock`).
14. **Lần đo hai tay khi sàng lọc (buổi 1)** chỉ ghi vào nhật ký buổi và phiếu giấy, không vào
    `cuff_log.csv` (không phải M0–M2). Vẫn tính vào số lần bơm và ngưỡng an toàn 180/110 (mục 6.4,
    6.5).
15. **Khoảng giá trị nhãn hay gặp** (ngoài khoảng thì hỏi xác nhận, không từ chối): SBP 80–200 mmHg,
    DBP 40–130 mmHg, mạch 40–150 /phút. Chỉ để bắt lỗi gõ, không phải tiêu chí khoa học.
16. **Các mốc nhắc:** nhắc bấm "Cuff xả xong" sau 120 s kể từ `t0`; giờ bấm cuff lệch kế hoạch quá
    30 s thì ghi lý do; nhắc ở phút 100 của buổi, trần 120 phút (protocol 6.4).
17. **Đèn cử động** trước khi khóa ngưỡng trên G2: dùng ngưỡng mặc định của `motion-sqi-v0`, ghi nhãn
    "tạm", và chỉ hiện ở chế độ bring-up; ở chế độ người tham gia chỉ hiện hình IMU cho tới khi khóa
    G2. Đèn tuột điện cực và bão hòa vẫn hiện ở mọi chế độ.
18. **Sao lưu:** cuối mỗi buổi ứng dụng chép thư mục buổi (raw, nhật ký buổi, `cuff_log.csv`, đầu ra
    ingest, `session_index.json`) sang ổ cứng ngoài đã mã hóa BitLocker, rồi so SHA-256 từng file
    của bản chép với bản gốc. Chưa chép và so xong thì buổi chưa đóng (màn hình Danh sách buổi ghi
    "chưa sao lưu"). Không đồng bộ lên đám mây công cộng ([kế hoạch quản lý dữ liệu](
    ../ethics/data_management_plan_v0.1.md) mục 4).
19. **Bốn giá trị chờ việc khác:** hash firmware nghiên cứu (sau khi đóng băng firmware),
    `SPO2_ADC_RGE` (sau phép thử dải ADC trên cổ tay), model máy cuff (theo hồ sơ đạo đức), checklist
    đã duyệt và danh sách người trực (theo hội đồng). Ứng dụng chạy SYNTHETIC và bring-up với giá trị
    tạm; chế độ người tham gia chỉ mở khi đủ bốn giá trị này trong config.
20. **Hai máy** (đo và xử lý): ghi vào ổ máy đo, chuyển thư mục buổi sau khi đóng buổi, nhập bằng nút
    "Nhập buổi đo" có kiểm SHA-256; đồng hồ máy đo đúng giờ (thêm vào checklist); mọi máy và ổ chứa
    dữ liệu người tham gia phải mã hóa, kiểm bản Windows Home trước người tham gia đầu tiên (mục 9.1).

## 11. Kiểm thử

- Code thuần (`software/session_app/`): test SYNTHETIC cho máy trạng thái lượt (một lượt mở mỗi lúc),
  đếm lần bơm theo bảng ở mục 6.5 (xuyên bản ghi và khởi động lại, tối đa 2 lần đo lại, chỉ ở M0,
  nút "Cử động" khóa ở `t0`, `device_error` không cho đo lại, `t0` nhầm không tính), ghép sự kiện (mã 4 của "Cử động" không thành mốc pha,
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

1. ~~Ingest đọc `cuff-log-v2`; phân tích chọn một nhãn mỗi vị trí, nhận bảng xét duyệt phiên, kiểm
   7–28 ngày, endpoint phụ 12–14~~ (xong 2026-11-27). Ứng dụng phải ghi `cuff-log-v2` và tự kiểm
   "cử động ghi trước `t0`" trên nhật ký buổi, vì ingest không thấy nhật ký đó.
2. Thêm L1, L2 vào logger, có test; thử đọc song song trên laptop đo.
3. ~~`software/session_app/`: máy trạng thái lượt, đếm lần bơm, ghép sự kiện, kiểm nhãn và an toàn,
   nhật ký buổi, có test.~~ Xong 2026-11-27: `software/session_app/visit.py` (lớp `Visit`), config
   `configs/session_app/session_app_v0.json`, test `tests/test_session_app_visit.py` (cuff log sinh ra
   được `read_cuff_log` đọc lại). Chưa có: ghi nhật ký buổi ra file JSONL và đọc lại (phần I/O của
   ứng dụng), kiểm chéo ordinal với `decode.json` sau buổi (mục 7), gọi `build_session_index`.
   Giới hạn đã biết: một sự kiện mã 4 bị mất sau khi lệnh đã được xác nhận làm lệch các mốc sau
   trong hàng đợi; kiểm chéo với `decode.json` sau buổi bắt được việc này.
4. Màn hình Ghi (xem trực tiếp, nút cuff, nhập nhãn, hai nút dừng), chạy được với nguồn giả.
5. Màn hình Chuẩn bị, chỉnh LED hai bản ghi.
6. Màn hình Sau buổi (ingest mọi phiên MCU) và Danh sách buổi.
7. Buổi giả trên bàn ở chế độ bring-up, rồi sửa đặc tả theo những gì thấy được.

Việc phía phân tích đi kèm (mục 10.1, điểm 12–13) đã xong 2026-11-27. Bước 2 (L1, L2 của logger) đã
cài cùng ngày; còn phải thử đọc song song trên laptop đo.
