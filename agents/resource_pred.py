

import os
import sys
import logging
import pandas as pd
from flask import Flask, jsonify, request
from prophet import Prophet
from pyspark.sql import SparkSession
from pyspark.sql.functions import to_timestamp
from datetime import datetime, timedelta
import joblib

# UPDATED: Smarter way to get project_root for Colab/Script execution
# Determine project_root based on the execution context
if '__file__' in locals():
    # If run as a script (e.g., python agents/resource_pred.py)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
else:
    # If run directly in a Jupyter/Colab cell
    # Assumes the notebook's working directory is the project root /content/
    project_root = '/content' 

sys.path.append(project_root) # Add project root to sys.path to find 'api' module

# Import from the 'api' directory
from api.api_models import ResourceForecastItem, ResourceForecastResponse, HospitalResource
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__) # Flask app instance

# --- Model File Path ---
MODEL_PATH = os.path.join(project_root, "models", "resource_forecast.pkl")
DATA_PATH = os.path.join(project_root, "data", "historical_demand.csv")

# Initialize SparkSession in local mode
spark = SparkSession.builder \
    .appName("ResourcePredictionAgent") \
    .master("local[*]") \
    .config("spark.driver.memory", "4g") \
    .getOrCreate()
logger.info("Spark Session initialized.")

# --- Helper function to load historical data (using Spark) ---
def get_historical_demand_data() -> pd.DataFrame:
    """
    Loads historical demand data using Spark, then converts to Pandas DataFrame.
    """
    try:
        spark_df = spark.read.csv(DATA_PATH, header=True, inferSchema=True)
        spark_df = spark_df.withColumn("timestamp", to_timestamp(spark_df["timestamp"]))
        logger.info(f"Loaded {spark_df.count()} historical records using Spark from {DATA_PATH}")
        pd_df = spark_df.toPandas()
        return pd_df
    except FileNotFoundError:
        logger.error(f"Historical data file not found at {DATA_PATH}. Please ensure it exists and has been generated.")
        return pd.DataFrame(columns=['timestamp', 'icu_demand', 'ventilator_demand', 'oxygen_demand'])
    except Exception as e:
        logger.error(f"Error loading historical data with Spark from {DATA_PATH}: {e}", exc_info=True)
        return pd.DataFrame(columns=['timestamp', 'icu_demand', 'ventilator_demand', 'oxygen_demand'])

# --- Forecasting Logic to incorporate saving/loading for all three resources ---
def generate_forecast(horizon_hours: int = 24, retrain_if_needed: bool = True) -> List[ResourceForecastItem]:
    logger.info(f"Generating forecast for {horizon_hours} hours...")

    model_icu = None
    model_vent = None
    model_oxygen = None
    
    # Try to load the combined models
    # We also create a 'models' directory here if it doesn't exist, as it's needed for saving
    models_dir = os.path.join(project_root, "models")
    os.makedirs(models_dir, exist_ok=True) # Ensure models directory exists

    if os.path.exists(MODEL_PATH) and retrain_if_needed:
        try:
            combined_models = joblib.load(MODEL_PATH)
            model_icu = combined_models.get("icu_model")
            model_vent = combined_models.get("vent_model")
            model_oxygen = combined_models.get("oxygen_model")
            if model_icu and model_vent and model_oxygen: # Ensure all models were loaded
                logger.info(f"Loaded combined Prophet models from {MODEL_PATH}.")
            else:
                logger.warning(f"Combined models from {MODEL_PATH} incomplete or corrupt. Retraining will occur.")
                model_icu, model_vent, model_oxygen = None, None, None # Force retraining if incomplete
        except Exception as e:
            logger.warning(f"Could not load combined models from {MODEL_PATH}: {e}. Retraining will occur.")
            model_icu, model_vent, model_oxygen = None, None, None # Force retraining if loading fails

    # If models not loaded (or if retraining forced)
    if model_icu is None or model_vent is None or model_oxygen is None: # Check for all three
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
    if model_icu and model_vent and model_oxygen: # Ensure all three models are available
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

# --- Flask API Endpoints ---
@app.route("/resource_forecast", methods=["GET"])
def get_resource_forecast():
    horizon_hours = request.args.get('horizon_hours', default=24, type=int)
    logger.info(f"Received request for resource forecast for {horizon_hours} hours.")

    try:
        forecast_data = generate_forecast(horizon_hours=horizon_hours, retrain_if_needed=True)
        response = ResourceForecastResponse(forecast=forecast_data)
        return jsonify({"forecast": [item.dict() for item in forecast_data]}), 200
    except Exception as e:
        logger.error(f"Error generating forecast: {e}", exc_info=True)
        return jsonify({"error": str(e), "message": "Failed to generate resource forecast"}), 500

@app.route("/hospital_status", methods=["GET"])
def get_hospital_status():
    logger.info("Providing mock hospital status.")
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
        ).dict(),
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
        ).dict(),
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
        ).dict()
    ]
    return jsonify(mock_hospitals), 200

if __name__ == "__main__":
    # To pre-train the model and save the .pkl file when running this script directly:
    print("--- Running Resource Prediction Agent (Standalone Mode) ---")
    print("Pre-training/loading model for initial setup...")
    generate_forecast(horizon_hours=1, retrain_if_needed=True) # Run forecast once to trigger train/load
    print(f"Model training/loading complete. Model saved/verified at {MODEL_PATH}")

    # To run the web server for this agent AFTER the model is trained/saved:
    print("\nStarting Flask web server...")
    # Set FLASK_APP environment variable (important for Flask CLI)
    os.environ['FLASK_APP'] = 'agents.resource_pred:app' 
    # Run Flask application using os.system for Colab compatibility
    os.system('flask run --port 5002 --host 0.0.0.0') 
    # Note: In a Colab cell, os.system('flask run') will block execution.
    # For background Flask server with ngrok, use the threading approach from previous instructions.
