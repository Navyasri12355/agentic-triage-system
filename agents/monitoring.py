"""
Monitoring Agent
- Ingests streaming patient vitals / RFID / EHR data
- Normalizes input
- Flags anomalies
"""

def ingest_data(source: dict):
    """
    source: dict from IoT devices, RFID, or EHR
    Returns normalized data
    """
    # TODO: normalize input, handle missing values
    normalized = source
    return normalized

def detect_anomalies(data: dict):
    """
    Checks for abnormal vitals or missing info
    """
    # TODO: add anomaly detection logic
    if data.get("heart_rate", 0) > 180:
        return True
    return False
