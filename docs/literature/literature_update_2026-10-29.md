# Các bài gần nhất với RQ1 và mức độ mới của đề tài

> **Ngày lập:** 2026-10-29; **cập nhật lần 2:** 2026-10-29 (tìm có hệ thống, có nhật ký, trên
> PubMed, Europe PMC và OpenAlex cho giai đoạn 2022–2026; đọc toàn văn N5, N7, N8, N16; thêm
> N18–N42; viết lại mục 4–6; ghi quyết định ngày 2026-10-29 về S4 và kết quả thử truy cập N6).
> **Cách làm:** tìm, sàng lọc và tóm tắt bằng trợ lý AI (Claude Code), qua API PubMed
> E-utilities, Europe PMC REST và OpenAlex; toàn văn đọc qua Europe PMC, BioC (NCBI), trang PMC
> và kho ETH Zurich. Chỉ có một bên sàng lọc (trợ lý AI); chưa có người trong nhóm đối chiếu
> từng đoạn. **Mọi con số phải đối chiếu nguyên văn trước khi đưa vào bản thảo.**
> Bổ sung cho [ma trận Tuần 1](week_01_literature_matrix.md) và
> [tổng quan bổ sung 2026-10-14](literature_update_2026-10-14.md) (mã S1–S14). Tìm có nhật ký
> nhưng **không phải systematic review**: không đăng ký protocol, một bên sàng lọc, không có sơ
> đồ PRISMA.

## 1. Câu hỏi

Đã có bài nào làm giống RQ1 chưa: trên cùng một thiết bị, so sánh PPG-only với
PPG + PAT để dự đoán ΔSBP/ΔDBP ở **các phiên sau** hiệu chuẩn cuff, có baseline
zero-change, đánh giá theo người? Nếu có, phần nào của đề tài còn mới?

## 2. Nhật ký tìm kiếm

### 2.1. Lần 1 (2026-10-29, tìm có mục tiêu)

| Công cụ | Truy vấn | Kết quả |
| --- | --- | --- |
| OpenAlex (tìm theo tiêu đề) | `features from the photoplethysmogram and the electrocardiogram for estimating changes in blood pressure`; `conventional pulse transit times as markers of blood pressure changes in humans`; `photoplethysmography fast upstroke time intervals cuff-less measurement of blood pressure changes in humans`; `wearable cuff-less blood pressure estimation at home via pulse transit time`; `pulse transit time based continuous cuffless blood pressure estimation new extension comprehensive evaluation`; `cuffless blood pressure calibration drift days pulse arrival time photoplethysmography wearable`; `pulse arrival time photoplethysmogram features comparison blood pressure tracking interventions wearable` | N1–N5, N9 và các bài liên quan khác |
| OpenAlex (bài trích dẫn) | Bài trích dẫn N1 và S3, 25 bài được trích nhiều nhất mỗi bên | N6, N7, N8; bổ sung 2026-10-29: N13, N15 |
| OpenAlex (bài trích dẫn, bổ sung 2026-10-29) | Bài trích dẫn S4 (Aurora-BP), 25 bài được trích nhiều nhất | N12, N14, N16, N17 |
| OpenAlex (tìm theo tiêu đề, bổ sung 2026-10-29) | `pre-ejection period stress dependent pulse wave velocity based applications` | N11 |
| Tìm kiếm web (chế độ mở rộng) | `wrist ECG PPG pulse arrival time cuffless blood pressure multiple days after calibration added value over PPG features`; `2024 2025 study pulse arrival time versus PPG morphology features blood pressure changes longitudinal repeated sessions healthy volunteers cold pressor mental arithmetic calibration baseline` | N10; không thấy bài so sánh PPG-only với PPG + PAT qua nhiều phiên |
| Europe PMC (REST) | Tra PMC ID, abstract và toàn văn XML theo DOI | Mức đọc ở bảng 3 |

Ghi chú của lần 1 (giữ để truy vết): nature.com chuyển sang trang đăng nhập; hai trong ba
trang pmc.ncbi.nlm.nih.gov bị CAPTCHA (đã đọc thay bằng Europe PMC). Lần 1 **dừng sớm** vì giới
hạn thời gian và chưa tra có hệ thống. Mức đọc hiện tại của từng nguồn ghi ở bảng 3 (đã sửa
sau lần 2).

**Sửa ghi chú lần 1 về truy cập.** Lần 1 ghi S4 và N6 đều là "IEEE, toàn văn có phí". Ghi đúng:

- S4 có phí. Theo quyết định ngày 2026-10-29, không lấy toàn văn qua thư viện, chỉ dùng abstract.
- N6 là truy cập mở hybrid, bản đã xuất bản có giấy phép CC BY 4.0 (Crossref). Tải tự động bị chặn
  (mục 2.2).

### 2.2. Lần 2 (2026-10-29, tìm có hệ thống)

**Phạm vi.** 32 truy vấn chạy ngày 2026-10-29: 13 trên PubMed (E-utilities, trường
`[tiab]`, lọc `2022:2026[dp]`), 7 trên Europe PMC (REST, trường `TITLE_ABS`, lọc
`PUB_YEAR:[2022 TO 2026]`, nguồn MED/PMC/PPR; riêng E6 và E9 tìm cả toàn văn mở), 7 trên
OpenAlex (lọc `title_and_abstract.search`, `publication_year:2022-2026`) và 5 tập bài trích dẫn
trên OpenAlex (mọi bài trích dẫn S4, S3, N1, N6, N8, không lọc năm). Tám chủ đề theo yêu cầu:
T1 thiết bị cổ tay hoặc đồng hồ đo cả ECG và PPG; T2 PAT so với đặc trưng PPG; T3 giá trị gia
tăng sau hiệu chuẩn cuff; T4 đánh giá nhiều ngày hoặc nhiều phiên; T5 baseline chỉ hiệu chuẩn
hoặc zero-change; T6 bài dùng dataset Aurora-BP; T7 PEP khi stress; T8 áp lực tiếp xúc ở PPG
cổ tay. Thêm hai truy vấn rộng để kiểm độ nhạy (P0/E0 và P10).

**Số bản ghi.** 2.180 bản ghi (PubMed 784, Europe PMC 652, OpenAlex tìm kiếm 362, OpenAlex
trích dẫn 382). Loại trùng theo DOI, PMID và tiêu đề chuẩn hóa còn **1.085 bản ghi**. Mọi bản
ghi đã được tải về; không truy vấn nào bị cắt trang.

**Sàng lọc.** Trợ lý AI đọc tiêu đề của cả 1.085 bản ghi, đọc abstract của 196 bản ghi (ứng
viên sau sàng lọc tiêu đề, cộng mọi bản ghi có tiêu đề liên quan BP trong E6, O6, P6 và C1 để
kiểm kê bài dùng Aurora-BP). **Giữ lại 80** bản ghi: 25 thành dòng N18–N42, 34 ghi ở mục 3.1–3.2,
21 là nguồn đã có (S, N, #) hoặc bản preprint/abstract hội nghị của nguồn đã có. **Loại 1.005.**
Không có người thứ hai sàng lọc.

**Tiêu chí giữ lại:** nghiên cứu trên người (hoặc tổng quan/khuyến cáo mới) liên quan trực
tiếp tới một chủ đề T1–T8 ở mức có thể làm đổi khoảng trống hoặc rủi ro của RQ1. **Mã lý do
loại** (dùng ở bảng dưới):

- **L1** chủ đề khác (HRV, rung nhĩ, ngừng tim, ngủ, tâm thần, can thiệp lối sống, trùng tên
  viết tắt hay tên dự án);
- **L2** dữ liệu ICU, phẫu thuật hoặc dataset công khai một buổi (MIMIC, VitalDB, UCI, PulseDB),
  không có cấu trúc phiên;
- **L3** cảm biến hoặc vị trí khác (camera, radar, siêu âm, tonometry, áp điện, BCG, cân,
  smartphone) và không thuộc T7/T8;
- **L4** không hiệu chuẩn (BP tuyệt đối) hoặc chỉ phân loại tăng huyết áp;
- **L5** một buổi, không so PPG với PAT, không có baseline chỉ hiệu chuẩn;
- **L6** tổng quan, bình luận hoặc khuyến cáo chung, không thêm thông tin cho khoảng trống;
- **L7** trùng nội dung (abstract hội nghị, preprint của bài đã đăng).

**Bảng 2.2a. Kết quả theo truy vấn** ("Đã xem abstract" gồm cả nguồn đã có; với C1, C2,
E6, O6, P6 con số lớn vì mọi bản ghi có tiêu đề liên quan BP đều được xem để kiểm kê Aurora-BP)

| ID | Nguồn | Chủ đề | Bản ghi | Đã xem abstract | Giữ lại | Dòng N mới | Lý do loại chính |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0 | PubMed | Rộng: BP + PPG + ECG/PAT/PTT | 250 | 45 | 20 | N18, N20, N26, N27, N35, N41, N42 | L2, L5, L1 |
| P1 | PubMed | T1 | 22 | 6 | 4 | N35, N42 | L1 (ngừng tim, rung nhĩ), L6 |
| P2 | PubMed | T2 | 19 | 9 | 4 | — | L5, L2, L3 |
| P3 | PubMed | T3 (ECG/PAT + PPG) | 28 | 17 | 11 | N18, N41 | L2, L4 |
| P3b | PubMed | T3 (mọi cảm biến) | 94 | 41 | 28 | N18, N22, N24, N28, N31, N33, N34, N39, N40 | L3, L4, L6 |
| P4 | PubMed | T4 | 46 | 25 | 17 | N18, N28, N31, N33, N34, N39, N40 | L3, L4 |
| P5 | PubMed | T5 | 65 | 27 | 17 | N18, N22, N23, N25, N26, N32, N34 | L1 (từ khóa "BP changes" rộng), L3 |
| P6 | PubMed | T6 | 10 | 8 | 7 | N20 | L1 (dự án khác tên AURORA) |
| P7 | PubMed | T7 (PEP + stress) | 104 | 9 | 5 | N28, N29, N30 | L1 (PEP chỉ là chỉ số tâm sinh lý) |
| P7b | PubMed | T7 (PEP + PAT/PTT/PWV/PPG) | 16 | 5 | 4 | N28, N29 | L1, L2 |
| P8 | PubMed | T8 | 20 | 8 | 7 | N35, N36, N38 | L1 (SpO2, HR), vị trí ngón tay |
| P9 | PubMed | Lõi RQ1 (giao T1–T4) | 10 | 7 | 3 | N18 | L3, L2 |
| P10 | PubMed | Rộng: mọi bài PAT | 100 | 28 | 13 | N18, N25, N26, N27, N28, N41 | L1 (ngủ, tim mạch lâm sàng, trùng viết tắt) |
| E0 | Europe PMC | Rộng (như P0) | 258 | 40 | 16 | N18, N20, N27, N35, N41, N42 | L2, L5, L7 |
| E4 | Europe PMC | T4 | 49 | 26 | 17 | N18, N21, N28, N31, N33, N39, N40 | L3, L4 |
| E5 | Europe PMC | T5 | 146 | 33 | 22 | N18, N21, N22, N23, N25, N26, N28, N29, N34 | L1, L3 |
| E6 | Europe PMC | T6 (cả toàn văn mở) | 98 | 31 | 19 | N20, N21, N22, N38, N39, N40 | L1 (AURORA là dự án khác), chỉ trích dẫn Aurora |
| E7 | Europe PMC | T7 | 73 | 6 | 4 | N28, N29 | L1 |
| E8 | Europe PMC | T8 | 19 | 8 | 7 | N35, N36, N38 | L1 |
| E9 | Europe PMC | Lõi RQ1, toàn văn mở | 9 | 5 | 2 | N40 | L6, L2 |
| O1 | OpenAlex | T1 | 62 | 9 | 3 | N35, N42 | L1, L7 |
| O2 | OpenAlex | T2 | 20 | 3 | 1 | — | L3, L2 |
| O4 | OpenAlex | T3/T4 | 69 | 27 | 15 | N21, N31, N33, N39, N40 | L7, L4, L3 |
| O5 | OpenAlex | T5 | 10 | 1 | 0 | — | L1 |
| O6 | OpenAlex | T6 | 23 | 21 | 17 | N20, N21 | L1 |
| O7 | OpenAlex | T7 | 113 | 8 | 4 | N28, N29 | L1 |
| O8 | OpenAlex | T8 | 65 | 16 | 9 | N35, N36, N37, N38 | L1 ("contact force" trong kỹ thuật khác) |
| C1 | OpenAlex | Bài trích dẫn S4 | 95 | 87 | 22 | N19, N20, N21, N22, N39 | L2, L3, L6 |
| C2 | OpenAlex | Bài trích dẫn S3 | 82 | 42 | 12 | N19, N22, N27, N39 | L3, L6 |
| C3 | OpenAlex | Bài trích dẫn N1 | 78 | 12 | 7 | N36 | L2, L3 |
| C4 | OpenAlex | Bài trích dẫn N6 | 82 | 28 | 8 | N20, N21, N33, N39 | L2, L3, L6 |
| C5 | OpenAlex | Bài trích dẫn N8 | 45 | 14 | 3 | N34 | L6, L1 |

**Chuỗi truy vấn nguyên văn** (ngày chạy 2026-10-29):

```text
P0  "blood pressure"[tiab] AND (photoplethysmogra*[tiab] OR PPG[tiab]) AND (electrocardiogra*[tiab] OR ECG[tiab] OR "pulse arrival time"[tiab] OR "pulse transit time"[tiab]) AND 2022:2026[dp]
P1  "blood pressure"[tiab] AND (wrist*[tiab] OR watch[tiab] OR smartwatch*[tiab] OR "smart watch"[tiab] OR wristband*[tiab] OR bracelet*[tiab]) AND (electrocardiogra*[tiab] OR ECG[tiab] OR EKG[tiab]) AND (photoplethysmogra*[tiab] OR PPG[tiab]) AND 2022:2026[dp]
P2  ("pulse arrival time"[tiab] OR "pulse transit time"[tiab] OR PTT[tiab]) AND (photoplethysmogra*[tiab] OR PPG[tiab]) AND "blood pressure"[tiab] AND (morpholog*[tiab] OR waveform*[tiab] OR "pulse wave analysis"[tiab] OR "pulse contour"[tiab] OR "PPG features"[tiab] OR "PPG-only"[tiab] OR "PPG only"[tiab]) AND (compar*[tiab] OR "added value"[tiab] OR additional[tiab] OR combin*[tiab] OR fusion[tiab]) AND 2022:2026[dp]
P3  calibrat*[tiab] AND ("pulse arrival time"[tiab] OR "pulse transit time"[tiab] OR electrocardiogra*[tiab] OR ECG[tiab]) AND (photoplethysmogra*[tiab] OR PPG[tiab]) AND "blood pressure"[tiab] AND (cuffless[tiab] OR cuff-less[tiab] OR "cuff-free"[tiab] OR wearable*[tiab]) AND 2022:2026[dp]
P3b "blood pressure"[tiab] AND (cuffless[tiab] OR cuff-less[tiab]) AND calibrat*[tiab] AND 2022:2026[dp]
P4  ("pulse arrival time"[tiab] OR "pulse transit time"[tiab] OR cuffless[tiab] OR cuff-less[tiab]) AND "blood pressure"[tiab] AND calibrat*[tiab] AND (day[tiab] OR days[tiab] OR week*[tiab] OR month*[tiab] OR year*[tiab] OR longitudinal[tiab] OR "long-term"[tiab] OR multiday[tiab] OR "multi-day"[tiab] OR session*[tiab] OR recalibrat*[tiab] OR drift[tiab] OR aging[tiab]) AND 2022:2026[dp]
P5  "blood pressure"[tiab] AND (cuffless[tiab] OR cuff-less[tiab] OR wearable*[tiab] OR "pulse arrival time"[tiab] OR "pulse transit time"[tiab]) AND ("calibration-only"[tiab] OR "calibration only"[tiab] OR "zero-change"[tiab] OR "zero change"[tiab] OR "no-change"[tiab] OR "baseline device"[tiab] OR "calibration BP"[tiab] OR "calibration value*"[tiab] OR "naive model"[tiab] OR "null model"[tiab] OR "B-score"[tiab] OR "persistence model"[tiab] OR "dummy model"[tiab] OR "baseline model*"[tiab] OR "trivial"[tiab] OR "track changes"[tiab] OR "tracking changes"[tiab] OR "BP changes"[tiab] OR "blood pressure changes"[tiab]) AND 2022:2026[dp]
P6  ("Aurora-BP"[tiab] OR "AuroraBP"[tiab] OR (Aurora[tiab] AND "blood pressure"[tiab])) AND 2022:2026[dp]
P7  ("pre-ejection period"[tiab] OR "preejection period"[tiab]) AND (stress*[tiab] OR "mental arithmetic"[tiab] OR "cold pressor"[tiab] OR sympathetic[tiab] OR "pulse arrival time"[tiab] OR "pulse transit time"[tiab]) AND 2022:2026[dp]
P7b ("pre-ejection period"[tiab] OR "preejection period"[tiab]) AND ("pulse arrival time"[tiab] OR "pulse transit time"[tiab] OR "pulse wave velocity"[tiab] OR photoplethysmogra*[tiab] OR PPG[tiab] OR cuffless[tiab] OR cuff-less[tiab]) AND 2022:2026[dp]
P8  ("contact pressure"[tiab] OR "contact force"[tiab] OR "hold-down pressure"[tiab] OR "applied pressure"[tiab] OR "strap tension"[tiab] OR "strap tightness"[tiab] OR "sensor pressure"[tiab]) AND (photoplethysmogra*[tiab] OR PPG[tiab]) AND 2022:2026[dp]
P9  ("pulse arrival time"[tiab] OR "pulse transit time"[tiab] OR electrocardiogra*[tiab] OR ECG[tiab]) AND (photoplethysmogra*[tiab] OR PPG[tiab]) AND "blood pressure"[tiab] AND calibrat*[tiab] AND (day[tiab] OR days[tiab] OR week*[tiab] OR month*[tiab] OR session*[tiab] OR longitudinal[tiab] OR "long-term"[tiab]) AND 2022:2026[dp]
P10 "pulse arrival time"[tiab] AND 2022:2026[dp]

E0  TITLE_ABS:"blood pressure" AND (TITLE_ABS:photoplethysmogra* OR TITLE_ABS:PPG) AND (TITLE_ABS:electrocardiogra* OR TITLE_ABS:ECG OR TITLE_ABS:"pulse arrival time" OR TITLE_ABS:"pulse transit time") AND PUB_YEAR:[2022 TO 2026] AND (SRC:MED OR SRC:PMC OR SRC:PPR)
E4  (TITLE_ABS:"pulse arrival time" OR TITLE_ABS:"pulse transit time" OR TITLE_ABS:cuffless OR TITLE_ABS:"cuff-less") AND TITLE_ABS:"blood pressure" AND TITLE_ABS:calibrat* AND (TITLE_ABS:day OR TITLE_ABS:days OR TITLE_ABS:week* OR TITLE_ABS:month* OR TITLE_ABS:year* OR TITLE_ABS:longitudinal OR TITLE_ABS:"long-term" OR TITLE_ABS:session* OR TITLE_ABS:recalibrat* OR TITLE_ABS:drift OR TITLE_ABS:aging) AND PUB_YEAR:[2022 TO 2026] AND (SRC:MED OR SRC:PMC OR SRC:PPR)
E5  TITLE_ABS:"blood pressure" AND (TITLE_ABS:cuffless OR TITLE_ABS:"cuff-less" OR TITLE_ABS:wearable* OR TITLE_ABS:"pulse arrival time" OR TITLE_ABS:"pulse transit time") AND (TITLE_ABS:"calibration-only" OR TITLE_ABS:"calibration only" OR TITLE_ABS:"zero-change" OR TITLE_ABS:"zero change" OR TITLE_ABS:"no-change" OR TITLE_ABS:"baseline device" OR TITLE_ABS:"calibration BP" OR TITLE_ABS:"naive model" OR TITLE_ABS:"null model" OR TITLE_ABS:"B-score" OR TITLE_ABS:"persistence model" OR TITLE_ABS:"dummy model" OR TITLE_ABS:"track changes" OR TITLE_ABS:"tracking changes" OR TITLE_ABS:"BP changes" OR TITLE_ABS:"blood pressure changes") AND PUB_YEAR:[2022 TO 2026] AND (SRC:MED OR SRC:PMC OR SRC:PPR)
E6  ("Aurora-BP" OR "AuroraBP" OR "Aurora project" OR ("Aurora" AND "cuffless")) AND PUB_YEAR:[2022 TO 2026] AND (SRC:MED OR SRC:PMC OR SRC:PPR)
E7  (TITLE_ABS:"pre-ejection period" OR TITLE_ABS:"preejection period") AND (TITLE_ABS:"pulse arrival time" OR TITLE_ABS:"pulse transit time" OR TITLE_ABS:"pulse wave velocity" OR TITLE_ABS:photoplethysmogra* OR TITLE_ABS:PPG OR TITLE_ABS:cuffless OR TITLE_ABS:stress) AND PUB_YEAR:[2022 TO 2026] AND (SRC:MED OR SRC:PMC OR SRC:PPR)
E8  (TITLE_ABS:"contact pressure" OR TITLE_ABS:"contact force" OR TITLE_ABS:"hold-down pressure" OR TITLE_ABS:"applied pressure" OR TITLE_ABS:"strap tension" OR TITLE_ABS:"strap tightness" OR TITLE_ABS:"sensor pressure") AND (TITLE_ABS:photoplethysmogra* OR TITLE_ABS:PPG) AND PUB_YEAR:[2022 TO 2026] AND (SRC:MED OR SRC:PMC OR SRC:PPR)
E9  ("pulse arrival time" AND ("PPG only" OR "PPG-only" OR "photoplethysmogram only") AND "blood pressure" AND calibration AND (days OR sessions OR longitudinal)) AND PUB_YEAR:[2022 TO 2026] AND (SRC:MED OR SRC:PMC OR SRC:PPR)

OpenAlex: filter=title_and_abstract.search:<chuỗi>,publication_year:2022-2026
O1  "blood pressure" AND (wrist OR watch OR smartwatch OR wristband OR bracelet) AND (electrocardiogram OR electrocardiography OR ECG) AND (photoplethysmography OR photoplethysmogram OR PPG)
O2  ("pulse arrival time" OR "pulse transit time") AND (photoplethysmography OR photoplethysmogram OR PPG) AND "blood pressure" AND (morphology OR "waveform features" OR "pulse wave analysis" OR "PPG features" OR "PPG only") AND (comparison OR compared OR "added value" OR combined OR fusion)
O4  "blood pressure" AND ("pulse arrival time" OR "pulse transit time" OR cuffless OR "cuff-less") AND calibration AND (days OR weeks OR months OR longitudinal OR "long-term" OR sessions OR recalibration OR drift)
O5  "blood pressure" AND (cuffless OR "cuff-less" OR wearable OR "pulse arrival time" OR "pulse transit time") AND ("calibration-only" OR "calibration only" OR "zero-change" OR "zero change" OR "no-change" OR "baseline device" OR "naive model" OR "null model" OR "B-score" OR "persistence model" OR "dummy model")
O6  "Aurora-BP" OR (Aurora AND "blood pressure" AND (wearable OR cuffless OR "cuff-less" OR ambulatory))
O7  ("pre-ejection period" OR "preejection period") AND ("pulse arrival time" OR "pulse transit time" OR "pulse wave velocity" OR photoplethysmography OR cuffless OR stress)
O8  ("contact pressure" OR "contact force" OR "hold-down pressure" OR "applied pressure" OR "strap tension" OR "strap tightness") AND (photoplethysmography OR photoplethysmogram OR PPG)
C1  cites:W4213432829 (S4)   C2 cites:W4310598717 (S3)   C3 cites:W4317215138 (N1)
C4  cites:W4377142751 (N6)   C5 cites:W4409443090 (N8)
```

**Đã mở toàn văn** (đọc ngày 2026-10-29, trừ hình và danh mục tài liệu tham khảo):

- N5 (BioC, PMC8221527), N7 (Europe PMC XML, PMC11532190), N8 (trang PMC12331212),
  N16 (bản chấp nhận, ETH Research Collection, văn bản trích tự động), N18 (BioC, PMC9154072):
  đọc hết phần thân bài.
- Đọc có chọn lọc: N22 (đoạn Methods mô tả thiết bị, PMC10906216), N39 (PMC13506816) và N40
  (PMC13669345) (abstract và các đoạn về phạm vi, hiệu chuẩn, baseline).
- Đã tải nhưng chưa đọc: N23 (PMC10158604).
- Ngoài bài báo: bản ghi dataset Aurora-BP trên Zenodo (mô tả và danh sách tệp; chưa đọc tệp
  Data Use Agreement).

**Bị chặn** (ghi là bị chặn, không phải "không tìm thấy"):

- N6: truy cập mở hybrid. Crossref ghi giấy phép CC BY 4.0 cho bản đã xuất bản; Europe PMC có
  PMID 37204948 nhưng không có PMCID. Hai đường tải đều bị chặn:
  - ieeexplore.ieee.org trả HTTP 418 cho truy cập tự động; trình duyệt trong app hai lần không mở
    được trang IEEE;
  - kho CityU Scholars có bản "Final Published version" (CC BY), nhưng tệp PDF nằm sau trang kiểm
    tra Cloudflare: truy cập tự động bị trả 403, trình duyệt trong app hiện ô "Verify you are
    human". Không vượt kiểm tra này.
- S4: toàn văn có phí. Crossref chỉ có giấy phép IEEE; Europe PMC có PMID 35201992 nhưng không có
  PMCID; trang publication của Microsoft Research trả HTTP 403. Theo quyết định ngày 2026-10-29,
  không lấy qua thư viện; S4 chỉ dùng abstract.
- Europe PMC `fullTextXML` trả HTTP 500 cho PMC8221527, PMC12331212, PMC9154072 (đã đọc thay
  bằng BioC hoặc trang PMC). BioC không có N8 (ngoài tập truy cập mở).
- Trang item của ETH Research Collection trả HTTP 500 (đã lấy văn bản qua REST API của kho).
- Semantic Scholar API trả HTTP 429, nên không lấy được abstract của He 2022, Li Y 2026 (mục
  6.1).
- Toàn văn đóng, không thử vượt: N19, N20, N28, N31, N37 và ba bài thiếu abstract ở mục 6.1.

**Dừng sớm:** không với phần tìm và sàng lọc tiêu đề (mọi bản ghi của 32 truy vấn đã tải và
đọc tiêu đề). Có giới hạn ở bước sau: chỉ đọc abstract của 196 bản ghi; đọc toàn văn 5 bài và
một phần 3 bài. Các bản ghi bị loại ở bước tiêu đề không được đọc abstract.

**Chưa tra:** IEEE Xplore, Scopus, Web of Science, Embase, Google Scholar, CNKI; ngoài giai
đoạn 2022–2026 (trừ tập bài trích dẫn); tài liệu không phải tiếng Anh (vài bản ghi tiếng Bồ
Đào Nha, Nga, Đức trong OpenAlex chỉ được sàng lọc theo tiêu đề). OpenAlex không có abstract
của một số nhà xuất bản, nên tìm theo `title_and_abstract` có thể sót bài. Không thấy một bài
không có nghĩa là bài đó không tồn tại.

## 3. Bảng nguồn

| Mã | Trích dẫn | DOI | Thiết kế (theo nguồn) | Liên quan tới RQ1 | Mức đã đọc |
| --- | --- | --- | --- | --- | --- |
| **N1** | Finnegan E, Davidson SM, Harford M, Watkinson P, Tarassenko L, Villarroel M. Features from the photoplethysmogram and the electrocardiogram for estimating changes in blood pressure. *Sci Rep* 2023 | [10.1038/s41598-022-27170-2](https://doi.org/10.1038/s41598-022-27170-2) | 30 người khỏe, tuổi 28,0 (9,0), phân tích 26 người; truyền phenylephrine tĩnh mạch; PPG ngón tay, ECG ngực; cuff mỗi phút; **một buổi** khoảng 28 phút; baseline zero-change; LOSO lồng. So bốn bộ đặc trưng PPG, ECG, PPG + ECG, PAT. ΔSBP (median qua fold): zero-change MAE 7,40; RF PPG 4,75; LASSO + OLS PAT 4,91 mmHg | **Gần nhất về cách đánh giá.** Khác: một buổi, thuốc chứ không phải nghiệm pháp, PPG ngón tay; không có mô hình PPG + PAT. Tác giả nêu hướng tiếp: dữ liệu dọc theo thời gian của từng người | Toàn văn (Europe PMC), đọc 200.000/272.331 ký tự; kết quả ΔDBP ở phụ lục chưa đọc |
| **N2** | Natarajan K et al. (8 tác giả). Photoplethysmography fast upstroke time intervals can be useful features for cuff-less measurement of blood pressure changes in humans. *IEEE Trans Biomed Eng* (online 2021) | [10.1109/tbme.2021.3087105](https://doi.org/10.1109/tbme.2021.3087105) | 32 người (25% tăng huyết áp, tuổi 52); thở chậm, tính nhẩm, ngâm lạnh, nitroglycerin; PPG ngón tay, ngón chân, tai và ECG; cuff thủ công; một quy trình phòng thí nghiệm. Baseline "không đổi" RMSE 10,9/6,5 mmHg; đặc trưng sườn lên PPG cộng PAT giảm RMSE SBP 6–7% (9,5 mmHg) | Gần về nghiệm pháp và so PPG với PAT. Khác: một buổi, không ở cổ tay (tác giả ghi tín hiệu cổ tay kém hữu ích). Ghi nhận: dạng sóng PPG chịu ảnh hưởng của áp lực tiếp xúc nhiều hơn PAT. Cùng cohort với N3 và N18 | Toàn văn (PMC), một lượt |
| **N3** | Block RC et al. (13 tác giả). Conventional pulse transit times as markers of blood pressure changes in humans. *Sci Rep* 2020 | [10.1038/s41598-020-73143-8](https://doi.org/10.1038/s41598-020-73143-8) | Cùng cohort N2 (32/44 người); so sáu khoảng PAT/PTT; PAT ngón chân tương quan với SBP tốt nhất (r −0,63 ± 0,05); PAT ngón tay tương quan kém | Cơ sở cho việc PAT phụ thuộc vị trí đo và PEP; một buổi | Toàn văn (Europe PMC), một lượt |
| **N4** | Ding X, Yan BP, Zhang YT, Liu J, Zhao N, Tsang HK. Pulse transit time based continuous cuffless blood pressure estimation: a new extension and a comprehensive evaluation. *Sci Rep* 2017 | [10.1038/s41598-017-11507-3](https://doi.org/10.1038/s41598-017-11507-3) | 33 người (14 tăng huyết áp); PTT và PIR; Finapres; đứng dậy, thở sâu, Valsalva, bóp tay; theo dõi 24 giờ ở nhóm nhỏ. Sang ngày 2, sai số tăng ở mọi phương pháp | Bằng chứng sai số tăng khi đánh giá ngày hôm sau; không có baseline chỉ hiệu chuẩn trong phần đã đọc | Toàn văn (Europe PMC), đọc 100.000/137.802 ký tự |
| **N5** | Ganti VG et al. (6 tác giả). Wearable cuff-less blood pressure estimation at home via pulse transit time. *IEEE J Biomed Health Inform* (online 2020) | [10.1109/jbhi.2020.3021532](https://doi.org/10.1109/jbhi.2020.3021532) | Đồng hồ SeismoWatch 2.0: ECG một đạo trình (ngón tay bên kia chạm điện cực trên dây đeo), SCG ba trục (áp đồng hồ lên giữa xương ức), PPG cổ tay nhiều bước sóng. PTT = mở van động mạch chủ trên SCG → chân sóng PPG cổ tay (hồng ngoại); ECG chỉ dùng để tách nhịp. 21 người khỏe (25,9 ± 3,4 tuổi) đo tại nhà mỗi giờ trong 24 giờ, cuff Omron BP785N; dùng 216/245 lần đo. Hồi quy tuyến tính theo từng người trên dữ liệu 24 giờ: RMSE DBP/MAP/SBP 2,72/2,99/4,75 mmHg, r 0,69/0,61/0,33. Hiệu chuẩn một điểm (giữ nguyên một giá trị DBP) RMSE 6,05 ± 1,75 mmHg; 4 điểm 4,73 ± 2,41; 6 điểm 3,83 ± 1,40 mmHg | Cùng ngày (24 giờ), không có phiên khác ngày; không so PPG-only với PAT (đo PTT thật, không dùng PAT); cần áp đồng hồ lên ngực nên không thuần cổ tay. Tác giả ghi cần đánh giá đường hiệu chuẩn qua nhiều ngày. Phép hiệu chuẩn một điểm của bài tương tự baseline zero-change, nhưng các mô hình PTT được ước lượng trên chính dữ liệu cùng ngày | Toàn văn (BioC, PMC8221527), 2026-10-29 |
| **N6** | Liu ZD et al. (8 tác giả). Cuffless blood pressure measurement using smartwatches: a large-scale validation study. *IEEE J Biomed Health Inform* 2023;27(9):4216–4227 | [10.1109/jbhi.2023.3278168](https://doi.org/10.1109/jbhi.2023.3278168) | 3.077 người, theo dõi khoảng 1 tháng; đồng hồ đo ECG, sóng áp lực mạch, PPG nhiều bước sóng; nghe tim hai người đo; mô hình PTT (theo cách gọi của bài), học máy và học sâu, có và không hiệu chuẩn. Theo N8 (toàn văn): thiết bị đo ECG và PPG khi đặt ngón tay bàn tay kia lên cảm biến, cùng một cảm biến sóng mạch trên động mạch quay; bài có bảng so với baseline model (Bảng IV) và báo sai số thấp hơn baseline 0–3 mmHg; N8 lo ngại rò rỉ dữ liệu vì phương pháp tốt nhất và tham số α được chọn trên dữ liệu test | **Đối thủ lớn nhất về quy mô và nhiều phiên.** Đã biết (qua N8) là có so với baseline; **chưa biết** có tách PPG-only với PPG + PAT không | Abstract; nội dung so với baseline lấy từ N8. Bài truy cập mở (CC BY) nhưng toàn văn **bị chặn** khi tải (mục 2.2). Chưa trả lời được bốn câu: có so PPG-only với PPG + PAT trên cùng người không; baseline gồm gì; khoảng cách từ hiệu chuẩn tới lần đo; có chia train/test theo người không |
| **N7** | Hove C et al. (10 tác giả). A prototype photoplethysmography-based cuffless device shows promising results in tracking changes in blood pressure. *Front Med Technol* 2024 | [10.3389/fmedt.2024.1464473](https://doi.org/10.3389/fmedt.2024.1464473) | Nguyên mẫu chỉ PPG (Aidee Health) đặt ở **cánh tay trên** trái; tuyển 67, phân tích 38 người (29 loại do nhiễu tham chiếu), tuổi trung vị 33; bóp tay tĩnh 30% MVC, tính nhẩm trừ 13 trong 5 phút, ngâm tay vào nước đá 2 phút; tham chiếu kẹp ngón tay (Nexfin hoặc Human NIBP) hiệu chuẩn lại trước mỗi hoạt động; thiết bị hiệu chuẩn offset một lần lúc nghỉ đầu buổi; mô hình xây trên chính cohort bằng 3-fold CV rồi lấy trung bình ba mô hình. Theo ISO 81060-3: Accuracy 0,3 (8,7)/0,04 (6,6) mmHg (SBP/DBP); Stability (11 người đo lại bóp tay ngày hôm sau) 1,9 (9,2)/2,9 (8,1); Change bách phân vị 50/85: 39/56% (SBP), 32/48% (DBP) | Nghiệm pháp gần protocol của nhóm. Có đo lại ngày hôm sau ở 11 người nhưng chỉ PPG, không có baseline chỉ hiệu chuẩn; không ở cổ tay. Phần đã đọc không nói rõ dự đoán cho mỗi người có dùng mô hình không học từ người đó không | Toàn văn (Europe PMC XML, PMC11532190), 2026-10-29 |
| **N8** | Mukkamala R, Shroff SG, Kyriakoulis KG, Avolio AP, Stergiou GS. Cuffless blood pressure measurement: where do we actually stand? *Hypertension* 2025 | [10.1161/hypertensionaha.125.24822](https://doi.org/10.1161/hypertensionaha.125.24822) | Tổng quan. Theo tác giả: Aurora cho thấy phân tích bằng học máy sóng tonometry, PPG cổ tay và ECG không thêm giá trị so với baseline từ BP hiệu chuẩn và thời điểm trong ngày; các nghiên cứu lớn gần đây (gồm N6, N20) có so với baseline nhưng có nguy cơ rò rỉ dữ liệu; thiết bị Aktiia và Samsung cho giá trị gần BP hiệu chuẩn (N23, N24); kiểm tra ngay sau hiệu chuẩn không cho thông tin; áp lực tiếp xúc làm đổi biên độ và hình dạng PPG. Kết luận: chưa có bằng chứng thuyết phục rằng phân tích dạng sóng và PAT thêm giá trị đáng kể ngoài cuff hiệu chuẩn hoặc nhân khẩu học; nên hoài nghi trừ khi có thử nghiệm độc lập, tiến cứu, so sánh chặt với baseline model hoặc thử nghiệm ngẫu nhiên | Khung định vị chính cho RQ1. Ba điều kiện "đáng xem xét" của tác giả là tiêu chí phản biện có thể gặp. Tác giả khai có tài trợ NIH và thỏa thuận nghiên cứu với Apple | Toàn văn (trang PMC12331212), trừ phụ lục và hình, 2026-10-29 |
| **N9** | Finnegan E et al. (8 tác giả). Pulse arrival time as a surrogate of blood pressure. *Sci Rep* 2021 | [10.1038/s41598-021-01358-4](https://doi.org/10.1038/s41598-021-01358-4) | 30 người khỏe, buổi khoảng 28 phút, truyền phenylephrine; PEP tăng 5,5 ± 4,5 ms so với nền, trong khi PTT thay đổi biên độ lớn hơn (−16,8 ± 7,5 ms theo abstract); so các mô hình PAT và PTT | Cơ sở PAT của N1; PEP ít đổi khi dùng phenylephrine, khác với nghiệm pháp stress (N11) | Abstract (Europe PMC) |
| **N10** | Kaetheeswaran J, Ma B, Abedi A, Khan SS, Lankarany M. Calibration-free cuffless blood pressure estimation using multimodal ECG-PPG fusion on a Google Pixel Watch. arXiv:2608.26325, 2026 | [arXiv:2608.26325](https://arxiv.org/abs/2608.26325) | 40 người, đồng hồ thương mại, kết hợp ECG–PPG và nhân khẩu học, không hiệu chuẩn | Hướng không hiệu chuẩn, khác RQ1; preprint chưa phản biện. Dữ liệu có thể là N42 | Abstract |
| **N11** | Pilz N, Patzak A, Bothe TL. The pre-ejection period is a highly stress dependent parameter of paramount importance for pulse-wave-velocity based applications. *Front Cardiovasc Med* 2023 | [10.3389/fcvm.2023.1138356](https://doi.org/10.3389/fcvm.2023.1138356) | 71 người trẻ; PEP đo bằng impedance cardiography lúc nghỉ, stress tinh thần (TSST) và gắng sức (ergometer). PEP lúc nghỉ trung bình 104,5 ms, biến thiên giữa người lớn, trong người nhỏ; stress tinh thần giảm PEP 16% (90,0 ms); gắng sức giảm một nửa (53,9 ms) | Bằng chứng trực tiếp cho rủi ro PEP ở M2 (tính nhẩm) của RQ1, và ở M4 (đạp xe) trước khi bỏ ngày 2026-10-29: PAT có thể ngắn lại do PEP | Abstract (PubMed) |
| **N12** | Charlton PH, Marozas V, Mejía-Mejía E, Kyriacou PA, Mant J. Determinants of photoplethysmography signal quality at the wrist. *PLOS Digit Health* 2025 | [10.1371/journal.pdig.0000585](https://doi.org/10.1371/journal.pdig.0000585) | Aurora-BP, PPG cổ tay của 1.142 người; SNR, perfusion index, TMCC. Chất lượng cao nhất khi nằm ngửa; khi ngồi, tay buông dọc thân 10,5 dB, tay trên đùi 13,7 dB, cảm biến ngang tim 15,5 dB; SNR và TMCC tăng theo tuổi | Tư thế tay và độ cao cảm biến đổi chất lượng PPG cổ tay → cố định tư thế tay giữa các phiên; liên quan SQI (RQ3) | Abstract |
| **N13** | Sirkiä JP, Panula T, Kaisti M. Investigating the impact of contact pressure on photoplethysmograms. *Biomed Eng Adv* 2024 | [10.1016/j.bea.2024.100123](https://doi.org/10.1016/j.bea.2024.100123) | Thiết bị cuff ngón tay đo PPG đa phổ ở nhiều mức áp lực tiếp xúc; SpO2, PAT và đặc trưng PPG đều đổi theo áp lực; PAT tính từ chân sóng kênh đỏ và hồng ngoại ổn định nhất; áp lực khoảng 20–30 mmHg đến mức DBP cho đặc trưng tốt nhất | Rủi ro áp lực tiếp xúc của RQ1 (RQ mục 4.F): đặc trưng PPG nhạy với áp lực hơn PAT từ chân sóng (ở ngón tay) | Abstract (OpenAlex) |
| **N14** | Cheung MY, Sabharwal A, Coté GL, Veeraraghavan A. Wearable blood pressure monitoring devices: understanding heterogeneity in design and evaluation. *IEEE Trans Biomed Eng* 2024 | [10.1109/tbme.2024.3434344](https://doi.org/10.1109/tbme.2024.3434344) | Chưa đọc | Cách thiết kế và báo cáo đánh giá thiết bị BP đeo được | Chỉ metadata |
| **N15** | Elgendi M et al. (7 tác giả). Recommendations for evaluating photoplethysmography-based algorithms for blood pressure assessment. *Commun Med* 2024 | [10.1038/s43856-024-00555-2](https://doi.org/10.1038/s43856-024-00555-2) | Chưa đọc | Danh mục kiểm khi viết phần đánh giá | Chỉ metadata |
| **N16** | Cisnal A, Li Y, Fuchs B, Ejtehadi M, Riener R, Paez-Granados D. Robust feature selection for BP estimation in multiple populations: towards cuffless ambulatory BP monitoring. *IEEE J Biomed Health Inform* 2024 | [10.1109/jbhi.2024.3411693](https://doi.org/10.1109/jbhi.2024.3411693) | Aurora-BP, nhánh oscillometric (khám tại phòng và 24 giờ lưu động): 548 → 523 người, trung bình 23,9 lần đo/người sau xử lý; PPG cổ tay (cảm biến dựa trên MAX30101, tay đối diện cuff), đoạn 30 s, 500 Hz; chỉ PPG cộng nhân khẩu học, trong đó có SBP/DBP lúc nghỉ làm đặc trưng; chọn đặc trưng Markov blanket trên toàn bộ dữ liệu; Gradient Boosting; CV lồng (ngoài: bỏ một người; trong: 10-fold). MAE 10,29/6,74 mmHg (SBP/DBP); tại phòng 8,49/5,03, lưu động 11,35/7,85 | Không có ECG/PAT, không so với baseline chỉ BP lúc nghỉ trong phần đã đọc, nên không thu hẹp khoảng trống RQ1. Chọn đặc trưng trên toàn bộ dữ liệu trước CV (tác giả thừa nhận có thể gây thiên lệch) là cách cần tránh. Aurora dùng cảm biến dựa trên MAX30101 như thiết bị của nhóm; ETH dùng dữ liệu theo thỏa thuận chuyển giao với Microsoft | Toàn văn bản chấp nhận (ETH Research Collection, hdl 20.500.11850/677790), văn bản trích tự động, không xem hình, 2026-10-29 |
| **N17** | Min S et al. (12 tác giả). Wearable blood pressure sensors for cardiovascular monitoring and machine learning algorithms for blood pressure estimation. *Nat Rev Cardiol* 2025 | [10.1038/s41569-025-01127-0](https://doi.org/10.1038/s41569-025-01127-0) | Tổng quan, chưa đọc | Bối cảnh cho phần Introduction | Chỉ metadata |
| **N18** | Yavarimanesh M, Block RC, Natarajan K, … Mukkamala R (7 tác giả). Assessment of calibration models for cuff-less blood pressure measurement after one year of aging. *IEEE Trans Biomed Eng* 2022;69(6):2087–2093 (online 2021) | [10.1109/tbme.2021.3136492](https://doi.org/10.1109/tbme.2021.3136492) | Cùng cohort N2/N3: thu lại dữ liệu ở 13/32 người, ba phiên cách nhau khoảng 1 năm (10–14 tháng); phân tích 10 người (6 nam, 57 ± 18 tuổi, 3 tăng huyết áp); phiên đầu coi là làm quen, mô hình lập ở phiên 2 và đánh giá ở phiên 3. Mỗi phiên: ECG, PPG tai, ngón tay, ngón chân, cuff nghe tim thủ công trước và sau thở chậm, tính nhẩm, ngâm lạnh (chân phải), thường thêm nitroglycerin. Bốn mô hình tuyến tính, hệ số riêng từng người lập từ mọi nghiệm pháp của một phiên: PAT ngón chân → SBP; PAT ngón tay + b-time → SBP; PAT tai + STT → SBP; STT + PW tai (chỉ PPG) → DBP. Baseline "naïve" = trung bình các lần cuff ban đầu của người đó. Sau 1 năm, bỏ ngoại lai, RMSE: PAT ngón chân 9,6 ± 0,8 so với naïve 12,7 ± 1,0 mmHg (p < 0,05); PAT ngón tay + b-time 10,3 ± 1,2 (p = 0,12); PAT tai + STT 11,9 ± 1,2; mô hình chỉ PPG cho DBP 7,3 ± 0,7 so với naïve 4,8 ± 0,3 (kém hơn naïve). Lập mô hình từ 1–3 nghiệm pháp cho RMSE 18,1–48,1 mmHg (chưa bỏ ngoại lai) | **Làm đổi khoảng trống (mục 5).** Đã có đánh giá qua nhiều phiên (cách 1 năm) cho mô hình có PAT và mô hình chỉ đặc trưng PPG, so với baseline chỉ dùng cuff hiệu chuẩn, có nghiệm pháp gần M1, M2 (và M3 trước khi bỏ ngày 2026-10-29). Khác RQ1: không ở cổ tay; hiệu chuẩn nhiều điểm theo từng người bằng cả bộ nghiệm pháp, không phải chỉ offset từ M0; cách 1 năm, không phải vài ngày đến 4 tuần; không có ablation ghép cặp PPG-only với PPG + PAT cho cùng đầu ra; 10 người. Tác giả ước tính cần 31 người để mô hình ngón tay vượt naïve có ý nghĩa (α 0,05, power 0,8). Tác giả quy kết quả kém của PAT tai/ngón tay chủ yếu cho co cơ trơn mạch, PEP là yếu tố phụ | Toàn văn (BioC, PMC9154072), 2026-10-29 |
| **N19** | Cisnal A, Paez-Granados D, Pérez Turiel J, Fraile JC. Are PAT-based models suitable for continuous blood pressure monitoring in ambulatory settings? *Proc IEEE CBMS* 2025:1–6 | [10.1109/cbms65348.2025.00046](https://doi.org/10.1109/cbms65348.2025.00046) | Aurora-BP, 307 người, điều kiện lưu động; mô hình dựa trên PAT từ ECG và PPG của thiết bị mang theo. MAE tốt nhất 14,23 (SBP) và 9,67 mmHg (DBP); "baseline models" tốt hơn mô hình PAT tốt nhất cho SBP (MAE 13,04 mmHg) và tương đương cho DBP | Bằng chứng gần nhất về PAT so với baseline trên dữ liệu cổ tay lưu động. Abstract không nói baseline gồm gì, không nhắc mô hình PPG-only hay PPG + PAT, cũng không nhắc đánh giá ở phiên khác ngày; chưa xác nhận được khi chưa có toàn văn | Abstract (Semantic Scholar); toàn văn đóng |
| **N20** | Liu ZD, Li Y, Zhang YT, … Miao F (7 tác giả). HGCTNet: handcrafted feature-guided CNN and transformer network for wearable cuffless blood pressure measurement. *IEEE J Biomed Health Inform* 2024;28(7):3882–3894 | [10.1109/jbhi.2024.3395445](https://doi.org/10.1109/jbhi.2024.3395445) | Học sâu kết hợp đặc trưng thủ công từ sinh hiệu đo bằng thiết bị đeo và nhân khẩu học; hai bộ dữ liệu CAS-BP và Aurora-BP. Sai số SBP/DBP: CAS-BP 0,7 ± 8,3/0,9 ± 6,5 mmHg; Aurora-BP −0,4 ± 8,6/−0,4 ± 7,0 mmHg. Theo N8: bài phân tích một tập con dữ liệu của N6 cùng dữ liệu Aurora, có so với baseline model (Bảng IV) và so nhiều phương pháp trên dữ liệu test | Cùng nhóm N6; một trong các bài "tốt hơn baseline 0–3 mmHg" mà N8 cho là có nguy cơ rò rỉ. Abstract không cho biết có tách PPG-only với PPG + PAT hay đánh giá phiên khác ngày | Abstract; nội dung về baseline lấy từ N8; toàn văn đóng |
| **N21** | Huang H et al. (9 tác giả). RAGCBPNet: an efficient feature fusion framework for wearable cuffless blood pressure monitoring and long-term validation in real-world settings. *medRxiv* 2025 (preprint) | [10.1101/2025.10.30.25339198](https://doi.org/10.1101/2025.10.30.25339198) | Kết hợp đặc trưng PPG thủ công và học sâu với thông tin nhân khẩu học; Aurora-BP (MAE 7,08/4,90 mmHg) và một bộ dữ liệu đồng hồ 30+ ngày trong sinh hoạt tự do. Theo abstract: hiệu chuẩn ban đầu đủ giữ chuẩn AAMI cho SBP tới 14 ngày và cho DBP suốt thời gian theo dõi; dự đoán có biến thiên thấp hơn rõ so với BP tham chiếu | Nhiều tuần sau hiệu chuẩn nhưng chỉ PPG; biến thiên dự đoán thấp hơn tham chiếu là dấu hiệu bám gần mốc hiệu chuẩn (vấn đề N8 nêu). Không thấy ECG/PAT hay baseline chỉ hiệu chuẩn trong abstract. Abstract viết tên mô hình là "RACGBPNet", khác tiêu đề | Abstract; preprint chưa phản biện |
| **N22** | Derendinger FC et al. (7 tác giả). Ability of a 24-h ambulatory cuffless blood pressure monitoring device to track blood pressure changes in clinical practice. *J Hypertens* 2024;42(4):662–671 | [10.1097/hjh.0000000000003667](https://doi.org/10.1097/hjh.0000000000003667) | 166 người đo đồng thời 24 giờ Somnotouch-NIBP (ECG + PPG ngón tay; bài gọi là PTT, theo quy ước dự án là PAT) và máy cuff lưu động; BP hiệu chuẩn = lần cuff đầu. Chênh lệch trung bình (SD) giữa BP hiệu chuẩn và BP trung bình 24 giờ: SBP theo cuff 7,4 (13,2), theo thiết bị không cuff 1,8 (8,3) mmHg; DBP 6,6 (6,8) so với 1,6 (5,8). Quan hệ gần tuyến tính giữa mức BP thay đổi so với hiệu chuẩn và sai số của thiết bị | Thiết bị dựa trên PAT cho đầu ra bám gần BP hiệu chuẩn, tức hành xử gần zero-change. Củng cố yêu cầu báo SD của ΔBP tham chiếu và so với zero-change (RQ mục 4.D) | Abstract; đoạn Methods mô tả thiết bị (toàn văn PMC10906216, chưa đọc hết) |
| **N23** | Tan I et al. (8 tác giả). Evaluation of the ability of a commercially available cuffless wearable device to track blood pressure changes. *J Hypertens* 2023;41(6):1003–1010 | [10.1097/hjh.0000000000003428](https://doi.org/10.1097/hjh.0000000000003428) | Aktiia (PPG cổ tay); 41 người (80% tăng huyết áp) đeo 6–12 ngày, ABPM đầu và cuối đợt; ở 3 người tăng liều thuốc, BP giảm sau 2 tuần theo Aktiia −1,0/−0,8 mmHg so với đo tại nhà −19,7/−11,5 mmHg; thiết bị không theo được mức giảm BP ban đêm | Nhiều ngày nhưng chỉ PPG, không PAT; ví dụ thiết bị không theo được thay đổi BP lớn sau hiệu chuẩn | Abstract (toàn văn PMC10158604 đã tải, chưa đọc) |
| **N24** | Falter M et al. (11 tác giả). Smartwatch-based blood pressure measurement demonstrates insufficient accuracy. *Front Cardiovasc Med* 2022;9:958212 | [10.3389/fcvm.2022.958212](https://doi.org/10.3389/fcvm.2022.958212) | 40 bệnh nhân làm ABPM 24 giờ đeo thêm Samsung Galaxy Watch Active 2 (PPG) sau hiệu chuẩn; sai lệch tỷ lệ: BP thấp bị đánh giá cao, BP cao bị đánh giá thấp; tác giả kết luận có sai lệch hệ thống về phía điểm hiệu chuẩn; biến thiên BP của đồng hồ thấp hơn ABPM | Đầu ra thiết bị co về mốc hiệu chuẩn (24 giờ, chỉ PPG) → baseline zero-change là đối chứng bắt buộc | Abstract |
| **N25** | Hametner B et al. (12 tác giả). Non-invasive pulse arrival time as a surrogate for oscillometric systolic blood pressure changes during non-pharmacological intervention. *Physiol Meas* 2024;45(5):055015 | [10.1088/1361-6579/ad45ab](https://doi.org/10.1088/1361-6579/ad45ab) | 51 người (31 nữ); nhóm can thiệp làm nhiệm vụ thể lực và tinh thần (thứ tự đối trọng), có nhóm chứng; PAT đo bằng thiết bị cầm tay; BP oscillometric ở nền và sau mỗi nhiệm vụ. Sau thể lực: HR và SBP tăng, PAT giảm. Nhiệm vụ tinh thần: SBP giảm khi HR ổn định, PAT tăng. Tương quan thay đổi SBP–PAT: nền → thể lực −0,33; thể lực → tinh thần −0,51; nền → tinh thần −0,12 (không có ý nghĩa) | Gần M2 của RQ1: từ nền sang nhiệm vụ tinh thần, tương quan giữa thay đổi PAT và thay đổi SBP không có ý nghĩa thống kê (r = −0,12); một buổi | Abstract |
| **N26** | Heimark S et al. (11 tác giả). Blood pressure altering method affects correlation with pulse arrival time. *Blood Press Monit* 2022;27(2):139–146 (online 2021) | [10.1097/mbp.0000000000000577](https://doi.org/10.1097/mbp.0000000000000577) | 75 người (43,7% tăng huyết áp); đai ngực nguyên mẫu có ECG một kênh và cảm biến PPG; BP nghe tim; bài tập tĩnh và động. Tương quan cá nhân PAT–SBP −0,82 ± 0,14 (toàn protocol), −0,79 ± 0,27 (tĩnh), −0,77 ± 0,19 (động); PAT–DBP 0,25 ± 0,35, −0,74 ± 0,23 và 0,39 ± 0,41 (đổi dấu theo loại bài tập) | Quan hệ PAT–DBP phụ thuộc loại nghiệm pháp → ủng hộ phân tầng theo nghiệm pháp (RQ mục 4.B, 4.D); một buổi, không ở cổ tay | Abstract |
| **N27** | Heimark S et al. (12 tác giả). Accuracy and user acceptability of 24-hour ambulatory blood pressure monitoring by a prototype cuffless multi-sensor device compared to a conventional oscillometric device. *Blood Press* 2023;32(1):2274595 | [10.1080/08037051.2023.2274595](https://doi.org/10.1080/08037051.2023.2274595) | 95 người; thiết bị đa cảm biến đeo ngực (Aidee Health) tính PAT từ ECG và PPG; mô hình BP chung dựa trên PAT; đối chiếu ABPM 24 giờ. SBP ban ngày: tham chiếu 129,7 (13,8) so với PAT 133,6 (20,9) mmHg, LoA [−26,7; 34,6]; ban đêm 113,1 (16,5) so với 131,9 (23,4), LoA [−20,9; 58,4] | Mô hình PAT chung đồng thuận kém trong 24 giờ, nhất là ban đêm; không có PPG-only hay baseline chỉ hiệu chuẩn trong abstract | Abstract |
| **N28** | Xie C et al. (6 tác giả). Effects of pulse transit time and pulse arrival time on cuff-less blood pressure estimation: a comparison study with multiple experimental interventions. *Proc IEEE EMBC* 2023:1–4 | [10.1109/embc40787.2023.10340548](https://doi.org/10.1109/embc40787.2023.10340548) | 55 người, nhiều can thiệp làm đổi BP và PEP; so tương quan của BP với PTT và PAT và năm mô hình ước lượng. PEP đổi nhanh khi có stress thể lực; PTT tương quan tuyến tính tốt hơn, nhưng phần lớn mô hình dựa trên PAT chính xác hơn mô hình dựa trên PTT ở mọi can thiệp, nhất là khi có hiệu chuẩn | PEP vừa gây nhiễu vừa có thể mang thông tin cho mô hình PAT; một buổi; abstract không nêu vị trí PPG | Abstract; toàn văn đóng |
| **N29** | Djupedal H et al. (5 tác giả). Effects of experimental hypovolemia and pain on pre-ejection period and pulse transit time in healthy volunteers. *Physiol Rep* 2022;10(12):e15355 | [10.14814/phy2.15355](https://doi.org/10.14814/phy2.15355) | 14 người khỏe; LBNP 60 mmHg và cold pressor (đau) theo thiết kế 2 × 2; PEP và PTT tính từ ECG, Doppler động mạch chủ lên và sóng áp lực kẹp ngón tay. PEP tăng khi giảm thể tích, không đổi khi đau; PTT giảm khi đau, tăng khi giảm thể tích | Gần M3 (ngâm lạnh, đã bỏ ngày 2026-10-29): ở nghiên cứu này kích thích lạnh không làm đổi PEP, thay đổi nằm ở PTT; cỡ mẫu nhỏ, PTT không đo bằng PPG | Abstract |
| **N30** | Brinkmann K et al. (4 tác giả). A well-powered test of task difficulty effects on cardiovascular indicators of mental effort. *Int J Psychophysiol* 2026;225:113382 | [10.1016/j.ijpsycho.2026.113382](https://doi.org/10.1016/j.ijpsycho.2026.113382) | 114 người trẻ, nhiệm vụ nhớ dãy số dễ và khó; phản ứng PEP, cung lượng tim, SBP, DBP, HR mạnh hơn ở nhiệm vụ khó; sức cản ngoại vi và HRV không khác | Nhiệm vụ nhận thức làm PEP đổi theo độ khó → PAT ở M2 có thể đổi một phần do PEP; không đo PAT | Abstract |
| **N31** | Han M et al. (13 tác giả). Feasibility and measurement stability of smartwatch-based cuffless blood pressure monitoring: a real-world prospective observational study. *Hypertens Res* 2023;46(4):922–931 | [10.1038/s41440-023-01215-z](https://doi.org/10.1038/s41440-023-01215-z) | 760 người dùng Samsung Galaxy Watch (PPG) tải dữ liệu 4 tuần sau hiệu chuẩn; 35.797 lần đo, trung bình 22 ± 4 ngày; sai số trước–sau hiệu chuẩn của SBP (chênh trung bình 7 ngày trước và sau hiệu chuẩn) 6,8 ± 5,6 mmHg, tăng khi SBP cao | Đánh giá ngoài đời thực nhiều tuần với thiết bị chỉ PPG; không có tham chiếu ghép cặp, không có PAT | Abstract; toàn văn đóng |
| **N32** | van Vliet M et al. (12 tác giả). Assessment of photoplethysmography-based blood pressure determinations during long-term and short-term remote cardiac monitoring: the RECAMO study. *Eur Heart J Digit Health* 2025;6(4):763–771 | [10.1093/ehjdh/ztaf027](https://doi.org/10.1093/ehjdh/ztaf027) | Thiết bị PPG cổ tay hiệu chuẩn bằng cuff, 150 bệnh nhân trong 28 ngày, so với ba lần đo tham chiếu tự động mỗi ngày; đánh giá theo khuyến cáo ESH (cần hiệu chuẩn lại, thức–ngủ ở 40 người có ABPM, áp suất thủy tĩnh). Sai số trung bình 28 ngày 3,84 (SD 4,46)/4,08 (3,97) mmHg; trước khi hiệu chuẩn lại ngày 28: 2,49 (3,10)/2,98 (3,48) | Đánh giá 4 tuần theo ESH với thiết bị chỉ PPG; không PAT, không thấy baseline chỉ hiệu chuẩn trong abstract | Abstract (toàn văn PMC12282382 chưa đọc) |
| **N33** | Walzel S et al. (5 tác giả). Long-term accuracy and stability of blood pressure measurements from a smartwatch: prospective validation study. *Digit Health* 2026;12:20552076261415923 | [10.1177/20552076261415923](https://doi.org/10.1177/20552076261415923) | 37 người, 28 ngày: hiệu chuẩn ngày 0, đo ghép cặp 27 ngày liên tiếp Galaxy Watch 5 với Omron M4; tiêu chí ISO/IEEE và phép thử hiệu chuẩn lại của ESH. MD SBP/DBP −0,34/0,62 mmHg, trôi trong chu kỳ hiệu chuẩn −0,19/1,02 mmHg; khi BP tham chiếu cách điểm hiệu chuẩn 10 mmHg, MD là 3,4 (SBP) và 5,1 mmHg (DBP) | Sai số tăng khi BP rời xa điểm hiệu chuẩn: cùng dạng "bám mốc" như N22, N24; chỉ PPG | Abstract |
| **N34** | Proença M et al. (7 tác giả). Long-term stability and blood pressure change tracking with a cuffless wearable device in hypertensive patients. *Blood Press* 2026;35(1):2707794 | [10.1080/08037051.2026.2707794](https://doi.org/10.1080/08037051.2026.2707794) | 30 bệnh nhân tăng huyết áp, 4 lần khám trong 6 tuần; thiết bị PPG đeo (CSEM) so với Microlife WatchBP Home A; chênh ΔSBP 0,2 ± 12,8, ΔDBP −0,1 ± 7,4 mmHg; không thấy trôi theo thời gian; cùng chiều với thay đổi lớn 83% (SBP), 86% (DBP) | Theo dõi ΔBP qua nhiều tuần (gần endpoint RQ1) nhưng chỉ PPG; SD của chênh ΔSBP lớn; abstract không có baseline zero-change | Abstract |
| **N35** | Ho MY et al. (4 tác giả). WF-PPG: a wrist-finger dual-channel dataset for studying the impact of contact pressure on PPG morphology. *Sci Data* 2025;12:200 | [10.1038/s41597-025-04453-7](https://doi.org/10.1038/s41597-025-04453-7) | Dataset PPG cổ tay ở nhiều mức áp lực tiếp xúc chỉnh chính xác, kèm PPG ngón tay đồng thời làm tham chiếu chất lượng, cùng áp lực tiếp xúc, ECG, BP và SpO2 | Có thể dùng để kiểm độ nhạy của đặc trưng PPG-only với áp lực tiếp xúc trước khi có dữ liệu người (RQ mục 4.F) | Abstract |
| **N36** | Pham HM et al. (6 tác giả). Reliable wrist PPG monitoring by mitigating poor skin sensor contact. *Sci Rep* 2025;15:45046 | [10.1038/s41598-025-31883-5](https://doi.org/10.1038/s41598-025-31883-5) | Tác giả nêu tiếp xúc da–cảm biến kém ngay cả khi ngồi yên làm méo hình thái PPG cổ tay (mất hoặc dịch đặc trưng sóng); đề xuất mô hình sinh chuyển sóng méo về hình thái lý tưởng; báo cải thiện các tác vụ HR, HRV, nhịp thở, BP | Xác nhận rủi ro: trong điều kiện ngồi yên như protocol, áp lực tiếp xúc vẫn làm đổi hình thái PPG cổ tay | Abstract |
| **N37** | McMurray JP et al. (6 tác giả). Multiwavelength photoplethysmography signal analysis as a function of varied wrist contact pressure. *Optical Diagnostics and Sensing: Toward Point-of-Care Diagnostics* (SPIE) 2023 | [10.1117/12.2649531](https://doi.org/10.1117/12.2649531) | Áp lực tiếp xúc ở mặt lòng cổ tay dọc động mạch quay; xanh lá, đỏ, hồng ngoại; biên độ AC, DC, perfusion index và hình thái khác biệt có ý nghĩa theo áp lực, khác nhau theo bước sóng | Bằng chứng ở cổ tay cho rủi ro áp lực tiếp xúc (RQ mục 4.F) | Abstract (hội nghị); toàn văn đóng |
| **N38** | Yang C et al. (5 tác giả). Mechanical contact conditions in wearable reflectance photoplethysmography: scoping review. *JMIR Mhealth Uhealth* 2026;14:e99333 | [10.2196/99333](https://doi.org/10.2196/99333) | Scoping review (PubMed, IEEE Xplore, Scopus, Web of Science đến 2026-06-01); 21 nghiên cứu; lực/áp lực tiếp xúc đi kèm thay đổi thành phần AC/DC, đặc trưng biên độ và hình thái; cách đo và báo cáo áp lực rất không đồng nhất | Nguồn tổng hợp cho rủi ro áp lực tiếp xúc; gợi ý ghi lại điều kiện tiếp xúc ở mỗi phiên | Abstract |
| **N39** | Bustamante-Rodríguez JC et al. (4 tác giả). Wearable, cuffless, and portable devices for blood pressure monitoring (2015–2025): a scoping review of technologies, calibration, clinical validation, and regulatory frameworks. *Front Digit Health* 2026;8:1870156 | [10.3389/fdgth.2026.1870156](https://doi.org/10.3389/fdgth.2026.1870156) | Scoping review theo PRISMA-ScR, tìm PubMed/MEDLINE, Scopus, Web of Science, Embase; 63 nguồn (49 nghiên cứu gốc trên người, 33 về thiết bị không cuff). Theo tác giả, khoảng trống còn lại: độ ổn định sau hiệu chuẩn, điều kiện động, khi ngủ, điều trị, loạn nhịp, nhóm đặc biệt | Tổng quan gần nhất xác nhận độ ổn định sau hiệu chuẩn còn là khoảng trống; cần xem bảng trích xuất của bài để tìm nghiên cứu ECG + PPG nhiều phiên | Abstract và các đoạn về phạm vi, số nguồn (PMC13506816) |
| **N40** | Cisnal A, Podder I, Grossmann L, … (7 tác giả). Towards trustworthy AI-driven cuffless blood pressure monitoring. *NPJ Digit Med* 2026;9 | [10.1038/s41746-026-02898-7](https://doi.org/10.1038/s41746-026-02898-7) | Systematic review; phân loại theo tín hiệu thay thế, kiểu mô hình và chiến lược hiệu chuẩn; mẫu báo cáo kiểu "model card" (BP-Card). Rào cản theo tác giả: độ thực tế của protocol, trôi hiệu chuẩn, đa dạng quần thể. Khuyến nghị luôn báo baseline model (với cách có hiệu chuẩn: BP hiệu chuẩn của từng người), dẫn các phân tích Aurora | Khung báo cáo có thể dùng cho bài của nhóm; cùng nhóm tác giả N16, N19 | Abstract và các đoạn về baseline (PMC13669345) |
| **N41** | Torad MA et al. (6 tác giả). ESP32-S3-based multimodal wearable for remote vital-sign acquisition with ECG-to-PPG pulse-arrival-time tracking and functional cloud triage: an engineering proof of concept. *Sensors* 2026;26(19):6047 | [10.3390/s26196047](https://doi.org/10.3390/s26196047) | ESP32-S3 với AD8232 (ECG), MAX30102 (PPG/SpO2), MAX30205 (nhiệt độ); FreeRTOS, ECG/PPG danh định 100 Hz; khoảng sóng R → chân sóng PPG được gọi đúng là PAT; chỉ có thử trên bàn và kịch bản tổng hợp, chưa có dữ liệu người | Củng cố mục 5: ráp ESP32-S3 với module ECG + PPG để đo PAT không phải điểm mới. Bài lấy mẫu 100 Hz, thấp hơn thiết kế của nhóm (ECG 512, PPG 200 sps) | Abstract |
| **N42** | Kaetheeswaran J et al. (5 tác giả). HEART-Watch: a multimodal physiological dataset from a Google Pixel Watch across different physical states. *PLOS Digit Health* 2026;5(8):e0001647 | [10.1371/journal.pdig.0001647](https://doi.org/10.1371/journal.pdig.0001647) | ECG, PPG, gia tốc từ Pixel Watch ở 40 người khỏe khi ngồi, đứng, đi; ECG ngực tham chiếu; BP cánh tay đo ngắt quãng | Dataset đồng hồ ECG + PPG công khai, cùng nhóm tác giả N10; một buổi, không có cấu trúc nhiều phiên | Abstract |

S3 (Aurora, tổng kết) và S4 (Mieloszyk 2022, dataset Aurora-BP: 1.125 người, đồng hồ
PPG + ECG, tonometry, 24 giờ) ở [tổng quan 2026-10-14](literature_update_2026-10-14.md)
vẫn là nguồn lớn nhất về ECG + PPG cổ tay qua nhiều thời điểm. S4 chỉ dùng abstract theo
quyết định ngày 2026-10-29 (toàn văn có phí, không lấy qua thư viện).

### 3.1. Các bài dùng dataset Aurora-BP (chủ đề T6)

Theo abstract (hoặc toàn văn ở N16), các bài 2022–2026 sau dùng dữ liệu Aurora-BP:

- **So PAT hoặc đặc trưng với baseline, hoặc đánh giá nhiều ngày:** N19 (mô hình PAT không vượt
  baseline cho SBP), N20 (có bảng baseline theo N8), N21 (Aurora cộng dữ liệu đồng hồ 30+ ngày),
  S7 (khoảng dự đoán conformal, 483 người).
- **Chỉ PPG cổ tay:** N16 (chọn đặc trưng, PPG + nhân khẩu học), N12 (chất lượng PPG cổ tay),
  Dendorfer A, Charlton PH 2025, ECSA ([10.3390/ecsa-12-26556](https://doi.org/10.3390/ecsa-12-26556):
  năm lớp hình thái sóng PPG cổ tay ở 686 người), Liu D et al. 2026, bioRxiv
  ([10.64898/2026.08.19.745616](https://doi.org/10.64898/2026.08.19.745616): PPG thái dương so với
  cổ tay theo tuổi).
- **Phân loại, sàng lọc hoặc mục đích khác:** Gon GK et al. 2024, JMIR Cardio
  ([10.2196/60238](https://doi.org/10.2196/60238): dự đoán tăng huyết áp bằng suy luận nhân quả,
  ECG + PPG); Huang ZX et al. 2025, JBHI ([10.1109/jbhi.2025.3640660](https://doi.org/10.1109/jbhi.2025.3640660):
  BpBLS, CAS-BP và Aurora-BP); Hong J et al. 2026, Eur Heart J Digit Health
  ([10.1093/ehjdh/ztag131](https://doi.org/10.1093/ehjdh/ztag131): sàng lọc tăng huyết áp theo khác
  biệt thức–ngủ, 180 người); van den Brink WJ et al. 2026 (abstract hội nghị,
  [10.1093/ehjdh/ztaf143.155](https://doi.org/10.1093/ehjdh/ztaf143.155): biến thiên BP và hội chứng
  chuyển hóa); Msokar S et al. 2026, Preprints.org
  ([10.20944/preprints202610.1859.v1](https://doi.org/10.20944/preprints202610.1859.v1): phân loại
  nhóm BP qua nhiều dataset); Podder I et al. 2025, TechRxiv
  ([10.36227/techrxiv.175296041.12589238/v1](https://doi.org/10.36227/techrxiv.175296041.12589238/v1):
  tiền huấn luyện trên Aurora cho ΔSBP ở người tổn thương tủy sống); Aston PJ 2024, CinC
  ([10.22489/cinc.2024.038](https://doi.org/10.22489/cinc.2024.038): màu da và độ chính xác phân
  loại).

**Kết luận cho T6 (trong phạm vi abstract đã đọc):** chỉ N19 so mô hình dựa trên PAT với
baseline; chưa thấy bài nào trên Aurora-BP so ghép cặp PPG-only với PPG + PAT so với baseline chỉ
hiệu chuẩn ở ngày hôm sau. Chưa loại trừ được S4 (chỉ dùng abstract theo quyết định ngày
2026-10-29), N19 và N20 (chưa đọc toàn văn).

**Truy cập dữ liệu:** Aurora-BP có bản ghi mở trên Zenodo
([10.5281/zenodo.19099165](https://doi.org/10.5281/zenodo.19099165), bản ghi tạo 2026-03-18), kèm
tệp Data Use Agreement; tổng dung lượng khoảng 6,7 GB (nhánh oscillometric 5,0 GB, nghe tim
1,6 GB, `features.tsv` 30 MB). Các điểm chính của Data Use Agreement theo mô tả trên Zenodo: không
phân phối lại; **không ghép với nguồn dữ liệu khác**; không định danh hay liên hệ người tham gia;
lưu trữ có kiểm soát truy cập; được công bố kết quả nếu không chứa thông tin mật của Microsoft hay
thông tin cá nhân; phải trích dẫn Aurora-BP Study. N16 dùng dữ liệu theo thỏa thuận chuyển giao
riêng giữa Microsoft và ETH. Chưa đọc toàn văn tệp Data Use Agreement.

### 3.2. Bài giữ lại sau sàng lọc nhưng không thành dòng riêng

Đã đọc abstract; liên quan nhưng không làm đổi khoảng trống hơn các dòng N ở trên. DOI kiểm
qua OpenAlex ngày 2026-10-29.

- **T4/T5, thiết bị chỉ PPG qua nhiều ngày:** Mekonnen BK et al. 2024, *Sci Rep*
  ([10.1038/s41598-024-75583-y](https://doi.org/10.1038/s41598-024-75583-y): PPG cá nhân hóa,
  kiểm tới 30+ ngày ở 15 người); Wang CF et al. 2023, *Biosensors*
  ([10.3390/bios13030321](https://doi.org/10.3390/bios13030321): PPG cánh tay trên, hiệu chuẩn một
  lần, 4 tuần); Lee Y et al. 2025, *Clin Hypertens*
  ([10.5646/ch.2025.31.e21](https://doi.org/10.5646/ch.2025.31.e21): Galaxy Watch 6, 896 người,
  chênh trước–sau hiệu chuẩn 4,64 ± 4,73 mmHg SBP); Lee Y et al. 2023, EMBC
  ([10.1109/embc40787.2023.10340129](https://doi.org/10.1109/embc40787.2023.10340129)); Lee J et
  al. 2026, preprint JMIR ([10.2196/preprints.106980](https://doi.org/10.2196/preprints.106980):
  1.714 người dùng Galaxy Watch, 2021–2023); Wu W et al. 2025, BIBM
  ([10.1109/bibm66473.2025.11356894](https://doi.org/10.1109/bibm66473.2025.11356894): PPG 24 giờ,
  243 người, vẫn trôi hiệu chuẩn); Hussein R et al. 2025, EMBC
  ([10.1109/embc58623.2025.11254768](https://doi.org/10.1109/embc58623.2025.11254768): tần suất hiệu
  chuẩn PPG); López-Jiménez FA et al. 2025, *J Cardiovasc Transl Res*
  ([10.1007/s12265-024-10589-5](https://doi.org/10.1007/s12265-024-10589-5): thiết bị đa thông số
  đeo ngực, kiểm giá trị tham chiếu 4 tuần).
- **T3, mô hình hiệu chuẩn:** Barvík D et al. 2022, *IEEE Rev Biomed Eng*
  ([10.1109/rbme.2021.3109643](https://doi.org/10.1109/rbme.2021.3109643): tổng quan mô hình hiệu
  chuẩn PTT); Mousavi AS et al. 2024, *IEEE TBME*
  ([10.1109/tbme.2023.3307658](https://doi.org/10.1109/tbme.2023.3307658): hiệu chuẩn một điểm dựa
  trên mô hình vật lý, 22 người); Seo Y et al. 2023, *Biomed Eng Lett*
  ([10.1007/s13534-023-00271-1](https://doi.org/10.1007/s13534-023-00271-1): hiệu chuẩn lại bằng
  cuff cổ tay); Tamura T et al. 2023, *Health Technol*
  ([10.1007/s12553-023-00726-6](https://doi.org/10.1007/s12553-023-00726-6): đề xuất tiêu chí ổn
  định dài hạn); He S, Bolić M 2024, *Sci Rep*
  ([10.1038/s41598-024-77171-6](https://doi.org/10.1038/s41598-024-77171-6): chỉ số đo khả năng bám
  xu hướng).
- **T2:** Park S et al. 2023, *Biomed Eng Lett*
  ([10.1007/s13534-023-00284-w](https://doi.org/10.1007/s13534-023-00284-w): VitalDB, so bộ đặc
  trưng PAT và hình thái PPG ở người có và không đái tháo đường); Yang Y et al. 2026, *Physiol Meas*
  ([10.1088/1361-6579/aeab62](https://doi.org/10.1088/1361-6579/aeab62): 28 phiên ở 9 người, PTT/PIR
  theo cách gọi của bài và tonometry thái dương khi bóp tay); Yi MK et al. 2026, *Physiol Meas*
  ([10.1088/1361-6579/aeb063](https://doi.org/10.1088/1361-6579/aeb063): khung đánh giá đặc trưng
  PPG có tính tới điều kiện đo).
- **T7:** Nawar A et al. 2024, EMBC
  ([10.1109/embc53108.2024.10781523](https://doi.org/10.1109/embc53108.2024.10781523): stress nói
  trước đám đông, thay đổi PAT tương quan với ΔMAP r = −0,58, 35 người phần lớn sau nhồi máu cơ
  tim); Rojano-Hernández E et al. 2025, EMBC
  ([10.1109/embc58623.2025.11251854](https://doi.org/10.1109/embc58623.2025.11251854): ước lượng PEP
  bằng impedance plethysmography tay–tay).
- **T8:** Lambert Cause J et al. 2024, *Sensors*
  ([10.3390/s24092692](https://doi.org/10.3390/s24092692): lực tiếp xúc và PPG năm bước sóng, 11
  người); Pilt K, Reiu A 2024, *Med Biol Eng Comput*
  ([10.1007/s11517-023-02992-y](https://doi.org/10.1007/s11517-023-02992-y): áp suất xuyên thành và
  chỉ số độ cứng từ PPG ngón tay); Scardulla F et al. 2025, *Sensors*
  ([10.3390/s25144477](https://doi.org/10.3390/s25144477): áp lực tiếp xúc 20/60/75 mmHg và độ chính
  xác HR).
- **Định vị:** Stergiou GS et al. 2022, *J Hypertens*
  ([10.1097/hjh.0000000000003224](https://doi.org/10.1097/hjh.0000000000003224): tuyên bố ESH 2022);
  Mukkamala R et al. 2022, *Annu Rev Biomed Eng*
  ([10.1146/annurev-bioeng-110220-014644](https://doi.org/10.1146/annurev-bioeng-110220-014644));
  Parati G et al. 2026, *Eur J Prev Cardiol*
  ([10.1093/eurjpc/zwag058](https://doi.org/10.1093/eurjpc/zwag058): tuyên bố khoa học 2026).

## 4. So sánh với thiết kế của nhóm

| Đặc điểm của RQ1 | Đã có trong nguồn đã đọc |
| --- | --- |
| Baseline zero-change hoặc chỉ hiệu chuẩn, đánh giá theo người | N1 (zero-change, LOSO lồng), N2 (baseline không đổi), N18 (baseline naïve = trung bình cuff ban đầu, sau 1 năm), N19 (baseline models, abstract), S3/S4 (baseline "khó") |
| So PPG với PAT trên cùng người | N1 (từng bộ riêng), N2 (PPG + PAT), N18 (mô hình PAT, PAT + đặc trưng PPG, chỉ PPG; đầu ra khác nhau), N25, N26 (PAT theo từng nghiệm pháp) |
| Nghiệm pháp tạo ΔBP không dùng thuốc | N2, N3, N4, N7, N18 (thở chậm, tính nhẩm, ngâm lạnh; thêm nitroglycerin), N25, N26, N28 |
| PPG và ECG cùng ở cổ tay | N5 (ECG cổ tay–ngón tay bên kia, SCG ở ngực), N6, S4/N19/N20 (Aurora), N10, N42 (dataset), N41 (chỉ thử trên bàn) |
| Đánh giá ở phiên khác ngày sau hiệu chuẩn | N4 (ngày hôm sau, nhóm nhỏ), N6 (khoảng 1 tháng), N7 (11 người ngày hôm sau, chỉ PPG), N18 (1 năm), N21 (30+ ngày, chỉ PPG), N23, N31–N34 (1–6 tuần, chỉ PPG), S3/S4 (ngày hôm sau) |
| Đầu ra thiết bị bám gần mốc hiệu chuẩn | N22 (PAT, 24 giờ), N23, N24, N33 (PPG); N8 tổng hợp |
| **Gộp: thiết bị chỉ ở cổ tay, PPG-only so với PPG + PAT ghép cặp theo người, cùng thuật toán, ở phiên vài ngày đến 4 tuần, so với zero-change, có nghiệm pháp** | **Không thấy** trong các nguồn đã mở. Gần nhất là N18 (nhiều phiên, có baseline naïve, nhưng không ở cổ tay, hiệu chuẩn nhiều điểm theo từng người, cách 1 năm, không có ablation ghép cặp cho cùng đầu ra). Chưa loại trừ được: S4 vì chỉ có abstract (quyết định ngày 2026-10-29); N6 vì toàn văn bị chặn khi tải (mục 2.2); N19, N20 vì chưa đọc toàn văn |

## 5. Đánh giá mức độ mới

### 5.1. Khoảng trống của RQ1 sau lần tra 2

**Phải sửa so với lần 1.** Lần 1 viết rằng so sánh PPG với PAT có baseline chỉ ở một buổi đo.
N18 cho thấy điều đó không còn đúng: Yavarimanesh et al. (2022) đã đánh giá mô hình có PAT và
mô hình chỉ đặc trưng PPG ở phiên cách 1 năm, so với baseline chỉ dùng cuff hiệu chuẩn, có thở
chậm, tính nhẩm và ngâm lạnh. Trên dữ liệu cổ tay, N19 (abstract) báo mô hình dựa trên PAT không
vượt baseline cho SBP khi theo dõi lưu động. Vì vậy, các thành phần sau, **kể cả khi gộp một phần**,
đều không phải điểm mới: nhiều phiên; baseline chỉ hiệu chuẩn; nghiệm pháp; so mô hình PAT với mô
hình đặc trưng PPG.

**Có thể còn là đóng góp** (chỉ trong phạm vi các nguồn đã mở, mục 2.2): phép so sánh ghép cặp,
đăng ký trước, PPG-only với PPG + PAT với các điều kiện sau cùng lúc:

1. Thiết bị chỉ ở cổ tay: PPG cổ tay và ECG đạo trình I giữa hai cổ tay.
2. Phiên cách nhau vài ngày đến 4 tuần.
3. Hiệu chuẩn chỉ bằng offset từ M0 phiên 1, hệ số mức quần thể học bằng LOSO lồng, khác N18
   (hệ số riêng từng người từ cả bộ nghiệm pháp).
4. Cùng thuật toán, cùng tập lần đo, cùng đầu ra cho hai mô hình.
5. Luôn so với zero-change, CI bootstrap theo người và mức δ khóa trước.

**Không được viết** "đầu tiên" hay "chưa có nghiên cứu nào". Cách viết đúng: "Trong các nguồn đã
tra (PubMed, Europe PMC, OpenAlex, 2022–2026, tra ngày 2026-10-29; chưa tra IEEE Xplore, Scopus,
Web of Science; S4 chỉ đọc abstract; N6 chưa đọc được toàn văn), chưa thấy nghiên cứu so sánh
ghép cặp PPG-only với PPG + PAT trên cùng thiết bị cổ tay ở các phiên khác ngày so với
zero-change. Yavarimanesh et al. (2022) đã so mô hình có PAT với mô hình đặc trưng PPG qua hai
phiên cách nhau một năm, có baseline chỉ dùng cuff hiệu chuẩn, nhưng với PPG ở tai, ngón tay,
ngón chân và hiệu chuẩn nhiều điểm theo từng người." Theo quyết định ngày 2026-10-29 bỏ qua toàn
văn S4, bài báo phải nêu giới hạn: khoảng trống chưa được kiểm với toàn văn S4.

**Kết quả âm tính vẫn là đóng góp** theo khung của N8, và khả năng này cao hơn sau lần 2: ở N18,
mô hình chỉ PPG cho DBP kém hơn naïve sau 1 năm, mô hình PAT ngón tay chưa vượt naïve có ý nghĩa;
ở N19, mô hình PAT trên dữ liệu cổ tay không vượt baseline; N22–N24, N33 cho thấy đầu ra của bốn
thiết bị thương mại được đánh giá bám gần mốc hiệu chuẩn. Suy luận của trợ lý (không nguồn nào nói trực tiếp): N18 quy kết
quả kém của PAT tai/ngón tay cho co cơ trơn mạch, mà đường tới cổ tay cũng qua động mạch cơ, nên
PAT cổ tay có thể chịu cùng vấn đề.

**Điểm yếu so với các bài gần nhất:** cỡ mẫu nhỏ hơn nhiều so với N6 (3.077) và S4 (1.125); N18
ước tính cần 31 người cho một so sánh tương tự (mô hình ngón tay so với naïve sau 1 năm), cao
hơn mục tiêu ≥ 15 người của RQ1. Cuff ngắt quãng, trong khi N7 và N4 dùng tham chiếu liên tục;
người trẻ khỏe, dải ΔBP hẹp. Phản biện sẽ hỏi vì sao không dùng Aurora-BP, nay đã có bản mở trên
Zenodo kèm Data Use Agreement (mục 3.1).

### 5.2. Ảnh hưởng tới rủi ro của RQ1 (để nhóm cân nhắc, không tự sửa RQ)

Ghi chú 2026-10-30: protocol đã bỏ M3 (ngâm chân nước lạnh) và M4 (đạp xe) ngày 2026-10-29, nên các
ý về M3, M4 dưới đây chỉ còn để tham khảo nếu sau này xin sửa đổi thêm nghiệm pháp. Các ý về PEP, áp
lực tiếp xúc và cỡ mẫu đã đưa vào RQ mục 4.F–4.G ngày 2026-10-30.

- **PEP ở M2 (và M4 trước khi bỏ):** N11 (stress tinh thần giảm PEP 16%, gắng sức giảm một nửa), N30 (PEP đổi theo độ
  khó nhiệm vụ), N25 (từ nền sang nhiệm vụ tinh thần, tương quan giữa thay đổi PAT và SBP không có ý nghĩa thống kê)
  ủng hộ rủi ro đã ghi ở RQ mục 4.F và việc báo kết quả theo từng nghiệm pháp.
- **Ngâm lạnh (M3, đã bỏ):** N29 (PEP không đổi khi đau do lạnh, PTT giảm) và N18 (co cơ trơn mạch)
  gợi ý rằng khi ngâm lạnh, thay đổi PAT chủ yếu đến từ phần mạch, không từ PEP; cỡ mẫu nhỏ.
- **Áp lực tiếp xúc:** N8, N13, N35–N38 và N18 (khuyến nghị giữ nguyên vị trí đặt cảm biến) củng cố
  rủi ro ở RQ mục 4.F. WF-PPG (N35) có thể dùng để kiểm độ nhạy của đặc trưng PPG trước khi thu dữ
  liệu người.
- **Tư thế tay:** N12 cho thấy độ cao cảm biến so với tim đổi chất lượng PPG cổ tay → cố định tư thế
  tay ở mọi phiên.
- **Cỡ mẫu:** con số 31 người của N18 nên được đưa vào mô phỏng độ nhạy ở RQ mục 4.E.

### 5.3. Đoạn cần sửa trong ma trận và RQ

Lần tra không sửa ma trận và RQ, chỉ ghi lại danh sách dưới đây để nhóm sửa. Ngày 2026-10-30 đã sửa
theo danh sách này:
- ma trận: phần đầu, mục 2.1, khoảng trống 1–2, đóng góp 1;
- RQ: mục 1, 4.F và 4.G.

Danh sách giữ làm nhật ký. Khoảng trống 4 (RQ3) không đổi.

- **Ma trận, phần đầu** (dòng "Nguồn bổ sung … (N1–N17)") → N1–N42.
- **Ma trận mục 2.1:**
  - Thêm N18, N19 (và N22–N24 cho baseline chỉ hiệu chuẩn) vào "Bằng chứng chính" của RQ1.
  - Sửa hàng "Mới tìm, chưa đọc": N5, N7, N8, N16 đã đọc toàn văn; N9, N11–N13 đã đọc abstract.
  - Sửa câu "Chưa có tìm kiếm có hệ thống trên PubMed/IEEE Xplore…" thành: đã tra PubMed, Europe PMC,
    OpenAlex ngày 2026-10-29; IEEE Xplore, Scopus chưa tra.
- **Ma trận mục 4, khoảng trống 1:**
  - Sau câu "Cả hai nghiên cứu đó chỉ đánh giá **trong một buổi** …" thêm N18 (nhiều phiên, có baseline
    naïve, không ở cổ tay).
  - Câu "Các nghiên cứu nhiều ngày trên thiết bị cổ tay có quy mô lớn … chưa cho thấy phép so sánh
    ghép cặp …" cần thêm N19 (PAT không vượt baseline trên Aurora) và việc N6 có so với baseline (theo N8).
  - Đoạn "**Khoảng trống, ở phạm vi hẹp:** …" thu hẹp theo năm điều kiện ở mục 5.1.
  - Câu "phải kiểm lại sau khi đọc toàn văn S4 và N6" đã đổi thành "… toàn văn N6", kèm ghi chú S4
    chỉ dùng abstract (sửa ngày 2026-10-29 theo quyết định bỏ qua S4). Cân nhắc thêm N19, N20.
- **Ma trận mục 4, khoảng trống 2:**
  - Câu "Đa số nghiên cứu gần nhất (N1, N2, N7) chỉ đánh giá trong một buổi" chưa chính xác với N7
    (11 người đo lại ngày hôm sau).
  - Thêm N18 (1 năm), N21, N31–N34 (nhiều tuần, chỉ PPG) và N22–N24, N33 (đầu ra bám mốc hiệu chuẩn).
- **Ma trận mục 4, khoảng trống 4 (RQ3):** lần 2 không tra chủ đề SQI + độ bất định, nên câu "chưa
  tìm kiếm cho giai đoạn 2022–2026" vẫn đúng.
- **RQ mục 1, đoạn "Các nghiên cứu gần nhất (v0.4)":**
  - Câu "So sánh trực tiếp PPG với PAT có baseline zero-change … chỉ ở **một buổi đo**" không còn đúng
    sau N18.
  - Thêm N18, N19. Câu về S4 và N6 trong đoạn này đã theo quyết định ngày 2026-10-29 (S4 chỉ dùng
    abstract, kiểm lại sau khi đọc toàn văn N6).
- **RQ mục 4.F và 4.G:** cân nhắc thêm N11, N25, N29, N30 (PEP), N35–N38 (áp lực tiếp xúc) và con số
  31 người của N18 (mục 5.2).

## 6. Việc cần làm

### 6.1. Cần lấy toàn văn

Toàn văn đóng hoặc bị chặn khi tra ngày 2026-10-29. Thứ tự theo mức ảnh hưởng tới khoảng trống
của RQ1.

**S4 không nằm trong danh sách:** theo quyết định ngày 2026-10-29, S4 (Mieloszyk 2022,
[10.1109/jbhi.2022.3153259](https://doi.org/10.1109/jbhi.2022.3153259)) bỏ qua, không lấy qua thư
viện, chỉ dùng abstract. Khoảng trống của RQ1 chưa được kiểm với toàn văn S4, và bài báo phải nêu
giới hạn này.

1. **N6** – Liu ZD et al. *IEEE J Biomed Health Inform* 2023;27(9):4216–4227,
   [10.1109/jbhi.2023.3278168](https://doi.org/10.1109/jbhi.2023.3278168).
   - Truy cập mở (CC BY 4.0), **không cần thư viện**.
   - Tải tự động bị chặn ở IEEE và ở CityU Scholars (mục 2.2), nên cần một người mở bằng trình
     duyệt thường rồi lưu PDF.
   - Cần trả lời:
     - có so PPG-only với PPG + PAT (bài có thể gọi là PTT) trên cùng người không;
     - Bảng IV: baseline gồm gì, có phải chỉ hiệu chuẩn (zero-change) không;
     - khoảng cách từ hiệu chuẩn tới các lần đo trong khoảng 1 tháng;
     - có chia train/test theo người và theo thời gian không;
     - cách chọn tham số α (N8 nêu nghi vấn).
2. **N19** – Cisnal A et al. *Proc IEEE CBMS* 2025,
   [10.1109/cbms65348.2025.00046](https://doi.org/10.1109/cbms65348.2025.00046): định nghĩa baseline
   models, có mô hình PPG-only không, cách chia dữ liệu.
3. **N20** – Liu ZD et al. *IEEE JBHI* 2024,
   [10.1109/jbhi.2024.3395445](https://doi.org/10.1109/jbhi.2024.3395445): Bảng IV, V (baseline,
   nhiều phương pháp).
4. **N28** – Xie C et al. EMBC 2023,
   [10.1109/embc40787.2023.10340548](https://doi.org/10.1109/embc40787.2023.10340548): vị trí PPG,
   can thiệp, cách hiệu chuẩn.
5. **N31** – Han M et al. *Hypertens Res* 2023
   ([10.1038/s41440-023-01215-z](https://doi.org/10.1038/s41440-023-01215-z)) và **N37** – McMurray JP
   et al. SPIE 2023 ([10.1117/12.2649531](https://doi.org/10.1117/12.2649531)).
6. **Bài chưa sàng lọc được vì không lấy được abstract** (OpenAlex và Europe PMC không có abstract;
   Semantic Scholar trả 429):
   - He J et al. 2022. A new approach for daily life blood-pressure estimation using smart watch.
     *Biomed Signal Process Control* 75:103616,
     [10.1016/j.bspc.2022.103616](https://doi.org/10.1016/j.bspc.2022.103616). Tiêu đề gợi ý đồng hồ
     đo hằng ngày; có thể liên quan T1/T4.
   - Liu J et al. 2024. *Appl Soft Comput* 167:112390,
     [10.1016/j.asoc.2024.112390](https://doi.org/10.1016/j.asoc.2024.112390) (trích dẫn N1, N6, S4).
   - Cao X et al. 2026. *Sens Actuators A Phys* 412:118546,
     [10.1016/j.sna.2026.118546](https://doi.org/10.1016/j.sna.2026.118546) (tiếp xúc da–cảm biến ở cổ
     tay, T8).
   - Li Y et al. 2026, SSRN preprint,
     [10.2139/ssrn.7436498](https://doi.org/10.2139/ssrn.7436498) (ước lượng xu hướng BP).

### 6.2. Việc khác

1. **Trước Tuần 8:** đọc toàn văn N6 (mục 6.1). Nếu N6 đã so ghép cặp PPG-only với PPG + PAT qua
   nhiều ngày, có baseline chỉ hiệu chuẩn, phải viết lại khoảng trống ở mục 5.1. S4 bỏ qua theo
   quyết định ngày 2026-10-29: khoảng trống chưa được kiểm với toàn văn S4, và bài báo phải nêu giới
   hạn này.
2. Sửa ma trận mục 2.1, 4 và RQ mục 1 theo mục 5.3 (nhóm quyết định; sửa RQ cần được duyệt).
3. **Aurora-BP:** đọc toàn văn tệp Data Use Agreement trên Zenodo trước khi tải. Điều khoản "không
   ghép với nguồn dữ liệu khác" cần được hiểu đúng trước khi dùng Aurora làm dữ liệu thứ hai. Quyết
   định trước khi chọn tạp chí ở Tuần 8.
4. Đọc toàn văn trước khi trích số: N23 (đã tải), N32 (PMC12282382), N22 (phần còn lại), N39 (bảng
   trích xuất), N11, N12, N13, N29 (truy cập mở).
5. Chưa tra: IEEE Xplore và Scopus cho cùng chủ đề T1–T8. Nên chạy cùng chuỗi truy vấn, ghi số bản ghi
   như mục 2.2.
6. Nhờ một người trong nhóm sàng lọc lại ngẫu nhiên một phần bản ghi bị loại (ví dụ 100 bản ghi)
   để ước lượng tỷ lệ bỏ sót của trợ lý AI.
7. Đối chiếu nguyên văn mọi con số trong bảng 3 trước khi trích trong bản thảo.
