# Báo cáo tiến độ Tuần 2

> **Giai đoạn:** Tuần 2 / 28 tuần
> **Người tổng hợp:** Nguyễn Đức Huy
> **Vai trò:** Xử lý tín hiệu, PAT, phương pháp thống kê, protocol, tổng quan y văn và điều phối báo cáo
> **Ngày báo cáo:** 2026-09-26 (mốc báo cáo gốc)
> **Ngày rà soát bằng chứng:** 2026-10-01
> **Ngày cập nhật bố cục:** 2026-10-08. Giữ các mốc bằng chứng lịch sử; bản thảo chưa đồng nghĩa đã được review, khóa schema/cửa sổ hoặc phê duyệt protocol.

---

## 1. Mục tiêu tuần 2

Theo [kế hoạch Tuần 2](../../../docs/plans/WEEK_02.md), các mục tiêu trọng tâm gồm:

1. Xây dựng và kiểm thử reader PulseDB, xác nhận nguồn/quyền sử dụng và khảo sát ít nhất 1.000 đoạn ECG, PPG, ABP.
2. Chuẩn bị thiết kế phần cứng v0 trên tài liệu: BOM, sơ đồ khối, pin map, nguồn/mức logic, cấu hình lấy mẫu dự kiến và kế hoạch bring-up.
3. Hoàn thiện bản thảo định nghĩa mẫu, nhãn, cửa sổ, PAT/PTT/PEP/PWA và giới hạn diễn giải PAT.
4. Đối chiếu giao diện logger → pipeline, schema metadata, clock/timestamp và liên kết nhãn với Linh, Đức Anh.
5. Tổng hợp bằng chứng, review chéo và ghi rõ các việc chuyển tiếp do chưa có phần cứng.

Các mục tiêu trên không phải kết quả đã nghiệm thu; PulseDB không thay bản ghi thiết bị của nhóm.

---

## 2. Thành viên phụ trách và Phân công công việc

| Công việc | Người phụ trách chính | Reviewer dự kiến | Trạng thái ghi nhận |
| --- | --- | --- | --- |
| Reader, notebook, metadata/nhãn và test PulseDB | Linh | Huy, Đức Anh | Có đầu ra ở ref cục bộ; chưa có bằng chứng Huy chạy lại/review hoàn tất |
| Thiết kế v0, packet schema, pin map và kế hoạch bring-up | Đức Anh | Huy, Linh | Có tài liệu ở ref cục bộ; chưa khóa giao diện hoặc xác nhận bản ghi v0 hợp lệ |
| Thuật ngữ, mẫu/nhãn, cửa sổ, schema đề xuất và quy trình kiểm tra | Huy | Linh, Đức Anh | Đã có bản thảo; chờ review chéo và quyết định của nhóm |
| Tổng hợp báo cáo Tuần 2 | Huy | Cả nhóm | Đã có báo cáo tiến độ; chưa nghiệm thu toàn bộ Tuần 2 |

### Phạm vi bằng chứng rà soát

- Workspace `develop` và `dev/huy` ở `ae67fb9` (2026-09-26). Ref cục bộ `origin/develop` ở `e8915f6`, `origin/dev/ngoclinh` ở `100ec92`, `origin/dev/ducanh` ở `e13d669` (2026-09-30).
- Đọc bằng Git mà không chuyển nhánh/merge; chưa fetch hoặc xác nhận trực tiếp GitHub. Đường dẫn thuộc ref mới có thể chưa tồn tại trong workspace.
- Chưa có bằng chứng Huy chạy lại reader/notebook, review packet hoặc nhóm nghiệm thu. Không ghi công việc của Linh/Đức Anh là kết quả của Huy.

---

## 3. Công việc đã hoàn thành của Huy

Dấu tích xác nhận đã soạn bản thảo hoặc chuẩn bị biểu mẫu, không xác nhận phê duyệt khoa học hay kiểm tra thiết bị thật.

- [x] **Thuật ngữ sinh lý:** Soạn PAT, PTT, PEP, PWA và giới hạn PAT từ R peak đến PPG foot.
- [x] **Đơn vị quan sát và nhãn:** Soạn định nghĩa người, phiên, lần cuff, cửa sổ và nhịp; một lần cuff hợp lệ tạo tối đa một cặp nhãn BP độc lập.
- [x] **Cửa sổ ứng viên:** Đề xuất 10/20/30/60 giây trước mốc bắt đầu bơm cuff; cửa sổ chính chưa khóa.
- [x] **Chống rò rỉ:** Soạn quy tắc chia theo người, calibration trước evaluation và bootstrap theo người; không tuning trên test.
- [x] **Metadata và nguồn nhãn:** Có bảng schema đề xuất, phân biệt ABP công khai, cuff prototype và dữ liệu mô phỏng.
- [x] **Phiếu kiểm tra tín hiệu:** Chuẩn bị trình tự kiểm tra timestamp, R peak, trôi nền, PPG foot và ghép nhịp; chưa áp dụng trên bản ghi v0.
- [x] **Báo cáo tiến độ:** Tổng hợp bằng chứng, việc còn chờ và quyết định cần nhóm xác nhận.

Review PulseDB và kiểm tra waveform v0 vẫn chưa hoàn thành; chi tiết ở mục 5 và mục 7.

---

## 4. Danh mục sản phẩm đầu ra và Đường dẫn

| STT | Tên sản phẩm | Đường dẫn tương đối | Trạng thái |
| --- | --- | --- | --- |
| 1 | Mục tiêu, phụ thuộc và blocker Tuần 2 | [Kế hoạch Tuần 2](../../../docs/plans/WEEK_02.md) | Kế hoạch đã ghi thiếu phần cứng; chưa phải bằng chứng hoàn thành việc của cả nhóm |
| 2 | Thuật ngữ, đơn vị quan sát, cửa sổ, chống rò rỉ, schema đề xuất và quy trình kiểm tra | [Tài liệu phương pháp của Huy](../../../docs/protocol/week_02_sample_label_glossary.md) | Bản thảo đã có nội dung, chờ Linh và Đức Anh review giao diện |
| 3 | Báo cáo tiến độ Tuần 2 | [reports/weekly/week_02/README.md](README.md) | Đã tổng hợp; chưa đóng Tuần 2 |

---

## 5. Tóm tắt các nội dung chuyên môn chính

### 5.1. Thuật ngữ, mẫu/nhãn và giao diện dữ liệu

Trạng thái trong bảng phân biệt bản thảo, review và kiểm chứng thực nghiệm; chưa có bằng chứng reviewer phê duyệt hoặc nhóm nghiệm thu.

| Phần việc của Huy | Trạng thái sau rà soát | Bằng chứng / phần còn lại |
| --- | --- | --- |
| Tổng hợp PAT, PTT, PEP, PWA và giới hạn PAT | Đã soạn bản thảo; chờ review | Mục 1 tài liệu phương pháp; PAT từ R peak đến PPG foot, công thức PEP + PTT chỉ là cách viết gọn và không đo riêng hai thành phần. |
| Định nghĩa người, phiên, lần cuff, quan sát BP, cửa sổ và nhịp | Đã soạn bản thảo; chờ review | Mục 2 tài liệu phương pháp nêu các khóa `subject_id`, `session_id`, `event_id`, `window_id` và beat index/timestamp. |
| Một lần cuff và nhiều cửa sổ dùng chung SBP/DBP | Đã soạn bản thảo; chờ review | Mục 2: một lần cuff hợp lệ tạo tối đa một cặp nhãn độc lập; các cửa sổ cùng `event_id` không thành nhiều quan sát BP độc lập. |
| Đề xuất cửa sổ 10/20/30/60 giây | Đã soạn bản thảo; chờ review | Mục 3: cửa sổ trước `t0`, `window_start`/`window_end`; cửa sổ chính chưa được khóa. |
| Quy tắc chống rò rỉ và chia tập theo người | Đã soạn bản thảo; chờ review | Mục 4: nhóm theo `subject_id`, hiệu chuẩn trước kiểm tra theo thời gian, không tuning trên test và bootstrap theo người. |
| Đề xuất schema nhãn và metadata | Đã đề xuất; có đầu vào để review, chưa khóa | Mục 5 đã có bảng trường/đơn vị; Linh, Đức Anh và Huy cần đối chiếu reader/packet/clock mới. |
| Phân biệt PulseDB ABP với nhãn cuff và dữ liệu mô phỏng | Đã soạn bản thảo; chờ review | Mục 6 phân biệt `public_abp`, `prototype_cuff`, `simulation`; không gán đoạn ABP thành event cuff. |
| Chuẩn bị quy trình kiểm tra R peak, trôi nền, PPG foot, timestamp và ghép nhịp | Đã chuẩn bị phiếu; chưa kiểm tra bản ghi v0 | Mục 7 có trình tự và phiếu chờ bản ghi v0. Chưa có kết quả kiểm tra tín hiệu prototype. |
| Review trực quan PulseDB từ đầu ra của Linh | Đã có đầu ra để review; chưa có bằng chứng Huy review | Ref `origin/develop@e8915f6` có reader/notebook/test; còn cần checksum, hướng dẫn chạy sạch và bằng chứng tái lập ít nhất 1.000 đoạn. |
| Cập nhật báo cáo Tuần 2 với bằng chứng và blocker | Đã cập nhật báo cáo; chưa đóng Tuần 2 | Báo cáo này ghi kết quả rà soát, việc chờ bàn giao và điểm cần nhóm quyết định. |

Tài liệu đã bổ sung quy tắc chống rò rỉ, mức bắt buộc/đơn vị metadata và quy trình kiểm tra. Các nội dung vẫn là bản thảo chờ review; protocol, schema và ngưỡng chưa được nhóm phê duyệt.

### 5.2. Đối chiếu PulseDB và công việc chờ Linh

- Nhận định “chưa có reader/notebook” là trạng thái báo cáo gốc 2026-09-26, không còn mô tả đầy đủ các ref mới. `origin/develop@e8915f6` có `software/pulsedb/`, `tests/test_pulsedb.py`, `notebooks/01_eda_and_visualization.ipynb`, `docs/pulsedb_provenance.md`. **Đã có đầu ra để Huy bắt đầu review**, chưa chứng minh chạy lại/nghiệm thu.
- Provenance còn ghi file sử dụng và checksum sẽ hoàn thiện. Test metadata trùng hiện kiểm tra khóa trên mảng tự tạo, chưa chứng minh reader phát hiện trùng. Notebook có tham chiếu `mat_files`, `subset`, `signals_1000` mà chưa thấy bước định nghĩa trong các cell đã đọc; cần chạy lại từ kernel sạch. Chưa xác minh độc lập nguồn/quyền sử dụng hoặc dữ liệu trong lần sửa tài liệu.
- Huy cần Linh bàn giao nguồn/phiên bản và quyền sử dụng phần PulseDB, checksum manifest, hướng dẫn chạy reader/notebook, test file thiếu/metadata trùng/sai kênh, bảng ánh xạ subject/kênh/đơn vị/tần số/nhãn và bằng chứng số đoạn đọc thành công. Sau đó Huy mới chạy lại, ghi mã commit/phiên bản, lỗi và nhận xét review.
- Nếu dùng PulseDB để minh họa lỗi tín hiệu, mọi hình/bảng phải ghi rõ **dữ liệu công khai, không phải tín hiệu do prototype của nhóm thu**. ABP waveform và nhãn dẫn xuất từ ABP không phải nhãn cuff của thiết kế prototype.

### 5.3. Đối chiếu thiết kế v0 và công việc chờ Đức Anh

- `origin/dev/ducanh@e13d669` có `configs/hardware/Packet_Schema_V0.1.md`, `hardware/bom/BOM_V0.1_with_PinMap.xlsx`, `configs/hardware/Quy trinh bring-up.docx`. Đã đọc packet Markdown; chưa thẩm định XLSX/DOCX. Packet đề xuất ECG 512 SPS, PPG AFE/tần số chưa chốt. Huy cần review khác biệt với protocol cũ, timestamp lấy mẫu/FIFO/nhận gói, clock và marker cuff; chưa có quyết định khóa giao diện.
- Chưa có bằng chứng bản ghi raw v0 hợp lệ hoặc kết quả kiểm thử phần cứng được bàn giao; tình trạng có/mua/mượn phần cứng thực tế cần Đức Anh xác nhận. Phiếu mục 7 vẫn **chờ bản ghi v0**, chưa kiểm tra timestamp, R peak, PPG foot, nhiễu, bão hòa, mất mẫu hoặc ghép nhịp thực.
- Sau khi nhận phần cứng, hoàn tất bring-up và điều kiện an toàn/phê duyệt cần thiết, mới thực hiện kiểm tra trên bản ghi được phép dùng và ghi manifest, reviewer, lỗi. **Chưa đạt điểm kiểm soát gốc “có tín hiệu v0 đầu tiên”; PulseDB không thay thế bản ghi thiết bị.**

---

## 6. Kết quả kiểm tra kỹ thuật (Verification Results)

Các kết quả dưới đây giữ mốc kiểm tra cục bộ **2026-10-01**, không phải kết quả chạy lại khi đổi bố cục ngày 2026-10-08.

| Công cụ kiểm tra | Lệnh thực hiện | Kết quả | Chi tiết / Bằng chứng |
| --- | --- | --- | --- |
| **Ruff Linter** | `ruff check .` | **PASS cục bộ** | Exit 0 tại workspace `ae67fb9` kèm thay đổi tài liệu chưa commit |
| **Pytest** | `pytest -q` | **PASS cục bộ** | `3 passed in 0.10s`, exit 0; không thay kiểm thử code PulseDB ở ref mới |
| **Environment Check** | `python scripts/check_environment.py` | **PASS cục bộ** | Exit 0; Python 3.13.12, khác Python 3.11 và dependency pin của repo |
| **Git Diff Check** | `git diff --check` | **PASS** | Exit 0 ở lần kiểm tra lịch sử |
| **Kiểm tra tài liệu** | Kiểm tra liên kết tương đối, conflict markers và local file URLs | **PASS** | Ghi nhận kiểm tra trong 8 tệp sửa |

Lần rà soát tài liệu này không chạy reader/notebook trên dataset, không thu waveform và không xác nhận CI online. Lint/smoke test không chứng minh phương pháp khoa học đã được phê duyệt.

Kiểm tra cục bộ ngày 2026-10-01 trong workspace `ae67fb9` kèm thay đổi tài liệu chưa commit: Ruff đạt (exit 0), pytest `3 passed in 0.10s` (exit 0), environment check đạt (exit 0), `git diff --check` đạt (exit 0); kiểm tra liên kết tương đối/conflict markers/local file URLs trong 8 tệp sửa đạt. Môi trường thực chạy Python **3.13.12**, khác cấu hình hỗ trợ Python 3.11 và dependency pin của repo; kết quả này không thay thế CI Python 3.11 hoặc kiểm thử code PulseDB ở ref mới.

---

## 7. Khó khăn, Rủi ro và Vướng mắc kỹ thuật

1. **Thiếu phần cứng/bản ghi v0:** Chưa kiểm chứng đồng bộ, nhiễu, bão hòa, R peak hoặc PPG foot trên thiết bị; chưa đạt điểm kiểm soát “có tín hiệu v0 đầu tiên”.
2. **Bàn giao PulseDB chưa đủ bằng chứng tái lập:** Cần checksum, metadata/nhãn, notebook chạy từ kernel sạch và log số đoạn đọc được; không dựa riêng vào output notebook lưu.
3. **Giao diện chưa khóa:** Timestamp lấy mẫu/FIFO/nhận gói, clock, sampling và marker cuff còn cần đối chiếu; PPG AFE/fs chưa chốt.
4. **Nguy cơ diễn giải quá mức:** ABP công khai không phải cuff; nhiều cửa sổ không tạo thêm nhãn độc lập; bản thảo và smoke test không chứng minh phương pháp đã được duyệt.

---

## 8. Các vấn đề cần nhóm và giảng viên xác nhận

> [!IMPORTANT]
> **Checklist lấy ý kiến thống nhất:**
> - [ ] **Nhóm:** Review và khóa mốc PPG foot, ghép nhịp, cửa sổ, schema/logger và quy chiếu thời gian theo các điểm dưới đây.
> - [ ] **Linh:** Xác nhận nguồn/quyền sử dụng, metadata/nhãn, checksum và hướng dẫn chạy PulseDB tái lập.
> - [ ] **Đức Anh:** Xác nhận giao diện clock/timestamp, cấu hình lấy mẫu dự kiến và tình trạng phần cứng/bản ghi v0.
> - [ ] **Nhóm/giảng viên:** Khóa cửa sổ/SQI trên pilot hoặc validation và đáp ứng an toàn/phê duyệt cần thiết trước đo trên người.

1. Thuật toán và mốc xác định PPG foot, quy tắc ghép nhịp với R peak.
2. Cửa sổ phân tích chính trong các ứng viên 10/20/30/60 giây và ngưỡng SQI; khóa trên pilot/validation trước khi xem test set.
3. Cách ghi mốc `t0` bắt đầu bơm cuff và liên kết một nhãn cuff với một `event_id`.
4. Schema logger chính thức, các trường/đơn vị bắt buộc và phiên bản packet.
5. Cách đồng bộ clock ECG–PPG–cuff, kiểm tra timestamp, tràn counter và mất mẫu.

Tuần 2 chưa thể nghiệm thu toàn bộ: chưa có bằng chứng Huy review PulseDB hoàn tất, chưa có xác nhận giao diện và chưa có bản ghi v0 được kiểm tra. Không ghi nhận việc của Linh/Đức Anh là kết quả của Huy.

---

## 9. Kế hoạch chuyển giao sang Tuần 3

Các việc đang chờ và bằng chứng cần nhận được giữ nguyên để bàn giao; chưa đánh dấu hoàn thành bằng dữ liệu thay thế.

| Việc | Phụ trách / reviewer cần xác nhận | Bằng chứng cần bổ sung |
| --- | --- | --- |
| Bàn giao PulseDB tái lập | Linh; Huy review | File/version thực dùng, quyền sử dụng, checksum, ánh xạ người/kênh/đơn vị/nhãn, notebook chạy sạch, ít nhất 1.000 đoạn |
| Review PulseDB | Huy; Linh xử lý góp ý | Commit, môi trường/lệnh, lỗi, kết quả và quyết định review; không chỉ dựa output notebook lưu |
| Logger → pipeline | Huy, Linh, Đức Anh | Clock, timestamp mẫu/FIFO/nhận gói, sampling từng kênh, mất mẫu, metadata/version và marker `t0` |
| Khóa phương pháp | Huy đề xuất; nhóm/giảng viên review | Foot/ghép nhịp, cửa sổ, SQI, thống kê; căn cứ pilot/validation và quyết định trước test |
| Kiểm tra v0 | Đức Anh bàn giao; Huy/Linh review | Manifest raw/log cấu hình, phiếu kiểm tra; an toàn/phê duyệt cần thiết trước đo trên người |
| Truy vết task | Huy và nhóm | Số Issue/PR, reviewer, commit được review và quyết định; chưa có bằng chứng đầy đủ |
