# simulator/machine.py
import requests
import time
import random
from datetime import datetime

URL = "http://127.0.0.1:8000/ingest"

# Make a list of 10 signals present for furnace signals
# Each signal content base_value like set-up value and tolerance
SIGNAL_CONFIGS = {
    "temperature_zone_1": (850.0, 10.0),    # 850°C +/- 5
    "temperature_zone_2": (250.0, 5.0),
    "main_gas_flow": (24.0, 3.0),          # 24 m3/h +/- 2
    "main_gas_pressure": (80.0, 10.0),
    "carbon_potential": (0.8, 0.05),       # 0.8% C +/- 0.05
    "oxygen_mV": (1150.0, 20.0),
    "addition_gas_flow": (350, 50),
    "addition_gas_pressure": (45.0, 5.0),
    "furnace_empty": (0, 1, "bool"),      # present for status running or not running
    "CO_percentage": (20, 3)
}


def generate_signal_value(signal_name):
    config = SIGNAL_CONFIGS.get(signal_name, (100.0, 5.0))

    # because furnace_empty has 3 parts, so if signal is furnace_empty, generate 3 attributes
    if len(config) == 3:
        base_val, tolerance, sig_type = config
    else:
        base_val, tolerance = config
        sig_type = "float"

    # Solve for Boolean (0/1)
    if sig_type == "bool":
        # 90% correct status base_val, 10% change status
        return base_val if random.random() > 0.1 else (1 if base_val == 0 else 0)

    # Logic for numeric attributes
    is_anomaly = random.random() < 0.05
    if is_anomaly:
        return random.choice([round(base_val * 5, 2), 0.0])

    return round(base_val + random.uniform(-tolerance, tolerance), 2)


while True:
    payloads = []
    timestamp = datetime.now().isoformat()

    for sig in SIGNAL_CONFIGS:
        payloads.append({
            "machine_id": "FURNACE-001",
            "signal_name": sig,
            "value": generate_signal_value(sig),
            "timestamp": timestamp
        })

    # Send 10 signal to FastAPI
    try:
        response = requests.post(URL, json=payloads)
        print(f"Sent {len(SIGNAL_CONFIGS)} signals at {timestamp} - Status: {response.status_code}")
    except Exception as e:
        print(f"Connection Error: {e}")

    time.sleep(2)  # Send signal every 2 seconds