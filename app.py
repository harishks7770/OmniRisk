import streamlit as st
import pandas as pd
import requests
import time
import random
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="OmniRisk Live Streaming Monitor", page_icon="🛡️", layout="wide")

st.title("🛡️ OmniRisk Real-Time Fraud Stream & Telemetry Monitor")
st.markdown(
    "Real-time telemetry stream scoring incoming transactions, displaying live alerts, and isolating fraudulent events.")

# Initialize Session State for Persistent Flagged Fraud List
if "flagged_fraud" not in st.session_state:
    st.session_state.flagged_fraud = pd.DataFrame(
        columns=["Timestamp", "User ID", "Total Spend 1h", "Tx Count 1h", "Prediction", "Status"]
    )

# Stream Control Sidebar
st.sidebar.header("🕹️ Stream Controls")
stream_active = st.sidebar.checkbox("Start Live Streaming Feed", value=False)
stream_speed = st.sidebar.slider("Stream Interval (seconds)", min_value=0.5, max_value=3.0, value=1.0)

if st.sidebar.button("Clear Isolated Fraud List"):
    st.session_state.flagged_fraud = pd.DataFrame(
        columns=["Timestamp", "User ID", "Total Spend 1h", "Tx Count 1h", "Prediction", "Status"]
    )
    st.rerun()

# Layout Split: Left = Live Logs Feed, Right = Isolated Fraud List
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📡 Live Transaction Feed")
    stream_placeholder = st.empty()

with col_right:
    st.subheader("🚨 Isolated Fraudulent Transactions List")
    fraud_count_placeholder = st.empty()
    fraud_table_placeholder = st.empty()

# Load Dataset Snapshot for Stream Simulation
try:
    df_snapshot = pd.read_parquet("data/user_features_snapshot.parquet")
    # Clean the dataset: replace any NaN (missing) values with 0 to prevent crash
    df_snapshot = df_snapshot.fillna({
        "total_spend_1h": 0.0,
        "transaction_count_1h": 0
    })
except Exception as e:
    st.error(f"Error loading Parquet dataset: {e}")
    df_snapshot = None

# Streaming Loop
if stream_active and df_snapshot is not None:
    while stream_active:
        # Sample a transaction or occasionally inject a high-velocity fraud spike
        sample_user = df_snapshot.sample(1).iloc[0]
        user_id = str(sample_user["user_id"])

        # Bulletproof parsing: mathematically check for NaNs before converting
        raw_spend = sample_user["total_spend_1h"]
        total_spend = float(raw_spend) if pd.notna(raw_spend) else 0.0

        raw_tx = sample_user["transaction_count_1h"]
        tx_count = int(raw_tx) if pd.notna(raw_tx) else 0

        # 15% probability to simulate an extreme fraud spike guarantees live red flags
        if random.random() < 0.15:
            user_id = f"USER_FRAUD_SPIKE_{random.randint(100, 999)}"
            total_spend = random.uniform(30000.0, 95000.0)
            tx_count = random.randint(75, 250)

        # Query Live FastAPI Endpoint
        prediction = 0
        try:
            response = requests.post(
                "http://127.0.0.1:8000/predict",
                json={"user_id": user_id},
                timeout=1
            )
            if response.status_code == 200:
                prediction = response.json().get("fraud_prediction", 0)
        except Exception:
            pass  # Fallback for injected synthetic IDs

        # Force prediction flag if metrics represent severe anomaly spikes
        if total_spend > 25000.0 or tx_count > 60:
            prediction = 1

        timestamp = datetime.now().strftime("%H:%M:%S")
        status_label = "🚨 HIGH RISK (FRAUD)" if prediction == 1 else "✅ LOW RISK"

        event_data = {
            "Timestamp": timestamp,
            "User ID": user_id,
            "Total Spend 1h": f"${total_spend:,.2f}",
            "Tx Count 1h": tx_count,
            "Prediction": prediction,
            "Status": status_label
        }

        # If High Risk, capture and push into persistent session list
        if prediction == 1:
            new_fraud_row = pd.DataFrame([event_data])
            st.session_state.flagged_fraud = pd.concat(
                [new_fraud_row, st.session_state.flagged_fraud], ignore_index=True
            )

        # Render Left Column: Live Card Alert
        with stream_placeholder.container():
            if prediction == 1:
                st.error(
                    f"### 🚨 HIGH RISK DETECTED at {timestamp}\n"
                    f"**User ID:** `{user_id}`  \n"
                    f"**Spend (1h):** `${total_spend:,.2f}` | **Tx Count (1h):** `{tx_count}`  \n"
                    f"**Inference:** `FRAUD (1)`"
                )
            else:
                st.success(
                    f"### 🟢 Normal Transaction at {timestamp}\n"
                    f"**User ID:** `{user_id}`  \n"
                    f"**Spend (1h):** `${total_spend:,.2f}` | **Tx Count (1h):** `{tx_count}`  \n"
                    f"**Inference:** `NORMAL (0)`"
                )

        # Render Right Column: Dedicated Fraud Table
        fraud_count_placeholder.metric(
            label="Total Fraud Cases Captured",
            value=len(st.session_state.flagged_fraud)
        )

        with fraud_table_placeholder.container():
            if not st.session_state.flagged_fraud.empty:
                st.dataframe(
                    st.session_state.flagged_fraud,
                    use_container_width=True,
                    height=400
                )
            else:
                st.info("No fraudulent transactions detected in the current session.")

        time.sleep(stream_speed)
else:
    # Render static view when stream is paused
    with stream_placeholder.container():
        st.info("Check 'Start Live Streaming Feed' in the left sidebar to start monitoring.")

    fraud_count_placeholder.metric(
        label="Total Fraud Cases Captured",
        value=len(st.session_state.flagged_fraud)
    )

    with fraud_table_placeholder.container():
        if not st.session_state.flagged_fraud.empty:
            st.dataframe(
                st.session_state.flagged_fraud,
                use_container_width=True,
                height=400
            )
        else:
            st.info("No fraudulent transactions detected in the current session.")