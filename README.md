# Medusabytes – Agentic Emergency Triage System

An autonomous, agentic AI-based triage platform designed for resource-limited emergency settings in India. It dynamically assesses patient severity, predicts resource demand (beds, oxygen, ventilators), and allocates care efficiently — all while keeping clinicians in control.

**Live Demo:** [Google Drive - Video & Presentation](https://drive.google.com/drive/folders/1ah3BWG-TkTODqcH-lZrUo7v0DIlQy5HJ)

---

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
│ (8000)     │  │   (5002)   │  │   (8001)   │  │  (8002)    │
│  FastAPI   │  │   FastAPI  │  │  FastAPI   │  │  FastAPI   │
└────────────┘  └────────────┘  └────────────┘  └────────────┘
    │                │                │                 │
    └────────────────┴────────────────┴─────────────────┘
                     └─ Backend Infrastructure
                        - XGBoost Models
                        - Prophet Time Series
                        - OR-Tools Optimization
```

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** ≥ 18.0.0
- **npm** or **yarn**
- **Python** ≥ 3.9
- **pip** (latest)

### Setup (One-Time)

```bash
# 1. Frontend dependencies
npm install

# 2. Backend environment
python -m venv venv
source venv/bin/activate           # Linux/macOS
# or
venv\Scripts\activate              # Windows

# 3. Backend dependencies
pip install -r requirements.txt
```

### Running the System

**Terminal 1 - Frontend:**
```bash
npm run dev
# Opens http://localhost:5173
```

**Terminal 2-5 - Backend agents** (activate venv in each):

```bash
# Agent 1: Triage (FastAPI) - Port 8000
uvicorn agents.triage:app --reload --port 8000

# Agent 2: Resource Prediction (FastAPI) - Port 5002
python agents/resource_pred.py

# Agent 3: Allocation (FastAPI) - Port 8001
uvicorn agents.allocation:app --reload --port 8001

# Agent 4: Monitoring (FastAPI) - Port 8002 [Optional]
uvicorn agents.monitoring:app --reload --port 8002
```

Or run all at once:
```bash
bash startup.sh        # Linux/macOS
startup.bat            # Windows
```

---

## 🏥 Agents Overview

### 1. **Triage Agent** (Port 8000)
**Purpose:** Real-time patient severity assessment

- **Framework:** FastAPI
- **ML Model:** XGBoost (+ rule-based fallback)
- **Input:** Patient vitals (age, HR, BP, SpO2, temperature, consciousness level, pain, etc.)
- **Output:** RED/YELLOW/GREEN severity + intervention recommendations
- **Endpoint:** `POST /predict`

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

### 2. **Resource Prediction Agent** (Port 5002)
**Purpose:** 24-hour demand forecasting for critical resources

- **Framework:** FastAPI
- **Time Series Model:** Prophet
- **Forecasts:** ICU beds, ventilators, oxygen cylinders
- **Input:** Historical demand data
- **Output:** Hourly predictions for next 24 hours
- **Endpoint:** `GET /resource_forecast?horizon_hours=24`

**Example Response:**
```json
{
  "forecast": [
    {
      "timestamp": "2026-04-11T00:00:00Z",
      "icu_demand_forecast": 12,
      "ventilator_demand_forecast": 6,
      "oxygen_demand_forecast": 55
    }
  ]
}
```

### 3. **Allocation Agent** (Port 8001)
**Purpose:** Optimized patient-to-hospital assignment

- **Framework:** FastAPI
- **Algorithm:** OR-Tools constraint optimization
- **Considers:** Patient severity, distance, hospital capacity
- **Input:** Patient list (ID, severity, location) + Hospital list (capacity, location)
- **Output:** Optimal allocations
- **Endpoint:** `POST /allocate`

### 4. **Monitoring Agent** (Port 8002) [Optional]
**Purpose:** Real-time vitals collection and facility status tracking

- **Framework:** FastAPI
- **Function:** Aggregates facility data and vitals streams
- **Status:** Available, not yet integrated in frontend

---

## 📊 Technology Stack

### Frontend
- **React 18.2** - UI framework
- **Vite 5.0** - Ultra-fast build tool
- **Tailwind CSS 3.4** - Modern styling
- **PostCSS** - CSS processing

### Backend
- **FastAPI** - Async async web framework (all agents)
- **XGBoost** - ML for severity prediction
- **Prophet** - Time series forecasting
- **OR-Tools** - Optimization algorithms
- **Pandas/NumPy** - Data processing
- **Pydantic** - Data validation

### Database
- **In-memory** (current MVP)
- Optional: MongoDB/Mongita for persistence

---

## 🧪 Testing APIs

### Using curl

**Test Triage:**
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

### Using Frontend
1. Open http://localhost:5173
2. Complete facility setup
3. Click "New Patient Intake"
4. Enter patient vitals → "Run Risk Prediction"
5. Click "Allocate Patients" for assignments

---

## 📁 Project Structure

```
agentic-triage-system/
├── index.html                      # HTML entry point
├── package.json                    # JavaScript dependencies
├── requirements.txt                # Python dependencies
├── vite.config.js                  # Vite configuration
├── tailwind.config.js              # Tailwind CSS config
├── postscss.config.js              # PostCSS config
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore rules
│
├── src/                            # Frontend (React)
│   ├── main.jsx                    # React entry point
│   ├── App.jsx                     # Main component
│   └── index.css                   # Global styles
│
├── agents/                         # Backend (Python)
│   ├── triage.py                   # Severity prediction
│   ├── resource_pred.py            # Demand forecasting
│   ├── allocation.py               # Patient allocation
│   ├── monitoring.py               # Vitals collection
│   ├── audit.py                    # Compliance logging
│   └── dashboard.py                # Metrics calculation
│
├── models/
│   └── xgb_model_risk1.pkl         # XGBoost model
│
├── data/                           # Output data
│   ├── triage_output.csv
│   └── patient_status.csv
│
├── db/                             # Database files
│
├── venv/                           # Python virtual environment
│
└── [startup.sh, startup.bat]       # Startup scripts
```

---

## 🔧 Development

### Frontend Development
```bash
npm run dev          # Start dev server with HMR
npm run build        # Production build (creates dist/)
npm run preview      # Preview production build
```

### Backend Development
```bash
# View API documentation (FastAPI)
http://127.0.0.1:8000/docs
http://127.0.0.1:8001/docs
http://127.0.0.1:8002/docs
```

---

## ⚠️ Known Limitations & Future Work

### Current State
- CORS open to all origins (dev only)
- No authentication/authorization
- In-memory storage (no persistence)
- Models are not auto-trained; requires pre-trained files

### Planned Features
- 🔒 JWT/OAuth authentication
- 💾 Persistent database (MongoDB/SQL)
- 🔌 Unified API Gateway (single port)
- 📡 WebSocket real-time updates
- 📊 Advanced analytics dashboard
- 📱 Mobile app integration

---

## 🐛 Troubleshooting

### "Cannot find module" errors
```bash
npm install
pip install -r requirements.txt
```

### CORS errors (403/401)
- Ensure all backend agents are running
- Check port numbers match in frontend API calls
- Verify CORS middleware is enabled (should be by default)

### API not responding
- Check if backend agent is running on correct port
- Verify firewall settings
- Look for error messages in agent terminal

### Prophet/pandas errors
```bash
pip install --upgrade prophet pandas
```

---

## 📄 License

MIT License - See LICENSE file for details

---

## 👥 Contributing

This project was developed as part of an academic initiative to improve emergency response systems in resource-limited settings.

For issues or contributions, please refer to the repository.
