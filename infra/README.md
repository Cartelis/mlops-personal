# GCP infrastructure (Week 4)

Terraform for the week-4 lab: a GCS bucket, Artifact Registry, a runtime service account, and Cloud Run. `main.tf` wires only those four modules.

`modules/gke_spot` is not applied. It is an optional spot node pool for a cluster that already exists, and it needs the Kubernetes API. Leave it unused for the main lab.

## Prerequisites

- A GCP project with billing (course credits)
- `gcloud auth login` and `gcloud auth application-default login`
- Terraform >= 1.5
- Docker, to build the week-3 CPU image

## 1. Enable APIs

From `tutorial/fraud-detection`:

```bash
bash scripts/enable_gcp_apis.sh <gcp-project-id>
```

## 2. First apply (placeholder image)

Cloud Run rejects a service whose image is not already in a registry. The example variables keep the public `hello` image so the first apply can create the registry and the service together.

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Set project_id. Leave image on us-docker.pkg.dev/cloudrun/container/hello.

terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

`terraform.tfvars`, `.terraform/` and `*.tfstate` are listed in `infra/.gitignore`. Do not commit them.

## 3. Push the week-3 CPU image and switch the service

Cloud Run runs `linux/amd64`. On Apple Silicon a plain `docker build` produces `arm64`, and the new revision fails with `exec format error`.

```bash
# From tutorial/fraud-detection, the parent of infra/
docker build --platform linux/amd64 -f docker/Dockerfile.cpu -t mlops-cpu:v1.2.0 .

cd infra
export REGION=europe-west1
export AR_URL=$(terraform output -raw artifact_registry_url)
gcloud auth configure-docker "${REGION}-docker.pkg.dev"
docker tag mlops-cpu:v1.2.0 "${AR_URL}/mlops-cpu:v1.2.0"
docker push "${AR_URL}/mlops-cpu:v1.2.0"
```

In `terraform.tfvars`, set `image` to the pushed name (`${AR_URL}/mlops-cpu:v1.2.0`). Then:

```bash
terraform apply -auto-approve
curl -s "$(terraform output -raw endpoint_url)/health"
curl -s -X POST "$(terraform output -raw endpoint_url)/predict" \
  -H "Content-Type: application/json" \
  -d '{"f0":0.1,"f1":-0.2,"f2":0.3,"f3":0.0,"f4":0.1,"f5":0.2,"f6":0.0,"f7":0.1,"f8":0.2,"f9":0.0}'
```

`/predict` answers only after the revision uses the fraud CPU image. The placeholder `hello` image has its own pages, not this API.

## 4. Teardown (required after the lab)

```bash
cd infra
terraform destroy
```

The lab bucket has `force_destroy` set, so destroy can delete its objects. In the Cloud console, confirm that the Cloud Run service, the Artifact Registry repository and the bucket are gone. Credits keep being charged until those resources are deleted.

## If apply or curl fails

| Symptom | What to do |
|---|---|
| `API not enabled` | Run `scripts/enable_gcp_apis.sh` again |
| `Image not found` | Keep the `hello` image for the first apply. Push, change `image`, apply again |
| Revision failed, `exec format error` | Rebuild with `--platform linux/amd64` and push that image |
| `allUsers` blocked by organization policy | Grant your user `roles/run.invoker` on the service and call it with `curl -H "Authorization: Bearer $(gcloud auth print-identity-token)"` |
| `403` on `docker push` | `gcloud auth configure-docker ${REGION}-docker.pkg.dev` |
| Bucket name taken | The bucket is `<project_id>-mlops-data` and the name is global |
