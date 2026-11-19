"""Locust load test for the week-12 scaling demo.

One user sends at most one request per second, so "-u 60" means about 60 requests/s.

Every request opens a NEW connection ("Connection: close"). A Kubernetes Service balances per
connection, not per request: with keep-alive, connections made while only one pod existed would
stay on that pod forever and newly scaled-out pods would never receive traffic.
"""
import random

from locust import FastHttpUser, constant_throughput, task


class Client(FastHttpUser):
    wait_time = constant_throughput(1)  # at most 1 request per second per user

    @task
    def predict(self):
        self.client.post(
            "/predict",
            json={f"f{i}": round(random.uniform(-2, 2), 4) for i in range(10)},
            headers={"Connection": "close"},
        )
