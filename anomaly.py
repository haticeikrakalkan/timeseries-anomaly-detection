import pandas as pd
from sklearn.ensemble import IsolationForest


def compute_score(values, window=36):
    prev_mean = values.rolling(window).mean().shift(1)
    prev_std = values.rolling(window).std().shift(1)
    score = ((values - prev_mean) / prev_std).abs()
    return score

def detect_alarms(score, threshold=3.4):
    return (score > threshold).astype(int)

def detect_isolation_forest(X_train, X_test, n_estimators=100, contamination=0.002, random_state=42):
    model = IsolationForest(contamination=contamination,
                            n_estimators=n_estimators,
                            random_state=random_state)
    model.fit(X_train)
    y_pred = model.predict(X_test)
    return pd.Series((y_pred == -1).astype(int), index=X_test.index)



def evaluate(alarm, labels, times, windows):
    alarm = alarm == 1
    true_alarm  = (alarm & (labels == 1)).sum()
    false_alarm = (alarm & (labels == 0)).sum()
    windows_caught = 0
    for start, end in windows:
        if (alarm & (times >= start) & (times <= end)).sum() > 0:
            windows_caught += 1
    return {"alarm": alarm.sum(), "true_alarm": true_alarm, "false_alarm": false_alarm, "windows_caught": windows_caught}