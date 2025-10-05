"""
Allocation & Routing Agent
- Matches patients to hospitals/resources
- Uses OR-Tools for optimization
"""

from ortools.linear_solver import pywraplp

def allocate_resources(patients: list, hospitals: list):
    """
    patients: [{id, severity, location}]
    hospitals: [{id, capacity, location}]
    Returns: allocation plan
    """
    # TODO: Build optimization model
    allocation = []
    for i, patient in enumerate(patients):
        allocation.append({"patient_id": patient["id"], "hospital_id": hospitals[i % len(hospitals)]["id"]})
    return allocation
