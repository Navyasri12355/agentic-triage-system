# agents/monitoring.py
from data.mqtt_client import start_mqtt_listener
from db.mongo_client import insert_vitals
import datetime

def process_vitals(vitals):
    vitals["timestamp"] = datetime.datetime.utcnow().isoformat()

    # Basic checks
    vitals["anomaly_flag"] = False
    vitals["anomaly_reasons"] = []

    if vitals.get("spo2", 0) < 90:
        vitals["anomaly_flag"] = True
        vitals["anomaly_reasons"].append("low_spo2")
    if vitals.get("hr", 0) > 120 or vitals.get("hr", 0) < 40:
        vitals["anomaly_flag"] = True
        vitals["anomaly_reasons"].append("hr_out_of_range")
    if vitals.get("temp", 0) > 38:
        vitals["anomaly_flag"] = True
        vitals["anomaly_reasons"].append("fever")

    insert_vitals(vitals)
    print(f"📥 Saved vitals for patient {vitals.get('patient_id')} → anomaly={vitals['anomaly_flag']}")

def main():
    start_mqtt_listener(process_vitals)
    print("🩺 Monitoring Agent running... (listening on vitals/stream)")
    while True:
        pass

if __name__ == "__main__":
    main()
