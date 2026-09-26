# Tuần 2 — định nghĩa mẫu, nhãn và thuật ngữ sinh lý (bản thảo v0.1)

> **Trạng thái:** Đề xuất để Linh và Đức Anh review trước khi mã hóa logger, trình đọc và phân tích. Tài liệu này không thay thế protocol được duyệt. Chưa có bản ghi v0 để kiểm tra trực quan.

## 1. Thuật ngữ dùng thống nhất

| Thuật ngữ | Định nghĩa trong dự án | Giới hạn diễn giải |
| --- | --- | --- |
| ECG R peak | Mốc thời gian đỉnh R của một nhịp trên ECG. | Chỉ dùng khi tín hiệu và đồng bộ đủ chất lượng; đỉnh giả hoặc bỏ sót làm sai ghép nhịp. |
| PPG foot | Mốc khởi đầu phần lên của xung PPG ngoại vi cùng nhịp, theo một quy tắc phát hiện được khóa trước. | Phương pháp tiếp tuyến và đạo hàm bậc hai là ứng viên; kết quả có thể lệch do nhiễu, lọc và cách định nghĩa foot. |
| PAT | Khoảng từ R peak ECG tới PPG foot của nhịp tương ứng: `t_ppg_foot - t_ecg_r_peak` (ms). | Bao gồm thời gian trước khi máu được tống ra khỏi tim và thời gian sóng mạch truyền đến vị trí PPG; **không gọi PAT là PTT**. |
| PEP | Pre-ejection period, thành phần thời gian trước tống máu. | PEP có thể biến đổi và không được đo riêng bằng cấu hình ECG + PPG dự kiến. Cách chọn mốc ECG (Q hay R) ảnh hưởng cách biểu diễn chính xác thành phần này. |
| PTT | Thời gian sóng mạch đi giữa hai mốc trên đường động mạch. | Không suy ra PTT riêng từ một R peak và một PPG foot; không áp trực tiếp quan hệ vật lý của PTT lên PAT. |
| PWA | Pulse wave analysis: phân tích hình thái sóng mạch/PPG (ví dụ thời gian lên và độ rộng xung). | Các đặc trưng cần định nghĩa, kiểm tra và khóa trước; PWA không tự tạo nhãn BP. |
| SBP / DBP | Huyết áp tâm thu / tâm trương; đơn vị `mmHg`. | Đánh giá hai đầu ra riêng. Nguồn nhãn phải được ghi rõ. |

Trong cách viết gọn của kế hoạch, `PAT = PEP + PTT`; vì mốc đo là **đỉnh R**, thời gian từ R đến lúc tống máu có thể khác định nghĩa PEP bắt đầu ở Q. Khi cần độ chính xác sinh lý, phải ghi rõ hai mốc này và tránh diễn giải PEP là đại lượng đã đo. PEP thay đổi là một lý do PAT không đồng nhất với PTT hoặc BP.

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
- Đây là các **phương án để so sánh độ nhạy**, chưa phải bốn nhãn hay bốn quan sát độc lập. Cửa sổ chính và SQI phải được khóa trước khi xem test set; không chọn hậu nghiệm cửa sổ có sai số đẹp nhất.
- Lưu `window_start`, `window_end`, thời điểm cuff trả kết quả và độ lệch giữa cuối cửa sổ với nhãn. Ghi rõ clock, đơn vị và mọi khoảng mất mẫu.
- Nếu không có `t0` đáng tin cậy, thiếu tín hiệu hoặc không có clock đồng bộ, đánh dấu không thể ghép nhãn thay vì ước đoán thời điểm.

## 4. Trường metadata tối thiểu cần thống nhất

Đây là **đề xuất giao diện**, chưa thay đổi schema hoặc packet đã khóa:

| Trường | Mục đích / kiểm tra |
| --- | --- |
| `subject_id`, `session_id`, `event_id` | Khóa liên kết; duy nhất ở đúng cấp. |
| `source_type` | Phân biệt `prototype_cuff`, `public_abp` và dữ liệu mô phỏng. |
| `recording_id`, `raw_file_ref`, `raw_checksum` | Truy xuất raw bất biến, không đưa dữ liệu thật lên Git. |
| `device_config_version`, `firmware_version` | Truy xuất cấu hình logger và cảm biến. |
| `timestamp_unit`, `clock_id`, `ecg_sample_rate_hz`, `ppg_sample_rate_hz` | Kiểm tra trục thời gian, tần số và đồng bộ kênh. |
| `ecg_unit`, `ppg_unit`, `channel_map`, `polarity` | Chặn nhầm kênh/đơn vị/cực tính. |
| `cuff_start_time`, `cuff_result_time`, `cuff_status` | Ghép cửa sổ trước cuff; ghi lỗi/thiếu nhãn. |
| `sbp_mmhg`, `dbp_mmhg`, `label_source` | Một cặp BP cho một lần cuff; `label_source` không được bỏ khi trộn nguồn. |
| `window_id`, `window_start`, `window_end`, `quality_flags` | Truy xuất từng cửa sổ và lý do thiếu/loại, không nhân bản nhãn. |

Tên và kiểu dữ liệu phải được Linh và Đức Anh đối chiếu với packet thật. Dữ liệu dẫn xuất cần lưu version script/config/split/seed/commit như chính sách dữ liệu; không sửa raw.

## 5. Phân biệt PulseDB với nhãn cuff của prototype

PulseDB công bố các **đoạn 10 giây** ECG, PPG và waveform **ABP** từ MIMIC-III/VitalDB, có thông tin subject. Nhãn BP dẫn xuất từ ABP không phải lần đo cuff của protocol tại cổ tay. Một đoạn PulseDB cũng không chứng minh có một lần đo cuff tương ứng. Vì vậy:

- Dùng PulseDB để kiểm tra trình đọc, kênh, metadata và phương pháp tín hiệu theo đúng phiên bản/điều khoản dữ liệu.
- Không gán `event_id` cuff hoặc trộn nhãn ABP với nhãn cuff trong phân tích chính khi chưa có thiết kế và biên bản riêng.
- Không coi các đoạn 10 giây cùng người hoặc cùng bản ghi là mẫu độc lập trong split, bootstrap hay suy luận thống kê.
- Không khẳng định có đánh giá cross-session cuff từ PulseDB chỉ vì có nhiều đoạn của cùng `subject_id`.

## 6. Phiếu kiểm tra trực quan bản ghi v0

Chưa điền kết quả khi chưa có raw và log cấu hình. Khi nhận được bản ghi được phép kiểm tra, reviewer ghi **đường dẫn nội bộ hoặc mã manifest**, không chép waveform hoặc thông tin người tham gia lên Git.

| Mục cần xem | Dấu hiệu / câu hỏi cần ghi | Kết quả |
| --- | --- | --- |
| Timestamp ECG/PPG | Có tăng đơn điệu, mất mẫu, tràn counter hoặc trôi clock không? | Chờ bản ghi v0 |
| ECG R peak | Đỉnh R nhận diện được? Có đỉnh giả, bỏ sót hoặc sai cực tính? | Chờ bản ghi v0 |
| ECG baseline | Có trôi nền, nhiễu nguồn hoặc bão hòa kéo dài? | Chờ bản ghi v0 |
| PPG foot | Chân xung nhận diện được? Có cử động, clipping, đảo cực tính hoặc lệch pha do lọc? | Chờ bản ghi v0 |
| Ghép nhịp | Một R peak có một xung PPG sinh lý phù hợp trên cùng clock? | Chờ bản ghi v0 |
| Quyết định | Người review, ngày, mã bản ghi, phiên bản thiết bị, lỗi và issue cần xử lý. | Chờ review chéo |

## Nguồn và điểm cần duyệt

- [Mukkamala et al., 2015](https://doi.org/10.1109/TBME.2015.2441951): phân biệt PTT/PAT và các giới hạn mô hình hóa BP.
- [Gao et al., 2016](https://doi.org/10.14814/phy2.12768): ảnh hưởng của thành phần trước tống máu tới quan hệ PAT–BP.
- [Wang et al., PulseDB](https://doi.org/10.3389/fdgth.2022.1090854): cấu trúc ECG/PPG/ABP của dữ liệu công khai.
- [Protocol v0.1](protocol_outline_v0.1.md) và [chính sách dữ liệu](../DATA_POLICY.md). Nhóm cần duyệt định nghĩa mốc ECG/PPG foot, schema logger và cách xử lý cửa sổ trước khi triển khai.
