# Tests — kiểm tra code bằng dữ liệu nhỏ

Các file `test_*.py` chứa hàm kiểm tra được pytest gọi, không phải chương trình
demo để bấm Run Python File và xem metrics. Fixture là dữ liệu nhỏ do code tạo;
không có dataset thật hoặc dữ liệu người tham gia trong những test bên dưới.

## Mỗi file kiểm tra gì

| File | Nội dung kiểm tra | Dữ liệu sử dụng |
| --- | --- | --- |
| [test_week_03_baselines.py](test_week_03_baselines.py) | B0/B1 đúng hằng số, thay nhãn evaluation không đổi dự đoán, B1 từ chối người chưa hiệu chuẩn, input lỗi và state model | Nhãn BP và ID giả lập, kể cả input lỗi có chủ đích |
| [test_bp_metrics.py](test_bp_metrics.py) | MAE/bias/SD khớp tính tay; weighting theo mẫu/người, trường hợp một mẫu, input lỗi, demo tái lập và chạy trực tiếp | Mảng số tự tạo; subprocess chạy demo trong isolated mode từ `scripts/` |
| [test_smoke.py](test_smoke.py) | Import package, cấu trúc thư mục và phép tính NumPy | Mảng `[1.0, 2.0, 3.0, 4.0]`, đường dẫn package |
| [test_pulsedb.py](test_pulsedb.py) | Reader: file thiếu, sai số kênh, thứ tự kênh/dòng, trường bắt buộc/tùy chọn thiếu (NaN, không điền 0), độ dài trường, file một đoạn, gender M/F/lạ/thiếu, cell array dạng list, Subject nhiều giá trị, `limit`. Validator: waveform trùng, nhãn bất thường, tuổi thiếu, lệch độ dài kênh, token thiếu ID dùng chung với split | File tạm rỗng; mock `mat73.loadmat` trả Subset SYNTHETIC |
| [test_b0_pulsedb_csv.py](test_b0_pulsedb_csv.py) | Runner B0 trên CSV: fit chỉ trên train và metrics val tính tay, từ chối giao người/hash/waveform giữa split, nhãn val lỗi, thiếu split/header, config mặc định tương đối repo và yêu cầu xác nhận đơn vị | CSV nhãn SYNTHETIC |
| [test_split_manifest.py](test_split_manifest.py) | Validator đối chiếu inventory từ chối mất/thêm/trùng mẫu và leakage; hash/sort/tái lập; runner kế thừa reader và không ghi đè | SYNTHETIC, MAT loader mock, output trong thư mục tạm |
| [test_b3_pipeline.py](test_b3_pipeline.py) | Đặc trưng khớp tính tay và không đọc ABP/nhãn; B3 tái lập; pipeline từ chối leakage/hash sai/thiếu dòng/raw khác inventory; thay nhãn val/test hoặc waveform test không đổi dự đoán; runner tái lập và không ghi đè | Chỉ SYNTHETIC `SYN_*`; reader mock, output trong thư mục tạm |
| [test_week04_features.py](test_week04_features.py) | Mốc R/foot và PAT trên fixture giải tích nhiều fs, cờ SQI, nhịp sát biên không bị tính là không ghép, độ lệch foot của lọc zero-phase, timestamp/masked/gaps, provenance fixture | Fixture SYNTHETIC từ `scripts/demo_week04_huy.py` |
| [test_motion_sqi.py](test_motion_sqi.py) | `motion-sqi-v0`: nghỉ; cú giật 0,2–0,5 s bị bắt dù P95 cả cửa sổ bỏ sót; spike đơn không phải chuyển động; xoay chậm chỉ gyro bắt; thiếu bias không bao giờ cho `no_motion_detected`; mất mẫu, bão hòa, cửa sổ < 1 s là `not_evaluable`; bias gyro từ đoạn nghỉ và các lý do từ chối; config/đầu vào sai | Chỉ SYNTHETIC; kiểm code, không phải độ nhạy phát hiện trên người |
| [test_week05_fiducials.py](test_week05_fiducials.py) | Phương pháp mốc Tuần 5 (R ở 125/500 Hz, nội suy dưới mẫu, đoạn phẳng, kênh bị loại), PAT gắn nhãn chứ không xóa, quy tắc MAD, ghép một–một, vùng review, từ chối split test và đáp án SYNTHETIC, provenance và không ghi đè của script, `annotate` | Chỉ SYNTHETIC `SYN_*`; output trong thư mục tạm |
| [test_subject_bootstrap.py](test_subject_bootstrap.py) | Bootstrap theo người: cluster lặp, cùng draws cho mọi model, trường hợp ít người/suy biến, bảng dự đoán đối chiếu manifest | ID và dự đoán SYNTHETIC |
| [test_check_environment.py](test_check_environment.py) | So sánh `requires-python` và pin của `scripts/check_environment.py` | Chuỗi requirement tự tạo |
| [test_packet_simulation.py](test_packet_simulation.py) | Sáu case packet, decoder validation, dữ liệu/timeline/gap/offset, tái lập và CLI | Chỉ SYNTHETIC; config và expected fixture, output tạm |
| [test_firmware_packet_kat.py](test_firmware_packet_kat.py) | Known-answer V0.2 của encoder firmware (`firmware/include/packet_kat.h`: CRC `"123456789"`, packet ECG 50 byte có `VERSION = 2` và `STATUS` bit 4, 8, packet `0xD1` 142 byte có word hash bit 31) khớp cách dựng độc lập bằng `struct`/`binascii.crc_hqx` và `packet_wire.py`; `SYNC`, `VERSION = 2`, mọi mã kênh V0.2, tên bit `STATUS` 0–8, giới hạn 32 mẫu, hằng `0xD1` trong `packet_wire.h` khớp codec. Không biên dịch C | `tests/fixtures/packet_v3_expected.json` (CRC, so trường với packet mẫu V0.1), header C của firmware |
| [test_firmware_c_encoder.py](test_firmware_c_encoder.py) | Biên dịch `firmware/app/packet_wire.c` với harness C sinh trong thư mục tạm, chạy `pkt_self_test` (phép tự kiểm lúc khởi động), 303 packet V0.2 ngẫu nhiên seed 20261024 (N = 1–32, mọi mã kênh, `STATUS` 0–0x1FF, dữ liệu ở biên int32, IMU ở biên int16) và 4 packet biên (mọi trường header bằng 0 hoặc bằng giá trị lớn nhất, `T_FIRST_US` âm thì về 0): byte trùng `encode_packet`; N = 0, N = 33 hoặc bộ đệm thiếu thì trả 0 và không ghi gì. 200 payload `0xD1` (seed 61, hash có word bit 31, chuỗi ASCII 0–31 byte) trùng `device_info_data`; chuỗi 32 byte hoặc không phải ASCII thì trả lỗi và không ghi gì | Cần trình biên dịch C (`$CC`, `cc`, `gcc`, `clang`); không có thì skip, build/chạy lỗi thì fail. Không kiểm ISR, task, USB, phần cứng |
| [test_firmware_imu_plan.py](test_firmware_imu_plan.py) | Biên dịch `firmware/app/imu_plan.c` (cùng `packet_wire.c`) với harness C: công thức neo lại V0.2 mục 5 khớp bảng đáp án và 400 bộ ngẫu nhiên (seed 24) của `reanchor_index` trong simulator; cách chia phần 1–170 frame khớp `backlog_chunks`; kịch bản tay theo spec (đầy, đầy hai lần liền, đọc lỗi, chưa có mốc tin cậy, 0 frame, không đủ chỗ); dòng thời gian BMI270 giả 40 s có dừng đọc 500 ms và 2 500 ms đi qua logger: chỉ số neo lại bằng chỉ số thật, logger chỉ báo 6 `sample_index_reanchored`, mọi `DATA` khớp chỉ số | Cần trình biên dịch C như dòng trên; chỉ SYNTHETIC, không có MCU, task hay BMI270 |
| [test_firmware_samp_map.py](test_firmware_samp_map.py) | Biên dịch `firmware/app/samp_map.c` với harness C có bảng cạnh đánh số như callback capture: packet hợp lệ lấy cạnh của mẫu cuối; packet đầu cần cạnh 0; xung mất (khoảng dài), xung thừa (khoảng ngắn), mất một cộng thừa một (đủ số lượng vẫn bị bắt), cạnh chưa tới hoặc đã rời bộ đệm, cạnh của mẫu cuối muộn hơn hạn chờ 1 µs, chỉ số không liền, biên dung sai 1 931–1 975 µs, FIFO tràn; ở `LỖI` thì giữ và đếm nguyên nhân một lần; chính sách khởi động lại 1 s / 10 s. Dòng thời gian ECG giả 40 s với lỗi như env `samp_faults` qua logger: 4 lần neo lại, chỉ 4 `sample_index_reanchored`, `anchor_sources` khớp bộ đếm (vòng đọc là bản Python của `ecg_reader_task`: không kiểm trình tự dừng/khởi động lại bằng C, vòng chờ hay bộ đệm 64 ô) | Cần trình biên dịch C; chỉ SYNTHETIC, không có MCU, capture hay MAX30001 |
| [test_firmware_stream_compat.py](test_firmware_stream_compat.py) | Logger nhận luồng 10 phút dựng theo quy ước firmware khung V0.2 (chữ ROM đầu luồng, `VERSION = 2`, ECG/PPG/IMU giả, PPG ba khe và IMU sáu trục chung mốc neo, sự kiện t0, `0xD1` mỗi 10 s, `SEQ` gán lúc gửi, tràn hàng đợi và USB timeout): chỉ có issue đã cài, 100 266 packet và 1 027 192 mẫu đúng công thức `DATA`, 60 packet `0xD1` hợp lệ; bit 1 chuyển sang packet kế giải thích khoảng mất 48 mẫu; bit 5 chuyển sang packet kế giữ ranh giới neo lại (không chuyển thì logger báo nhầm số mẫu mất đã biết); `0xD1` bị bỏ ở hàng đợi được đếm; task PPG chốt trễ 12 ms mỗi 10 s (như env `ppg_delay`) đọc 10 mẫu và logger nhận đủ | Chỉ SYNTHETIC, dựng bằng `encode_packet`; không có MCU |
| [test_packet_logger.py](test_packet_logger.py) | CRC-16/CCITT-FALSE known-answer và oracle `binascii`; packet ghép tay; 13 case `synthetic-packet-v3`; `T_FIRST_US`; chia đoạn byte bất kỳ; rác/`SYNC` giả, không nhảy theo độ dài khai báo, một packet hỏng là một lỗi, đuôi cụt/`0xA5` lẻ, header vô lý; xung đột, mất liền nhiều packet, tràn 2³², index nhảy/lùi/vượt 32 mẫu mỗi packet vắng, neo lại lùi (`chain_id`), `FS = 0`, dữ liệu ngoài dải, bit STATUS dự trữ; anchor không tăng, anchor đầu/cuối sai, bước nhảy kéo dài, drift ±3 % qua khoảng mất, quy tắc `0xC1`; không báo offset cho `DEVICE`; metadata/config sai; record/replay cùng hash, mở exclusive, manifest ghi sau cùng, CLI | Chỉ SYNTHETIC; `tests/fixtures/packet_v3_expected.json` (đáp án suy tay), output tạm |
| [test_b2_pipeline.py](test_b2_pipeline.py) | B2: HR 45–180 bpm, trung vị R–R khi nhịp không đều, sóng T không làm gấp đôi HR, thiếu HR, giới tính, chỉ hai trạng thái, split ghim đúng B3 v1, hai bảng đúng dòng, mỗi learner đúng dòng/cột/trọng số, không trích đặc trưng dòng test, nhãn val/test không đổi dự đoán, runner từ chối khi chưa duyệt, chưa commit hay split khác, `hr_mask.csv` | Chỉ SYNTHETIC; file HDF5 và repo Git tạm, output tạm |
| [test_packet_temp.py](test_packet_temp.py) | Kênh nhiệt độ `0xB1` (V0.2 mục 11): một giá trị mỗi packet 1 Hz, chỉ số là tick, cửa sổ pha anchor, bit được phép | Chỉ SYNTHETIC |
| [test_packet_control.py](test_packet_control.py) | `0xD2` và `0xD3` trong receiver (V0.2 mục 12–13): đúng bộ thanh ghi từng AFE, thế hệ tăng, bit 1 theo AFE, kiểm xác nhận theo kết quả | Chỉ SYNTHETIC |
| [test_packet_silence.py](test_packet_silence.py) | `channel_holes`: kênh dừng, bắt đầu muộn, ngắt quãng; chỉ anchor đã so khớp và nhịp `0xD1` đúng lưới 10 s mới tính; im lặng hay không rõ thời gian; đếm `SEQ` mất | Chỉ SYNTHETIC |
| [test_command_desk.py](test_command_desk.py) | Lệnh PC → thiết bị trong lúc `record` (V0.2 mục 13): một lệnh chờ, gửi lại sau 500 ms, giới hạn tốc độ, nhật ký, thiết bị giả trả `0xD3` | Chỉ SYNTHETIC; đồng hồ và cổng giả |
| [test_fiducial_gate.py](test_fiducial_gate.py) | Cổng nghiệm thu mốc Tuần 5: trung bình theo người, chỉ số không xác định thì trượt, nhóm xác nhận chỉ chấm phương pháp thắng, độ lặp lại người đánh dấu, `annotate` tiếp tục phiên dở | Chỉ SYNTHETIC; output tạm |
| [test_pulsedb_h5_reader.py](test_pulsedb_h5_reader.py) | Reader `h5py` khớp reader `mat73`, đọc từng phần theo khối, chỉ chạm dòng yêu cầu, đóng file khi lỗi | File HDF5 SYNTHETIC tự tạo (`pulsedb_h5_fixture.py`) |
| [test_firmware_cmd_wire.py](test_firmware_cmd_wire.py), [test_firmware_control.py](test_firmware_control.py) | Biên dịch `cmd_wire.c`, `cmd_exec.c` và bộ dựng `DATA` của `0xD2`: tách khung lệnh, quyết định lệnh, kiểm bằng bộ kiểm của receiver | Harness C, chỉ SYNTHETIC |
| [test_firmware_afe_order.py](test_firmware_afe_order.py) | Biên dịch `afe_order.c`: thứ tự `0xD2` theo AFE, giữ mất mát tới khi có bit 1, nhắc lại 10 s, số thứ tự 64 bit | Harness C, chỉ SYNTHETIC |
| [test_firmware_ecg_loop.py](test_firmware_ecg_loop.py), [test_firmware_ecg_read.py](test_firmware_ecg_read.py) | Biên dịch `ecg_loop.c` (kiểm chip 1 s, im 2 s, khởi động lại 100 ms, đọc FIFO trước `SYNCH`) và `ecg_read.c` (packet, chỉ số, bit của mỗi lần đọc FIFO) | Harness C, chỉ SYNTHETIC |
| [test_firmware_max30001.py](test_firmware_max30001.py), [test_firmware_max30101.py](test_firmware_max30101.py), [test_firmware_bmi270.py](test_firmware_bmi270.py) | Biên dịch lõi driver ba chip, chạy với chip mô phỏng theo datasheet: khởi động, đọc lại cấu hình, đọc FIFO, kiểm sức khỏe | Harness C, chip mô phỏng; không chứng minh chip thật |
| [test_firmware_die_temp.py](test_firmware_die_temp.py), [test_firmware_stim_plan.py](test_firmware_stim_plan.py) | Biên dịch máy trạng thái nhiệt độ die (V0.2 mục 11.1) và lịch xung kích thích đồng bộ (kế hoạch đo 10 phút) | Harness C, chỉ SYNTHETIC |
| [test_packet_v02.py](test_packet_v02.py) | Packet Schema V0.2: bảng kênh theo version, word thông tin thiết bị giữ mẫu bit, 5 case simulator V0.2 (IMU tồn đọng, FIFO đầy, trộn version, đổi định danh), mất phần mới nhất, biên chia 32/33/64/65 frame, bit dự trữ theo version, bit 5 của V0.2, dải IMU có dấu, `0xD1` sai/thiếu/lệch metadata/mất thứ tự, phát lại sau restart, record/replay V0.2; một raw ba lần khởi động (chữ ROM giữa phiên, packet bị reset cắt, firmware nạp lại) qua record/replay với `device_info` từng phiên; output không phụ thuộc kích thước khối đọc | Chỉ SYNTHETIC; đáp án suy từ spec V0.2 |

Mock trong `test_pulsedb.py` chưa chứng minh reader đọc đúng mọi file PulseDB
thật. Kết quả test không chứng minh split PulseDB, calibration hoặc phần cứng đã
được nghiệm thu.

## Cách chạy và đầu ra

Từ Git root, dùng môi trường đã cài dependency:

```powershell
# Chỉ kiểm tra code B0/B1, metrics và demo:
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_week_03_baselines.py tests/test_bp_metrics.py

# Kiểm tra toàn bộ repo:
.\.venv\Scripts\python.exe -m pytest -q
```

Pytest in tiến độ và số test `passed`, `failed` hoặc `errors`, không xuất bảng
hiệu năng BP. `-p no:cacheprovider` chỉ tắt ghi cache, không tắt các test; phù
hợp khi sandbox hạn chế quyền cache. Test dùng `tmp_path` vẫn cần truy cập thư
mục tạm. Không sửa hoặc bỏ test để che lỗi quyền truy cập.

Trong VSCode có thể chạy bằng mục **Testing** sau khi cấu hình Python/pytest,
hoặc cấu hình test cục bộ ở **Run and Debug** nếu có. Để xem B0/B1 và metrics
ngay bằng nút Run Python File, mở
[demo_week_03_baselines.py](../scripts/demo_week_03_baselines.py) theo
[hướng dẫn demo](../scripts/README.md).

Công thức và định dạng đầu vào:
[quy ước B0/B1 và metrics](../docs/protocol/week_03_baselines_metrics.md).
