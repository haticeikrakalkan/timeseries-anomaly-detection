from anomaly import compute_score, detect_alarms, evaluate
import pandas as pd

def test_spike_is_detected():
    values = pd.Series([10, 11] * 50)
    values[80] = 50
    score = compute_score(values)
    alarms = detect_alarms(score)
    assert alarms[80] == 1
    assert alarms.sum() == 1

def test_evaluate_counts():
    times = pd.Series(pd.date_range("2014-01-01", periods=10, freq="5min"))
    alarm = pd.Series([0, 0, 0, 1, 0, 0, 0, 0, 1, 0])
    labels = pd.Series([0, 0, 1, 1, 1, 0, 0, 0, 0, 0])
    windows = [(times[2], times[4])]
    result = evaluate(alarm, labels, times, windows)

    assert result["alarm"] == 2
    assert result["true_alarm"] == 1
    assert result["false_alarm"] == 1
    assert result["windows_caught"] == 1