from dataclasses import dataclass
import math
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


# Thứ tự kênh trong Signals theo quy ước của PulseDB Subset (xem
# docs/pulsedb_provenance.md). Reader không tự đổi thứ tự kênh.
CHANNEL_ORDER = ("ecg", "ppg", "abp")

# Các trường nhân khẩu có thể không có trong file; khi thiếu thì trả NaN,
# không điền 0 hoặc giá trị suy đoán.
OPTIONAL_FIELDS = {
    "height_cm": ["Height", "height"],
    "weight_kg": ["Weight", "weight"],
    "bmi_kg_m2": ["BMI", "bmi"],
}


# Ba hàm dưới dùng chung với reader h5py (software/pulsedb/h5_reader.py) để
# hai reader chuyển một ô dữ liệu thành cùng một giá trị.
def extract_scalar(value):
    """Trả số/chuỗi đơn khi ô có đúng một giá trị; nếu không thì trả mảng."""
    value = np.asarray(value).squeeze()
    if value.size == 1:
        return value.item()
    return value


def subject_text(value, idx):
    if isinstance(value, np.ndarray):
        raise ValueError(
            f"Subject của đoạn {idx} không phải một giá trị đơn: {value!r}"
        )
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def normalize_gender(value):
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")

    if value is None:
        return "Unknown"
    if isinstance(value, float) and math.isnan(value):
        return "Unknown"

    if isinstance(value, str):
        normalized = value.strip().upper()
        if normalized in {"M", "MALE"}:
            return "M"
        if normalized in {"F", "FEMALE"}:
            return "F"
        if normalized == "":
            return "Unknown"

    # PulseDB Subset lưu giới tính dạng ký tự 'M'/'F'. Mã số hoặc
    # chuỗi khác cần bảng ánh xạ có tài liệu nguồn, không tự đoán.
    raise ValueError(
        f"Giá trị Gender không nhận dạng được: {value!r}; "
        "cần bảng ánh xạ có nguồn trước khi đọc"
    )


class PulseDBReader:
    """Đọc một file Subset PulseDB (MATLAB v7.3) thành danh sách PulseSegment.

    Reader chỉ đọc và kiểm tra cấu trúc; không lọc, không loại mẫu, không
    chuẩn hóa tín hiệu và không suy diễn metadata thiếu.
    """

    def __init__(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")
        self.file_path = file_path

    def read(self, limit: int = None):
        """Trả về các đoạn theo đúng thứ tự dòng trong file.

        ``limit`` chỉ giới hạn số đoạn trả về. ``mat73.loadmat`` vẫn nạp toàn
        bộ file vào RAM, và mỗi đoạn giữ view tới mảng Signals gốc, nên
        ``limit`` không giảm bộ nhớ đỉnh.
        """
        if limit is not None and (
            isinstance(limit, bool) or not isinstance(limit, int) or limit < 0
        ):
            raise ValueError("limit phải là số nguyên không âm hoặc None")

        data = mat73.loadmat(self.file_path)

        # Auto-unwrap bóc sạch mọi lớp bọc ngoài nếu có
        while isinstance(data, dict) and len(data) == 1:
            single_key = list(data.keys())[0]
            data = data[single_key]

        def get_key(possible_names, required=True):
            for name in possible_names:
                if name in data:
                    return data[name]
                for key in data.keys():
                    if key.lower() == name.lower():
                        return data[key]

            if not required:
                return None

            raise KeyError(
                f"Không tìm thấy một trong các key: {possible_names}. "
                f"Các key hiện có: {list(data.keys())}"
            )

        signals = get_key(["Signals", "signals", "sig"])

        if signals.ndim != 3:
            raise ValueError(
                f"Signals phải có 3 chiều (segment, channel, sample), "
                f"nhưng nhận được shape {signals.shape}"
            )

        if signals.shape[1] != len(CHANNEL_ORDER):
            raise ValueError(
                f"Signals phải có đúng 3 kênh (ECG, PPG, ABP), "
                f"nhưng nhận được {signals.shape[1]} kênh"
            )

        total_segments = signals.shape[0]

        def per_segment(possible_names, required=True):
            value = get_key(possible_names, required=required)
            if value is None:
                # mat73 trả None cho mảng rỗng. Trường tùy chọn thiếu thì
                # là NaN; trường bắt buộc rỗng là lỗi cấu trúc file.
                if required:
                    raise ValueError(
                        f"Trường bắt buộc {possible_names[0]} rỗng hoặc None"
                    )
                return np.full(total_segments, np.nan)
            if not isinstance(value, list) and np.ndim(value) == 0:
                # File chỉ có một đoạn: mat73 có thể trả về scalar.
                value = np.asarray(value).reshape(1)
            if len(value) != total_segments:
                raise ValueError(
                    f"Trường {possible_names[0]} có {len(value)} phần tử, "
                    f"khác số đoạn trong Signals ({total_segments})"
                )
            return value

        fields = {
            "sbp": per_segment(["SBP", "sbp"]),
            "dbp": per_segment(["DBP", "dbp"]),
            "subject_id": per_segment(["Subject", "Subject_ID", "subject", "subj"]),
            "age": per_segment(["Age", "age"]),
            "gender": per_segment(["Gender", "gender"]),
        }
        for field, names in OPTIONAL_FIELDS.items():
            fields[field] = per_segment(names, required=False)

        n_segments = (
            min(limit, total_segments)
            if limit is not None
            else total_segments
        )

        def extract_float(arr, idx):
            return float(extract_scalar(arr[idx]))

        segments = []

        for i in range(n_segments):
            segment = PulseSegment(
                subject_id=subject_text(extract_scalar(fields["subject_id"][i]), i),
                gender=normalize_gender(extract_scalar(fields["gender"][i])),
                age=extract_float(fields["age"], i),
                height_cm=extract_float(fields["height_cm"], i),
                weight_kg=extract_float(fields["weight_kg"], i),
                bmi_kg_m2=extract_float(fields["bmi_kg_m2"], i),
                sbp=extract_float(fields["sbp"], i),
                dbp=extract_float(fields["dbp"], i),
                ecg=signals[i, 0, :],
                ppg=signals[i, 1, :],
                abp=signals[i, 2, :],
            )
            segments.append(segment)

        return segments
