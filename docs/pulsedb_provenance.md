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
- Gói Kaggle **version 4** (cập nhật 2022-12-08). Huy tải ngày 2026-10-25 bằng
  Kaggle API (`kaggle` 2.2.5) vào `data/raw/pulsedb/` (ngoài Git); kích thước và
  SHA-256 ở mục 4. Không biết version của bản các notebook Tuần 3–4 đã dùng trên
  Kaggle.

## 2. Giấy phép

Dữ liệu PulseDB dẫn xuất từ VitalDB phân phối theo CC BY-NC-SA 4.0 (gói Kaggle
có `LICENSE.txt`, mục 4). Không commit
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
| `VitalDB_AAMI_Cal_Subset.mat` | `bc68fc239d3809f20cda01bb55eeae7aee88912f8143e0c4cde18d9c4384dcde` | Output cell 15 notebook EDA (Kaggle, kernel Python 3.11). Commit `acc8b8b` ghi cùng giá trị khi chạy `shasum -a 256 data/pulsedb_data/VitalDB_AAMI_Cal_Subset.mat` trên macOS | Lần tính trên Kaggle **không phải** phiên tạo CSV Tuần 3; cell tổng kết in lại giá trị gõ cứng. Lần tính trên macOS chưa có log lệnh, kích thước file hay version gói Kaggle đi kèm |
| `data/processed/linh_week03/pulsedb_manifest_1000.csv` | `ed630151680665cdc4ede92189880aec95ee54e35d8a3f14c81b918fc0eb9d60` | `configs/data/b0_pulsedb_validation.json`; tính lại ngày 2026-10-15 cho cùng giá trị | Bản sao `notebooks/pulsedb_manifest_1000.csv` có nội dung giống hệt và **đang được Git theo dõi** |

**Các file tải ngày 2026-10-25** (Kaggle version 4; `.mat` giải nén từ `.mat.zip`
tải về; kích thước `.mat` khớp danh sách file của Kaggle):

| File | Kích thước (byte) | SHA-256 | Vai trò |
| --- | ---: | --- | --- |
| `VitalDB_Train_Subset.mat` | 13.797.698.523 | `20f19685b67a17fff6673743114cb17345a959d02367553ceea3cf560b14d002` | Pool (mục 5) |
| `VitalDB_Train_Subset.mat.zip` | 13.405.647.245 | `99428ad60ab2e23c01311ded788225aa9d6c1a3ba5a62f22f35805fd3f3e9cec` | Bản tải về |
| `VitalDB_CalFree_Test_Subset.mat` | 1.706.947.648 | `f0dffa676987124cdca00d46ae88fd4d8bf7f6ac411e6cdb36b98ff8bcf4a00a` | Tập kiểm tra ngoài, chưa dùng |
| `VitalDB_CalFree_Test_Subset.mat.zip` | 1.658.731.199 | `8b53b6c98420108ca946e435783eddd22e9658664f2bbaa78f21f3fea882403e` | Bản tải về |
| `VitalDB_AAMI_Test_Subset.mat` | 19.806.481 | `af1c1444d03da58cd24e6d4c8eaad43c64f3d015bead9509256f30ac7744d0c9` | Chỉ để so hai reader (mục 6) |
| `VitalDB_AAMI_Test_Subset.mat.zip` | 19.216.849 | `570623681ea1be9967416c33fa814997ac499c6e8735bdb7394c8c42b3acc79f` | Bản tải về |
| `LICENSE.txt` | 20.849 | `1349a4b6148492b44f629e64eed676612e234fe9a839e4f3b277c1482c8849f1` | Giấy phép |

Ghi nhận để minh bạch: ngày 2026-10-25, lệnh kiểm cấu trúc HDF5 của CalFree (chạy
trước khi có reader mới) đã in 5 giá trị SBP đầu file. Không giá trị nào được dùng
cho quyết định hay mô hình nào; sau đó CalFree không được đọc lại.

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

Theo Bảng 4 của bài báo, bản VitalDB của AAMI Test có 116 người, khớp với 116
người trong file thực dùng. Phần VitalDB của Train có 1.293 người (cùng số người
với CalBased Test), của CalFree Test có 144 người.

**Hệ quả cho dự án (chưa khóa):**

- Chia train/val/test theo người bên trong `VitalDB_AAMI_Cal_Subset` là hợp lệ
  về mặt rò rỉ **giữa các tập của chính nhóm**.
- Mọi người trong pool này cũng có mặt trong `VitalDB_AAMI_Test_Subset`. Nếu sau
  này dùng AAMI Test hoặc gộp thêm subset khác, có nguy cơ trùng người với tập
  dùng để huấn luyện hoặc chọn mô hình.
- Vai trò của từng subset được chốt ngày 2026-10-24 (mục dưới). Ghi lại đúng nội
  dung đó vào trường `pool_decision` của config split trước khi chạy.

**Quyết định pool (Huy, 2026-10-24; chưa có file raw nào trên máy, chưa đọc nhãn
hay tín hiệu của subset nào):**

| Subset | Vai trò |
| --- | --- |
| `VitalDB_Train_Subset.mat` (1.293 người) | Pool để chia train/val/test, **lấy mẫu con 400 người** |
| `VitalDB_CalFree_Test_Subset.mat` (144 người) | Tập kiểm tra ngoài, không trùng người với Train |
| `VitalDB_CalBased_Test_Subset.mat` | Không dùng: cùng người với Train |
| `VitalDB_AAMI_Cal_Subset.mat`, `VitalDB_AAMI_Test_Subset.mat` | Không dùng cho split mới: notebook Tuần 3–4 đã chấm điểm test trên 100 trong 116 người của AAMI Cal |

- **Lấy mẫu con:** chỉ dựa vào trường `Subject` (không đọc SBP/DBP, nhân khẩu hay
  tín hiệu). Danh sách ID duy nhất được sắp xếp, hoán vị bằng seed **20261024**,
  lấy 400 ID đầu. Seed này tách khỏi seed 72 của bước chia train/val/test. Ghi N,
  seed, hash danh sách ID đã chọn và hash file raw vào config và report của split.
- **Lý do:** pool AAMI Cal đã bị lộ ở vai trò test; Train chưa bị chạm; 400 người
  cho khoảng 320/40/40 người theo tỉ lệ 0,8/0,1/0,1 và khoảng 4,3 GB float64, vừa
  RAM 15,7 GB của máy làm việc khi đọc từng phần.
- **Triển khai ngày 2026-10-25:** reader `h5py` đọc từng phần
  (`software/pulsedb/h5_reader.py`, đã so với reader `mat73` ở mục 6) và trường
  `subject_subsample` của builder split
  ([hướng dẫn split](protocol/run_pulsedb_split.md)). Kết quả trên file Train ở trên:
  pool có 465.480 dòng và 1.293 người (khớp Bảng 4 của bài báo). 400 người được chọn,
  mỗi người đúng 360 đoạn, tổng 144.000 dòng; SHA-256 danh sách ID đã chọn là
  `1f0580a149fc7c2591e952a377e68adf1de53e50e7a9e012a18ed4aa2b2269ea`. Split
  320/40/40 người (115.200/14.400/14.400 đoạn). Chạy hai lần
  (`data/processed/pulsedb_train400_split_run01`, `_run02`, ngoài Git) cho cùng
  `inventory.csv` SHA-256 `17d3a8c2aa7a7d5a304d219aaaabada10a696232d529a1b0e19788f5d1fb7c26`
  và `manifest.csv` SHA-256
  `257d9653d6d42de26b77c291de79031b77ad7f3d29c6365d2319940acbe07d36`. Không có
  ECG/PPG nào trùng giữa các split. Config:
  [pulsedb_train400_split.json](../configs/data/pulsedb_train400_split.json).

## 6. Cấu trúc tín hiệu, nhãn và đơn vị

- `Signals` có 3 kênh theo thứ tự reader đang dùng: 0 = ECG, 1 = PPG, 2 = ABP.
  Trước đây tài liệu ghi tên kênh là `ECG_F`, `PPG_F`, `ABP_Raw`. **Chưa xác
  minh** tên và thứ tự kênh với code tạo subset của PulseDB. Từ 2026-10-24,
  `build_pulsedb_split.py` tự kiểm trên các dòng **train** (`channel_order_check`,
  `channel-order-check-v0`): tương quan Pearson giữa cực đại từng kênh với SBP và
  cực tiểu với DBP; kênh 2 phải đạt ≥ 0,8 cả hai và cao nhất trong ba kênh, nếu không
  thì không tạo split. Giá trị ghi vào `report.json`. Ngưỡng lỏng: chỉ bắt kênh bị
  đảo, không chứng minh kênh đúng về đơn vị hay lọc.
- Mỗi đoạn dài 10 giây (bài báo) và có 1250 mẫu/kênh, nên tần số lấy mẫu suy ra
  là **125 Hz**. Bài báo (mục 2.2 "Record selection") ghi tín hiệu VitalDB được
  hạ tần số lấy mẫu từ 500 Hz xuống 125 Hz để khớp với MIMIC-III, đúng với giá
  trị suy ra từ shape. Phần text đã đọc (bản PMC9944565) không nêu phương pháp
  resample hay bộ lọc chống aliasing đã dùng.
- Đơn vị ECG/PPG: README PulseDB v2_0 có thêm tín hiệu "non-normalized"
  (`ECG_Record`, `PPG_Record`), gợi ý `ECG_F`/`PPG_F` đã chuẩn hóa. Vì vậy dự án
  coi ECG/PPG của Subset là **đơn vị tùy ý (a.u.)**, không phải mV. **Kiểm trên
  raw ngày 2026-10-25:** ECG và PPG đã được **chuẩn hóa min-max theo từng đoạn về
  [0, 1]**. Trên 200 dòng train lấy cách đều trong split 400 người, min của cả hai
  kênh đúng bằng 0 và max bằng 1 (sai khác tối đa 1 ulp) ở mọi dòng. Trên cả 115.200
  dòng train, min của ECG/PPG là hằng số (kiểm thứ tự kênh không tính được tương
  quan). ABP vẫn ở mmHg (cực đại từng đoạn 80–208 mmHg trên 200 dòng đó). Kiểm thứ
  tự kênh trên train đạt: ABP có r = 0,98 với SBP và 0,93 với DBP. Hệ quả: đặc
  trưng biên độ (`min`, `max`, `range`) của ECG/PPG không mang thông tin, và biên độ
  PPG tuyệt đối không dùng được trên PulseDB Subset.
- **Cấu trúc HDF5 thật** (kiểm ngày 2026-10-25, chỉ đọc metadata): khóa ngoài
  `#refs#` và `Subset`. Trong `Subset` có `Age`, `BMI`, `DBP`, `Gender`, `Height`,
  `SBP`, `Signals`, `Subject`, `Weight`, mỗi trường gắn `MATLAB_class`. Trường số có
  shape `(1, N)` kiểu float64. `Subject`/`Gender` là cell `(1, N)` gồm tham chiếu tới
  mảng char uint16 trong `#refs#`. `Signals` có shape HDF5 `(1250, 3, N)` float64,
  tức `(N, 3, 1250)` theo MATLAB. N bằng 465.480 (Train; chunk `Signals` (1250, 3, 2)
  gzip; `#refs#` có 100.010 mục), 57.600 (CalFree) và 666 (AAMI Test).
- **Reader `h5py` so với reader `mat73`** (`scripts/compare_pulsedb_readers.py`,
  2026-10-25, Python 3.11.7, numpy 1.26.4, h5py 3.16.0, mat73 0.65): trên AAMI Test
  (666 dòng, 116 người), 0 sai khác ở cả 11 trường của mọi dòng và ở
  `subject_ids()`. Dùng AAMI Test vì file nhỏ (vừa RAM cho `mat73`) và không thuộc
  split mới nào; không dùng CalFree để giữ nguyên tập kiểm tra ngoài; Train quá lớn
  cho `mat73`. Bố cục MATLAB khác (cell `(N, 1)`, file một dòng, ô rỗng, trường tùy
  chọn thiếu, ranh giới khối) được kiểm bằng file SYNTHETIC trong test.
- Nhãn `SBP`/`DBP` (mmHg): theo bài báo, là trung bình SBP/DBP từng nhịp trong
  đoạn, lấy từ đỉnh tâm thu và điểm chân của sóng ABP. Đây là nhãn từ ABP xâm
  lấn, không phải cuff.
- PulseDB đã sàng lọc chất lượng, trong đó loại đoạn có tương quan PPG–ABP
  dưới 0,9 sau khi căn độ trễ. Như vậy ABP đã tham gia vào việc **chọn đoạn**;
  cần ghi điều này khi diễn giải kết quả.
- Bài báo ghi MIMIC-III có lệch thời gian giữa các kênh tới 500 ms, còn VitalDB
  được đồng bộ. File đang dùng là VitalDB.
- Bộ lọc: mục 2.4.2 của bài báo ghi PPG được lọc bằng bộ lọc Chebyshev-II bậc
  4, dải [0,5, 8] Hz, trước khi đưa vào thuật toán Elgendi để tìm đỉnh tâm thu
  và các điểm chuyển (turning points). Mục 2.4.1 chỉ ghi R-peak ECG được tìm bằng
  Pan–Tompkins, không mô tả bộ lọc ECG riêng. Phần text đã đọc **không** nói bộ
  lọc Chebyshev-II là zero-phase hay causal, và không nói `PPG_F`/`ECG_F` trong
  file Subset có phải là tín hiệu đã qua bộ lọc này hay không. Vì vậy độ trễ do
  lọc của `ECG_F`/`PPG_F` vẫn **chưa xác định**, và PAT trên PulseDB vẫn cần
  kiểm chứng riêng (ví dụ đối chiếu với code tạo subset của PulseDB).
- Đơn vị nhân khẩu: `Age` năm, `Height` cm, `Weight` kg, `BMI` kg/m². Khi file
  không có trường chiều cao/cân nặng/BMI, reader trả `NaN`, không điền 0.

## 7. Định danh và giới hạn truy vết

- `Subject` có dạng `p<6 chữ số>_<hậu tố>`, ví dụ `p000238_1`. Bài báo và README
  không nêu ý nghĩa hậu tố, nhưng code tạo subset chính thức
  ([`Generate_Subsets.m`](https://github.com/pulselabteam/PulseDB/blob/main/Generate_Subsets.m),
  nhánh `main`, đọc ngày 2026-10-23) dùng 7 ký tự đầu làm mã người và ký tự cuối
  làm **nguồn**: `0` là MIMIC-III, `1` là VitalDB. Hậu tố không phải chỉ số bản
  ghi, nên **không cắt hậu tố** khi chia split. Trong một pool VitalDB, mọi ID phải
  có hậu tố `_1`, và split theo nguyên chuỗi tương đương split theo mã người. Không
  suy ra cùng tiền tố ở hai nguồn là cùng người. Trong pool 1.000 dòng, mọi ID đều
  có hậu tố `_1`; file AAMI Cal 70.212 dòng chưa được kiểm toàn bộ. **Pool Train
  (2026-10-25):** cả 465.480 dòng khớp mẫu `p\d{6}_[01]` và đều có hậu tố `_1`
  (`pool_subject_id_format` trong `report.json` của split).
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
6. Commit `acc8b8b` ghi đã đọc lại file `.mat`, chọn lại 1.000 đoạn theo quy tắc
   bước 2 và đối chiếu: `subject_id` và `sample_hash` khớp theo thứ tự ở cả
   1.000/1.000 dòng. Kết quả chỉ có dạng bảng trong tài liệu, chưa có log chạy.

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
phục vụ việc này.

**Quy tắc QC nhãn (Huy, 2026-10-24; khóa trước khi đọc nhãn của pool Train):**

- Chỉ loại nhãn **bất khả về vật lý**: DBP ≥ SBP (hiệu áp ≤ 0). Dòng bị loại khỏi cả
  fit lẫn chấm điểm, ở **mọi split**; inventory và manifest vẫn giữ đủ mọi dòng (luật
  bảo toàn của split v2), việc loại chỉ xảy ra ở bước mô hình.
- Không loại theo ngưỡng BP cao/thấp hay hiệu áp nhỏ (ví dụ dòng 265,6/258,5 mmHg ở
  trên vẫn được giữ), vì các ngưỡng đó chưa có nguồn và có thể loại cực trị thật.
- Report ghi số dòng bị loại theo từng split và phân bố hiệu áp trên train.
- Triển khai ngày 2026-10-25 trong `b3-pipeline-v1`
  ([run_b3_pulsedb.md](protocol/run_b3_pulsedb.md)); `b3-pipeline-v0` giữ hành vi
  cũ, không loại dòng nào. Quy tắc không áp cho dòng test, vì chúng không được chấm
  ở bước val.
- Kết quả trên split 400 người: **0 dòng** train và 0 dòng val có DBP ≥ SBP. Hiệu áp
  train (115.200 dòng): min 4,1; p01 28,3; p05 34,7; p50 51,1; p95 75,7; p99 90,4;
  max 141,3 mmHg. Train có SBP tối đa 286,6 và DBP tối đa 276,9 mmHg: các dòng này
  được giữ, vì quy tắc không có ngưỡng BP cao.

## 10. Chính sách dữ liệu

Không commit toàn bộ PulseDB hoặc file `.mat`. Git chỉ chứa code, tài liệu, test,
notebook và thông tin checksum/provenance. Ngày 2026-10-24 (Huy) gỡ khỏi Git hai
CSV của pool AAMI Cal: `notebooks/pulsedb_manifest_1000.csv` (nhãn SBP/DBP kèm ID
người, cả dòng test) và `notebooks/metrics_all_splits.csv` (MAE trên test). Pool này
không còn dùng cho split mới (mục 5). Lịch sử Git vẫn giữ hai file (commit `1f218eb`
và `acc8b8b`); lấy lại bằng
`git show 1f218eb:notebooks/pulsedb_manifest_1000.csv` khi cần chạy runner B0 lịch
sử. Hai notebook Tuần 3–4 vẫn tham chiếu các đường dẫn này và là tài liệu lịch sử.

## 11. Việc còn mở

- Xác định `ECG_F`/`PPG_F` đã qua bộ lọc nào và lọc zero-phase hay causal (mục
  6) trước khi tính PAT trên PulseDB.
- Đánh giá CalFree Test (tập kiểm tra ngoài) chỉ sau khi model được khóa, bằng
  script khóa riêng (chưa viết).
