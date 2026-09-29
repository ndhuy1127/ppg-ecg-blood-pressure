# Báo cáo Tuần 2 — tiến độ phần việc của Huy

> Rà soát 2026-09-26. Đây là **báo cáo tiến độ**, không phải biên bản nghiệm thu Tuần 2. Trạng thái “hoàn thành” dưới đây chỉ áp dụng cho bản thảo/phần chuẩn bị do Huy phụ trách; chưa có xác nhận chung của nhóm hoặc kết quả đo trên thiết bị.

## Sản phẩm và bằng chứng trong repository

| Sản phẩm | Bằng chứng | Trạng thái |
| --- | --- | --- |
| Mục tiêu, phụ thuộc và blocker Tuần 2 | [Kế hoạch Tuần 2](../../../docs/plans/WEEK_02.md) | Kế hoạch đã ghi thiếu phần cứng; chưa phải bằng chứng hoàn thành việc của cả nhóm |
| Thuật ngữ, đơn vị quan sát, cửa sổ, chống rò rỉ, schema đề xuất và quy trình kiểm tra | [Tài liệu phương pháp của Huy](../../../docs/protocol/week_02_sample_label_glossary.md) | Bản thảo đã có nội dung, chờ Linh và Đức Anh review giao diện |

## Bảng kiểm tra phần việc Tuần 2 của Huy

| Phần việc của Huy | Trạng thái sau rà soát | Bằng chứng / phần còn lại |
| --- | --- | --- |
| Tổng hợp PAT, PTT, PEP, PWA và giới hạn PAT | Hoàn thành và có bằng chứng | Mục 1 tài liệu phương pháp; PAT từ R peak đến PPG foot, công thức PEP + PTT chỉ là cách viết gọn và không đo riêng hai thành phần. Bản thảo chờ review. |
| Định nghĩa người, phiên, lần cuff, quan sát BP, cửa sổ và nhịp | Hoàn thành và có bằng chứng | Mục 2 tài liệu phương pháp nêu các khóa `subject_id`, `session_id`, `event_id`, `window_id` và beat index/timestamp. |
| Một lần cuff và nhiều cửa sổ dùng chung SBP/DBP | Hoàn thành và có bằng chứng | Mục 2: một lần cuff hợp lệ tạo tối đa một cặp nhãn độc lập; các cửa sổ cùng `event_id` không thành nhiều quan sát BP độc lập. |
| Đề xuất cửa sổ 10/20/30/60 giây | Hoàn thành và có bằng chứng | Mục 3: cửa sổ trước `t0`, `window_start`/`window_end`; cửa sổ chính chưa được khóa. |
| Quy tắc chống rò rỉ và chia tập theo người | Hoàn thành và có bằng chứng | Mục 4: nhóm theo `subject_id`, hiệu chuẩn trước kiểm tra theo thời gian, không tuning trên test và bootstrap theo người. |
| Đề xuất schema nhãn và metadata | Đang bị chặn bởi Linh, Đức Anh hoặc phần cứng | Mục 5 đã có bảng đề xuất với trường bắt buộc/theo nguồn/chờ xác nhận và đơn vị; schema chính thức, ánh xạ PulseDB, packet và clock phải được Linh, Đức Anh đối chiếu. |
| Phân biệt PulseDB ABP với nhãn cuff và dữ liệu mô phỏng | Hoàn thành và có bằng chứng | Mục 6 phân biệt `public_abp`, `prototype_cuff`, `simulation`; không gán đoạn ABP thành event cuff. |
| Chuẩn bị quy trình kiểm tra R peak, trôi nền, PPG foot, timestamp và ghép nhịp | Hoàn thành và có bằng chứng | Mục 7 có trình tự và phiếu chờ bản ghi v0. Chưa có kết quả kiểm tra tín hiệu prototype. |
| Review trực quan PulseDB từ đầu ra của Linh | Đang bị chặn bởi Linh, Đức Anh hoặc phần cứng | Chờ đầu ra PulseDB của Linh; chưa thấy reader, notebook hoặc bằng chứng 1.000 đoạn trong repo để chạy lại. Phụ thuộc ở đây là Linh. |
| Cập nhật báo cáo Tuần 2 với bằng chứng và blocker | Hoàn thành và có bằng chứng | Báo cáo này ghi kết quả rà soát, việc chờ bàn giao và điểm cần nhóm quyết định; chưa đóng Tuần 2. |

Trước lần cập nhật này, quy tắc chống rò rỉ, mức bắt buộc/đơn vị của metadata và quy trình kiểm tra mới **đã làm nhưng cần sửa**; báo cáo thuộc nhóm **có thể hoàn thiện ngay**. Các phần đó đã được bổ sung trong tài liệu phương pháp và báo cáo này. Trạng thái “hoàn thành” không đồng nghĩa protocol, schema hay ngưỡng đã được nhóm phê duyệt.

## Công việc đã kiểm tra được và chờ Linh

- Kiểm tra danh sách file đang theo dõi trong `software/data_io/`, `notebooks/`, `scripts/`, `tests/`, `configs/data/` và báo cáo Tuần 2: chưa có reader PulseDB, notebook, manifest/checksum, test chuyên biệt hay output khảo sát ít nhất 1.000 đoạn. Vì vậy **chờ đầu ra PulseDB của Linh**, chưa thể review trực quan hoặc xác nhận ánh xạ ECG, PPG, ABP, `subject_id`, SBP/DBP trên dữ liệu thực.
- Huy cần Linh bàn giao nguồn/phiên bản và quyền sử dụng phần PulseDB, checksum manifest, hướng dẫn chạy reader/notebook, test file thiếu/metadata trùng/sai kênh, bảng ánh xạ subject/kênh/đơn vị/tần số/nhãn và bằng chứng số đoạn đọc thành công. Sau đó Huy mới chạy lại, ghi mã commit/phiên bản, lỗi và nhận xét review.
- Nếu dùng PulseDB để minh họa lỗi tín hiệu, mọi hình/bảng phải ghi rõ **dữ liệu công khai, không phải tín hiệu do prototype của nhóm thu**. ABP waveform và nhãn dẫn xuất từ ABP không phải nhãn cuff của thiết kế prototype.

## Chờ Đức Anh, phần cứng và việc chuyển tiếp

- Chờ Đức Anh đối chiếu bảng metadata với packet schema dự kiến: kênh/đơn vị, pin và cấu hình lấy mẫu dự kiến, định dạng timestamp hoặc chỉ số mẫu, clock chung/ánh xạ clock và cách ghi `t0` bắt đầu bơm cuff. Chưa có bằng chứng nhóm đã khóa giao diện logger → pipeline.
- Chưa có phần cứng PPG/ECG và bản ghi raw v0 hợp lệ. Phiếu kiểm tra ở mục 7 tài liệu phương pháp vẫn để **chờ bản ghi v0**: chưa kiểm tra timestamp ECG/PPG thật, R peak, PPG foot, trôi nền, nhiễu, bão hòa, tiếp xúc điện cực, mất mẫu hoặc ghép một R peak với xung PPG tương ứng.
- Sau khi nhận phần cứng, hoàn tất bring-up và điều kiện an toàn/phê duyệt cần thiết, mới thực hiện kiểm tra trên bản ghi được phép dùng và ghi manifest, reviewer, lỗi. **Chưa đạt điểm kiểm soát gốc “có tín hiệu v0 đầu tiên”; PulseDB không thay thế bản ghi thiết bị.**

## Quyết định còn cần cả nhóm thống nhất

1. Thuật toán và mốc xác định PPG foot, quy tắc ghép nhịp với R peak.
2. Cửa sổ phân tích chính trong các ứng viên 10/20/30/60 giây và ngưỡng SQI; khóa trên pilot/validation trước khi xem test set.
3. Cách ghi mốc `t0` bắt đầu bơm cuff và liên kết một nhãn cuff với một `event_id`.
4. Schema logger chính thức, các trường/đơn vị bắt buộc và phiên bản packet.
5. Cách đồng bộ clock ECG–PPG–cuff, kiểm tra timestamp, tràn counter và mất mẫu.

Tuần 2 chưa thể nghiệm thu toàn bộ: chưa có đầu ra PulseDB của Linh được review, chưa có xác nhận giao diện từ Đức Anh/Linh và chưa có tín hiệu v0 thật. Không ghi nhận việc của Linh hoặc Đức Anh là kết quả do Huy hoàn thành.
