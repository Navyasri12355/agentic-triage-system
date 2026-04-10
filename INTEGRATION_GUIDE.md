# Integration Guide - Emergency Triage System

This document explains how to set up and run all components of the Emergency Triage System.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    React + Vite Frontend (5173)                │
│         - Triage Dashboard                                      │
│         - Patient Intake & Assessment                          │
│         - Resource Forecasting                                 │
│         - Patient Allocation Results                          │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTP/CORS Requests
    ┌────────────────┼────────────────┬─────────────────┐
    │                │                │                 │
    ▼                ▼                ▼                 ▼
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
│   Triage   │  │ Resource   │  │ Allocation │  │ Monitoring │
│   Agent    │  │ Prediction │  │   Agent    │  │   Agent    │
│ (8000)    │  │   (5002)   │  │   (8001)   │  │  (8002)    │
│  FastAPI   │  │   Flask    │  │  FastAPI   │  │  FastAPI   │
└────────────┘  └────────────┘  └────────────┘  └────────────┘
    │                │                │                 │
    └────────────────┴────────────────┴─────────────────┘
                     └─ Shared Backend Infrastructure
                        - XGBoost Models
                        - Prophet Time Series
                        - OR-Tools Optimization
```

## Prerequisites

- **Node.js** ≥ 18.0.0
- **npm** or **yarn**
- **Python** ≥ 3.9
- **pip** (latest version)

## Quick Start

### 1. Frontend Setup

```bash
# Navigate to project root
cd /path/to/agentic-triage-system

# Install frontend dependencies
npm install

# Start Vite dev server (runs on http://localhost:5173)
npm run dev
# or
npm start
```

The frontend will automatically open in your browser.

### 2. Backend Setup (Python)

Open a **new terminal** and run:

```bash
# Create and activate virtual environment (one-time)
python -m venv venv

# Activate virtual environment
source venv/bin/activate          # Linux/macOS
# or
venv\Scripts\activate             # Windows

# Install Python dependencies (one-time)
pip install -r requirements.txt
```

### 3. Run Backend Agents

Run each agent in a **separate terminal** (make sure to activate venv in each):

#### A. Triage Agent (FastAPI) - Port 8000
```bash
source venv/bin/activate
uvicorn agents.triage:app --reload --port 8000
```
✅ This endpoint receives patient vitals and returns severity predictions

#### B. Resource Prediction Agent (Flask) - Port 5002
```bash
source venv/bin/activate
python agents/resource_pred.py
```
✅ This endpoint provides 24-hour resource demand forecasts

#### C. Allocation Agent (FastAPI) - Port 8001
```bash
source venv/bin/activate
uvicorn agents.allocation:app --reload --port 8001
```
✅ This endpoint allocates patients to hospitals using optimization

#### D. Monitoring Agent (FastAPI) - Port 8002 (Optional)
```bash
source venv/bin/activate
uvicorn agents.monitoring:app --reload --port 8002
```
✅ This endpoint collects real-time vitals and facility data

## API Endpoints

### 1. Triage Agent (Port 8000)
**Endpoint:** `POST /predict`
- Receives patient vitals and comorbidities
- Returns severity classification (RED/YELLOW/GREEN) and intervention recommendations

**Example Request:**
```json
[{
  "age": 45,
  "sex": 1,
  "hr": 120,
  "sbp": 140,
  "dbp": 90,
  "rr": 22,
  "spo2": 94,
  "temp": 37.8,
  "dyspnea": 1,
  "chest_pain": 0,
  "confusion": 0,
  "comorb": 1,
  "pulse_pressure": 50,
  "map": 106.67,
  "shock_index": 0.857,
  "abnormal_count": 4
}]
```

### 2. Resource Prediction Agent (Port 5002)
**Endpoint:** `GET /resource_forecast?horizon_hours=24`
- Returns hourly forecasts for ICU beds, ventilators, and oxygen for next 24 hours

**Response Format:**
```json
{
  "forecast": [
    {
      "timestamp": "2026-04-10T00:00:00",
      "icu_demand_forecast": 12,
      "ventilator_demand_forecast": 6,
      "oxygen_demand_forecast": 55
    },
    ...
  ]
}
```

### 3. Allocation Agent (Port 8001)
**Endpoint:** `POST /allocate`
- Allocates patients to hospitals based on distance and capacity

**Request Format:**
```json
{
  "patients": [
    {
      "id": "patient-uuid",
      "severity": 3,
      "location": [28.6139, 77.2090]
    }
  ],
  "hospitals": [
    {
      "id": "hospital-uuid",
      "capacity": 20,
      "location": [28.5355, 77.3910]
    }
  ]
}
```

## Testing the System

### Using the Frontend
1. Open http://localhost:5173 in your browser
2. Complete facility setup
3. Click "New Patient Intake" to add patients
4. Fill in patient vitals and click "Run Risk Prediction"
5. Click "Allocate Patients" to assign patients to hospitals

### Using curl (for testing APIs)

**Test Triage Endpoint:**
```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '[{"age":45,"sex":1,"hr":120,"sbp":140,"dbp":90,"rr":22,"spo2":94,"temp":37.8,"dyspnea":1,"chest_pain":0,"confusion":0,"comorb":1,"pulse_pressure":50,"map":106.67,"shock_index":0.857,"abnormal_count":4}]'
```

**Test Resource Forecast:**
```bash
curl http://127.0.0.1:5002/resource_forecast?horizon_hours=24
```

**Test Allocation:**
```bash
curl -X POST http://127.0.0.1:8001/allocate \
  -H "Content-Type: application/json" \
  -d '{"patients":[{"id":"p1","severity":3,"location":[28.6,77.2]}],"hospitals":[{"id":"h1","capacity":20,"location":[28.5,77.3]}]}'
```

## Frontend Build

### Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
```
This creates optimized files in the `dist/` directory.

### Preview Production Build
```bash
npm run preview
```

## Troubleshooting

### "Cannot find module" errors
```bash
npm install
pip install -r requirements.txt
```

### CORS errors (403/401)
- Ensure all backend agents are running
- Check that the port numbers in frontend API calls match backend ports
- All agents have CORS middleware enabled (allow_origins=["*"])

### API not responding (Connection refused)
- Verify backend agent is running on the correct port
- Check firewall settings
- Look for error messages in the agent terminal

### Model not loading
- Check that `models/xgb_model_risk1.pkl` exists
- If missing, the triage agent will run in rule-based mode

### Prophet library errors
- Run: `pip install --upgrade prophet`
- On some systems, you may need: `conda install -c conda-forge prophet`

## Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```env
VITE_API_TRIAGE=http://127.0.0.1:8000
VITE_API_RESOURCE=http://127.0.0.1:5002
VITE_API_ALLOCATION=http://127.0.0.1:8001
```

However, currently the frontend has hardcoded URLs for simplicity during development.

## Integration Notes

### What's Integrated ✅
- **Triage Agent** → Frontend (patient prediction)
- **Resource Prediction** → Frontend (capacity forecasting)
- **Allocation Agent** → Frontend (patient-to-hospital assignment)

### What's Optional ⚠️
- **Monitoring Agent** → Can be used for real-time vitals collection
- **Audit Agent** → Can log all triage decisions for compliance

### Future Improvements
- 🔧 Unified API Gateway (centralize all agents under one port)
- 📊 Real-time WebSocket updates for live dashboard
- 🔐 Authentication and authorization
- 💾 Persistent database (currently in-memory)
- 📱 Mobile app integration

## Support

For detailed documentation on individual agents, see:
- `agents/triage.py` - Severity assessment logic
- `agents/resource_pred.py` - Demand forecasting
- `agents/allocation.py` - Resource allocation algorithm
- `agents/monitoring.py` - Vitals collection
