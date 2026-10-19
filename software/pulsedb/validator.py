# software/pulsedb/validator.py
import hashlib

import numpy as np
import pandas as pd

from software.data_io.split_manifest import MISSING_SUBJECT_TOKENS as _SPLIT_TOKENS

# Same tokens the split rejects, plus the empty string.
MISSING_SUBJECT_TOKENS = frozenset(_SPLIT_TOKENS | {""})


def _subject_missing(subject_id) -> bool:
    if subject_id is None:
        return True
    if isinstance(subject_id, float) and np.isnan(subject_id):
        return True
    return str(subject_id).strip().lower() in MISSING_SUBJECT_TOKENS


def _waveform_key(seg) -> str:
    """Băm riêng waveform 3 kênh, không chứa ID/nhãn/metadata."""
    h = hashlib.sha256()
    for name in ("ecg", "ppg", "abp"):
        values = np.ascontiguousarray(np.asarray(getattr(seg, name), dtype="<f8"))
        h.update(f"{name}:{values.shape}".encode())
        h.update(values.tobytes())
    return h.hexdigest()


class PulseValidator:
    """Lớp chuyên kiểm tra tính hợp lệ và thống kê lỗi của dữ liệu PulseDB segments

    Validator chỉ gắn cờ; không xóa, sửa hoặc điền giá trị cho segment nào.
    Ngưỡng hợp lý sinh lý của nhãn (ví dụ pulse pressure tối thiểu) chưa
    chốt nên chỉ xuất giá trị ``pulse_pressure``.
    """

    def __init__(self, segments):
        self.segments = segments

    def validate_and_summarize(self) -> pd.DataFrame:
        """Quét toàn bộ danh sách segments và trả về DataFrame thống kê chi tiết"""
        records = []
        first_index_by_waveform = {}

        for idx, seg in enumerate(self.segments):
            # 1. Kiểm tra NaN và Inf trên các kênh tín hiệu
            ecg_nan = np.isnan(seg.ecg).sum()
            ppg_nan = np.isnan(seg.ppg).sum()
            abp_nan = np.isnan(seg.abp).sum()

            ecg_inf = np.isinf(seg.ecg).sum()
            ppg_inf = np.isinf(seg.ppg).sum()
            abp_inf = np.isinf(seg.abp).sum()

            # 2. Kiểm tra missing value trên metadata & nhãn huyết áp
            subject_missing = _subject_missing(seg.subject_id)
            label_nonfinite = not (
                np.isfinite(seg.sbp) and np.isfinite(seg.dbp)
            )
            meta_has_nan = subject_missing or label_nonfinite
            # Tuổi thiếu từng dòng là dữ liệu thiếu hợp lệ, gắn cờ riêng.
            age_missing = not np.isfinite(seg.age)

            # 3. Nhãn không nhất quán: DBP không được >= SBP
            dbp_ge_sbp = (not label_nonfinite) and seg.dbp >= seg.sbp
            pulse_pressure = (
                seg.sbp - seg.dbp if not label_nonfinite else np.nan
            )

            # 4. Waveform giống hệt một segment trước đó (bất kể ID/nhãn)
            lengths = {len(seg.ecg), len(seg.ppg), len(seg.abp)}
            key = _waveform_key(seg)
            duplicate_of = first_index_by_waveform.setdefault(key, idx)

            records.append({
                "segment_idx": idx,
                "subject_id": seg.subject_id,
                "ecg_len": len(seg.ecg),
                "ppg_len": len(seg.ppg),
                "abp_len": len(seg.abp),
                "length_mismatch": len(lengths) != 1,
                "ecg_nan": ecg_nan,
                "ppg_nan": ppg_nan,
                "abp_nan": abp_nan,
                "ecg_inf": ecg_inf,
                "ppg_inf": ppg_inf,
                "abp_inf": abp_inf,
                "subject_missing": subject_missing,
                "label_nonfinite": label_nonfinite,
                "meta_has_nan": meta_has_nan,
                "age_missing": age_missing,
                "sbp": seg.sbp,
                "dbp": seg.dbp,
                "pulse_pressure": pulse_pressure,
                "dbp_ge_sbp": dbp_ge_sbp,
                "waveform_duplicate_of": (
                    duplicate_of if duplicate_of != idx else pd.NA
                ),
            })

        df_stats = pd.DataFrame(records)
        if not df_stats.empty:
            df_stats["waveform_duplicate_of"] = df_stats[
                "waveform_duplicate_of"
            ].astype("Int64")
        return df_stats

    @staticmethod
    def print_report(df_stats: pd.DataFrame):
        """In ra báo cáo tổng hợp sạch sẽ, trực quan"""
        print("="*20 + " THỐNG KÊ ĐỘ DÀI TÍN HIỆU " + "="*20)
        print(f"• Số lượng đoạn phân tích : {len(df_stats)}")
        print(f"• Độ dài chuẩn ECG        : {df_stats['ecg_len'].unique()} samples")
        print(f"• Độ dài chuẩn PPG        : {df_stats['ppg_len'].unique()} samples")
        print(f"• Độ dài chuẩn ABP        : {df_stats['abp_len'].unique()} samples")
        print(f"• Đoạn lệch độ dài kênh   : {df_stats['length_mismatch'].sum()}")

        total_nan = df_stats['ecg_nan'].sum() + df_stats['ppg_nan'].sum() + df_stats['abp_nan'].sum()
        total_inf = df_stats['ecg_inf'].sum() + df_stats['ppg_inf'].sum() + df_stats['abp_inf'].sum()

        print("\n" + "="*20 + " BÁO CÁO LỖI (NAN / INF) " + "="*20)
        print(f"• Tổng số lỗi NaN (3 kênh): {total_nan}")
        print(f"• Tổng số lỗi Inf (3 kênh): {total_inf}")
        print(f"• Số segments thiếu Meta  : {df_stats['meta_has_nan'].sum()}")
        print(f"• Số segments thiếu tuổi  : {df_stats['age_missing'].sum()}")

        print("\n" + "="*20 + " CỜ NHÃN VÀ TRÙNG LẶP " + "="*20)
        print(f"• Nhãn DBP >= SBP         : {df_stats['dbp_ge_sbp'].sum()}")
        print(f"• Pulse pressure nhỏ nhất : {df_stats['pulse_pressure'].min()} mmHg")
        print(f"• Waveform trùng đoạn trước: {df_stats['waveform_duplicate_of'].notna().sum()}")
        print("  (chỉ gắn cờ; không tự xóa hoặc gộp đoạn)")
        print("="*50)
