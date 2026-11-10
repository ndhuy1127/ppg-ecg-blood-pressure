# Kế hoạch phân tích thống kê (SAP) v1 cho RQ1

> **Trạng thái: đề xuất ngày 2026-11-07, chờ duyệt.**
>
> - **Nguồn đã chốt hay đề xuất trước đó:** [RQ v0.4](../research_questions_v0.1.md) mục 4,
>   [protocol v0.3](protocol_outline_v0.2.md) mục 4.1, 6.4–6.5, 7.3, 9, 10;
>   [kịch bản bài báo](../paper_scenarios_v0.1.md). Chỗ nào SAP khác các file đó đều ghi rõ
>   "đề xuất đổi".
> - **Khi nào khóa:** bằng một commit có ngày, **trước pilot**. Sau pilot chỉ được điền những giá
>   trị ghi "chốt sau pilot" (δ, số người, phân bổ phiên), theo đúng quy tắc ở đây, trước khi thu
>   dữ liệu chính.
> - **Những gì không được dùng:** không dùng kết quả RQ1, cũng không dùng sai số mô hình trên
>   pilot hay dữ liệu chính, để chốt bất kỳ mục nào.
> - **Dữ liệu:** SAP này không phụ thuộc dữ liệu người nào. Mô phỏng ở mục 9 chỉ dùng giả định.
> - **RQ2b và RQ3:** dùng lại các quy tắc ở đây; RQ3 là thăm dò.

## 1. Câu hỏi và nguyên tắc

- **RQ1:** ở người khỏe mạnh 18–35 tuổi không có trong dữ liệu huấn luyện, sau khi hiệu chuẩn
  bằng trung bình M0 của phiên 1, thêm PAT vào mô hình đặc trưng PPG có làm giảm sai số dự đoán
  ΔSBP và ΔDBP ở phiên 2–3 so với chỉ dùng PPG hay không, và giảm bao nhiêu (RQ mục 4).
- SBP và DBP phân tích riêng. Một lần cuff là một nhãn. Đơn vị suy luận là người. Bootstrap lấy
  mẫu lại theo người.
- PAT = PEP + PTT (cách viết gọn, mốc R), không gọi PAT là PTT.
- **LOSO lồng** (protocol 9.1):
  - vòng ngoài chạy đúng một lần, sau commit khóa mọi lựa chọn;
  - người làm pilot không vào vòng ngoài.

## 2. Dữ liệu và tập phân tích

- **Lần cuff hợp lệ:** có SBP và DBP từ máy cuff, không bị dừng vì lỗi máy (protocol 6.4, mục
  "Số lần bơm"). Lần đo lại thay cho lần hỏng, không thêm nhãn.
- **Người đạt chuẩn** (định nghĩa của [kịch bản bài báo](../paper_scenarios_v0.1.md), chép lại
  để khóa):
  - đã qua sàng lọc;
  - có phiên 1 đạt và ít nhất một phiên sau đạt. Một phiên đạt khi có ≥ 2 lần cuff hợp lệ tính
    được PAT và đặc trưng PPG ([SQI v1](sqi_specification_v1.md) mục 4);
  - phiên sau có cờ `led_readjusted` không được tính là phiên đạt;
  - người làm pilot không được tính.
- **Tập phân tích chính:** mọi lần cuff hợp lệ ở phiên ≥ 2 (M0, M1, M2) của người đạt chuẩn,
  tính được cả PAT lẫn đặc trưng PPG. Không lọc theo SQI. Phiên `led_readjusted` không thuộc tập
  này.
- **Báo kèm:** số người tuyển, sàng lọc, đạt chuẩn, bỏ cuộc và lý do; số lần cuff theo người,
  phiên, nghiệm pháp; tỷ lệ lần đo mất ECG theo người.

## 3. Estimand và endpoint

- **Estimand chính** (RQ mục 4.A), riêng cho ΔSBP và ΔDBP:
  - θ = E_s[d_s], với d_s = MAE_s(PPG+PAT) − MAE_s(PPG-only);
  - MAE_s là trung bình |sai số| trên các lần cuff của người s trong tập phân tích chính;
  - mỗi lần cuff có trọng số như nhau trong một người, mỗi người có trọng số như nhau khi tính θ.
- **Estimand đồng chính:** θ⁰ = E_s[d⁰_s], với d⁰_s = MAE_s(PPG+PAT) − MAE_s(zero-change).
- **Endpoint phụ (không xác nhận), báo với cùng cách tính:**
  1. chỉ các lần cuff M0 ở phiên ≥ 2;
  2. theo từng nghiệm pháp;
  3. PPG-only trên mọi lần cuff có PPG, kể cả lần mất ECG;
  4. PAT-only và ablation PPG + PAT + HR/HRV từ ECG;
  5. tập đã lọc SQI ([SQI v1](sqi_specification_v1.md) mục 5);
  6. có cả các phiên `led_readjusted`;
  7. bỏ các lần cuff mang cờ dừng an toàn (protocol 10);
  8. RQ2b: cùng phiên so với khác phiên (RQ mục 5.B);
  9. Pearson r giữa ΔBP tham chiếu và dự đoán; tỷ lệ |sai số| ≤ 5 và ≤ 10 mmHg (chỉ mô tả).

## 4. Hiệu chuẩn và đặc trưng

- BP₀ của mỗi người là trung bình các lần cuff M0 hợp lệ ở phiên 1. ΔBP của một lần cuff bằng
  giá trị cuff trừ BP₀.
- **Đặc trưng nền:** trung vị của từng đặc trưng trên các cửa sổ M0 phiên 1. Mô hình nhận Δ
  đặc trưng, tức giá trị ở lần cuff trừ giá trị nền.
- **Bộ đặc trưng** (RQ mục 4.B), khóa trên pilot, mỗi mô hình một tập cố định:
  - PPG-only: thời gian lên, độ rộng tại 50 % biên độ, biên độ xung, HR từ PPG;
  - PPG + PAT: thêm ΔPAT;
  - PAT-only: Δ(1/PAT²);
  - ablation: thêm HR và HRV từ ECG.

  Cửa sổ, phương pháp mốc R và chân sóng, quy tắc ghép nhịp cũng khóa trên pilot.
- **Thuật toán (đề xuất, chờ duyệt):** Ridge trên Δ đặc trưng, α = 1 cố định, không hệ số chặn.
  Hai mô hình của phép so sánh chính dùng cùng thuật toán và cùng α. Vì α cố định nên bỏ vòng
  trong (protocol 9.1 cho phép).
  - Không hệ số chặn để zero-change là trường hợp riêng: mọi Δ đặc trưng bằng 0 thì dự đoán 0.
  - Vì vậy mỗi Δ đặc trưng **chỉ chia** cho SD của nó trên các lần cuff của người huấn luyện
    trong lượt ngoài, **không trừ trung bình**: trừ trung bình sẽ làm Δ đặc trưng = 0 không còn
    cho dự đoán 0. ΔBP cũng không trừ trung bình.
  - Mô hình học trên mọi lần cuff có nhãn của người huấn luyện: M0, M1, M2 của mọi phiên, mỗi
    người cùng tổng trọng số.
- Ghi chú: **zero-change** dự đoán ΔBP = 0, tức BP = BP₀.

## 5. Ước lượng và khoảng tin cậy

- Với mỗi đầu ra, tính d_s và d⁰_s cho từng người đạt chuẩn, rồi trung bình đều theo người.
- **Bootstrap theo người:**
  - lấy mẫu lại người có hoàn lại, cùng các lượt rút cho d và d⁰;
  - 10 000 lượt, seed cố định ghi trong commit khóa;
  - CI percentile (`software/evaluation/subject_bootstrap.py`).
- Phân tích hỗ trợ: Wilcoxon signed-rank trên d_s, hai phía, không dùng để kết luận.

## 6. Đa kiểm định (đề xuất: phương án A, chờ duyệt)

Kết luận chính cho một đầu ra cần **cả hai** CI của trung bình d_s và d⁰_s nằm hoàn toàn dưới 0
(kiểm định giao–hợp, RQ mục 4.E). Mỗi CI dùng cùng một mức. Giữa SBP và DBP dùng Holm theo đúng
các bước sau:

1. Xét cả hai đầu ra với CI hai phía 97,5 %.
2. Nếu đúng một đầu ra đạt kết luận chính ở bước 1, xét đầu ra còn lại với CI 95 %.
3. Nếu cả hai đều đạt ở bước 1 thì cả hai đều được tuyên bố.
4. Nếu không đầu ra nào đạt ở bước 1 thì dừng: không đầu ra nào được tuyên bố.

Bảng báo CI ở mức thật đã dùng cho từng đầu ra. Phương án B (Holm trên bốn phép so sánh) ghi lại
để thầy chọn. Lý do đề xuất A: kết luận chỉ đúng khi cả hai điều kiện cùng đạt, nên kiểm định
giao–hợp không cần chia mức trong một đầu ra.

## 7. Đọc kết quả theo δ

Dùng CI của trung bình d_s ở mức thật của mục 6, ký hiệu [L; U]. Đọc đúng như RQ mục 4.E:

- U < −δ: thêm PAT giảm sai số ít nhất δ;
- U < 0 và L < −δ ≤ U: có lợi, chưa chắc đạt δ;
- −δ ≤ L và U ≤ δ: tương đương trong phạm vi δ. Đây là kết quả âm tính có thông tin;
- L > 0 và U > δ: sai số tăng;
- còn lại: chưa kết luận, không viết "PAT không giúp".

## 8. Mức hiệu ứng nhỏ nhất đáng quan tâm δ (chốt sau pilot)

- **Quy tắc đề xuất (chờ duyệt, chưa có nguồn):**
  - σ_rep,X = SD của hiệu hai lần M0 liền nhau trong cùng phiên, chia √2, tính trên mọi phiên
    pilot có hai lần M0 hợp lệ. Đây là SD lặp lại của một lần đo cuff.
  - δ_X = max(1 mmHg; 0,5 × σ_rep,X), làm tròn lên bước 0,5 mmHg.
- **Lý do:** cải thiện MAE nhỏ hơn một nửa sai số lặp lại của chính tham chiếu thì khó tách khỏi
  nhiễu tham chiếu trong ứng dụng; sàn 1 mmHg tránh δ quá nhỏ khi pilot ít phiên.
- **Trước pilot**, mô phỏng dùng các kịch bản δ_SBP ∈ {1; 2; 3} và δ_DBP ∈ {1; 1,5; 2} mmHg.
- δ không đổi sau khi chốt, kể cả sau khi thấy dữ liệu chính.

## 9. Mô phỏng độ nhạy (2026-11-07, chỉ giả định)

**Cách làm.** Code: `scripts/simulate_rq1_sensitivity.py` và
`software/evaluation/rq1_sensitivity.py`. Config: `configs/analysis/rq1_sensitivity_v1.json`.

- Mỗi kịch bản mô phỏng 2 000 nghiên cứu. Mỗi nghiên cứu lấy CI bootstrap theo người với 1 000
  lượt rút, dùng chung cho d_s, d⁰_s và mọi mức CI (như mục 5).
- Mỗi phiên đánh giá có 4 lần cuff: M0, M0, M1, M2.
- ΔBP thật gồm ba phần: dao động giữa các ngày (SD 2,5/2 mmHg cho SBP/DBP); M1 (−3/−1,5 mmHg);
  M2 theo ba kịch bản hẹp, vừa, rộng (+3/+8/+15 mmHg SBP; +2/+5/+9 mmHg DBP).
- Nhiễu cuff có SD 3/2,5 mmHg. BP₀ là trung bình hai lần M0.
- Mỗi mô hình bắt được một phần ΔBP thật và có sai số theo người và theo lần cuff.
- Ba kịch bản mô hình: "null" (PAT không thêm gì), "benefit" (PAT giúp vừa) và "strong" (PAT giúp
  mạnh).
- SBP và DBP được mô phỏng riêng, nên chưa chạy được bước Holm giữa hai đầu ra (mục 6). Bảng báo
  xác suất cho từng đầu ra ở mức 95 % (trước Holm) và 97,5 % (bước đầu của Holm).

Mọi tham số là giả định, ghi trong config; số mô hình là kịch bản tự đặt, không phải ước lượng.
Mức nhiễu cuff và dao động giữa ngày được chọn để trung vị |ΔSBP| giữa hai buổi lúc nghỉ khoảng
3 mmHg, như ước lượng đọc từ Hình 3 của S4. Bảng đầy đủ:
[reports/weekly/week_07/rq1_sensitivity/summary.md](../../reports/weekly/week_07/rq1_sensitivity/summary.md)
(SHA-256 `450ac6ed…`, kèm `report.json`; chạy lại sau review cùng ngày).

**Kết quả, chỉ đúng dưới các giả định trên:**

1. **Cùng số buổi thì 3 phiên mỗi người cho CI hẹp hơn một chút so với 2 phiên.** Độ rộng CI
   95 % của trung bình d_s ở kịch bản M2 "vừa", mô hình "null" (mmHg):

   | Số buổi | Cách chia | SBP | DBP |
   | --- | --- | --- | --- |
   | 50–51 | 25 người × 2 phiên | 1,32 | 0,95 |
   | 50–51 | 17 người × 3 phiên | 1,22 | 0,87 |
   | 60 | 30 người × 2 phiên | 1,21 | 0,87 |
   | 60 | 20 người × 3 phiên | 1,13 | 0,81 |

   Ưu thế này đến từ giả định nhiễu theo lần cuff lớn hơn sai số riêng theo người. Nếu pilot cho
   thấy ngược lại thì nhiều người hơn sẽ có lợi hơn. Vì vậy chưa chốt; quy tắc chọn ở cuối mục.
2. **Khi PAT không thêm gì,** CI dài 0,9–1,7 mmHg (SBP) và 0,6–1,2 mmHg (DBP). Với
   δ_SBP = 2 và δ_DBP = 1,5, từ 97 % nghiên cứu trở lên cho kết quả "tương đương trong phạm vi
   δ", tức kết quả âm tính có thông tin. Tỷ lệ CI nằm dưới 0 là 3–5 %, gần mức 2,5 % của kiểm định
   một phía.
3. **Dải ΔBP và năng lực của mô hình cùng quyết định khả năng đạt kết luận chính.** Zero-change
   khó vượt khi ΔBP nhỏ. Tỷ lệ đạt kết luận chính (cả d_s lẫn d⁰_s dưới 0, mức 95 %, một đầu ra),
   trên mọi cách chia từ 15 người:

   | Kịch bản M2 | SBP "benefit" | SBP "strong" | DBP "benefit" | DBP "strong" |
   | --- | --- | --- | --- | --- |
   | Hẹp | ≤ 1 % | 6–8 % | ≤ 1 % | 5–7 % |
   | Vừa | 6–9 % | 33–72 % | 1–2 % | 18–40 % |
   | Rộng | 54–96 % | 92–100 % | 14–33 % | 69–99 % |

4. **R3 hiện tại gần như không phân biệt được dải ΔBP.** Thống kê R3 (trung vị qua người của
   trung vị |ΔSBP|) chỉ đi từ 3,7 lên 4,6 mmHg khi M2 tăng từ +3 lên +15 mmHg, vì một nửa số lần
   cuff là M0. Ngưỡng 15 mmHg vì vậy không bao giờ đạt, kể cả ở kịch bản rộng. Thống kê P2 mới đề
   xuất ở dưới thì đi theo đáp ứng M2 (2,9 → 15 mmHg SBP).

**Lưới P2** (cùng summary, mục "P2 grid"): giữ mọi giả định khác, cho trung bình đáp ứng M2 đổi
từ 4 đến 15 mmHg SBP (2 đến 9 mmHg DBP), với 25 người × 2 phiên và 20 người × 3 phiên. Tỷ lệ đạt
kết luận chính ở mức 95 % theo thống kê P2:

| P2 SBP (mmHg) | 4 | 6 | 8 | 10 | 12 | 15 |
| --- | --- | --- | --- | --- | --- | --- |
| "benefit" | 1 % | 2 % | 6–8 % | 19–23 % | 41–49 % | 78–83 % |
| "strong" | 9–12 % | 22–24 % | 43–50 % | 73–77 % | 91–95 % | 99–100 % |

Không có mức P2 nào bảo đảm kết luận chính: xác suất phụ thuộc mạnh vào việc PAT giúp bao nhiêu,
mà điều này chưa biết trước pilot.

**Đề xuất cho P2/R3 (đề xuất đổi so với protocol 6.5, chờ duyệt):**

- **Thống kê:** P2 ở pilot dùng trung vị qua người của ΔSBP **có dấu** ở lần cuff M2, so với
  trung bình M0 cùng buổi. Thống kê này đi theo đáp ứng M2, khác R3.
- **Ngưỡng:** đề xuất **10 mmHg** làm mức báo động, không phải mức bảo đảm.
  - Dưới 10 mmHg, ngay cả kịch bản PAT giúp mạnh cũng chỉ có khoảng ba phần tư khả năng đạt kết
    luận chính, còn kịch bản giúp vừa dưới 25 %.
  - Dưới ngưỡng thì báo thầy và rà lại nghiệm pháp (protocol 6.4, "Dự phòng") trước khi thu chính.
  - Con số 10 là lựa chọn dựa trên các kịch bản đã chạy, không suy ra được từ dữ liệu.
- **R3:** giữ làm chỉ số mô tả ở G4 kèm SD của ΔBP tham chiếu, không làm ngưỡng kích hoạt.

**Chốt sau pilot (quy tắc, không theo kết quả RQ1):**

1. Chạy lại mô phỏng với các tham số ước lượng từ pilot: SD lặp cuff, dao động giữa ngày, đáp
   ứng M1 và M2. Năng lực mô hình vẫn là kịch bản, vì không được dùng sai số mô hình trên pilot.
   Ghi config và hash.
2. Giữ trần tuyển 35 người, trừ người pilot, và lấy số buổi khả thi từ lịch thu chính.
3. Trong các cách chia cùng số buổi, chọn cách có CI kỳ vọng hẹp nhất, với điều kiện ≥ 15 người
   đạt chuẩn. Nếu hai cách chênh nhau dưới 5 % thì chọn cách nhiều người hơn, vì ít phụ thuộc giả
   định hơn.
4. Ghi N, phân bổ phiên và δ vào file này kèm ngày và commit, trước buổi thu chính đầu tiên.

## 10. Dữ liệu thiếu và lượt dừng

Theo protocol mục 10, khóa lại ở đây:

- **Mất nhãn cuff:** lần đo bị hủy. Không điền nhãn.
- **Mất ECG nhưng PPG đạt:** ra khỏi phép so sánh chính; vẫn vào PPG-only trên mọi lần đo
  (endpoint phụ 3). Báo tỷ lệ theo người.
- **Mất PPG:** ra khỏi mọi mô hình có PPG.
- **Lượt bị dừng vì an toàn:** đã có nhãn đầy đủ thì giữ; endpoint phụ 7 bỏ các lượt này.
- **Người chỉ có phiên 1:** không đạt chuẩn, không vào RQ1; báo số người và lý do.
- **Không điền dữ liệu thiếu bằng mô hình.** Phân tích chính dùng mọi lần cuff có sẵn của người
  đạt chuẩn (complete case ở mức lần cuff).
- Nếu tỷ lệ mất ECG khác nhau rõ giữa nghiệm pháp, nêu là rủi ro thiên lệch, không sửa bằng
  trọng số.

## 11. Báo cáo

- Bảng chính theo đầu ra: MAE, ME ± SD của sai số, cho zero-change, PAT-only, PPG-only và
  PPG + PAT; trung bình d_s và d⁰_s; CI ở mức thật; cách đọc theo δ.
- Luôn báo SD của ΔBP tham chiếu và tỷ lệ |ΔBP| > 5 mmHg, gộp và theo nghiệm pháp.
- **Hình:** d_s theo người; phân bố ΔBP theo nghiệm pháp; Bland–Altman cho dữ liệu đo lặp (phương
  pháp LoA cho đo lặp, chờ chọn).
- Mọi kết quả phụ ghi là không xác nhận.

## 12. Kiểm soát thay đổi

- Mọi thay đổi sau khi khóa phải là một commit riêng có ngày và lý do, trước khi chạy vòng ngoài.
- Thay đổi sau khi đã chạy vòng ngoài thì tạo phiên bản mới và báo cả hai.
- Vòng ngoài chạy bằng một script ghi commit, hash dữ liệu, config, và từ chối chạy khi file
  này hay config chưa commit (như các runner B2, B5).

## 13. Các mục chờ duyệt

1. Phương án A cho đa kiểm định (mục 6).
2. Quy tắc δ (mục 8).
3. Ridge với α = 1, không hệ số chặn, không vòng trong (mục 4).
4. 10 000 lượt bootstrap, seed cố định (mục 5).
5. P2 mới: ΔSBP có dấu của M2, ngưỡng báo động 10 mmHg (phụ thuộc kịch bản mô hình). R3 chỉ
   để mô tả (mục 9).
6. Quy tắc chọn số người và phân bổ phiên sau pilot (mục 9).
7. Các endpoint phụ (mục 3).
8. SQI v1 ([sqi_specification_v1.md](sqi_specification_v1.md)).
