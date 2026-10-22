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
| [test_pulsedb.py](test_pulsedb.py) | Reader: file thiếu, sai số kênh, thứ tự kênh/dòng, trường bắt buộc/tùy chọn thiếu (NaN, không điền 0), độ dài trường, file một đoạn, gender M/F/lạ/thiếu, cell array dạng list, Subject nhiều giá trị, `limit`. Validator: waveform trùng, nhãn bất thường, tuổi thiếu, lệch độ dài kênh, token thiếu ID dùng chung với split | File tạm rỗng; mock `mat73.loadmat` trả Subset SYNTHETIC |
| [test_b0_pulsedb_csv.py](test_b0_pulsedb_csv.py) | Runner B0 trên CSV: fit chỉ trên train và metrics val tính tay, từ chối giao người/hash/waveform giữa split, nhãn val lỗi, thiếu split/header, config mặc định tương đối repo và yêu cầu xác nhận đơn vị | CSV nhãn SYNTHETIC |
| [test_split_manifest.py](test_split_manifest.py) | Validator đối chiếu inventory từ chối mất/thêm/trùng mẫu và leakage; hash/sort/tái lập; runner kế thừa reader và không ghi đè | SYNTHETIC, MAT loader mock, output trong thư mục tạm |
| [test_b3_pipeline.py](test_b3_pipeline.py) | Đặc trưng khớp tính tay và không đọc ABP/nhãn; B3 tái lập; pipeline từ chối leakage/hash sai/thiếu dòng/raw khác inventory; thay nhãn val/test hoặc waveform test không đổi dự đoán; runner tái lập và không ghi đè | Chỉ SYNTHETIC `SYN_*`; reader mock, output trong thư mục tạm |
| [test_week04_features.py](test_week04_features.py) | Mốc R/foot và PAT trên fixture giải tích nhiều fs, cờ SQI, nhịp sát biên không bị tính là không ghép, độ lệch foot của lọc zero-phase, timestamp/masked/gaps, provenance fixture | Fixture SYNTHETIC từ `scripts/demo_week04_huy.py` |
| [test_week05_fiducials.py](test_week05_fiducials.py) | Phương pháp mốc Tuần 5 (R ở 125/500 Hz, nội suy dưới mẫu, đoạn phẳng, kênh bị loại), PAT gắn nhãn chứ không xóa, quy tắc MAD, ghép một–một, vùng review, từ chối split test và đáp án SYNTHETIC, provenance và không ghi đè của script, `annotate` | Chỉ SYNTHETIC `SYN_*`; output trong thư mục tạm |
| [test_subject_bootstrap.py](test_subject_bootstrap.py) | Bootstrap theo người: cluster lặp, cùng draws cho mọi model, trường hợp ít người/suy biến, bảng dự đoán đối chiếu manifest | ID và dự đoán SYNTHETIC |
| [test_check_environment.py](test_check_environment.py) | So sánh `requires-python` và pin của `scripts/check_environment.py` | Chuỗi requirement tự tạo |
| [test_packet_simulation.py](test_packet_simulation.py) | Sáu case packet, decoder validation, dữ liệu/timeline/gap/offset, tái lập và CLI | Chỉ SYNTHETIC; config và expected fixture, output tạm |
| [test_packet_logger.py](test_packet_logger.py) | CRC-16/CCITT-FALSE known-answer và oracle `binascii`; packet ghép tay; 13 case `synthetic-packet-v3`; `T_FIRST_US`; chia đoạn byte bất kỳ; rác/`SYNC` giả, không nhảy theo độ dài khai báo, một packet hỏng là một lỗi, đuôi cụt/`0xA5` lẻ, header vô lý; xung đột, mất liền nhiều packet, tràn 2³², index nhảy/lùi/vượt 32 mẫu mỗi packet vắng, neo lại lùi (`chain_id`), `FS = 0`, dữ liệu ngoài dải, bit STATUS dự trữ; anchor không tăng, anchor đầu/cuối sai, bước nhảy kéo dài, drift ±3 % qua khoảng mất, quy tắc `0xC1`; không báo offset cho `DEVICE`; metadata/config sai; record/replay cùng hash, mở exclusive, manifest ghi sau cùng, CLI | Chỉ SYNTHETIC; `tests/fixtures/packet_v3_expected.json` (đáp án suy tay), output tạm |

Mock trong `test_pulsedb.py` chưa chứng minh reader đọc đúng mọi file PulseDB
thật. Kết quả test không chứng minh split PulseDB, calibration hoặc phần cứng đã
được nghiệm thu.

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
