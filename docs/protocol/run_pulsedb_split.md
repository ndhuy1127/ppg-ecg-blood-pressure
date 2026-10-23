# Split PulseDB có inventory — bản sửa phần Linh Tuần 3

## Phạm vi và ảnh hưởng

Pipeline mới `software/data_io/split_manifest.py` và
`scripts/build_pulsedb_split.py` kế thừa `software/pulsedb/reader.py` trong repo.
Không dùng reader import từ dataset Kaggle riêng, không chọn `file_paths[0]`.
CSV/notebook cũ và cấu hình B0 đang dùng **không bị sửa hoặc thay thế**.

Schema hiện tại là `pulsedb-split-v2`, không tương đương hash notebook lịch sử
hoặc bản v1. V2 thêm `waveform_hash` không chứa ID/nhãn và schema đóng để không
làm mất metadata khi xuất CSV. Config v1 bị từ chối; không chỉ đổi tên version
trên CSV cũ: phải tạo lại inventory/hash từ waveform. Dữ liệu bàn giao cũ giữ nguyên.
Pipeline giữ **mọi dòng reader trả về** của một file được chỉ định; không áp dụng
quy tắc chọn 10 đoạn/người hoặc pool 1.000 đoạn của notebook cũ. Vì vậy không
coi output mới là lần tái tạo pool cũ. Pool thực nghiệm phải
chốt trước khi chạy; không tái chia holdout gốc để tuyên bố đánh giá PulseDB.
Không dùng nhãn test để chọn tỷ lệ, seed, model hoặc tiêu chí loại.

## Chọn pool và vai trò subset

Gói Kaggle có 5 subset VitalDB. Theo bài báo PulseDB, Train và CalBased Test là
cùng người; AAMI Test và AAMI Cal là cùng người (nhóm C); CalFree Test là nhóm
người riêng. CSV lịch sử dùng `VitalDB_AAMI_Cal_Subset.mat` (116 người, đều có
mặt trong AAMI Test). Chi tiết và bằng chứng: [provenance PulseDB](../pulsedb_provenance.md).

Trước khi chạy, trường `pool_decision` phải ghi rõ:

- file nào là pool để chia train/val/test;
- subset nào là held-out bên ngoài và subset nào **không được dùng** ở bất kỳ
  bước nào vì trùng người với pool.

Không chọn pool, seed hay tỷ lệ dựa trên kết quả mô hình. Quy tắc QC nhãn (ví dụ
pulse pressure bất thường) được chốt riêng và chỉ gắn cờ, không xóa dòng khỏi
inventory.

## Config đầu vào

Lưu JSON cục bộ ngoài Git, ví dụ
`D:\ppg-ecg-blood-pressure\data\processed\linh_split_config.json`.
Không có config mặc định và không bịa checksum. JSON phải có
đúng các trường sau, tất cả chuỗi phải không rỗng:

| Trường | Giá trị / ý nghĩa |
| --- | --- |
| `schema_version` | `pulsedb-split-v2` |
| `input_path` | File MAT cụ thể; đường dẫn tương đối tính từ thư mục config |
| `input_sha256` | SHA-256 lowercase của đúng file raw, 64 ký tự |
| `source` | Tên file/nguồn thật; không hard-code nguồn khác file đã chọn |
| `source_version` | Phiên bản bản dữ liệu thực dùng |
| `license`, `permission_basis` | Điều khoản và bằng chứng quyền dùng đã kiểm tra |
| `pool_decision` | Quyết định đã chốt về pool và quan hệ với holdout có sẵn |
| `subject_identity_review` | Kết quả kiểm tra ý nghĩa ID/alias và giới hạn còn lại |
| `unit` | `mmHg` |
| `seed` | Số nguyên; 72 là seed lịch sử, chỉ dùng nếu quyết định giữ seed đó |
| `ratios` | Ba tỷ lệ dương tổng bằng 1, thứ tự train/val/test; 0.8/0.1/0.1 là phương án lịch sử |

Các mô tả quyền dùng/pool/ID là khai báo cần người kiểm tra, **không phải chứng
nhận tự động**. Có thể tính checksum tại máy được phép giữ dataset bằng
`Get-FileHash -Algorithm SHA256`, rồi ghi giá trị lowercase vào config.
Không tự tải dataset hoặc commit đường dẫn/metadata nhạy cảm.

## Chạy và kiểm tra tái lập

Dùng môi trường đã cài theo repo, không cài dependency trong lúc chạy:

```powershell
& 'D:\ppg-ecg-blood-pressure\.venv\Scripts\python.exe' -B 'D:\ppg-ecg-blood-pressure\scripts\build_pulsedb_split.py' --config 'D:\ppg-ecg-blood-pressure\data\processed\linh_split_config.json' --output 'D:\ppg-ecg-blood-pressure\data\processed\linh_split_run_01'
```

Chạy lại với cùng config/raw/code/môi trường và output mới `linh_split_run_02`.
So sánh SHA-256 `manifest.csv` và `inventory.csv`; script từ chối thư mục output
đã tồn tại. Terminal chỉ in hash và số người/đoạn, không in ID cá nhân.
Raw được hash trước/sau đọc; checksum sai hoặc raw thay đổi thì dừng.
Reader hiện nạp file vào RAM; chưa có streaming và không nên chạy file lớn trên
máy thiếu bộ nhớ. Chạy tại môi trường dữ liệu được phép (ví dụ Kaggle) nếu cần.

Output gồm:

- `inventory.csv`: mọi mẫu trước split, để đối chiếu độc lập với manifest.
- `manifest.csv`: inventory cộng split; sort theo checksum nguồn và raw index.
- `config.json`: bản config đã dùng; chỉ lưu nơi nội bộ được phép.
- `report.json`: hash raw/config/inventory/manifest, commit, trạng thái dirty,
  hash code (`code_sha256_lf`, tính trên nội dung LF như blob Git), phiên bản
  Python/dependency, số người/đoạn mỗi split, phân bố BP **chỉ của train và val**
  (`split_summary.test.bp` là `null`, để nhãn test không được xem trước khi có
  model khóa) và giới hạn.

`sample_id = source_sha256:raw_index`; `raw_index` là dòng zero-based trong file,
**không phải record/session/timestamp được suy đoán**. Hash nội dung dùng JSON
có version cho ID/nhãn và waveform float64 little-endian, channel/shape rõ ràng.
Đổi dtype nhưng giữ đúng giá trị biểu diễn cho cùng hash; không hứa phục hồi
giá trị đã mất do làm tròn float32. Không hash tuổi/giới khi thiếu metadata.
Integer waveform không biểu diễn chính xác bằng float64 bị từ chối, không âm
thầm làm tròn (ví dụ `2**53 + 1`). Integer lớn nhưng biểu diễn chính xác vẫn được
chấp nhận. Quy ước hash/CSV v2 không đổi cho dữ liệu đã được hỗ trợ chính xác.
`sample_hash` kiểm tra ID/nhãn và waveform; `waveform_hash` chỉ chứa waveform,
channel/shape và version, độc lập ID/nhãn/nguồn. Waveform giống hệt khác split
làm pipeline dừng để kiểm tra thủ công, không tự xóa mẫu hoặc suy ra hai ID là cùng người.
Hash này không phát hiện cửa sổ chồng lấn một phần, gần giống hoặc thay cách lọc.

Từ 2026-10-24 `build_pulsedb_split.py` còn từ chối tạo split (không ghi output) khi:

- **ECG/PPG giống hệt ở hai split** (`predictor_hash`: chỉ ECG và PPG, không ABP,
  nhãn hay ID; `waveform_hash` gồm cả ABP nên không bắt được trường hợp này). Bản sao
  trong cùng một split chỉ được đếm. Cả hai số ghi ở `report.json`
  (`predictor_duplicates`); `predictor_hash` không nằm trong manifest, schema
  `pulsedb-split-v2` không đổi.
- **Kiểm thứ tự kênh trên train không đạt** (`channel_order_check`, xem
  [provenance](../pulsedb_provenance.md) mục 6); kết quả ghi ở `channel_order_check`
  của report.

## Hợp đồng validation

`validate_manifest(manifest, inventory)` trả `True` khi đạt, còn lỗi thì raise
`ValueError`; không chỉ in PASS/FAIL. Inventory là bắt buộc. Validator kiểm tra
đủ mẫu, không thêm/trùng dòng, nguồn/raw index/ID/hash/nhãn không bị sửa và không
giao subject/sample hash/waveform hash/record/window giữa split. Không tự xóa đoạn vì nhãn giống nhau;
content hash giống nhau trong cùng split được giữ nguyên.

`make_manifest()` sort ID trước shuffle bằng RNG cục bộ, không ảnh hưởng global
random state; yêu cầu đủ người để cả ba split không rỗng. Số người train và val
là `floor(N × tỷ lệ)` tính bằng phân số thập phân chính xác, phần dư thuộc test
(ví dụ N = 116 với 0.8/0.1/0.1 cho 92/11/13). Với 0.8/0.1/0.1 kết quả giống phép
tính float cũ cho mọi N ≤ 20.000; với tỷ lệ như 0.7 thì float cũ có thể thiếu một
người (`int(90 × 0.7) = 62`). Hiện chỉ cho một nguồn
và một checksum; nhiều nguồn bị từ chối cho đến khi có identity mapping đã kiểm chứng.

API `build_inventory(..., record_ids=...)` nhận record metadata thật phủ đủ dòng,
giữ nhóm record qua validator; nếu record chứa nhiều subject chia khác split,
pipeline dừng thay vì tự đổi group/split. CLI hiện chưa nhận record metadata.
Các cột tùy chọn được hỗ trợ là `record_id` và `window_id` (chuỗi không rỗng).
Có thể bổ sung `window_id` thật vào inventory qua API trước split. Khóa cửa sổ
được kiểm tra trong nguồn/record nếu có; không có record thì trong nguồn.
Cả hai cột được giữ khi xuất CSV theo thứ tự cố định. Cột khác bị từ chối ở
validation và serialization, không âm thầm bỏ; mở rộng phải tăng version schema.
Đọc lại CSV bằng `read_manifest_bytes(path.read_bytes())` trong module split:
hàm giữ cột định danh/nguồn/hash/split là chuỗi, giữ số 0 đầu và token `NA`,
`N/A`, `NULL` thay vì suy thành missing; BP dùng float round-trip, raw index là
integer. Missing ID vẫn bị từ chối, không bù bằng ID tự tạo. Hàm đọc kiểm tra
schema/dòng và split, không thay đối chiếu inventory/leakage. Không dùng
`pd.read_csv()` mặc định để nghiệm thu định danh. `manifest_bytes()` cũng từ
chối split ngoài train/val/test hoặc missing; nó không tự chứng minh bảo toàn.
Inventory phải được bảo vệ/truy vết bằng hash raw và code; validator
không phát hiện được nếu cả inventory và manifest bị thay giả đồng thời.

## Test và việc còn mở

```powershell
& 'D:\ppg-ecg-blood-pressure\.venv\Scripts\python.exe' -B -m pytest -q -p no:cacheprovider 'D:\ppg-ecg-blood-pressure\tests\test_split_manifest.py'
```

Test chỉ dùng SYNTHETIC, gọi validator thật với mất/thêm/trùng mẫu, leakage,
ID/split/hash lỗi, thay nhãn, waveform trùng khác ID/nhãn, metadata round-trip;
kiểm tra reader repo qua mock MAT loader, hash,
sort, thống kê, tái chạy, checksum và không ghi đè output. Không chứng minh
nguồn raw, ID người, record/cửa sổ gốc hoặc PulseDB đã được nghiệm thu.

Còn cần config/pool đã chốt, quyền dùng/checksum thật, chạy
raw hai lần, đối chiếu số dòng raw-reader-inventory và record/alias nếu có.
Thiếu record metadata phải ghi giới hạn; không tạo ID người hay timestamp giả.
Chưa có chronology/calibration thì chưa đánh giá B1/cross-session/DeltaBP.
Không có preprocessing học tham số trong pipeline này. Mọi bổ sung fit sau này
phải chỉ dùng train. Cần CI Python 3.11 đạt trước nghiệm thu chung.