# Models — baseline B0/B1/B3

B3 (`XGBoostBaseline` trong [xgboost_baseline.py](xgboost_baseline.py)) có API
`fit(train_features, train_labels)`, `predict(features)` và `save(directory)`.
Xem [hướng dẫn B0/B3](../../docs/protocol/run_b3_pulsedb.md). Phần dưới mô tả B0/B1.

[constant_baselines.py](constant_baselines.py) chứa hai lớp dự đoán **BP tuyệt
đối**, riêng SBP và DBP. File này được demo/pipeline import; không tự đọc
dataset hoặc in kết quả khi bấm chạy riêng.

## Các lớp và dữ liệu đầu vào/đầu ra

| Thành phần | Đầu vào | Xử lý và đầu ra |
| --- | --- | --- |
| `PopulationMeanBaseline.fit(train_labels)` | Nhãn train `(n, 2)` | B0 tính trung bình từng cột và lưu một cặp hằng số; trả lại đối tượng model |
| `PopulationMeanBaseline.predict(n_samples)` | Số nguyên dương | Trả mảng `(n_samples, 2)`, mọi dòng bằng cặp hằng số train |
| `PersonalMeanBaseline.fit(calibration_subject_ids, calibration_labels)` | ID người `(n,)` và nhãn hiệu chuẩn `(n, 2)` | B1 tính trung bình từng cột cho từng người, lưu ánh xạ ID → cặp hằng số; trả model |
| `PersonalMeanBaseline.predict(subject_ids)` | ID người cần dự đoán `(m,)` | Trả mảng `(m, 2)`, giữ thứ tự ID; mỗi người dùng hằng số hiệu chuẩn của mình |
| `UncalibratedSubjectError` | Phát sinh khi B1 gặp người chưa hiệu chuẩn | Báo lỗi cho cả lời gọi; không tự chuyển sang B0 hoặc lấy nhãn evaluation |

Cột luôn là **[SBP, DBP]**, đơn vị **mmHg**. Nhãn phải là số thực hữu hạn,
`n >= 1`; danh sách ID phải là chuỗi không rỗng và khớp số dòng. Kiểm tra kỹ
thuật được dùng chung từ [_bp_validation.py](../_bp_validation.py).

`fit` chỉ nhận train hoặc calibration riêng; `predict` không nhận nhãn thật
của evaluation. Gọi `predict` trước `fit` gây `RuntimeError`. Dữ liệu không hợp
lệ gây `ValueError`. Mỗi lần fit hợp lệ thay hằng số cũ, không cộng dồn dữ liệu.

## Ví dụ bằng số giả lập

Chạy các câu lệnh này trong Python từ Git root để import được `software`:

```python
from software.models.constant_baselines import (
    PopulationMeanBaseline, PersonalMeanBaseline,
)

b0 = PopulationMeanBaseline().fit([[110, 70], [130, 90]])
print(b0.predict(2))
# [[120.  80.]
#  [120.  80.]]

b1 = PersonalMeanBaseline().fit(
    ["SYN_A", "SYN_A", "SYN_B"],
    [[110, 70], [130, 80], [140, 90]],
)
print(b1.predict(["SYN_B", "SYN_A"]))
# [[140.  90.]
#  [120.  75.]]
```

Muốn chạy bằng nút VSCode, mở
[demo_week_03_baselines.py](../../scripts/demo_week_03_baselines.py) và bấm
**Run Python File in Terminal**; xem [hướng dẫn demo](../../scripts/README.md).

## Dữ liệu được lưu và giới hạn

B0 giữ một cặp hằng số trong `_constant`; B1 giữ các cặp hằng số theo người
trong `_constants`. Đây là dữ liệu trong bộ nhớ, không phải model artifact
được ghi ra đĩa; file `.py` không chứa dữ liệu người tham gia.

B0 mặc định dùng trung bình đều theo dòng train; truyền `sample_weight` 1/n_s (như
`b3-pipeline-v1`, 2026-10-25) thì thành trung bình của các trung bình theo người
([quy ước Tuần 3](../../docs/protocol/week_03_baselines_metrics.md)). B1 dùng trung bình đều các dòng
hiệu chuẩn của từng người và thuộc kịch bản cá nhân hóa có hiệu chuẩn. Caller
phải xác minh split, không trùng record/event và calibration có trước evaluation;
API không nhận metadata để tự chứng minh các điều kiện đó. Quy tắc dataset thật
và trọng số chưa chốt cho phân tích. Xem
[quy ước phương pháp](../../docs/protocol/week_03_baselines_metrics.md).
