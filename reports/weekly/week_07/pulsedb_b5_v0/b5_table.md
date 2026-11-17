Val: 40 subjects, 14400 rows; train: 115200 rows.

| Model | Target | MAE subject-balanced [95% CI] | Bias subject-balanced [95% CI] | SD sample |
| --- | --- | --- | --- | ---: |
| B0 | SBP | 15.11 [13.47, 16.88] | 4.30 [0.79, 7.67] | 18.79 |
| B0 | DBP | 10.40 [9.12, 11.80] | 2.12 [-0.92, 5.14] | 12.78 |
| B3 | SBP | 14.58 [12.89, 16.49] | 3.96 [0.33, 7.52] | 18.39 |
| B3 | DBP | 10.12 [8.94, 11.44] | 1.44 [-1.56, 4.33] | 12.49 |
| B5 | SBP | 13.24 [11.84, 14.64] | 3.09 [0.04, 6.05] | 16.73 |
| B5 | DBP | 9.76 [8.56, 11.20] | 2.08 [-0.83, 4.86] | 12.08 |

- B5 - B0, SBP: -1.87 [-3.23, -0.45] mmHg (subject-balanced MAE difference on the same draws; negative: lower error than the reference)
- B5 - B0, DBP: -0.64 [-1.35, 0.15] mmHg (subject-balanced MAE difference on the same draws; negative: lower error than the reference)
- B5 - B3, SBP: -1.34 [-2.53, -0.16] mmHg (subject-balanced MAE difference on the same draws; negative: lower error than the reference)
- B5 - B3, DBP: -0.36 [-0.91, 0.18] mmHg (subject-balanced MAE difference on the same draws; negative: lower error than the reference)

Error = prediction - reference (mmHg). Bootstrap: subject cluster percentile; shared draws across models, seed 20261013, 2000 repetitions, status ok.
