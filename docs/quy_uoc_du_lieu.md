# Quy ước Quản lý và Cấu trúc Dữ liệu

Tài liệu này quy định chuẩn quản lý, đặt tên và cấu trúc dữ liệu cho dự án PPG-ECG Blood Pressure Estimation.

---

## 1. Phân loại thư mục dữ liệu

Dữ liệu dự án được phân chia nghiêm ngặt theo 3 cấp độ, cộng một thư mục riêng cho kết quả chạy. Cả bốn thư mục đều bị Git bỏ qua (`.gitignore`):

* `data/raw/`: Dữ liệu gốc thu thập từ thiết bị đo. Tuyệt đối **KHÔNG** chỉnh sửa hay xóa file trong thư mục này.
* `data/interim/`: Dữ liệu thô đã qua xử lý sơ bộ (lọc nhiễu ban đầu, cắt bớt đoạn nhiễu nặng, định dạng lại timestamp).
* `data/processed/`: Dữ liệu hoàn chỉnh đã trích xuất đặc trưng (features), đồng bộ PPG/ECG và nhãn SBP/DBP, sẵn sàng cho huấn luyện mô hình ML/DL.
* `runs/` (ở gốc repository, ngoài `data/`): Kết quả chạy mô hình (dự đoán, model, metrics, provenance). Runner `scripts/run_b0_pulsedb_csv.py` và `scripts/run_b3_pulsedb.py` mặc định ghi vào `runs/` và từ chối ghi đè output đã có. File dự đoán theo dòng chứa `subject_id`, nên không commit.

---

## 2. Quy ước đặt tên File & Định danh

Mọi file dữ liệu phải tuân theo cấu trúc tên thống nhất:

$$\text{<subject\_id>\_<session\_id>\_<event\_id>\_<data\_type>.<ext>}$$

### Định danh (IDs):
* **`subject_id`**: Mã tình nguyện viên/người tham gia (Ví dụ: `SUB001`, `SUB002`).
* **`session_id`**: Mã phiên đo (Ví dụ: `S001`, `S002`).
* **`event_id`**: Mã một lần đo cuff đối chứng trong phiên (Ví dụ: `E01`, `E02`). Mỗi `event_id` có tối đa một cặp nhãn SBP/DBP. Trạng thái đo (nghỉ, sau vận động nếu protocol cho phép) ghi ở trường metadata riêng, không mã hóa vào `event_id` (xem [định nghĩa mẫu và nhãn](protocol/week_02_sample_label_glossary.md)).

**Ví dụ tên file chuẩn:**
* `SUB001_S001_E01_raw.csv`
* `SUB001_S001_E01_processed.parquet`

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
  "source_raw_files": ["SUB001_S001_E01_raw.csv"],
  "script_used": "<script trong scripts/, ví dụ scripts/demo_week04_huy.py>",
  "config_used": "<config trong configs/, ví dụ configs/data/week04_huy.json>",
  "git_commit_hash": "<commit Git của code đã chạy>"
}
```

Ví dụ trong khuôn là cặp script/config thật hiện có cho bộ đặc trưng Tuần 4 (module `software/feature_extraction/week04.py`); script này mới chạy trên dữ liệu SYNTHETIC.
