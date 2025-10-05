from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Tuple
from ortools.linear_solver import pywraplp
import math, random

app = FastAPI(title="Allocation & Routing Agent API")

# ---------------------------
# Pydantic Models
# ---------------------------
class Patient(BaseModel):
    id: str
    severity: int
    location: Tuple[float, float]

class Hospital(BaseModel):
    id: str
    capacity: int
    location: Tuple[float, float]

class AllocationResult(BaseModel):
    patient_id: str
    hospital_id: str
    distance: float
    severity: int

# ---------------------------
# Core Logic
# ---------------------------
def calculate_distance(loc1, loc2):
    return math.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)

def fallback_allocation(patients, hospitals):
    allocation, hospital_index = [], 0
    for p in patients:
        h = hospitals[hospital_index % len(hospitals)]
        allocation.append({
            "patient_id": p["id"],
            "hospital_id": h["id"],
            "distance": round(calculate_distance(p["location"], h["location"]), 2),
            "severity": p.get("severity", 1)
        })
        hospital_index += 1
    return allocation

def allocate_resources(patients, hospitals):
    if not patients or not hospitals:
        return []
    solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver:
        return fallback_allocation(patients, hospitals)

    n_p, n_h = len(patients), len(hospitals)
    x = [[solver.BoolVar(f'x[{i},{j}]') for j in range(n_h)] for i in range(n_p)]
    obj = solver.Objective()

    for i in range(n_p):
        for j in range(n_h):
            dist = calculate_distance(patients[i]["location"], hospitals[j]["location"])
            w = patients[i].get("severity", 1)
            obj.SetCoefficient(x[i][j], dist * w)
    obj.SetMinimization()

    for i in range(n_p):
        solver.Add(sum(x[i][j] for j in range(n_h)) == 1)
    for j in range(n_h):
        solver.Add(sum(x[i][j] for i in range(n_p)) <= hospitals[j]["capacity"])

    status = solver.Solve()
    if status != pywraplp.Solver.OPTIMAL:
        return fallback_allocation(patients, hospitals)

    allocation = []
    for i in range(n_p):
        for j in range(n_h):
            if x[i][j].solution_value() > 0.5:
                allocation.append({
                    "patient_id": patients[i]["id"],
                    "hospital_id": hospitals[j]["id"],
                    "distance": round(calculate_distance(patients[i]["location"], hospitals[j]["location"]), 2),
                    "severity": patients[i]["severity"]
                })
    return allocation

def allocation_agent_main(patient_data_list, hospital_data_list):
    print("[INFO] Running Allocation Agent...")
    result = allocate_resources(patient_data_list, hospital_data_list)
    print("[INFO] Allocation complete.")
    return result

# ---------------------------
# FastAPI Endpoints
# ---------------------------
@app.get("/")
def home():
    return {"message": "Allocation Agent API is running!"}

@app.post("/allocate", response_model=List[AllocationResult])
def allocate(patients: List[Patient], hospitals: List[Hospital]):
    patient_dicts = [p.dict() for p in patients]
    hospital_dicts = [h.dict() for h in hospitals]
    return allocation_agent_main(patient_dicts, hospital_dicts)

# ---------------------------
# Run server
# ---------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("allocation_agent_api:app", host="0.0.0.0", port=8000, reload=True)
