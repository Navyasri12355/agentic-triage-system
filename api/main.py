from fastapi import FastAPI
from agents.triage import compute_triage
from agents.resource_pred import predict_resources

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Agentic Triage System Backend Running"}

@app.post("/triage/")
def triage(patient_data: dict):
    severity = compute_triage(patient_data)
    return {"severity": severity}

@app.get("/forecast/")
def forecast():
    demand = predict_resources()
    return {"forecast": demand}
