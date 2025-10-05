# Medusabytes – Agentic Emergency Triage System

An autonomous, agentic AI-based triage platform designed for resource-limited emergency settings in India.  
It dynamically assesses patient severity, predicts resource demand (beds, oxygen, ventilators), and allocates care efficiently — all while keeping clinicians in control.

### Drive link to video and ppt - https://drive.google.com/drive/folders/1ah3BWG-TkTODqcH-lZrUo7v0DIlQy5HJ
---
## System Overview

- **Frontend:** React + Vite for dashboards and triage visualization  
- **Backend:** Python (Flask/FastAPI) for AI APIs (triage scoring, resource prediction, allocation)
- **Database:** In memory allocation for MVP 
- **Communication:** REST APIs (JSON), WebSocket (for live triage updates)
- **AI Layer:** XGBoost for severity prediction

---

## ⚙️ Prerequisites

Before setup, ensure you have:

- **Node.js** ≥ 18.0.0  
- **npm** or **yarn**
- **Python** ≥ 3.9  
- **pip** (latest version)

---

## Frontend Setup (React)

Navigate to src folder
```bash
# Clone repo
git clone https://github.com/Navyasri12355/agentic-triage-system.git
cd src

# Install dependencies
npm install

#Start server
npm start
#This runs on port 5173
```
## Backend Setup (React)
Return to the main directory
```bash
# Create and activate a virtual environment:\
python -m venv venv
source venv/bin/activate   # (Linux/macOS)
venv\Scripts\activate      # (Windows)

#Install Python dependencies
pip install -r requirements.txt

#Run the Triage Agent (FastAPI):
#This agent runs the patient triage and prediction logic (integrated with frontend)

uvicorn main:app --reload --port 5002

#Run the Resource Prediction Agent (Flask):
#This agent handles the resource forecasting based on the logic in resource_pred.py (integrated with frontend)
python agents/resource_pred.py

#Run the Allocation Agent
#did not integrate with frontend due to time constraints
python agents/allocation.py

#Run the monitoring agent
#did not integrate with frontend due to time constraints
python agents/monitoring.py
```
# Key Features
1. Monitoring Agent: Collects real-time vitals, symptoms, and facility data.
2. Triage Agent: Computes severity scores using hybrid rules + ML (XGBoost).
3. Resource Prediction Agent: Forecasts ICU/oxygen demand.
4. Allocation & Routing Agent: Matches patients to hospitals via optimization
algorithms.