#!/usr/bin/env bash
# Run from tutorial/fraud-detection. Every command is also safe to paste separately.
set -eu
mkdir -p models data

# Use the same Python and sklearn versions for training and container serving.
docker build -f docker/Dockerfile.prepare -t mlops-prepare:week3 .
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$PWD/models:/app/models" -v "$PWD/data:/app/data" mlops-prepare:week3

docker build -f docker/Dockerfile.single -t mlops-single:local .
docker build -f docker/Dockerfile.cpu -t mlops-cpu:local .
docker build -f docker/Dockerfile.onnx -t mlops-onnx:local .

# These commands return once HTTP and Docker HEALTHCHECK are ready.
python3 scripts/week3.py start cpu --port 18080
python3 scripts/week3.py start onnx --port 18081
curl -fsS http://127.0.0.1:18080/health
curl -fsS http://127.0.0.1:18080/predict \
  -H 'Content-Type: application/json' \
  -d '{"f0":0.1,"f1":-0.2,"f2":0.3,"f3":0.0,
       "f4":0.1,"f5":0.2,"f6":0.0,"f7":0.1,
       "f8":0.2,"f9":0.0}'
python3 scripts/week3.py api-check
python3 scripts/week3.py sizes --kinds single cpu onnx

trivy image --scanners vuln --severity HIGH,CRITICAL -f json \
  -o docs/week3/trivy-cpu.json mlops-cpu:local
trivy image --scanners vuln --severity HIGH,CRITICAL -f json \
  -o docs/week3/trivy-onnx.json mlops-onnx:local
trivy image -f spdx-json -o docs/week3/sbom-cpu.json mlops-cpu:local
python3 scripts/week3.py scan-report --gate
