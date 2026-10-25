# Evaluation — chỉ số sai số huyết áp

Ngoài `bp_metrics.py` (dưới đây) và `subject_bootstrap.py`, thư mục có
[fiducial_agreement.py](fiducial_agreement.py) (Tuần 5): so mốc R/foot tự động với
đánh dấu tay, chỉ train/val. Mô tả đầu vào/đầu ra ở
[week05_fiducials_pat_validity.md](../../docs/protocol/week05_fiducials_pat_validity.md),
mục 4.

[fiducial_gate.py](fiducial_gate.py) (Tuần 5): cổng nghiệm thu mốc đăng ký trước.
`gate` chấm mọi phương án trên nhóm chọn, giữ phương án đạt mọi ngưỡng có MAE trung
bình theo người thấp nhất, rồi chỉ chấm phương án đó một lần trên nhóm xác nhận;
`repeatability` so hai lượt đánh dấu của cùng người cách nhau ít nhất `min_days`.
Ngưỡng nằm trong khối `acceptance` của `configs/data/week05_huy.json`; mô tả ở
[week05_fiducials_pat_validity.md](../../docs/protocol/week05_fiducials_pat_validity.md),
mục 9.

[bp_metrics.py](bp_metrics.py) chứa hàm đánh giá và các lớp chứa kết quả.
Demo/pipeline gọi hàm với nhãn và dự đoán; chạy riêng file không tự tạo dữ liệu
hay in báo cáo.

## Đầu vào

Hàm chính: `evaluate_bp(reference, predictions, subject_ids)`.

| Đối số | Dữ liệu cần cung cấp |
| --- | --- |
| `reference` | Nhãn tham chiếu, số thực hữu hạn `(n, 2)` |
| `predictions` | Dự đoán, cùng shape `(n, 2)` với reference |
| `subject_ids` | Chuỗi mã người giả danh `(n,)` để tổng hợp theo người |

Cột theo thứ tự **[SBP, DBP]**, đơn vị **mmHg**, `n >= 1`. Sai số là
`prediction - reference`. Đầu vào thiếu, sai shape hoặc NaN/Inf gây
`ValueError`; hàm không tự bỏ dòng. Caller phải kiểm tra đơn vị quan sát và
trùng cuff event trước khi gọi; hàm không nhận event ID hay thông tin split.

## Nội dung và kết quả trả về

| Thành phần trong file | Vai trò |
| --- | --- |
| `TARGETS` | Thứ tự hai đầu ra `SBP`, `DBP` |
| `ErrorMetrics` | Chứa `n`, `mae`, `bias`, `sd` cho một nhóm mẫu và một đầu ra |
| `SubjectBalancedMetrics` | Chứa `n_subjects`, MAE và bias trung bình đều theo người |
| `BPEvaluation` | Gom các cách tổng hợp vào một đối tượng kết quả |
| `_summarize(errors)` | Hàm phụ tính MAE/bias/SD cho một nhóm sai số |
| `evaluate_bp(...)` | Kiểm tra input, tính sai số, nhóm theo người và trả `BPEvaluation` |

MAE là trung bình độ lớn sai số; bias là trung bình sai số có dấu. SD là độ
lệch chuẩn mẫu của sai số (`ddof=1`). Tính riêng SBP/DBP. Với một mẫu,
`sd=None` (JSON `null`); không thay bằng 0.

| Trường trong `BPEvaluation` | Ý nghĩa |
| --- | --- |
| `sample_weighted` | Metrics từ tất cả dòng; người có nhiều dòng ảnh hưởng nhiều hơn |
| `by_subject` | Metrics riêng cho mỗi ID, kèm số mẫu của người đó |
| `subject_balanced` | Trung bình đều MAE/bias của từng người; không có SD macro |

## Ví dụ sử dụng với dữ liệu giả lập

Chạy trong Python từ Git root:

```python
from software.evaluation.bp_metrics import evaluate_bp

result = evaluate_bp(
    reference=[[120, 80], [120, 80], [120, 80]],
    predictions=[[118, 81], [120, 79], [122, 83]],
    subject_ids=["SYN_A", "SYN_A", "SYN_A"],
)
print(result.sample_weighted["SBP"])
# ErrorMetrics(n=3, mae=1.3333333333333333, bias=0.0, sd=2.0)
```

Để xem toàn bộ JSON bằng nút VSCode, chạy
[demo_week_03_baselines.py](../../scripts/demo_week_03_baselines.py).
File metrics không chứa dataset, không tự đọc/ghi dữ liệu hay lưu báo cáo;
dữ liệu tham chiếu, dự đoán và kết quả chỉ được xử lý trong bộ nhớ.

Công thức đầy đủ và cách xử lý đo lặp nằm trong
[quy ước phương pháp](../../docs/protocol/week_03_baselines_metrics.md).
SD mô tả không phải CI; module này không tính bootstrap (xem
[subject_bootstrap.py](subject_bootstrap.py)), beta, Pearson ΔBP,
Bland–Altman hay coverage.
