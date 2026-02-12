resource "aws_secretsmanager_secret" "database_url" {
  name                    = "${var.project_name}/${var.environment}/database-url"
  recovery_window_in_days = var.recovery_window_in_days

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = var.database_url
}

resource "aws_secretsmanager_secret" "database_url_sync" {
  name                    = "${var.project_name}/${var.environment}/database-url-sync"
  recovery_window_in_days = var.recovery_window_in_days

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "database_url_sync" {
  secret_id     = aws_secretsmanager_secret.database_url_sync.id
  secret_string = var.database_url_sync
}

resource "aws_secretsmanager_secret" "secret_key" {
  name                    = "${var.project_name}/${var.environment}/secret-key"
  recovery_window_in_days = var.recovery_window_in_days

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "secret_key" {
  secret_id     = aws_secretsmanager_secret.secret_key.id
  secret_string = var.secret_key
}

resource "aws_secretsmanager_secret" "pin_pepper" {
  name                    = "${var.project_name}/${var.environment}/pin-pepper"
  recovery_window_in_days = var.recovery_window_in_days

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "pin_pepper" {
  secret_id     = aws_secretsmanager_secret.pin_pepper.id
  secret_string = var.pin_pepper
}
