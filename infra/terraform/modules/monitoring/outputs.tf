output "app_log_group_name" {
  description = "CloudWatch log group name for app"
  value       = aws_cloudwatch_log_group.app.name
}

output "worker_log_group_name" {
  description = "CloudWatch log group name for worker"
  value       = aws_cloudwatch_log_group.worker.name
}

output "migration_log_group_name" {
  description = "CloudWatch log group name for migration"
  value       = aws_cloudwatch_log_group.migration.name
}

output "app_log_group_arn" {
  description = "CloudWatch log group ARN for app"
  value       = aws_cloudwatch_log_group.app.arn
}
