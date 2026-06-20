# ── PriceCart — Railway Deployment (multi-stage build) ───────────────────────
# Stage 1: Build the React frontend with Node.js
# Stage 2: Python/Playwright runtime with the built frontend baked in
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Frontend Build ───────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies (cached unless package.json changes)
COPY frontend/package*.json ./
RUN npm ci

# Copy source and build
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python/Playwright Runtime ───────────────────────────────────────
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Install Python packages
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium matching the installed playwright package version
RUN python -m playwright install chromium

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend from Stage 1 into backend/static/
# FastAPI serves static files from backend/static/
COPY --from=frontend-builder /app/frontend/dist ./backend/static/

WORKDIR /app/backend

EXPOSE 8000

# Railway injects $PORT automatically
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
