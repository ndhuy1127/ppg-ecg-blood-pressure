| Model | Target | Split | Subjects | Rows | MAE subject-balanced [95% CI] | Bias subject-balanced [95% CI] | MAE sample | Bias sample | SD sample (ddof=1) |
| --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: |
| B0 | SBP | val | 40 | 14400 | 15.11 [13.47, 16.88] | 4.30 [0.79, 7.67] | 15.11 | 4.30 | 18.79 |
| B0 | DBP | val | 40 | 14400 | 10.40 [9.12, 11.80] | 2.12 [-0.92, 5.14] | 10.40 | 2.12 | 12.78 |
| B3 | SBP | val | 40 | 14400 | 14.58 [12.89, 16.49] | 3.96 [0.33, 7.52] | 14.58 | 3.96 | 18.39 |
| B3 | DBP | val | 40 | 14400 | 10.12 [8.94, 11.44] | 1.44 [-1.56, 4.33] | 10.12 | 1.44 | 12.49 |

B3 - B0, SBP, subject-balanced MAE difference (same draws): -0.52 [-1.35, 0.58] mmHg; negative means lower error than the reference.
B3 - B0, DBP, subject-balanced MAE difference (same draws): -0.28 [-0.86, 0.36] mmHg; negative means lower error than the reference.
Error = prediction - reference (mmHg). Bootstrap: subject cluster percentile; shared draws across models, seed 20261013, 2000 repetitions, status ok.
