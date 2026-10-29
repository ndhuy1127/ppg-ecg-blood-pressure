# Quy ước Quản lý và Cấu trúc Dữ liệu

Tài liệu này quy định chuẩn quản lý, đặt tên và cấu trúc dữ liệu cho dự án PPG-ECG Blood Pressure Estimation.

---

## 1. Phân loại thư mục dữ liệu

Dữ liệu dự án được phân chia nghiêm ngặt theo 3 cấp độ, cộng một thư mục riêng cho kết quả chạy. Cả bốn thư mục đều bị Git bỏ qua (`.gitignore`):

* `data/raw/`: Dữ liệu gốc thu thập từ thiết bị đo trên người tham gia. Tuyệt đối **KHÔNG** chỉnh sửa, ghi đè hay xóa file trong thư mục này để "làm sạch" kết quả. Hai ngoại lệ, đều ghi nhật ký xóa (mã, ngày, người làm, không kèm danh tính): (1) xóa toàn bộ raw của một mã người tham gia khi người đó rút lui **và chọn xóa dữ liệu**, trước mốc khóa dữ liệu (snapshot G4), theo [kế hoạch quản lý dữ liệu](ethics/data_management_plan_v0.1.md) mục 4; (2) tiêu hủy khi hết thời hạn lưu, theo mục 5 của kế hoạch đó. Ngoại lệ (1) thêm ngày 2026-10-26; điều kiện "chọn xóa, trước mốc khóa" và ngoại lệ (2) thêm ngày 2026-10-29.
  * **Cấu trúc raw thiết bị (chốt 2026-10-29):** mỗi lần ghi là một thư mục `data/raw/<subject_id>/<session_id>/<recording>/`, chứa đúng một `raw.bin` (mọi byte nhận từ thiết bị) và `session_manifest.json` có SHA-256, cùng các file khác của logger (bản sao config/metadata, decode, nhật ký lệnh; [hướng dẫn logger](protocol/packet_logger.md), mục "Nơi ghi"). `<recording>` mặc định là giờ UTC lúc bắt đầu ghi; một buổi có thể có nhiều lần ghi. Tệp nhật ký cuff của buổi (nếu có tệp số) đặt trong `data/raw/<subject_id>/<session_id>/`.
  * Logger từ chối ghi dữ liệu người vào chỗ khác, kể cả `runs/`. Bản ghi bring-up không người và SYNTHETIC không vào `data/raw/`.
  * Xóa khi rút lui (ngoại lệ 1) nghĩa là xóa **cả thư mục** `data/raw/<subject_id>/`, cùng mọi dữ liệu dẫn xuất mang mã đó ở nơi khác (`data/interim/`, `data/processed/`, output `replay` hay kết quả trong `runs/`), theo kế hoạch quản lý dữ liệu mục 4.
* `data/interim/`: Dữ liệu thô đã qua xử lý sơ bộ (lọc nhiễu ban đầu, cắt bớt đoạn nhiễu nặng, định dạng lại timestamp).
* `data/processed/`: Dữ liệu hoàn chỉnh đã trích xuất đặc trưng (features), đồng bộ PPG/ECG và nhãn SBP/DBP, sẵn sàng cho huấn luyện mô hình ML/DL.
* `runs/` (ở gốc repository, ngoài `data/`): Kết quả chạy mô hình (dự đoán, model, metrics, provenance). Runner `scripts/run_b0_pulsedb_csv.py` và `scripts/run_b3_pulsedb.py` mặc định ghi vào `runs/` và từ chối ghi đè output đã có. File dự đoán theo dòng chứa `subject_id`, nên không commit. Bản ghi bring-up và SYNTHETIC của logger mặc định ở `runs/packet_logger/`; raw của người tham gia không bao giờ ở `runs/`.

---

## 2. Quy ước đặt tên File & Định danh

File dữ liệu **dẫn xuất** (`data/interim/`, `data/processed/`) theo cấu trúc tên thống nhất:

$$\text{<subject\_id>\_<session\_id>\_<event\_id>\_<data\_type>.<ext>}$$

Raw thiết bị **không** đặt tên theo event (chốt 2026-10-29): một `raw.bin` mỗi lần ghi chứa nhiều lượt đo, và các lượt đo nằm trong luồng dưới dạng packet sự kiện `0xC1`. Raw đặt theo thư mục ở mục 1.

### Định danh (IDs):
* **`subject_id`**: Mã giả danh người tham gia, `SUB` + 3 chữ số (Ví dụ: `SUB001`, `SUB002`; cách gán mã ở [kế hoạch quản lý dữ liệu](ethics/data_management_plan_v0.1.md) mục 2). Mã `SYN_*` (ví dụ `SYN_A`) chỉ dùng cho dữ liệu SYNTHETIC trong test/demo. Metadata phiên của logger (`packet-session-metadata-v1`) bắt buộc có `subject_id` khi ghi trên người; bản ghi bring-up không người để null kèm lý do (chốt 2026-10-29).
* **`session_id`**: Mã **buổi nghiên cứu**, `S` + 3 chữ số (Ví dụ: `S001`, `S002`).
* **`device_session_id`**: `SESSION_ID` (uint32) do firmware đặt mỗi lần MCU khởi động; khác với `session_id`. Một buổi nghiên cứu có thể có nhiều `device_session_id` khi MCU khởi động lại giữa buổi. Manifest của logger ghi tên này; `decode.json` và các file CSV của logger giữ tên wire `session_id` cho nó (chốt 2026-10-29).
* **`event_id`**: Mã một lần đo cuff đối chứng trong phiên (Ví dụ: `E01`, `E02`). Mỗi `event_id` có tối đa một cặp nhãn SBP/DBP. Trạng thái đo (nghỉ, sau vận động nếu protocol cho phép) ghi ở trường metadata riêng, không mã hóa vào `event_id` (xem [định nghĩa mẫu và nhãn](protocol/week_02_sample_label_glossary.md)).

**Ví dụ tên file dẫn xuất:**
* `SUB001_S001_E01_window.parquet` (`data/interim/`)
* `SUB001_S001_E01_processed.parquet` (`data/processed/`)

**Ví dụ raw:** `data/raw/SUB001/S001/20261105T090000123456Z/raw.bin`.

---

## 3. Đơn vị đo & Tần số lấy mẫu (Sampling Rate)

### Đơn vị tín hiệu chuẩn:
* **ECG (Tín hiệu điện tim):** Millivolt ($mV$) cho dữ liệu thiết bị. ECG/PPG của PulseDB Subset được coi là đơn vị tùy ý ($a.u.$), xem [provenance PulseDB](pulsedb_provenance.md), mục 6.
* **PPG (Tín hiệu quang thể tích):** Đơn vị tùy chỉnh / Biên độ chuẩn hóa ($a.u.$)
* **SBP (Huyết áp tâm thu):** $mmHg$
* **DBP (Huyết áp tâm trương):** $mmHg$

### Tần số lấy mẫu (Sampling Rate):
* **Thiết bị prototype (ECG và PPG):** cấu hình V1 và lý do nằm ở [interface_power_sampling_v0.md, mục 4](../configs/hardware/interface_power_sampling_v0.md); quyết định còn mở (độ rộng xung PPG) ở mục 6 của tài liệu đó. Tài liệu này không lặp lại giá trị để tránh lệch nhau.
* **PulseDB Subset (dữ liệu công khai):** $125\,Hz$ cho cả ba kênh (suy ra từ 1250 mẫu/đoạn 10 giây, khớp với bài báo PulseDB; xem [provenance PulseDB](pulsedb_provenance.md), mục 6).

---

## 4. Khả năng truy xuất nguồn gốc (Data Traceability)

Mỗi file trong `data/processed/` phải kèm theo một file metadata `.json` tương ứng cùng tên để truy xuất nguồn gốc. Mẫu dưới đây chỉ là khuôn: các giá trị trong `<...>` là chỗ điền, chưa có script xử lý dữ liệu prototype.
```json
{
  "processed_file": "SUB001_S001_E01_processed.parquet",
  "source_raw_files": ["data/raw/SUB001/S001/<recording>/raw.bin"],
  "script_used": "<script trong scripts/, ví dụ scripts/demo_week04_huy.py>",
  "config_used": "<config trong configs/, ví dụ configs/data/week04_huy.json>",
  "git_commit_hash": "<commit Git của code đã chạy>"
}
```

Ví dụ trong khuôn là cặp script/config thật hiện có cho bộ đặc trưng Tuần 4 (module `software/feature_extraction/week04.py`); script này mới chạy trên dữ liệu SYNTHETIC.
