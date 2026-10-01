# Báo cáo Tuần 2 — tiến độ phần việc của Huy

> **Ngày báo cáo gốc:** 2026-09-26; **rà soát tài liệu:** 2026-10-01. Đây là báo cáo tiến độ, không phải biên bản nghiệm thu. Có bản thảo không đồng nghĩa đã review, khóa schema/cửa sổ hoặc phê duyệt protocol.

## Phạm vi bằng chứng rà soát

- Workspace `develop` và `dev/huy` ở `ae67fb9` (2026-09-26). Ref cục bộ `origin/develop` ở `e8915f6`, `origin/dev/ngoclinh` ở `100ec92`, `origin/dev/ducanh` ở `e13d669` (2026-09-30).
- Đọc bằng Git mà không chuyển nhánh/merge; chưa fetch hoặc xác nhận trực tiếp GitHub. Đường dẫn thuộc ref mới có thể chưa tồn tại trong workspace.
- Chưa có bằng chứng Huy chạy lại reader/notebook, review packet hoặc nhóm nghiệm thu. Không ghi công việc của Linh/Đức Anh là kết quả của Huy.

## Sản phẩm và bằng chứng trong repository

| Sản phẩm | Bằng chứng | Trạng thái |
| --- | --- | --- |
| Mục tiêu, phụ thuộc và blocker Tuần 2 | [Kế hoạch Tuần 2](../../../docs/plans/WEEK_02.md) | Kế hoạch đã ghi thiếu phần cứng; chưa phải bằng chứng hoàn thành việc của cả nhóm |
| Thuật ngữ, đơn vị quan sát, cửa sổ, chống rò rỉ, schema đề xuất và quy trình kiểm tra | [Tài liệu phương pháp của Huy](../../../docs/protocol/week_02_sample_label_glossary.md) | Bản thảo đã có nội dung, chờ Linh và Đức Anh review giao diện |

## Bảng kiểm tra phần việc Tuần 2 của Huy

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

## Công việc đã kiểm tra được và chờ Linh

- Nhận định “chưa có reader/notebook” là trạng thái báo cáo gốc 2026-09-26, không còn mô tả đầy đủ các ref mới. `origin/develop@e8915f6` có `software/pulsedb/`, `tests/test_pulsedb.py`, `notebooks/01_eda_and_visualization.ipynb`, `docs/pulsedb_provenance.md`. **Đã có đầu ra để Huy bắt đầu review**, chưa chứng minh chạy lại/nghiệm thu.
- Provenance còn ghi file sử dụng và checksum sẽ hoàn thiện. Test metadata trùng hiện kiểm tra khóa trên mảng tự tạo, chưa chứng minh reader phát hiện trùng. Notebook có tham chiếu `mat_files`, `subset`, `signals_1000` mà chưa thấy bước định nghĩa trong các cell đã đọc; cần chạy lại từ kernel sạch. Chưa xác minh độc lập nguồn/quyền sử dụng hoặc dữ liệu trong lần sửa tài liệu.
- Huy cần Linh bàn giao nguồn/phiên bản và quyền sử dụng phần PulseDB, checksum manifest, hướng dẫn chạy reader/notebook, test file thiếu/metadata trùng/sai kênh, bảng ánh xạ subject/kênh/đơn vị/tần số/nhãn và bằng chứng số đoạn đọc thành công. Sau đó Huy mới chạy lại, ghi mã commit/phiên bản, lỗi và nhận xét review.
- Nếu dùng PulseDB để minh họa lỗi tín hiệu, mọi hình/bảng phải ghi rõ **dữ liệu công khai, không phải tín hiệu do prototype của nhóm thu**. ABP waveform và nhãn dẫn xuất từ ABP không phải nhãn cuff của thiết kế prototype.

## Chờ Đức Anh, phần cứng và việc chuyển tiếp

- `origin/dev/ducanh@e13d669` có `configs/hardware/Packet_Schema_V0.1.md`, `hardware/bom/BOM_V0.1_with_PinMap.xlsx`, `configs/hardware/Quy trinh bring-up.docx`. Đã đọc packet Markdown; chưa thẩm định XLSX/DOCX. Packet đề xuất ECG 512 SPS, PPG AFE/tần số chưa chốt. Huy cần review khác biệt với protocol cũ, timestamp lấy mẫu/FIFO/nhận gói, clock và marker cuff; chưa có quyết định khóa giao diện.
- Chưa có bằng chứng bản ghi raw v0 hợp lệ hoặc kết quả kiểm thử phần cứng được bàn giao; tình trạng có/mua/mượn phần cứng thực tế cần Đức Anh xác nhận. Phiếu mục 7 vẫn **chờ bản ghi v0**, chưa kiểm tra timestamp, R peak, PPG foot, nhiễu, bão hòa, mất mẫu hoặc ghép nhịp thực.
- Sau khi nhận phần cứng, hoàn tất bring-up và điều kiện an toàn/phê duyệt cần thiết, mới thực hiện kiểm tra trên bản ghi được phép dùng và ghi manifest, reviewer, lỗi. **Chưa đạt điểm kiểm soát gốc “có tín hiệu v0 đầu tiên”; PulseDB không thay thế bản ghi thiết bị.**

## Quyết định còn cần cả nhóm thống nhất

1. Thuật toán và mốc xác định PPG foot, quy tắc ghép nhịp với R peak.
2. Cửa sổ phân tích chính trong các ứng viên 10/20/30/60 giây và ngưỡng SQI; khóa trên pilot/validation trước khi xem test set.
3. Cách ghi mốc `t0` bắt đầu bơm cuff và liên kết một nhãn cuff với một `event_id`.
4. Schema logger chính thức, các trường/đơn vị bắt buộc và phiên bản packet.
5. Cách đồng bộ clock ECG–PPG–cuff, kiểm tra timestamp, tràn counter và mất mẫu.

Tuần 2 chưa thể nghiệm thu toàn bộ: chưa có bằng chứng Huy review PulseDB hoàn tất, chưa có xác nhận giao diện và chưa có bản ghi v0 được kiểm tra. Không ghi nhận việc của Linh/Đức Anh là kết quả của Huy.

## Việc còn lại và điều kiện hoàn thành

| Việc | Phụ trách / reviewer cần xác nhận | Bằng chứng cần bổ sung |
| --- | --- | --- |
| Bàn giao PulseDB tái lập | Linh; Huy review | File/version thực dùng, quyền sử dụng, checksum, ánh xạ người/kênh/đơn vị/nhãn, notebook chạy sạch, ít nhất 1.000 đoạn |
| Review PulseDB | Huy; Linh xử lý góp ý | Commit, môi trường/lệnh, lỗi, kết quả và quyết định review; không chỉ dựa output notebook lưu |
| Logger → pipeline | Huy, Linh, Đức Anh | Clock, timestamp mẫu/FIFO/nhận gói, sampling từng kênh, mất mẫu, metadata/version và marker `t0` |
| Khóa phương pháp | Huy đề xuất; nhóm/giảng viên review | Foot/ghép nhịp, cửa sổ, SQI, thống kê; căn cứ pilot/validation và quyết định trước test |
| Kiểm tra v0 | Đức Anh bàn giao; Huy/Linh review | Manifest raw/log cấu hình, phiếu kiểm tra; an toàn/phê duyệt cần thiết trước đo trên người |
| Truy vết task | Huy và nhóm | Số Issue/PR, reviewer, commit được review và quyết định; chưa có bằng chứng đầy đủ |

Lần rà soát tài liệu này không chạy reader/notebook trên dataset, không thu waveform và không xác nhận CI online. Lint/smoke test không chứng minh phương pháp khoa học đã được phê duyệt.

Kiểm tra cục bộ ngày 2026-10-01 trong workspace `ae67fb9` kèm thay đổi tài liệu chưa commit: Ruff đạt (exit 0), pytest `3 passed in 0.10s` (exit 0), environment check đạt (exit 0), `git diff --check` đạt (exit 0); kiểm tra liên kết tương đối/conflict markers/local file URLs trong 8 tệp sửa đạt. Môi trường thực chạy Python **3.13.12**, khác cấu hình hỗ trợ Python 3.11 và dependency pin của repo; kết quả này không thay thế CI Python 3.11 hoặc kiểm thử code PulseDB ở ref mới.
