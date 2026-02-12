#!/usr/bin/env bash
# Deploy helper for the ATM simulator AWS infrastructure.
#
# Usage:
#   ./scripts/deploy.sh <command> [options]
#
# Commands:
#   init      — Initialize Terraform and apply infrastructure
#   push      — Build and push Docker image to ECR
#   migrate   — Run database migrations via ECS task
#   deploy    — Force new ECS deployment
#   status    — Show current ECS service status
#   all       — Run push + migrate + deploy in sequence
#   destroy   — Tear down all infrastructure (requires confirmation)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TF_DIR="${PROJECT_ROOT}/infra/terraform/environments/dev"

red()   { printf "\033[31m%s\033[0m\n" "$1"; }
green() { printf "\033[32m%s\033[0m\n" "$1"; }
bold()  { printf "\033[1m%s\033[0m\n" "$1"; }

# ── Helpers ──────────────────────────────────────────────────────────

tf_output() {
  terraform -chdir="${TF_DIR}" output -raw "$1" 2>/dev/null
}

require_tf_init() {
  if [ ! -d "${TF_DIR}/.terraform" ]; then
    red "Terraform not initialized. Run: $0 init"
    exit 1
  fi
}

get_aws_region() {
  aws configure get region 2>/dev/null || echo "us-east-1"
}

# ── Commands ─────────────────────────────────────────────────────────

cmd_init() {
  bold "Initializing Terraform..."

  if [ ! -f "${TF_DIR}/terraform.tfvars" ]; then
    red "Missing terraform.tfvars. Create it from the example:"
    echo "  cd ${TF_DIR}"
    echo "  cp terraform.tfvars.example terraform.tfvars"
    echo "  # Edit terraform.tfvars with your values"
    exit 1
  fi

  terraform -chdir="${TF_DIR}" init
  bold "Planning infrastructure..."
  terraform -chdir="${TF_DIR}" plan

  echo ""
  read -rp "Apply this plan? (yes/no): " confirm
  if [ "${confirm}" = "yes" ]; then
    terraform -chdir="${TF_DIR}" apply -auto-approve
    echo ""
    green "Infrastructure provisioned. Key outputs:"
    echo "  ECR URL:  $(tf_output ecr_repository_url)"
    echo "  RDS:      $(tf_output rds_endpoint)"
    echo "  Cluster:  $(tf_output ecs_cluster_name)"
  else
    echo "Aborted."
  fi
}

cmd_push() {
  require_tf_init
  local region
  region=$(get_aws_region)
  local ecr_url
  ecr_url=$(tf_output ecr_repository_url)
  local registry
  registry="${ecr_url%%/*}"
  local tag="${1:-$(git -C "${PROJECT_ROOT}" rev-parse --short HEAD)}"

  bold "Building production Docker image..."
  docker build --target production -t "${ecr_url}:${tag}" -t "${ecr_url}:latest" "${PROJECT_ROOT}"

  bold "Logging in to ECR..."
  aws ecr get-login-password --region "${region}" | \
    docker login --username AWS --password-stdin "${registry}"

  bold "Pushing image (tag: ${tag})..."
  docker push "${ecr_url}:${tag}"
  docker push "${ecr_url}:latest"

  green "Image pushed: ${ecr_url}:${tag}"
}

cmd_migrate() {
  require_tf_init
  local cluster
  cluster=$(tf_output ecs_cluster_name)
  local task_family
  task_family=$(tf_output migration_task_family)
  local subnets
  subnets=$(tf_output subnet_ids)
  local sg
  sg=$(tf_output fargate_security_group_id)

  bold "Running migration task..."
  local task_arn
  task_arn=$(aws ecs run-task \
    --cluster "${cluster}" \
    --task-definition "${task_family}" \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[${subnets}],securityGroups=[${sg}],assignPublicIp=ENABLED}" \
    --query 'tasks[0].taskArn' \
    --output text)

  echo "Task ARN: ${task_arn}"
  bold "Waiting for migration to complete..."
  aws ecs wait tasks-stopped --cluster "${cluster}" --tasks "${task_arn}"

  local exit_code
  exit_code=$(aws ecs describe-tasks \
    --cluster "${cluster}" \
    --tasks "${task_arn}" \
    --query 'tasks[0].containers[0].exitCode' \
    --output text)

  if [ "${exit_code}" = "0" ]; then
    green "Migration completed successfully."
  else
    red "Migration failed with exit code: ${exit_code}"
    aws ecs describe-tasks \
      --cluster "${cluster}" \
      --tasks "${task_arn}" \
      --query 'tasks[0].containers[0].reason' \
      --output text
    exit 1
  fi
}

cmd_deploy() {
  require_tf_init
  local cluster
  cluster=$(tf_output ecs_cluster_name)
  local service
  service=$(tf_output ecs_app_service_name)

  bold "Forcing new deployment..."
  aws ecs update-service \
    --cluster "${cluster}" \
    --service "${service}" \
    --force-new-deployment \
    --query 'service.serviceName' \
    --output text

  bold "Waiting for service to stabilize..."
  aws ecs wait services-stable \
    --cluster "${cluster}" \
    --services "${service}"

  green "Deployment complete. Service is stable."
}

cmd_status() {
  require_tf_init
  local cluster
  cluster=$(tf_output ecs_cluster_name)
  local service
  service=$(tf_output ecs_app_service_name)

  bold "ECS Service Status"
  aws ecs describe-services \
    --cluster "${cluster}" \
    --services "${service}" \
    --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,TaskDef:taskDefinition}' \
    --output table

  # Get public IP
  local task_arn
  task_arn=$(aws ecs list-tasks --cluster "${cluster}" --service-name "${service}" \
    --query 'taskArns[0]' --output text 2>/dev/null || echo "")

  if [ -n "${task_arn}" ] && [ "${task_arn}" != "None" ]; then
    local eni_id
    eni_id=$(aws ecs describe-tasks --cluster "${cluster}" --tasks "${task_arn}" \
      --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
      --output text 2>/dev/null || echo "")
    if [ -n "${eni_id}" ]; then
      local public_ip
      public_ip=$(aws ec2 describe-network-interfaces --network-interface-ids "${eni_id}" \
        --query 'NetworkInterfaces[0].Association.PublicIp' --output text 2>/dev/null || echo "")
      if [ -n "${public_ip}" ] && [ "${public_ip}" != "None" ]; then
        echo ""
        bold "Public URL: http://${public_ip}:8000"
        echo "Run smoke tests: ./scripts/smoke_test.sh http://${public_ip}:8000"
      fi
    fi
  fi
}

cmd_all() {
  cmd_push "${1:-}"
  cmd_migrate
  cmd_deploy
}

cmd_destroy() {
  require_tf_init
  red "WARNING: This will destroy ALL infrastructure including the database."
  read -rp "Type 'destroy' to confirm: " confirm
  if [ "${confirm}" = "destroy" ]; then
    terraform -chdir="${TF_DIR}" destroy
  else
    echo "Aborted."
  fi
}

# ── Main ─────────────────────────────────────────────────────────────

usage() {
  echo "Usage: $0 <command> [options]"
  echo ""
  echo "Commands:"
  echo "  init      Initialize Terraform and provision infrastructure"
  echo "  push      Build and push Docker image to ECR"
  echo "  migrate   Run database migrations via ECS task"
  echo "  deploy    Force new ECS service deployment"
  echo "  status    Show ECS service status and public IP"
  echo "  all       Push + migrate + deploy in sequence"
  echo "  destroy   Tear down all infrastructure"
}

case "${1:-}" in
  init)    cmd_init ;;
  push)    cmd_push "${2:-}" ;;
  migrate) cmd_migrate ;;
  deploy)  cmd_deploy ;;
  status)  cmd_status ;;
  all)     cmd_all "${2:-}" ;;
  destroy) cmd_destroy ;;
  *)       usage; exit 1 ;;
esac
