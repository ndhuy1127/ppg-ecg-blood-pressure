RQ2a, pool 360 subjects, 129600 windows, 5 replicates, 180 (replicate, subject) pairs. A = random by window, B = by subject.

| Model | Target | MAE A [95% CI] | MAE B [95% CI] | Delta B - A [95% CI] | Degradation % [95% CI] | RMSE A / B | ME ± SD A | ME ± SD B |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B0 | SBP | 14.99 [14.02; 16.09] | 14.99 [14.03; 16.11] | 0.01 [-0.00; 0.02] | 0.06 [-0.03; 0.16] | 18.90 / 18.91 | -0.93 ± 18.82 | -1.01 ± 18.82 |
| B0 | DBP | 9.33 [8.64; 10.11] | 9.35 [8.66; 10.12] | 0.01 [-0.00; 0.02] | 0.12 [-0.02; 0.26] | 11.87 / 11.88 | -0.29 ± 11.79 | -0.31 ± 11.79 |
| B3 | SBP | 13.86 [12.99; 14.82] | 14.81 [13.79; 15.96] | 0.95 [0.64; 1.34] | 6.82 [4.66; 9.54] | 17.62 / 18.76 | -1.15 ± 17.56 | -1.34 ± 18.66 |
| B3 | DBP | 8.51 [7.90; 9.20] | 9.20 [8.51; 10.01] | 0.69 [0.50; 0.92] | 8.09 [5.97; 10.74] | 10.96 / 11.74 | -0.60 ± 10.90 | -0.63 ± 11.69 |

MAE: subject-balanced on the shared evaluation windows; CI: pool-subject cluster percentile; A and B paired, seed 20261113, 2000 draws. RMSE, ME, SD: over windows, mean of replicates, no CI. Error = prediction - reference (mmHg).
