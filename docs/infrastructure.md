# Infrastructure - Week 4

## Architecture

Git repo → Terraform → GCS + Artifact Registry + Cloud Run

## Resources

| Resource | Terraform module | Purpose |
|----------|------------------|---------|
| GCS bucket | `modules/storage` | DVC, MLflow, backups |
| Artifact Registry | `modules/artifact_registry` | Docker images |
| Cloud Run | `modules/cloud_run` | Inference API |
| Service Account | `modules/iam` | Least-privilege runtime |

## Deploy

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform apply
```

## Teardown (mandatory after lab)

```bash
cd infra && terraform destroy
```