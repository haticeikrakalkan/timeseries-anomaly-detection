# Time Series Anomaly Detection (NAB, unsupervised)

![CI](https://github.com/haticeikrakalkan/timeseries-anomaly-detection/actions/workflows/ci.yml/badge.svg)

**Live API:** https://anomaly-api-ttnm.onrender.com (Swagger UI: `/docs`)

> The API runs on Render's free plan. After a period of inactivity it spins down, so the first request can take around 30 seconds.

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

## Project structure

| File                                 | Purpose |
|--------------------------------------|---|
| `01_exploratory_data_analysis.ipynb` | Full analysis |
| `anomaly.py`                         | `compute_score`, `detect_alarms`, `detect_isolation_forest`, `evaluate` |
| `main.py`                            | FastAPI app (`GET /`, `POST /detect`) |
| `test_anomaly.py`                    | pytest tests (5 tests) |
| `run_experiments.py`                 | Logs the 48-setting grid to MLflow |
| `Dockerfile`, `.dockerignore`        | Container image for the API |
| `.github/workflows/ci.yml`           | GitHub Actions: runs the tests on every push |
| `ec2_cpu_utilization_5f5533.csv`     | Data |

## API

`POST /detect` takes a list of numbers and returns the indices of the alarms. The score needs a 36-value window, so at least 37 values are required.

```bash
curl -X POST https://anomaly-api-ttnm.onrender.com/detect \
  -H "Content-Type: application/json" \
  -d '{"values": [10, 11, 10, 11, ...]}'
```

Response: `{"alarms": [36]}`. If fewer than 37 values are sent: `{"alarms": [], "warning": "At least 37 values are required"}`.

## Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Tests

```bash
pytest -q
```

The tests cover the deviation score, the `evaluate` function, Isolation Forest and two API scenarios (spike detection, short series). CI runs them on every push to `main`.

## Docker

```bash
docker build -t anomaly-api .
docker run -p 8000:8000 anomaly-api
```

The live service is built from the same Dockerfile on Render and redeploys on every push to `main`.

## Experiment tracking (MLflow)

MLflow is not part of the API image (to keep it small); it is only needed for experiments:

```bash
pip install mlflow
python run_experiments.py
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Open `http://127.0.0.1:5000` to compare the 48 runs by parameters (`n_estimators`, `contamination`, `random_state`) and metrics (`alarm`, `true_alarm`, `false_alarm`, `windows_caught`).

## Limitations
- One file and two anomaly windows only. Results should not be generalized.
- The 3.4 threshold and the contamination range were chosen after looking at the labels,
  so the results are optimistic.
- Isolation Forest uses the baseline's score as a feature, so the two methods are not
  fully independent.
- Supervised learning was not used: two windows are too few to train and test fairly.
- GridSearchCV was not used, since tuning on so few labels would just fit the labels.
- If the previous 36 values are all identical, the standard deviation is 0 and the score
  becomes infinite. Rare in real CPU data, but an edge case.
- The tests emit a deprecation warning about using `httpx` with `starlette.testclient`.
  It does not affect functionality for now.

## Next steps
- Repeat on more NAB files.
- Split the notebook into smaller ones.