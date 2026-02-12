output "database_url_arn" {
  description = "ARN of the database URL secret"
  value       = aws_secretsmanager_secret.database_url.arn
}

output "database_url_sync_arn" {
  description = "ARN of the sync database URL secret"
  value       = aws_secretsmanager_secret.database_url_sync.arn
}

output "secret_key_arn" {
  description = "ARN of the secret key secret"
  value       = aws_secretsmanager_secret.secret_key.arn
}

output "pin_pepper_arn" {
  description = "ARN of the PIN pepper secret"
  value       = aws_secretsmanager_secret.pin_pepper.arn
}
