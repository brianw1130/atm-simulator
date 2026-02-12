# ECS Task Execution Role — used by ECS agent to pull images, fetch secrets, write logs
data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "task_execution" {
  name               = "${var.project_name}-${var.environment}-task-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_iam_role_policy_attachment" "task_execution_base" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "secrets_access" {
  statement {
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [
      var.database_url_secret_arn,
      var.database_url_sync_secret_arn,
      var.secret_key_secret_arn,
      var.pin_pepper_secret_arn,
    ]
  }
}

resource "aws_iam_role_policy" "secrets_access" {
  name   = "${var.project_name}-${var.environment}-secrets-access"
  role   = aws_iam_role.task_execution.id
  policy = data.aws_iam_policy_document.secrets_access.json
}

# ECS Task Role — used by the application container itself
resource "aws_iam_role" "task" {
  name               = "${var.project_name}-${var.environment}-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}
