"""Simple A/B comparison harness for model metric candidates."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_metrics(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "federated_test_accuracy" in data:
        return {"accuracy": data["federated_test_accuracy"]}
    if "overall_accuracy" in data:
        return {"accuracy": data["overall_accuracy"]}
    return data


def compare(baseline: dict, candidate: dict, alpha: float = 0.05) -> dict:
    b_acc = float(baseline.get("accuracy", 0))
    c_acc = float(candidate.get("accuracy", 0))
    delta_pp = round((c_acc - b_acc) * 100, 2)
    significant = abs(delta_pp) >= 1.0
    winner = "candidate" if c_acc > b_acc else "baseline" if b_acc > c_acc else "tie"
    return {
        "baseline_accuracy": b_acc,
        "candidate_accuracy": c_acc,
        "delta_pp": delta_pp,
        "alpha": alpha,
        "significant_at_1pp": significant,
        "winner": winner,
        "recommendation": "promote_candidate" if winner == "candidate" and significant else "keep_baseline",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", default="docs/ab-test-report.json")
    args = parser.parse_args()

    result = compare(
        load_metrics(ROOT / args.baseline),
        load_metrics(ROOT / args.candidate),
    )
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()