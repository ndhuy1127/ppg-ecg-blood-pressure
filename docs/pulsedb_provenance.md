# Thông tin nguồn gốc dữ liệu PulseDB

## 1. Bộ dữ liệu

- **Tên bộ dữ liệu:** PulseDB
- **Phần dữ liệu sử dụng:** PulseDB Supplementary Subsets
- **Cơ sở dữ liệu nguồn:** VitalDB
- **Nền tảng phân phối:** Kaggle
- **Bộ dữ liệu Kaggle:** `weinanwangrutgers/pulsedb-balanced-training-and-testing`

## 2. Nguồn tham khảo

- **Kho mã nguồn chính thức của PulseDB:**  
  https://github.com/pulselabteam/PulseDB

- **Bài báo về PulseDB:**  
  https://doi.org/10.3389/fdgth.2022.1090854

- **Bộ dữ liệu trên Kaggle:**  
  https://doi.org/10.34740/KAGGLE/DS/2447469

## 3. Phiên bản dữ liệu

Kho chính thức của PulseDB hiện cung cấp phiên bản `v2_0`.

Dự án sử dụng các tập dữ liệu bổ sung được phân phối qua Kaggle và có liên kết với kho PulseDB chính thức.

Cần ghi nhận riêng phiên bản của bộ dữ liệu Kaggle đã tải xuống. Phiên bản của kho PulseDB chính thức và phiên bản của bộ dữ liệu Kaggle không nhất thiết giống nhau.

## 4. Giấy phép sử dụng dữ liệu

Dữ liệu PulseDB có nguồn gốc từ VitalDB được ghi nhận là phân phối theo giấy phép CC BY-NC-SA 4.0.

Trước khi chia sẻ hoặc phân phối lại dữ liệu, cần kiểm tra giấy phép và điều khoản áp dụng cho bản phân phối cụ thể.

Toàn bộ dữ liệu gốc không được đưa vào kho Git của dự án.

## 5. Các tệp dữ liệu sử dụng

Bộ dữ liệu Kaggle cung cấp các tệp:

- `VitalDB_Train_Subset.mat`
- `VitalDB_AAMI_Cal_Subset.mat`
- `VitalDB_AAMI_Test_Subset.mat`
- `VitalDB_CalFree_Test_Subset.mat`
- `VitalDB_CalBased_Test_Subset.mat`

**Tệp được sử dụng trong lần chạy pipeline hiện tại:**

`data/pulsedb_data/VitalDB_AAMI_Cal_Subset.mat`

Pipeline đọc tệp này và chọn 1.000 đoạn tín hiệu để thực nghiệm.

Tệp Manifest tương ứng:

`notebooks/pulsedb_manifest_1000.csv`

Manifest có tổng cộng 1.000 mẫu, được chia thành:

| Tập dữ liệu | Số mẫu |
|---|---:|
| Train – huấn luyện | 800 |
| Validation – kiểm định | 100 |
| Test – kiểm tra | 100 |
| **Tổng cộng** | **1.000** |

Việc chia tập được thực hiện theo `subject_id` nhằm ngăn cùng một đối tượng xuất hiện trong nhiều tập dữ liệu.

## 6. Kiểm tra tính toàn vẹn bằng SHA-256

Cần phân biệt hai loại kiểm tra: checksum của tệp dữ liệu gốc và hash của từng mẫu trong Manifest.

### 6.1. Checksum của tệp dữ liệu gốc

Sử dụng thuật toán SHA-256 để tạo checksum cho chính xác tệp `.mat` được sử dụng.

Trên macOS, chạy lệnh sau tại thư mục gốc của dự án:

```bash
shasum -a 256 \
  data/pulsedb_data/VitalDB_AAMI_Cal_Subset.mat
```

Ghi lại checksum thu được cùng tên tệp, kích thước tệp và phiên bản dữ liệu.

**Tệp dữ liệu:** `VitalDB_AAMI_Cal_Subset.mat`

**Thuật toán:** SHA-256

**Checksum:**

```text
bc68fc239d3809f20cda01bb55eeae7aee88912f8143e0c4cde18d9c4384dcde
```

Checksum được tạo trực tiếp từ tệp dữ liệu đang sử dụng trong dự án bằng lệnh `shasum -a 256` trên macOS.
### 6.2. Hash của các mẫu trong Manifest

Manifest có cột `sample_hash`. Hash của mỗi mẫu được tính từ thông tin metadata, SBP, DBP và các mảng tín hiệu ECG, PPG, ABP.

Kết quả đối chiếu đã thực hiện:

| Nội dung kiểm tra | Kết quả |
|---|---:|
| Số dòng Manifest | 1.000 |
| Số đoạn tín hiệu được chọn | 1.000 |
| `subject_id` khớp theo thứ tự | Có |
| Hash khớp theo thứ tự | Có |
| Số hash khớp | 1.000/1.000 |

Kết quả xác nhận cả 1.000 đoạn tín hiệu được chọn đều khớp với các dòng tương ứng trong Manifest theo quy trình hash đã triển khai.

Hash của từng mẫu dùng để xác minh tính nhất quán giữa dữ liệu và Manifest, không thay thế checksum SHA-256 của tệp `.mat` gốc.

## 7. Quy định quản lý dữ liệu

- Không commit toàn bộ bộ dữ liệu PulseDB vào kho Git.
- Chỉ lưu mã nguồn, tài liệu, kiểm thử, notebook, Manifest và thông tin nguồn gốc dữ liệu cần thiết.
- Ghi nhận nguồn dữ liệu, phiên bản, tên tệp và checksum để hỗ trợ tái lập thực nghiệm.
- Không phân phối lại dữ liệu gốc khi chưa xác minh giấy phép và điều khoản sử dụng.

## 8. Cấu trúc dữ liệu

Các trường dữ liệu được ghi nhận trong tập bổ sung gồm:

- `Subject`
- `Signals`
- `SBP`
- `DBP`
- `Age`
- `Gender`
- `Height`
- `Weight`
- `BMI`

Mảng `Signals` chứa ba kênh tín hiệu:

- Kênh 0: `ECG_F` – điện tâm đồ ECG
- Kênh 1: `PPG_F` – tín hiệu quang thể tích PPG
- Kênh 2: `ABP_Raw` – tín hiệu huyết áp động mạch ABP

Mỗi đoạn tín hiệu có 1.250 điểm dữ liệu trên mỗi kênh.

Cấu trúc dự kiến của mảng tín hiệu:

`(số_lượng_đoạn_tín_hiệu, 3, 1250)`

Với tần số lấy mẫu 125 Hz, mỗi đoạn tương ứng 10 giây tín hiệu.

## 9. Đơn vị đo

- `SBP`: mmHg – huyết áp tâm thu
- `DBP`: mmHg – huyết áp tâm trương
- `Age`: năm
- `Height`: cm
- `Weight`: kg
- `BMI`: kg/m²

`ECG_F`, `PPG_F` và `ABP_Raw` là các tín hiệu dạng sóng. Đơn vị biên độ và các bước tiền xử lý hoặc chuẩn hóa cần được xác minh từ tài liệu dữ liệu trước khi ghi cụ thể.

## 10. Mã định danh đối tượng

Mã định danh đối tượng được lưu trong trường `Subject`.

Ví dụ:

`p000001_1`

Reader chuyển trường `Subject` thành `subject_id`.

Manifest lưu `subject_id` cho từng mẫu. Bộ kiểm tra xác minh rằng không có đối tượng nào xuất hiện đồng thời trong các tập train, validation và test.
