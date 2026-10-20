# Ma trận tổng quan tài liệu nghiên cứu (Tuần 1)

> **Phiên bản:** v0.2
> **Người thực hiện:** Nguyễn Đức Huy
> **Vai trò:** Xử lý tín hiệu, PAT, thống kê, protocol, tổng quan tài liệu và điều phối bài báo
> **Ngày lập:** 2026-09-22; **cập nhật:** 2026-10-14
> Metadata của 12 bài đã được đối chiếu với Crossref/nhà xuất bản; nội dung được đối chiếu ở mức ghi trong cột "Mức đã đọc". Nguồn bổ sung 2021–2026 nằm trong [tổng quan bổ sung](literature_update_2026-10-14.md).

---

## 1. Mục tiêu và phạm vi tổng quan

Tài liệu này là **tổng quan có cấu trúc ở mức sơ bộ (structured rapid review)** với 12 công trình liên quan trực tiếp đến bài toán của đề tài: **ước lượng biến thiên huyết áp (ΔSBP, ΔDBP) sau hiệu chuẩn cá nhân từ ECG và PPG trên thiết bị đeo cổ tay**. Đây chưa phải systematic review: chưa có truy vấn đầy đủ trên các cơ sở dữ liệu, sàng lọc hai người hay sơ đồ chọn bài.

Ma trận tập trung vào sáu khía cạnh:

1. **PAT khác PTT:** vai trò của thời gian tiền tống máu (pre-ejection period, PEP) và hệ quả khi dùng PAT thay cho PTT.
2. **Giá trị gia tăng của ECG + PPG** so với PPG đơn lẻ.
3. **Hiệu chuẩn cá nhân và dự đoán ΔBP** qua các phiên đo.
4. **Rò rỉ dữ liệu (data leakage):** chia theo người (subject-wise), theo thời gian/phiên, và rủi ro khi chia ngẫu nhiên theo cửa sổ.
5. **Chất lượng tín hiệu (SQI) và từ chối dự đoán.**
6. **Tính khả thi trên cổ tay.**

**Quy ước đọc bảng:**

- Nhiều bài gốc gọi khoảng R-peak ECG → PPG là "PTT" hoặc "rPTT". Theo quy ước của dự án, khoảng này là **PAT**; bảng ghi rõ khi bài gốc dùng tên khác.
- "Mức đã đọc" cho biết nội dung được đối chiếu tới đâu. Với bài chỉ đọc abstract, các chi tiết ngoài abstract được ghi "chưa xác minh" thay vì suy diễn.
- Không so sánh MAE giữa các bài khi bài toán (BP tuyệt đối hay ΔBP), nhãn, vị trí cảm biến, dải BP và cách hiệu chuẩn khác nhau.

---

## 2. Bảng ma trận tổng quan 12 nghiên cứu

| STT | Trích dẫn ngắn | Năm | DOI | Loại dữ liệu / thiết kế | Vị trí PPG | ECG? | Đại lượng thời gian | Nhãn huyết áp | Cách chia / đánh giá | Hiệu chuẩn cá nhân? | Chỉ số | Kết quả chính (theo nguồn) | Hạn chế | Mức đã đọc | Liên hệ với dự án |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **1** | Mukkamala et al., *IEEE TBME* 62(8):1879–1901 | 2015 | [10.1109/TBME.2015.2441951](https://doi.org/10.1109/TBME.2015.2441951) | Bài tổng quan lý thuyết và thực nghiệm | Tổng hợp nhiều vị trí | Có | PTT, PAT; PAT = PTT + PEP | Không áp dụng | Không áp dụng | Thảo luận nhu cầu hiệu chuẩn định kỳ | Không áp dụng | Trình bày cơ sở Moens–Korteweg/Hughes; PAT bằng PTT cộng PEP; PEP thay đổi đáng kể (bài nêu ví dụ 10–35% so với PTT) nên PAT không phải đại diện tốt của PTT; PAT ngón tay lúc nghỉ khoảng 180–260 ms | Tổng quan năm 2015, chưa gồm bằng chứng thiết bị đeo gần đây | Toàn văn ([PMC4515215](https://pmc.ncbi.nlm.nih.gov/articles/PMC4515215/)) | Cơ sở cho quy ước PAT/PTT/PEP và lý do không áp trực tiếp công thức PTT lên PAT |
| **2** | Zhang G. et al., *J Appl Physiol* 111(6):1681–1686 | 2011 | [10.1152/japplphysiol.00980.2011](https://doi.org/10.1152/japplphysiol.00980.2011) | Thực nghiệm trên 6 con chó với nhiều can thiệp huyết động | Đo xâm lấn trung tâm (PTT, PAT) | Có | So sánh PAT với PTT đo xâm lấn | BP động mạch xâm lấn | Phân tích theo từng con | Hồi quy riêng từng con | RMSE | Mô hình theo 1/PAT: RMSE DBP/MBP/SBP 9,8/10,4/11,9 mmHg; theo 1/PTT: 5,3/4,8/7,5 mmHg. Tác giả kết luận PAT không thay thế được PTT | Động vật, can thiệp mạnh hơn biến đổi sinh hoạt; chưa đọc toàn văn | Abstract | Căn cứ cho việc không gọi PAT là PTT và phải xem PEP là yếu tố gây nhiễu |
| **3** | Payne et al., *J Appl Physiol* 100(1):136–141 | 2006 | [10.1152/japplphysiol.00657.2005](https://doi.org/10.1152/japplphysiol.00657.2005) | 12 nam khỏe mạnh (tuổi TB 22), truyền tĩnh mạch 4 thuốc vận mạch (GTN, angiotensin II, norepinephrine, salbutamol) | Ngón tay | Có | R-peak → xung ngón tay, bài gọi là rPTT (theo dự án là PAT); đo thêm PEP | BP động mạch quay xâm lấn liên tục | Phân tích lặp trong từng người | Không phải nghiên cứu hiệu chuẩn thiết bị | R², giới hạn đồng thuận | PEP chiếm 12–35% rPTT và thay đổi theo thuốc. rPTT với SBP: R² = 0,39, LoA ±17 mmHg, tác giả đánh giá chưa đủ tin cậy để thay SBP. Với DBP/MAP: R² 0,02/0,08, tăng lên 0,41/0,45 sau khi trừ PEP | Chỉ nam trẻ; can thiệp thuốc cấp tính | Abstract | Xem PEP là nguồn sai số chính của PAT; không kỳ vọng PAT giải thích tốt DBP khi không đo PEP |
| **4** | Yoshizawa, Yamamoto & Ohtsuki, *IEEE Sensors J* 23(12):13311–13318 | 2023 | [10.1109/JSEN.2023.3272921](https://doi.org/10.1109/JSEN.2023.3272921) | Dataset công khai "Cuff-Less Blood Pressure Estimation" (UCI, dẫn xuất từ MIMIC-II) | PPG lâm sàng ICU | Có | Dùng PPG và ECG làm đầu vào deep learning | ABP xâm lấn | So sánh chia theo đoạn, theo bản ghi và gần-theo-người (quasi-subject) | Không | Pearson r, sai số | So với chia gần-theo-người, chia theo đoạn và theo bản ghi làm r của BP trung bình tăng giả 0,56 và 0,40 (PPG), 0,82 và 0,69 (ECG). Bản ghi MIMIC không tương ứng chắc chắn với người | Dataset ICU; chưa đọc chi tiết mô hình và MAE | Abstract | Căn cứ trực tiếp cho RQ2 và cho việc kiểm tra giao nhau theo người, không chỉ theo bản ghi |
| **5** | Kachuee et al., *IEEE TBME* 64(4):859–869 | 2017 | [10.1109/TBME.2016.2580904](https://doi.org/10.1109/TBME.2016.2580904) | MIMIC-II, khoảng 1.000 bản ghi (bài gọi là "subjects") | PPG lâm sàng ICU | Có | PAT và đặc trưng hình thái PPG | ABP xâm lấn | Chưa xác minh | Có thể có hoặc không hiệu chuẩn (theo abstract) | AAMI, BHS | Abstract: DBP và MAP đạt tiêu chí AAMI, BHS hạng A cho DBP và B cho MAP; SBP không đạt AAMI. Số đặc trưng, thuật toán tốt nhất và MAE cụ thể **chưa xác minh** | Dữ liệu ICU; "subject" có thể là bản ghi (xem #4) | Abstract ([PubMed](https://pubmed.ncbi.nlm.nih.gov/27323356/)) | Gợi ý nhóm đặc trưng PPG + PAT cho baseline; không dùng số MAE khi chưa đọc bảng gốc |
| **6** | Esmaili, Kachuee & Shabany, *IEEE TIM* 66(12):3299–3308 | 2017 | [10.1109/TIM.2017.2745081](https://doi.org/10.1109/TIM.2017.2745081) | 32 người khỏe mạnh (21–50 tuổi, 24 nam, 8 nữ); ghi lúc hồi phục sau một bài gắng sức | Ngón tay trái, PPG phản xạ 530 nm | Có | PTT từ âm tim (PCG) và PAT từ ECG; so sánh ba điểm trên PPG: foot, đạo hàm cực đại, đỉnh | Cuff tự động Omron M3 | Leave-one-pair-out trong từng người (5–6 cặp/người, 173 ước lượng) | Fit tham số riêng từng người từ các cặp còn lại | ME, MAE, SD, r | Bảng II, MAE SBP/DBP (mmHg). PAT: foot 7,92/5,93; đạo hàm cực đại 4,98/4,82; đỉnh 4,71/4,44. PTT: foot 8,33/5,92; đạo hàm 6,17/3,91; đỉnh 6,22/3,97 | Ngón tay; kiểm tra trong cùng người và cùng buổi, không chứng minh khả năng tổng quát sang người mới hay phiên sau | Toàn văn, bản tác giả ([arXiv:1812.00544](https://arxiv.org/abs/1812.00544)) | Cho thấy kết quả phụ thuộc mốc chọn trên PPG; dự án dùng foot nên không được viện dẫn số của mốc đỉnh |
| **7** | Ding et al., *IEEE TBME* 63(5):964–972 | 2016 | [10.1109/TBME.2015.2480679](https://doi.org/10.1109/TBME.2015.2480679) | 27 người khỏe mạnh | Chưa xác minh (ngoài abstract) | Có | PTT (theo bài) kết hợp tỷ số cường độ PPG (PIR). Abstract không nêu mốc đầu của PTT; nếu tính từ R-peak ECG thì theo quy ước dự án là PAT (chưa xác minh) | Finapres liên tục | Theo chuỗi thời gian trong từng người | Có | ME ± SD, sai số tuyệt đối TB | ME ± SD SBP/DBP/MBP: −0,37 ± 5,21 / −0,08 ± 4,06 / −0,18 ± 4,13 mmHg; tốt hơn hai thuật toán PTT được trích dẫn nhiều khoảng 2 mmHg. PIR bám theo biến đổi BP tần số thấp, PTT bám theo biến đổi tần số cao (hô hấp) | Chưa xác minh các can thiệp và vị trí cảm biến; cỡ mẫu nhỏ | Abstract ([PubMed](https://pubmed.ncbi.nlm.nih.gov/26415147/)) | Ứng viên đặc trưng PIR cho mô hình PPG; cần đọc toàn văn trước khi dùng làm căn cứ thiết kế |
| **8** | Zhang Q., Zhou & Zeng, *BioMed Eng OnLine* 16:23 | 2017 | [10.1186/s12938-017-0317-z](https://doi.org/10.1186/s12938-017-0317-z) | 10 người (7 nam, 3 nữ, 35 ± 14 tuổi), hai phiên 26 phút trong cùng ngày, có đạp xe nằm | Cánh tay trên trái | Có (ECG một tay) | R-peak → PPG foot, bài gọi là PTT (theo dự án là PAT) | Máy đo lưu động CONTEC ABPM50; chỉ SBP | Phiên 1 huấn luyện, phiên 2 kiểm thử, cùng người | Có, hệ số mô hình theo từng người | ME ± SD, MAE, RMSE | Mô hình PAT + HR: SBP 1,63 ± 4,44 mmHg, MAE 3,68 mmHg, RMSE 4,71 mmHg | 10 người; chỉ SBP; hai phiên cùng ngày; cánh tay trên, không phải cổ tay | Toàn văn ([PMC5294811](https://pmc.ncbi.nlm.nih.gov/articles/PMC5294811/)) | Cho thấy ECG biên độ nhỏ trên cùng một chi vẫn có thể cho PAT; không phải bằng chứng cho cổ tay hay nhiều ngày |
| **9** | Vybornova et al., *Blood Press Monit* 26(4):305–311 | 2021 | [10.1097/MBP.0000000000000531](https://doi.org/10.1097/MBP.0000000000000531) | 86 người, theo dõi 1 tháng | Cổ tay (vòng Aktiia) | Không | Phân tích hình thái sóng (PWA) | Nghe tim (auscultation), tư thế ngồi | Đánh giá lặp trong 1 tháng theo protocol ISO 81060-2:2013 mở rộng | Có, từ hai lần đo tham chiếu đầu tiên | ME ± SD | Sai khác SBP 0,46 ± 7,75 mmHg, DBP 0,39 ± 6,86 mmHg; SD của tiêu chí 2 là 3,9/3,6 mmHg | Thiết bị và thuật toán thương mại; protocol đã điều chỉnh cho thiết bị cuffless | Abstract | Mẫu thiết kế đánh giá dài hạn sau hiệu chuẩn; không suy ra prototype của nhóm "đạt ISO" |
| **10** | Elgendi, *Bioengineering* 3(4):21 | 2016 | [10.3390/bioengineering3040021](https://doi.org/10.3390/bioengineering3040021) | 106 bản ghi 60 giây, ghép từ các đoạn 20 giây của 40 người khỏe mạnh (nghỉ và sau gắng sức) | Ngón tay (Salus APG, 367 Hz) | Không | Không áp dụng | Nhãn chất lượng do hai người gán, chuyên gia phân xử | So sánh 8 SQI | Không áp dụng | F1 | Skewness là SQI tốt nhất trong 8 chỉ số (F1 86,0%, 87,2%, 79,1% ở các lần đánh giá) | 106 bản ghi không phải 106 người độc lập; không liên kết với ước lượng BP | Toàn văn ([PMC5597264](https://pmc.ncbi.nlm.nih.gov/articles/PMC5597264/)) | Skewness là ứng viên SQI cho PPG; ngưỡng phải được kiểm tra lại trên dữ liệu của dự án |
| **11** | Shen et al., *Biomed Signal Process Control* 92:106104 | 2024 | [10.1016/j.bspc.2024.106104](https://doi.org/10.1016/j.bspc.2024.106104) | 96 người từ MIMIC-III | PPG lâm sàng ICU | Theo bài gốc | Mô hình tham số (parameterized models) kết hợp mạng evidential (PEEL) | ABP xâm lấn | Chưa xác minh | Chưa xác minh | Sai số ước lượng, độ bất định | Abstract: sai số 3,74 mmHg (SBP) và 2,22 mmHg (DBP); abstract không nêu rõ đó là MAE | Chưa đọc toàn văn; dữ liệu ICU | Abstract (qua OpenAlex) | Ví dụ định lượng độ bất định cho BP cuffless; ngưỡng từ chối của dự án phải chọn trên validation và báo cáo bằng đường cong risk–coverage |
| **12** | Wang et al. (PulseDB), *Front Digit Health* 4:1090854 | 2023 | [10.3389/fdgth.2022.1090854](https://doi.org/10.3389/fdgth.2022.1090854) | 5.245.454 đoạn 10 giây từ 5.361 người (MIMIC-III đã đối khớp và VitalDB) | PPG lâm sàng, không tương đương PPG cổ tay | Có | ECG + PPG + ABP | ABP xâm lấn | 5 tập: huấn luyện, kiểm thử có hiệu chuẩn, kiểm thử không hiệu chuẩn, AAMI test và AAMI calibration; số người 2.506/2.506/279/242/242 | So sánh có và không hiệu chuẩn | MAE, SD | Bộ dữ liệu làm sạch quy mô lớn với các tập đánh giá tách theo mục tiêu | ICU/phẫu thuật, khác miền với cổ tay; đoạn 10 giây không phải lần đo cuff | Toàn văn ([PMC9944565](https://pmc.ncbi.nlm.nih.gov/articles/PMC9944565/)) | Nguồn dữ liệu công khai hiện dùng (phần VitalDB trên Kaggle) để phát triển pipeline và trả lời một phần RQ2 |

**Ghi chú về năm của PulseDB:** DOI chứa "2022" vì bài thuộc volume 4 (2022) của tạp chí, nhưng bài được công bố online ngày 2023-02-08; trích dẫn là 2023.

---

## 3. Tổng hợp theo các trục kỹ thuật

### 3.1. PAT khác PTT như thế nào?

$$\text{PAT} = \text{PEP} + \text{PTT}$$

- **PEP (pre-ejection period):** từ khởi đầu khử cực thất (thường lấy mốc Q/khởi đầu QRS) đến khi van động mạch chủ mở. Dự án đo PAT từ **đỉnh R**, không phải từ Q, nên phần "trước tống máu" trong PAT của dự án không trùng hoàn toàn với PEP. Yamashita et al. (2015, abstract hội nghị trên 6 con lợn) cho thấy PEP tính từ R và từ Q tương quan chặt nhưng lệch nhau một hằng số đáng kể. ECG + PPG chỉ đo được PAT, không tách được PEP và PTT ([glossary](../protocol/week_02_sample_label_glossary.md)).
- **PTT (pulse transit time):** thời gian sóng áp lực truyền từ gốc động mạch chủ đến vị trí đo ngoại vi. Theo Moens–Korteweg/Hughes, PTT liên hệ với độ cứng thành mạch và BP (#1).
- **Bằng chứng về ảnh hưởng của PEP:**
  - Payne 2006 (#3): PEP chiếm 12–35% khoảng R → xung ngón tay và thay đổi theo thuốc; DBP/MAP gần như không giải thích được bằng PAT (R² 0,02/0,08) cho tới khi trừ PEP.
  - Zhang 2011 (#2) và Gao 2016 (trên lợn, [10.14814/phy2.12768](https://doi.org/10.14814/phy2.12768)): PAT bám theo BP kém hơn PTT; Gao et al. quy phần kém hơn này cho thành phần PEP.
- **Quy ước bắt buộc của dự án:** khoảng R-peak ECG → PPG foot là **PAT**, không gọi là PTT. Mô hình dùng PAT phải chấp nhận rằng PAT chứa thành phần PEP thay đổi theo trạng thái giao cảm và sức co bóp cơ tim.

*Sửa so với v0.1:* bản trước ghi "PEP biến thiên 30–120 ms, đã được chứng minh trong Zhang 2011 và Payne 2006". Không nguồn nào trong ma trận nêu khoảng này, nên câu đó đã được thay bằng các con số có trong nguồn.

### 3.2. Hiệu chuẩn cá nhân và bài toán ΔBP

- Quan hệ giữa PAT/hình thái PPG và BP phụ thuộc thông số mạch máu riêng của từng người (chiều dài đường truyền, đường kính, độ dày và độ đàn hồi thành mạch), nên các nghiên cứu theo dõi người khỏe mạnh thường hiệu chuẩn theo từng người (#6, #8, #9).
- Đề tài giới hạn ở kịch bản có hiệu chuẩn. Ma trận này **không** đủ để kết luận phương pháp không hiệu chuẩn là bất khả thi.
- Cách tiếp cận được đề xuất kiểm chứng:
  1. Dùng một hoặc hai lần đo cuff đầu tiên làm mốc hiệu chuẩn $\text{SBP}_0, \text{DBP}_0$.
  2. Mô hình dự đoán $\Delta\text{SBP} = \text{SBP}_{\text{target}} - \text{SBP}_0$ và $\Delta\text{DBP} = \text{DBP}_{\text{target}} - \text{DBP}_0$.
  3. Ước lượng cuối $\widehat{\text{BP}} = \text{BP}_0 + \Delta\widehat{\text{BP}}$.
- Điểm yếu đã biết của cách đánh giá này: nếu BP ít thay đổi sau hiệu chuẩn, chỉ cần giữ nguyên $\text{BP}_0$ đã cho sai số nhỏ. Mukkamala et al. (2021) đề xuất luôn báo cáo baseline "BP hiệu chuẩn không đổi" bên cạnh thiết bị (xem [tổng quan bổ sung](literature_update_2026-10-14.md), S2). Đây là lý do dự án đặt zero-change làm baseline bắt buộc.

### 3.3. Rò rỉ dữ liệu trong dữ liệu sinh lý dạng cửa sổ

- **Chia ngẫu nhiên theo cửa sổ:** cắt tín hiệu của một người thành nhiều cửa sổ rồi xáo trộn vào train/validation/test. Mô hình có thể học đặc điểm dạng sóng riêng của người đó thay vì quan hệ với BP. Yoshizawa et al. (#4) đo được mức tăng giả của hệ số tương quan khi chia theo đoạn hoặc theo bản ghi so với chia gần-theo-người (tăng 0,40–0,82 tùy tín hiệu và cách chia). Mehta et al. (2024) phân tích cùng vấn đề cho PPG.
- **Chia theo người:** toàn bộ dữ liệu của một người chỉ nằm trong một tập. Moulaeifard et al. (2025) cho thấy trên PulseDB, sai số tăng từ 9,0/5,8 mmHg (có hiệu chuẩn) lên 13,9/8,5 mmHg (không hiệu chuẩn) và lên tới 18,6/10,3 mmHg trên dataset ngoài miền.
- **Chia theo thời gian/phiên:** trong bài toán hiệu chuẩn cá nhân, dữ liệu hiệu chuẩn phải có trước dữ liệu kiểm tra, và dữ liệu kiểm tra nên thuộc phiên khác (cách nhiều giờ hoặc nhiều ngày) để đo độ ổn định của hiệu chuẩn theo thời gian.

*Sửa so với v0.1:* bản trước ghi "MAE test < 3 mmHg, sang người mới hoặc phiên mới thì > 15 mmHg" mà không có nguồn; câu đó đã được thay bằng số liệu có nguồn ở trên.

### 3.4. SQI và cơ chế từ chối dự đoán

- Tín hiệu cổ tay nhạy với nhiễu chuyển động và thay đổi lực tiếp xúc. Dự đoán trên đoạn tín hiệu kém làm sai số tăng.
- Elgendi (#10) cung cấp cơ sở cho SQI dạng sóng PPG (skewness tốt nhất trong 8 chỉ số trên dữ liệu ngón tay). Shen 2024 (#11) và Shen 2025 (tổng quan bổ sung, S7) định lượng độ bất định cho dự đoán BP.
- Kết hợp SQI và độ bất định để từ chối dự đoán là **giả thuyết của RQ3**, chưa có kết quả của dự án. Ngưỡng phải được chọn trên validation và đánh giá bằng đường cong risk–coverage.

---

## 4. Khoảng trống nghiên cứu

Phần này viết lại sau khi bổ sung nguồn 2021–2026. Mỗi khoảng trống chỉ phản ánh **các nguồn nhóm đã đọc**, không phải kết luận về toàn bộ y văn. Các cụm "chưa ai làm", "lần đầu tiên" không được dùng khi chưa có tìm kiếm hệ thống.

1. **Giá trị gia tăng của PAT so với PPG sau hiệu chuẩn, đánh giá so với zero-change.**
   ECG + PPG trên thiết bị cổ tay **không còn hiếm**: dự án Aurora (Mieloszyk et al., 2022, 1.125 người) thu đồng thời ECG, PPG và tonometry ở cổ tay. Bài tổng kết của Mukkamala et al. (2023) cho biết không mô hình đặc trưng dạng sóng nào dự đoán BP nghe tim ngày hôm sau hoặc BP lưu động 24 giờ với sai số thấp hơn rõ rệt so với baseline chỉ dùng BP hiệu chuẩn và thời điểm trong ngày; Aurora cũng không có can thiệp làm BP thay đổi đáng kể. Các nguồn đã đọc **không** tách riêng PAT với PPG trong kết quả Aurora. Vì vậy câu hỏi còn mở, ở phạm vi hẹp, là: khi đã hiệu chuẩn, việc thêm PAT vào mô hình PPG có làm giảm sai số ΔBP ở phiên sau, và có vượt zero-change hay không. Bằng chứng Aurora cũng cho thấy kết quả âm tính là khả năng thực tế, nên RQ1 phải được thiết kế để kết quả âm tính vẫn diễn giải được.
2. **Độ ổn định của hiệu chuẩn qua nhiều ngày.**
   ESH 2023 đưa ra "recalibration test" và AHA 2025 nêu rằng các protocol validation hiện chưa xử lý độ ổn định theo thời gian. Vybornova 2021 theo dõi 1 tháng nhưng với thiết bị PPG thương mại. Đánh giá ΔBP qua 2–3 phiên ở các ngày khác nhau trên một prototype mở là một kiểm tra có ý nghĩa, nhưng ở quy mô 15–20 người thì đây là nghiên cứu khả thi (feasibility), không phải bằng chứng validation.
3. **Ảnh hưởng của cách chia dữ liệu.**
   Đây **không** phải khoảng trống mới: Yoshizawa 2023, Mehta 2024, PulseDB và Moulaeifard 2025 đã chứng minh rò rỉ theo người làm kết quả đẹp giả. Đóng góp của RQ2 là kiểm chứng lại hiệu ứng này trong pipeline của nhóm và lượng hóa nó cho bài toán của nhóm.
4. **Từ chối dự đoán kết hợp SQI và độ bất định.**
   Shen 2025 dùng conformal prediction trên Aurora-BP và có signal quality làm một đặc trưng; Shen 2024 dùng mạng evidential. Trong các nguồn đã đọc, chưa thấy đánh giá kết hợp lọc SQI đầu vào với độ bất định đầu ra bằng đường cong risk–coverage so với từ chối ngẫu nhiên ở cùng coverage, ở mức người. Đây là khoảng trống hẹp và cần tìm kiếm thêm trước khi đưa vào bài báo.

---

## 5. Đóng góp dự kiến

Các mục dưới đây là **dự kiến**, phụ thuộc vào việc có thu được dữ liệu prototype đủ chất lượng. Chưa mục nào đã được chứng minh.

**Đóng góp khoa học (nếu đạt điều kiện dữ liệu):**

1. Một câu trả lời có kiểm soát cho RQ1 trên nhóm người khỏe mạnh: PAT có giảm sai số ΔSBP/ΔDBP ở phiên sau so với mô hình PPG-only và so với zero-change hay không, kèm khoảng tin cậy bootstrap theo người. Kết quả âm tính (PAT không giúp) cũng là kết quả có giá trị và sẽ được báo cáo như vậy.
2. Ước lượng định lượng mức chênh sai số giữa các cách chia dữ liệu trên chính bài toán và dữ liệu của nhóm (RQ2). Đây là kiểm chứng lại một hiệu ứng đã biết.
3. Đánh giá cơ chế từ chối dự đoán bằng risk–coverage so với từ chối ngẫu nhiên (RQ3), nếu dữ liệu có đủ đoạn tín hiệu kém tự nhiên.

**Đóng góp phương pháp và tái lập (đã có một phần):**

- Pipeline mở có kiểm tra rò rỉ theo người, hash mẫu và waveform, một lần cuff = một nhãn, bootstrap theo người và provenance cho mọi kết quả. Đây là cải tiến về quy trình, không phải phát hiện khoa học.

**Cải tiến triển khai:**

- Nguyên mẫu vòng đeo cổ tay thu đồng bộ ECG (MAX30001) và PPG (MAX30101) với ESP32-S3, điện cực ngón tay tay đối diện để tạo đạo trình Lead I. Đây là tích hợp các linh kiện thương mại sẵn có. Giá trị của nó nằm ở việc cho phép kiểm soát đồng bộ thời gian và truy cập tín hiệu thô, không phải ở thiết kế cảm biến mới.
