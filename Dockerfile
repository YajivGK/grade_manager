# Multi-stage build for optimized Docker image
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy backend application code
COPY backend/ ./backend/

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy and make entrypoint script executable
COPY docker-entrypoint.py /entrypoint.py
RUN chmod +x /entrypoint.py

# Expose port (default 8050, can be overridden via PORT env var)
EXPOSE 8050

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8050

# Set working directory to backend
WORKDIR /app/backend

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health').read()" || exit 1

# Use entrypoint script
ENTRYPOINT ["python", "/entrypoint.py"]

