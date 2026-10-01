"""Locust load test for fraud detection API (week 12)."""
from __future__ import annotations

import random

from locust import HttpUser, between, task


class FraudApiUser(HttpUser):
    wait_time = between(0.01, 0.05)

    @task
    def predict(self):
        payload = {f"f{i}": round(random.uniform(-2, 2), 4) for i in range(10)}
        self.client.post("/predict", json=payload)

    @task(1)
    def health(self):
        self.client.get("/health")