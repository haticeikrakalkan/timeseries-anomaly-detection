import pandas as pd
from anomaly import compute_score, detect_isolation_forest, evaluate
import mlflow
from itertools import product

df = pd.read_csv("ec2_cpu_utilization_5f5533.csv", parse_dates=["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)
df["score"] = compute_score(df["value"])
df["is_anomaly"] = ((("2014-02-18 16:02:00" < df["timestamp"]) &  (df["timestamp"]< "2014-02-19 08:42:00")) | (("2014-02-24 10:17:00" < df["timestamp"]) &  (df["timestamp"]< "2014-02-25 02:57:00"))).astype(int)

X_train = df[["score","value"]][(df["score"].notna()) & (df["timestamp"] < "2014-02-18 16:02:00")]
X_test = df[["score","value"]][(df["score"].notna()) & (df["timestamp"] >= "2014-02-18 16:02:00")]

windows = [("2014-02-18 16:02", "2014-02-19 08:42"), ("2014-02-24 10:17", "2014-02-25 02:57")]
alarm = detect_isolation_forest(X_train, X_test)
labels = df.loc[X_test.index, "is_anomaly"]
times = df.loc[X_test.index, "timestamp"]
result = evaluate(alarm, labels, times, windows)


contaminations = [0.001,0.002,0.003,0.005]
random_states = [42,7,123]
n_estimators_list = [50,100,200,300]
mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("isolation-forest-grid")
for n, c, r in product(n_estimators_list, contaminations, random_states):
    with mlflow.start_run():
        mlflow.log_params({"n_estimators": n, "contamination": c, "random_state": r})
        alarm = detect_isolation_forest(X_train, X_test, n_estimators=n, contamination=c, random_state=r)
        result = evaluate(alarm, labels, times, windows)
        mlflow.log_metrics({
            "alarm": int(result["alarm"]),
            "true_alarm": int(result["true_alarm"]),
            "false_alarm": int(result["false_alarm"]),
            "windows_caught": int(result["windows_caught"]),
        })
