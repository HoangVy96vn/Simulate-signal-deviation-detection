from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import pandas as pd
import os
from collections import deque
from datetime import datetime

app = FastAPI(title="Industrial Deviation Management System")

# Tự động tạo thư mục chứa dữ liệu
os.makedirs("data", exist_ok=True)

# Bộ nhớ tạm lưu 5 giá trị gần nhất để tính toán Spike (L2)
history = {}

class Signal(BaseModel):
    machine_id: str
    signal_name: str
    value: float
    timestamp: str

# --- CẤU HÌNH NGƯỠNG (LEVEL 1) ---
THRESHOLDS = {
    "temperature_zone_1": (800.0, 870.0),
    "temperature_zone_2": (230.0, 270.0),
    "main_gas_pressure": (60.0, 100.0),
    "carbon_potential": (0.7, 0.9),
    "oxygen_mV": (1100.0, 1200.0),
    "CO_percentage": (15.0, 25.0)
}

def save_to_csv(sig: Signal):
    """Ghi dữ liệu tín hiệu vào file CSV chính"""
    file_path = f"data/{sig.machine_id}.csv"
    # Dùng model_dump() cho Pydantic v2, dict() cho v1
    data = sig.model_dump() if hasattr(sig, 'model_dump') else sig.dict()
    df = pd.DataFrame([data])
    df.to_csv(file_path, mode='a', header=not os.path.exists(file_path), index=False)

def save_alert_to_csv(alert_msg):
    """Ghi log cảnh báo vào file riêng để Dashboard hiển thị"""
    alert_file = "data/alerts_log.csv"
    new_alert = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": alert_msg
    }
    df = pd.DataFrame([new_alert])
    df.to_csv(alert_file, mode='a', header=not os.path.exists(alert_file), index=False)

@app.post("/ingest")
async def ingest_data(signals: List[Signal]):
    alerts_triggered = []

    for sig in signals:
        # --- LEVEL 1: KIỂM TRA NGƯỠNG ---
        if sig.signal_name in THRESHOLDS:
            lower, upper = THRESHOLDS[sig.signal_name]
            if sig.value > upper or sig.value < lower:
                msg = f"⚠️ [L1-RANGE] {sig.signal_name} out of range! Val: {sig.value} ({lower}-{upper})"
                alerts_triggered.append(msg)
                save_alert_to_csv(msg)

        # --- LEVEL 2: PHÁT HIỆN ĐỘT BIẾN (SPIKE) ---
        if sig.signal_name != "furnace_empty":
            if sig.signal_name not in history:
                history[sig.signal_name] = deque(maxlen=5)

            if len(history[sig.signal_name]) == 5:
                avg_recent = sum(history[sig.signal_name]) / 5
                # Nếu lệch quá 20% so với trung bình 5 điểm trước
                if avg_recent > 0 and abs(sig.value - avg_recent) > (avg_recent * 0.2):
                    msg = f"⚡ [L2-SPIKE] {sig.signal_name} sudden change! Val: {sig.value} (Avg: {round(avg_recent, 2)})"
                    alerts_triggered.append(msg)
                    save_alert_to_csv(msg)

            history[sig.signal_name].append(sig.value)

        # --- GHI DỮ LIỆU GỐC ---
        save_to_csv(sig)

    # In ra terminal để theo dõi nhanh
    if alerts_triggered:
        print(f"\n--- Alert at {datetime.now().strftime('%H:%M:%S')} ---")
        for a in alerts_triggered:
            print(a)

    return {"status": "success", "alerts_count": len(alerts_triggered)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)