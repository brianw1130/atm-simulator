output "cluster_id" {
  description = "ECS cluster ID"
  value       = aws_ecs_cluster.main.id
}

output "cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "app_service_name" {
  description = "App ECS service name"
  value       = aws_ecs_service.app.name
}

output "worker_service_name" {
  description = "Worker ECS service name"
  value       = aws_ecs_service.worker.name
}

output "app_task_definition_arn" {
  description = "App task definition ARN"
  value       = aws_ecs_task_definition.app.arn
}

output "migration_task_definition_arn" {
  description = "Migration task definition ARN"
  value       = aws_ecs_task_definition.migration.arn
}

output "migration_task_family" {
  description = "Migration task definition family name"
  value       = aws_ecs_task_definition.migration.family
}
