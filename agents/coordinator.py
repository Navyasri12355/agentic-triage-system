"""
Coordinator Agent
- Orchestrates actions between other agents
- Issues commands: dispatch ambulance, reserve bed, notify staff
"""

from agents.triage import compute_triage
from agents.resource_pred import predict_resources
from agents.allocation import allocate_resources

def coordinate(patient_data: dict, hospitals: list):
    severity = compute_triage(patient_data)
    forecast = predict_resources()
    allocation = allocate_resources([patient_data], hospitals)
    
    return {
        "severity": severity,
        "forecast": forecast,
        "allocation": allocation
    }
