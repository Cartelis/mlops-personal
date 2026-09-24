variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type    = string
  default = "europe-west1"
}

variable "image" {
  type        = string
  description = "Container image for Cloud Run. Start with the placeholder, switch to the AR image after docker push."
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "service_name" {
  type    = string
  default = "mlops-fraud-api"
}

variable "min_instances" {
  type    = number
  default = 0
}

variable "max_instances" {
  type    = number
  default = 5
}