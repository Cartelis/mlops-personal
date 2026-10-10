"""Self-healing MLOps agent using LangGraph."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Literal, TypedDict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langgraph.graph import END, StateGraph

from agents import tools

APPROVAL_FILE = ROOT / "approvals" / "production.flag"


class AgentState(TypedDict, total=False):
    incident_id: str
    approved: bool
    drift: dict
    metrics: dict
    gate: dict
    status: str
    message: str


def node_monitor(state: AgentState) -> AgentState:
    drift = tools.tool_check_drift()
    return {**state, "drift": drift, "status": "monitored"}


def route_after_monitor(state: AgentState) -> Literal["retrain", "notify_only"]:
    if state.get("drift", {}).get("drift_detected"):
        return "retrain"
    return "notify_only"


def node_retrain(state: AgentState) -> AgentState:
    retrain_result = tools.tool_run_retrain(approve=state.get("approved", False))
    if retrain_result.get("status") == "blocked":
        return {**state, "status": "retrain_blocked", "message": retrain_result["reason"]}
    metrics = tools.tool_read_metrics()
    gate = tools.tool_model_gate(metrics)
    return {**state, "metrics": metrics, "gate": gate, "status": "retrained"}


def route_after_retrain(state: AgentState) -> Literal["approve", "fail_gate", "blocked"]:
    if state.get("status") == "retrain_blocked":
        return "blocked"
    if not state.get("gate", {}).get("passed", False):
        return "fail_gate"
    return "approve"


def node_wait_approval(state: AgentState) -> AgentState:
    if state.get("approved") or APPROVAL_FILE.exists():
        return {**state, "approved": True, "status": "approved"}
    return {**state, "status": "pending_approval"}


def route_after_approval(state: AgentState) -> Literal["deploy", "wait"]:
    if state.get("approved") or APPROVAL_FILE.exists():
        return "deploy"
    return "wait"


def node_deploy(state: AgentState) -> AgentState:
    tools.tool_deploy()
    acc = state.get("metrics", {}).get("accuracy", "n/a")
    psi = state.get("drift", {}).get("psi", "n/a")
    msg = (
        f"[{state['incident_id']}] Self-healing deploy complete. "
        f"psi={psi} accuracy={acc}"
    )
    tools.tool_notify_slack(msg)
    return {**state, "status": "deployed", "message": msg}


def node_notify_only(state: AgentState) -> AgentState:
    msg = f"[{state['incident_id']}] No drift detected. Monitoring OK."
    tools.tool_notify_slack(msg)
    return {**state, "status": "no_action", "message": msg}


def node_fail_gate(state: AgentState) -> AgentState:
    msg = f"[{state['incident_id']}] Model gate failed. Manual review required."
    tools.tool_notify_slack(msg)
    return {**state, "status": "gate_failed", "message": msg}


def node_blocked(state: AgentState) -> AgentState:
    msg = f"[{state['incident_id']}] Retrain blocked by guardrail."
    tools.tool_notify_slack(msg)
    return {**state, "status": "blocked", "message": msg}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("monitor", node_monitor)
    graph.add_node("retrain", node_retrain)
    graph.add_node("wait_approval", node_wait_approval)
    graph.add_node("deploy", node_deploy)
    graph.add_node("notify_only", node_notify_only)
    graph.add_node("fail_gate", node_fail_gate)
    graph.add_node("blocked", node_blocked)

    graph.set_entry_point("monitor")
    graph.add_conditional_edges("monitor", route_after_monitor, {
        "retrain": "retrain",
        "notify_only": "notify_only",
    })
    graph.add_conditional_edges("retrain", route_after_retrain, {
        "approve": "wait_approval",
        "fail_gate": "fail_gate",
        "blocked": "blocked",
    })
    graph.add_conditional_edges("wait_approval", route_after_approval, {
        "deploy": "deploy",
        "wait": END,
    })

    graph.add_edge("deploy", END)
    graph.add_edge("notify_only", END)
    graph.add_edge("fail_gate", END)
    graph.add_edge("blocked", END)
    return graph.compile()


def run_agent(incident_id: str, approve: bool = False) -> dict:
    app = build_graph()
    result = app.invoke({
        "incident_id": incident_id,
        "approved": approve,
    })
    print(json.dumps(result, indent=2, default=str))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--incident-id", default="DR-LOCAL-001")
    parser.add_argument("--approve", action="store_true")
    args = parser.parse_args()
    run_agent(args.incident_id, approve=args.approve)


if __name__ == "__main__":
    main()