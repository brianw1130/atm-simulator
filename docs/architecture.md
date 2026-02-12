# Architecture

> **Owner:** Software Architect

## Overview

The ATM Simulator follows a layered architecture separating concerns across API routing,
business logic, data access, and presentation.

```
┌─────────────────────────────────────────────────┐
│  Presentation Layer                             │
│  ┌──────────────┐  ┌────────────────────────┐  │
│  │ Textual UI   │  │ FastAPI (REST API)      │  │
│  └──────┬───────┘  └───────────┬────────────┘  │
│─────────┼──────────────────────┼────────────────│
│  Business Logic Layer (services/)               │
│  ┌──────────────┐  ┌──────────┐  ┌──────────┐  │
│  │ auth_service  │  │ txn_svc  │  │ stmt_svc │  │
│  └──────┬───────┘  └────┬─────┘  └────┬─────┘  │
│─────────┼───────────────┼─────────────┼─────────│
│  Data Access Layer (models/ + db/)              │
│  ┌──────────────┐  ┌──────────────────────┐    │
│  │ SQLAlchemy   │  │ Alembic Migrations   │    │
│  └──────┬───────┘  └──────────────────────┘    │
│─────────┼───────────────────────────────────────│
│  ┌──────┴───────┐                               │
│  │ PostgreSQL   │                               │
│  └──────────────┘                               │
└─────────────────────────────────────────────────┘
```

## Technology Decisions

<!-- TODO: Architect to fill in ADRs (Architecture Decision Records) -->

## Data Model

<!-- TODO: Architect to provide complete ERD and entity descriptions -->

## API Design

<!-- TODO: Architect to define API contracts (auto-generated from FastAPI/OpenAPI) -->
