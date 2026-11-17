# Theo dõi thí nghiệm: B3 nhiều seed và bảng tổng hợp (2026-11-07)

Các file do script sinh ra, chép nguyên từ `runs/` (ngoài Git); không sửa số bằng tay. Không
có ID người. Hướng dẫn: [experiment_tracking.md](../../../../docs/protocol/experiment_tracking.md).

| File | Nguồn | SHA-256 |
| --- | --- | --- |
| [multiseed_table.md](multiseed_table.md) | `runs/b3_multiseed/20261107T062501Z/` (`scripts/run_b3_multiseed.py`) | `c273a4851b658933bd03837b86169dc3d5cae032b8974245edd6248028afcaf7` |
| [multiseed_report.json](multiseed_report.json) | như trên | `fd4f1cf8d7abab754ad14540d353ba31908dfae140f4005a5e9e2f98bec62cab` |
| [registry_runs.md](registry_runs.md) | `runs/registry/20261107T065225796480Z/` (`scripts/collect_runs.py`) | `66914257fe7450724350e784657a7a77c57d15780f529f60831ae593f767031e` |
| [registry_report.json](registry_report.json) | như trên | `da424b135c28b116d74fb0375b17d97b07f5e046eac287f82010e89240af5202` |

## B3 nhiều seed

Seed 42, 43, 44 của XGBoost, config `b3_pulsedb_v1.json` chỉ khác `b3.seed`, cùng split v2
(seed 72) và seed bootstrap 20261013, chỉ chấm val. Ba lần chạy ở commit `1c708df`, worktree
sạch. Kết quả **DETERMINISTIC**: `predictions_val.csv` trùng từng byte
(`aad32a7f9195…` ở cả ba seed), mọi metrics điểm có max − min = 0 và SD = 0, trùng số B3 của
Tuần 5. Đúng như dự kiến vì B3 v1 không lấy mẫu con. Độ bất định của B3 là CI bootstrap theo
người, không phải độ lệch giữa seed.

Script ghi đủ file đầu ra rồi mới lỗi khi in bảng ra console Windows (ký tự "−" ngoài bảng mã
cp1252), nên mã thoát là 1 dù kết quả đầy đủ; đã sửa ở `450302b`.

## Bảng tổng hợp

`registry_runs.md`: 5 lần chạy, 30 dòng, 0 lần chạy bị bỏ qua (B3 Tuần 5, B2 v1, ba seed B3).
Dấu `*` ở commit của lần chạy B3 Tuần 5 nghĩa là lúc runner ghi provenance, worktree có thay
đổi chưa commit; SHA-256 từng file mã nằm trong report của lần chạy đó.
