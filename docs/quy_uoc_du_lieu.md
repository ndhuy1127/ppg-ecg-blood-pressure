# Quy ước Quản lý và Cấu trúc Dữ liệu

Tài liệu này quy định chuẩn quản lý, đặt tên và cấu trúc dữ liệu cho dự án PPG-ECG Blood Pressure Estimation.

---

## 1. Phân loại thư mục dữ liệu

Dữ liệu dự án được phân chia nghiêm ngặt theo 4 cấp độ:

* `data/raw/`: Dữ liệu gốc thu thập từ thiết bị đo. Tuyệt đối **KHÔNG** chỉnh sửa hay xóa file trong thư mục này.
* `data/interim/`: Dữ liệu thô đã qua xử lý sơ bộ (lọc nhiễu ban đầu, cắt bớt đoạn nhiễu nặng, định dạng lại timestamp).
* `data/processed/`: Dữ liệu hoàn chỉnh đã trích xuất đặc trưng (features), đồng bộ PPG/ECG và nhãn SBP/DBP, sẵn sàng cho huấn luyện mô hình ML/DL.
* `data/results/`: Kết quả đầu ra từ mô hình (dự đoán, trọng số model, metrics đánh giá).

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
* **ECG (Tín hiệu điện tim):** Millivolt ($mV$)
* **PPG (Tín hiệu quang thể tích):** Đơn vị tùy chỉnh / Biên độ chuẩn hóa ($a.u.$)
* **SBP (Huyết áp tâm thu):** $mmHg$
* **DBP (Huyết áp tâm trương):** $mmHg$

### Tần số lấy mẫu (Sampling Rate):
> ⚠️ **LƯU Ý:** Các thông số tần số lấy mẫu dưới đây hiện ở dạng **ĐỀ XUẤT** và chờ Hội đồng/Lead duyệt chính thức.

* **ECG:** Đề xuất $500\,Hz$
* **PPG:** Đề xuất $100\,Hz$ hoặc $125\,Hz$

---

## 4. Khả năng truy xuất nguồn gốc (Data Traceability)

Mỗi file trong `data/processed/` phải kèm theo một file metadata `.json` tương ứng cùng tên để truy xuất nguồn gốc:
```json
{
  "processed_file": "SUB001_S001_E01_processed.parquet",
  "source_raw_files": ["SUB001_S001_E01_raw.csv"],
  "script_used": "src/features/extract_features.py",
  "config_used": "configs/feature_extraction_v1.yaml",
  "git_commit_hash": "a1b2c3d4e5f6..."
}