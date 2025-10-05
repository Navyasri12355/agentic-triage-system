"""
Triage Agent
- Computes dynamic severity score
- Uses hybrid rule-based + ML model (XGBoost placeholder here)
"""

import joblib

# Load ML model (placeholder)
try:
    model = joblib.load("models/triage_model.pkl")
except:
    model = None

def compute_triage(patient_data: dict):
    """
    Input: patient vitals + symptoms
    Output: severity score/class
    """
    # TODO: Preprocess patient_data
    if model:
        # Example: ML-based prediction
        features = [patient_data.get("heart_rate", 80),
                    patient_data.get("oxygen_saturation", 98)]
        severity = model.predict([features])[0]
    else:
        # Fallback: simple rules
        if patient_data.get("oxygen_saturation", 98) < 90:
            severity = "Critical"
        else:
            severity = "Stable"
    return severity
