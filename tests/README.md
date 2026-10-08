# Tests — kiểm tra code bằng dữ liệu nhỏ

Các file `test_*.py` chứa hàm kiểm tra được pytest gọi, không phải chương trình
demo để bấm Run Python File và xem metrics. Fixture là dữ liệu nhỏ do code tạo;
không có dataset thật hoặc dữ liệu người tham gia trong những test bên dưới.

## Mỗi file kiểm tra gì

| File | Nội dung kiểm tra | Dữ liệu sử dụng |
| --- | --- | --- |
| [test_week_03_baselines.py](test_week_03_baselines.py) | B0/B1 đúng hằng số, thay nhãn evaluation không đổi dự đoán, B1 từ chối người chưa hiệu chuẩn, input lỗi và state model | Nhãn BP và ID giả lập, kể cả input lỗi có chủ đích |
| [test_bp_metrics.py](test_bp_metrics.py) | MAE/bias/SD khớp tính tay; weighting theo mẫu/người, trường hợp một mẫu, input lỗi, demo tái lập và chạy trực tiếp | Mảng số tự tạo; subprocess chạy demo trong isolated mode từ `scripts/` |
| [test_smoke.py](test_smoke.py) | Import package, cấu trúc thư mục và phép tính NumPy | Mảng `[1.0, 2.0, 3.0, 4.0]`, đường dẫn package |
| [test_pulsedb.py](test_pulsedb.py) | File thiếu, kiểm tra khóa trùng trên mảng tự tạo, reader từ chối sai số kênh và nhận gender M/F | File tạm rỗng; mock `mat73.loadmat` trả dữ liệu giả lập |

Test khóa trùng trong `test_pulsedb.py` chưa chứng minh reader phát hiện trùng
metadata trên dataset thật. Kết quả test không chứng minh split PulseDB,
calibration hoặc phần cứng đã được nghiệm thu.

## Cách chạy và đầu ra

Từ Git root, dùng môi trường đã cài dependency:

```powershell
# Chỉ kiểm tra code B0/B1, metrics và demo:
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_week_03_baselines.py tests/test_bp_metrics.py

# Kiểm tra toàn bộ repo:
.\.venv\Scripts\python.exe -m pytest -q
```

Pytest in tiến độ và số test `passed`, `failed` hoặc `errors`, không xuất bảng
hiệu năng BP. `-p no:cacheprovider` chỉ tắt ghi cache, không tắt các test; phù
hợp khi sandbox hạn chế quyền cache. Test dùng `tmp_path` vẫn cần truy cập thư
mục tạm. Không sửa hoặc bỏ test để che lỗi quyền truy cập.

Trong VSCode có thể chạy bằng mục **Testing** sau khi cấu hình Python/pytest,
hoặc cấu hình test cục bộ ở **Run and Debug** nếu có. Để xem B0/B1 và metrics
ngay bằng nút Run Python File, mở
[demo_week_03_baselines.py](../scripts/demo_week_03_baselines.py) theo
[hướng dẫn demo](../scripts/README.md).

Công thức và định dạng đầu vào:
[quy ước B0/B1 và metrics](../docs/protocol/week_03_baselines_metrics.md).
