import requests
import time
import random
from datetime import datetime

URL = "http://127.0.0.1:8000/ingest"

SIGNAL_CONFIGS = {
    "temperature_zone_1": (850.0, 10.0),
    "temperature_zone_2": (250.0, 5.0),
    "main_gas_flow": (24.0, 3.0),
    "main_gas_pressure": (80.0, 10.0),
    "carbon_potential": (0.9, 0.05),
    "oxygen_mV": (1150.0, 50.0),
    "addition_gas_flow": (350.0, 50.0),
    "addition_gas_pressure": (45.0, 5.0),
    "furnace_empty": (0, 1, "bool"),
    "CO_percentage": (20.0, 3.0)
}


def generate_signal_value(signal_name):
    config = SIGNAL_CONFIGS.get(signal_name, (100.0, 5.0))

    # Chỉ lấy 2 giá trị đầu vì logic bool đã xử lý riêng ở dưới
    base_val, tolerance = config[0], config[1]

    is_anomaly = random.random() < 0.05
    if is_anomaly:
        return random.choice([round(base_val * 1.5, 2), 0.0])  # Giảm mức vọt xuống 1.5 để test L2-Spike dễ hơn

    return round(base_val + random.uniform(-tolerance, tolerance), 2)


# --- KHỞI TẠO BIẾN CHO BATCH ---
counter = 0
current_status = 0  # 0: Running, 1: Empty

print("--- Start Simulator ---")

while True:
    payloads = []
    timestamp = datetime.now().isoformat()

    # 1. Quản lý trạng thái Mẻ (Batch)
    counter += 1
    if counter >= 15:  # Đảo trạng thái sau mỗi 30 giây (15 lần * 2 giây)
        current_status = 1 if current_status == 0 else 0
        counter = 0
        print(f"🔄 Furnace changed status to: {'EMPTY' if current_status == 1 else 'RUNNING'}")

    # 2. Tạo dữ liệu cho 10 tín hiệu
    for sig in SIGNAL_CONFIGS:
        if sig == "furnace_empty":
            val = float(current_status)  # Đảm bảo gửi dạng số
        else:
            val = generate_signal_value(sig)

        payloads.append({
            "machine_id": "FURNACE-001",
            "signal_name": sig,
            "value": val,
            "timestamp": timestamp
        })

    # 3. Gửi dữ liệu
    try:
        response = requests.post(URL, json=payloads, timeout=5)
        print(f"Sent {len(payloads)} signals - Status: {response.status_code}")
    except Exception as e:
        print(f"Connection Error: {e}")

    time.sleep(2)