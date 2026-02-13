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

**Installing the AWS CLI (macOS):**

```bash
# Via Homebrew (recommended)
brew install awscli

# Verify installation
aws --version
```

If you don't use Homebrew, download the macOS `.pkg` installer from [https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

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
| `FRONTEND_ENABLED` | `true` | Set to `false` to disable React web UI serving (API-only mode). |

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

## Docker Multi-Stage Build

The `Dockerfile` uses a multi-stage build to produce an optimized production image that serves both the FastAPI backend and the React web UI from a single container.

### Build Stages

| Stage | Base Image | Purpose |
|---|---|---|
| `frontend-build` | `node:20-alpine` | Installs npm dependencies and runs `npm run build` to compile the React app into static assets (`frontend/dist/`). |
| `base` | `python:3.12-slim` | Installs system dependencies (libpq, gcc, curl). Shared by all Python stages. |
| `dependencies` | `base` | Installs Python dev dependencies. Used by the development stage. |
| `production` | `base` | Installs production Python packages, copies source code and compiled frontend assets. Runs as non-root `appuser`. |
| `development` | `dependencies` | Full source mount with hot reload (`--reload`). Used by `docker compose up`. |

### How Frontend Serving Works

In production, FastAPI serves the React SPA:
1. The `frontend-build` stage compiles React to `frontend/dist/` (HTML + JS + CSS).
2. The `production` stage copies `frontend/dist/` into the image.
3. `src/atm/main.py` mounts `/assets` as static files and serves `index.html` for all non-API routes.
4. The `FRONTEND_ENABLED` env var (default `true`) controls whether static file serving is active.

In development, a separate Vite dev server runs on port 5173 with hot module replacement, proxying API calls to the backend on port 8000.

### Building for Production

```bash
# Build targeting the production stage
docker build --target production -t atm-simulator:latest .

# Run the production container
docker run -p 8000:8000 --env-file .env atm-simulator:latest
```

The React UI will be accessible at `http://localhost:8000`.

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment.

### CI Workflow (`.github/workflows/ci.yml`)

Runs on every push to `main` and on every pull request targeting `main`.

| Job | What It Does |
|---|---|
| **lint** | Runs `ruff check .` (linting) and `ruff format --check .` (formatting). |
| **type-check** | Runs `mypy --strict src/` to enforce type annotations. |
| **test** | Runs `pytest` with coverage against a SQLite test database. Uploads XML coverage report as artifact. |
| **security** | Runs `pip-audit` (dependency CVEs) and `bandit -r src/` (Python SAST). |
| **security-frontend** | Runs `npm audit --audit-level=high` on frontend dependencies. |
| **security-docker** | Runs Trivy filesystem scan (dependency CVEs) and IaC scan (Terraform misconfigs). |
| **security-secrets** | Runs Gitleaks against full git history to detect leaked credentials. |
| **frontend-lint** | Runs ESLint (`--max-warnings=0`) and TypeScript type check (`tsc --noEmit`). |
| **frontend-test** | Runs Vitest with coverage thresholds. Uploads coverage report as artifact. |
| **frontend-build** | Runs `npm run build` and verifies `dist/index.html` exists. |
| **terraform** | Runs `terraform fmt -check`, `terraform init`, and `terraform validate`. |

### CodeQL Workflow (`.github/workflows/codeql.yml`)

Runs on every push to `main`, on every pull request, and weekly (Monday 06:00 UTC).

| Job | What It Does |
|---|---|
| **analyze (python)** | Deep SAST: SQL injection, insecure deserialization, taint tracking in Python source. |
| **analyze (javascript-typescript)** | Deep SAST: XSS, prototype pollution, injection flaws in React/TypeScript code. |

> **Note:** CodeQL is free for public repositories. For private repos, it requires GitHub Advanced Security.

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

Set these in your GitHub repository under **Settings > Secrets and variables > Actions**.

**Secrets** (set before first deployment):

| Name | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM user access key (see [IAM User Setup](#iam-user-setup)) |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |

**Variables** (set `AWS_REGION` now; the other two after `terraform apply`):

| Name | Description |
|---|---|
| `AWS_REGION` | AWS region, e.g. `us-east-1` |
| `SUBNET_IDS` | Comma-separated subnet IDs for migration tasks |
| `SECURITY_GROUP_ID` | Security group ID for migration tasks |

> **Why are `SUBNET_IDS` and `SECURITY_GROUP_ID` set after `terraform apply`?**
>
> These values are generated by AWS when Terraform creates the VPC infrastructure.
> They don't exist until the resources are provisioned. After `terraform apply`
> completes, run `terraform output` to get the values, then paste them into the
> GitHub variables. The deploy workflow needs them to launch the migration ECS task
> into the correct network. The full sequence is:
>
> 1. `terraform apply` — creates VPC, subnets, security groups, etc.
> 2. `terraform output` — displays the generated IDs
> 3. Copy `subnet_ids` → GitHub variable `SUBNET_IDS`
> 4. Copy `fargate_security_group_id` → GitHub variable `SECURITY_GROUP_ID`
> 5. Now the Deploy workflow can run successfully

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

> **TODO: Add HTTPS support.** The app currently serves plain HTTP on port 8000.
> For production use, add an Application Load Balancer (ALB) with an ACM
> certificate for TLS termination. This requires:
>
> 1. A registered domain name (Route 53 or external registrar)
> 2. An ACM certificate (free, but requires domain validation)
> 3. A new `alb` Terraform module (ALB, target group, HTTPS listener, HTTP→HTTPS redirect)
> 4. Update the Fargate security group to only accept traffic from the ALB
> 5. Estimated added cost: ~$16/month for the ALB

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

### IAM User Setup

Create a dedicated IAM user for Terraform and CI/CD deployments.

1. In the AWS Console, go to **IAM > Users > Create user**
2. Name: `atm-simulator-deploy`
3. On the **Set permissions** step, choose **Attach policies directly**
4. Click **Create policy**, switch to the **JSON** tab, and paste the policy below
5. Name it `atm-simulator-deploy-policy`, create it
6. Back on the user creation page, refresh the policy list, search for `atm-simulator-deploy-policy`, check it, and finish
7. Create an **Access Key** (CLI use case) — save the Access Key ID and Secret Access Key

<details>
<summary>IAM Policy JSON (click to expand)</summary>

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "VPCNetworking",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateVpc",
        "ec2:DeleteVpc",
        "ec2:DescribeVpcs",
        "ec2:ModifyVpcAttribute",
        "ec2:CreateSubnet",
        "ec2:DeleteSubnet",
        "ec2:DescribeSubnets",
        "ec2:CreateInternetGateway",
        "ec2:DeleteInternetGateway",
        "ec2:AttachInternetGateway",
        "ec2:DetachInternetGateway",
        "ec2:DescribeInternetGateways",
        "ec2:CreateRouteTable",
        "ec2:DeleteRouteTable",
        "ec2:DescribeRouteTables",
        "ec2:CreateRoute",
        "ec2:DeleteRoute",
        "ec2:AssociateRouteTable",
        "ec2:DisassociateRouteTable",
        "ec2:CreateSecurityGroup",
        "ec2:DeleteSecurityGroup",
        "ec2:DescribeSecurityGroups",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeVpcAttribute",
        "ec2:DescribeAccountAttributes",
        "ec2:DescribeAvailabilityZones",
        "ec2:CreateTags",
        "ec2:DeleteTags",
        "ec2:DescribeTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "RDS",
      "Effect": "Allow",
      "Action": [
        "rds:CreateDBInstance",
        "rds:DeleteDBInstance",
        "rds:DescribeDBInstances",
        "rds:ModifyDBInstance",
        "rds:CreateDBSubnetGroup",
        "rds:DeleteDBSubnetGroup",
        "rds:DescribeDBSubnetGroups",
        "rds:AddTagsToResource",
        "rds:RemoveTagsFromResource",
        "rds:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECR",
      "Effect": "Allow",
      "Action": [
        "ecr:CreateRepository",
        "ecr:DeleteRepository",
        "ecr:DescribeRepositories",
        "ecr:GetRepositoryPolicy",
        "ecr:SetRepositoryPolicy",
        "ecr:DeleteRepositoryPolicy",
        "ecr:PutLifecyclePolicy",
        "ecr:GetLifecyclePolicy",
        "ecr:DeleteLifecyclePolicy",
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:BatchGetImage",
        "ecr:CompleteLayerUpload",
        "ecr:GetDownloadUrlForLayer",
        "ecr:InitiateLayerUpload",
        "ecr:PutImage",
        "ecr:UploadLayerPart",
        "ecr:ListTagsForResource",
        "ecr:TagResource",
        "ecr:UntagResource",
        "ecr:PutImageScanningConfiguration",
        "ecr:DescribeImageScanFindings"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECS",
      "Effect": "Allow",
      "Action": [
        "ecs:CreateCluster",
        "ecs:DeleteCluster",
        "ecs:DescribeClusters",
        "ecs:UpdateClusterSettings",
        "ecs:RegisterTaskDefinition",
        "ecs:DeregisterTaskDefinition",
        "ecs:DescribeTaskDefinition",
        "ecs:ListTaskDefinitions",
        "ecs:CreateService",
        "ecs:DeleteService",
        "ecs:DescribeServices",
        "ecs:UpdateService",
        "ecs:RunTask",
        "ecs:StopTask",
        "ecs:DescribeTasks",
        "ecs:ListTasks",
        "ecs:TagResource",
        "ecs:UntagResource",
        "ecs:ListTagsForResource",
        "ecs:PutClusterCapacityProviders"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SecretsManager",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:CreateSecret",
        "secretsmanager:DeleteSecret",
        "secretsmanager:DescribeSecret",
        "secretsmanager:GetSecretValue",
        "secretsmanager:PutSecretValue",
        "secretsmanager:UpdateSecret",
        "secretsmanager:TagResource",
        "secretsmanager:UntagResource",
        "secretsmanager:GetResourcePolicy"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:GetBucketPolicy",
        "s3:PutBucketPolicy",
        "s3:DeleteBucketPolicy",
        "s3:GetBucketVersioning",
        "s3:PutBucketVersioning",
        "s3:GetEncryptionConfiguration",
        "s3:PutEncryptionConfiguration",
        "s3:GetLifecycleConfiguration",
        "s3:PutLifecycleConfiguration",
        "s3:GetBucketPublicAccessBlock",
        "s3:PutBucketPublicAccessBlock",
        "s3:GetBucketTagging",
        "s3:PutBucketTagging",
        "s3:GetBucketAcl",
        "s3:GetBucketCORS",
        "s3:GetBucketWebsite",
        "s3:GetBucketLogging",
        "s3:GetBucketObjectLockConfiguration",
        "s3:GetAccelerateConfiguration",
        "s3:GetReplicationConfiguration",
        "s3:GetBucketRequestPayment",
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents",
        "logs:FilterLogEvents",
        "logs:PutRetentionPolicy",
        "logs:DeleteRetentionPolicy",
        "logs:TagLogGroup",
        "logs:UntagLogGroup",
        "logs:ListTagsLogGroup",
        "logs:TagResource",
        "logs:UntagResource",
        "logs:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMRolesForECS",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:UpdateRole",
        "iam:TagRole",
        "iam:UntagRole",
        "iam:ListRoleTags",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:ListAttachedRolePolicies",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRolePolicy",
        "iam:ListRolePolicies",
        "iam:PassRole",
        "iam:ListInstanceProfilesForRole"
      ],
      "Resource": [
        "arn:aws:iam::*:role/atm-simulator-*"
      ]
    }
  ]
}
```

</details>

**What each permission block covers:**

| Sid | Terraform Resources |
|-----|-------------------|
| VPCNetworking | VPC, subnets, internet gateway, route tables, security groups |
| RDS | PostgreSQL database instance and DB subnet group |
| ECR | Container image registry, image push/pull, lifecycle policies |
| ECS | Cluster, task definitions, services, run-task for migrations |
| SecretsManager | 4 secrets (database URLs, secret key, PIN pepper) |
| S3 | Statement PDF storage bucket with versioning and encryption |
| CloudWatchLogs | 3 log groups (app, worker, migration) |
| IAMRolesForECS | 2 IAM roles for ECS tasks (scoped to `atm-simulator-*` names only) |

### Configure the AWS CLI

After creating the IAM user and access key, configure the CLI:

```bash
aws configure
```

This prompts for four values:

| Prompt | Value |
|--------|-------|
| AWS Access Key ID | The access key from IAM user creation |
| AWS Secret Access Key | The secret key from IAM user creation |
| Default region name | `us-east-1` (must match `terraform.tfvars`) |
| Default output format | Press Enter to accept the default (json) |

Verify it works:

```bash
aws sts get-caller-identity
```

You should see your IAM user ARN in the output.

### Initial Deployment

#### 1. Create `terraform.tfvars`

```bash
cd infra/terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

| Variable | How to Generate |
|----------|----------------|
| `db_password` | Choose a strong password (12+ chars, mixed case, numbers, symbols) |
| `secret_key` | Run: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `pin_pepper` | Run the same command again (use a **different** value than `secret_key`) |

Both `secret_key` and `pin_pepper` can be any string — the `token_urlsafe` command generates 32 bytes of cryptographically random data encoded as URL-safe text.

> **Important:** Once accounts are created, the `pin_pepper` value must never change.
> If it changes, all existing PIN hashes become invalid and no one can log in.

Make sure this file is not tracked by git:

```bash
# Should print the file path (meaning it IS ignored)
git check-ignore infra/terraform/environments/dev/terraform.tfvars
```

#### 2. Run Terraform

```bash
# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply (creates all AWS resources)
terraform apply

# Display the outputs — you'll need these for GitHub variables and deployments
terraform output
```

After `terraform apply`, you'll have:
- ECR repository URL (for pushing Docker images)
- RDS endpoint (database is ready)
- ECS cluster and services (waiting for a Docker image)

#### 3. Set GitHub Variables

Copy the values from `terraform output` into your GitHub repository variables (see [Required GitHub Secrets and Variables](#required-github-secrets-and-variables)):

- `subnet_ids` → GitHub variable `SUBNET_IDS`
- `fargate_security_group_id` → GitHub variable `SECURITY_GROUP_ID`

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
