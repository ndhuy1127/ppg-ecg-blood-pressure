# Tuần 2 — định nghĩa mẫu, nhãn và thuật ngữ sinh lý (bản thảo v0.1)

> Tài liệu này không thay thế protocol. Chưa có bằng chứng bản ghi v0 được bàn giao để kiểm tra trực quan.
> **Rà soát:** 2026-10-01. Tình trạng phần cứng thực tế chưa được xác nhận.

## 1. Thuật ngữ dùng thống nhất

| Thuật ngữ | Định nghĩa trong dự án | Giới hạn diễn giải |
| --- | --- | --- |
| ECG R peak | Mốc thời gian đỉnh R của một nhịp trên ECG. | Chỉ dùng khi tín hiệu và đồng bộ đủ chất lượng; đỉnh giả hoặc bỏ sót làm sai ghép nhịp. |
| PPG foot | Mốc khởi đầu phần lên của xung PPG ngoại vi cùng nhịp, theo một quy tắc phát hiện được khóa trước. | Phương pháp tiếp tuyến và đạo hàm bậc hai là ứng viên; kết quả có thể lệch do nhiễu, lọc và cách định nghĩa foot. |
| PAT | Khoảng từ R peak ECG tới PPG foot của nhịp tương ứng: `t_ppg_foot - t_ecg_r_peak` (ms). | Bao gồm thời gian trước khi máu được tống ra khỏi tim và thời gian sóng mạch truyền đến vị trí PPG; **không gọi PAT là PTT**. |
| PEP | Pre-ejection period: khoảng từ khởi đầu khử cực thất (thường lấy mốc bắt đầu QRS/Q) đến khi van động mạch chủ mở và bắt đầu tống máu. | PEP có thể biến đổi và không được đo riêng bằng cấu hình ECG + PPG dự kiến. Mốc R peak không trùng mốc bắt đầu QRS/Q. |
| PTT | Thời gian sóng mạch truyền giữa hai mốc động mạch đã định nghĩa, chẳng hạn từ lúc tống máu đến mốc sóng ngoại vi tương ứng. | Không suy ra PTT riêng từ một R peak và một PPG foot; không áp trực tiếp quan hệ vật lý của PTT lên PAT. |
| PWA | Pulse wave analysis: phân tích hình thái sóng mạch/PPG (ví dụ thời gian lên và độ rộng xung). | Các đặc trưng cần định nghĩa, kiểm tra và khóa trước; PWA không tự tạo nhãn BP. |
| SBP / DBP | Huyết áp tâm thu / tâm trương; đơn vị `mmHg`. | Đánh giá hai đầu ra riêng. Nguồn nhãn phải được ghi rõ. |

Trong cách viết gọn của kế hoạch, `PAT = PEP + PTT`; vì mốc đo là **đỉnh R**, thời gian từ R đến lúc tống máu có thể khác PEP bắt đầu ở Q/QRS. Khi cần độ chính xác sinh lý, phải ghi rõ hai mốc và cách chọn PPG foot. ECG + PPG chỉ cho phép đo PAT theo định nghĩa ở trên, không đo riêng PEP hoặc PTT. PEP thay đổi là một lý do PAT không đồng nhất với PTT hoặc BP.

## 2. Đơn vị quan sát và khóa liên kết

| Cấp | Khóa đề xuất | Ý nghĩa |
| --- | --- | --- |
| Người | `subject_id` | Mã giả danh; không chứa tên, mã sinh viên hay thông tin liên hệ. |
| Phiên | `subject_id`, `session_id` | Một lần đến/đợt đo có thứ tự thời gian; mã phiên không được dùng thay thời điểm. |
| Lần đo cuff | `subject_id`, `session_id`, `event_id` | **Một** lần đo cuff đối chứng tạo tối đa **một** cặp nhãn SBP/DBP độc lập. Lần đo lỗi hoặc thiếu nhãn phải được đánh dấu, không tự điền. |
| Cửa sổ tín hiệu | Khóa lần đo + `window_id` | Một đoạn tín hiệu dẫn xuất gắn với lần đo; nhiều cửa sổ của cùng `event_id` chia sẻ nhãn và không phải quan sát độc lập. |
| Nhịp | Khóa cửa sổ + chỉ số nhịp / timestamp | Đơn vị để ghép R peak với PPG foot và tính PAT trước khi tổng hợp theo lần đo. |

**Quan sát cho phân tích BP chính:** một lần đo cuff hợp lệ, với một vector đặc trưng tổng hợp từ cửa sổ được chọn trước và một cặp nhãn `SBP`, `DBP`. Chia tập phải giữ nguyên nhóm theo người; trong bài toán hiệu chuẩn cá nhân, phiên hiệu chuẩn phải có trước phiên kiểm tra. Nhiều nhịp/cửa sổ không làm tăng số nhãn BP độc lập. Khoảng tin cậy dùng bootstrap theo `subject_id`, không theo cửa sổ.

## 3. Thời gian và cửa sổ ứng viên

- Gọi `t0` là thời điểm **bắt đầu bơm cuff**, dùng cùng quy chiếu clock với timestamp mẫu hoặc lưu ánh xạ clock có thể kiểm tra.
- Cửa sổ ứng viên dài `L ∈ {10, 20, 30, 60}` giây: `[t0 - L, t0)`. Chỉ dùng tín hiệu trước cuff; mẫu trong lúc bơm/xả không thuộc đầu vào chính.
- Với từng cửa sổ, ghi `window_start = t0 - L` và `window_end = t0` theo cùng clock với `t0`, kèm đơn vị thời gian. Đây là biên cửa sổ dự kiến; chỉ xác nhận sau khi có timestamp và mốc cuff đáng tin cậy.
- Đây là các **phương án để so sánh độ nhạy**, chưa phải bốn nhãn hay bốn quan sát độc lập. Protocol v0.1 nêu 20–30 giây là phương án chính dự kiến, nhưng cửa sổ chính chưa được khóa. Cửa sổ chính và SQI phải được khóa trên pilot/validation trước khi xem test set; không chọn hậu nghiệm cửa sổ có sai số đẹp nhất.
- Lưu `window_start`, `window_end`, thời điểm cuff trả kết quả và độ lệch giữa cuối cửa sổ với nhãn. Ghi rõ clock, đơn vị và mọi khoảng mất mẫu.
- Nếu không có `t0` đáng tin cậy, thiếu tín hiệu hoặc không có clock đồng bộ, đánh dấu không thể ghép nhãn thay vì ước đoán thời điểm.

## 4. Chống rò rỉ dữ liệu và suy luận thống kê

- Chia train/validation/test theo `subject_id`: cùng một người không xuất hiện ở nhiều tập trong đánh giá theo người. Giữ toàn bộ phiên, lần đo và cửa sổ của người đó cùng một tập; không random-split cửa sổ.
- Với cá nhân hóa, dữ liệu hiệu chuẩn của một người phải có trước dữ liệu kiểm tra theo thời gian. Chỉ dùng phần hiệu chuẩn được cho phép của người kiểm tra; không dùng phiên tương lai để xây dựng mốc hiệu chuẩn.
- Cửa sổ chồng lấn, nhiều nhịp trong một cửa sổ và nhiều cửa sổ cùng `event_id` không phải các quan sát BP độc lập. Tính số nhãn BP độc lập theo lần đo cuff hợp lệ và giữ cấu trúc lặp theo người.
- Chọn cửa sổ chính, quy tắc tìm R peak/PPG foot, feature, SQI và tham số trên train/validation trước khi mở test set; không điều chỉnh theo kết quả test. Các ngưỡng trong protocol v0.1 chưa khóa.
- Bootstrap và khoảng tin cậy theo cụm `subject_id`, giữ tất cả lần đo của người được lấy mẫu; không bootstrap cửa sổ hoặc nhịp như các quan sát độc lập.

## 5. Trường metadata tối thiểu cần thống nhất

Đây là **đề xuất giao diện logic** để Linh và Đức Anh đối chiếu, chưa phải packet đã khóa. “Bắt buộc” chỉ có nghĩa là cần trường đó để dùng bản ghi trong phân tích tương ứng; không được tự điền giá trị thiếu. `public_abp` không có lần đo cuff của prototype, nên không tạo `event_id` cuff cho nguồn này.

| Trường | Áp dụng trong đề xuất | Đơn vị / kiểu dự kiến | Mục đích / điểm cần xác nhận |
| --- | --- | --- | --- |
| `source_type`, `recording_id` | Bắt buộc cho mọi bản ghi | Loại nguồn; mã bản ghi | `source_type` phân biệt `prototype_cuff`, `public_abp`, `simulation`; `recording_id` truy về bản ghi gốc. |
| `subject_id` | Bắt buộc cho dữ liệu người trong đánh giá theo người | Mã giả danh | Giữ nguyên ánh xạ người của nguồn được phép dùng; nếu không xác định được, không đưa vào subject-wise split. Không dùng định danh trực tiếp. |
| `session_id`, `event_id` | Bắt buộc cho lần đo `prototype_cuff`; theo nguồn đối với dữ liệu công khai | Mã phiên; mã lần đo cuff | Khóa tổ hợp `subject_id` + `session_id` + `event_id` phải xác định tối đa một cặp nhãn cuff. Không bịa phiên hoặc event cuff cho PulseDB. |
| `raw_file_ref`, `raw_checksum` | Bắt buộc khi đưa bản ghi vào pipeline có truy vết | Đường dẫn nội bộ; checksum kèm thuật toán | Truy về raw bất biến, không commit raw hoặc dữ liệu nhạy cảm. Cách tạo manifest chưa chốt. |
| `label_source`, `sbp_mmhg`, `dbp_mmhg` | `label_source` bắt buộc khi có nhãn BP; cặp SBP/DBP bắt buộc cho lần cuff hợp lệ | Loại nguồn; `mmHg` | Phân biệt nhãn cuff với nhãn dẫn xuất từ ABP; không tự điền nhãn thiếu. Quy tắc dẫn xuất ABP chưa xác nhận trên phiên bản PulseDB dùng thực tế. |
| `cuff_start_time`, `cuff_result_time`, `cuff_status` | Bắt buộc cho ghép nhãn `prototype_cuff` | Thời điểm cùng clock hoặc ánh xạ clock; trạng thái | `t0` là bắt đầu bơm cuff; nếu mốc không đáng tin cậy thì không ghép cửa sổ. Cách ghi marker chưa chốt. |
| `window_id`, `window_start`, `window_end` | Bắt buộc cho cửa sổ dẫn xuất | Mã cửa sổ; thời điểm cùng clock và đơn vị đã khai báo | Truy cửa sổ về event/bản ghi gốc; nhiều cửa sổ có thể dùng chung nhãn, không phải nhãn độc lập. |
| `beat_index` hoặc `beat_timestamp` | Bắt buộc khi lưu đặc trưng theo nhịp | Số thứ tự hoặc thời điểm cùng clock | Ghép một R peak với một PPG foot tương ứng; quy tắc phát hiện và ghép chưa chốt. |
| `ecg_sample_rate_hz`, `ppg_sample_rate_hz`, `ecg_unit`, `ppg_unit`, `channel_map`, `polarity` | Bắt buộc khi đọc waveform tương ứng | `Hz`; đơn vị tín hiệu theo nguồn; ánh xạ kênh/cực tính | Kiểm tra kênh, đơn vị và trục thời gian; giá trị PulseDB phải lấy từ metadata thật, giá trị prototype vẫn dự kiến đến khi đo. |
| `timestamp_unit`, `clock_id`, timestamp mẫu hoặc chỉ số mẫu | Bắt buộc để ghép ECG–PPG và cuff | Đơn vị thời gian; mã clock; thời điểm hoặc chỉ số | Cần chứng minh clock chung hoặc ánh xạ clock; định dạng packet, tràn counter, mất mẫu và độ chính xác thực chưa xác nhận. |
| `device_config_version`, `firmware_version`, phiên bản packet | Chỉ áp dụng cho prototype; chưa chốt | Mã phiên bản | Truy cấu hình và định dạng logger; chưa có số phiên bản đo thực. |
| `quality_flags`, phiên bản script/config/split/seed/commit | Bắt buộc khi tạo dữ liệu dẫn xuất | Cờ và mã phiên bản | Truy quy tắc loại dữ liệu và phép phân tích; ngưỡng SQI phải được khóa trước trên pilot/validation. |

Tên trường, kiểu dữ liệu cụ thể, ánh xạ clock, tần số lấy mẫu và cách đóng gói phải được Linh và Đức Anh xác nhận trước khi khóa schema. Raw bất biến; dữ liệu dẫn xuất cần truy về raw, script, config, split, seed và commit theo [chính sách dữ liệu](../DATA_POLICY.md).

**Đầu vào hiện có:** packet schema tại ref cục bộ `origin/dev/ducanh` (`e13d669`, 2026-09-30), tệp `configs/hardware/Packet_Schema_V0.1.md`, đề xuất ECG 512 SPS, hai loại gói ECG/PPG và timestamp mẫu đầu gói (µs); PPG AFE/tần số chưa chốt. Protocol cũ nêu ECG 250–500 Hz, PPG 100–250 Hz. Không tự thay bằng một cấu hình cuối cùng: cần đối chiếu timestamp lấy mẫu với đọc FIFO/nhận gói, clock theo kênh, mất mẫu, metadata phiên và marker cuff. Packet chưa khóa.

## 6. Phân biệt nguồn nhãn BP

PulseDB công bố các **đoạn 10 giây** ECG, PPG và waveform **ABP** từ MIMIC-III/VitalDB, có thông tin subject. Nhãn BP dẫn xuất từ ABP không phải lần đo cuff của protocol tại cổ tay. Một đoạn PulseDB cũng không chứng minh có một lần đo cuff tương ứng. Vì vậy:

- Dùng PulseDB để kiểm tra trình đọc, kênh, metadata và phương pháp tín hiệu theo đúng phiên bản/điều khoản dữ liệu.
- Không gán `event_id` cuff hoặc trộn nhãn ABP với nhãn cuff trong phân tích chính khi chưa có thiết kế và biên bản riêng.
- Không coi các đoạn 10 giây cùng người hoặc cùng bản ghi là mẫu độc lập trong split, bootstrap hay suy luận thống kê.
- Không khẳng định có đánh giá cross-session cuff từ PulseDB chỉ vì có nhiều đoạn của cùng `subject_id`.
- `prototype_cuff`: một lần cuff hợp lệ tạo tối đa một cặp SBP/DBP độc lập, gắn với `event_id`.
- `public_abp`: nhãn BP nếu có được dẫn xuất từ waveform ABP theo quy tắc của đúng bản dữ liệu; không coi là nhãn cuff của prototype.
- `simulation`: chỉ dùng để kiểm tra code/giao diện, luôn ghi rõ là mô phỏng và không dùng làm bằng chứng hiệu năng trên người hay thiết bị.

## 7. Quy trình và phiếu kiểm tra bản ghi v0

Chưa điền kết quả khi chưa có phần cứng, raw thật và log cấu hình. Khi nhận được bản ghi được phép kiểm tra, người kiểm tra ghi **đường dẫn nội bộ hoặc mã manifest**, không chép waveform hoặc thông tin người tham gia lên Git. Trình tự dự kiến:

1. Xác nhận nguồn, checksum, cấu hình thiết bị, kênh, đơn vị và clock/tần số lấy mẫu từ metadata và log; đánh dấu dữ liệu hoặc mốc thiếu, không tự suy đoán.
2. Kiểm tra timestamp/chỉ số mẫu tăng đúng thứ tự, mất mẫu, tràn counter và khả năng quy đổi hai kênh về cùng trục thời gian. Vẽ tín hiệu ở khoảng ngắn để kiểm tra bão hòa, nhiễu và trôi đường nền.
3. Đánh dấu R peak và PPG foot theo quy tắc ứng viên, xem đỉnh giả/bỏ sót và ảnh hưởng của lọc. Chỉ ghép nhịp khi cùng clock và có một xung PPG tương ứng hợp lý; ghi trường hợp không ghép được.
4. Lưu ngày, mã bản ghi, phiên bản thiết bị, lỗi, quyết định và issue cần xử lý; không thay đổi ngưỡng sau khi xem test set.

**Đã có đầu ra PulseDB** tại ref cục bộ `origin/develop` (`e8915f6`, 2026-09-30): `software/pulsedb/`, `tests/test_pulsedb.py`, `notebooks/01_eda_and_visualization.ipynb`, `docs/pulsedb_provenance.md`. Chưa chạy lại hoặc nghiệm thu. Cần xác nhận nguồn/phiên bản, checksum file thực dùng, hướng dẫn chạy sạch, ánh xạ người/kênh/đơn vị/nhãn và bằng chứng ít nhất 1.000 đoạn. Provenance còn ghi checksum/file sử dụng sẽ hoàn thiện; notebook cần kiểm tra biến đầu vào từ kernel sạch. Mọi hình minh họa phải ghi **dữ liệu công khai, không phải tín hiệu thiết bị nhóm thu**.

| Mục cần xem | Dấu hiệu / câu hỏi cần ghi | Kết quả |
| --- | --- | --- |
| Timestamp ECG/PPG | Có tăng đơn điệu, mất mẫu, tràn counter hoặc trôi clock không? | Chờ bản ghi v0 |
| ECG R peak | Đỉnh R nhận diện được? Có đỉnh giả, bỏ sót hoặc sai cực tính? | Chờ bản ghi v0 |
| ECG baseline | Có trôi nền, nhiễu nguồn hoặc bão hòa kéo dài? | Chờ bản ghi v0 |
| PPG foot | Chân xung nhận diện được? Có cử động, clipping, đảo cực tính hoặc lệch pha do lọc? | Chờ bản ghi v0 |
| Ghép nhịp | Một R peak có một xung PPG sinh lý phù hợp trên cùng clock? | Chờ bản ghi v0 |
| Quyết định | Ngày, mã bản ghi, phiên bản thiết bị, lỗi và issue cần xử lý. | Chờ bản ghi v0 |

## Nguồn và điểm còn mở

- [Mukkamala et al., 2015](https://doi.org/10.1109/TBME.2015.2441951): phân biệt PTT/PAT và các giới hạn mô hình hóa BP.
- [Gao et al., 2016](https://doi.org/10.14814/phy2.12768): thực nghiệm trên lợn; PAT tương quan với BP kém hơn PTT xâm lấn và tác giả quy phần kém hơn cho thành phần PEP.
- [Yamashita et al., 2015](https://doi.org/10.1186/2197-425X-3-S1-A588): abstract hội nghị trên 6 con lợn; PEP tính từ R và từ Q tương quan chặt nhưng lệch nhau có hệ thống. Bằng chứng yếu, chỉ dùng để minh họa vì sao phải khai báo mốc.
- [Wang et al., PulseDB](https://doi.org/10.3389/fdgth.2022.1090854): cấu trúc ECG/PPG/ABP của dữ liệu công khai.
- [Protocol v0.1](protocol_outline_v0.1.md) và [chính sách dữ liệu](../DATA_POLICY.md). Cần chốt định nghĩa mốc ECG/PPG foot, schema logger và cách xử lý cửa sổ trước khi triển khai.
