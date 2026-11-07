### Panel `full` (val: 40 subjects, 14400 rows; train: 115200 rows)

| Model | Target | MAE subject-balanced [95% CI] | Bias subject-balanced [95% CI] |
| --- | --- | --- | --- |
| B0@full | SBP | 15.11 [13.47, 16.88] | 4.30 [0.79, 7.67] |
| B0@full | DBP | 10.40 [9.12, 11.80] | 2.12 [-0.92, 5.14] |
| B2a@full | SBP | 16.40 [14.26, 18.88] | 4.76 [0.36, 9.09] |
| B2a@full | DBP | 11.15 [9.61, 12.97] | 1.62 [-1.58, 4.98] |
| B3@full | SBP | 14.58 [12.89, 16.49] | 3.96 [0.33, 7.52] |
| B3@full | DBP | 10.12 [8.94, 11.44] | 1.44 [-1.56, 4.33] |

- B2a - B0 @full, SBP: 1.29 [-0.39, 3.07] mmHg (negative: lower error than the reference)
- B2a - B0 @full, DBP: 0.74 [-0.81, 2.30] mmHg (negative: lower error than the reference)
- B3 - B2a @full, SBP: -1.82 [-3.52, -0.07] mmHg (negative: lower error than the reference)
- B3 - B2a @full, DBP: -1.03 [-2.70, 0.66] mmHg (negative: lower error than the reference)

### Panel `hr_available` (val: 40 subjects, 14376 rows; train: 115078 rows)

| Model | Target | MAE subject-balanced [95% CI] | Bias subject-balanced [95% CI] |
| --- | --- | --- | --- |
| B0@hr_available | SBP | 15.10 [13.46, 16.87] | 4.29 [0.78, 7.66] |
| B0@hr_available | DBP | 10.40 [9.12, 11.79] | 2.11 [-0.93, 5.13] |
| B2a@hr_available | SBP | 16.46 [14.35, 18.90] | 4.82 [0.41, 9.23] |
| B2a@hr_available | DBP | 10.83 [9.26, 12.57] | 1.42 [-1.78, 4.78] |
| B2b@hr_available | SBP | 16.51 [14.39, 18.73] | 4.54 [0.13, 8.77] |
| B2b@hr_available | DBP | 10.82 [9.33, 12.67] | 1.53 [-1.63, 4.84] |
| B3@hr_available | SBP | 14.57 [12.87, 16.47] | 3.96 [0.33, 7.54] |
| B3@hr_available | DBP | 10.14 [8.97, 11.46] | 1.43 [-1.56, 4.33] |

- B2b - B0 @hr_available, SBP: 1.41 [-0.35, 3.20] mmHg (negative: lower error than the reference)
- B2b - B0 @hr_available, DBP: 0.42 [-1.08, 1.99] mmHg (negative: lower error than the reference)
- B3 - B2b @hr_available, SBP: -1.94 [-3.76, -0.18] mmHg (negative: lower error than the reference)
- B3 - B2b @hr_available, DBP: -0.68 [-2.21, 0.91] mmHg (negative: lower error than the reference)
- B2b - B2a @hr_available, SBP: 0.05 [-0.89, 1.09] mmHg (negative: lower error than the reference)
- B2b - B2a @hr_available, DBP: -0.01 [-0.61, 0.61] mmHg (negative: lower error than the reference)

