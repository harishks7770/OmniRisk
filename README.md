# 🛡️ OmniRisk: Real-Time Fraud Detection & MLOps Pipeline

**OmniRisk** is a production-grade, end-to-end Machine Learning Operations (MLOps) pipeline designed to detect fraudulent transactions in real-time. It bridges the gap between raw data engineering and live model serving by orchestrating feature stores, model registries, low-latency APIs, and automated data drift monitoring.

Designed to mimic an enterprise financial security stack, this system utilizes a **Hybrid Rules-and-ML Architecture**, combining hard business-logic thresholds with a trained XGBoost classifier to intercept anomalous spending velocity and volume.

---

## 🛠️ Tech Stack & Tools

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=FastAPI&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-%23FE4B4B.svg?style=for-the-badge&logo=streamlit&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

* **Feature Store:** Feast, Redis (Dockerized)
* **Model Tracking & Registry:** MLflow, SQLite
* **Machine Learning:** XGBoost, Scikit-Learn
* **Data Health & Drift:** SciPy (Kolmogorov-Smirnov Test)

---

## 🏗️ System Architecture

```mermaid
graph TD
    A[Parquet Data Batches] -->|Batch Load| B(Feast Feature Store)
    B -->|Sync| C[(Redis Online Store)]
    
    D[XGBoost Model] -->|Register & Version| E(MLflow Registry)
    
    C -->|Feature Fetch| F[FastAPI Inference Engine]
    E -->|Load Model| F
    
    F -->|JSON Response| G[Streamlit Live Dashboard]
    
    A -->|Snapshot Comparison| H[SciPy Data Drift Monitor]
    H -->|KS-Test Alert| I[GitHub Actions CI/CD Retraining]



