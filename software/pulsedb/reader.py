from dataclasses import dataclass
from pathlib import Path

import mat73
import numpy as np


# =========================
# PulseDB constants
# =========================

EXPECTED_SAMPLING_RATE_HZ = 125
EXPECTED_SAMPLES_PER_SEGMENT = 1250
EXPECTED_CHANNELS = 3

# Official PulseDB subset channel order:
# 0 -> ECG_F
# 1 -> PPG_F
# 2 -> ABP_Raw
CHANNEL_NAMES = ("ecg", "ppg", "abp")


# =========================
# One PulseDB segment
# =========================

@dataclass
class PulseSegment:
    subject_id: str

    ecg: np.ndarray
    ppg: np.ndarray
    abp: np.ndarray

    sbp: float
    dbp: float

    age: float
    gender: str
    height_cm: float
    weight_kg: float
    bmi_kg_m2: float


# =========================
# PulseDB Reader
# =========================

class PulseDBReader:
    REQUIRED_FIELDS = {
        "Subject",
        "Signals",
        "SBP",
        "DBP",
        "Age",
        "Gender",
        "Height",
        "Weight",
        "BMI",
    }

    def __init__(self, path):
        self.path = Path(path)

    # -------------------------
    # Load raw .mat file
    # -------------------------

    def load_raw(self):
        if not self.path.is_file():
            raise FileNotFoundError(
                f"PulseDB file does not exist: {self.path}"
            )

        data = mat73.loadmat(str(self.path))

        if "Subset" not in data:
            raise ValueError(
                f"Missing 'Subset' field in {self.path}"
            )

        subset = data["Subset"]

        missing = self.REQUIRED_FIELDS - set(subset.keys())

        if missing:
            raise ValueError(
                f"Missing required fields: {sorted(missing)}"
            )

        return subset

    # -------------------------
    # Read and validate dataset
    # -------------------------

    def read(self, limit=None):
        subset = self.load_raw()

        signals = np.asarray(subset["Signals"])

        # Signals must have: (number_of_segments, channels, samples)
        if signals.ndim != 3:
            raise ValueError(
                f"Signals must be 3-dimensional, got {signals.shape}"
            )

        # Check number of channels
        if signals.shape[1] != EXPECTED_CHANNELS:
            raise ValueError(
                f"Expected {EXPECTED_CHANNELS} channels, "
                f"got {signals.shape[1]}"
            )

        # Check number of samples per segment
        if signals.shape[2] != EXPECTED_SAMPLES_PER_SEGMENT:
            raise ValueError(
                f"Expected {EXPECTED_SAMPLES_PER_SEGMENT} samples "
                f"per segment, got {signals.shape[2]}"
            )

        # 1. Lấy tổng số segments gốc trong file .mat
        total_segments = signals.shape[0]

        # 2. Chuyển đổi toàn bộ mảng metadata gốc
        subjects = subset["Subject"]
        sbp = np.asarray(subset["SBP"], dtype=float).reshape(-1)
        dbp = np.asarray(subset["DBP"], dtype=float).reshape(-1)
        age = np.asarray(subset["Age"], dtype=float).reshape(-1)
        height = np.asarray(subset["Height"], dtype=float).reshape(-1)
        weight = np.asarray(subset["Weight"], dtype=float).reshape(-1)
        bmi = np.asarray(subset["BMI"], dtype=float).reshape(-1)
        genders = subset["Gender"]

        # 3. Kiểm tra độ dài metadata với tổng số segments gốc
        metadata_lengths = {
            "Subject": len(subjects),
            "SBP": len(sbp),
            "DBP": len(dbp),
            "Age": len(age),
            "Gender": len(genders),
            "Height": len(height),
            "Weight": len(weight),
            "BMI": len(bmi),
        }

        for field, length in metadata_lengths.items():
            if length != total_segments:
                raise ValueError(
                    f"{field} has {length} entries, "
                    f"but Signals has {total_segments} segments"
                )

        # 4. Tối ưu cắt Slicing (Early Slicing) ngay lập tức nếu truyền limit
        n_segments = total_segments
        if limit is not None:
            n_segments = min(limit, total_segments)

        signals = signals[:n_segments]
        subjects = subjects[:n_segments]
        sbp = sbp[:n_segments]
        dbp = dbp[:n_segments]
        age = age[:n_segments]
        height = height[:n_segments]
        weight = weight[:n_segments]
        bmi = bmi[:n_segments]
        genders = genders[:n_segments]

        # 5. Khởi tạo đối tượng PulseSegment chỉ cho n_segments đã cắt
        segments = []
        for i in range(n_segments):
            subject_id = self._get_subject_id(subjects[i])
            gender = self._get_gender(genders[i])

            segment = PulseSegment(
                subject_id=subject_id,
                ecg=signals[i, 0, :],
                ppg=signals[i, 1, :],
                abp=signals[i, 2, :],
                sbp=float(sbp[i]),
                dbp=float(dbp[i]),
                age=float(age[i]),
                gender=gender,
                height_cm=float(height[i]),
                weight_kg=float(weight[i]),
                bmi_kg_m2=float(bmi[i]),
            )

            segments.append(segment)

        return segments

    # -------------------------
    # Helpers
    # -------------------------

    @staticmethod
    def _get_subject_id(value):
        if isinstance(value, (list, tuple, np.ndarray)):
            if len(value) == 0:
                raise ValueError("Empty Subject value")

            value = value[0]

        return str(value)

    @staticmethod
    def _get_gender(value):
        if isinstance(value, (list, tuple, np.ndarray)):
            if len(value) == 0:
                raise ValueError("Empty Gender value")

            value = value[0]

        return str(value)