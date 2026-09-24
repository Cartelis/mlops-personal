variable "project_id" { type = string }
variable "region" { type = string }
variable "service_name" { type = string }
variable "image" { type = string }
variable "service_account_email" { type = string }

variable "min_instances" {
  type        = number
  description = "Cloud Run floor: 0 = scale-to-zero; 1 = one warm instance (no cold start)"
  default     = 0
}

variable "max_instances" {
  type        = number
  description = "Cloud Run ceiling: hard limit on concurrent instances"
  default     = 5
}
