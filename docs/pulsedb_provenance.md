# PulseDB Provenance

## 1. Dataset

- Dataset: PulseDB
- Data subset used: PulseDB Supplementary Subsets
- Source database: VitalDB
- Distribution: Kaggle
- Kaggle dataset: `weinanwangrutgers/pulsedb-balanced-training-and-testing`

## 2. Source

- Official PulseDB repository:
  https://github.com/pulselabteam/PulseDB

- PulseDB paper:
  https://doi.org/10.3389/fdgth.2022.1090854

- Kaggle dataset:
  https://doi.org/10.34740/KAGGLE/DS/2447469

## 3. Version

The PulseDB official repository currently provides version `v2_0`.

The data used in this project are the supplementary subsets distributed through Kaggle and linked from the official PulseDB repository.

## 4. Data license

The VitalDB-derived PulseDB data are distributed under the
CC BY-NC-SA 4.0 license.

The full dataset is not committed to this Git repository.

## 5. Data files used

The Kaggle package provides the following subset files:

- `VitalDB_Train_Subset.mat`
- `VitalDB_AAMI_Cal_Subset.mat`
- `VitalDB_AAMI_Test_Subset.mat`
- `VitalDB_CalFree_Test_Subset.mat`
- `VitalDB_CalBased_Test_Subset.mat`

The exact files used for this project will be recorded when the reader and notebook are finalized.

## 6. Checksum

A SHA-256 checksum manifest will be generated for the exact data files used in this project.

No checksum is assumed or invented for the Kaggle package.

## 7. Data policy

The complete PulseDB dataset must not be committed to this Git repository.

Only source code, documentation, tests, notebooks, and checksum/provenance information are stored in Git.
## 8. Data schema

The supplementary subset contains the following fields:

- `Subject`
- `Signals`
- `SBP`
- `DBP`
- `Age`
- `Gender`
- `Height`
- `Weight`
- `BMI`

The `Signals` array contains three channels:

- Channel 0: `ECG_F`
- Channel 1: `PPG_F`
- Channel 2: `ABP_Raw`

Each segment contains 1250 samples per channel.

The sampling frequency is 125 Hz, corresponding to a 10-second segment.

The signal array therefore has the form:

`(number_of_segments, 3, 1250)`
## 9. Units

- `SBP`: mmHg
- `DBP`: mmHg
- `Age`: years
- `Height`: cm
- `Weight`: kg
- `BMI`: kg/m²

`ECG_F`, `PPG_F`, and `ABP_Raw` are waveform signals.
## 10. Subject identifier

The subject identifier is stored in the `Subject` field.

Example:

`p000001_1`

The reader maps the `Subject` field to `subject_id`.