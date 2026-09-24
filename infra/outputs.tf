output "endpoint_url" {
  value       = module.cloud_run.url
  description = "HTTPS inference endpoint"
}

output "gcs_bucket" {
  value = module.storage.bucket_name
}

output "artifact_registry_url" {
  value = module.artifact_registry.repo_url
}