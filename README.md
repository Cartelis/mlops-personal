# Fraud Detection — MLOps semester reference project

Reference scaffold for course weeks 1–16. Students fork or copy this structure into their team repo.

## Week 3: verified Docker lab

On Ubuntu 22.04/24.04, first follow [Docker and Trivy setup](docs/setup-ubuntu.md). Then use [the step-by-step Week 3 guide](docs/week3.md). It prepares the model inside a pinned container environment, then builds, starts and checks CPU/ONNX APIs, records real image sizes, scans vulnerabilities and documents GPU/GHCR prerequisites. The executable command sequence is `scripts/week3-local.sh`.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Generate sample data and train a baseline model
python scripts/bootstrap.py

# Week 2: MLflow + DVC pipeline
export MLFLOW_TRACKING_URI=http://127.0.0.1:5000
mlflow server --port 5000 &   # separate terminal
dvc repro

# Week 3: use the self-contained pinned preparation + Docker path
# Requires Docker Server, Python3 (standard library only), curl, Trivy.
bash scripts/week3-local.sh

# Week 4: GCP Terraform + Cloud Run
./scripts/enable_gcp_apis.sh <gcp-project-id>
cd infra && cp terraform.tfvars.example terraform.tfvars
# edit project_id, then: terraform init && terraform apply

# Week 5: Kubernetes inference + HPC GPU training
./scripts/k8s_deploy.sh
kubectl apply -f k8s/job-training-single-node.yaml   # HPC only

# Week 6: CI/CD (local checks)
pip install -r requirements-dev.txt
pytest tests/ -v
python scripts/check_model_gate.py --threshold 0.95

# Week 7: Model Registry + serving
python scripts/register_model.py
kubectl apply -f deploy/kserve/inference-service-onnx.yaml
# HPC: kubectl apply -f deploy/kserve/inference-service-vllm.yaml
python scripts/benchmark_vllm.py --url http://localhost:8000 --model <model> --output docs/benchmark-fp16.json

# Week 8: GPU profiling (HPC)
python scripts/benchmark_gpu_inference.py --precision fp32 --batch-size 1 --output docs/benchmark-gpu-fp32-b1.json
python scripts/benchmark_gpu_inference.py --precision amp --batch-size 32 --output docs/benchmark-gpu-amp-b32.json
python scripts/profile_gpu.py

# Week 9: Airflow 3 + Ray + MLflow in a kind cluster (see docs/orchestration.md)
scripts/lab9/00_preflight.sh && scripts/lab9/01_build_image.sh      # at home
scripts/lab9/02_cluster_up.sh ... scripts/lab9/09_inference_test.sh  # the lab, one script at a time
# Ray-only variant (also used by week 10):
pip install -r requirements-orchestration.txt
export MLFLOW_TRACKING_URI=http://127.0.0.1:5000
python pipeline/ray_pipeline.py --run-id demo --approve

# Week 10: Self-healing agent
pip install -r requirements-agents.txt -r requirements-orchestration.txt
export MLFLOW_TRACKING_URI=sqlite:///mlflow.db
python scripts/simulate_drift.py
python -m agents.mlops_agent --incident-id DR-001 --approve

# Week 11: Observability stack
pip install -r requirements-observability.txt
python -m uvicorn src.serve:app --port 8080 &
python scripts/generate_traffic.py --requests 200
python -m observability.evidently_report --output docs/drift-report.json
python scripts/aiops_correlate.py --drift-report docs/drift-report.json
# Optional: docker compose -f monitoring/docker-compose.yml up -d

# Week 12: Scaling & cost engineering
pip install -r requirements-scaling.txt
python scripts/run_load_test.py --users 50 --run-time 1m
python scripts/scaling_simulator.py --rps 800
python scripts/tco_calculator.py --replicas 32 --spot --rightsizing
kubectl apply -f k8s/hpa-fraud-api.yaml

# Week 13: Security & compliance
python -m security.watermark --apply --model models/model.pkl
python scripts/adversarial_probe.py --samples 100
python scripts/generate_sbom.py --image mlops-cpu:local
python scripts/run_security_audit.py
kubectl apply -f security/policies/
kubectl apply -f k8s/network-policy-fraud-api.yaml

# Week 14: Edge MLOps + Federated Learning
pip install -r requirements-edge-fl.txt
python scripts/optimize_edge_model.py
python scripts/benchmark_edge.py
docker build -f docker/Dockerfile.edge -t mlops-edge:local .
python -m federated.partition_data --clients 3
python -m federated.fl_simulation --rounds 5 --clients 3

# Week 15: Testing & validation
pip install -r requirements-testing.txt
python scripts/run_data_validation.py
pytest tests/ -v
# docs/traceability.md, requirements v1.14

# Week 16: Governance + capstone package
pip install -r requirements-governance.txt
python scripts/generate_governance_report.py
pytest tests/test_governance.py -v
# docs/model-card.md, docs/governance-report.json, requirements v1.15
```

## Layout

| Path | Purpose |
|------|---------|
| `docs/requirements.md` | Living requirements (v1.0 → v1.15) |
| `governance/` | Model card + capstone checklist (week 16) |
| `validation/` | Data contract + slice tests (week 15) |
| `docs/traceability.md` | NFR → test mapping (week 15) |
| `federated/` | Flower FedAvg simulation (week 14) |
| `deploy/edge/` | Edge K8s deployment (week 14) |
| `security/` | Policies, validation, audit, watermark (week 13) |
| `scaling/` | Locust load tests (week 12) |
| `k8s/hpa-fraud-api.yaml` | HPA 1–50 replicas (week 12) |
| `monitoring/` | Prometheus, Grafana, alerts (week 11) |
| `observability/` | JSON logging, Evidently reports (week 11) |
| `agents/` | LangGraph self-healing agent (week 10) |
| `pipeline/` | Ray orchestration pipeline (week 9) |
| `.github/workflows/` | ML CI/CD pipeline (week 6) |
| `deploy/kserve/` | KServe and vLLM manifests (week 7) |
| `deploy/argocd/` | GitOps Application manifest |
| `tests/` | Unit and integration tests |
| `src/` | Training, evaluation, serving, DDP, GPU inference |
| `docker/` | CPU, GPU, ONNX Dockerfiles |
| `infra/` | GCP Terraform (week 4) |
| `k8s/` | Kubernetes manifests (week 5) |
| `scripts/` | Bootstrap, model gate, k8s deploy |
| `dvc.yaml` | Reproducible pipeline (week 2) |
| `reproduce.py` | Re-run a historical MLflow experiment |
# Mašininio mokymosi operacijų sistemos (MLOps) kurso repo

Užrašai [knyga (pdf)](https://klevas.mif.vu.lt/~linp/mlops/mlops-uzrasai.pdf).
Pratybų [notes (pdf)](https://klevas.mif.vu.lt/~linp/mlops/mlops-pratybos.pdf)

#### Artimiausios datos:
1. [Pirmos užduoties](./pirma.md) pridavimo data (2026-10-21)
2. [Komandinių užduočių registracija](./komandine.md) (2026-10-28)
3. [Antros užduoties](./antra.md) pridavimo data (2026-11-11)
4. Komandinės užduoties pridavimo data (2026-12-09)
5. Komandinės užduoties pristatymas (2026-12-16)
6. Egzaminas ()

### Atsiskaitymai:
1. [Pirma užduotis](./pirma.md)
2. [Antra užduotis](./antra.md)
3. [Komandinės užduotys](./komandine.md)

#### Kurso turinys:
1. (2026-09-09) 1 savaitė: [Teorija](https://klevas.mif.vu.lt/~linp/mlops/mlops-01.pdf).
2. (2026-09-10) 2 savaitė: [Teorija](./slides/mlops-02.pdf).
3. (2026-09-17) 3 savaitė: [Teorija](https://klevas.mif.vu.lt/~linp/mlops/mlops-03.pdf).
4. (2026-09-24) 4 savaitė: [Teorija](https://klevas.mif.vu.lt/~linp/mlops/mlops-04.pdf).
5. (2026-10-01) 5 savaitė: [Teorija](https://klevas.mif.vu.lt/~linp/mlops/mlops-05.pdf).
6. (2026-10-08) 6 savaitė: [Teorija](https://klevas.mif.vu.lt/~linp/mlops/mlops-06.pdf).
