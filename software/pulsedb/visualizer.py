# software/pulsedb/visualizer.py
import matplotlib.pyplot as plt
import numpy as np

class PulseVisualizer:
    """Lớp chuyên trách trực quan hóa các đoạn tín hiệu sinh học PulseDB"""

    @staticmethod
    def plot_segment(segment, segment_idx: int = 0, sampling_rate: float = 125.0):
        """Vẽ đồng thời 3 kênh tín hiệu ECG, PPG và ABP của một segment trên cùng một trục thời gian"""
        time = np.arange(len(segment.ecg)) / sampling_rate

        fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
        
        # 1. Kênh ECG
        axes[0].plot(time, segment.ecg, color='tab:blue', linewidth=1.2)
        axes[0].set_title(
            f"Segment {segment_idx} | Subject: {segment.subject_id} | "
            f"BP: {segment.sbp}/{segment.dbp} mmHg | Age/Gender: {segment.age}/{segment.gender}",
            fontsize=11, fontweight='bold'
        )
        # ECG_F của PulseDB Subset chưa được xác minh là mV; không gán đơn vị vật lý.
        axes[0].set_ylabel("ECG (a.u.)", fontsize=10)
        axes[0].grid(True, linestyle="--", alpha=0.6)

        # 2. Kênh PPG
        axes[1].plot(time, segment.ppg, color='tab:orange', linewidth=1.2)
        axes[1].set_ylabel("PPG (a.u.)", fontsize=10)
        axes[1].grid(True, linestyle="--", alpha=0.6)

        # 3. Kênh ABP
        axes[2].plot(time, segment.abp, color='tab:red', linewidth=1.2)
        axes[2].set_ylabel("ABP (mmHg)", fontsize=10)
        axes[2].set_xlabel("Time (seconds)", fontsize=10)
        axes[2].grid(True, linestyle="--", alpha=0.6)

        plt.tight_layout()
        plt.show()