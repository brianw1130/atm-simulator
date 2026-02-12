variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
}

variable "database_url" {
  description = "Async database connection URL"
  type        = string
  sensitive   = true
}

variable "database_url_sync" {
  description = "Sync database connection URL (for Alembic)"
  type        = string
  sensitive   = true
}

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

variable "recovery_window_in_days" {
  description = "Number of days before permanent secret deletion (0 for immediate)"
  type        = number
  default     = 0
}
