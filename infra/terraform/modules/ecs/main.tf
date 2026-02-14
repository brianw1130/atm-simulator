# ── ECS Cluster ──────────────────────────────────────────────────────

resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}"

  setting {
    name  = "containerInsights"
    value = var.container_insights ? "enabled" : "disabled"
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# ── Shared environment & secrets definitions ─────────────────────────

locals {
  app_image = "${var.ecr_repository_url}:${var.image_tag}"

  common_env = [
    { name = "REDIS_URL", value = "redis://localhost:6379/0" },
    { name = "SESSION_TIMEOUT_SECONDS", value = tostring(var.session_timeout_seconds) },
    { name = "MAX_FAILED_PIN_ATTEMPTS", value = tostring(var.max_failed_pin_attempts) },
    { name = "LOCKOUT_DURATION_SECONDS", value = tostring(var.lockout_duration_seconds) },
    { name = "DAILY_WITHDRAWAL_LIMIT", value = tostring(var.daily_withdrawal_limit) },
    { name = "DAILY_TRANSFER_LIMIT", value = tostring(var.daily_transfer_limit) },
    { name = "STATEMENT_OUTPUT_DIR", value = "/app/statements" },
    { name = "LOG_LEVEL", value = var.log_level },
    { name = "ENVIRONMENT", value = "production" },
    { name = "S3_BUCKET_NAME", value = var.s3_statements_bucket_name },
    { name = "AWS_REGION", value = var.aws_region },
    { name = "SEED_SNAPSHOT_S3_KEY", value = var.seed_snapshot_s3_key },
  ]

  common_secrets = [
    { name = "DATABASE_URL", valueFrom = var.database_url_secret_arn },
    { name = "SECRET_KEY", valueFrom = var.secret_key_secret_arn },
    { name = "PIN_PEPPER", valueFrom = var.pin_pepper_secret_arn },
  ]

  redis_sidecar = {
    name      = "redis"
    image     = "redis:7-alpine"
    essential = true
    portMappings = [
      { containerPort = 6379, protocol = "tcp" }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = var.app_log_group
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "redis"
      }
    }
  }
}

# ── App Task Definition (app + Redis sidecar) ───────────────────────

resource "aws_ecs_task_definition" "app" {
  family                   = "${var.project_name}-${var.environment}-app"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.app_cpu
  memory                   = var.app_memory
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "app"
      image     = local.app_image
      essential = true
      portMappings = [
        { containerPort = 8000, protocol = "tcp" }
      ]
      environment = local.common_env
      secrets     = local.common_secrets
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.app_log_group
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "app"
        }
      }
      dependsOn = [
        { containerName = "redis", condition = "START" }
      ]
    },
    local.redis_sidecar,
  ])

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# ── Worker Task Definition (celery + Redis sidecar) ─────────────────

resource "aws_ecs_task_definition" "worker" {
  family                   = "${var.project_name}-${var.environment}-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.app_cpu
  memory                   = var.app_memory
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name        = "worker"
      image       = local.app_image
      essential   = true
      command     = ["celery", "-A", "src.atm.worker", "worker", "--loglevel=info"]
      environment = local.common_env
      secrets     = local.common_secrets
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.worker_log_group
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "worker"
        }
      }
      dependsOn = [
        { containerName = "redis", condition = "START" }
      ]
    },
    local.redis_sidecar,
  ])

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# ── Migration Task Definition (one-shot, no Redis needed) ───────────

resource "aws_ecs_task_definition" "migration" {
  family                   = "${var.project_name}-${var.environment}-migration"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "migration"
      image     = local.app_image
      essential = true
      command   = ["alembic", "upgrade", "head"]
      environment = [
        { name = "ENVIRONMENT", value = "production" },
      ]
      secrets = [
        { name = "DATABASE_URL", valueFrom = var.database_url_secret_arn },
        { name = "DATABASE_URL_SYNC", valueFrom = var.database_url_sync_secret_arn },
        { name = "SECRET_KEY", valueFrom = var.secret_key_secret_arn },
        { name = "PIN_PEPPER", valueFrom = var.pin_pepper_secret_arn },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.migration_log_group
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "migration"
        }
      }
    },
  ])

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# ── App Service ──────────────────────────────────────────────────────

resource "aws_ecs_service" "app" {
  name            = "${var.project_name}-${var.environment}-app"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.app_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [var.security_group_id]
    assign_public_ip = true
  }

  deployment_minimum_healthy_percent = var.deployment_minimum_healthy_percent
  deployment_maximum_percent         = 200

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# ── Worker Service (desired_count=0 by default to save costs) ────────

resource "aws_ecs_service" "worker" {
  name            = "${var.project_name}-${var.environment}-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [var.security_group_id]
    assign_public_ip = true
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}
