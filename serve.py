import pandas as pd
import boto3
import json
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from feast import FeatureStore
import mlflow

app = FastAPI(title="OmniRisk Inference API")
store = None
model = None


class PredictRequest(BaseModel):
    user_id: str


@app.on_event("startup")
def initialize_services():
    global store, model
    # 1. Initialize Feast online client inside FastAPI startup event to fetch features from Redis[cite: 1]
    store = FeatureStore(repo_path="feast_repo")

    # 2. Load the registered XGBoost model from MLflow
    mlflow.set_tracking_uri("sqlite:///mlruns.db")
    model = mlflow.pyfunc.load_model("models:/OmniRisk_Fraud_Detector/1")
    print("Feast Online Store and MLflow Model loaded successfully.")


def log_to_s3(request_data, prediction, feature_vector):
    """
    Serve predictions and send request/response pairs asynchronously to an S3 bucket for logging.
    """
    payload = {
        "user_id": request_data.user_id,
        "features": feature_vector,
        "prediction": int(prediction)
    }

    print(f"Async S3 Logging Triggered: {payload}")

    # Commented out until AWS credentials are provided for production
    # s3 = boto3.client('s3')
    # s3.put_object(
    #     Bucket='omnirisk-inference-logs',
    #     Key=f"logs/{request_data.user_id}.json",
    #     Body=json.dumps(payload)
    # )


@app.post("/predict")
async def predict_fraud(request: PredictRequest, background_tasks: BackgroundTasks):
    # Build a FastAPI service that accepts a POST request payload[cite: 1]

    # Fetch real-time features from Redis
    online_features = store.get_online_features(
        features=[
            "user_features:transaction_count_1h",
            "user_features:total_spend_1h"
        ],
        entity_rows=[{"user_id": request.user_id}]
    ).to_dict()

    # Convert to DataFrame for model expected format
    df = pd.DataFrame(online_features)
    model_input = df[["transaction_count_1h", "total_spend_1h"]]

    # Generate Prediction
    prediction = model.predict(model_input)[0]

    # Send logs asynchronously to avoid blocking the API response[cite: 1]
    background_tasks.add_task(log_to_s3, request, prediction, online_features)

    return {
        "user_id": request.user_id,
        "fraud_prediction": int(prediction)
    }