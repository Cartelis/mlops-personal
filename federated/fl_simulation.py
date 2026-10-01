"""FedAvg simulation for fraud detection (local engine + optional Flower Ray engine)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

ROOT = Path(__file__).resolve().parents[1]
TEST_PATH = ROOT / "data" / "processed" / "test.csv"
RESULTS_PATH = ROOT / "docs" / "fl-results.json"


def load_xy(path: Path) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(path)
    features = [c for c in df.columns if c.startswith("f")]
    return df[features].to_numpy(), df["target"].to_numpy()


class FraudClient:
    """Sklearn client compatible with FedAvg weight averaging."""

    def __init__(self, cid: int):
        path = ROOT / "data" / "federated" / f"client_{cid}" / "train.csv"
        self.x, self.y = load_xy(path)
        self.model = LogisticRegression(max_iter=200, random_state=42 + cid)

    def get_parameters(self) -> list[np.ndarray]:
        if not hasattr(self.model, "coef_"):
            self.model.fit(self.x, self.y)
        return [self.model.coef_.copy(), self.model.intercept_.copy()]

    def set_parameters(self, parameters: list[np.ndarray]) -> None:
        self.model.coef_ = np.array(parameters[0])
        self.model.intercept_ = np.array(parameters[1])
        self.model.classes_ = np.array([0, 1])

    def fit(self, parameters: list[np.ndarray]) -> tuple[list[np.ndarray], int]:
        self.set_parameters(parameters)
        self.model.fit(self.x, self.y)
        return self.get_parameters(), len(self.x)


def fedavg_aggregate(results: list[tuple[list[np.ndarray], int]]) -> list[np.ndarray]:
    total = sum(n for _, n in results)
    coef = sum(p[0] * n for p, n in results) / total
    intercept = sum(p[1] * n for p, n in results) / total
    return [coef, intercept]


def evaluate_params(parameters: list[np.ndarray], test_x: np.ndarray, test_y: np.ndarray) -> float:
    model = LogisticRegression(max_iter=200)
    model.coef_ = np.array(parameters[0])
    model.intercept_ = np.array(parameters[1])
    model.classes_ = np.array([0, 1])
    return float(accuracy_score(test_y, model.predict(test_x)))


def centralized_baseline(test_x: np.ndarray, test_y: np.ndarray) -> float:
    train_x, train_y = load_xy(ROOT / "data" / "processed" / "train.csv")
    model = LogisticRegression(max_iter=300, random_state=42)
    model.fit(train_x, train_y)
    return float(accuracy_score(test_y, model.predict(test_x)))


def run_fedavg_local(clients: int, rounds: int) -> list[np.ndarray]:
    client_objs = [FraudClient(i) for i in range(clients)]
    global_params = client_objs[0].get_parameters()
    for _ in range(rounds):
        results = [c.fit(global_params) for c in client_objs]
        global_params = fedavg_aggregate(results)
    return global_params


def run_fedavg_flower(clients: int, rounds: int) -> list[np.ndarray]:
    import flwr as fl
    from flwr.client import NumPyClient

    class FlowerClient(NumPyClient):
        def __init__(self, cid: int):
            self._client = FraudClient(cid)

        def get_parameters(self, config):
            return self._client.get_parameters()

        def set_parameters(self, parameters):
            self._client.set_parameters(parameters)

        def fit(self, parameters, config):
            updated, n = self._client.fit(parameters)
            return updated, n, {}

        def evaluate(self, parameters, config):
            self.set_parameters(parameters)
            acc = float(accuracy_score(self._client.y, self._client.model.predict(self._client.x)))
            return float(1.0 - acc), len(self._client.x), {"accuracy": acc}

    def client_fn(cid: str):
        return FlowerClient(int(cid)).to_client()

    fl.simulation.start_simulation(
        client_fn=client_fn,
        num_clients=clients,
        config=fl.server.ServerConfig(num_rounds=rounds),
        strategy=fl.server.strategy.FedAvg(),
        client_resources={"num_cpus": 1},
    )
    return run_fedavg_local(clients, rounds)


def run_simulation(clients: int, rounds: int, engine: str) -> dict:
    test_x, test_y = load_xy(TEST_PATH)
    if engine == "flower":
        final_params = run_fedavg_flower(clients, rounds)
        engine_used = "flower-ray"
    else:
        final_params = run_fedavg_local(clients, rounds)
        engine_used = "local-fedavg"

    fed_acc = evaluate_params(final_params, test_x, test_y)
    cent_acc = centralized_baseline(test_x, test_y)
    gap_pp = round((cent_acc - fed_acc) * 100, 2)

    return {
        "clients": clients,
        "rounds": rounds,
        "strategy": "FedAvg",
        "engine": engine_used,
        "centralized_accuracy": round(cent_acc, 4),
        "federated_test_accuracy": round(fed_acc, 4),
        "accuracy_gap_pp": gap_pp,
        "meets_2pp_target": gap_pp <= 2.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clients", type=int, default=3)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--engine", choices=["local", "flower"], default="local")
    args = parser.parse_args()

    partition_path = ROOT / "data" / "federated" / "client_0" / "train.csv"
    if not partition_path.exists():
        from federated.partition_data import partition

        partition(args.clients)

    result = run_simulation(args.clients, args.rounds, args.engine)
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()