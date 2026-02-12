variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "atm-simulator"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "availability_zones" {
  description = "Availability zones for subnets"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# ── Database ──────────────────────────────────────────────────────────

variable "db_password" {
  description = "Master password for the RDS PostgreSQL instance"
  type        = string
  sensitive   = true
}

# ── Secrets ───────────────────────────────────────────────────────────

variable "secret_key" {
  description = "Application secret key for session signing"
  type        = string
  sensitive   = true
}

variable "pin_pepper" {
  description = "Application-level pepper for PIN hashing"
  type        = string
  sensitive   = true
}

# ── ECS ───────────────────────────────────────────────────────────────

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}
