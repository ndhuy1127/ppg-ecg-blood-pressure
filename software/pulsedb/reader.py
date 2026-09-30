from dataclasses import dataclass
import os
import numpy as np
import mat73

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
                if name in data: return data[name]
                for k in data.keys():
                    if k.lower() == name.lower(): return data[k]
            if default is not None:
                return default
            raise KeyError(f"Không tìm thấy một trong các key: {possible_names}. Các key hiện có: {list(data.keys())}")

        signals = get_key(["Signals", "signals", "sig"])
        sbp = get_key(["SBP", "sbp"])
        dbp = get_key(["DBP", "dbp"])
        subjects = get_key(["Subject", "Subject_ID", "subject", "subj"])
        
        age = get_key(["Age", "age"])
        gender = get_key(["Gender", "gender"])
        height = get_key(["Height", "height"], default=np.zeros(len(signals)))
        weight = get_key(["Weight", "weight"], default=np.zeros(len(signals)))
        bmi = get_key(["BMI", "bmi"], default=np.zeros(len(signals)))

        total_segments = signals.shape[0]
        n_segments = min(limit, total_segments) if limit is not None else total_segments

        segments = []
        for i in range(n_segments):
            ecg_sig = signals[i, 0, :]
            ppg_sig = signals[i, 1, :]
            abp_sig = signals[i, 2, :]

            def extract_val(arr, idx):
                val = arr[idx]
                return float(val.item() if hasattr(val, 'item') else val)

            sbp_val = extract_val(sbp, i)
            dbp_val = extract_val(dbp, i)

            raw_subj = subjects[i]
            if isinstance(raw_subj, np.ndarray) and raw_subj.size > 0:
                subj_id = str(raw_subj.item() if raw_subj.size == 1 else raw_subj[0])
            else:
                subj_id = str(raw_subj)

            g_val = extract_val(gender, i)
            gender_val = "M" if g_val == 1 or g_val == 'M' else ("F" if g_val == 0 or g_val == 'F' else "Unknown")
            
            segment = PulseSegment(
                subject_id=subj_id, 
                gender=gender_val,
                age=extract_val(age, i), 
                height_cm=extract_val(height, i),
                weight_kg=extract_val(weight, i), 
                bmi_kg_m2=extract_val(bmi, i),
                sbp=sbp_val, 
                dbp=dbp_val, 
                ecg=ecg_sig, 
                ppg=ppg_sig, 
                abp=abp_sig,
            )
            segments.append(segment)

        return segments