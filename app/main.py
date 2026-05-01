from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import pandas as pd
import os
from collections import deque
from datetime import datetime

app = FastAPI(title="Advanced Deviation Detection System")

# Auto create folder for data storage
os.makedirs("data", exist_ok=True)

# Create dictionary for storing the last 5 signal values to analyze spike in process
# Structure: { "signal_name": deque([v1, v2, v3, v4, v5], maxlen=5) }
history = {}


class Signal(BaseModel):
    machine_id: str
    signal_name: str
    value: float
    timestamp: str


# --- Alert level 1 for signals out of control limit ---
# Identify control limit for required signals:
THRESHOLDS = {
    "temperature_zone_1": (840.0, 860.0),
    "temperature_zone_2": (245.0, 255.0),
    "main_gas_flow": (21.0, 27.0),
    "main_gas_pressure": (70.0, 90.0),
    "carbon_potential": (0.85, 0.95),
    "oxygen_mV": (1100.0, 1200.0),
    "CO_percentage": (17.0, 23.0)
}

def save_alert_to_csv(alert_msg):
    alert_path = "data/alerts_log.csv"
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_alert = pd.DataFrame([{"timestamp": now, "message": alert_msg}])
    new_alert.to_csv(alert_path, mode='a', header=not os.path.exists(alert_path), index=False)


@app.post("/ingest")
async def ingest_data(signals: List[Signal]):
    alerts = []
    for sig in signals:
        # Check alert Level 1
        if sig.signal_name in THRESHOLDS:
            lower, upper = THRESHOLDS[sig.signal_name]
            if sig.value > upper or sig.value < lower:
                msg = f"⚠️ [L1-RANGE] {sig.signal_name} out of range! Value: {sig.value}"
                alerts.append(msg)
                save_alert_to_csv(msg)

        # Check alert Level 2 (Spike)
        if sig.signal_name != "furnace_empty":
            if sig.signal_name not in history:
                history[sig.signal_name] = deque(maxlen=5)
            if len(history[sig.signal_name]) == 5:
                avg_recent = sum(history[sig.signal_name]) / 5
                if avg_recent > 0 and abs(sig.value - avg_recent) > (avg_recent * 0.15):  # if signal out 15% average of last 5 points -> spike
                    msg = f"⚡ [L2-SPIKE] {sig.signal_name} sudden change! Value: {sig.value}"
                    alerts.append(msg)
                    save_alert_to_csv(msg)
            history[sig.signal_name].append(sig.value)

        save_to_csv(sig)
    return {"status": "success", "alerts_count": len(alerts)}


def save_to_csv(sig: Signal):
    file_path = f"data/{sig.machine_id}.csv"
    df = pd.DataFrame([sig.dict()])
    df.to_csv(file_path, mode='a', header=not os.path.exists(file_path), index=False)


if __name__ == "__main__":
    import uvicorn
    from datetime import datetime

    uvicorn.run(app, host="127.0.0.1", port=8000)