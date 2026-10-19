# Nguồn gốc dữ liệu PulseDB

Tài liệu ghi nguồn, file thực dùng, checksum, cấu trúc, vai trò các subset và
giới hạn truy vết của dữ liệu PulseDB dùng trong dự án. Mỗi mục ghi rõ bằng
chứng: output notebook đã lưu trong repo, bài báo PulseDB, hoặc chưa xác minh.
PulseDB là dữ liệu công khai; nhãn của nó **không phải nhãn cuff** và không thay
bản ghi thiết bị của nhóm.

## 1. Dataset và nguồn

- Dataset: PulseDB, phần Supplementary Subsets dẫn xuất từ VitalDB.
- Phân phối: Kaggle `weinanwangrutgers/pulsedb-balanced-training-and-testing`
  (https://doi.org/10.34740/KAGGLE/DS/2447469).
- Repository chính thức: https://github.com/pulselabteam/PulseDB (hiện cung cấp
  bản `v2_0`).
- Bài báo: Wang W. et al., "PulseDB: A large, cleaned dataset based on MIMIC-III
  and VitalDB for benchmarking cuff-less blood pressure estimation methods",
  Frontiers in Digital Health, 2023, https://doi.org/10.3389/fdgth.2022.1090854.
- **Chưa ghi:** số version của gói Kaggle tại thời điểm tải. Cần bổ sung khi
  chạy lại để biết file có đổi giữa các lần chạy hay không.

## 2. Giấy phép

Dữ liệu PulseDB dẫn xuất từ VitalDB phân phối theo CC BY-NC-SA 4.0. Không commit
file `.mat` hay toàn bộ dataset vào Git.

## 3. File trong gói Kaggle và file thực dùng

Output cell 1 của `notebooks/week3-split-hash.ipynb` và cell 3 của
`notebooks/01_eda_and_visualization.ipynb` liệt kê 5 file trong
`/kaggle/input/datasets/weinanwangrutgers/pulsedb-balanced-training-and-testing/`:

- `VitalDB_AAMI_Cal_Subset.mat`
- `VitalDB_Train_Subset.mat`
- `VitalDB_AAMI_Test_Subset.mat`
- `VitalDB_CalFree_Test_Subset.mat`
- `VitalDB_CalBased_Test_Subset.mat`

Gói này **không có** các file Info hoặc Segment của PulseDB, nên không có trường
thời gian `T` hay chỉ số đoạn gốc (xem mục 7).

**File thực dùng ở cả hai notebook:** `VitalDB_AAMI_Cal_Subset.mat`. Bằng chứng:
cell 4 notebook EDA in đường dẫn file này; cell 3 notebook Tuần 3 đọc
`file_paths[0]`, mà output cell 1 cho thấy `file_paths[0]` là file này.

| Thuộc tính (từ output notebook) | Giá trị |
| --- | --- |
| Khóa cấp ngoài | `Subset` |
| Trường trong `Subset` | `Age`, `BMI`, `DBP`, `Gender`, `Height`, `SBP`, `Signals`, `Subject`, `Weight` |
| `Signals` | shape `(70212, 3, 1250)`, dtype `float64` |
| Số người (`Subject` khác nhau) | 116 |
| NaN trong 1.000 đoạn đầu | 0 ở cả ba kênh |

## 4. Checksum

| File | SHA-256 | Bằng chứng | Giới hạn |
| --- | --- | --- | --- |
| `VitalDB_AAMI_Cal_Subset.mat` | `bc68fc239d3809f20cda01bb55eeae7aee88912f8143e0c4cde18d9c4384dcde` | Output cell 15 notebook EDA (Kaggle, kernel Python 3.11) | Tính trong phiên chạy notebook EDA, **không phải** phiên tạo CSV Tuần 3; cell tổng kết in lại giá trị gõ cứng. Chỉ chứng minh hai lần chạy cùng đường dẫn Kaggle, chưa chứng minh cùng nội dung file |
| `data/processed/linh_week03/pulsedb_manifest_1000.csv` | `ed630151680665cdc4ede92189880aec95ee54e35d8a3f14c81b918fc0eb9d60` | `configs/data/b0_pulsedb_validation.json`; tính lại ngày 2026-10-15 cho cùng giá trị | Bản sao `notebooks/pulsedb_manifest_1000.csv` có nội dung giống hệt và **đang được Git theo dõi** |

Lần chạy split mới phải để `scripts/build_pulsedb_split.py` tự kiểm tra
SHA-256 raw trước và sau khi đọc (xem `docs/protocol/run_pulsedb_split.md`).

## 5. Vai trò các subset theo bài báo PulseDB

Theo bài báo (mục mô tả các subset), người tham gia chia thành ba nhóm:

| Subset | Nhóm người | Quan hệ |
| --- | --- | --- |
| Train | A | Dùng để huấn luyện |
| CalBased Test | A (cùng người với Train) | Các đoạn khác, không chồng lấn với Train |
| CalFree Test | B | Không trùng người với Train |
| AAMI Test | C | Đánh giá theo kiểu AAMI |
| AAMI Cal | C (cùng người với AAMI Test) | Các đoạn còn lại của cùng người, không chồng lấn với AAMI Test |

Bài báo ghi bản VitalDB của AAMI Test có 116 người, khớp với 116 người trong
file thực dùng. Phần VitalDB của Train có 1.293 người.

**Hệ quả cho dự án (chưa khóa):**

- Chia train/val/test theo người bên trong `VitalDB_AAMI_Cal_Subset` là hợp lệ
  về mặt rò rỉ **giữa các tập của chính nhóm**.
- Mọi người trong pool này cũng có mặt trong `VitalDB_AAMI_Test_Subset`. Nếu sau
  này dùng AAMI Test hoặc gộp thêm subset khác, có nguy cơ trùng người với tập
  dùng để huấn luyện hoặc chọn mô hình.
- Vai trò của từng subset (pool để chia, held-out, không dùng) **chưa
  chốt**. Phải ghi quyết định này vào trường `pool_decision` của config split
  trước khi chạy lại.

## 6. Cấu trúc tín hiệu, nhãn và đơn vị

- `Signals` có 3 kênh theo thứ tự reader đang dùng: 0 = ECG, 1 = PPG, 2 = ABP.
  Trước đây tài liệu ghi tên kênh là `ECG_F`, `PPG_F`, `ABP_Raw`. **Chưa xác
  minh** tên và thứ tự kênh với code tạo subset của PulseDB hay bằng kiểm tra
  định lượng trên raw. Cách kiểm tra đề xuất: trên một số đoạn, so cực đại/cực
  tiểu của kênh 2 với nhãn SBP/DBP; kênh ABP phải nằm trong cùng thang mmHg.
- Mỗi đoạn dài 10 giây (bài báo) và có 1250 mẫu/kênh, nên tần số lấy mẫu suy ra
  là **125 Hz**. Bài báo không nêu tốc độ này trong phần text đã đọc.
- Đơn vị ECG/PPG: README PulseDB v2_0 có thêm tín hiệu "non-normalized"
  (`ECG_Record`, `PPG_Record`), gợi ý `ECG_F`/`PPG_F` đã chuẩn hóa. Vì vậy dự án
  coi ECG/PPG của Subset là **đơn vị tùy ý (a.u.)**, không phải mV.
- Nhãn `SBP`/`DBP` (mmHg): theo bài báo, là trung bình SBP/DBP từng nhịp trong
  đoạn, lấy từ đỉnh tâm thu và điểm chân của sóng ABP. Đây là nhãn từ ABP xâm
  lấn, không phải cuff.
- PulseDB đã sàng lọc chất lượng, trong đó loại đoạn có tương quan PPG–ABP
  dưới 0,9 sau khi căn độ trễ. Như vậy ABP đã tham gia vào việc **chọn đoạn**;
  cần ghi điều này khi diễn giải kết quả.
- Bài báo ghi MIMIC-III có lệch thời gian giữa các kênh tới 500 ms, còn VitalDB
  được đồng bộ. File đang dùng là VitalDB. Độ trễ do bộ lọc của `ECG_F`/`PPG_F`
  chưa được xác định, nên PAT trên PulseDB vẫn cần kiểm chứng riêng.
- Đơn vị nhân khẩu: `Age` năm, `Height` cm, `Weight` kg, `BMI` kg/m². Khi file
  không có trường chiều cao/cân nặng/BMI, reader trả `NaN`, không điền 0.

## 7. Định danh và giới hạn truy vết

- `Subject` có dạng `p<6 chữ số>_<hậu tố>`, ví dụ `p000238_1`. Ý nghĩa hậu tố
  không được nêu trong bài báo hay README. Trong pool 1.000 dòng, mọi ID đều có
  hậu tố `_1`. **Chưa kiểm tra** toàn file 70.212 dòng: nếu cùng một tiền tố có
  nhiều hậu tố, split theo nguyên chuỗi có thể đặt cùng một người vào hai tập.
  Khi chạy lại trên raw, cần đếm số tiền tố khác nhau so với số ID khác nhau.
- File Subset không có timestamp, phiên đo hay chỉ số đoạn gốc. Đơn vị truy vết
  tốt nhất hiện có là **(SHA-256 file, chỉ số dòng trong file)**, chính là
  `sample_id = source_sha256:raw_index` của split v2. Không suy ra thứ tự thời
  gian từ thứ tự dòng.
- PulseDB v2_0 có file Info/Segment với trường thời gian `T` và chỉ số đoạn gốc,
  nhưng gói Kaggle đang dùng không có các file này. Muốn đánh giá B1 hay theo
  thời gian thì phải lấy thêm các file đó từ nguồn chính thức. Không được dựng
  thời gian thay thế.

## 8. Pool 1.000 đoạn lịch sử (Tuần 3)

Notebook `notebooks/week3-split-hash.ipynb` tạo
`pulsedb_manifest_1000.csv` như sau (theo code và output đã lưu):

1. Đọc toàn bộ `VitalDB_AAMI_Cal_Subset.mat` (70.212 đoạn, 116 người).
2. Duyệt theo thứ tự dòng, lấy tối đa 10 đoạn đầu của mỗi người; giữ người đủ
   10 đoạn cho tới khi đạt 1.000 đoạn, tức 100 người.
3. Chia theo người: sắp xếp ID, `random.seed(72)`, xáo trộn, tỷ lệ 0,8/0,1/0,1,
   được 80/10/10 người (800/100/100 đoạn). Đã tái hiện đúng phép gán này từ CSV.
4. `sample_id` là thứ tự sau khi chọn (0–999), **không phải** chỉ số dòng trong
   `.mat`.
5. `sample_hash` băm metadata dạng chuỗi (ID, giới, tuổi, chiều cao, cân nặng,
   BMI, SBP, DBP) cùng byte của ba kênh. Nó phát hiện được bản sao giống hệt toàn
   bộ, nhưng không phát hiện được hai đoạn cùng waveform mà khác metadata hoặc
   nhãn. Split v2 bổ sung `waveform_hash` cho trường hợp này.

Giới hạn của notebook:

- Reader được import từ dataset Kaggle `bosuacuoi/pulsedb-reader`, không phải
  một commit trong repo. Phiên bản code đã dùng không truy được.
- Cột `source` được gõ cứng thành `VitalDB_AAMI_Cal_Subset.mat` thay vì lấy từ
  file thực đọc. Lần chạy đã lưu khớp, nhưng cách làm này phụ thuộc thứ tự
  `os.walk`.
- Thứ tự `execution_count` không tăng dần (ví dụ cell 17 = 70, cell 18 = 68,
  cell 19 = 63), nên notebook không được chạy lại liền mạch từ kernel sạch.
- Notebook EDA Tuần 2 khảo sát 1.000 dòng đầu file, chỉ gồm **2 người**, nên
  không đại diện cho pool.

Hệ quả: CSV này là bằng chứng lịch sử, không truy về được dòng raw, và **không
tương thích** với validator split v2 (cần inventory). Split v2 trên cùng file giữ
đủ 116 người, nên phép gán người vào tập sẽ khác CSV dù cùng seed 72. Kết quả B0
Tuần 3 trên CSV vì vậy không so sánh trực tiếp được với mô hình chạy trên
manifest v2; B0 phải chạy lại trên cùng manifest.

## 9. Quan sát nhãn cần quy tắc QC

Trong CSV lịch sử, dòng `sample_id = 216` (tập train) có SBP 265,6 / DBP 258,5
mmHg, pulse pressure khoảng 7 mmHg. Đây nhiều khả năng là artifact ABP, nhưng
**chưa kiểm tra waveform**. Dòng này được giữ nguyên. Quy tắc QC cho nhãn (ví dụ
ngưỡng pulse pressure, DBP ≥ SBP) phải được định nghĩa trước, chỉ dựa trên
train/validation, và chỉ gắn cờ. `PulseValidator` đã xuất các cột
`pulse_pressure`, `dbp_ge_sbp`, `label_nonfinite` và `waveform_duplicate_of` để
phục vụ việc này. Ngưỡng chưa được chốt.

## 10. Chính sách dữ liệu

Không commit toàn bộ PulseDB hoặc file `.mat`. Git chỉ chứa code, tài liệu, test,
notebook và thông tin checksum/provenance. Việc có giữ CSV nhãn kèm ID người
(`notebooks/pulsedb_manifest_1000.csv`) trong Git hay không **chưa quyết
định**; chưa xóa file này.

## 11. Việc còn mở

- Chốt vai trò từng subset (mục 5) và ghi vào `pool_decision`.
- Chạy `scripts/build_pulsedb_split.py` hai lần trên raw đã chốt, bằng reader của
  repo, và đối chiếu SHA-256 inventory/manifest.
- Kiểm tra thứ tự kênh và ý nghĩa hậu tố ID (mục 6, 7) trên raw.
- Chốt quy tắc QC nhãn (mục 9) trước khi huấn luyện mô hình.
- Ghi số version của gói Kaggle.
