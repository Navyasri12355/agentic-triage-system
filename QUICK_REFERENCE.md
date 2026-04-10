# Quick Reference Guide

## Directory Structure
```
agentic-triage-system/
├── 📄 index.html                    # HTML entry point
├── 📦 package.json                  # JavaScript dependencies
├── 🐍 requirements.txt              # Python dependencies
│
├── ⚙️ Configuration Files
│   ├── vite.config.js               # Vite bundler config
│   ├── tailwind.config.js           # Tailwind CSS config
│   ├── postcss.config.js            # PostCSS config
│   ├── .env.example                 # Environment variables template
│   └── .gitignore                   # Git ignore rules
│
├── 📚 Documentation
│   ├── INTEGRATION_GUIDE.md          # Complete setup guide
│   ├── SETUP_COMPLETE.md            # What was fixed & done
│   ├── README.md                    # Project overview
│   └── LICENSE                      # MIT License
│
├── 🚀 Startup Scripts
│   ├── startup.sh                   # Linux/macOS startup
│   ├── startup.bat                  # Windows startup
│   └── agents/*.py                  # Backend agents
│
├── src/ (Frontend - React)
│   ├── index.css                    # Global styles (Tailwind imports)
│   ├── main.jsx                     # React entry point
│   ├── App.jsx                      # Main component (58KB - monolithic)
│   └── ...
│
├── agents/ (Backend - Python)
│   ├── triage.py                    # Severity prediction (FastAPI)
│   ├── resource_pred.py             # Demand forecasting (Flask)
│   ├── allocation.py                # Patient assignment (FastAPI)
│   ├── monitoring.py                # Vitals collection (FastAPI)
│   ├── audit.py                     # Compliance logging
│   ├── dashboard.py                 # Metrics calculation
│   └── coordinator.py               # Agent coordination
│
├── models/
│   └── xgb_model_risk1.pkl          # XGBoost model for triage
│
├── data/
│   ├── triage_output.csv            # Triage results log
│   ├── patient_status.csv           # Patient tracking
│   └── ...
│
├── db/
│   └── ...                          # Database files (SQLite/Mongita)
│
└── venv/                            # Python virtual environment
```

## Port Map
```
5173  ← Frontend (React + Vite)
5002  ← Resource Prediction Agent (Flask)
8000  ← Triage Agent (FastAPI)
8001  ← Allocation Agent (FastAPI)
8002  ← Monitoring Agent (FastAPI)
```

## Frontend Architecture

### App Structure
```
App.jsx (Main Component - 1050 lines)
├── getMockUserId()                    [Utility]
├── sortPatients()                     [Utility]
├── ResourceForecastPanel              [Component]
├── TriageStatusIndicator              [Component]
├── PatientCard                        [Component]
├── TriageDetailModal                  [Component]
├── PatientFormModal                   [Component]
├── TriageDashboard                    [Component]
├── FacilitySetup                      [Component]
└── AllocationDashboard                [Component] ← NEW/FIXED
```

### API Calls from Frontend
```
POST http://127.0.0.1:8000/predict
  ↓
  Receives: Patient vitals data
  Returns: Risk level, intervention recommendation
  
GET http://127.0.0.1:5002/resource_forecast?horizon_hours=24
  ↓
  Returns: ICU, ventilator, oxygen demand for next 24h
  
POST http://127.0.0.1:8001/allocate
  ↓
  Receives: Patient list + Hospital list
  Returns: Allocation assignments
```

## Backend Architecture

### Triage Agent (Port 8000)
- Framework: FastAPI
- Model: XGBoost (with rule-based fallback)
- Input: Patient vitals (age, HR, BP, SpO2, etc.)
- Output: Risk level (RED/YELLOW/GREEN), intervention

### Resource Prediction (Port 5002)
- Framework: Flask/FastAPI
- Model: Prophet (Time Series)
- Input: Historical demand data
- Output: 24-hour hourly forecasts

### Allocation Agent (Port 8001)
- Framework: FastAPI
- Algorithm: OR-Tools optimization
- Input: Patients (ID, severity, location), Hospitals (capacity, location)
- Output: Optimal patient-to-hospital assignments

### Monitoring Agent (Port 8002)
- Framework: FastAPI
- Function: Collect real-time vitals
- Optional: Not yet integrated in frontend

## Key Technologies
```
Frontend:
  ├── React 18.2         - UI framework
  ├── Vite 5.0           - Build tool (super fast)
  ├── Tailwind CSS 3.4   - Styling
  └── PostCSS            - CSS processing

Backend:
  ├── FastAPI            - Web framework (Triage, Allocation, Monitoring)
  ├── Flask              - Web framework (Resource Prediction)
  ├── XGBoost            - ML for severity prediction
  ├── Prophet            - Time series forecasting
  ├── OR-Tools           - Optimization (allocation)
  ├── Pandas/NumPy       - Data processing
  └── Pydantic           - Data validation

Database:
  ├── In-memory (current MVP)
  ├── Optional: MongoDB/Mongita
  └── Optional: SQLite
```

## Environment Setup

### One-Time Setup
```bash
# Frontend
npm install

# Backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Development Start
```bash
# Terminal 1: Frontend
npm run dev

# Terminal 2-5: Backend agents (or use startup script)
bash startup.sh            # All at once
```

## API Testing Commands

### Test Triage
```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '[{"age":45,"sex":1,"hr":120,"sbp":140,"dbp":90,"rr":22,"spo2":94,"temp":37.8,"dyspnea":1,"chest_pain":0,"confusion":0,"comorb":1,"pulse_pressure":50,"map":106.67,"shock_index":0.857,"abnormal_count":4}]'
```

### Test Resource Prediction
```bash
curl http://127.0.0.1:5002/resource_forecast?horizon_hours=24
```

### Test Allocation
```bash
curl -X POST http://127.0.0.1:8001/allocate \
  -H "Content-Type: application/json" \
  -d '{"patients":[{"id":"p1","severity":3,"location":[28.6,77.2]}],"hospitals":[{"id":"h1","capacity":20,"location":[28.5,77.3]}]}'
```

## Common Tasks

### Run Frontend Only
```bash
npm run dev
```

### Build Frontend for Production
```bash
npm run build        # Creates dist/ folder
npm run preview      # Preview production build locally
```

### Run Backend Only
```bash
bash startup.sh      # All agents
# OR manually:
uvicorn agents.triage:app --reload --port 8000
python agents/resource_pred.py
uvicorn agents.allocation:app --reload --port 8001
uvicorn agents.monitoring:app --reload --port 8002
```

### Check if Services are Running
```bash
curl http://localhost:5173/        # Frontend
curl http://127.0.0.1:8000/docs    # Triage (API docs)
curl http://127.0.0.1:5002/        # Resource
curl http://127.0.0.1:8001/        # Allocation
curl http://127.0.0.1:8002/docs    # Monitoring (API docs)
```

### View Logs (Linux/macOS)
```bash
tail -f logs/triage.log
tail -f logs/resource_pred.log
tail -f logs/allocation.log
```

## Performance Notes

### Frontend
- Vite: ~300ms dev server startup
- Hot Module Replacement (HMR) for instant updates
- Production build: <100KB gzipped (optimized)

### Backend
- FastAPI: ~50ms response time (simple requests)
- Prophet: ~2-5 seconds for 24h forecast
- OR-Tools: ~100-500ms for allocation (depending on data size)

## Security Considerations

⚠️ **Current State (Development):**
- CORS open to all origins (`["*"]`)
- No authentication
- In-memory storage (no persistence)

✅ **For Production:**
- Restrict CORS to frontend domain
- Add JWT/OAuth authentication
- Use persistent database
- Add request validation
- Enable HTTPS
- Rate limiting
- Input sanitization

## Files Modified ✅
- `index.html` - Removed CDN dependency
- `src/main.jsx` - Added CSS import
- `src/App.jsx` - Fixed React structure, added allocation dashboard
- `package.json` - Added dev/build scripts
- `agents/allocation.py` - Added CORS middleware

## Files Created ✅
- `vite.config.js`
- `tailwind.config.js`
- `postcss.config.js`
- `src/index.css`
- `.env.example`
- `INTEGRATION_GUIDE.md`
- `SETUP_COMPLETE.md`
- `startup.sh`
- `startup.bat`

## Next Phase Ideas
- [ ] Unified API Gateway (single port backend)
- [ ] Database persistence
- [ ] WebSocket real-time updates
- [ ] User authentication
- [ ] Admin dashboard
- [ ] Audit logging
- [ ] Mobile app
- [ ] Advanced analytics
