from dataclasses import dataclass
import os

import mat73
import numpy as np


@dataclass
class PulseSegment:
    subject_id: str
    gender: str
    age: float
    height_cm: float
    weight_kg: float
    bmi_kg_m2: float
    sbp: float
    dbp: float
    ecg: np.ndarray
    ppg: np.ndarray
    abp: np.ndarray


class PulseDBReader:
    def __init__(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")
        self.file_path = file_path

    def read(self, limit: int = None):
        data = mat73.loadmat(self.file_path)

        # Auto-unwrap bóc sạch mọi lớp bọc ngoài nếu có
        while isinstance(data, dict) and len(data) == 1:
            single_key = list(data.keys())[0]
            data = data[single_key]

        def get_key(possible_names, default=None):
            for name in possible_names:
                if name in data:
                    return data[name]
                for key in data.keys():
                    if key.lower() == name.lower():
                        return data[key]

            if default is not None:
                return default

            raise KeyError(
                f"Không tìm thấy một trong các key: {possible_names}. "
                f"Các key hiện có: {list(data.keys())}"
            )

        signals = get_key(["Signals", "signals", "sig"])
        sbp = get_key(["SBP", "sbp"])
        dbp = get_key(["DBP", "dbp"])
        subjects = get_key(
            ["Subject", "Subject_ID", "subject", "subj"]
        )
        age = get_key(["Age", "age"])
        gender = get_key(["Gender", "gender"])
        height = get_key(
            ["Height", "height"],
            default=np.zeros(len(signals)),
        )
        weight = get_key(
            ["Weight", "weight"],
            default=np.zeros(len(signals)),
        )
        bmi = get_key(
            ["BMI", "bmi"],
            default=np.zeros(len(signals)),
        )

        if signals.ndim != 3:
            raise ValueError(
                f"Signals phải có 3 chiều (segment, channel, sample), "
                f"nhưng nhận được shape {signals.shape}"
            )

        if signals.shape[1] != 3:
            raise ValueError(
                f"Signals phải có đúng 3 kênh (ECG, PPG, ABP), "
                f"nhưng nhận được {signals.shape[1]} kênh"
            )

        total_segments = signals.shape[0]
        n_segments = (
            min(limit, total_segments)
            if limit is not None
            else total_segments
        )

        def extract_scalar(arr, idx):
            value = np.asarray(arr[idx]).squeeze()
            if value.size == 1:
                return value.item()
            return value

        def extract_float(arr, idx):
            return float(extract_scalar(arr, idx))

        def extract_subject(arr, idx):
            value = extract_scalar(arr, idx)
            if isinstance(value, bytes):
                return value.decode("utf-8", errors="replace")
            return str(value)

        def normalize_gender(value):
            if isinstance(value, bytes):
                value = value.decode("utf-8", errors="replace")

            if isinstance(value, str):
                normalized = value.strip().upper()
                if normalized in {"M", "MALE"}:
                    return "M"
                if normalized in {"F", "FEMALE"}:
                    return "F"

            if value in (1, 1.0):
                return "M"
            if value in (0, 0.0):
                return "F"

            return "Unknown"

        segments = []

        for i in range(n_segments):
            segment = PulseSegment(
                subject_id=extract_subject(subjects, i),
                gender=normalize_gender(extract_scalar(gender, i)),
                age=extract_float(age, i),
                height_cm=extract_float(height, i),
                weight_kg=extract_float(weight, i),
                bmi_kg_m2=extract_float(bmi, i),
                sbp=extract_float(sbp, i),
                dbp=extract_float(dbp, i),
                ecg=signals[i, 0, :],
                ppg=signals[i, 1, :],
                abp=signals[i, 2, :],
            )
            segments.append(segment)

        return segments
