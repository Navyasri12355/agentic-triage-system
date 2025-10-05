"""
Resource Prediction Agent
- Forecasts ICU / oxygen / ventilator demand (next 1–24 hrs)
"""

import numpy as np
import datetime

def predict_resources():
    """
    Dummy forecast for now
    Replace with time-series ML model later
    """
    current_time = datetime.datetime.now()
    forecast = {
        "timestamp": str(current_time),
        "icu_beds": np.random.randint(10, 30),
        "oxygen_cylinders": np.random.randint(50, 100),
        "ventilators": np.random.randint(5, 15)
    }
    return forecast
