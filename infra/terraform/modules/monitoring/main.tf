resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.project_name}-${var.environment}/app"
  retention_in_days = var.log_retention_days

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/${var.project_name}-${var.environment}/worker"
  retention_in_days = var.log_retention_days

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_cloudwatch_log_group" "migration" {
  name              = "/ecs/${var.project_name}-${var.environment}/migration"
  retention_in_days = var.log_retention_days

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}
