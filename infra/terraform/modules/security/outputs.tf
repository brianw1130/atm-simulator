output "fargate_sg_id" {
  description = "Security group ID for Fargate tasks"
  value       = aws_security_group.fargate.id
}

output "rds_sg_id" {
  description = "Security group ID for RDS"
  value       = aws_security_group.rds.id
}
