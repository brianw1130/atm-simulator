variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for ECS services"
  type        = list(string)
}

variable "security_group_id" {
  description = "Security group ID for Fargate tasks"
  type        = string
}

variable "ecr_repository_url" {
  description = "URL of the ECR repository"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

# Secret ARNs
variable "database_url_secret_arn" {
  description = "ARN of the DATABASE_URL secret"
  type        = string
}

variable "database_url_sync_secret_arn" {
  description = "ARN of the DATABASE_URL_SYNC secret"
  type        = string
}

variable "secret_key_secret_arn" {
  description = "ARN of the SECRET_KEY secret"
  type        = string
}

variable "pin_pepper_secret_arn" {
  description = "ARN of the PIN_PEPPER secret"
  type        = string
}

# Log groups
variable "app_log_group" {
  description = "CloudWatch log group for app"
  type        = string
}

variable "worker_log_group" {
  description = "CloudWatch log group for worker"
  type        = string
}

variable "migration_log_group" {
  description = "CloudWatch log group for migration"
  type        = string
}

# Task sizing
variable "app_cpu" {
  description = "CPU units for app task (1024 = 1 vCPU)"
  type        = number
  default     = 256
}

variable "app_memory" {
  description = "Memory in MB for app task"
  type        = number
  default     = 512
}

variable "app_desired_count" {
  description = "Desired count for app service"
  type        = number
  default     = 1
}

variable "worker_desired_count" {
  description = "Desired count for worker service (0 to save costs)"
  type        = number
  default     = 0
}

# Environment variables
variable "session_timeout_seconds" {
  description = "Session timeout in seconds"
  type        = number
  default     = 120
}

variable "max_failed_pin_attempts" {
  description = "Max failed PIN attempts before lockout"
  type        = number
  default     = 3
}

variable "lockout_duration_seconds" {
  description = "Account lockout duration in seconds"
  type        = number
  default     = 1800
}

variable "daily_withdrawal_limit" {
  description = "Daily withdrawal limit in cents"
  type        = number
  default     = 50000
}

variable "daily_transfer_limit" {
  description = "Daily transfer limit in cents"
  type        = number
  default     = 250000
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
}
