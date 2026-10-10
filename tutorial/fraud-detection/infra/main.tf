module "iam" {
  source     = "./modules/iam"
  project_id = var.project_id
}

module "storage" {
  source     = "./modules/storage"
  project_id = var.project_id
  region     = var.region
}

module "artifact_registry" {
  source     = "./modules/artifact_registry"
  project_id = var.project_id
  region     = var.region
}

module "cloud_run" {
  source                = "./modules/cloud_run"
  project_id            = var.project_id
  region                = var.region
  service_name          = var.service_name
  image                 = var.image
  service_account_email = module.iam.email
  min_instances         = var.min_instances
  max_instances         = var.max_instances
  depends_on            = [module.artifact_registry, module.iam]
}