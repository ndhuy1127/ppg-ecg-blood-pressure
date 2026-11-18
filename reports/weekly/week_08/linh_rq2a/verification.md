# Week 8 — RQ2a Reproduction Verification

## Environment
- Branch: dev/ngoclinh
- Dataset: PulseDB VitalDB_Train_Subset.mat
- Raw dataset SHA-256: verified
- Split: 400 subjects (320 train, 40 val, 40 test)
- Split manifest SHA-256:
  257d9653d6d42de26b77c291de79031b77ad7f3d29c6365d2319940acbe07d36

## Unit tests
- tests/test_rq2a.py
- Result: 17 passed in 3.83s

## Experiment
- Pool: 360 subjects, 129600 windows
- Replicates: 5
- Evaluation pairs: 180
- Method A: random split by window
- Method B: split by subject
- Bootstrap: subject-cluster percentile, 2000 draws
- Seed: 20261113

## Results
| Model | Target | MAE A | MAE B | Delta B-A (95% CI) |
| --- | --- | ---: | ---: | --- |
| B0 | SBP | 14.99 | 14.99 | 0.01 [-0.00; 0.02] |
| B0 | DBP | 9.33 | 9.35 | 0.01 [-0.00; 0.02] |
| B3 | SBP | 13.86 | 14.81 | 0.95 [0.64; 1.34] |
| B3 | DBP | 8.51 | 9.20 | 0.69 [0.50; 0.92] |

## Conclusion
For B3, window-level random splitting produces
lower evaluation MAE than subject-level splitting.

The positive paired confidence intervals indicate
the difference is consistently above zero under
the specified bootstrap procedure.

This experiment evaluates split sensitivity and
does not validate blood pressure measurement
performance on real hardware.

## Output
- runs/rq2a_pulsedb/linh_run_01
