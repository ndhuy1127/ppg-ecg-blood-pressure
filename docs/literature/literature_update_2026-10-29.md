# Các bài gần nhất với RQ1 và mức độ mới của đề tài

> **Ngày lập:** 2026-10-29
> **Cách làm:** tìm và tóm tắt bằng trợ lý AI (Claude Code) qua OpenAlex, Europe PMC
> và tìm kiếm web. Toàn văn được đọc qua công cụ trích xuất tự động, chưa có người
> trong nhóm đối chiếu từng đoạn. **Mọi con số phải đối chiếu nguyên văn trước khi
> đưa vào bản thảo.**
> Bổ sung cho [ma trận Tuần 1](week_01_literature_matrix.md) và
> [tổng quan bổ sung 2026-10-14](literature_update_2026-10-14.md) (mã S1–S14). Không
> phải systematic review.

## 1. Câu hỏi

Đã có bài nào làm giống RQ1 chưa: trên cùng một thiết bị, so sánh PPG-only với
PPG + PAT để dự đoán ΔSBP/ΔDBP ở **các phiên sau** hiệu chuẩn cuff, có baseline
zero-change, đánh giá theo người? Nếu có, phần nào của đề tài còn mới?

## 2. Nhật ký tìm kiếm

| Công cụ | Truy vấn | Kết quả |
| --- | --- | --- |
| OpenAlex (tìm theo tiêu đề) | `features from the photoplethysmogram and the electrocardiogram for estimating changes in blood pressure`; `conventional pulse transit times as markers of blood pressure changes in humans`; `photoplethysmography fast upstroke time intervals cuff-less measurement of blood pressure changes in humans`; `wearable cuff-less blood pressure estimation at home via pulse transit time`; `pulse transit time based continuous cuffless blood pressure estimation new extension comprehensive evaluation`; `cuffless blood pressure calibration drift days pulse arrival time photoplethysmography wearable`; `pulse arrival time photoplethysmogram features comparison blood pressure tracking interventions wearable` | N1–N5, N9 và các bài liên quan khác |
| OpenAlex (bài trích dẫn) | Bài trích dẫn N1 và S3, 25 bài được trích nhiều nhất mỗi bên | N6, N7, N8; bổ sung 2026-10-29: N13, N15 |
| OpenAlex (bài trích dẫn, bổ sung 2026-10-29) | Bài trích dẫn S4 (Aurora-BP), 25 bài được trích nhiều nhất | N12, N14, N16, N17 |
| OpenAlex (tìm theo tiêu đề, bổ sung 2026-10-29) | `pre-ejection period stress dependent pulse wave velocity based applications` | N11 |
| Tìm kiếm web (chế độ mở rộng) | `wrist ECG PPG pulse arrival time cuffless blood pressure multiple days after calibration added value over PPG features`; `2024 2025 study pulse arrival time versus PPG morphology features blood pressure changes longitudinal repeated sessions healthy volunteers cold pressor mental arithmetic calibration baseline` | N10; không thấy bài so sánh PPG-only với PPG + PAT qua nhiều phiên |
| Europe PMC (REST) | Tra PMC ID, abstract và toàn văn XML theo DOI | Mức đọc ở bảng 3 |

**Không mở được:** nature.com (chuyển sang trang đăng nhập); hai trong ba trang
pmc.ncbi.nlm.nih.gov (CAPTCHA, đã đọc thay bằng Europe PMC).

**Chỉ đọc abstract** (sửa 2026-10-29; bản trước ghi nhầm N7 là bài IEEE): S4, N6
(IEEE, toàn văn có phí, chưa thử qua thư viện trường); N5 (IEEE, có bản PMC8221527
nhưng chưa mở); N7, N8 (truy cập mở, lần này chưa đọc toàn văn); N10 (arXiv, chưa đọc
PDF).

**Chưa tìm:** truy vấn có hệ thống trên PubMed, IEEE Xplore, Scopus, Google Scholar;
tài liệu không phải tiếng Anh. **Dừng sớm: có** (giới hạn thời gian). Không thấy một
bài không có nghĩa là bài đó không tồn tại.

## 3. Bảng nguồn

| Mã | Trích dẫn | DOI | Thiết kế (theo nguồn) | Liên quan tới RQ1 | Mức đã đọc |
| --- | --- | --- | --- | --- | --- |
| **N1** | Finnegan E, Davidson SM, Harford M, Watkinson P, Tarassenko L, Villarroel M. Features from the photoplethysmogram and the electrocardiogram for estimating changes in blood pressure. *Sci Rep* 2023 | [10.1038/s41598-022-27170-2](https://doi.org/10.1038/s41598-022-27170-2) | 30 người khỏe, tuổi 28,0 (9,0), phân tích 26 người; truyền phenylephrine tĩnh mạch; PPG ngón tay, ECG ngực; cuff mỗi phút; **một buổi** khoảng 28 phút; baseline zero-change; LOSO lồng. So bốn bộ đặc trưng PPG, ECG, PPG + ECG, PAT. ΔSBP (median qua fold): zero-change MAE 7,40; RF PPG 4,75; LASSO + OLS PAT 4,91 mmHg | **Gần nhất về cách đánh giá.** Khác: một buổi, thuốc chứ không phải nghiệm pháp, PPG ngón tay; không có mô hình PPG + PAT. Tác giả nêu hướng tiếp: dữ liệu dọc theo thời gian của từng người | Toàn văn (Europe PMC), đọc 200.000/272.331 ký tự; kết quả ΔDBP ở phụ lục chưa đọc |
| **N2** | Natarajan K et al. (8 tác giả). Photoplethysmography fast upstroke time intervals can be useful features for cuff-less measurement of blood pressure changes in humans. *IEEE Trans Biomed Eng* (online 2021) | [10.1109/tbme.2021.3087105](https://doi.org/10.1109/tbme.2021.3087105) | 32 người (25% tăng huyết áp, tuổi 52); thở chậm, tính nhẩm, ngâm lạnh, nitroglycerin; PPG ngón tay, ngón chân, tai và ECG; cuff thủ công; một quy trình phòng thí nghiệm. Baseline "không đổi" RMSE 10,9/6,5 mmHg; đặc trưng sườn lên PPG cộng PAT giảm RMSE SBP 6–7% (9,5 mmHg) | Gần về nghiệm pháp và so PPG với PAT. Khác: một buổi, không ở cổ tay (tác giả ghi tín hiệu cổ tay kém hữu ích). Ghi nhận: dạng sóng PPG chịu ảnh hưởng của áp lực tiếp xúc nhiều hơn PAT | Toàn văn (PMC), một lượt |
| **N3** | Block RC et al. (13 tác giả). Conventional pulse transit times as markers of blood pressure changes in humans. *Sci Rep* 2020 | [10.1038/s41598-020-73143-8](https://doi.org/10.1038/s41598-020-73143-8) | Cùng cohort N2 (32/44 người); so sáu khoảng PAT/PTT; PAT ngón chân tương quan với SBP tốt nhất (r −0,63 ± 0,05); PAT ngón tay tương quan kém | Cơ sở cho việc PAT phụ thuộc vị trí đo và PEP; một buổi | Toàn văn (Europe PMC), một lượt |
| **N4** | Ding X, Yan BP, Zhang YT, Liu J, Zhao N, Tsang HK. Pulse transit time based continuous cuffless blood pressure estimation: a new extension and a comprehensive evaluation. *Sci Rep* 2017 | [10.1038/s41598-017-11507-3](https://doi.org/10.1038/s41598-017-11507-3) | 33 người (14 tăng huyết áp); PTT và PIR; Finapres; đứng dậy, thở sâu, Valsalva, bóp tay; theo dõi 24 giờ ở nhóm nhỏ. Sang ngày 2, sai số tăng ở mọi phương pháp | Bằng chứng sai số tăng khi đánh giá ngày hôm sau; không có baseline chỉ hiệu chuẩn trong phần đã đọc | Toàn văn (Europe PMC), đọc 100.000/137.802 ký tự |
| **N5** | Ganti VG et al. (6 tác giả). Wearable cuff-less blood pressure estimation at home via pulse transit time. *IEEE J Biomed Health Inform* (online 2020) | [10.1109/jbhi.2020.3021532](https://doi.org/10.1109/jbhi.2020.3021532) | Đồng hồ đo ECG một đạo trình, SCG, PPG nhiều bước sóng; 21 người khỏe tại nhà trong 24 giờ; cuff oscillometric | Thiết bị cổ tay, nhiều lần đo trong 24 giờ; dùng PTT từ SCG, không so PPG-only với PPG + PAT trong abstract | Abstract |
| **N6** | Liu ZD et al. (8 tác giả). Cuffless blood pressure measurement using smartwatches: a large-scale validation study. *IEEE J Biomed Health Inform* 2023 | [10.1109/jbhi.2023.3278168](https://doi.org/10.1109/jbhi.2023.3278168) | 3.077 người, theo dõi khoảng 1 tháng; đồng hồ đo ECG, sóng áp lực mạch, PPG nhiều bước sóng; nghe tim hai người đo; mô hình PTT, học máy và học sâu, có và không hiệu chuẩn | **Đối thủ lớn nhất về quy mô và nhiều phiên.** Abstract không cho biết có so PPG-only với PPG + PAT hay có baseline chỉ hiệu chuẩn không | Abstract |
| **N7** | Hove C et al. (10 tác giả). A prototype photoplethysmography-based cuffless device shows promising results in tracking changes in blood pressure. *Front Med Technol* 2024 | [10.3389/fmedt.2024.1464473](https://doi.org/10.3389/fmedt.2024.1464473) | Nguyên mẫu chỉ PPG; 38 người khỏe; bóp tay tĩnh, stress tinh thần, ngâm lạnh; tham chiếu liên tục (Nexfin); hiệu chuẩn một lần; chỉ số theo ISO 81060-3 | Ví dụ bài nguyên mẫu + nghiệm pháp ở tạp chí; chỉ PPG, một buổi | Abstract |
| **N8** | Mukkamala R, Shroff SG, Kyriakoulis KG, Avolio AP, Stergiou GS. Cuffless blood pressure measurement: where do we actually stand? *Hypertension* 2025 | [10.1161/hypertensionaha.125.24822](https://doi.org/10.1161/hypertensionaha.125.24822) | Tổng quan: theo tác giả, đến nay chưa có bằng chứng thuyết phục rằng phân tích dạng sóng và PAT thêm được giá trị đáng kể ngoài cuff hiệu chuẩn hoặc nhân khẩu học | Khung định vị chính cho RQ1: câu hỏi còn mở, và phản biện sẽ hoài nghi | Abstract (toàn văn PMC12331212 chưa đọc) |
| **N9** | Finnegan E et al. (8 tác giả). Pulse arrival time as a surrogate of blood pressure. *Sci Rep* 2021 | [10.1038/s41598-021-01358-4](https://doi.org/10.1038/s41598-021-01358-4) | Chưa đọc | Có thể là cơ sở PAT của N1 | Chỉ metadata |
| **N10** | Kaetheeswaran J, Ma B, Abedi A, Khan SS, Lankarany M. Calibration-free cuffless blood pressure estimation using multimodal ECG-PPG fusion on a Google Pixel Watch. arXiv:2608.26325, 2026 | [arXiv:2608.26325](https://arxiv.org/abs/2608.26325) | 40 người, đồng hồ thương mại, kết hợp ECG–PPG và nhân khẩu học, không hiệu chuẩn | Hướng không hiệu chuẩn, khác RQ1; preprint chưa phản biện | Abstract |
| **N11** | Pilz N, Patzak A, Bothe TL. The pre-ejection period is a highly stress dependent parameter of paramount importance for pulse-wave-velocity based applications. *Front Cardiovasc Med* 2023 | [10.3389/fcvm.2023.1138356](https://doi.org/10.3389/fcvm.2023.1138356) | Chưa đọc | Theo tiêu đề: PEP phụ thuộc mạnh vào stress; liên quan nghiệm pháp tính nhẩm M2 và rủi ro PEP của RQ1 | Chỉ metadata |
| **N12** | Charlton PH, Marozas V, Mejía-Mejía E, Kyriacou PA, Mant J. Determinants of photoplethysmography signal quality at the wrist. *PLOS Digit Health* 2025 | [10.1371/journal.pdig.0000585](https://doi.org/10.1371/journal.pdig.0000585) | Chưa đọc | Chất lượng PPG ở cổ tay: SQI (RQ3) và cách đeo trong protocol | Chỉ metadata |
| **N13** | Sirkiä JP, Panula T, Kaisti M. Investigating the impact of contact pressure on photoplethysmograms. *Biomed Eng Adv* 2024 | [10.1016/j.bea.2024.100123](https://doi.org/10.1016/j.bea.2024.100123) | Chưa đọc | Rủi ro áp lực tiếp xúc của RQ1 (RQ mục 4.F) | Chỉ metadata |
| **N14** | Cheung MY, Sabharwal A, Coté GL, Veeraraghavan A. Wearable blood pressure monitoring devices: understanding heterogeneity in design and evaluation. *IEEE Trans Biomed Eng* 2024 | [10.1109/tbme.2024.3434344](https://doi.org/10.1109/tbme.2024.3434344) | Chưa đọc | Cách thiết kế và báo cáo đánh giá thiết bị BP đeo được | Chỉ metadata |
| **N15** | Elgendi M et al. (7 tác giả). Recommendations for evaluating photoplethysmography-based algorithms for blood pressure assessment. *Commun Med* 2024 | [10.1038/s43856-024-00555-2](https://doi.org/10.1038/s43856-024-00555-2) | Chưa đọc | Danh mục kiểm khi viết phần đánh giá | Chỉ metadata |
| **N16** | Cisnal A et al. (6 tác giả). Robust feature selection for BP estimation in multiple populations: towards cuffless ambulatory BP monitoring. *IEEE J Biomed Health Inform* 2024 | [10.1109/jbhi.2024.3411693](https://doi.org/10.1109/jbhi.2024.3411693) | Chưa đọc; trích dẫn S4, chưa biết có dùng dữ liệu Aurora không | Chọn đặc trưng PPG/PAT; có thể gần RQ1, cần đọc | Chỉ metadata |
| **N17** | Min S et al. (12 tác giả). Wearable blood pressure sensors for cardiovascular monitoring and machine learning algorithms for blood pressure estimation. *Nat Rev Cardiol* 2025 | [10.1038/s41569-025-01127-0](https://doi.org/10.1038/s41569-025-01127-0) | Tổng quan, chưa đọc | Bối cảnh cho phần Introduction | Chỉ metadata |

S3 (Aurora, tổng kết) và S4 (Mieloszyk 2022, dataset Aurora-BP: 1.125 người, đồng hồ
PPG + ECG, tonometry, 24 giờ) ở [tổng quan 2026-10-14](literature_update_2026-10-14.md)
vẫn là nguồn lớn nhất về ECG + PPG cổ tay qua nhiều thời điểm; S4 mới đọc abstract.

## 4. So sánh với thiết kế của nhóm

| Đặc điểm của RQ1 | Đã có trong nguồn đã đọc |
| --- | --- |
| Baseline zero-change, LOSO theo người | N1 (cả hai), N2 (baseline không đổi), S3/S4 (baseline "khó") |
| So PPG với PAT trên cùng người | N1 (từng bộ riêng, không có PPG + PAT), N2 (PPG + PAT so với tham chiếu) |
| Nghiệm pháp tạo ΔBP không dùng thuốc | N2, N3, N4, N7 |
| PPG và ECG cùng ở cổ tay | N5, N6, S4, N10 |
| Đánh giá ở phiên khác ngày sau hiệu chuẩn | N4 (24 giờ, nhóm nhỏ), N6 (khoảng 1 tháng), S3/S4 (ngày hôm sau) |
| **Gộp tất cả: cùng thiết bị cổ tay, so PPG-only với PPG + PAT ghép cặp theo người, ở phiên sau, so với zero-change, có nghiệm pháp** | **Không thấy** trong các nguồn đã mở. Chưa loại trừ được N6 và S4 vì mới đọc abstract |

## 5. Đánh giá mức độ mới

**Không phải điểm mới:** dùng PAT hay đặc trưng PPG để ước lượng BP; ráp module
MAX30001/MAX30101; chia theo người (RQ2a đã được nhiều bài chứng minh, xem S6, S8,
S9); mô hình học máy.

**Có thể là đóng góp** (chỉ trong phạm vi các nguồn đã mở): một phép so sánh ghép cặp,
đăng ký trước, giữa PPG-only và PPG + PAT trên cùng thiết bị cổ tay, ở các phiên sau
hiệu chuẩn, có nghiệm pháp tạo ΔBP và luôn so với zero-change. N1 tự nêu dữ liệu dọc
theo thời gian là hướng tiếp theo, và N8 cho rằng câu hỏi "PAT/dạng sóng có thêm giá trị
ngoài hiệu chuẩn không" vẫn chưa có bằng chứng thuyết phục. Kết quả âm tính có độ nhạy
đủ cũng là đóng góp theo khung của N8.

**Không được viết** "đầu tiên" hay "chưa có nghiên cứu nào". Cách viết đúng: "Trong
các nguồn đã tra (OpenAlex, Europe PMC, tìm kiếm web; chưa tra có hệ thống PubMed,
IEEE Xplore, Scopus), chưa thấy nghiên cứu so sánh ghép cặp …".

**Điểm yếu so với các bài gần nhất:** cỡ mẫu nhỏ hơn nhiều so với N6 (3.077) và S4
(1.125); cuff ngắt quãng, trong khi N7 và N4 dùng tham chiếu liên tục; người trẻ khỏe,
dải ΔBP hẹp. Phản biện sẽ hỏi vì sao không dùng dataset Aurora-BP.

## 6. Việc cần làm

1. **Đọc toàn văn N6 và S4** (ưu tiên cao nhất, trước Tuần 8): nếu một trong hai đã so
   PPG-only với PPG + PAT qua nhiều ngày và có baseline chỉ hiệu chuẩn, phải viết lại
   khoảng trống của RQ1.
2. Đọc toàn văn N8 (PMC12331212) và N9; đọc nốt phần còn lại của N1 (ΔDBP, kết luận).
   Đọc N11–N17 (mới có metadata) trước khi trích; ưu tiên N16 (có thể gần RQ1), N11 và N13 (rủi ro PEP và áp lực tiếp xúc của RQ1).
3. Tìm các nghiên cứu khác đã dùng dataset Aurora-BP (bài trích dẫn S4).
4. Tra có hệ thống PubMed và IEEE Xplore cho tổ hợp: wrist/watch, ECG, PPG, pulse arrival
   time, calibration, days/sessions, zero-change hoặc calibration-only baseline; ghi số
   bản ghi và tiêu chí chọn.
5. Cân nhắc dùng Aurora-BP làm dữ liệu thứ hai cho câu hỏi kiểu RQ1 ở quy mô lớn (kiểm
   điều khoản truy cập; S3 ghi Aurora không có can thiệp làm BP thay đổi đáng kể). Quyết
   định trước khi chọn tạp chí ở Tuần 8, vì sẽ làm tăng khối lượng việc.
6. Đối chiếu nguyên văn mọi con số trong bảng 3 trước khi trích trong bản thảo.
