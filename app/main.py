from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import pandas as pd
import os
from collections import deque
from datetime import datetime

app = FastAPI(title="Advanced Deviation Detection System")

# Tự động tạo thư mục chứa dữ liệu
os.makedirs("data", exist_ok=True)

# Bộ nhớ tạm lưu 5 giá trị gần nhất của từng tín hiệu để so sánh Spike
# Cấu trúc: { "signal_name": deque([v1, v2, v3, v4, v5], maxlen=5) }
history = {}


class Signal(BaseModel):
    machine_id: str
    signal_name: str
    value: float
    timestamp: str


# --- CẤU HÌNH NGƯỠNG CẢNH BÁO (LEVEL 1) ---
# Định nghĩa: (Cận dưới, Cận trên)
THRESHOLDS = {
    "temperature_zone_1": (840.0, 860.0),
    "temperature_zone_2": (245.0, 255.0),
    "main_gas_pressure": (70.0, 90.0),
    "carbon_potential": (0.85, 0.95),
    "oxygen_mV": (1100.0, 1200.0),
    "CO_percentage": (17.0, 23.0)
}


@app.post("/ingest")
async def ingest_data(signals: List[Signal]):
    alerts = []

    for sig in signals:
        # --- LEVEL 1: KIỂM TRA NGƯỠNG (OUT OF RANGE) ---
        if sig.signal_name in THRESHOLDS:
            lower, upper = THRESHOLDS[sig.signal_name]
            if sig.value > upper or sig.value < lower:
                msg = f"⚠️ [L1-RANGE] {sig.signal_name} out of range! Value: {sig.value} (Limit: {lower}-{upper})"
                alerts.append(msg)

        # --- LEVEL 2: KIỂM TRA ĐỘT BIẾN (SUDDEN CHANGE/SPIKE) ---
        # Chỉ kiểm tra Spike cho các tín hiệu liên tục, bỏ qua tín hiệu trạng thái (0/1)
        if sig.signal_name != "furnace_empty":
            if sig.signal_name not in history:
                history[sig.signal_name] = deque(maxlen=5)

            # Nếu đã có đủ 5 điểm dữ liệu trước đó, bắt đầu so sánh
            if len(history[sig.signal_name]) == 5:
                avg_recent = sum(history[sig.signal_name]) / 5

                # Nếu giá trị mới lệch quá 20% so với trung bình 5 điểm trước đó
                # (Tránh chia cho 0 nếu avg = 0)
                if avg_recent > 0 and abs(sig.value - avg_recent) > (avg_recent * 0.2):
                    msg = f"⚡ [L2-SPIKE] {sig.signal_name} sudden change! Value: {sig.value} (Avg of last 5: {round(avg_recent, 2)})"
                    alerts.append(msg)

            # Cập nhật giá trị mới vào bộ nhớ lịch sử
            history[sig.signal_name].append(sig.value)

        # --- GHI DỮ LIỆU ---
        save_to_csv(sig)

    # In cảnh báo ra Terminal của Server để Vy dễ theo dõi
    if alerts:
        print(f"\n--- {datetime.now().strftime('%H:%M:%S')} NEW ALERTS ---")
        for a in alerts:
            print(a)

    return {
        "status": "success",
        "alerts_count": len(alerts),
        "alerts_detail": alerts
    }


def save_to_csv(sig: Signal):
    file_path = f"data/{sig.machine_id}.csv"
    # Pydantic v2 dùng .model_dump(), v1 dùng .dict()
    df = pd.DataFrame([sig.dict()])
    df.to_csv(file_path, mode='a', header=not os.path.exists(file_path), index=False)


if __name__ == "__main__":
    import uvicorn
    from datetime import datetime

    uvicorn.run(app, host="127.0.0.1", port=8000)