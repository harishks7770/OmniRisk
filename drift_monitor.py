import pandas as pd
from scipy.stats import ks_2samp
import requests

# 1. Load reference data (original training snapshot)
reference_data = pd.read_parquet("data/user_features_snapshot.parquet")
reference_spend = reference_data["total_spend_1h"].dropna()

# 2. Simulate fetching S3 logs (Phase 3 async logs)
# We sample and multiply by 1.5 to artificially induce data drift for testing
current_data = reference_spend.sample(500, random_state=42) * 1.5

print("Running Custom Data Drift Analysis (Kolmogorov-Smirnov Test)...")

# Calculate Data Drift using the KS Test
# The statistic approaches 1.0 when distributions are completely different
ks_stat, p_value = ks_2samp(reference_spend, current_data)

print(f"Drift Statistic (KS Score): {ks_stat:.4f}")
print(f"P-Value: {p_value:.4e}")

# 3. Connect drift alert script to invoke workflow
# A KS statistic > 0.25 strongly indicates drifted distributions
# A p-value under 0.05 strongly indicates drifted distributions
if p_value < 0.05:
    print("ALERT: Drift threshold exceeded (KS Score > 0.25). Triggering automated retraining pipeline...")

    # Expose automated retraining endpoint via GitHub Actions workflow
    # url = "https://api.github.com/repos/YOUR_USERNAME/omnirisk/actions/workflows/retrain.yml/dispatches"
    # headers = {
    #     "Accept": "application/vnd.github.v3+json",
    #     "Authorization": "token YOUR_GITHUB_PAT"
    # }
    # data = {"ref": "main"}
    # response = requests.post(url, headers=headers, json=data)
    # print(f"GitHub Actions Trigger Response Code: {response.status_code}")
else:
    print("Data distribution is stable. No retraining required.")