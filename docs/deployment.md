# Deployment Guide

> **Owner:** DevOps / Cloud Engineer

## Prerequisites

Before setting up the ATM Simulator, ensure the following tools are installed:

| Tool | Minimum Version | Purpose |
|---|---|---|
| **Docker** | 24.0+ | Container runtime for the application and database |
| **Docker Compose** | v2.20+ | Multi-container orchestration (included with Docker Desktop) |
| **Python** | 3.12+ | Required only for local development without Docker |
| **Git** | 2.x | Clone the repository |

For AWS cloud deployment (Phase 3), you also need:

| Tool | Minimum Version | Purpose |
|---|---|---|
| **Terraform** | 1.5+ | Infrastructure as Code for AWS provisioning |
| **AWS CLI** | 2.x | AWS resource management and ECS deployments |

Verify your installations:

```bash
docker --version
docker compose version
python3 --version
git --version
terraform --version   # for cloud deployment
aws --version         # for cloud deployment
```

## Quick Start with Docker

The fastest way to get the application running is with Docker Compose, which starts both the application and a PostgreSQL database.

```bash
# 1. Clone the repository
git clone <repo-url> && cd atm-simulator

# 2. Create environment file from template
cp .env.example .env

# 3. Build and start all services (app + PostgreSQL)
docker compose up --build

# 4. In a separate terminal, run database migrations
docker compose exec app alembic upgrade head

# 5. Seed the database with sample accounts
docker compose exec app python -m scripts.seed_db
```

The application will be available at `http://localhost:8000`. API docs are served at `http://localhost:8000/docs`.

To stop the services:

```bash
docker compose down          # stop containers, keep data
docker compose down -v       # stop containers and delete volumes (resets database)
```

## Local Development Without Docker

For local development, you can run the application directly using SQLite instead of PostgreSQL. This requires no external database setup.

```bash
# 1. Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# 2. Install the package with development dependencies
pip install -e ".[dev]"

# 3. Set environment variables for SQLite
export DATABASE_URL="sqlite+aiosqlite:///./atm.db"
export DATABASE_URL_SYNC="sqlite:///./atm.db"
export SECRET_KEY="local-dev-secret"
export PIN_PEPPER="local-dev-pepper"
export ENVIRONMENT="development"
export STATEMENT_OUTPUT_DIR="./statements"

# 4. Run database migrations
alembic upgrade head

# 5. Seed the database
python -m scripts.seed_db

# 6. Start the development server
uvicorn src.atm.main:app --reload --port 8000
```

### Running Tests Locally

```bash
# Run full test suite with coverage
pytest --cov=src/atm --cov-report=term-missing

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run only E2E tests
pytest tests/e2e/

# Run a specific test file
pytest tests/unit/services/test_auth_service.py -v
```

## Environment Variables

All configuration is managed through environment variables. Copy `.env.example` to `.env` and adjust as needed.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://atm_user:atm_pass@db:5432/atm_db` | Async database connection string used by the SQLAlchemy async engine (asyncpg driver) |
| `DATABASE_URL_SYNC` | `postgresql://atm_user:atm_pass@db:5432/atm_db` | Synchronous connection string used by Alembic migrations |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL for sessions, rate limiting, and Celery broker |
| `SECRET_KEY` | `change-me-in-production` | Key for session token signing. **Must** be changed in production. |
| `PIN_PEPPER` | `change-me-in-production` | Application-level pepper appended to PINs before bcrypt hashing. **Must** be changed in production. |
| `SESSION_TIMEOUT_SECONDS` | `120` | Seconds of inactivity before a session expires (2 minutes) |
| `MAX_FAILED_PIN_ATTEMPTS` | `3` | Consecutive failed PIN entries before account lockout |
| `LOCKOUT_DURATION_SECONDS` | `1800` | Duration in seconds that an account stays locked after max failed attempts (30 minutes) |
| `DAILY_WITHDRAWAL_LIMIT` | `50000` | Daily withdrawal limit per account in cents ($500.00) |
| `DAILY_TRANSFER_LIMIT` | `250000` | Daily transfer limit per account in cents ($2,500.00) |
| `STATEMENT_OUTPUT_DIR` | `/app/statements` | Directory where generated PDF statements are saved |
| `LOG_LEVEL` | `INFO` | Python log level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `ENVIRONMENT` | `development` | Application environment: `development`, `testing`, or `production`. Controls debug features, docs endpoints, and database echo. |

## Database Setup

### Migrations (Alembic)

The project uses Alembic for database schema migrations.

```bash
# Apply all pending migrations
docker compose exec app alembic upgrade head

# Generate a new migration after model changes
docker compose exec app alembic revision --autogenerate -m "description of change"

# Roll back the most recent migration
docker compose exec app alembic downgrade -1

# View current migration status
docker compose exec app alembic current
```

### Seed Data

The seed script creates test accounts for local development:

```bash
docker compose exec app python -m scripts.seed_db
```

This creates five accounts across three customers (Alice, Bob, Charlie) with predefined balances and PINs. See `CLAUDE.md` for the full seed data table.

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment.

### CI Workflow (`.github/workflows/ci.yml`)

Runs on every push to `main` and on every pull request targeting `main`.

| Job | What It Does |
|---|---|
| **lint** | Installs dependencies, then runs `ruff check .` (linting) and `ruff format --check .` (formatting verification). Catches style violations and import ordering issues. |
| **type-check** | Runs `mypy --strict src/` to enforce type annotations across the entire source tree. All public functions must have complete type hints. |
| **test** | Runs `pytest` with coverage against a SQLite test database (no PostgreSQL required in CI). Generates both terminal and XML coverage reports. The XML report is uploaded as a build artifact. |

A failing job blocks pull request merges.

### Deploy Workflow (`.github/workflows/deploy.yml`)

Triggered manually via `workflow_dispatch` with an environment selector (dev or production).

| Job | What It Does |
|---|---|
| **test** | Re-runs the full CI suite to ensure tests pass before deploying. |
| **build-and-push** | Builds the production Docker image and pushes it to Amazon ECR, tagged with the git SHA and `latest`. |
| **migrate** | Runs database migrations as a one-shot ECS Fargate task (`alembic upgrade head`). Waits for completion and checks the exit code. |
| **deploy** | Forces a new deployment of the ECS app service and waits for stability. |

### Required GitHub Secrets and Variables

| Name | Type | Description |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | Secret | IAM user access key for deployments |
| `AWS_SECRET_ACCESS_KEY` | Secret | IAM user secret key for deployments |
| `AWS_REGION` | Variable | AWS region (default: `us-east-1`) |
| `SUBNET_IDS` | Variable | Comma-separated subnet IDs for migration tasks |
| `SECURITY_GROUP_ID` | Variable | Security group ID for migration tasks |

### Coverage Reports

After each test run, the coverage report is uploaded as a GitHub Actions artifact named `coverage-report`. Download it from the workflow run summary to inspect line-by-line coverage.

## AWS Cloud Deployment

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          AWS VPC                                │
│                       10.0.0.0/16                               │
│                                                                 │
│  ┌────────────────────┐       ┌────────────────────┐           │
│  │  Public Subnet 1   │       │  Public Subnet 2   │           │
│  │    10.0.1.0/24     │       │    10.0.2.0/24     │           │
│  │                    │       │                    │           │
│  │  ┌──────────────┐  │       │                    │           │
│  │  │ ECS Fargate  │  │       │                    │           │
│  │  │ ┌──────────┐ │  │       │  ┌──────────────┐  │           │
│  │  │ │   App    │ │  │       │  │  RDS         │  │           │
│  │  │ │ :8000    │ │  │       │  │  PostgreSQL  │  │           │
│  │  │ ├──────────┤ │  │       │  │  :5432       │  │           │
│  │  │ │  Redis   │ │  │       │  └──────────────┘  │           │
│  │  │ │  :6379   │ │  │       │                    │           │
│  │  │ └──────────┘ │  │       │                    │           │
│  │  └──────────────┘  │       │                    │           │
│  └────────────────────┘       └────────────────────┘           │
│                                                                 │
│  Internet Gateway                                               │
└─────────────────────────────────────────────────────────────────┘
         │
    ┌────┴────┐
    │ Internet│
    └─────────┘

Supporting Services:
  - ECR: Docker image registry
  - Secrets Manager: DATABASE_URL, SECRET_KEY, PIN_PEPPER
  - CloudWatch: Application logs (structured JSON)
  - S3: PDF statement storage
```

### Cost Estimate (~$24/month)

| Service | Configuration | Monthly Cost |
|---------|--------------|-------------|
| ECS Fargate (app + Redis sidecar) | 0.25 vCPU / 512 MB, 24/7 | ~$7.50 |
| RDS PostgreSQL | db.t4g.micro, 20GB gp3, single-AZ | ~$13 (free tier: $0) |
| ECR | <1 GB stored | ~$0.10 |
| S3 (statements) | <1 GB stored | ~$0.03 |
| CloudWatch Logs | <5 GB/month | ~$2.50 |
| Secrets Manager | 4 secrets | ~$1.20 |
| **Total** | | **~$24/month** (~$11 with RDS free tier) |

**Cost-saving decisions:**
- Redis runs as a Fargate sidecar (not ElastiCache, saving ~$8.50/month)
- No ALB — Fargate task has a public IP with direct HTTP (saving ~$16/month)
- Worker service `desired_count=0` by default (saving ~$7.50/month at idle)
- No NAT Gateway — all resources in public subnets

### Infrastructure Setup with Terraform

All infrastructure is defined in `infra/terraform/` using modular HCL.

```
infra/terraform/
├── modules/
│   ├── networking/    # VPC, subnets, IGW, route tables
│   ├── security/      # Security groups (Fargate, RDS)
│   ├── ecr/           # Docker image repository
│   ├── rds/           # PostgreSQL database
│   ├── secrets/       # Secrets Manager
│   ├── ecs/           # Cluster, task definitions, services
│   ├── s3/            # Statement storage bucket
│   └── monitoring/    # CloudWatch log groups
└── environments/
    └── dev/           # Dev environment configuration
```

### Initial Deployment

```bash
# 1. Navigate to the environment directory
cd infra/terraform/environments/dev

# 2. Create your variables file
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values (db_password, secret_key, pin_pepper)

# 3. Initialize Terraform
terraform init

# 4. Review the plan
terraform plan

# 5. Apply (creates all AWS resources)
terraform apply

# 6. Note the outputs — you'll need these for deployment
terraform output
```

After `terraform apply`, you'll have:
- ECR repository URL (for pushing Docker images)
- RDS endpoint (database is ready)
- ECS cluster and services (waiting for a Docker image)

### First Docker Image Push

```bash
# Get ECR repository URL from Terraform output
ECR_URL=$(terraform output -raw ecr_repository_url)

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin "${ECR_URL%%/*}"

# Build and push the production image
docker build --target production -t "${ECR_URL}:latest" .
docker push "${ECR_URL}:latest"
```

### Running Migrations

Migrations run as a one-shot ECS Fargate task:

```bash
CLUSTER=$(terraform output -raw ecs_cluster_name)
SUBNETS=$(terraform output -raw subnet_ids)
SG=$(terraform output -raw fargate_security_group_id)
TASK_FAMILY=$(terraform output -raw migration_task_family)

aws ecs run-task \
  --cluster "${CLUSTER}" \
  --task-definition "${TASK_FAMILY}" \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[${SUBNETS}],securityGroups=[${SG}],assignPublicIp=ENABLED}"
```

### Seeding the Database

After the first migration, seed the database by running a one-off task:

```bash
aws ecs run-task \
  --cluster "${CLUSTER}" \
  --task-definition "${TASK_FAMILY}" \
  --launch-type FARGATE \
  --overrides '{"containerOverrides":[{"name":"migration","command":["python","-m","scripts.seed_db"]}]}' \
  --network-configuration "awsvpcConfiguration={subnets=[${SUBNETS}],securityGroups=[${SG}],assignPublicIp=ENABLED}"
```

### Deploying Updates

**Via GitHub Actions (recommended):**

1. Go to **Actions** > **Deploy** > **Run workflow**
2. Select the target environment (dev or production)
3. The workflow builds, migrates, and deploys automatically

**Manually:**

```bash
# Build and push new image
docker build --target production -t "${ECR_URL}:$(git rev-parse HEAD)" .
docker push "${ECR_URL}:$(git rev-parse HEAD)"

# Run migrations
aws ecs run-task --cluster "${CLUSTER}" --task-definition "${TASK_FAMILY}" \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[${SUBNETS}],securityGroups=[${SG}],assignPublicIp=ENABLED}"

# Force new deployment
aws ecs update-service --cluster "${CLUSTER}" --service "${SERVICE}" --force-new-deployment
```

### Smoke Testing

After deployment, run the smoke test script against the Fargate public IP:

```bash
# Find the task's public IP
TASK_ARN=$(aws ecs list-tasks --cluster "${CLUSTER}" --service-name "${SERVICE}" \
  --query 'taskArns[0]' --output text)
ENI_ID=$(aws ecs describe-tasks --cluster "${CLUSTER}" --tasks "${TASK_ARN}" \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)
PUBLIC_IP=$(aws ec2 describe-network-interfaces --network-interface-ids "${ENI_ID}" \
  --query 'NetworkInterfaces[0].Association.PublicIp' --output text)

# Run smoke tests
./scripts/smoke_test.sh "http://${PUBLIC_IP}:8000"
```

### Scaling the Worker

The Celery worker service is scaled to 0 by default. To enable async PDF generation:

```bash
aws ecs update-service \
  --cluster "${CLUSTER}" \
  --service "atm-simulator-dev-worker" \
  --desired-count 1
```

To scale back down:

```bash
aws ecs update-service \
  --cluster "${CLUSTER}" \
  --service "atm-simulator-dev-worker" \
  --desired-count 0
```

### Viewing Logs

```bash
# App logs
aws logs tail "/ecs/atm-simulator-dev/app" --follow

# Worker logs
aws logs tail "/ecs/atm-simulator-dev/worker" --follow

# Migration logs
aws logs tail "/ecs/atm-simulator-dev/migration" --follow
```

### Tearing Down

```bash
cd infra/terraform/environments/dev
terraform destroy
```

**Warning:** This deletes all resources including the RDS database. Back up data first.

### Troubleshooting

| Problem | Solution |
|---------|---------|
| ECS task fails to start | Check CloudWatch logs: `aws logs tail /ecs/atm-simulator-dev/app --since 30m` |
| Migration task fails | Check migration logs and verify DATABASE_URL_SYNC secret is correct |
| Health check failing | Ensure security group allows inbound on port 8000 |
| Cannot connect to RDS | Verify RDS security group allows inbound from Fargate SG on port 5432 |
| Redis connection refused | Redis sidecar should be at `localhost:6379` — check ECS task definition |
| "Secret not found" errors | Run `terraform apply` again to ensure secrets are created |
