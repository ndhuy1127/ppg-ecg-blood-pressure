# software/pulsedb/validator.py
import numpy as np
import pandas as pd

class PulseValidator:
    """Lớp chuyên kiểm tra tính hợp lệ và thống kê lỗi của dữ liệu PulseDB segments"""

    def __init__(self, segments):
        self.segments = segments

    def validate_and_summarize(self) -> pd.DataFrame:
        """Quét toàn bộ danh sách segments và trả về DataFrame thống kê chi tiết"""
        records = []

        for idx, seg in enumerate(self.segments):
            # 1. Kiểm tra NaN và Inf trên các kênh tín hiệu
            ecg_nan = np.isnan(seg.ecg).sum()
            ppg_nan = np.isnan(seg.ppg).sum()
            abp_nan = np.isnan(seg.abp).sum()

            ecg_inf = np.isinf(seg.ecg).sum()
            ppg_inf = np.isinf(seg.ppg).sum()
            abp_inf = np.isinf(seg.abp).sum()

            # 2. Kiểm tra missing value trên metadata & nhãn huyết áp
            meta_has_nan = (
                pd.isna(seg.subject_id) or 
                pd.isna(seg.sbp) or 
                pd.isna(seg.dbp)
            )

            records.append({
                "segment_idx": idx,
                "subject_id": seg.subject_id,
                "ecg_len": len(seg.ecg),
                "ppg_len": len(seg.ppg),
                "abp_len": len(seg.abp),
                "ecg_nan": ecg_nan,
                "ppg_nan": ppg_nan,
                "abp_nan": abp_nan,
                "ecg_inf": ecg_inf,
                "ppg_inf": ppg_inf,
                "abp_inf": abp_inf,
                "meta_has_nan": meta_has_nan,
                "sbp": seg.sbp,
                "dbp": seg.dbp
            })

        df_stats = pd.DataFrame(records)
        return df_stats

    @staticmethod
    def print_report(df_stats: pd.DataFrame):
        """In ra báo cáo tổng hợp sạch sẽ, trực quan"""
        print("="*20 + " THỐNG KÊ ĐỘ DÀI TÍN HIỆU " + "="*20)
        print(f"• Số lượng đoạn phân tích : {len(df_stats)}")
        print(f"• Độ dài chuẩn ECG        : {df_stats['ecg_len'].unique()} samples")
        print(f"• Độ dài chuẩn PPG        : {df_stats['ppg_len'].unique()} samples")
        print(f"• Độ dài chuẩn ABP        : {df_stats['abp_len'].unique()} samples")

        total_nan = df_stats['ecg_nan'].sum() + df_stats['ppg_nan'].sum() + df_stats['abp_nan'].sum()
        total_inf = df_stats['ecg_inf'].sum() + df_stats['ppg_inf'].sum() + df_stats['abp_inf'].sum()

        print("\n" + "="*20 + " BÁO CÁO LỖI (NAN / INF) " + "="*20)
        print(f"• Tổng số lỗi NaN (3 kênh): {total_nan}")
        print(f"• Tổng số lỗi Inf (3 kênh): {total_inf}")
        print(f"• Số segments thiếu Meta  : {df_stats['meta_has_nan'].sum()}")
        print("="*50)