#!/usr/bin/env bash
# Week 13 preflight: step 0 of the lab, run at the start (takes ~1-3 min, needs internet).
#   bash security/preflight.sh
# Checks your tools and cluster, verifies that NetworkPolicy is really enforced,
# and pre-pulls every image the lab needs, so the lab itself works on bad Wi-Fi.
# It only creates/deletes a temporary namespace "preflight-sec13"; nothing else is changed.
set -u
K="${KUBECTL:-kubectl}"            # e.g. KUBECTL="minikube kubectl --" bash security/preflight.sh
GK_VERSION="v3.23.1"
IMAGES=(
  "nginxinc/nginx-unprivileged:1.27-alpine"   # vault stand-ins + M1 solution
  "busybox:1.36"                              # attacker pod
  "nginx:latest"                              # the intern's bad deploy (on purpose)
  "openpolicyagent/gatekeeper:${GK_VERSION}"  # Gatekeeper itself
)
NS="preflight-sec13"
fail=0
ok()   { printf '  \033[32mPASS\033[0m %s\n' "$*"; }
warn() { printf '  \033[33mWARN\033[0m %s\n' "$*"; }
bad()  { printf '  \033[31mFAIL\033[0m %s\n' "$*"; fail=1; }
cleanup() { $K delete ns "$NS" --wait=false >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "== 1. Tools"
command -v docker >/dev/null && ok "docker found" || warn "docker not found (fine if your cluster runs elsewhere)"
if $K version --client >/dev/null 2>&1; then ok "kubectl found"; else bad "kubectl not found"; exit 1; fi

echo "== 2. Cluster"
ctx="$($K config current-context 2>/dev/null)"
if ! $K get nodes >/dev/null 2>&1; then bad "cannot reach a cluster (context: ${ctx:-none}). Start it: minikube start   (only if step 4 later FAILs: minikube start -p sec13 --cni=calico --cpus 4 --memory 4g)"; exit 1; fi
ok "connected to context '$ctx'"
case "$ctx" in
  *sec13*|minikube*|kind-*|k3d-*|docker-desktop|rancher-desktop|orbstack) ;;
  *) warn "context '$ctx' does not look like a local cluster - make sure this is YOUR laptop cluster";;
esac

ver() { $K version -o json 2>/dev/null | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['$1']['minor'].rstrip('+'))" 2>/dev/null; }
cmin="$(ver clientVersion)"; smin="$(ver serverVersion)"
if [ -n "$cmin" ] && [ -n "$smin" ]; then
  d=$(( cmin > smin ? cmin - smin : smin - cmin ))
  if [ "$d" -le 1 ]; then ok "kubectl 1.$cmin vs cluster 1.$smin (skew ok)"
  else warn "kubectl 1.$cmin vs cluster 1.$smin - more than 1 minor apart; if commands misbehave use: KUBECTL=\"minikube kubectl --\""; fi
fi

mem_ki="$($K get nodes -o jsonpath='{.items[0].status.allocatable.memory}' 2>/dev/null | tr -d 'Ki')"
if [ -n "$mem_ki" ] && [ "$mem_ki" -eq "$mem_ki" ] 2>/dev/null; then
  mem_gb=$(( mem_ki / 1024 / 1024 ))
  # note: with minikube's docker driver this shows Docker's total, not the --memory limit
  [ "$mem_gb" -ge 3 ] && ok "node memory ~${mem_gb} GiB" || warn "node memory ~${mem_gb} GiB; 4 GiB recommended"
fi

echo "== 3. Pre-pulling images (first time can take a few minutes)"
$K create ns "$NS" >/dev/null 2>&1
i=0
for img in "${IMAGES[@]}"; do
  i=$((i+1))
  $K -n "$NS" run "pull-$i" --image="$img" --restart=Never --command -- sh -c "true" >/dev/null 2>&1
done
# A pod leaves phase Pending only after its image is pulled. Whether the container then
# succeeds or fails does not matter (the gatekeeper image has no shell and will fail - fine).
for n in $(seq 1 $i); do
  img="${IMAGES[$((n-1))]}"; res="timeout"
  for _ in $(seq 1 120); do      # up to ~4 min per image (first pull on slow Wi-Fi)
    phase="$($K -n "$NS" get pod "pull-$n" -o jsonpath='{.status.phase}' 2>/dev/null)"
    why="$($K -n "$NS" get pod "pull-$n" -o jsonpath='{.status.containerStatuses[0].state.waiting.reason}' 2>/dev/null)"
    case "$why" in ErrImagePull|ImagePullBackOff|InvalidImageName) res="pullfail"; break;; esac
    if [ -n "$phase" ] && [ "$phase" != "Pending" ]; then res="ok"; break; fi
    sleep 2
  done
  case "$res" in
    ok)       ok "image ready: $img";;
    pullfail) bad "could not pull $img (no internet? Docker Hub rate limit?)";;
    *)        warn "still pulling $img - wait a minute and re-run preflight";;
  esac
done

echo "== 4. Is NetworkPolicy actually enforced? (needs a CNI like Calico)"
$K -n "$NS" create deployment web --image=nginxinc/nginx-unprivileged:1.27-alpine --port=8080 >/dev/null 2>&1
$K -n "$NS" expose deployment web --port=80 --target-port=8080 >/dev/null 2>&1
$K -n "$NS" run client --image=busybox:1.36 --restart=Never --command -- sleep 600 >/dev/null 2>&1
$K -n "$NS" rollout status deployment/web --timeout=180s >/dev/null 2>&1
$K -n "$NS" wait --for=condition=Ready pod/client --timeout=180s >/dev/null 2>&1
# one long-lived client + exec: deterministic (no one-off pods racing with the policy)
probe() { $K -n "$NS" exec client -- wget -qO- -T 3 http://web >/dev/null 2>&1; }
if probe; then
  cat <<'EOF' | $K apply -f - >/dev/null
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: deny-all, namespace: preflight-sec13}
spec: {podSelector: {}, policyTypes: [Ingress]}
EOF
  enforced=0                     # policies can take a few seconds to apply: 3 tries
  for _ in 1 2 3; do sleep 5; if ! probe; then enforced=1; break; fi; done
  if [ "$enforced" -eq 0 ]; then
    bad "NetworkPolicy is NOT enforced by your cluster's network plugin. Recreate with Calico:"
    echo "        minikube start -p sec13 --cni=calico --cpus 4 --memory 4g   (a separate profile keeps your other cluster)"
  else ok "NetworkPolicy enforced (traffic blocked after deny-all)"; fi
else
  bad "test pod could not reach a test service even without policies - cluster networking/DNS problem"
fi

echo
if [ "$fail" -eq 0 ]; then echo "Preflight OK - you're ready for week 13."; else echo "Preflight found problems (see FAIL above). Fix them (see the hints) or ask the lecturer; if stuck, follow M1/M2 on the projector and start with M3."; fi
exit "$fail"
