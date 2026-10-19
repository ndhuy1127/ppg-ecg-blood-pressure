# Data Conventions and Volume Estimates

The authoritative data convention (folders, IDs, file names, units, sampling
rates, traceability) is [quy_uoc_du_lieu.md](quy_uoc_du_lieu.md). This file only
keeps the short naming rule and the storage estimate; if the two disagree,
`quy_uoc_du_lieu.md` wins.

## 1. Naming Conventions

- Use lowercase letters and snake_case (e.g., `ecg_raw_2026.csv`).
- Study data files follow `<subject_id>_<session_id>_<event_id>_<data_type>.<ext>`
  as defined in `quy_uoc_du_lieu.md`.

## 2. Sampling rates (status)

| Source | ECG | PPG | Status |
| --- | --- | --- | --- |
| PulseDB Subset (public) | 125 Hz | 125 Hz | From file shape: 1250 samples per 10-s segment |
| Prototype device | 500 or 512 SPS | Depends on PPG AFE, LED mode and averaging | **Not decided**; see `configs/hardware/interface_power_sampling_v0.md` |

Do not assume the two channels share one sampling rate or one clock.

## 3. Volume Estimation

Storage planning estimate, not a measurement:

- Assumption: 500 samples/s, one CSV row per sample, about 48 bytes per row
  (timestamp, ECG, PPG, sequence, status as text).
- Result: 500 x 60 x 48 bytes ≈ 1.44 MB per minute of raw CSV.

Recompute when the device sampling rates and the logger file format are
decided. Binary packets (see the packet schema) are several times smaller.
