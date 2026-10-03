# Security Audit Report — Week 13

Date: _YYYY-MM-DD_ | Team: _name_

## 1. Threat model summary

| Threat | Likelihood | Impact | Control |
|--------|------------|--------|---------|
| Model evasion | Medium | High | Input validation, bounds |
| Model extraction | Low | High | Rate limit, audit, minimal output |
| Container CVE | Medium | High | Trivy CI gate |
| Privileged pod | Low | Critical | Gatekeeper policy |
| PII leakage in logs | Medium | Critical | PII rejection + feature hash |

## 2. Supply chain

| Check | Status | Evidence |
|-------|--------|----------|
| Trivy scan (CRITICAL=0) | _pass/fail_ | `docs/security-audit.json` |
| SBOM generated | _pass/fail_ | `docs/sbom-cpu.json` |
| Image tag pinned (not :latest) | _pass/fail_ | `k8s/deployment-cpu.yaml` |

## 3. Policy-as-code (Gatekeeper)

| Policy | File | Status |
|--------|------|--------|
| Disallow privileged | `security/policies/disallow-privileged.yaml` | _ |
| Require limits | `security/policies/require-limits.yaml` | _ |
| Disallow :latest | `security/policies/disallow-latest-tag.yaml` | _ |
| Require non-root | `security/policies/require-non-root.yaml` | _ |

## 4. Runtime controls

| Control | Status | Notes |
|---------|--------|-------|
| NetworkPolicy | _ | `k8s/network-policy-fraud-api.yaml` |
| Secrets template (no plain secrets in Git) | _ | `security/secrets-template.yaml` |
| Inference audit log | _ | `docs/inference-audit.log` |
| Model watermark verified | _ | `models/model.pkl.manifest.json` |

## 5. Adversarial probe results

Run: `python scripts/adversarial_probe.py --samples 100`

| Metric | Value |
|--------|-------|
| Baseline accuracy | _ |
| Adversarial accuracy | _ |
| Prediction flip rate | _ |

## 6. Compliance mapping (summary)

- **GDPR:** PII fields blocked at API; audit uses feature hash only.
- **EU AI Act:** Logging + technical documentation path via requirements.md and this report.

## 7. Open risks / accepted risks

_(List any accepted HIGH CVEs with expiry date and mitigation plan.)_