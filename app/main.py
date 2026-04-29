from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import pandas as pd
import os

app = FastAPI()


class Signal(BaseModel):
    machine_id: str
    signal_name: str
    value: float
    timestamp: str


# Thresholds for warning (optional)
THRESHOLDS = {"temp_core": 120.0, "gas_pressure": 110.0}


@app.post("/ingest")
async def ingest_data(signals: List[Signal]):
    alerts = []

    for sig in signals:
        # 1. Logic: Check if signal is out of threshold
        if sig.signal_name in THRESHOLDS and sig.value > THRESHOLDS[sig.signal_name]:
            alert_msg = f"CRITICAL: {sig.signal_name} exceeded threshold! Value: {sig.value}"
            alerts.append(alert_msg)
            print(alert_msg)

        # 2. Storage: record data to csv file (In reality, data are recorded into Data Lake)
        save_to_csv(sig)

    return {"status": "success", "alerts_triggered": alerts}

# function for saving data to csv file
def save_to_csv(sig: Signal):
    file_path = f"data/{sig.machine_id}.csv"
    df = pd.DataFrame([sig.dict()])
    df.to_csv(file_path, mode='a', header=not os.path.exists(file_path), index=False)