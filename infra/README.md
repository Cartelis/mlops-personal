# GCP infrastructure (Week 4)

Terraform modules for GCS, Artifact Registry, IAM, and Cloud Run.

## Prerequisites

- GCP project with billing enabled
- `gcloud auth application-default login`
- Terraform >= 1.5

## Deploy

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit project_id

terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Push week-3 image to Artifact Registry
export AR_URL=$(terraform output -raw artifact_registry_url)
docker tag ghcr.io/<org>/mlops-cpu:v1.2.0 ${AR_URL}/mlops-cpu:v1.2.0
gcloud auth configure-docker $(echo $AR_URL | cut -d/ -f1)
docker push ${AR_URL}/mlops-cpu:v1.2.0
terraform apply -auto-approve

curl $(terraform output -raw endpoint_url)/health
```

## Teardown (required after lab)

```bash
terraform destroy
```