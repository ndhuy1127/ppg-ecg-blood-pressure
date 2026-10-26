"""B2 features on PulseDB: demographics plus an ECG peak-rate HR.

Definition: docs/protocol/b2_pulsedb_definition.md (proposed 2026-10-26, pending
Huy's approval). Inputs are the demographic fields and the ECG vector of one
segment; ABP, SBP/DBP, subject IDs and hashes are never passed in. The HR is an
unvalidated ECG peak-rate estimate: the R detector has not passed the Week 5
gate, and a plausible value does not prove a correct one.
"""

import math

import numpy as np

from software.signal_processing.fiducials import Channel, SignalConfig, prepare, r_peaks

VERSION = "pulsedb-demographics-hr-v0"
DEMOGRAPHIC_NAMES = ("age_y", "sex", "height_cm", "weight_kg", "bmi_kg_m2")
HR_NAME = "hr_bpm"
SEX_CODES = {"F": 0.0, "M": 1.0}
ECG_FS_HZ = 125.0  # PulseDB Subset: 1 250 samples per 10 s (provenance section 6)
# Frozen with the definition (section 3); the dataclass defaults differ.
HR_CONFIG = SignalConfig(
    r_method="derivative_energy", r_energy_window_s=0.1, r_energy_threshold="quantile",
    refractory_s=0.25, prominence_fraction=0.2, ecg_polarity=1, filter_mode="none",
    edge_s=0.1, flat_std=1e-8,
)
HR_MIN_PEAKS = 4
HR_RANGE_BPM = (30.0, 220.0)


def demographics(segment) -> tuple[float, ...]:
    """The five demographic features of one segment, in DEMOGRAPHIC_NAMES order."""
    if segment.gender not in SEX_CODES:
        raise ValueError("sex must be M or F; other values are not encoded")
    values = (segment.age, SEX_CODES[segment.gender], segment.height_cm,
              segment.weight_kg, segment.bmi_kg_m2)
    for name, value in zip(DEMOGRAPHIC_NAMES, values):
        if isinstance(value, bool) or not isinstance(value, (int, float, np.number)) or (
            not math.isfinite(value)
        ):
            raise ValueError(f"{name} must be a finite number; nothing is imputed")
    return tuple(float(value) for value in values)


def hr_bpm(ecg, fs_hz=ECG_FS_HZ):
    """60 / median R-R of the segment, or None when not measurable.

    Not measurable: ``prepare`` flags the channel, fewer than HR_MIN_PEAKS R
    peaks, a nonfinite rate, or a rate outside HR_RANGE_BPM (inclusive). Every
    detected peak is used; no R-R trimming, clipping or imputation.
    """
    channel = Channel(values=ecg, fs_hz=fs_hz, unit="a.u.", clock_id=None)
    values, times, flags, _ = prepare(channel, HR_CONFIG, "ecg")
    if flags:
        return None
    found = r_peaks(values, times, fs_hz, HR_CONFIG)
    if len(found) < HR_MIN_PEAKS:
        return None
    with np.errstate(divide="ignore", invalid="ignore"):
        rate = 60.0 / float(np.median(np.diff(times[found])))
    low, high = HR_RANGE_BPM
    return rate if math.isfinite(rate) and low <= rate <= high else None


def check_constant_by_subject(subject_ids, rows) -> None:
    """Demographics must be the same in every segment of a subject."""
    seen = {}
    for subject, row in zip(subject_ids, rows):
        if seen.setdefault(subject, row) != row:
            raise ValueError("Demographics differ between segments of one subject")
