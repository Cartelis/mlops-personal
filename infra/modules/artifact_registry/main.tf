resource "google_artifact_registry_repository" "mlops" {
  location      = var.region
  repository_id = "mlops"
  format        = "DOCKER"
  description   = "MLOps course container images"
}