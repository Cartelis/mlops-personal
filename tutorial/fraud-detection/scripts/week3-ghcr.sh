#!/usr/bin/env bash
# Publish the local CPU/ONNX images after their scans pass.
# Run from tutorial/fraud-detection; authenticate interactively, never paste tokens.
set -eu
gh auth login --hostname github.com --git-protocol ssh --web \
  --scopes write:packages,read:packages
OWNER=$(gh api user --jq '.login | ascii_downcase')
gh auth token | docker login ghcr.io -u "$OWNER" --password-stdin
VERSION=v1.2.2-cpu
python3 scripts/week3.py scan-report --kinds cpu onnx --gate
docker tag mlops-cpu:local "ghcr.io/$OWNER/week3-cpu:$VERSION"
docker push "ghcr.io/$OWNER/week3-cpu:$VERSION"
docker tag mlops-onnx:local "ghcr.io/$OWNER/week3-onnx:$VERSION"
docker push "ghcr.io/$OWNER/week3-onnx:$VERSION"
