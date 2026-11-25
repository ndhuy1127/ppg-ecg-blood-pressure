# Aurora-BP: truy cập, điều khoản và đối sánh biến

Ngày đọc các trang: 2026-11-25. Chỉ đọc trang công khai (README/tài liệu GitHub, trang Zenodo, tóm tắt bài báo); không tải dữ liệu, không đăng ký, không gửi biểu mẫu. Nội dung các trang được lấy qua công cụ tóm tắt trang web nên các điều khoản cần được đối chiếu lại với file PDF DUA gốc trước khi cam kết.

## 1. Nguồn và cách truy cập

| Nội dung | URL |
|---|---|
| Kho mã mẫu và tài liệu (giấy phép MIT cho kho mã) | https://github.com/microsoft/aurorabp-sample-data |
| Mô tả file, giao thức nghiên cứu, biến | https://github.com/microsoft/aurorabp-sample-data/blob/main/docs/README.md |
| Bộ dữ liệu đầy đủ (Zenodo, DOI) | https://doi.org/10.5281/zenodo.19099166 (chuyển tới https://zenodo.org/doi/10.5281/zenodo.19099166) |
| Bài báo | https://ieeexplore.ieee.org/document/9721156 (DOI 10.1109/JBHI.2022.3153259) |

Cách truy cập (theo trang Zenodo, https://zenodo.org/doi/10.5281/zenodo.19099166):
- Bản ghi được đánh dấu quyền truy cập "Open"; các file có liên kết tải trực tiếp. Trang không mô tả biểu mẫu yêu cầu truy cập, không nêu người ký, không nêu cần xác nhận của cơ quan chủ quản, không nêu thời gian duyệt hay chi phí.
- Việc chấp nhận DUA diễn ra khi tải, truy cập, xem hoặc sử dụng dữ liệu (cùng nguồn; README GitHub https://github.com/microsoft/aurorabp-sample-data nói tương tự).
- Phiên bản v1, công bố 24/02/2022; siêu dữ liệu kỹ thuật ghi ngày tạo/sửa 18/03/2026 (https://zenodo.org/doi/10.5281/zenodo.19099166). Nhà xuất bản ghi là Microsoft.
- Các file: `DataUseAgreement_AuroraBPStudyData.pdf` (130 kB), `participants.tsv` (81 kB), `measurements_auscultatory.tsv` (2,2 MB), `measurements_oscillometric.tsv` (4,0 MB), `features.tsv` (30 MB), `measurements_auscultatory.zip` (1,6 GB), `measurements_oscillometric.zip` (5,0 GB), `README.md`; tổng 6,7 GB (cùng nguồn Zenodo).
- Lưu ý: README GitHub nói "full dataset requires a data access request" trong docs/README.md (https://github.com/microsoft/aurorabp-sample-data/blob/main/docs/README.md), trong khi trang Zenodo hiện ghi Open và không có biểu mẫu. Hai mô tả không khớp hẳn; cần xác nhận khi mở trang bằng trình duyệt (xem mục 7).

## 2. Điều khoản chính của DUA

Nguồn: bản tóm tắt điều khoản trên https://zenodo.org/doi/10.5281/zenodo.19099166 (nội dung của file `DataUseAgreement_AuroraBPStudyData.pdf`) và ý chính trong https://github.com/microsoft/aurorabp-sample-data.

Được phép:
- Chỉ dùng cho nghiên cứu; không phát triển sản phẩm, không thương mại hóa.
- Chỉ nhà nghiên cứu chính (PI) của bên nhận và người dưới sự giám sát trực tiếp của PI được dùng dữ liệu.
- Được công bố kết quả nếu không đưa vào phần đáng kể của dữ liệu, không có thông tin mật của Microsoft hay dữ liệu cá nhân, và có trích dẫn Aurora-BP Study (và bài báo nguồn khi phù hợp).

Bị cấm:
- Chuyển giao/phân phối cho nhà nghiên cứu khác (kể cả trong cùng cơ quan) hoặc bên thứ ba khi chưa có văn bản đồng ý của Microsoft; người khác phải tự lấy quyền truy cập.
- Cố xác định danh tính hoặc liên hệ người tham gia, tái dựng thông tin cá nhân, dịch ngược dữ liệu.
- Kết hợp (join) dữ liệu với nguồn dữ liệu khác (README GitHub và DUA cùng nêu điều này).
- PI không được dùng dữ liệu để xây dựng phần mềm phục vụ chẩn đoán.
- Dùng tên/logo Microsoft trong quảng bá khi chưa có đồng ý bằng văn bản; dùng sai phạm vi thỏa thuận; vi phạm pháp luật.

Bảo mật: phải duy trì biện pháp hành chính, kỹ thuật, vật lý để bảo vệ tính bí mật, và theo thực hành tốt về lưu trữ/sử dụng dữ liệu (ví dụ hướng dẫn bảo mật dbGaP của NIH) áp dụng cho cả dữ liệu dẫn xuất ("any resulting data").

Dữ liệu/mã dẫn xuất: DUA không cấm công bố mã. Tuy nhiên điều khoản cấm chuyển giao dữ liệu và bảng kết quả chứa phần đáng kể của dữ liệu; đặc trưng dẫn xuất ở mức từng bản ghi có nguy cơ bị coi là "dữ liệu" nên chưa nên chia sẻ khi chưa có đồng ý của Microsoft. Đây là suy luận từ điều khoản, không phải câu chữ của DUA; cần hỏi để chắc chắn.

Đạo đức: DUA có điều khoản yêu cầu, khi cần thiết, xác nhận việc sử dụng đã được hội đồng đạo đức (IRB hoặc tương đương) chấp thuận theo các quy định Hoa Kỳ (45 CFR Part 46; 21 CFR Parts 50 và 56) (https://zenodo.org/doi/10.5281/zenodo.19099166). Không rõ DUA có yêu cầu giấy xác nhận miễn xét duyệt cụ thể cho dữ liệu đã khử định danh hay không.

Khác: dữ liệu cung cấp "nguyên trạng", Microsoft không bảo đảm độ chính xác/tính sẵn có và không hỗ trợ; mức bồi thường tối đa theo DUA là 5 USD (cùng nguồn).

## 3. Mô tả dữ liệu

Nguồn mô tả: https://github.com/microsoft/aurorabp-sample-data/blob/main/docs/README.md (trừ khi ghi khác).

Thiết kế và nhóm:
- Phê duyệt đạo đức của nghiên cứu gốc: WCG IRB (Puyallup, WA, Hoa Kỳ). Loại trừ: dưới 18 tuổi, mang thai, tù nhân, người sống trong cơ sở, người không đồng ý được bằng tiếng Anh.
- Hai nhóm giao thức, mỗi người chỉ tham gia một giao thức, chạy không đồng thời:
  - Auscultatory (ID tiền tố "a"): sóng xung quay kèm huyết áp đo thủ công; không có pha ambulatory.
  - Oscillometric (ID tiền tố "o"): theo dõi ambulatory tối thiểu 24 giờ, đồng bộ với huyết áp tự động.
- Mỗi giao thức có hai lần đến phòng thí nghiệm cách nhau ít nhất 24 giờ. Lần đầu: gắn thiết bị, đo theo tư thế, đo sau vận động. Lần quay lại: lặp chuỗi đo (với nhóm oscillometric chỉ các tư thế ngồi). Nhãn pha: initial, ambulatory, return, synthetic (đường nền hài hòa tính từ dữ liệu lần đầu).
- Số người: bài báo nêu 1125 người tham gia, tuổi 21 đến 85, 49,2% nữ (https://www.microsoft.com/en-us/research/?p=858498 và kết quả tìm kiếm tóm tắt bài báo). README/Zenodo không nêu số người từng nhóm, số phiên hay số phép đo.

Cảm biến và tần số lấy mẫu:
| Thiết bị | Cảm biến | Linh kiện | Tần số |
|---|---|---|---|
| Tonometry cổ tay | áp lực | MS5803-02BA | 200 S/s |
| Tonometry cổ tay | ECG | ADS1292 | 488,28 S/s |
| Tonometry cổ tay | gia tốc | LSM6DS3 | 100 S/s |
| Quang học (kiểu đồng hồ) | PPG | MAX30101 | 250 S/s |
| Quang học | ECG | ADS1292 | 498,67 S/s |
| Quang học | gia tốc | LSM330 | 100 S/s |

- Các luồng sóng được lấy mẫu lại về chung 500 mẫu/giây; thiết bị tonometry và quang học được căn thời gian nhờ ECG. Bước sóng/màu kênh PPG, vị trí điện cực và cấu hình dẫn truyền ECG không được nêu trong trang đã đọc.

Phương pháp đo huyết áp tham chiếu:
- Auscultatory: hai quan sát viên dùng ống nghe hai đầu và huyết áp kế đồng hồ (ADC Diagnostix 700/703), lấy trung bình hai người (có lúc chỉ một người); tay đo ngẫu nhiên.
- Oscillometric: máy đo huyết áp lưu động Spacelabs OnTrak 90227 trên tay trội hoặc tay ưa dùng; ambulatory đo mỗi 30 phút lúc thức (khoảng 8h-20h) và mỗi 60 phút ban đêm.
- Bản ghi tonometry/quang học bắt đầu khoảng 2 phút trước và kết thúc 2 phút sau mỗi lần đo huyết áp; căn chỉnh không bảo đảm khi lần đo phải lặp do lỗi.

Tư thế/thao tác:
- Auscultatory: nằm nghỉ khoảng 10 phút, rồi nằm ngửa và ngồi; sau vận động: đạp xe nằm 2 phút, hai lần đo.
- Oscillometric: bảy phép đo lần đầu/quay lại (ngồi tay xuống, trên đùi, tay giơ lên; nằm ngửa hai lần; đứng tay xuống, tay giơ lên); sau vận động: đạp xe tốc độ đi bộ và chạy, đo ngay và sau nghỉ 3 và 6 phút.
- Dữ liệu sau vận động có trong thu thập nhưng bị loại khỏi phân tích sau khi trích đặc trưng.

Định dạng và cấu trúc:
- `participants.tsv` (một dòng mỗi người), `measurements_auscultatory.tsv` và `measurements_oscillometric.tsv` (một dòng mỗi phép đo), `features.tsv` (đặc trưng dẫn xuất kèm cột nền và delta).
- File sóng: `measurements_<protocol>/<pid>/<pid>.<phase>.<measurement>.tsv`, cột `t, ekg, optical, pressure, accel_x, accel_y, accel_z`.
- Cột bảng phép đo gồm `pid, phase, measurement, date_time, sbp, dbp, duration, pressure_quality, optical_quality, waveform_file_path, waveforms_generated`.

## 4. Bảng đối sánh biến

Nguồn chung: https://github.com/microsoft/aurorabp-sample-data/blob/main/docs/README.md (README Zenodo: https://zenodo.org/doi/10.5281/zenodo.19099166).

| Biến cần cho nhóm | Aurora-BP có không / tên biến hoặc file | Ghi chú |
|---|---|---|
| Mã đối tượng | Có: `pid` (tiền tố a/o) trong mọi bảng | Mã giả danh; không ghép với dữ liệu khác (DUA) |
| Mã phiên/lần đến, ngày, khoảng cách giữa các lần | Có một phần: `phase` (initial/ambulatory/return/synthetic), `measurement`, `date_time` theo từng phép đo | Khoảng cách tối thiểu 24 h giữa hai lần đến theo giao thức; khoảng cách thực tế cần tính từ `date_time`; chưa biết `date_time` có bị dịch/đặt lại hay không |
| SBP/DBP cuff và mốc thời gian | Có: `sbp`, `dbp`, `date_time` | Auscultatory: có cột quan sát viên chính/phụ (README ghi có thể nhầm nhãn, cần kiểm); `date_time` của phép đo ambulatory so với mốc sóng cần kiểm |
| Loại tham chiếu huyết áp | Có theo nhóm: auscultatory (thủ công) hoặc oscillometric (Spacelabs OnTrak) | Do nhóm chia theo file/tiền tố pid |
| ECG: dẫn/vị trí và tần số | Có: cột `ekg`, ADS1292, ~488 hoặc ~499 S/s gốc, 500 S/s sau lấy mẫu lại | Cấu hình dẫn/vị trí điện cực không nêu ở trang đã đọc; thiết bị cổ tay |
| PPG: cổ tay, bước sóng/màu, tần số | Có: cột `optical`, MAX30101, 250 S/s gốc, 500 S/s sau lấy mẫu lại | Màu/bước sóng kênh không nêu; chỉ một cột `optical` |
| ECG và PPG cùng đồng hồ/đồng bộ | Có: cùng thiết bị quang học (ECG ADS1292 và PPG MAX30101) trong cùng file sóng, chung cột `t` | Thiết bị quang học và tonometry được căn bằng ECG; mức sai lệch pha ECG-PPG chưa biết |
| Gia tốc | Có: `accel_x, accel_y, accel_z`, 100 S/s | Đặc trưng: góc tay, mức chuyển động, số bước 5 và 30 phút |
| Nhãn tư thế/thao tác | Có theo `measurement` (ngồi, nằm, đứng, vị trí tay; sau vận động) | Tên chuẩn của nhãn trong `measurement` cần xem file thật; nhóm ambulatory chưa có nhãn hoạt động chi tiết ngoài gia tốc |
| Nhân khẩu | Có (tự khai) trong `participants.tsv`: tuổi, chiều cao (inch), cân nặng (pound), giới tính; cỡ thiết bị, thang Fitzpatrick, tay đo | Không có cột BMI; tính từ chiều cao/cân nặng |
| Thuốc hạ áp / bệnh lý | Có một phần: `cvd_meds` (bool, thuốc tim mạch gồm huyết áp); tình trạng tăng huyết áp (normal/unknown, managed, unmanaged); các bệnh sử bool (THA, bệnh mạch vành, đái tháo đường, loạn nhịp, nhồi máu, đột quỵ, suy tim, hẹp động mạch chủ, bệnh van tim, khác) | Không tách riêng thuốc hạ áp với các thuốc tim mạch khác |
| PAT/PTT hoặc điểm mốc tính sẵn | Có trong `features.tsv`: `rPAT` và nghịch đảo rPAT (từ PPG quang học và từ tonometer), kèm HR, HRV, dP/dt, thời gian tăng tâm thu, v.v.; cột baseline và delta | Định nghĩa điểm mốc (foot hay đỉnh dP/dt) chưa được nêu ở trang đã đọc; nhóm vẫn cần tự tính PAT từ sóng thô để dùng định nghĩa foot riêng. Tên "rPAT" là của bộ dữ liệu; trong tài liệu nhóm vẫn dùng PAT = khoảng R đến foot PPG |
| Chất lượng tín hiệu | Có: `pressure_quality`, `optical_quality` | Ngưỡng và ý nghĩa cần xem tài liệu |

## 5. Ước lượng số cặp dùng được

Điều công khai nêu được:
- Tổng 1125 người (tuổi 21 đến 85) cho cả hai giao thức (https://www.microsoft.com/en-us/research/?p=858498, kết quả tìm kiếm tóm tắt bài báo).
- Mỗi giao thức có hai lần đến phòng thí nghiệm cách nhau tối thiểu 24 h, mỗi lần có chuỗi đo theo tư thế với tham chiếu huyết áp (https://github.com/microsoft/aurorabp-sample-data/blob/main/docs/README.md). Vì vậy về nguyên tắc người nào hoàn thành cả hai lần đến đều có hai phiên cách nhau 24 h trở lên, có ECG, PPG (thiết bị quang học) và tham chiếu.
- Chú ý: nhóm auscultatory có sóng tonometry, nhưng các mô tả cho thấy PPG (MAX30101) thuộc thiết bị quang học; chưa rõ mọi phép đo của cả hai nhóm có sóng quang học hay không (cột `optical_quality` gợi ý có thể thiếu ở một số phép đo).
- Với nhóm oscillometric ở lần quay lại chỉ có tư thế ngồi (https://github.com/microsoft/aurorabp-sample-data/blob/main/docs/README.md), nên cặp so sánh giữa hai lần đến nên giới hạn ở các tư thế ngồi trùng nhau.

Chưa biết cho tới khi có dữ liệu:
- Số người từng nhóm, số người hoàn thành cả hai lần đến, số phép đo có đủ ECG + PPG + tham chiếu và qua kiểm tra chất lượng.
- Khoảng cách thực tế giữa hai lần đến, và có `date_time` đủ để tính hay không.
- Số cặp trong-người sau khi loại phép đo sau vận động và phép đo chất lượng thấp.

## 6. Nội dung soạn sẵn cho yêu cầu truy cập

Lưu ý: trang Zenodo hiện không có biểu mẫu; đoạn dưới dùng khi có biểu mẫu/email xin phép hoặc khi cần gửi xin đồng ý ngoại lệ với Microsoft (ví dụ để làm rõ điều khoản "không kết hợp dữ liệu").

Bản tiếng Việt:

> Mục đích sử dụng: nghiên cứu học thuật tại [tên trường], do [người chịu trách nhiệm] làm nhà nghiên cứu chính. Chúng tôi nghiên cứu mối liên hệ giữa thay đổi trong người của thời gian đến xung (PAT, từ sóng R của ECG đến chân sóng PPG) và thay đổi huyết áp giữa các phiên đo cách nhau tối thiểu 24 giờ, và so sánh mô hình chỉ dùng PPG với mô hình PPG kết hợp PAT. Kế hoạch phân tích được đăng ký trước khi xem dữ liệu kiểm tra. Chúng tôi không cố gắng xác định danh tính người tham gia, không chuyển giao hay phân phối lại dữ liệu, không dùng cho mục đích thương mại hay phát triển phần mềm chẩn đoán, không kết hợp dữ liệu này với nguồn dữ liệu khác. Dữ liệu được lưu trên máy có kiểm soát truy cập, chỉ [người chịu trách nhiệm] và người dưới sự giám sát trực tiếp được dùng. Kết quả chỉ công bố ở dạng tổng hợp, có trích dẫn Aurora-BP Study và bài báo nguồn. Liên hệ: [email].

English version:

> Intended use: academic research at [institution name], with [responsible person] as principal investigator. We study the within-subject relationship between changes in pulse arrival time (PAT, from the ECG R-peak to the PPG foot) and changes in blood pressure across sessions at least 24 hours apart, and compare PPG-only models against PPG-plus-PAT models. The analysis plan is pre-registered before any held-out data are examined. We will not attempt to identify participants, will not transfer or redistribute the data, will not use it for commercial purposes or for building diagnostic software, and will not join it with other data sources. Data will be stored on access-controlled systems, available only to [responsible person] and people under direct supervision. Results will be published in aggregate form only, citing the Aurora-BP Study and the source publication. Contact: [email].

Chú ý khi dùng: nếu kế hoạch của nhóm có so sánh hoặc huấn luyện kết hợp với dữ liệu khác (ví dụ PulseDB hoặc dữ liệu tự thu), điều khoản "không kết hợp dữ liệu" có thể cấm; nên chỉ chạy phân tích riêng trên Aurora-BP và so sánh bằng kết quả tổng hợp, hoặc hỏi Microsoft trước.

## 7. Những gì chưa rõ / cần hỏi

Ngày đọc các trang: 2026-11-25.

1. Quy trình truy cập thực tế: Zenodo ghi "Open" và không có biểu mẫu, trong khi README GitHub nhắc "data access request". Cần mở trang Zenodo bằng trình duyệt để xem có bước yêu cầu truy cập/đăng nhập không, và xác nhận bộ dữ liệu còn khả dụng (bản ghi chỉnh sửa ngày 18/03/2026).
2. Ai ký DUA, có cần chữ ký cơ quan chủ quản hay không: trang chỉ nêu việc chấp nhận bằng hành vi tải/sử dụng và vai trò PI; chưa rõ. Cần đọc PDF DUA gốc.
3. Điều khoản "không kết hợp dữ liệu" có cấm dùng chung với PulseDB hoặc dữ liệu của nhóm trong cùng một mô hình không; và điều khoản "không xây phần mềm chẩn đoán" ảnh hưởng đến mục tiêu ước lượng huyết áp thế nào.
4. DUA có yêu cầu giấy chấp thuận/miễn xét duyệt của hội đồng đạo đức bên nhận không (điều khoản J nêu "khi cần thiết", theo quy định Hoa Kỳ).
5. Có được chia sẻ đặc trưng dẫn xuất hoặc mã ở mức bản ghi không (cần đồng ý bằng văn bản theo điều khoản chuyển giao).
6. Số người, số phiên, số cặp có đủ ECG + PPG + tham chiếu (mục 5), đơn vị và quy ước của `date_time`, định nghĩa điểm mốc của rPAT, bước sóng/màu kênh PPG, cấu hình dẫn ECG: chỉ biết sau khi có dữ liệu hoặc đọc đầy đủ docs/README.md và bài báo.
7. Một số trang chỉ đọc được qua bản tóm tắt tự động; bài báo IEEE (https://ieeexplore.ieee.org/document/9721156) chưa đọc toàn văn; số liệu 1125 người lấy từ bản tóm tắt tìm kiếm của trang Microsoft Research.
