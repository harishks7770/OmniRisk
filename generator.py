# generator.py
import json
import time
import random
from datetime import datetime
from faker import Faker
import os

fake = Faker()
os.makedirs("data/raw_stream", exist_ok=True)

print("Starting synthetic transaction generator...")
batch_id = 0

while True:
    transactions = []
    for _ in range(50):  # Generate 50 events per batch
        transactions.append({
            "transaction_id": fake.uuid4(),
            "user_id": f"USER_{random.randint(100, 999)}",
            "merchant_id": f"MERCH_{random.randint(10, 99)}",
            "amount": round(random.uniform(5.0, 5000.0), 2),
            "event_timestamp": datetime.utcnow().isoformat() + "Z",
            "is_fraud": random.choice([0, 0, 0, 0, 1])  # 20% mock fraud rate
        })

    file_path = f"data/raw_stream/batch_{batch_id}_{int(time.time())}.json"
    with open(file_path, "w") as f:
        for t in transactions:
            f.write(json.dumps(t) + "\n")

    print(f"Written batch {batch_id} to {file_path}")
    batch_id += 1
    time.sleep(2)  # Emit every 2 seconds