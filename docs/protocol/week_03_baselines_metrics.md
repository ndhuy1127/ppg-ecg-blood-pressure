# Tuần 3 — giao diện B0/B1 và chỉ số đánh giá

> Huy, 2026-10-03. **Đã triển khai và kiểm thử cục bộ bằng dữ liệu giả lập**;
> chờ Linh review code và nhóm thống nhất các quyết định phương pháp còn mở.
> Tài liệu không khóa protocol, split, calibration PulseDB hay ngưỡng SQI.

## 1. Phạm vi và nguồn định nghĩa

[Kế hoạch Tuần 3](../plans/WEEK_03.md) quy định B0 là trung bình nhãn train,
B1 là hằng số từ phần hiệu chuẩn riêng trước đánh giá; tuần này kiểm tra **BP
tuyệt đối**, riêng SBP và DBP. [Glossary Tuần 2](week_02_sample_label_glossary.md)
quy định đơn vị quan sát và chronology; [RQ v0.1](../research_questions_v0.1.md)
là bản thảo cho ΔBP, Pearson, Bland–Altman và risk–coverage.

Tên B0/B1 tuần này không đồng nghĩa với số thứ tự Baseline 1/2 trong RQ v0.1.
B1 có thể tương ứng zero-change nếu mốc BP chính là trung bình hiệu chuẩn đó;
code hiện không tính ΔBP hay chứng minh kết quả cross-session.

Không có module baseline/metrics cùng chức năng trong workspace trước thay đổi.
Reader hiện có ở `software/pulsedb/` được giữ nguyên; không đọc dataset thật.

## 2. Hợp đồng đầu vào và trách nhiệm tích hợp

- Nhãn và dự đoán: mảng số thực hữu hạn `(n, 2)`, `n >= 1`, cột **[SBP, DBP]**,
  đơn vị **mmHg**. API không tự phát hiện đảo cột hoặc đổi đơn vị.
- Không nhận mảng 1 chiều dù chỉ có một cặp; dùng `[[120, 80]]`.
  Từ chối rỗng, sai shape, ragged, chuỗi số, bool, complex, `None`, NaN/Inf
  và masked array bằng `ValueError`; không tự impute hoặc loại dòng.
- ID người: mảng 1 chiều chuỗi giả danh không rỗng, không có khoảng trắng ở
  đầu/cuối; không tự ép ID số thành chuỗi hoặc chuẩn hóa ID. Khi đi cùng nhãn,
  số ID phải bằng số dòng. Không đưa định danh trực tiếp vào API/log.
- Overflow trong phép tính BP bị từ chối bằng `ValueError`. Không dùng
  bộ kiểm tra này như tiêu chí loại BP sinh lý hoặc ngưỡng protocol.
- `predict` trước `fit` gây `RuntimeError`. Mỗi lần `fit` hợp lệ **thay** state
  cũ, không tích lũy dữ liệu; fit bị lỗi giữ nguyên state đã hợp lệ.
- API chỉ tính công thức trên dữ liệu được cung cấp: **không xác minh split,
  sample/event ID, chronology hoặc nguồn nhãn** vì không nhận các metadata đó.
  Linh/Huy phải kiểm tra manifest trước khi gọi. Tên đối số train/calibration
  và việc predict không nhận nhãn giúp tách luồng, không thay validator leakage.

Một dòng đầu vào là một đơn vị quan sát đã được thống nhất. Với prototype cuff,
mỗi `(subject_id, session_id, event_id)` chỉ đóng góp một cặp nhãn; phải tổng hợp
các cửa sổ theo quy tắc khóa trước rồi gọi API. Không đưa nhiều cửa sổ cùng cuff
vào như nhiều nhãn độc lập. Với PulseDB, đơn vị đoạn ABP và việc trùng/overlap
record cần manifest được review; không tạo event cuff hoặc chronology từ thứ tự
file/dòng. Bootstrap tương lai giữ cụm người; không thực hiện trong module này.

## 3. B0 — trung bình train

Mã: `software/models/constant_baselines.py`, lớp `PopulationMeanBaseline`.

Với từng đầu ra `k ∈ {SBP, DBP}`:

```text
c_k = (1 / N_train) × Σ_i y_train[i, k]
prediction[j, k] = c_k
```

`fit(train_labels)` chỉ nhận nhãn train; `predict(n_samples)` chỉ nhận số dòng
cần dự đoán. Số dòng phải là số nguyên dương, không phải bool. Validation/test
không tính lại hằng số. Bản triển khai dùng **trọng số đều theo dòng train**,
phù hợp trung bình nhãn trong kế hoạch. Trọng số train theo người hoặc theo
đơn vị quan sát của pool công khai còn cần nhóm thống nhất trước chạy thật;
không tự chọn từ kết quả test. Trọng số fit khác trọng số báo cáo metrics.

## 4. B1 — trung bình hiệu chuẩn riêng của từng người

Mã: cùng module, lớp `PersonalMeanBaseline`.

```text
c[s, k] = (1 / N_calibration[s]) × Σ_(i thuộc calibration người s) y[i, k]
prediction[j, k] = c[subject_ids[j], k]
```

Kế hoạch chưa khóa phép tổng hợp nhiều nhãn hiệu chuẩn; theo yêu cầu tác vụ,
code dùng trung bình đều các dòng hiệu chuẩn của từng người. Đây là quy ước
triển khai để kiểm thử, chờ review trước phân tích thật.

`fit(calibration_subject_ids, calibration_labels)` nhận **phần hiệu chuẩn được
cung cấp riêng**, không nhận evaluation. `predict(subject_ids)` chỉ nhận ID,
giữ thứ tự và số lần lặp đầu vào. Có bất kỳ người chưa hiệu chuẩn thì cả lời gọi
gây `UncalibratedSubjectError` (kế thừa `ValueError`), không trả kết quả một phần,
không dùng B0 và không dùng nhãn evaluation để bổ sung. Lỗi không in ID người.

B1 chỉ thuộc kịch bản **cá nhân hóa có hiệu chuẩn**, không báo cáo như dự đoán
người mới chưa hiệu chuẩn. Phần calibration phải không trùng sample/record/event
đánh giá và phải có trước toàn bộ evaluation tương ứng. Chưa chọn calibration
PulseDB: cần metadata phiên/thời gian, quyền dùng nhãn và quy tắc của Linh/nhóm.

## 5. MAE, bias và SD

Mã: `software/evaluation/bp_metrics.py`, hàm
`evaluate_bp(reference, predictions, subject_ids)`.

Tính độc lập cho SBP và DBP, không gộp hai đầu ra:

```text
e_i = prediction_i - reference_i             [mmHg]
MAE = (1 / N) × Σ_i |e_i|                    [mmHg]
bias = (1 / N) × Σ_i e_i                     [mmHg]
SD = sqrt(Σ_i (e_i - bias)^2 / (N - 1))      [mmHg], N >= 2
```

Bias dương nghĩa là dự đoán cao hơn tham chiếu. SD là **SD mẫu, ddof=1**.
Với `N=1`, MAE/bias vẫn tính, `sd=None` (JSON `null`), nghĩa là chưa xác định;
không thay bằng 0. Với `N=0`, toàn bộ lời gọi lỗi. Cùng quy tắc cho mỗi người.

Kết quả dataclass có ba phần:

| Trường | Trọng số / cách tính | Diễn giải |
| --- | --- | --- |
| `sample_weighted` | Tính MAE/bias/SD từ tất cả dòng sai số; có `n` | Người có nhiều dòng có ảnh hưởng lớn hơn |
| `by_subject` | Tính MAE/bias/SD riêng từng ID; có `n` mỗi người | Mô tả cấu trúc đo lặp |
| `subject_balanced` | Trung bình đều MAE từng người và bias từng người; có `n_subjects` | MAE/bias chính theo kế hoạch Tuần 3, mỗi người có trọng số bằng nhau |

Nếu có `S` người: `MAE_subject_balanced = Σ_s MAE_s / S`,
`bias_subject_balanced = Σ_s bias_s / S`.
Không xuất SD macro: trung bình SD từng người không phải SD gộp, cũng không
phải SD của bias giữa người. SD hiện có chỉ là SD mô tả tất cả sai số hoặc sai
số của từng người, không phải standard error/CI và không giả định dòng độc lập.
Quy ước SD dùng cho báo cáo nghiên cứu chính vẫn cần review thống kê.

## 6. Các chỉ số mở rộng — chỉ đặc tả, chưa chạy

| Đại lượng | Đối chiếu repo và công thức/quy ước | Đầu vào và khi chưa tính được |
| --- | --- | --- |
| **beta (β)** | Không có định nghĩa β trong kế hoạch/RQ/glossary đã đọc. **Cần thống nhất** beta là hệ số gì, trục nào, đơn vị, weighting và intercept. Nếu nhóm chọn slope OLS của `Δprediction = α + β × Δreference`, công thức ứng viên là `β = Σ(x-x̄)(z-z̄) / Σ(x-x̄)²`, với `x=Δreference`, `z=Δprediction`; đây chưa phải quyết định chính thức và không được tự xuất bằng code. | Cần định nghĩa được phê duyệt, cặp ΔBP, mốc hiệu chuẩn, chronology, grouping/weighting. Slope ứng viên không xác định khi `var(x)=0` hoặc thiếu đủ cặp; không tự diễn giải β như một chỉ số đã khóa. |
| **Tương quan ΔBP** | RQ1-D đã nêu Pearson: `r = Σ(x-x̄)(z-z̄) / sqrt[Σ(x-x̄)² × Σ(z-z̄)²]`. `ΔBP = BP_future - BP_calibration`, đánh giá SBP/DBP riêng. Cách gộp theo người/phiên và CI còn chờ review. | Cần cặp Δreference/Δprediction cùng mốc cá nhân, ID phiên/người, chronology. Không tính khi thiếu mốc/thời gian, ít hơn hai cặp hoặc một vector hằng. B1 zero-change tạo Δprediction hằng 0 thì r không xác định, không phải r=0. |
| **Bland–Altman** | RQ2-D nêu biểu đồ và “khoảng tin cậy 95%”, chưa phân biệt CI với giới hạn đồng thuận (LoA). Quy ước minh họa ứng viên: trục ngang `(prediction + reference)/2`, trục dọc `e`; bias `ē`, LoA xấp xỉ `ē ± 1.96 × SD(e)` nếu giả định thích hợp. **LoA không phải CI của bias hoặc CI của LoA**. Phương pháp cho đo lặp theo người và CI chưa khóa. | Cần cặp cùng đơn vị/đại lượng, người/phiên/event, cấu trúc đo lặp và đánh giá giả định sai số. Dưới hai cặp không có SD; dữ liệu đo lặp không dùng trực tiếp công thức độc lập để tuyên bố đồng thuận. Chưa tạo hình/LoA/CI. |
| **Coverage trong selective prediction** | RQ3 định nghĩa tỷ lệ giữ lại: công thức mô tả theo mẫu `coverage = N_accepted / N_eligible`; risk là MAE trên accepted. Có thể tính `coverage_s = N_accepted_s / N_eligible_s` và trung bình đều theo người, nhưng mẫu số eligible, weighting, các người không có accepted và cách dựng/AUC đường cong **cần thống nhất**. Không nhầm với coverage của prediction interval hoặc tỷ lệ `|e| ≤ 5/10 mmHg` ở RQ1-D. | Cần toàn bộ ứng viên eligible gồm cả rejected, mask accepted, SQI/uncertainty, ngưỡng khóa từ validation, nhãn và ID để tính risk. `N_eligible=0` thì coverage không xác định; `N_accepted=0` thì MAE retained không xác định dù coverage có thể bằng 0. Không tự loại rejected khỏi mẫu số. |

Các công thức ứng viên trong bảng chỉ làm rõ lựa chọn cần review, không bổ sung
quyết định khoa học chính thức. Không chạy bootstrap, kiểm định, phân tích thật
hay tuning test trong lần này. RQ/protocol v0.1 vẫn là bản thảo.

## 7. Ví dụ và lệnh chạy lại

Chạy từ Git root, dùng môi trường đã cài dependency theo README. Ví dụ dưới đây
chỉ dùng số tự tạo; không phải nhãn cuff/ABP thật:

```python
from software.models.constant_baselines import (
    PopulationMeanBaseline, PersonalMeanBaseline,
)
from software.evaluation.bp_metrics import evaluate_bp

train = [[110, 70], [130, 90]]                 # người train SYN_TRAIN
calibration = [[118, 78], [122, 82]]          # SYN_EVAL, thời điểm 0 và 1
evaluation = [[124, 84], [126, 86]]           # SYN_EVAL, thời điểm 2 và 3
evaluation_ids = ["SYN_EVAL", "SYN_EVAL"]

b0 = PopulationMeanBaseline().fit(train)
b1 = PersonalMeanBaseline().fit(["SYN_EVAL", "SYN_EVAL"], calibration)
print(evaluate_bp(evaluation, b0.predict(2), evaluation_ids))
print(evaluate_bp(evaluation, b1.predict(evaluation_ids), evaluation_ids))
```

Script tạo dữ liệu bằng `numpy.random.default_rng(seed=20261003)`, kiểm tra
người train tách evaluation, row ID calibration không trùng evaluation và thời
điểm calibration trước evaluation **trong ví dụ giả lập**. In JSON đánh dấu
`SYNTHETIC`, seed, môi trường, đơn vị, ddof và các metrics. Các ID/thời điểm đó
không được dùng thay metadata PulseDB. Script không đọc hoặc ghi dữ liệu thật.

```powershell
.\.venv\Scripts\python.exe -m scripts.demo_week_03_baselines
.\.venv\Scripts\python.exe -m pytest -q tests/test_week_03_baselines.py tests/test_bp_metrics.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/check_environment.py
.\.venv\Scripts\python.exe -m pip check
```

Demo hỗ trợ chạy trực tiếp bằng **Run Python File in Terminal** trong VSCode,
hoặc bằng `python scripts/demo_week_03_baselines.py`. Khi chạy trực tiếp,
script thêm thư mục repo vào đường dẫn import trước khi gọi code trong
`software`. Cách chạy module `-m scripts.demo_week_03_baselines` vẫn hoạt động.
Không cần cài thêm dependency. Nếu dùng Python 3.11 theo README, có thể thay
đường dẫn interpreter bằng `python` đã kích hoạt.
Seed cố định giúp lặp lại trong cùng môi trường; không cam kết mọi phiên bản
NumPy/Python cho số thực trùng từng bit. Demo chứng minh code/công thức, không
cho phép kết luận baseline tốt, PAT hữu ích hoặc đạt tiêu chuẩn thiết bị.

**Cách tùy chọn qua Run and Debug (cấu hình cục bộ thêm ngày 2026-10-05):** mở thư
mục repository, chọn **Run and Debug** (`Ctrl+Shift+D`), chọn **Demo B0/B1 -
Tuan 3** rồi bấm nút tam giác hoặc nhấn `F5`. Để chạy các test mới, chọn **Test
B0/B1 va metrics - Tuan 3**. Kết quả hiện trong Terminal. Cấu hình tại
`.vscode/launch.json` dùng interpreter `.venv` của repo và chạy theo module từ
root. Cần extension Python và Python Debugger; đã xác nhận hai extension có
trong danh sách cài cục bộ. Chưa thao tác trực tiếp nút giao diện để xác minh.
`.vscode/` đang được Git ignore, nên cấu hình này chỉ có trên workspace hiện tại.

Kết quả chạy và đầu vào còn chờ nằm trong
[báo cáo Huy Tuần 3](../../reports/weekly/week_03/README.md).
