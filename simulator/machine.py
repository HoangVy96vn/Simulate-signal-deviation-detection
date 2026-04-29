# simulator/machine.py
import requests
import time
import random
from datetime import datetime

URL = "http://127.0.0.1:8000/ingest"

# Make a list of 10 signals present for furnace signals
# Each signal content base_value like set-up value and tolerance
SIGNAL_CONFIGS = {
    "temperature_zone_1": (850.0, 5.0),    # 850°C +/- 5
    "temperature_zone_2": (845.0, 5.0),
    "main_gas_flow": (24.0, 2.0),          # 24 m3/h +/- 2
    "main_gas_pressure": (50.0, 3.0),
    "carbon_potential": (0.8, 0.05),       # 0.8% C +/- 0.05
    "oxygen_mV": (1150.0, 10.0),
    "addition_gas_flow": (5.0, 1.0),
    "addition_gas_pressure": (45.0, 2.0),
    "furnace_loading": (1000.0, 0.0),      # Tải trọng cố định
    "furnace_empty": (0.0, 0.0)
}


def generate_signal_value(signal_name):
    """Generate signal with 5% abnormality"""
    base_val = 100.0
    # set 5% abnormality
    is_anomaly = random.random() < 0.05

    if is_anomaly:
        # Abnormality: Signal out or loss
        return random.choice([base_val * 5, 0.0])

    # Normal: Signal values around base_val +/- 5%
    return round(base_val + random.uniform(-5.0, 5.0), 2)


while True:
    payloads = []
    timestamp = datetime.now().isoformat()

    for sig in SIGNALS:
        payloads.append({
            "machine_id": "FURNACE-001",
            "signal_name": sig,
            "value": generate_signal_value(sig),
            "timestamp": timestamp
        })

    # Send 10 signal to FastAPI
    try:
        response = requests.post(URL, json=payloads)
        print(f"Sent {len(SIGNALS)} signals at {timestamp} - Status: {response.status_code}")
    except Exception as e:
        print(f"Connection Error: {e}")

    time.sleep(2)  # Send signal every 2 seconds