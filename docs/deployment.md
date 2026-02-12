# Deployment Guide

> **Owner:** DevOps / Cloud Engineer

## Local Development (Docker)

```bash
cp .env.example .env
docker compose up --build
docker compose exec app alembic upgrade head
docker compose exec app python -m scripts.seed_db
```

## CI/CD Pipeline

<!-- TODO: Document GitHub Actions workflow -->

## Cloud Deployment (Phase 3)

<!-- TODO: Document AWS deployment (ECS/App Runner + RDS + S3) -->
