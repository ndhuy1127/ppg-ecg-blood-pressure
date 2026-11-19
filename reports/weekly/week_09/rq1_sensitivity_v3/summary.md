# RQ1 sensitivity simulation v3 (assumptions only, no human data)

CI method `t_envelope`, subject level, 2000 simulated studies per row; Monte Carlo SE of a share at most 1.1 percentage points. Every column uses the 97.5 % CI (first Holm step) unless stated. SBP and DBP are simulated apart. `equiv@δ`: share of studies whose CI lies within ±δ (SAP section 7 reading 'equivalent'). `rule δ`: SAP section 8 rule applied to the simulated cuff noise. All numbers hold only under the config assumptions.

Decision rules written before this run (2026-11-19, before any v3 output was produced):

- **R1_precision**: At the planned design, reference noise, M2 moderate, no M6, no repeat, model 'null': the share of studies whose 97.5 % CI of mean d_s lies within +-fixed_delta (reading 'equivalent') is at least 0.80, for SBP and DBP. Checked with the decision_check draws.
- **R2_alarm**: Same setting, model 'strong': P(main conclusion) at 97.5 % below 0.50 is an alarm reported to the team, not a pass/fail criterion; it depends on the invented model scenario.
- **R3_action**: If R1 fails: report which of repeat, M6 (with and without PAT gain at M6) or both restore R1, with their cost in session time; the choice among them is made by the team (C2, M6 criteria), never because an option makes the main conclusion more likely.
- **R4_delta**: Readings are reported at the SAP rule delta for each noise level and at fixed_delta. Whether to cap delta is decided by the team from the R1/R2 tables before the SAP is locked; no cap is applied in this run.

## Cuff noise levels

| Target | σ cuff | rule δ | fixed δ | implied resting median \|ΔBP\| (S4: about 3 mmHg SBP) |
| --- | ---: | ---: | ---: | ---: |
| SBP | 3 | 1.5 | 2 | 3.00 |
| SBP | 5 | 2.5 | 2 | 4.46 |
| SBP | 7 | 3.5 | 2 | 6.02 |
| DBP | 2.5 | 1.5 | 1.5 | 2.47 |
| DBP | 4 | 2 | 1.5 | 3.57 |
| DBP | 5 | 2.5 | 1.5 | 4.35 |

## Decision check (10000 bootstrap draws)

| Target | σ cuff | Subjects × sessions | Effect | mean d | CI width mean (q90) | equiv@fixed δ | equiv@rule δ | P(main) | R1 |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| SBP | 3 | 25 × 2 | null | 0.00 | 1.73 (2.11) | 0.99 | 0.90 | 0.00 |  |
| SBP | 3 | 32 × 2 | null | 0.01 | 1.48 (1.76) | 1.00 | 0.98 | 0.00 |  |
| SBP | 3 | 25 × 2 | strong | -1.47 | 1.88 (2.30) | 0.16 | 0.01 | 0.25 |  |
| SBP | 3 | 32 × 2 | strong | -1.49 | 1.63 (1.94) | 0.20 | 0.01 | 0.35 |  |
| SBP | 5 | 25 × 2 | null | 0.00 | 1.77 (2.16) | 0.99 | 1.00 | 0.00 |  |
| SBP | 5 | 32 × 2 | null | -0.00 | 1.53 (1.82) | 1.00 | 1.00 | 0.00 | pass |
| SBP | 5 | 25 × 2 | strong | -1.20 | 2.00 (2.42) | 0.33 | 0.74 | 0.15 |  |
| SBP | 5 | 32 × 2 | strong | -1.19 | 1.71 (2.02) | 0.45 | 0.87 | 0.19 |  |
| SBP | 7 | 25 × 2 | null | 0.00 | 1.80 (2.19) | 0.99 | 1.00 | 0.00 |  |
| SBP | 7 | 32 × 2 | null | -0.01 | 1.56 (1.86) | 1.00 | 1.00 | 0.00 |  |
| SBP | 7 | 25 × 2 | strong | -0.98 | 2.06 (2.48) | 0.51 | 1.00 | 0.08 |  |
| SBP | 7 | 32 × 2 | strong | -0.94 | 1.78 (2.12) | 0.68 | 1.00 | 0.12 |  |
| DBP | 2.5 | 25 × 2 | null | -0.00 | 1.25 (1.51) | 1.00 | 1.00 | 0.00 |  |
| DBP | 2.5 | 32 × 2 | null | -0.00 | 1.08 (1.27) | 1.00 | 1.00 | 0.00 |  |
| DBP | 2.5 | 25 × 2 | strong | -1.02 | 1.38 (1.68) | 0.25 | 0.25 | 0.09 |  |
| DBP | 2.5 | 32 × 2 | strong | -1.04 | 1.19 (1.41) | 0.30 | 0.30 | 0.14 |  |
| DBP | 4 | 25 × 2 | null | -0.00 | 1.28 (1.56) | 1.00 | 1.00 | 0.00 |  |
| DBP | 4 | 32 × 2 | null | -0.00 | 1.10 (1.30) | 1.00 | 1.00 | 0.00 | pass |
| DBP | 4 | 25 × 2 | strong | -0.83 | 1.44 (1.75) | 0.43 | 0.91 | 0.07 |  |
| DBP | 4 | 32 × 2 | strong | -0.83 | 1.25 (1.49) | 0.56 | 0.97 | 0.10 |  |
| DBP | 5 | 25 × 2 | null | 0.00 | 1.29 (1.55) | 1.00 | 1.00 | 0.00 |  |
| DBP | 5 | 32 × 2 | null | 0.00 | 1.12 (1.32) | 1.00 | 1.00 | 0.00 |  |
| DBP | 5 | 25 × 2 | strong | -0.72 | 1.47 (1.79) | 0.57 | 1.00 | 0.06 |  |
| DBP | 5 | 32 × 2 | strong | -0.71 | 1.27 (1.52) | 0.70 | 1.00 | 0.08 |  |

## SBP, design size (M2 moderate, no M6, no repeat)

| σ cuff | Subjects × sessions | null: CI width | null: equiv@fixed δ | benefit: P(main) | strong: P(main) |
| ---: | --- | ---: | ---: | ---: | ---: |
| 3 | 15 × 2 | 2.38 | 0.85 | 0.02 | 0.13 |
| 3 | 25 × 2 | 1.72 | 0.99 | 0.03 | 0.25 |
| 3 | 32 × 2 | 1.49 | 1.00 | 0.03 | 0.35 |
| 5 | 15 × 2 | 2.45 | 0.83 | 0.01 | 0.08 |
| 5 | 25 × 2 | 1.76 | 1.00 | 0.02 | 0.15 |
| 5 | 32 × 2 | 1.52 | 1.00 | 0.02 | 0.19 |
| 7 | 15 × 2 | 2.51 | 0.81 | 0.01 | 0.04 |
| 7 | 25 × 2 | 1.80 | 0.99 | 0.01 | 0.08 |
| 7 | 32 × 2 | 1.56 | 1.00 | 0.02 | 0.11 |

## SBP, options at 32 × 2

Null rows give precision; benefit/strong rows the chance of the main conclusion. `d core`: mean d over the M0–M2 cuffs only; `d true`: mean d against the latent true change. P6: median M6 change against same-session M0.

| σ cuff | M2 | M6 | Repeat | null: CI width | null: equiv@fixed δ | null: equiv@rule δ | benefit: P(main) | strong: P(main) | strong: d / d core / d true | P2 | P6 |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| 3 | narrow | none | none | 1.51 | 1.00 | 0.96 | 0.00 | 0.02 | -1.19 / -1.19 / -1.48 | 3.0 | — |
| 3 | narrow | none | plateau_rho_0.3 | 1.51 | 1.00 | 0.97 | 0.00 | 0.03 | -1.21 / -1.21 / -1.48 | 3.0 | — |
| 3 | narrow | low | none | 1.38 | 1.00 | 0.99 | 0.16 | 0.74 | -1.70 / -1.18 / -2.05 | 3.1 | 10.0 |
| 3 | narrow | low | plateau_rho_0.3 | 1.38 | 1.00 | 0.99 | 0.17 | 0.79 | -1.77 / -1.22 / -2.06 | 3.0 | 10.0 |
| 3 | narrow | low_no_pat_gain | none | 1.37 | 1.00 | 0.99 | 0.01 | 0.22 | -1.01 / -1.18 / -1.24 | 3.0 | 10.0 |
| 3 | narrow | low_no_pat_gain | plateau_rho_0.3 | 1.37 | 1.00 | 0.99 | 0.01 | 0.26 | -1.04 / -1.22 / -1.25 | 3.0 | 9.9 |
| 3 | narrow | high | none | 1.37 | 1.00 | 0.99 | 0.94 | 1.00 | -2.72 / -1.19 / -3.08 | 3.0 | 20.1 |
| 3 | narrow | high | plateau_rho_0.3 | 1.36 | 1.00 | 0.99 | 0.96 | 1.00 | -2.75 / -1.21 / -3.05 | 3.0 | 20.1 |
| 3 | narrow | high_no_pat_gain | none | 1.36 | 1.00 | 0.99 | 0.16 | 0.69 | -0.96 / -1.17 / -1.19 | 3.0 | 20.0 |
| 3 | narrow | high_no_pat_gain | plateau_rho_0.3 | 1.36 | 1.00 | 0.99 | 0.17 | 0.72 | -0.98 / -1.20 / -1.19 | 3.0 | 20.0 |
| 3 | moderate | none | none | 1.49 | 1.00 | 0.98 | 0.03 | 0.35 | -1.49 / -1.49 / -1.81 | 8.1 | — |
| 3 | moderate | none | plateau_rho_0.3 | 1.49 | 1.00 | 0.98 | 0.03 | 0.39 | -1.52 / -1.52 / -1.81 | 8.0 | — |
| 3 | moderate | low | none | 1.38 | 1.00 | 0.99 | 0.49 | 0.96 | -1.96 / -1.49 / -2.32 | 8.0 | 10.0 |
| 3 | moderate | low | plateau_rho_0.3 | 1.38 | 1.00 | 0.99 | 0.52 | 0.97 | -2.00 / -1.53 / -2.33 | 8.1 | 10.0 |
| 3 | moderate | low_no_pat_gain | none | 1.38 | 1.00 | 0.98 | 0.15 | 0.70 | -1.25 / -1.48 / -1.51 | 8.0 | 10.0 |
| 3 | moderate | low_no_pat_gain | plateau_rho_0.3 | 1.38 | 1.00 | 0.99 | 0.14 | 0.73 | -1.28 / -1.52 / -1.51 | 8.0 | 10.0 |
| 3 | moderate | high | none | 1.37 | 1.00 | 0.99 | 0.99 | 1.00 | -2.95 / -1.48 / -3.34 | 7.9 | 20.1 |
| 3 | moderate | high | plateau_rho_0.3 | 1.37 | 1.00 | 0.99 | 0.99 | 1.00 | -3.00 / -1.50 / -3.33 | 8.0 | 20.1 |
| 3 | moderate | high_no_pat_gain | none | 1.38 | 1.00 | 0.99 | 0.39 | 0.93 | -1.22 / -1.50 / -1.48 | 8.0 | 20.1 |
| 3 | moderate | high_no_pat_gain | plateau_rho_0.3 | 1.37 | 1.00 | 0.99 | 0.40 | 0.94 | -1.23 / -1.51 / -1.46 | 8.0 | 20.0 |
| 5 | narrow | none | none | 1.55 | 1.00 | 1.00 | 0.00 | 0.02 | -0.92 / -0.92 / -1.47 | 3.0 | — |
| 5 | narrow | none | plateau_rho_0.3 | 1.55 | 1.00 | 1.00 | 0.00 | 0.02 | -0.96 / -0.96 / -1.47 | 3.0 | — |
| 5 | narrow | low | none | 1.41 | 1.00 | 1.00 | 0.11 | 0.52 | -1.37 / -0.91 / -2.05 | 3.0 | 10.0 |
| 5 | narrow | low | plateau_rho_0.3 | 1.41 | 1.00 | 1.00 | 0.16 | 0.61 | -1.47 / -0.98 / -2.06 | 3.0 | 10.0 |
| 5 | narrow | low_no_pat_gain | none | 1.41 | 1.00 | 1.00 | 0.01 | 0.14 | -0.80 / -0.92 / -1.24 | 3.0 | 9.9 |
| 5 | narrow | low_no_pat_gain | plateau_rho_0.3 | 1.41 | 1.00 | 1.00 | 0.02 | 0.16 | -0.84 / -0.97 / -1.24 | 3.0 | 10.0 |
| 5 | narrow | high | none | 1.40 | 1.00 | 1.00 | 0.91 | 1.00 | -2.32 / -0.92 / -3.06 | 2.9 | 20.0 |
| 5 | narrow | high | plateau_rho_0.3 | 1.39 | 1.00 | 1.00 | 0.93 | 1.00 | -2.42 / -0.98 / -3.07 | 3.0 | 20.0 |
| 5 | narrow | high_no_pat_gain | none | 1.40 | 1.00 | 1.00 | 0.09 | 0.45 | -0.76 / -0.92 / -1.19 | 3.0 | 20.0 |
| 5 | narrow | high_no_pat_gain | plateau_rho_0.3 | 1.39 | 1.00 | 1.00 | 0.13 | 0.51 | -0.80 / -0.97 / -1.19 | 2.9 | 20.0 |
| 5 | moderate | none | none | 1.52 | 1.00 | 1.00 | 0.02 | 0.19 | -1.19 / -1.19 / -1.81 | 8.0 | — |
| 5 | moderate | none | plateau_rho_0.3 | 1.53 | 1.00 | 1.00 | 0.03 | 0.25 | -1.25 / -1.25 / -1.81 | 7.9 | — |
| 5 | moderate | low | none | 1.40 | 1.00 | 1.00 | 0.33 | 0.81 | -1.60 / -1.19 / -2.33 | 8.0 | 10.0 |
| 5 | moderate | low | plateau_rho_0.3 | 1.42 | 1.00 | 1.00 | 0.38 | 0.87 | -1.68 / -1.25 / -2.32 | 8.0 | 10.0 |
| 5 | moderate | low_no_pat_gain | none | 1.42 | 1.00 | 1.00 | 0.09 | 0.45 | -1.00 / -1.18 / -1.51 | 8.0 | 10.1 |
| 5 | moderate | low_no_pat_gain | plateau_rho_0.3 | 1.42 | 1.00 | 1.00 | 0.10 | 0.52 | -1.05 / -1.24 / -1.50 | 8.0 | 10.0 |
| 5 | moderate | high | none | 1.41 | 1.00 | 1.00 | 0.97 | 1.00 | -2.53 / -1.19 / -3.34 | 8.0 | 20.0 |
| 5 | moderate | high | plateau_rho_0.3 | 1.40 | 1.00 | 1.00 | 0.98 | 1.00 | -2.62 / -1.24 / -3.33 | 8.0 | 20.0 |
| 5 | moderate | high_no_pat_gain | none | 1.39 | 1.00 | 1.00 | 0.26 | 0.72 | -0.98 / -1.19 / -1.46 | 8.0 | 19.9 |
| 5 | moderate | high_no_pat_gain | plateau_rho_0.3 | 1.40 | 1.00 | 1.00 | 0.27 | 0.77 | -1.02 / -1.25 / -1.47 | 7.9 | 19.9 |
| 7 | narrow | none | none | 1.58 | 1.00 | 1.00 | 0.00 | 0.01 | -0.73 / -0.73 / -1.46 | 3.0 | — |
| 7 | narrow | none | plateau_rho_0.3 | 1.57 | 1.00 | 1.00 | 0.00 | 0.02 | -0.78 / -0.78 / -1.46 | 3.0 | — |
| 7 | narrow | low | none | 1.44 | 1.00 | 1.00 | 0.08 | 0.33 | -1.13 / -0.73 / -2.05 | 3.0 | 10.0 |
| 7 | narrow | low | plateau_rho_0.3 | 1.44 | 1.00 | 1.00 | 0.10 | 0.41 | -1.21 / -0.78 / -2.05 | 3.1 | 10.1 |
| 7 | narrow | low_no_pat_gain | none | 1.43 | 1.00 | 1.00 | 0.01 | 0.08 | -0.65 / -0.74 / -1.23 | 3.0 | 10.0 |
| 7 | narrow | low_no_pat_gain | plateau_rho_0.3 | 1.44 | 1.00 | 1.00 | 0.01 | 0.08 | -0.69 / -0.79 / -1.24 | 3.0 | 10.0 |
| 7 | narrow | high | none | 1.41 | 1.00 | 1.00 | 0.80 | 0.97 | -1.98 / -0.73 / -3.08 | 3.0 | 20.0 |
| 7 | narrow | high | plateau_rho_0.3 | 1.42 | 1.00 | 1.00 | 0.85 | 0.99 | -2.10 / -0.78 / -3.06 | 3.0 | 20.1 |
| 7 | narrow | high_no_pat_gain | none | 1.42 | 1.00 | 1.00 | 0.07 | 0.27 | -0.62 / -0.73 / -1.19 | 2.9 | 20.0 |
| 7 | narrow | high_no_pat_gain | plateau_rho_0.3 | 1.43 | 1.00 | 1.00 | 0.08 | 0.32 | -0.66 / -0.79 / -1.19 | 3.0 | 20.0 |
| 7 | moderate | none | none | 1.56 | 1.00 | 1.00 | 0.02 | 0.11 | -0.96 / -0.96 / -1.81 | 8.0 | — |
| 7 | moderate | none | plateau_rho_0.3 | 1.57 | 1.00 | 1.00 | 0.02 | 0.15 | -1.02 / -1.02 / -1.81 | 8.0 | — |
| 7 | moderate | low | none | 1.43 | 1.00 | 1.00 | 0.20 | 0.56 | -1.31 / -0.96 / -2.34 | 8.0 | 10.0 |
| 7 | moderate | low | plateau_rho_0.3 | 1.44 | 1.00 | 1.00 | 0.27 | 0.65 | -1.41 / -1.03 / -2.34 | 8.0 | 10.0 |
| 7 | moderate | low_no_pat_gain | none | 1.43 | 1.00 | 1.00 | 0.05 | 0.25 | -0.82 / -0.95 / -1.51 | 8.0 | 9.9 |
| 7 | moderate | low_no_pat_gain | plateau_rho_0.3 | 1.45 | 1.00 | 1.00 | 0.07 | 0.30 | -0.88 / -1.01 / -1.51 | 7.9 | 10.0 |
| 7 | moderate | high | none | 1.42 | 1.00 | 1.00 | 0.88 | 0.98 | -2.16 / -0.97 / -3.33 | 8.0 | 19.9 |
| 7 | moderate | high | plateau_rho_0.3 | 1.43 | 1.00 | 1.00 | 0.93 | 1.00 | -2.30 / -1.02 / -3.33 | 8.0 | 20.2 |
| 7 | moderate | high_no_pat_gain | none | 1.43 | 1.00 | 1.00 | 0.16 | 0.46 | -0.79 / -0.95 / -1.46 | 8.0 | 20.1 |
| 7 | moderate | high_no_pat_gain | plateau_rho_0.3 | 1.44 | 1.00 | 1.00 | 0.17 | 0.57 | -0.85 / -1.02 / -1.46 | 8.0 | 20.1 |

## DBP, design size (M2 moderate, no M6, no repeat)

| σ cuff | Subjects × sessions | null: CI width | null: equiv@fixed δ | benefit: P(main) | strong: P(main) |
| ---: | --- | ---: | ---: | ---: | ---: |
| 2.5 | 15 × 2 | 1.75 | 0.88 | 0.00 | 0.06 |
| 2.5 | 25 × 2 | 1.24 | 1.00 | 0.00 | 0.10 |
| 2.5 | 32 × 2 | 1.09 | 1.00 | 0.00 | 0.14 |
| 4 | 15 × 2 | 1.78 | 0.86 | 0.00 | 0.03 |
| 4 | 25 × 2 | 1.29 | 0.99 | 0.00 | 0.08 |
| 4 | 32 × 2 | 1.12 | 1.00 | 0.01 | 0.09 |
| 5 | 15 × 2 | 1.80 | 0.85 | 0.00 | 0.02 |
| 5 | 25 × 2 | 1.30 | 0.99 | 0.00 | 0.05 |
| 5 | 32 × 2 | 1.12 | 1.00 | 0.00 | 0.08 |

## DBP, options at 32 × 2

Null rows give precision; benefit/strong rows the chance of the main conclusion. `d core`: mean d over the M0–M2 cuffs only; `d true`: mean d against the latent true change. P6: median M6 change against same-session M0.

| σ cuff | M2 | M6 | Repeat | null: CI width | null: equiv@fixed δ | null: equiv@rule δ | benefit: P(main) | strong: P(main) | strong: d / d core / d true | P2 | P6 |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| 2.5 | narrow | none | none | 1.09 | 1.00 | 1.00 | 0.00 | 0.02 | -0.87 / -0.87 / -1.13 | 2.0 | — |
| 2.5 | narrow | none | plateau_rho_0.3 | 1.09 | 1.00 | 1.00 | 0.00 | 0.02 | -0.88 / -0.88 / -1.11 | 2.0 | — |
| 2.5 | narrow | low | none | 0.99 | 1.00 | 1.00 | 0.05 | 0.64 | -1.28 / -0.85 / -1.57 | 2.0 | 7.0 |
| 2.5 | narrow | low | plateau_rho_0.3 | 1.00 | 1.00 | 1.00 | 0.05 | 0.68 | -1.32 / -0.89 / -1.57 | 2.0 | 7.0 |
| 2.5 | narrow | low_no_pat_gain | none | 0.99 | 1.00 | 1.00 | 0.00 | 0.08 | -0.73 / -0.85 / -0.93 | 2.0 | 7.0 |
| 2.5 | narrow | low_no_pat_gain | plateau_rho_0.3 | 0.99 | 1.00 | 1.00 | 0.00 | 0.09 | -0.74 / -0.87 / -0.93 | 2.0 | 7.0 |
| 2.5 | narrow | high | none | 0.98 | 1.00 | 1.00 | 0.68 | 1.00 | -1.97 / -0.86 / -2.27 | 2.0 | 14.0 |
| 2.5 | narrow | high | plateau_rho_0.3 | 0.99 | 1.00 | 1.00 | 0.70 | 1.00 | -2.02 / -0.90 / -2.25 | 2.0 | 14.0 |
| 2.5 | narrow | high_no_pat_gain | none | 0.99 | 1.00 | 1.00 | 0.03 | 0.40 | -0.70 / -0.86 / -0.90 | 2.0 | 14.0 |
| 2.5 | narrow | high_no_pat_gain | plateau_rho_0.3 | 0.98 | 1.00 | 1.00 | 0.03 | 0.43 | -0.72 / -0.89 / -0.89 | 2.0 | 14.0 |
| 2.5 | moderate | none | none | 1.09 | 1.00 | 1.00 | 0.00 | 0.14 | -1.04 / -1.04 / -1.31 | 5.1 | — |
| 2.5 | moderate | none | plateau_rho_0.3 | 1.08 | 1.00 | 1.00 | 0.00 | 0.16 | -1.07 / -1.07 / -1.30 | 5.0 | — |
| 2.5 | moderate | low | none | 0.99 | 1.00 | 1.00 | 0.13 | 0.84 | -1.43 / -1.04 / -1.73 | 5.0 | 7.0 |
| 2.5 | moderate | low | plateau_rho_0.3 | 0.99 | 1.00 | 1.00 | 0.14 | 0.87 | -1.46 / -1.07 / -1.72 | 5.0 | 7.0 |
| 2.5 | moderate | low_no_pat_gain | none | 1.00 | 1.00 | 1.00 | 0.01 | 0.31 | -0.86 / -1.03 / -1.08 | 5.0 | 7.1 |
| 2.5 | moderate | low_no_pat_gain | plateau_rho_0.3 | 0.99 | 1.00 | 1.00 | 0.01 | 0.35 | -0.90 / -1.07 / -1.09 | 5.0 | 7.0 |
| 2.5 | moderate | high | none | 1.00 | 1.00 | 1.00 | 0.85 | 1.00 | -2.11 / -1.03 / -2.40 | 5.0 | 14.0 |
| 2.5 | moderate | high | plateau_rho_0.3 | 1.00 | 1.00 | 1.00 | 0.86 | 1.00 | -2.15 / -1.06 / -2.41 | 5.0 | 14.0 |
| 2.5 | moderate | high_no_pat_gain | none | 0.99 | 1.00 | 1.00 | 0.11 | 0.73 | -0.84 / -1.03 / -1.04 | 5.0 | 14.0 |
| 2.5 | moderate | high_no_pat_gain | plateau_rho_0.3 | 0.99 | 1.00 | 1.00 | 0.11 | 0.75 | -0.87 / -1.07 / -1.06 | 5.0 | 14.0 |
| 4 | narrow | none | none | 1.11 | 1.00 | 1.00 | 0.00 | 0.02 | -0.68 / -0.68 / -1.11 | 1.9 | — |
| 4 | narrow | none | plateau_rho_0.3 | 1.11 | 1.00 | 1.00 | 0.00 | 0.02 | -0.71 / -0.71 / -1.11 | 2.0 | — |
| 4 | narrow | low | none | 1.02 | 1.00 | 1.00 | 0.04 | 0.45 | -1.05 / -0.68 / -1.57 | 2.0 | 7.0 |
| 4 | narrow | low | plateau_rho_0.3 | 1.02 | 1.00 | 1.00 | 0.05 | 0.51 | -1.11 / -0.71 / -1.56 | 2.0 | 7.0 |
| 4 | narrow | low_no_pat_gain | none | 1.01 | 1.00 | 1.00 | 0.00 | 0.06 | -0.58 / -0.68 / -0.93 | 2.0 | 7.0 |
| 4 | narrow | low_no_pat_gain | plateau_rho_0.3 | 1.01 | 1.00 | 1.00 | 0.01 | 0.07 | -0.60 / -0.71 / -0.92 | 2.0 | 7.0 |
| 4 | narrow | high | none | 1.00 | 1.00 | 1.00 | 0.66 | 0.99 | -1.71 / -0.68 / -2.24 | 2.0 | 13.9 |
| 4 | narrow | high | plateau_rho_0.3 | 1.01 | 1.00 | 1.00 | 0.70 | 0.99 | -1.78 / -0.71 / -2.25 | 2.1 | 14.0 |
| 4 | narrow | high_no_pat_gain | none | 1.00 | 1.00 | 1.00 | 0.03 | 0.26 | -0.56 / -0.68 / -0.91 | 2.0 | 14.0 |
| 4 | narrow | high_no_pat_gain | plateau_rho_0.3 | 1.01 | 1.00 | 1.00 | 0.03 | 0.31 | -0.59 / -0.71 / -0.90 | 2.0 | 13.9 |
| 4 | moderate | none | none | 1.12 | 1.00 | 1.00 | 0.01 | 0.09 | -0.83 / -0.83 / -1.29 | 5.0 | — |
| 4 | moderate | none | plateau_rho_0.3 | 1.11 | 1.00 | 1.00 | 0.00 | 0.11 | -0.86 / -0.86 / -1.30 | 5.0 | — |
| 4 | moderate | low | none | 1.01 | 1.00 | 1.00 | 0.11 | 0.66 | -1.18 / -0.84 / -1.72 | 5.0 | 6.9 |
| 4 | moderate | low | plateau_rho_0.3 | 1.02 | 1.00 | 1.00 | 0.13 | 0.72 | -1.24 / -0.87 / -1.72 | 5.0 | 7.1 |
| 4 | moderate | low_no_pat_gain | none | 1.02 | 1.00 | 1.00 | 0.01 | 0.20 | -0.70 / -0.83 / -1.08 | 4.9 | 7.0 |
| 4 | moderate | low_no_pat_gain | plateau_rho_0.3 | 1.02 | 1.00 | 1.00 | 0.02 | 0.24 | -0.73 / -0.87 / -1.08 | 5.0 | 7.0 |
| 4 | moderate | high | none | 1.02 | 1.00 | 1.00 | 0.79 | 1.00 | -1.84 / -0.83 / -2.41 | 5.0 | 14.0 |
| 4 | moderate | high | plateau_rho_0.3 | 1.01 | 1.00 | 1.00 | 0.82 | 1.00 | -1.91 / -0.87 / -2.40 | 5.0 | 14.0 |
| 4 | moderate | high_no_pat_gain | none | 1.01 | 1.00 | 1.00 | 0.08 | 0.50 | -0.68 / -0.83 / -1.05 | 5.0 | 14.0 |
| 4 | moderate | high_no_pat_gain | plateau_rho_0.3 | 1.01 | 1.00 | 1.00 | 0.09 | 0.57 | -0.72 / -0.88 / -1.05 | 5.0 | 14.0 |
| 5 | narrow | none | none | 1.13 | 1.00 | 1.00 | 0.00 | 0.01 | -0.57 / -0.57 / -1.11 | 1.9 | — |
| 5 | narrow | none | plateau_rho_0.3 | 1.13 | 1.00 | 1.00 | 0.00 | 0.02 | -0.63 / -0.63 / -1.11 | 2.0 | — |
| 5 | narrow | low | none | 1.02 | 1.00 | 1.00 | 0.03 | 0.33 | -0.92 / -0.58 / -1.56 | 2.0 | 7.0 |
| 5 | narrow | low | plateau_rho_0.3 | 1.03 | 1.00 | 1.00 | 0.05 | 0.41 | -0.99 / -0.63 / -1.58 | 2.0 | 7.0 |
| 5 | narrow | low_no_pat_gain | none | 1.02 | 1.00 | 1.00 | 0.00 | 0.05 | -0.50 / -0.58 / -0.93 | 2.0 | 7.0 |
| 5 | narrow | low_no_pat_gain | plateau_rho_0.3 | 1.03 | 1.00 | 1.00 | 0.00 | 0.06 | -0.52 / -0.61 / -0.93 | 2.0 | 7.0 |
| 5 | narrow | high | none | 1.02 | 1.00 | 1.00 | 0.60 | 0.97 | -1.55 / -0.58 / -2.24 | 1.9 | 14.0 |
| 5 | narrow | high | plateau_rho_0.3 | 1.01 | 1.00 | 1.00 | 0.65 | 0.98 | -1.64 / -0.62 / -2.25 | 2.0 | 14.0 |
| 5 | narrow | high_no_pat_gain | none | 1.02 | 1.00 | 1.00 | 0.03 | 0.20 | -0.48 / -0.58 / -0.90 | 2.0 | 14.0 |
| 5 | narrow | high_no_pat_gain | plateau_rho_0.3 | 1.02 | 1.00 | 1.00 | 0.03 | 0.22 | -0.52 / -0.62 / -0.90 | 2.0 | 13.9 |
| 5 | moderate | none | none | 1.12 | 1.00 | 1.00 | 0.00 | 0.08 | -0.72 / -0.72 / -1.29 | 4.9 | — |
| 5 | moderate | none | plateau_rho_0.3 | 1.12 | 1.00 | 1.00 | 0.01 | 0.08 | -0.77 / -0.77 / -1.31 | 4.9 | — |
| 5 | moderate | low | none | 1.03 | 1.00 | 1.00 | 0.09 | 0.52 | -1.04 / -0.72 / -1.72 | 5.0 | 7.0 |
| 5 | moderate | low | plateau_rho_0.3 | 1.03 | 1.00 | 1.00 | 0.11 | 0.59 | -1.10 / -0.76 / -1.72 | 5.1 | 7.1 |
| 5 | moderate | low_no_pat_gain | none | 1.03 | 1.00 | 1.00 | 0.01 | 0.16 | -0.61 / -0.72 / -1.08 | 5.0 | 7.0 |
| 5 | moderate | low_no_pat_gain | plateau_rho_0.3 | 1.02 | 1.00 | 1.00 | 0.02 | 0.18 | -0.65 / -0.76 / -1.08 | 5.0 | 7.0 |
| 5 | moderate | high | none | 1.02 | 1.00 | 1.00 | 0.70 | 0.98 | -1.67 / -0.72 / -2.40 | 5.0 | 14.0 |
| 5 | moderate | high | plateau_rho_0.3 | 1.03 | 1.00 | 1.00 | 0.77 | 0.99 | -1.75 / -0.76 / -2.40 | 5.0 | 14.0 |
| 5 | moderate | high_no_pat_gain | none | 1.02 | 1.00 | 1.00 | 0.07 | 0.38 | -0.59 / -0.72 / -1.06 | 5.0 | 14.1 |
| 5 | moderate | high_no_pat_gain | plateau_rho_0.3 | 1.03 | 1.00 | 1.00 | 0.07 | 0.45 | -0.64 / -0.77 / -1.06 | 5.0 | 14.1 |
