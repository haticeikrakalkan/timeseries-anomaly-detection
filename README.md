# Time Series Anomaly Detection (NAB, unsupervised)

## Goal
Detect anomalies in a server CPU utilization series without using labels for training.
Labels are used only afterwards to check the results.

## Data
- Numenta Anomaly Benchmark (NAB), file `ec2_cpu_utilization_5f5533.csv`
- 4,032 rows, 5-minute intervals, 14 Feb - 28 Feb 2014, no missing time steps
- Ground truth: two anomaly windows from NAB's `combined_windows.json`
  1. 2014-02-18 16:02 - 2014-02-19 08:42
  2. 2014-02-24 10:17 - 2014-02-25 02:57
- The series moves through three levels (~46, ~43.5, ~38) with two sharp spikes
  (19 Feb 00:22 and 24 Feb 21:57). Hourly seasonality is weak.

## Methods
1. **Deviation score (baseline):** `|value - rolling mean| / rolling std` over the previous
   36 points (shifted by one so a point never sees itself). Alarm if score > 3.4.
2. **Isolation Forest:** features are `value` and the deviation score. Trained only on the
   period before the first anomaly window, tested on the rest.
3. **Robustness grid:** 48 Isolation Forest settings
   (n_estimators x contamination x random_state = 4 x 4 x 3).

Because labels are time windows rather than single points, success is measured as
"how many windows contain at least one alarm" and "how many alarms fall inside a window".
Accuracy is not used (about 90% of rows are normal).

## Results (test period)

| Method | Alarms | True | False | Windows caught |
|---|---|---|---|---|
| Deviation score (thr 3.4) | 5 | 4 | 1 | 2 / 2 |
| Isolation Forest (cont 0.002, 100 trees, seed 42) | 2 | 2 | 0 | 2 / 2 |

Robustness grid (48 runs): every run caught both windows. The difference is in false alarms.

| contamination | Behaviour across 12 runs |
|---|---|
| 0.001 | 2 alarms, 0 false alarms, identical in every run |
| 0.002 | 2-3 alarms, 0 false alarms |
| 0.003 | unstable: 3-17 alarms, 0-10 false alarms depending on the seed |
| 0.005 | stable but noisy: 13-17 alarms, 7-10 false alarms |

An early Isolation Forest trained on the whole series with `value` only flagged level
extremes instead of anomalies (394 alarms, only 55 inside windows).

## Limitations
- One file and two anomaly windows only. Results should not be generalized.
- The 3.4 threshold and the contamination range were chosen after looking at the labels,
  so the results are optimistic.
- Isolation Forest uses the baseline's score as a feature, so the two methods are not
  fully independent.
- Supervised learning was not used: two windows are too few to train and test fairly.
- GridSearchCV was not used, since tuning on so few labels would just fit the labels.

## Next steps
- Repeat on more NAB files.
- Refactor the notebook into tested Python modules, then add an API, Docker, CI and MLflow tracking.

## Files
- `01_exploratory_data_analysis.ipynb`: full analysis
- `ec2_cpu_utilization_5f5533.csv`: data