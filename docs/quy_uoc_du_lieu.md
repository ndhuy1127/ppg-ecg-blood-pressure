# Quy ước Dữ liệu và Đặt tên Tệp (Data & File Conventions)

## 1. Cấu trúc thư mục dữ liệu (`data/`)
- `data/raw/`: Dữ liệu thô ban đầu (chỉ đọc, không chỉnh sửa trực tiếp).
- `data/processed/`: Dữ liệu đã qua tiền xử lý (lọc nhiễu, cắt đoạn, trích xuất đặc trưng).
- `data/interim/`: Dữ liệu trung gian trong quá trình thực nghiệm.

## 2. Quy tắc đặt tên file
- **Cấu trúc:** `<loai_du_lieu>_<subject_id>_<lan_thu>.<dinh_dang>`
- **Ví dụ:** `ppg_sub001_trial01.csv`, `ecg_sub001_trial01.npy`
- **Quy tắc:** Viết chữ thường, phân cách bằng dấu gạch dưới (`_`), không dùng tiếng Việt có dấu, không khoảng trắng.
