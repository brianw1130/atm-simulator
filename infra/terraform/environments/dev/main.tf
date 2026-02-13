terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# ── Networking ────────────────────────────────────────────────────────

module "networking" {
  source = "../../modules/networking"

  project_name       = var.project_name
  environment        = var.environment
  availability_zones = var.availability_zones
}

# ── Security Groups ──────────────────────────────────────────────────

module "security" {
  source = "../../modules/security"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.networking.vpc_id
  vpc_cidr     = module.networking.vpc_cidr
}

# ── ECR Repository ───────────────────────────────────────────────────

module "ecr" {
  source = "../../modules/ecr"

  project_name = var.project_name
  environment  = var.environment
}

# ── RDS PostgreSQL ───────────────────────────────────────────────────

module "rds" {
  source = "../../modules/rds"

  project_name      = var.project_name
  environment       = var.environment
  subnet_ids        = module.networking.public_subnet_ids
  security_group_id = module.security.rds_sg_id
  db_password       = var.db_password

  # Dev-specific settings
  deletion_protection = false
  skip_final_snapshot = true
  publicly_accessible = true
}

# ── Secrets Manager ──────────────────────────────────────────────────

locals {
  # Construct database URLs from RDS outputs
  database_url      = "postgresql+asyncpg://atm_user:${var.db_password}@${module.rds.endpoint}/atm_db"
  database_url_sync = "postgresql://atm_user:${var.db_password}@${module.rds.endpoint}/atm_db"
}

module "secrets" {
  source = "../../modules/secrets"

  project_name      = var.project_name
  environment       = var.environment
  database_url      = local.database_url
  database_url_sync = local.database_url_sync
  secret_key        = var.secret_key
  pin_pepper        = var.pin_pepper

  # Dev: immediate deletion (no recovery window)
  recovery_window_in_days = 0
}

# ── Monitoring (CloudWatch) ──────────────────────────────────────────

module "monitoring" {
  source = "../../modules/monitoring"

  project_name       = var.project_name
  environment        = var.environment
  log_retention_days = 14 # Shorter retention for dev
}

# ── S3 (Statement Storage) ──────────────────────────────────────────

module "s3" {
  source = "../../modules/s3"

  project_name = var.project_name
  environment  = var.environment
}

# ── ECS (Fargate) ────────────────────────────────────────────────────

module "ecs" {
  source = "../../modules/ecs"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region

  # Networking
  subnet_ids        = module.networking.public_subnet_ids
  security_group_id = module.security.fargate_sg_id

  # Container image
  ecr_repository_url = module.ecr.repository_url
  image_tag          = var.image_tag

  # Secrets
  database_url_secret_arn      = module.secrets.database_url_arn
  database_url_sync_secret_arn = module.secrets.database_url_sync_arn
  secret_key_secret_arn        = module.secrets.secret_key_arn
  pin_pepper_secret_arn        = module.secrets.pin_pepper_arn

  # Logging
  app_log_group       = module.monitoring.app_log_group_name
  worker_log_group    = module.monitoring.worker_log_group_name
  migration_log_group = module.monitoring.migration_log_group_name

  # S3
  s3_statements_bucket_arn = module.s3.bucket_arn

  # Sizing (minimal for dev)
  app_cpu              = 256 # 0.25 vCPU
  app_memory           = 512 # 512 MB
  app_desired_count    = 1
  worker_desired_count = 0 # Disabled to save costs; scale to 1 when needed

  # Allow downtime during dev deployments
  deployment_minimum_healthy_percent = 0
}

# ── Outputs ──────────────────────────────────────────────────────────

output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "ecr_repository_url" {
  description = "ECR repository URL for Docker pushes"
  value       = module.ecr.repository_url
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = module.rds.endpoint
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "ecs_app_service_name" {
  description = "ECS app service name"
  value       = module.ecs.app_service_name
}

output "migration_task_family" {
  description = "Migration task definition family (for aws ecs run-task)"
  value       = module.ecs.migration_task_family
}

output "s3_statements_bucket" {
  description = "S3 bucket for PDF statements"
  value       = module.s3.bucket_name
}

output "subnet_ids" {
  description = "Public subnet IDs (for migration task network config)"
  value       = join(",", module.networking.public_subnet_ids)
}

output "fargate_security_group_id" {
  description = "Fargate security group ID (for migration task network config)"
  value       = module.security.fargate_sg_id
}
