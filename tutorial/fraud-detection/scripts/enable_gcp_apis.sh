#!/usr/bin/env bash
# Enable required GCP APIs for week 4 Terraform lab.
set -euo pipefail

PROJECT_ID="${1:?Usage: ./enable_gcp_apis.sh <gcp-project-id>}"
gcloud config set project "$PROJECT_ID"

gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com

echo "GCP APIs enabled for project: $PROJECT_ID"