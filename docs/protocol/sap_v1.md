# Kế hoạch phân tích thống kê (SAP) v1 cho RQ1

> **Trạng thái: đề xuất ngày 2026-11-07; mọi mục chốt ngày 2026-11-12 (báo thầy); chưa khóa.**
> Các giá trị ghi "chốt sau pilot" và ngưỡng SQI (khóa trên bản ghi G2) vẫn để trống theo quy
> tắc ở đây.
>
> - **Nguồn đã chốt hay đề xuất trước đó:** [RQ v0.4](../research_questions_v0.1.md) mục 4,
>   [protocol v0.3](protocol_outline_v0.2.md) mục 4.1, 6.4–6.5, 7.3, 9, 10;
>   [kịch bản bài báo](../paper_scenarios_v0.1.md). Chỗ nào SAP đổi so với các file đó đều ghi rõ;
>   các file đó đã được sửa theo ngày 2026-11-12.
> - **Khi nào khóa:** bằng một commit có ngày, **trước pilot**. Sau pilot chỉ được điền những giá
>   trị ghi "chốt sau pilot" (δ, số người, phân bổ phiên), theo đúng quy tắc ở đây, trước khi thu
>   dữ liệu chính.
> - **Những gì không được dùng:** không dùng kết quả RQ1, cũng không dùng sai số mô hình trên
>   pilot hay dữ liệu chính, để chốt bất kỳ mục nào.
> - **Dữ liệu:** SAP này không phụ thuộc dữ liệu người nào. Mô phỏng ở mục 9 chỉ dùng giả định.
> - **RQ2b và RQ3:** dùng lại các quy tắc ở đây; RQ3 là thăm dò.
> - **Sửa 2026-11-10 (chốt 2026-11-12), sau rà soát tài liệu và một vòng phản biện độc lập:**
>   mục 5 đổi kiểu khoảng tin cậy chính, vì kiểu percentile thiếu phủ ở 15–35 người; mục 6 và 7
>   thêm giới hạn của cách đọc; mục 9 chạy lại mô phỏng với config v2 (cùng giả định, thêm so
>   sánh các kiểu CI và bảng xác suất của từng cách đọc theo δ); mục 13 cập nhật.
> - **Sửa 2026-11-11 (chốt 2026-11-12):** mục 9 thêm hai mô phỏng còn thiếu (SBP và DBP chung
>   một nghiên cứu với Holm; Ridge huấn luyện thật trong LOSO), mục 4 thêm thang trọng số, mục 5
>   và 6 ghi kết quả, mục 13 cập nhật.
> - **Sửa 2026-11-12 (chốt, báo thầy), sau một vòng phản biện độc lập:** thêm hai baseline
>   không dùng tín hiệu (trung bình theo pha, độ lệch hằng số) và endpoint phụ bắt buộc dᴾ (mục
>   3, 4, 7, 11); thêm hai endpoint phụ (biến chỉ pha, trung vị theo pha; mục 3); mục 9 thêm kết
>   quả 9 và 10; mục 13 cập nhật.

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
- **Endpoint phụ bắt buộc, so với baseline theo pha (chốt 2026-11-12):**
  - θᴾ = E_s[dᴾ_s], với dᴾ_s = MAE_s(PPG+PAT) − MAE_s(trung bình theo pha) (baseline ở mục 4);
  - báo trung bình và CI 95 % khoảng bao (mục 5), dùng chung lượt rút với d và d⁰, luôn có
    trong bảng chính;
  - không phải điều kiện của kết luận chính (mục 7 ghi cách dùng khi viết bài). Phương án đã
    cân nhắc và không chọn: đưa dᴾ thành điều kiện thứ ba của kết luận chính. Dưới các giả định
    của mục 9 (kết quả 9), CI của dᴾ nằm dưới 0 ở ≤ 0,3 % nghiên cứu, nên kết luận chính gần
    như không bao giờ đạt; câu hỏi chính của RQ1 là PAT so với PPG-only, không phải mô hình so
    với giao thức.
- **Lý do cần endpoint này:** PPG-only và PPG + PAT có HR từ PPG, mà HR đổi rõ theo nghiệm pháp.
  Một mô hình chỉ cần nhận ra lần cuff đang ở pha nào (M0, M1, M2) rồi dự đoán mức đổi điển hình
  của pha đó là đã có thể vượt zero-change, dù không theo được BP của riêng từng người. Phép so
  chính d cũng không được che hoàn toàn khỏi điều này: PAT có thể chỉ giúp nhận ra pha tốt hơn HR.
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
  10. **PAT khi mô hình đã biết pha** (chốt 2026-11-12): pha + PPG so với
      pha + PPG + PAT. Hai mô hình thêm cùng ba biến chỉ pha (mục 4), cùng cách chia SD, cùng
      α, cùng thang trọng số. Hiệu MAE theo người và CI như d. Đây là phép kiểm trực tiếp hơn
      cho câu hỏi PAT có thêm thông tin ngoài pha hay không, nhưng là một đặc tả mô hình mới,
      nên không thay phép so chính. Độ nhạy thấp (mục 9, kết quả 10), nên chỉ dùng để mô tả.
  11. Baseline theo pha dùng trung vị thay trung bình (mục 4; chốt 2026-11-12): MAE tối ưu ở trung vị, nên vượt
      trung bình theo pha có thể chỉ nhờ phân bố ΔBP lệch.
- **Cách tính endpoint 5 và 7 (đề xuất 2026-11-14, chờ duyệt).** BP₀, đặc trưng nền và tư cách
  đạt chuẩn giữ nguyên như phân tích chính. Bộ lọc của endpoint (cờ SQI thuộc tập loại; cờ dừng
  an toàn) chỉ bỏ lần cuff khỏi tập học và tập đánh giá, rồi học lại theo mục 4; không xét lại
  ngưỡng ≥ 2 lần cuff mỗi phiên sau khi lọc. Các mô hình so trên cùng tập cuff còn lại. Người
  không còn lần cuff đánh giá nào thì không có d_s trong endpoint đó; báo số người, lý do và số
  lần cuff còn lại theo người. Ước lượng và CI theo mục 5, riêng SBP và DBP. Phương án đã cân
  nhắc và không chọn: lọc cả lần cuff hiệu chuẩn (đổi BP₀ nên đổi nhãn ΔBP của mọi lần cuff,
  trộn hai hiệu ứng và có thể loại người); giữ BP₀ nhưng tính lại đặc trưng nền từ lần cuff qua
  lọc (BP₀ và đặc trưng nền lệch mốc với nhau). Endpoint 6 vẫn chạy lại toàn bộ vì nó đổi chính
  tập phân tích.

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
- **Thuật toán (chốt 2026-11-12):** Ridge trên Δ đặc trưng, α = 1 cố định, không hệ số chặn.
  Hai mô hình của phép so sánh chính dùng cùng thuật toán và cùng α. Vì α cố định nên bỏ vòng
  trong (protocol 9.1 cho phép).
  - Không hệ số chặn để zero-change là trường hợp riêng: mọi Δ đặc trưng bằng 0 thì dự đoán 0.
  - Vì vậy mỗi Δ đặc trưng **chỉ chia** cho SD của nó trên các lần cuff của người huấn luyện
    trong lượt ngoài, **không trừ trung bình**: trừ trung bình sẽ làm Δ đặc trưng = 0 không còn
    cho dự đoán 0. ΔBP cũng không trừ trung bình.
  - Mô hình học trên mọi lần cuff có nhãn của người huấn luyện: M0, M1, M2 của mọi phiên, mỗi
    người cùng tổng trọng số.
  - **Thang trọng số (đề xuất 2026-11-11, chốt 2026-11-12):** mỗi lần cuff của người s có trọng số
    1 / (số lần cuff của s trong tập huấn luyện), nên mỗi người huấn luyện có tổng trọng số 1 và
    tổng các trọng số bằng số người huấn luyện. α = 1 áp trên thang này. Phải khóa thang, vì với
    α cố định, nhân mọi trọng số với một hằng số sẽ đổi độ co của Ridge.
- Ghi chú: **zero-change** dự đoán ΔBP = 0, tức BP = BP₀.
- **Hai baseline không dùng tín hiệu (chốt 2026-11-12).** "Không dùng tín hiệu"
  nghĩa là không đọc ECG hay PPG của người được dự đoán; chỉ dùng nhãn của người huấn luyện và
  pha theo lịch đo.
  - **Trung bình theo pha (P):** trong mỗi lượt ngoài, với mỗi pha p ∈ {M0, M1, M2}, lấy trung
    bình ΔBP của từng người huấn luyện trên các lần cuff pha p **ở phiên ≥ 2** thuộc tập phân
    tích chính, rồi lấy trung bình đều theo người của các giá trị đó. P dự đoán đúng giá trị
    này cho mọi lần cuff pha p của người bị giữ lại. Nhãn của người bị giữ lại không bao giờ
    vào P.
  - **Độ lệch hằng số (C):** như P nhưng gộp mọi pha thành một, nên chỉ có một giá trị. C chỉ
    tách phần "vượt zero-change nhờ học độ lệch chung giữa các phiên". Nó gần với baseline
    "static" của S4 nhưng không giống: S4 hồi quy trên BP hiệu chuẩn và giờ trong ngày.
  - **Vì sao chỉ dùng phiên ≥ 2:** đó là quần thể được đánh giá. Ở phiên 1, trung bình ΔBP của
    M0 bằng 0 theo cách tính BP₀, nên gộp phiên 1 sẽ kéo mức M0 về 0 một cách giả tạo.
  - **Pha** lấy từ lịch đo (mã sự kiện của người vận hành), không suy ra từ BP đo được, vì suy
    từ BP sẽ làm rò nhãn.
  - **Thiếu pha:** nếu không người huấn luyện nào có lần cuff pha p trong lượt đó thì P dự đoán
    0 cho pha p. Báo số lượt rơi vào trường hợp này, cùng số lần cuff mỗi pha bị bỏ qua (ví dụ
    dừng an toàn trước M2). Vì việc bỏ pha có thể phụ thuộc BP, kết quả chỉ áp cho các lần cuff
    đã đo được.
  - **Trọng số:** trung bình đều theo người trong từng pha. Khi số lần cuff mỗi pha khác nhau
    giữa người, cách này không trùng trọng số 1 / số lần cuff dùng trong MAE_s; ghi rõ khi báo.
  - **Biến thể trung vị** (endpoint phụ 11): thay trung bình đều theo người bằng trung vị của
    các trung bình theo người, cũng trong từng pha.
- **Biến chỉ pha cho endpoint phụ 10:** ba biến 0/1 là M1, M2 và "phiên ≥ 2". Lần cuff M0 của
  phiên 1 có cả ba biến bằng 0, nên mô hình vẫn dự đoán 0 khi mọi Δ đặc trưng bằng 0, đúng như
  mô hình không hệ số chặn ở trên.

## 5. Ước lượng và khoảng tin cậy

- Với mỗi đầu ra, tính d_s và d⁰_s cho từng người đạt chuẩn, rồi trung bình đều theo người.
- **Bootstrap theo người:**
  - lấy mẫu lại người có hoàn lại, cùng các lượt rút cho d và d⁰;
  - 10 000 lượt, seed cố định ghi trong commit khóa.
- **Khoảng tin cậy chính (đổi ngày 2026-11-10, chốt 2026-11-12; bản 2026-11-07 dùng
  percentile):** khoảng bao của hai khoảng sau, tức lấy cận rộng hơn ở mỗi phía:
  - bootstrap-t theo người: mỗi lượt rút chia cho sai số chuẩn của chính lượt đó;
  - Student t trên d_s: trung bình ± t(n − 1) × SD / √n.

  Khoảng bao nằm dưới 0 chỉ khi **cả hai** khoảng cùng nằm dưới 0.
- **Lý do đổi** (số ở mục 9, kết quả 5; mọi số là mô phỏng trên giả định):
  - percentile cho CI nằm dưới 0 ở 3,7 % nghiên cứu khi PAT không thêm gì, so với mức danh nghĩa
    2,5 %; BCa không khá hơn (4,0 %);
  - Student t giữ đúng mức khi d_s đối xứng (2,5 %), nhưng lên tới 8,3 % khi d_s lệch phải, tức
    khi vài người có sai số tăng mạnh lúc thêm PAT;
  - bootstrap-t chịu lệch tốt hơn (tối đa 4,1 %) nhưng lên tới 5,1 % khi d_s có đuôi nặng hoặc
    vài người ngoại lệ;
  - khoảng bao giữ 2,3 % ở mô hình BP và tối đa 4,1 % ở các dạng phân bố đã thử. Cái giá là CI
    rộng hơn percentile từ 9 % (35 người) tới 23 % (15 người).
  - Phương án đã cân nhắc và không chọn: chỉ dùng Student t. Đơn giản hơn, nhưng lên tới 8,3 %
    khi d_s lệch phải, mà với 15–35 người thì không kiểm được phân bố của d_s trước khi chạy.
- **Phân tích độ nhạy khai trước:** báo thêm CI percentile, BCa, bootstrap-t riêng và Student t
  riêng. Nếu kết luận chính đổi theo kiểu CI thì ghi rõ là kết luận không vững.
- **Giới hạn:**
  - Mọi kiểu CI ở đây coi d_s của các người là độc lập. Trong LOSO, các mô hình được huấn luyện
    trên những tập người chồng lấp nhau, nên d_s phụ thuộc nhau. Mô phỏng có huấn luyện Ridge
    thật trong LOSO (mục 9, kết quả 8; 2026-11-11) cho thấy phụ thuộc này làm CI trượt nhiều
    hơn danh nghĩa **ở phía trên** (CI nằm hẳn trên θ: tối đa khoảng 8 % so với 2,5 %), tức
    đánh giá thấp lợi ích. Phía dưới, chiều dẫn tới kết luận sai là PAT có lợi, không vượt
    2,5 % ở mọi kịch bản đã chạy. CI chính vì vậy giữ nguyên; độ phủ hai phía chỉ khoảng 92–95 %
    và phải nêu là giới hạn khi báo kết quả.
  - Code: `bootstrap_bp(..., contrasts=..., contrast_ci_methods=(...))` trong
    `software/evaluation/subject_bootstrap.py` tính năm kiểu CI cho hiệu MAE trung bình đều theo
    người (thêm 2026-11-11, có test đáp án biết trước). Công thức nằm ở
    `software/evaluation/mean_intervals.py`, dùng chung với mô phỏng ở mục 9, nên phân tích thật
    và mô phỏng tính CI giống hệt nhau.
- Phân tích hỗ trợ: Wilcoxon signed-rank trên d_s, hai phía, không dùng để kết luận.

## 6. Đa kiểm định (phương án A, chốt 2026-11-12)

Kết luận chính cho một đầu ra cần **cả hai** CI của trung bình d_s và d⁰_s nằm hoàn toàn dưới 0
(kiểm định giao–hợp, RQ mục 4.E). Mỗi CI dùng cùng một mức. Giữa SBP và DBP dùng Holm theo đúng
các bước sau:

1. Xét cả hai đầu ra với CI hai phía 97,5 %.
2. Nếu đúng một đầu ra đạt kết luận chính ở bước 1, xét đầu ra còn lại với CI 95 %.
3. Nếu cả hai đều đạt ở bước 1 thì cả hai đều được tuyên bố.
4. Nếu không đầu ra nào đạt ở bước 1 thì dừng: không đầu ra nào được tuyên bố.

Bảng báo CI ở mức thật đã dùng cho từng đầu ra. Lý do chọn A: kết luận chỉ đúng khi cả hai điều
kiện cùng đạt, nên kiểm định giao–hợp không cần chia mức trong một đầu ra; mô phỏng chung SBP và
DBP (kết quả 7) cho thấy A giữ sai lầm quanh mức danh nghĩa. Phương án đã cân nhắc và không chọn:
B, Holm trên bốn phép so sánh (2 đầu ra × 2 đối chứng). B chia mức thêm trong một đầu ra mà kiểm
định giao–hợp không cần, nên mất độ nhạy mà không giảm sai lầm của kết luận chính.

Ghi chú thêm ngày 2026-11-10:

- Bốn bước trên tương đương Holm với kiểm định một phía ở mức chung 2,5 %: ngưỡng 1,25 % ở bước
  1, rồi 2,5 % cho đầu ra còn lại.
- Sai lầm loại I của kết luận chính lớn nhất khi PAT không thêm gì (d = 0) còn mô hình chắc
  chắn vượt zero-change. Khi đó nó bằng tỷ lệ CI của d_s nằm dưới 0, tức cột `P(U<0)` của các dòng
  "null" ở mục 9.
- CI ở mức của Holm không phải CI đồng thời cho các phát biểu tại ±δ. Cách đọc theo δ ở mục 7 vì
  vậy là cách phân loại mô tả đi kèm kết luận chính, không phải một kiểm định có kiểm soát sai
  lầm chung.
- Mô phỏng chung SBP và DBP (mục 9, kết quả 7; 2026-11-11) cho xác suất sau đủ các bước Holm.
  Khi một đầu ra không có hiệu ứng, tỷ lệ tuyên bố nhầm đầu ra đó không quá 0,6 %, kể cả khi đầu
  ra kia mạnh và đi qua bước 1.

## 7. Đọc kết quả theo δ

Dùng CI của trung bình d_s ở mức thật của mục 6, ký hiệu [L; U]. Đọc đúng như RQ mục 4.E:

- U < −δ: thêm PAT giảm sai số ít nhất δ;
- U < 0 và L < −δ ≤ U: có lợi, chưa chắc đạt δ;
- −δ ≤ L và U ≤ δ: tương đương trong phạm vi δ. Đây là kết quả âm tính có thông tin;
- L > 0 và U > δ: sai số tăng;
- còn lại: chưa kết luận, không viết "PAT không giúp".

Ghi chú 2026-11-10: cách đọc thứ hai nghĩa là có lợi nhưng CI chưa loại được khả năng lợi ích
nhỏ hơn δ; nó không khẳng định lợi ích nhỏ hơn δ. Với dải ΔBP dự kiến, cách đọc thứ nhất gần như
ngoài tầm (mục 9, kết quả 6).

**Dùng dᴾ khi viết bài (chốt 2026-11-12).** Kết luận chính giữ đúng lời của RQ
mục 4.E: "thêm PAT làm giảm sai số so với PPG-only và vượt zero-change". dᴾ không đổi kết luận
đó, nhưng giới hạn những gì được viết thêm:

- Chỉ được viết rằng mô hình theo được thay đổi BP của từng người, vượt mức đoán theo pha của
  giao thức, khi CI của trung bình dᴾ_s nằm hoàn toàn dưới 0.
- Nếu CI của dᴾ không nằm hẳn dưới 0: viết "chưa chứng minh được mô hình vượt baseline theo
  pha". Không viết rằng lợi ích chắc chắn chỉ do nhận ra pha, vì CI chứa 0 không chứng minh
  điều đó.
- Vượt P chỉ cho biết mô hình hơn baseline này. Nó không chứng minh phần thông tin riêng từng
  người đến từ PAT; câu hỏi đó thuộc endpoint phụ 10. Khi kết luận chính đạt mà CI của endpoint
  phụ 10 chứa 0, viết rằng chưa tách được phần lợi ích của PAT ngoài việc nhận ra pha.

## 8. Mức hiệu ứng nhỏ nhất đáng quan tâm δ (chốt sau pilot)

- **Quy tắc (chốt 2026-11-12, chưa có nguồn; giá trị tính sau pilot):**
  - σ_rep,X = SD của hiệu hai lần M0 liền nhau trong cùng phiên, chia √2, tính trên mọi phiên
    pilot có hai lần M0 hợp lệ. Đây là SD lặp lại của một lần đo cuff.
  - δ_X = max(1 mmHg; 0,5 × σ_rep,X), làm tròn lên bước 0,5 mmHg.
- **Lý do:** cải thiện MAE nhỏ hơn một nửa sai số lặp lại của chính tham chiếu thì khó tách khỏi
  nhiễu tham chiếu trong ứng dụng; sàn 1 mmHg tránh δ quá nhỏ khi pilot ít phiên.
- **Trước pilot**, mô phỏng dùng các kịch bản δ_SBP ∈ {1; 2; 3} và δ_DBP ∈ {1; 1,5; 2} mmHg.
- δ không đổi sau khi chốt, kể cả sau khi thấy dữ liệu chính.

## 9. Mô phỏng độ nhạy (2026-11-07, chạy lại 2026-11-10; chỉ giả định)

**Cách làm.** Code: `scripts/simulate_rq1_sensitivity.py` và
`software/evaluation/rq1_sensitivity.py`. Config: `configs/analysis/rq1_sensitivity_v2.json`
(cùng giả định với v1; v1 vẫn chạy được và cho lại số của bản 2026-11-07).

- Mỗi kịch bản mô phỏng 2 000 nghiên cứu. Mỗi nghiên cứu lấy CI theo người với 1 000 lượt rút,
  dùng chung cho d_s, d⁰_s, mọi mức CI và mọi kiểu CI (như mục 5). Các nghiên cứu của một kịch
  bản chia thành 10 khối, mỗi khối một bộ lượt rút riêng (bản v1 dùng chung một bộ).
- **Các bảng dưới đây dùng khoảng bao của mục 5.** Bản 2026-11-07 dùng percentile, nên các số
  của bản đó lạc quan hơn (CI hẹp hơn, tỷ lệ đạt kết luận chính cao hơn).
- Phép kiểm kiểu CI (kết quả 5) còn rút thẳng d_s có trung bình 0 theo năm dạng phân bố (chuẩn,
  t ba bậc tự do, lệch phải, lệch trái, 10 % người ngoại lệ), mỗi dạng 10 000 mẫu, vì mô hình BP
  ở đây dùng sai số chuẩn và d_s của nó gần đối xứng.
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
[reports/weekly/week_07/rq1_sensitivity_v2/summary.md](../../reports/weekly/week_07/rq1_sensitivity_v2/summary.md)
(SHA-256 `1d6b42cf…`, kèm `report.json`; chạy ngày 2026-11-10 trên bản chưa commit, hash của
code ghi trong `report.json`). Bản 2026-11-07 dùng CI percentile vẫn ở
[rq1_sensitivity/summary.md](../../reports/weekly/week_07/rq1_sensitivity/summary.md)
(SHA-256 `450ac6ed…`).

**Kết quả, chỉ đúng dưới các giả định trên:**

1. **Cùng số buổi thì 2 phiên và 3 phiên mỗi người cho CI gần như bằng nhau.** Độ rộng CI 95 %
   của trung bình d_s ở kịch bản M2 "vừa", mô hình "null" (mmHg):

   | Số buổi | Cách chia | SBP | DBP |
   | --- | --- | --- | --- |
   | 50–51 | 25 người × 2 phiên | 1,48 | 1,08 |
   | 50–51 | 17 người × 3 phiên | 1,45 | 1,04 |
   | 60 | 30 người × 2 phiên | 1,34 | 0,97 |
   | 60 | 20 người × 3 phiên | 1,31 | 0,94 |

   Chênh lệch chỉ 2–4 %, dưới mức 5 % của quy tắc chọn ở cuối mục, nên theo quy tắc đó cách
   nhiều người hơn được ưu tiên. Bản 2026-11-07 (percentile) cho 3 phiên lợi hơn rõ (7–8 %),
   vì percentile không tính tới việc ít người thì phân vị phải rộng hơn. Kết luận này vẫn phụ
   thuộc giả định nhiễu theo lần cuff lớn hơn sai số riêng theo người, nên chốt sau pilot.
2. **Khi PAT không thêm gì,** CI dài 0,9–2,0 mmHg (SBP) và 0,7–1,5 mmHg (DBP). Với
   δ_SBP = 2 và δ_DBP = 1,5, ít nhất 92 % nghiên cứu (SBP) và 94 % (DBP) cho kết quả "tương đương
   trong phạm vi δ", tức kết quả âm tính có thông tin.
3. **Dải ΔBP và năng lực của mô hình cùng quyết định khả năng đạt kết luận chính.** Zero-change
   khó vượt khi ΔBP nhỏ. Tỷ lệ đạt kết luận chính (cả d_s lẫn d⁰_s dưới 0, mức 95 %, một đầu ra),
   trên mọi cách chia từ 15 người:

   | Kịch bản M2 | SBP "benefit" | SBP "strong" | DBP "benefit" | DBP "strong" |
   | --- | --- | --- | --- | --- |
   | Hẹp | 0 % | 3–6 % | 0 % | 2–5 % |
   | Vừa | 3–6 % | 20–66 % | 0–1 % | 10–35 % |
   | Rộng | 38–94 % | 84–100 % | 8–27 % | 54–98 % |

4. **R3 hiện tại gần như không phân biệt được dải ΔBP.** Thống kê R3 (trung vị qua người của
   trung vị |ΔSBP|) chỉ đi từ 3,7 lên 4,5 mmHg khi M2 tăng từ +3 lên +15 mmHg, vì một nửa số lần
   cuff là M0. Ngưỡng 15 mmHg vì vậy không bao giờ đạt, kể cả ở kịch bản rộng. Thống kê P2 mới đề
   xuất ở dưới thì đi theo đáp ứng M2 (2,9 → 15 mmHg SBP).
5. **Kiểu CI (thêm 2026-11-10).** Tỷ lệ nghiên cứu có CI 95 % của d_s nằm dưới 0 khi PAT không
   thêm gì (mức danh nghĩa 2,5 %), trung bình trên 36 dòng "null" của SBP; DBP cho số gần như
   trùng. Hai cột cuối là tỷ lệ lớn nhất ở mỗi phía trong phép kiểm theo dạng phân bố:

   | Kiểu CI | Mô hình BP, mức 95 % | Mô hình BP, mức 97,5 % (danh nghĩa 1,25 %) | Dạng phân bố: dưới 0 | Dạng phân bố: trên 0 |
   | --- | --- | --- | --- | --- |
   | Percentile | 3,7 % | 2,3 % | 9,3 % (lệch phải, 15 người) | 9,3 % |
   | BCa | 4,0 % | 2,5 % | 7,1 % (lệch phải, 15 người) | 7,1 % |
   | Bootstrap-t | 2,9 % | 1,5 % | 5,1 % (người ngoại lệ, 35 người) | 4,5 % |
   | Student t | 2,5 % | 1,2 % | 8,3 % (lệch phải, 15 người) | 8,2 % |
   | Khoảng bao (chọn) | 2,3 % | 1,1 % | 4,1 % (lệch phải, 15 người) | 4,2 % |

   - Bản 2026-11-07 ghi tỷ lệ của percentile là "3–5 %, gần mức 2,5 %". Câu đó sai: tỷ lệ này
     cao gấp rưỡi mức danh nghĩa, và ở mức 97,5 % của bước Holm đầu thì gần gấp đôi.
   - Không kiểu CI nào giữ được mức danh nghĩa khi d_s lệch mạnh và chỉ có 15 người. Khi báo kết
     quả phải kèm hình phân bố của d_s.
   - Với 1 000 lượt rút, đuôi 97,5 % chỉ có khoảng 12 lượt. Tăng lên 4 000 lượt thì tỷ lệ của
     bootstrap-t ở mức 97,5 % giảm từ 1,4 % xuống 1,1 % (d_s chuẩn, 15 người), nên 10 000 lượt
     của phân tích thật là cần thiết.
6. **Xác suất của từng cách đọc theo δ (thêm 2026-11-10).** Mức 95 %, δ_SBP = 2 và δ_DBP = 1,5,
   hai thiết kế 25 người × 2 phiên và 20 người × 3 phiên; d là hiệu ứng thật được giả định:

   | Đầu ra, kịch bản M2, mô hình | d (mmHg) | Giảm ít nhất δ | Có lợi, chưa chắc đạt δ | Tương đương trong δ |
   | --- | --- | --- | --- | --- |
   | SBP, hẹp, "benefit" | −0,61 | 0 % | 3–6 % | 93–97 % |
   | SBP, hẹp, "strong" | −1,17 | 0 % | 36–46 % | 53–64 % |
   | SBP, vừa, "benefit" | −0,81 | 0 % | 9–14 % | 85–91 % |
   | SBP, vừa, "strong" | −1,48 | 0 % | 71–76 % | 24–28 % |
   | SBP, rộng, "benefit" | −1,33 | 0 % | 54–59 % | 41–45 % |
   | SBP, rộng, "strong" | −2,26 | 8–10 % | 89–91 % | 0–1 % |
   | DBP, vừa, "strong" | −1,03 | 0 % | 60–64 % | 36–40 % |
   | DBP, rộng, "strong" | −1,45 | 1 % | 95 % | 4 % |

   - Cách đọc "sai số tăng" không xảy ra; "chưa kết luận" không quá 1 %.
   - **Cách đọc "giảm ít nhất δ" gần như ngoài tầm.** Chỉ kịch bản có hiệu ứng thật lớn hơn δ
     (SBP, rộng, "strong") mới đạt, và cũng chỉ 8–10 %. Mọi hiệu ứng giả định khác đều nhỏ hơn δ,
     nên kết quả tốt nhất có thể là "có lợi, chưa chắc đạt δ".
   - **Khi PAT giúp ở mức vừa, kết quả dễ gặp nhất là "tương đương trong δ"** (85–99 % ở kịch
     bản hẹp và vừa), dù hiệu ứng thật khác 0. Bài báo khi đó phải viết là lợi ích, nếu có, nhỏ
     hơn δ; không viết là PAT không có tác dụng.
7. **SBP và DBP chung một nghiên cứu, áp Holm (thêm 2026-11-11).** Code
   `software/evaluation/rq1_holm_loso.py`, `scripts/simulate_rq1_holm_loso.py`, config
   `configs/analysis/rq1_holm_loso_v1.json` (dùng nguyên target và mô hình của config v2); mọi
   thành phần ngẫu nhiên của DBP tương quan ρ với thành phần tương ứng của SBP, ρ ∈ {0; 0,6}
   (giả định). Kết quả: [rq1_holm_loso/summary.md](../../reports/weekly/week_07/rq1_holm_loso/summary.md)
   (SHA-256 `80d58cf5…`, kèm `report.json`; chạy 2026-11-11 trên bản chưa commit). Chạy lại
   2026-11-12 với runner v3 trên commit `edbe46d`, không có thay đổi chưa commit, để thêm kết quả
   9 và 10 (summary SHA-256 `e103e769…`). Mọi số của kết quả 7 và 8 trùng hệt lần trước, vì phần
   thêm không rút thêm số ngẫu nhiên nào.
   - Khi PAT không thêm gì ở cả hai đầu ra: tỷ lệ tuyên bố ít nhất một đầu ra ≤ 0,2 %. Cận
     trên khi mô hình chắc chắn vượt zero-change (Holm chỉ trên CI của d) là 1,5–2,8 %, quanh
     mức danh nghĩa 2,5 % (sai số Monte Carlo khoảng 0,35 điểm %).
   - Khi một đầu ra không có hiệu ứng và đầu ra kia mạnh: tuyên bố nhầm đầu ra không có hiệu
     ứng ≤ 0,6 %. Bước 2 của Holm vì vậy không làm tăng sai lầm trong các kịch bản đã chạy.
   - Cái giá của Holm: ví dụ M2 vừa, "strong" cả hai, 25 người × 2 phiên, ρ = 0: tuyên bố SBP
     26,7 % (một mình ở 95 %: 36,6 %), DBP 13,3 % (17,5 %), cả hai 6,3 %. ρ = 0,6 cho số gần
     như trùng.
   - Giới hạn: phần này dùng sai số mô hình đặt sẵn như các kết quả 1–6, không huấn luyện mô
     hình; chưa thử trường hợp phép so với zero-change là điều kiện chặn.
8. **Ridge huấn luyện thật trong LOSO (thêm 2026-11-11).** Cùng code và config, chỉ SBP, M2
   vừa và rộng. Đặc trưng sinh từ ΔBP thật theo một mô hình tự đặt: ba đặc trưng PPG yếu, một
   đặc trưng HR từ PPG chỉ đánh dấu M2, và ΔPAT với ba mức (không liên quan BP, vừa, mạnh); nền
   đặc trưng đo có nhiễu như BP₀. Mỗi lượt ngoài học Ridge như mục 4 trên n − 1 người. θ (trung
   bình d kỳ vọng của thiết kế) lấy từ một mô phỏng riêng 20 000 nghiên cứu.
   - Tương quan d giữa hai người cùng nghiên cứu gần 0 (−0,017 tới 0,004), và SD của trung bình
     d qua các nghiên cứu xấp xỉ sai số chuẩn ngây thơ (tỷ số 0,82–1,03).
   - Nhưng trung bình d của từng nghiên cứu lệch trái (độ lệch −0,26 tới −2,0): vài nghiên cứu
     có lợi ích lớn hơn hẳn, do các mô hình của một nghiên cứu học trên gần cùng một tập người.
     CI khoảng bao nằm hẳn dưới θ ở 0,4–2,1 % nghiên cứu, nằm hẳn trên θ ở 0,6–8,1 %. Xáo cột
     theo người giữa các nghiên cứu (giữ phân bố từng d_s, bỏ phụ thuộc) đưa hai tỷ lệ về
     1,8–3,3 % và 0,9–2,8 %, nên phần trượt thêm do phụ thuộc giữa các d_s.
   - Phía dưới là phía dẫn tới kết luận sai là PAT có lợi; phía này vẫn trong mức danh nghĩa với
     khoảng bao và Student t (≤ 2,5 %), nhưng không với percentile (tới 3,8 %) và BCa (tới
     4,3 %). Phía trên làm đánh giá thấp lợi ích, tức bảo thủ cho kết luận chính.
   - Khi ΔPAT không liên quan BP, thêm nó làm sai số tăng thật (θ = 0,012–0,050 mmHg); CI nằm
     dưới 0 ở ≤ 0,5 % nghiên cứu.
   - **Hệ quả:** giữ khoảng bao làm CI chính; báo độ phủ hai phía khoảng 92–95 % là giới hạn đã
     biết. Mọi số phụ thuộc mô hình đặc trưng tự đặt; chạy lại với tham số từ pilot.
9. **Hai baseline không dùng tín hiệu trong cùng các lượt LOSO (thêm 2026-11-12).** Cùng dữ
   liệu mô phỏng và các mô hình Ridge của kết quả 8 (summary mục "No-signal baselines"). θᴾ lấy
   từ cùng mô phỏng riêng 20 000 nghiên cứu như θ. Đơn vị mmHg, SBP.
   - **Trung bình theo pha thắng mọi mô hình ở mọi kịch bản.** MAE của nó 4,2–4,3 (M2 vừa) và
     4,4–4,5 (M2 rộng), so với zero-change 5,2 và 6,8, PPG-only 5,0–5,1 và 6,4–6,5, PPG + PAT
     4,7–5,2 và 5,4–6,6. θᴾ dương ở mọi dòng: 0,81–0,85 / 0,69–0,71 / 0,42–0,44 khi M2 vừa (PAT
     không liên quan, vừa, mạnh), 2,0–2,1 / 1,7 / 1,0–1,1 khi M2 rộng.
   - Vì vậy CI của dᴾ nằm dưới 0 ở ≤ 0,3 % nghiên cứu, kể cả khi mô hình đạt kết luận chính (tới
     92 % ở kịch bản mạnh nhất). CI nằm hẳn trên 0 ở 10–100 % nghiên cứu.
   - CI khoảng bao của dᴾ giữ mức: nằm hẳn dưới θᴾ ở 1,5–2,9 %, nằm hẳn trên ở 1,3–2,5 %.
   - Độ lệch hằng số kém zero-change 0,02–0,2 mmHg, vì mô phỏng không có độ lệch hệ thống giữa
     các phiên; nó chỉ có ích khi có độ lệch như vậy (như nhánh dao động kế của S4).
   - **Vì sao:** trong mô hình tự đặt, đặc trưng PPG chỉ theo BP rất yếu, HR chỉ đánh dấu M2 và
     với hệ số khác nhau giữa người, không gì đánh dấu M1, và Ridge không có hệ số chặn. Baseline
     theo pha thì biết đúng mức đổi trung bình của cả ba pha.
   - **Hệ quả:** nếu dᴾ là điều kiện của kết luận chính thì, dưới các giả định này, kết luận chính
     gần như không bao giờ đạt; đó là lý do giữ dᴾ là endpoint phụ bắt buộc. Kết quả cũng
     cho thấy vượt zero-change có thể còn rất xa mới vượt được mức đoán theo pha, nên quy tắc
     viết bài ở mục 7 là cần. Mọi số phụ thuộc mô hình đặc trưng tự đặt; chạy lại với tham số
     từ pilot.
10. **Endpoint phụ 10: cả hai nhánh Ridge có biến chỉ pha (thêm 2026-11-12).** Cùng dữ liệu và
    cùng các lượt LOSO (summary mục "PAT once the model knows the phase"); θᵂ lấy từ cùng mô
    phỏng riêng 20 000 nghiên cứu.
   - Có biến chỉ pha, MAE của hai nhánh xuống 4,1–4,6 mmHg, ngang trung bình theo pha (4,2–4,5);
     nhánh có PAT "strong" thấp hơn nó khoảng 0,1 mmHg.
   - **Phần lợi ích của PAT còn lại sau khi biết pha nhỏ hơn nhiều:** θᵂ = −0,02 tới −0,04 khi
     PAT "benefit" (θ không có biến chỉ pha: −0,09 tới −0,34), −0,13 tới −0,16 khi "strong" (θ:
     −0,37 tới −0,98). Trong mô hình tự đặt, phần lớn lợi ích của PAT ở d đến từ việc PAT theo
     mức đổi BP chung của từng pha.
   - CI nằm dưới 0 ở ≤ 2,4 % nghiên cứu khi "benefit" và 4,5–17 % khi "strong", so với 3–93 % của
     d. Endpoint này vì vậy chỉ để mô tả.
   - Khi PAT không liên quan BP: CI nằm dưới 0 ở ≤ 0,8 %, nằm hẳn dưới θᵂ ở ≤ 1,6 %; CI nằm hẳn
     trên 0 ở 12–25 %, tức thêm một đặc trưng nhiễu vào mô hình đã biết pha làm sai số tăng thấy
     được. Phía trên θᵂ trượt tới 12,5 % khi có hiệu ứng (bảo thủ, như kết quả 8).

**Lưới P2** (cùng summary, mục "P2 grid"): giữ mọi giả định khác, cho trung bình đáp ứng M2 đổi
từ 4 đến 15 mmHg SBP (2 đến 9 mmHg DBP), với 25 người × 2 phiên và 20 người × 3 phiên. Tỷ lệ đạt
kết luận chính ở mức 95 % theo thống kê P2:

| P2 SBP (mmHg) | 4 | 6 | 8 | 10 | 12 | 15 |
| --- | --- | --- | --- | --- | --- | --- |
| "benefit" | 0 % | 1 % | 4–5 % | 14–16 % | 33–37 % | 70–73 % |
| "strong" | 6–7 % | 17–18 % | 35–38 % | 64–66 % | 86–89 % | 98–99 % |

Không có mức P2 nào bảo đảm kết luận chính: xác suất phụ thuộc mạnh vào việc PAT giúp bao nhiêu,
mà điều này chưa biết trước pilot.

**P2/R3 (chốt 2026-11-12, đổi so với bản 2026-10-29 của protocol 6.5; protocol và kịch bản
bài báo đã sửa theo):**

- **Thống kê:** P2 ở pilot dùng trung vị qua người của ΔSBP **có dấu** ở lần cuff M2, so với
  trung bình M0 cùng buổi. Thống kê này đi theo đáp ứng M2, khác R3.
- **Ngưỡng:** **10 mmHg** làm mức báo động, không phải mức bảo đảm.
  - Ở mức 10 mmHg, ngay cả kịch bản PAT giúp mạnh cũng chỉ có khoảng hai phần ba khả năng đạt
    kết luận chính, còn kịch bản giúp vừa khoảng 15 % (số chạy lại 2026-11-10 với khoảng bao;
    bản trước ghi ba phần tư và dưới 25 %). Dưới 10 mmHg thì thấp hơn nữa.
  - Dưới ngưỡng thì báo thầy và rà lại nghiệm pháp (protocol 6.4, "Dự phòng") trước khi thu chính.
  - Con số 10 là lựa chọn dựa trên các kịch bản đã chạy, không suy ra được từ dữ liệu.
- **R3:** giữ làm chỉ số mô tả ở G4 kèm SD của ΔBP tham chiếu, không làm ngưỡng kích hoạt. Lý do:
  thống kê median |ΔSBP| trên mọi lần cuff phiên ≥ 2 gồm cả M0 các phiên sau, nên rất nhỏ ở người
  trẻ, và mô phỏng cho thấy không có ngưỡng nào của nó bảo đảm được kết luận chính; độ nhạy đã
  được phản ánh trong độ rộng CI.

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

- Bảng chính theo đầu ra: MAE, ME ± SD của sai số, cho zero-change, độ lệch hằng số, trung bình
  theo pha, PAT-only, PPG-only và PPG + PAT; trung bình d_s và d⁰_s, CI ở mức thật; trung bình
  dᴾ_s, CI 95 %; cách đọc theo δ. Thêm MAE và ME theo từng pha cho mọi dòng, vì giảm độ lệch
  thôi chưa đủ để nói mô hình theo được BP.
- Luôn báo SD của ΔBP tham chiếu và tỷ lệ |ΔBP| > 5 mmHg, gộp và theo nghiệm pháp.
- **Hình:** d_s theo người; phân bố ΔBP theo nghiệm pháp; Bland–Altman cho dữ liệu đo lặp (phương
  pháp LoA cho đo lặp, chờ chọn).
- Mọi kết quả phụ ghi là không xác nhận.

## 12. Kiểm soát thay đổi

- Mọi thay đổi sau khi khóa phải là một commit riêng có ngày và lý do, trước khi chạy vòng ngoài.
- Thay đổi sau khi đã chạy vòng ngoài thì tạo phiên bản mới và báo cả hai.
- Vòng ngoài chạy bằng một script ghi commit, hash dữ liệu, config, và từ chối chạy khi file
  này hay config chưa commit (như các runner B2, B5).

## 13. Các quyết định đã chốt và việc còn lại

Đã chốt 2026-11-12, báo thầy (nhóm tự quyết; mỗi mục có lý do và phương án đã cân nhắc ở mục
tương ứng):

1. Phương án A cho đa kiểm định (mục 6); không chọn B.
2. Quy tắc δ (mục 8); giá trị tính sau pilot theo đúng quy tắc.
3. Ridge với α = 1, không hệ số chặn, không vòng trong (mục 4).
4. 10 000 lượt bootstrap, seed cố định ghi trong commit khóa; CI chính là khoảng bao của
   bootstrap-t và Student t (mục 5); không chọn Student t riêng.
5. P2: ΔSBP có dấu của M2, ngưỡng báo động 10 mmHg; R3 chỉ để mô tả (mục 9).
6. Quy tắc chọn số người và phân bổ phiên sau pilot (mục 9).
7. Các endpoint phụ 1–11 (mục 3).
8. SQI v1 ([sqi_specification_v1.md](sqi_specification_v1.md)): cấu trúc cờ và cách dùng; ngưỡng
   khóa trên bản ghi G2.
9. Thang trọng số của Ridge (mục 4).
10. Hai baseline không dùng tín hiệu, endpoint phụ bắt buộc dᴾ (không phải điều kiện của kết luận
    chính) và cách dùng khi viết bài (mục 3, 4, 7; mục 9, kết quả 9).

Còn lại trước khi khóa (cập nhật 2026-11-12):

- ngưỡng SQI v1, khóa trên bản ghi G2;
- commit khóa SAP có ngày, trước buổi pilot đầu tiên, ghi seed bootstrap;
- sau pilot, trước thu chính: δ, số người, phân bổ phiên, theo quy tắc ở mục 8 và 9.

Đã xong: mô phỏng có huấn luyện Ridge thật trong LOSO và mô phỏng chung SBP và DBP (2026-11-11,
mục 9, kết quả 7 và 8); baseline không dùng tín hiệu mạnh hơn zero-change (2026-11-12, kết quả 9
và 10; [RQ](../research_questions_v0.1.md) mục 8).
