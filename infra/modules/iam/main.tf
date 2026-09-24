resource "google_service_account" "cloud_run" {
  account_id   = "mlops-cloud-run"
  display_name = "MLOps Cloud Run runtime"
}

resource "google_project_iam_member" "storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}