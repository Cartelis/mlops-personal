# GKE spot (preemptible) node pool for cost-optimized inference workloads
variable "project_id" {
  type = string
}

variable "cluster_name" {
  type = string
}

variable "cluster_location" {
  type = string
}

variable "node_count" {
  type    = number
  default = 1
}

variable "machine_type" {
  type    = string
  default = "e2-medium"
}

resource "google_container_node_pool" "spot_inference" {
  name     = "spot-inference"
  project  = var.project_id
  location = var.cluster_location
  cluster  = var.cluster_name

  initial_node_count = var.node_count

  node_config {
    machine_type = var.machine_type
    spot         = true
    disk_size_gb = 30

    labels = {
      workload = "mlops-inference"
      cost-tier = "spot"
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]
  }

  autoscaling {
    min_node_count = 0
    max_node_count = 10
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}