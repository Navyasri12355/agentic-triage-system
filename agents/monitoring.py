# agents/monitoring.py
from data.mqtt_client import start_mqtt_listener
from db.mongo_client import insert_vitals
import datetime

def process_vitals(vitals):
    # Add timestamp
    vitals["timestamp"] = datetime.datetime.utcnow().isoformat()
    
    # Split BP into SBP and DBP
    if "bp" in vitals:
        sbp, dbp = map(int, vitals["bp"].split("/"))
    else:
        sbp, dbp = 120, 80  # default if missing
    vitals["sbp"] = sbp
    vitals["dbp"] = dbp

    # Age calculation from DOB
    dob = vitals.get("dob")
    if dob:
        birth_year = int(dob.split("-")[0])
        age = datetime.datetime.now().year - birth_year
    else:
        age = 30
    vitals["age"] = age

    # Pulse pressure and MAP
    pulse_pressure = sbp - dbp
    map_val = dbp + (1/3) * pulse_pressure
    vitals["pulse_pressure"] = pulse_pressure
    vitals["map"] = round(map_val, 1)

    # Shock index
    hr = vitals.get("hr", 70)
    shock_index = hr / sbp
    vitals["shock_index"] = round(shock_index, 2)

    # Abnormal count from boolean flags
    dyspnea = int(vitals.get("dyspnea", 0))
    chest_pain = int(vitals.get("chest_pain", 0))
    confusion = int(vitals.get("confusion", 0))
    abnormal_count = dyspnea + chest_pain + confusion
    vitals["abnormal_count"] = abnormal_count

    # Anomaly detection
    vitals["anomaly_flag"] = False
    vitals["anomaly_reasons"] = []

    if vitals.get("spo2", 0) < 90:
        vitals["anomaly_flag"] = True
        vitals["anomaly_reasons"].append("low_spo2")
    if hr > 120 or hr < 40:
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
