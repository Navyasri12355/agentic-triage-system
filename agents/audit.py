import os
import pandas as pd
import numpy as np
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# -----------------------------
# 1️⃣ Setup FastAPI
# -----------------------------
app = FastAPI(title="Agentic AI Audit Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# 2️⃣ Data Models
# -----------------------------
class ModelAuditRequest(BaseModel):
    y_true: List[int]
    y_pred: List[int]
    sensitive_attribute: List[int]  # e.g., gender (0=female, 1=male)


class AllocationAuditRequest(BaseModel):
    allocations: List[dict]  # each entry: {"hospital_id": int, "age": int, "gender": int, "allocated": int}


# -----------------------------
# 3️⃣ Helper Functions
# -----------------------------

def compute_basic_metrics(y_true, y_pred):
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1_score": f1_score(y_true, y_pred, zero_division=0)
    }

def compute_fairness_metrics(y_true, y_pred, sensitive_attr):
    """
    Example fairness metrics:
    - Demographic Parity: P(ŷ=1 | group=0) vs P(ŷ=1 | group=1)
    - Equal Opportunity: P(ŷ=1 | y=1, group=0) vs P(ŷ=1 | y=1, group=1)
    """
    groups = np.unique(sensitive_attr)
    if len(groups) != 2:
        return {"warning": "Sensitive attribute must be binary (0/1)"}

    group0_idx = [i for i, g in enumerate(sensitive_attr) if g == 0]
    group1_idx = [i for i, g in enumerate(sensitive_attr) if g == 1]

    dp_group0 = np.mean(np.array(y_pred)[group0_idx])
    dp_group1 = np.mean(np.array(y_pred)[group1_idx])

    eo_group0 = np.mean(np.array(y_pred)[np.intersect1d(group0_idx, np.where(np.array(y_true)==1))])
    eo_group1 = np.mean(np.array(y_pred)[np.intersect1d(group1_idx, np.where(np.array(y_true)==1))])

    return {
        "demographic_parity_diff": abs(dp_group0 - dp_group1),
        "equal_opportunity_diff": abs(eo_group0 - eo_group1)
    }

def compute_allocation_fairness(data):
    df = pd.DataFrame(data)
    fairness_summary = df.groupby("gender")["allocated"].mean().to_dict()
    return {
        "allocation_rate_by_gender": fairness_summary,
        "max_difference": abs(fairness_summary.get(0, 0) - fairness_summary.get(1, 0))
    }

# -----------------------------
# 4️⃣ Endpoints
# -----------------------------

@app.get("/")
def health_check():
    return {"status": "✅ Audit Agent running", "version": "1.0"}

@app.post("/audit_model")
def audit_model(request: ModelAuditRequest):
    """Audits ML predictions for performance & fairness."""
    metrics = compute_basic_metrics(request.y_true, request.y_pred)
    fairness = compute_fairness_metrics(request.y_true, request.y_pred, request.sensitive_attribute)

    return {
        "model_metrics": metrics,
        "fairness_metrics": fairness,
        "recommendation": "⚠️ Retrain with fairness constraints" if fairness["demographic_parity_diff"] > 0.1 else "✅ Model is fair"
    }

@app.post("/audit_allocation")
def audit_allocation(request: AllocationAuditRequest):
    """Audits resource allocations for fairness."""
    fairness = compute_allocation_fairness(request.allocations)
    return {
        "allocation_fairness": fairness,
        "recommendation": "⚠️ Adjust resource rules" if fairness["max_difference"] > 0.1 else "✅ Allocation is balanced"
    }

# -----------------------------
# 5️⃣ Optional CSV Upload Endpoint
# -----------------------------
@app.post("/audit_csv")
async def audit_csv(file: UploadFile = File(...)):
    """Uploads a CSV file and computes metrics automatically."""
    try:
        df = pd.read_csv(file.file)
        if not all(col in df.columns for col in ["y_true", "y_pred", "sensitive_attribute"]):
            raise HTTPException(status_code=400, detail="Missing required columns.")
        metrics = compute_basic_metrics(df["y_true"], df["y_pred"])
        fairness = compute_fairness_metrics(df["y_true"], df["y_pred"], df["sensitive_attribute"])
        return {
            "csv_audit": metrics,
            "fairness": fairness
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

