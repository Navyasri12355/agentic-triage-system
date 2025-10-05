"""
Allocation & Routing Agent (Integrated Version)
-------------------------------------------------
- Assigns patients to hospitals using OR-Tools
- Integrates with other agents:
    - Triage Agent: uses severity scores
    - Resource Prediction Agent: reads available capacity
    - Coordinator Agent: central orchestrator calls this
- Includes fallback (round-robin) assignment
"""

from ortools.linear_solver import pywraplp
import math
import random


# ---------------------------------
# Helper Functions
# ---------------------------------

def calculate_distance(loc1, loc2):
    """Compute Euclidean distance between two coordinates."""
    return math.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)


def allocate_resources(patients, hospitals):
    """
    Allocates patients to hospitals optimally using OR-Tools.
    Falls back to round-robin allocation if solver fails.

    Args:
        patients: list of dicts like:
            [{"id": "P1", "severity": 3, "location": (x, y)}]
        hospitals: list of dicts like:
            [{"id": "H1", "capacity": 5, "location": (x, y)}]

    Returns:
        allocation: list of {"patient_id": ..., "hospital_id": ..., "distance": ..., "severity": ...}
    """
    if not patients or not hospitals:
        return []

    solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver:
        print("[WARN] OR-Tools solver not available. Using fallback allocation.")
        return fallback_allocation(patients, hospitals)

    num_patients = len(patients)
    num_hospitals = len(hospitals)

    # Decision variables: x[i][j] = 1 if patient i assigned to hospital j
    x = [[solver.BoolVar(f'x[{i},{j}]') for j in range(num_hospitals)] for i in range(num_patients)]

    # Objective: minimize total weighted distance (severity × distance)
    objective = solver.Objective()
    for i in range(num_patients):
        for j in range(num_hospitals):
            dist = calculate_distance(patients[i]["location"], hospitals[j]["location"])
            weight = patients[i].get("severity", 1)
            objective.SetCoefficient(x[i][j], dist * weight)
    objective.SetMinimization()

    # Constraint 1: Each patient assigned to exactly one hospital
    for i in range(num_patients):
        solver.Add(sum(x[i][j] for j in range(num_hospitals)) == 1)

    # Constraint 2: Hospital capacity
    for j in range(num_hospitals):
        solver.Add(sum(x[i][j] for i in range(num_patients)) <= hospitals[j]["capacity"])

    # Solve
    status = solver.Solve()
    allocation = []

    if status == pywraplp.Solver.OPTIMAL:
        for i in range(num_patients):
            for j in range(num_hospitals):
                if x[i][j].solution_value() > 0.5:
                    allocation.append({
                        "patient_id": patients[i]["id"],
                        "hospital_id": hospitals[j]["id"],
                        "distance": round(calculate_distance(patients[i]["location"], hospitals[j]["location"]), 2),
                        "severity": patients[i]["severity"]
                    })
    else:
        print("[WARN] No optimal solution found. Using fallback allocation.")
        allocation = fallback_allocation(patients, hospitals)

    return allocation


def fallback_allocation(patients, hospitals):
    """
    Basic round-robin assignment if optimization fails.
    """
    allocation = []
    hospital_index = 0

    for patient in patients:
        hospital = hospitals[hospital_index % len(hospitals)]
        allocation.append({
            "patient_id": patient["id"],
            "hospital_id": hospital["id"],
            "distance": round(calculate_distance(patient["location"], hospital["location"]), 2),
            "severity": patient.get("severity", 1)
        })
        hospital_index += 1

    return allocation


# ---------------------------------
# Integration Entry Point
# ---------------------------------

def allocation_agent_main(patient_data_list, hospital_data_list):
    """
    Entry point for Coordinator Agent.
    Handles pre-processing and returns allocation plan.
    """
    print("[INFO] Running Allocation Agent...")
    allocation_plan = allocate_resources(patient_data_list, hospital_data_list)
    print("[INFO] Allocation completed.")
    return allocation_plan


# ---------------------------------
# Dummy Demo (Run Directly)
# ---------------------------------
if __name__ == "__main__":
    # Dummy patient data
    patients = [
        {"id": f"P{i+1}", "severity": random.randint(1, 5), "location": (random.uniform(0, 10), random.uniform(0, 10))}
        for i in range(8)
    ]

    # Dummy hospital data
    hospitals = [
        {"id": "H1", "capacity": 3, "location": (2, 3)},
        {"id": "H2", "capacity": 4, "location": (8, 5)},
        {"id": "H3", "capacity": 2, "location": (5, 9)}
    ]

    print("\n=== Patients ===")
    for p in patients:
        print(p)
    print("\n=== Hospitals ===")
    for h in hospitals:
        print(h)

    result = allocation_agent_main(patients, hospitals)
    print("\n=== Allocation Plan ===")
    for r in result:
        print(f"Patient {r['patient_id']} → Hospital {r['hospital_id']} (Distance={r['distance']}, Severity={r['severity']})")
