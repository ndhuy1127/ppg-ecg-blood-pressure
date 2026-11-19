# Week 8 — RQ1 Synthetic Analysis Verification

## Environment
- Branch: dev/ngoclinh
- Source: SYNTHETIC
- Configuration: configs/analysis/rq1_analysis_v1.json
- Input: runs/rq1_synthetic_linh/cuff_features.csv
- Output: runs/rq1_synthetic_linh/analysis_01

## Unit tests
- tests/test_rq1_analysis.py
- Result: 35 passed in 14.49s

## Experiment
- Eligible subjects: 15/15
- Main-set cuff measurements: 120
- Analysis: RQ1 SAP v1, LOSO

## Results
| Target | PPG MAE | PPG + PAT MAE | Delta |
| --- | ---: | ---: | ---: |
| SBP | 4.56 | 2.14 | -2.42 |
| DBP | 3.89 | 3.37 | -0.52 |

## Statistical interpretation
- SBP: Delta 97.5% CI [-3.84, -1.36].
- DBP: Delta 95% CI [-1.04, 0.03].
- SBP improvement is indicated by the reported CI.
- DBP improvement is not established at 95%.
- Main conclusions are sensitive to the CI method.

## Limitations
- This run uses synthetic feature-table fixtures.
- It does not constitute end-to-end verification
  from multiple device recording sessions.
- It does not validate prediction performance
  on real subjects or hardware.

## Conclusion
RQ1 analysis executed successfully and generated
report.json and summary.md.

## End-to-end SYNTHETIC integration

### Pipeline
Synthetic ECG/PPG -> Packet Logger -> Device Ingest
-> PAT/PPG Features -> RQ1 Analysis (LOSO)

### Input
- 3 synthetic subjects
- 2 sessions per subject
- 2 cuff events per session
- Total: 6 sessions, 12 cuff events
- Source: runs/linh_rq1_e2e_multi_03

### Eligibility
- Eligible subjects: 3/3
- Excluded subjects: 0
- Main-set cuffs: 6
- No eligibility flags in the final input

### Results
| Model | SBP MAE | DBP MAE |
| --- | ---: | ---: |
| PPG-only | 1.77 | 1.77 |
| PPG + PAT | 1.76 | 1.76 |
| PAT-only | 1.51 | 1.51 |

### Statistical limitations
- Only 3 eligible subjects, below SAP requirement of 15.
- Confidence intervals are not reliable at this sample size.
- Some baseline comparison CIs are extremely wide.
- No scientific performance conclusion is drawn.
- Synthetic data only; no human measurement validation.

### Verification
- RQ1 completed without an execution error.
- report.json and summary.md were generated.
- End-to-end software integration is operational.

### Output
runs/linh_rq1_e2e_multi_03/analysis/
