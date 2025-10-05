
import os
import sys
import logging
import pandas as pd
from prophet import Prophet
from datetime import datetime, timedelta
import joblib
import numpy as np
import time

# --- FastAPI and Pydantic Imports ---
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict


# --- Embedded api_models.py classes (simplified to only what's needed for output) ---
# Note: For a real project, you would import these from a shared api_models.py file.
# They are embedded here for the "single file" requirement.
class Vitals(BaseModel): # Included for completeness, though not directly used in this agent's API
    heart_rate: int
    blood_pressure_systolic: int
    blood_pressure_diastolic: int
    respiratory_rate: int
    temperature: float
    oxygen_saturation: float
    consciousness_level: str
    pain_level: Optional[int]

class PatientInflow(BaseModel): # Included for completeness
    patient_id: str
    timestamp: datetime = datetime.now()
    gender: str
    age: int
    presenting_complaint: str
    vitals: Vitals

class HospitalResource(BaseModel): # Included for completeness and potential mock data if needed
    hospital_id: str
    name: str
    location: str
    icu_beds_total: int
    icu_beds_occupied: int
    ventilators_total: int
    ventilators_occupied: int
    oxygen_cylinders_total: Optional[int] = 0
    oxygen_cylinders_occupied: Optional[int] = 0
    current_patients_count: int
    max_capacity: int

class ResourceForecastItem(BaseModel):
    timestamp: datetime
    icu_demand_forecast: int
    ventilator_demand_forecast: int
    oxygen_demand_forecast: int

class ResourceForecastResponse(BaseModel):
    forecast: List[ResourceForecastItem]

# --- End of Embedded api_models.py classes ---


# --- Embedded generate_dummy_demand.py logic ---
def generate_dummy_data_func(start_date, end_date, output_path):
    dates = pd.date_range(start=start_date, end=end_date, freq='H')
    data = []
    for i, ts in enumerate(dates):
        base_icu = 10 + 5 * np.sin(i / 24 * 2 * np.pi) + 3 * np.sin(i / (24*7) * 2 * np.pi)
        base_vent = 5 + 3 * np.sin(i / 24 * 2 * np.pi) + 2 * np.sin(i / (24*7) * 2 * np.pi)
        base_oxygen = 50 + 15 * np.sin(i / 12 * 2 * np.pi) + 10 * np.sin(i / (24*7) * 2 * np.pi) + 0.1 * (i / (24*30))

        icu_demand = max(0, round(base_icu + np.random.normal(0, 2)))
        ventilator_demand = max(0, round(base_vent + np.random.normal(0, 1)))
        oxygen_demand = max(0, round(base_oxygen + np.random.normal(0, 5)))

        data.append({
            'timestamp': ts,
            'icu_demand': icu_demand,
            'ventilator_demand': ventilator_demand,
            'oxygen_demand': oxygen_demand
        })
            
    df = pd.DataFrame(data)
    
    temp_output_path = output_path + ".tmp"
    try:
        df.to_csv(temp_output_path, index=False)
        os.rename(temp_output_path, output_path)
        logger.info(f"Successfully generated dummy data and saved to '{output_path}'.")
    except Exception as e:
        logger.error(f"Error saving dummy data to '{output_path}': {e}", exc_info=True)
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)
        raise

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastAPI App Initialization ---
app = FastAPI(title="Resource Prediction Agent")

# Allow frontend requests (React/Streamlit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Model and Data File Paths ---
MODEL_PATH = "resource_forecast.pkl"
DATA_PATH = "historical_demand.csv"

# --- Helper function to load historical data (using Pandas directly) ---
def get_historical_demand_data() -> pd.DataFrame:
    """
    Loads historical demand data using Pandas directly from CSV.
    """
    logger.info(f"Attempting to read '{DATA_PATH}' from current directory: '{os.getcwd()}'")
    logger.info(f"Directory contents before read: {os.listdir(os.getcwd())}")
    try:
        if not os.path.exists(DATA_PATH):
            logger.error(f"File '{DATA_PATH}' does not exist at '{os.getcwd()}' before pandas attempts to read.")
            return pd.DataFrame(columns=['timestamp', 'icu_demand', 'ventilator_demand', 'oxygen_demand'])

        df = pd.read_csv(DATA_PATH)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        logger.info(f"Successfully loaded {len(df)} historical records using Pandas from {DATA_PATH}")
        return df
    except Exception as e:
        logger.error(f"Error loading historical data with Pandas from {DATA_PATH} (in '{os.getcwd()}'): {e}", exc_info=True)
        return pd.DataFrame(columns=['timestamp', 'icu_demand', 'ventilator_demand', 'oxygen_demand'])

# --- Forecasting Logic to incorporate saving/loading for all three resources ---
def generate_forecast(horizon_hours: int = 24, retrain_if_needed: bool = True) -> List[ResourceForecastItem]:
    logger.info(f"Generating forecast for {horizon_hours} hours...")

    model_icu = None
    model_vent = None
    model_oxygen = None
    
    # Try to load the combined models
    if os.path.exists(MODEL_PATH) and retrain_if_needed:
        try:
            combined_models = joblib.load(MODEL_PATH)
            model_icu = combined_models.get("icu_model")
            model_vent = combined_models.get("vent_model")
            model_oxygen = combined_models.get("oxygen_model")
            if model_icu and model_vent and model_oxygen:
                logger.info(f"Loaded combined Prophet models from {MODEL_PATH}.")
            else:
                logger.warning(f"Combined models from {MODEL_PATH} incomplete or corrupt. Retraining will occur.")
                model_icu, model_vent, model_oxygen = None, None, None
        except Exception as e:
            logger.warning(f"Could not load combined models from {MODEL_PATH}: {e}. Retraining will occur.")
            model_icu, model_vent, model_oxygen = None, None, None

    # If models not loaded (or if retraining forced)
    if model_icu is None or model_vent is None or model_oxygen is None:
        logger.info("Training/Retraining all ICU, Ventilator, and Oxygen Prophet models...")
        
        historical_df = get_historical_demand_data()
        if historical_df.empty:
            logger.error("No historical data available for training. Cannot proceed.")
            return []

        # Train ICU model
        df_icu = historical_df.rename(columns={'timestamp': 'ds', 'icu_demand': 'y'})
        model_icu = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False)
        model_icu.fit(df_icu)

        # Train Ventilator model
        df_vent = historical_df.rename(columns={'timestamp': 'ds', 'ventilator_demand': 'y'})
        model_vent = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False)
        model_vent.fit(df_vent)

        # New: Train Oxygen model
        df_oxygen = historical_df.rename(columns={'timestamp': 'ds', 'oxygen_demand': 'y'})
        model_oxygen = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False)
        model_oxygen.fit(df_oxygen)

        # Save the combined models into a single dictionary
        combined_models = {
            "icu_model": model_icu,
            "vent_model": model_vent,
            "oxygen_model": model_oxygen
        }
        joblib.dump(combined_models, MODEL_PATH)
        logger.info(f"Combined Prophet models saved to {MODEL_PATH}")

    forecasts = []

    # Generate forecast using the (loaded or newly trained) models
    if model_icu and model_vent and model_oxygen:
        # ICU Forecast
        future_icu = model_icu.make_future_dataframe(periods=horizon_hours, freq='H')
        forecast_icu = model_icu.predict(future_icu)
        icu_preds_df = forecast_icu[['ds', 'yhat']].tail(horizon_hours)

        # Ventilator Forecast
        future_vent = model_vent.make_future_dataframe(periods=horizon_hours, freq='H')
        forecast_vent = model_vent.predict(future_vent)
        vent_preds_df = forecast_vent[['ds', 'yhat']].tail(horizon_hours)

        # Oxygen Forecast
        future_oxygen = model_oxygen.make_future_dataframe(periods=horizon_hours, freq='H')
        forecast_oxygen = model_oxygen.predict(future_oxygen)
        oxygen_preds_df = forecast_oxygen[['ds', 'yhat']].tail(horizon_hours)

        # Combine and format results for all three
        start_time_forecast = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        for i in range(horizon_hours):
            current_forecast_time = start_time_forecast + timedelta(hours=i)
            icu_val, vent_val, oxygen_val = 0, 0, 0

            if not icu_preds_df.empty:
                closest_icu_forecast = icu_preds_df.loc[icu_preds_df['ds'] >= current_forecast_time].head(1)
                if not closest_icu_forecast.empty:
                    icu_val = round(max(0, closest_icu_forecast['yhat'].iloc[0]))
            
            if not vent_preds_df.empty:
                closest_vent_forecast = vent_preds_df.loc[vent_preds_df['ds'] >= current_forecast_time].head(1)
                if not closest_vent_forecast.empty:
                    vent_val = round(max(0, closest_vent_forecast['yhat'].iloc[0]))
            
            if not oxygen_preds_df.empty:
                closest_oxygen_forecast = oxygen_preds_df.loc[oxygen_preds_df['ds'] >= current_forecast_time].head(1)
                if not closest_oxygen_forecast.empty:
                    oxygen_val = round(max(0, closest_oxygen_forecast['yhat'].iloc[0]))

            forecasts.append(ResourceForecastItem(
                timestamp=current_forecast_time.isoformat() + 'Z',
                icu_demand_forecast=int(icu_val),
                ventilator_demand_forecast=int(vent_val),
                oxygen_demand_forecast=int(oxygen_val)
            ))
    else:
        logger.error("Forecast models could not be loaded or trained. Returning empty forecast.")
        
    logger.info(f"Generated {len(forecasts)} forecast items.")
    return forecasts

# --- FastAPI API Endpoints ---
@app.on_event("startup")
async def startup_event():
    """Ensures model and data are ready when FastAPI starts."""
    current_working_dir = os.getcwd()
    logger.info(f"FastAPI startup: Current working directory is '{current_working_dir}'")

    # Ensure dummy data exists
    if not os.path.exists(DATA_PATH):
        logger.info(f"'{DATA_PATH}' not found. Generating dummy historical data...")
        try:
            generate_dummy_data_func(datetime.now() - timedelta(days=90), datetime.now(), DATA_PATH)
            logger.info(f"Dummy data generated and saved to '{DATA_PATH}'.")
        except Exception as e:
            logger.error(f"FastAPI startup failed: Error generating dummy data: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to generate initial data.")
    else:
        logger.info(f"'{DATA_PATH}' found. Skipping dummy data generation.")
    
    # Pre-train/load model for initial setup
    logger.info("FastAPI startup: Pre-training/loading model...")
    try:
        # Generate a small forecast to trigger model train/load/save
        _ = generate_forecast(horizon_hours=1, retrain_if_needed=True) 
        logger.info(f"FastAPI startup: Model training/loading complete. Model saved/verified at '{MODEL_PATH}'.")
    except Exception as e:
        logger.error(f"FastAPI startup failed: Error in model generation/loading: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load/train model on startup.")


@app.get("/")
async def root():
    return {
        "status": "Resource Prediction Agent Running",
        "model_loaded": os.path.exists(MODEL_PATH), # Check if model file exists
        "timestamp": datetime.now().isoformat()
    }

@app.get("/resource_forecast", response_model=ResourceForecastResponse)
async def get_resource_forecast_api(horizon_hours: int = 24):
    logger.info(f"API request for resource forecast for {horizon_hours} hours.")
    try:
        # Use the existing generate_forecast function
        forecast_data = generate_forecast(horizon_hours=horizon_hours, retrain_if_needed=True)
        return ResourceForecastResponse(forecast=forecast_data)
    except Exception as e:
        logger.error(f"Error generating forecast for API: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate resource forecast: {e}")

@app.get("/hospital_status", response_model=List[HospitalResource])
async def get_hospital_status_api():
    logger.info("API request for mock hospital status.")
    mock_hospitals = [
        HospitalResource(
            hospital_id="HOSP001",
            name="City General Hospital",
            location="Downtown",
            icu_beds_total=20,
            icu_beds_occupied=15,
            ventilators_total=10,
            ventilators_occupied=7,
            oxygen_cylinders_total=100,
            oxygen_cylinders_occupied=60,
            current_patients_count=150,
            max_capacity=200
        ),
        HospitalResource(
            hospital_id="HOSP002",
            name="Community Care Center",
            location="Suburbia",
            icu_beds_total=10,
            icu_beds_occupied=5,
            ventilators_total=5,
            ventilators_occupied=2,
            oxygen_cylinders_total=50,
            oxygen_cylinders_occupied=20,
            current_patients_count=80,
            max_capacity=100
        ),
        HospitalResource(
            hospital_id="HOSP003",
            name="Regional Trauma Center",
            location="North District",
            icu_beds_total=30,
            icu_beds_occupied=25,
            ventilators_total=15,
            ventilators_occupied=12,
            oxygen_cylinders_total=150,
            oxygen_cylinders_occupied=100,
            current_patients_count=250,
            max_capacity=300
        )
    ]
    return mock_hospitals

# --- CLI Execution (For Uvicorn to run the app) ---
if __name__ == "__main__":
    # This block is here for clarity, but you typically run FastAPI with 'uvicorn' directly.
    # The 'uvicorn' command will automatically call the 'startup_event'.
    logger.info("This script is usually run via 'uvicorn'. Starting Uvicorn manually for direct execution...")
    import uvicorn
    # If historical_demand.csv doesn't exist, this will be handled by startup_event
    uvicorn.run(app, host="0.0.0.0", port=5002)
