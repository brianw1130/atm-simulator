FROM python:3.12-slim AS base

# Prevent Python from writing bytecode and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ── Dependencies stage ──────────────────────────────────────────────
FROM base AS dependencies

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# ── Production stage ────────────────────────────────────────────────
FROM base AS production

COPY pyproject.toml .
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
COPY scripts/ scripts/

RUN pip install --no-cache-dir .

# Create non-root user
RUN useradd --create-home appuser && \
    mkdir -p /app/statements && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.atm.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ── Development stage ───────────────────────────────────────────────
FROM dependencies AS development

COPY . .

# Create non-root user
RUN useradd --create-home appuser && \
    mkdir -p /app/statements && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.atm.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
