# dashboard.py
import streamlit as st
import requests
import pandas as pd
import json

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Agentic AI Audit Dashboard", layout="wide")

st.title("🧠 Agentic AI Audit Dashboard")
st.write("Analyze model performance, fairness, and allocation equity.")


# ---------------------------
# Sidebar Navigation
# ---------------------------
page = st.sidebar.radio("Navigate", ["Model Audit", "Allocation Audit", "CSV Upload", "System Health"])

# ---------------------------
# 1️⃣ Model Audit
# ---------------------------
if page == "Model Audit":
    st.header("📊 Model Performance & Fairness Audit")

    y_true = st.text_area("Enter True Labels (comma-separated)", "1,0,1,1,0,1")
    y_pred = st.text_area("Enter Predicted Labels (comma-separated)", "1,0,1,0,0,1")
    sensitive = st.text_area("Enter Sensitive Attribute (0=female, 1=male)", "0,1,0,1,0,1")

    if st.button("Run Model Audit"):
        data = {
            "y_true": list(map(int, y_true.split(","))),
            "y_pred": list(map(int, y_pred.split(","))),
            "sensitive_attribute": list(map(int, sensitive.split(",")))
        }

        res = requests.post(f"{BACKEND_URL}/audit_model", json=data)
        if res.status_code == 200:
            result = res.json()
            st.success("✅ Audit Completed Successfully")

            st.subheader("Model Metrics")
            st.json(result["model_metrics"])

            st.subheader("Fairness Metrics")
            st.json(result["fairness_metrics"])

            st.subheader("Recommendation")
            st.info(result["recommendation"])
        else:
            st.error(res.text)


# ---------------------------
# 2️⃣ Allocation Audit
# ---------------------------
elif page == "Allocation Audit":
    st.header("🏥 Resource Allocation Fairness Audit")

    st.markdown("Upload a CSV with columns: `hospital_id, age, gender, allocated`")
    uploaded_file = st.file_uploader("Upload CSV", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df)

        if st.button("Run Allocation Audit"):
            allocations = df.to_dict(orient="records")
            res = requests.post(f"{BACKEND_URL}/audit_allocation", json={"allocations": allocations})

            if res.status_code == 200:
                result = res.json()
                st.success("✅ Allocation Audit Completed")
                st.subheader("Fairness Results")
                st.json(result["allocation_fairness"])
                st.subheader("Recommendation")
                st.info(result["recommendation"])
            else:
                st.error(res.text)


# ---------------------------
# 3️⃣ CSV Upload (Auto-Audit)
# ---------------------------
elif page == "CSV Upload":
    st.header("📁 CSV-Based Audit")

    st.markdown("Upload a CSV containing columns: `y_true`, `y_pred`, `sensitive_attribute`")

    uploaded_file = st.file_uploader("Upload CSV for automatic audit", type="csv")

    if uploaded_file:
        files = {"file": uploaded_file.getvalue()}
        res = requests.post(f"{BACKEND_URL}/audit_csv", files={"file": uploaded_file})

        if res.status_code == 200:
            result = res.json()
            st.success("✅ CSV Audit Completed")
            st.subheader("Performance Metrics")
            st.json(result["csv_audit"])
            st.subheader("Fairness Metrics")
            st.json(result["fairness"])
        else:
            st.error(res.text)


# ---------------------------
# 4️⃣ Health Check
# ---------------------------
elif page == "System Health":
    st.header("🔍 System Health Check")
    res = requests.get(f"{BACKEND_URL}/")
    if res.status_code == 200:
        st.success("✅ Backend is running")
        st.json(res.json())
    else:
        st.error("❌ Backend not reachable.")
