import glob
import pandas as pd
import dask

# Force Dask to use single-threaded execution on Windows to avoid process deadlock
dask.config.set(scheduler="synchronous")

from feast import FeatureStore
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, f1_score, accuracy_score
import mlflow
import mlflow.xgboost

# 1. Initialize Feast Feature Store
store = FeatureStore(repo_path="feast_repo")

# 2. Extract Ground Truth Observation Entities
raw_files = glob.glob("data/raw_stream/*.json")
if not raw_files:
    raise FileNotFoundError("No raw transaction files found in data/raw_stream. Ensure generator container is running!")

df_raw = pd.concat([pd.read_json(f, lines=True) for f in raw_files], ignore_index=True)

# Make timestamp UTC timezone-aware for Feast
df_raw["event_timestamp"] = pd.to_datetime(df_raw["event_timestamp"], utc=True)

# Sample the latest 2,000 events for fast local join execution
entity_df = df_raw[["user_id", "event_timestamp", "is_fraud"]].sort_values("event_timestamp").tail(2000).copy()
print(f"Loaded {len(entity_df)} recent observation events for feature retrieval.")

# 3. Perform Feast Point-in-Time Join
print("Fetching point-in-time historical features via Feast...")
training_data = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "user_features:transaction_count_1h",
        "user_features:total_spend_1h"
    ]
).to_df()

# Handle initial boundary nulls
training_data = training_data.fillna(0)
print(f"Feature join completed! Feature matrix shape: {training_data.shape}")

# 4. Prepare Train/Test Split
X = training_data[["transaction_count_1h", "total_spend_1h"]]
y = training_data["is_fraud"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5. MLflow Tracking and Model Registry

# Force a relative local SQLite database to bypass Windows space-encoding bugs
mlflow.set_tracking_uri("sqlite:///mlruns.db")
mlflow.set_experiment("OmniRisk_Fraud_Detection")

with mlflow.start_run() as run:
    params = {
        "n_estimators": 100,
        "max_depth": 4,
        "learning_rate": 0.05,
        "eval_metric": "logloss",
        "random_state": 42
    }

    # Log Hyperparameters
    mlflow.log_params(params)

    # Train XGBoost Model
    print("Training XGBoost Fraud Detection Model...")
    model = xgb.XGBClassifier(**params)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if len(model.classes_) > 1 else y_pred

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "f1_score": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_proba) if len(set(y_test)) > 1 else 0.5
    }

    # Log Metrics
    mlflow.log_metrics(metrics)
    print("Execution Metrics:", metrics)

    # Register Artifact in MLflow Model Registry
    mlflow.xgboost.log_model(
        xgb_model=model,
        artifact_path="model",
        registered_model_name="OmniRisk_Fraud_Detector"
    )

    print("Run completed successfully! Model registered under 'OmniRisk_Fraud_Detector'.")