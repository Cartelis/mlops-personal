#!/usr/bin/env bash
# Week 13 reset: back to the start of the lab.
#   bash security/reset.sh          # deletes namespace "vault" + our constraints/templates (Gatekeeper stays)
#   bash security/reset.sh --all    # ...and uninstalls Gatekeeper too
# Your files (good-deployment.yaml, allow-*.yaml) are NOT touched.
set -u
K="${KUBECTL:-kubectl}"
DIR="$(cd "$(dirname "$0")" && pwd)"
echo "context: $($K config current-context)"
$K delete -f "$DIR/policies/constraints/" --ignore-not-found
$K delete -f "$DIR/policies/templates/" --ignore-not-found
$K delete ns vault --ignore-not-found
if [ "${1:-}" = "--all" ]; then
  $K delete -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.23.1/deploy/gatekeeper.yaml --ignore-not-found
fi
echo "Reset done. Start again with: kubectl apply -f security/lab/base/vault.yaml"
