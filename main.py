from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from anomaly import compute_score, detect_alarms

app = FastAPI()

class Series(BaseModel):
    values: list[float]


@app.get("/")

def home():
    return {"status": "ok"}

@app.post("/detect")

def detect(data: Series):
    values = pd.Series(data.values)
    if len(values) < 37:
        return {"alarms": [], "warning": "At least 37 values ​​are required"}
    score = compute_score(values)
    alarms = detect_alarms(score)
    return {"alarms": alarms[alarms == 1].index.tolist()}