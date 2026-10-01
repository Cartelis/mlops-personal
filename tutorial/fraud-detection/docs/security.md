# Security Hardening — Week 13

## Scope

- ML threat model: evasion, extraction, poisoning
- Supply chain: Trivy scan + SBOM
- Policy-as-code: Gatekeeper constraints
- API: PII rejection + inference audit (no raw features stored)
- Model watermark manifest

## Quick demo (local)

```bash
python scripts/bootstrap.py
python -m security.watermark --apply --model models/model.pkl
python -m security.watermark --verify --model models/model.pkl

python scripts/adversarial_probe.py --samples 100
python scripts/generate_sbom.py --image mlops-cpu:local --output docs/sbom-cpu.json
python scripts/security_scan.py --image mlops-cpu:local

python -m uvicorn src.serve:app --port 8080 &
curl -s -X POST localhost:8080/predict -H 'Content-Type: application/json' \
  -d '{"f0":0.1,"email":"a@b.com"}'   # expect 422 PII rejected
curl -s -X POST localhost:8080/predict -H 'Content-Type: application/json' \
  -d '{"f0":0.1,"f1":0.2,"f2":0.3,"f3":0.4,"f4":0.5,"f5":0.6,"f6":0.7,"f7":0.8,"f8":0.9,"f9":1.0}'

python scripts/run_security_audit.py --output docs/security-audit.json
```

## Kubernetes

```bash
kubectl apply -f security/policies/
kubectl apply -f k8s/network-policy-fraud-api.yaml
```

## CI

`.github/workflows/security.yml` runs Trivy on PR/push and uploads SBOM.

## Compliance notes

| Framework | ML relevance |
|-----------|----------------|
| GDPR | PII minimization, audit without personal data |
| EU AI Act | Risk management, logging, documentation for high-risk AI |
| NIST AI RMF | Map threats to controls (scan, policy, audit) |

## NFR (v1.12)

| ID | Requirement |
|----|-------------|
| NFR-50 | 0 critical CVEs in production images |
| NFR-51 | 100% deployments pass Gatekeeper |
| NFR-52 | 100% `/predict` calls audited |
| NFR-53 | 100% PII fields rejected |