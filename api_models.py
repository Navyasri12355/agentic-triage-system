

%%writefile api_models.py
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

# --- Shared Data Models ---
class Vitals(BaseModel):
    heart_rate: int
    blood_pressure_systolic: int
    blood_pressure_diastolic: int
    respiratory_rate: int
    temperature: float
    oxygen_saturation: float
    consciousness_level: str # e.g., "Alert", "Verbal", "Pain", "Unresponsive"
    pain_level: Optional[int] # 1-10

class PatientInflow(BaseModel):
    patient_id: str
    timestamp: datetime = datetime.now()
    gender: str
    age: int
    presenting_complaint: str
    vitals: Vitals

class HospitalResource(BaseModel):
    hospital_id: str
    name: str
    location: str
    icu_beds_total: int
    icu_beds_occupied: int
    ventilators_total: int
    ventilators_occupied: int
    oxygen_cylinders_total: Optional[int] = 0 # New: Oxygen Cylinders
    oxygen_cylinders_occupied: Optional[int] = 0 # New: Oxygen Cylinders
    current_patients_count: int
    max_capacity: int

# --- API Request/Response Models ---

# /triage_score (Triage Agent API) - simplified
class TriageRequest(BaseModel):
    patient_id: str
    vitals: Vitals
    presenting_complaint: str
    age: int

class TriageScoreResponse(BaseModel):
    patient_id: str
    severity_score: float # e.g., 0-100, or ESI 1-5
    severity_band: str # e.g., "Critical", "Urgent", "Stable"
    recommendation: str # e.g., "Immediate ICU", "ER", "General Ward"

# /resource_forecast (Resource Prediction Agent API)
class ResourceForecastItem(BaseModel):
    timestamp: datetime
    icu_demand_forecast: int
    ventilator_demand_forecast: int
    oxygen_demand_forecast: int # New: Oxygen demand forecast

class ResourceForecastResponse(BaseModel):
    forecast: List[ResourceForecastItem]

# /allocation (Allocation Agent API) - simplified
class AllocationRequest(BaseModel):
    patient_id: str
    severity_score: float
    resource_needs: Dict[str, int] # e.g., {"icu_beds": 1, "ventilators": 1, "oxygen_cylinders": 1}
    available_hospitals: List[HospitalResource] # List of current hospital states

class AllocationResponse(BaseModel):
    patient_id: str
    assigned_hospital_id: str
    assigned_hospital_name: str
    estimated_arrival_time: Optional[datetime]
    rejection_reason: Optional[str] = None # If no suitable hospital found

# /assign_patient (Coordinator Agent API - Final Decision) - simplified
class AssignPatientResponse(BaseModel):
    patient_id: str
    severity_score: float
    severity_band: str
    assigned_hospital_id: str
    assigned_hospital_name: str
    forecasted_resources: List[ResourceForecastItem]
    decision_log_id: str # Link to audit trail

# For Audit Log (Kafka message or direct DB insert) - simplified
class DecisionLogEntry(BaseModel):
    patient_id: str
    timestamp: datetime = datetime.now()
    severity_score: float
    assigned_hospital_id: Optional[str]
    forecast_snapshot: List[ResourceForecastItem]
    allocation_details: Dict
    decision_by: str = "Coordinator Agent" # or "Clinician Override"
    override_flag: bool = False
    review_status: str = "Approved" # "Approved", "Needs Review"
    reason_for_review: Optional[str] = None
