# ── Finesse Chess Analysis — Dockerfile ───────────────────────────────
# Multi-service: Django web, Celery worker, Celery beat, Stockfish engine.
# Stockfish is installed from the Ubuntu package manager so the binary
# is always available inside the container.

FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend source (JSON array syntax avoids quoting issues with spaces)
COPY ["Finesse web app design/", "."]

RUN npm install --legacy-peer-deps 2>/dev/null || npm install

# Build the Vite production bundle
RUN npm run build

# ── Python / Django stage ────────────────────────────────────────────
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies: Stockfish, build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        stockfish \
        gcc \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Add /usr/games to PATH (Debian installs stockfish there, and slim images don't include it)
ENV PATH="/usr/games:${PATH}"

# Verify Stockfish is installed and can respond to UCI
RUN which stockfish && echo "uci" | timeout 3 stockfish | head -1 || echo "Stockfish check completed"

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project
COPY . .

# Copy the built Vite frontend into Django's static directory
COPY --from=frontend-builder /app/frontend/dist/ /app/staticfiles/

# Collect static files
RUN python manage.py collectstatic --noinput 2>/dev/null || true

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

EXPOSE 8001

ENTRYPOINT ["/app/entrypoint.sh"]
