#!/usr/bin/env bash
# Week 13 self-check. Run from the repo's tutorial/fraud-detection folder:
#   bash security/check.sh          # checks M1 and M2
#   bash security/check.sh m1       # only M1
# Read-only: it never changes your cluster (uses server-side dry-run and exec).
# Self-check only (week 13 lab is not graded separately): aim for "Score: 9/9".
set -u
K="${KUBECTL:-kubectl}"
NS="vault"
DIR="$(cd "$(dirname "$0")" && pwd)"
only="${1:-all}"
# Fixed denominators: a check that cannot run yet counts as not passed,
# so "6/7" never looks like "almost done" when 3 checks were skipped.
case "$only" in m1) TOTAL=6;; m2) TOTAL=3;; *) TOTAL=9;; esac
pass=0
ok()  { pass=$((pass+1)); printf '  \033[32mPASS\033[0m %s\n' "$*"; }
no()  { printf '  \033[31mFAIL\033[0m %s\n' "$*"; }
hint(){ printf '       hint: %s\n' "$*"; }

echo "week13 check | $(date '+%Y-%m-%d %H:%M') | context: $($K config current-context 2>/dev/null) | user: $(git config user.name 2>/dev/null || whoami)"

if ! $K get ns "$NS" >/dev/null 2>&1; then
  no "namespace '$NS' exists"; hint "kubectl apply -f security/lab/base/vault.yaml"; echo "Score: $pass/$TOTAL"; exit 1
fi

if [ "$only" = "all" ] || [ "$only" = "m1" ]; then
  echo "== M1. Admission policies (Gatekeeper)"
  if $K -n gatekeeper-system get deploy gatekeeper-controller-manager >/dev/null 2>&1 &&
     [ "$($K -n gatekeeper-system get deploy gatekeeper-controller-manager -o jsonpath='{.status.readyReplicas}' 2>/dev/null)" -ge 1 ] 2>/dev/null; then
    ok "Gatekeeper is running"
  else
    no "Gatekeeper is running"; hint "kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.23.1/deploy/gatekeeper.yaml"
    hint "Gatekeeper fails OPEN: if it is down, every deploy is allowed. That's why we check it first."
  fi

  n=0
  for t in k8sdisallowprivileged k8srequirenonroot k8srequirelimits k8sdisallowlatesttag; do
    [ "$($K get constrainttemplate "$t" -o jsonpath='{.status.created}' 2>/dev/null)" = "true" ] && n=$((n+1))
  done
  [ "$n" -eq 4 ] && ok "4/4 ConstraintTemplates created" || { no "$n/4 ConstraintTemplates created"; hint "kubectl apply -f security/policies/templates/"; }

  n=0
  for c in k8sdisallowprivileged/vault-no-privileged k8srequirenonroot/vault-non-root k8srequirelimits/vault-require-limits k8sdisallowlatesttag/vault-pinned-images; do
    $K get "$c" >/dev/null 2>&1 && n=$((n+1))
  done
  [ "$n" -eq 4 ] && ok "4/4 Constraints active in namespace '$NS'" || { no "$n/4 Constraints active"; hint "kubectl wait --for=jsonpath='{.status.created}'=true constrainttemplate --all --timeout=60s && kubectl apply -f security/policies/constraints/"; }

  out="$($K apply --dry-run=server -f "$DIR/lab/bad-deployment.yaml" 2>&1)"
  rules=0
  for r in privileged non-root limits image-tag; do echo "$out" | grep -q "\[$r\]" && rules=$((rules+1)); done
  if [ "$rules" -eq 4 ]; then ok "bad-deployment.yaml is DENIED by all 4 rules"
  else no "bad-deployment.yaml denied by $rules/4 rules"; hint "is Gatekeeper ready and are all 4 constraints applied?"; fi

  good="$DIR/lab/good-deployment.yaml"
  if [ ! -f "$good" ]; then
    no "security/lab/good-deployment.yaml exists"; hint "cp security/lab/bad-deployment.yaml security/lab/good-deployment.yaml  and fix it"
  else
    out="$($K apply --dry-run=server -f "$good" 2>&1)"
    if echo "$out" | grep -q "denied"; then no "good-deployment.yaml is accepted"; echo "$out" | sed 's/^/       /' | head -8
    else
      ok "good-deployment.yaml is accepted"
      ready="$($K -n "$NS" get deploy model-trainer -o jsonpath='{.status.readyReplicas}' 2>/dev/null)"
      if [ "${ready:-0}" -ge 1 ] 2>/dev/null; then ok "model-trainer is actually Running (accepted != working)"
      else no "model-trainer is Running"; hint "kubectl apply -f security/lab/good-deployment.yaml; kubectl -n vault get pods; kubectl -n vault describe pod -l app=model-trainer"
           hint "admitted but not starting? an image that needs root cannot run with runAsNonRoot - pick a non-root image"; fi
    fi
  fi
fi

if [ "$only" = "all" ] || [ "$only" = "m2" ]; then
  echo "== M2. Network isolation (NetworkPolicy)"
  reach() { $K -n "$NS" exec "$1" -- wget -qO- -T 3 http://mlflow:5000 >/dev/null 2>&1; }
  if ! $K -n "$NS" get pod attacker >/dev/null 2>&1; then
    no "attacker pod exists"; hint "kubectl apply -f security/lab/attacker-pod.yaml"
  else
    np="$($K -n "$NS" get networkpolicy -o name 2>/dev/null | wc -l | tr -d ' ')"
    [ "$np" -ge 2 ] && ok "$np NetworkPolicies in '$NS'" || { no "at least 2 NetworkPolicies (default-deny + your allow rule), found $np"; hint "kubectl apply -f security/lab/default-deny.yaml"; }
    if reach pod/attacker; then no "attacker CANNOT reach mlflow"; hint "is default-deny applied? does your cluster enforce NetworkPolicy (run preflight.sh)?"
    else ok "attacker CANNOT reach mlflow"; fi
    if reach deploy/fraud-api; then ok "fraud-api CAN still reach mlflow"
    else no "fraud-api CAN still reach mlflow"; hint "write security/lab/allow-mlflow-from-api.yaml: podSelector app=mlflow, ingress from app=fraud-api, port 8080"; fi
  fi
fi

echo
echo "Score: $pass/$TOTAL"
[ "$pass" -eq "$TOTAL" ]
