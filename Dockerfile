# ============================================
# Stage 1: Builder - Install dependencies
# ============================================
# This stage compiles and installs Python packages
# We use a separate stage to keep the final image small

FROM python:3.13-slim AS builder

# Set working directory inside container
WORKDIR /app

# Install system dependencies needed for Python packages
# - gcc, g++: Compile C extensions (psycopg2, etc.)
# - libpq-dev: PostgreSQL client library headers
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (Docker layer caching optimization)
# If requirements.txt doesn't change, this layer is reused
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir: Don't store pip cache (saves space)
# --user: Install to user directory (easier to copy later)
RUN pip install --no-cache-dir --user -r requirements.txt


# ============================================
# Stage 2: Runtime - Final lightweight image
# ============================================
# This is the actual image that runs in production
# It's smaller because it doesn't include build tools

FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install only runtime dependencies (not build tools)
# libpq5: PostgreSQL client library (runtime only)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
# This avoids reinstalling everything
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Update PATH to include user-installed packages
ENV PATH=/root/.local/bin:$PATH

# Create logs directory (your app writes to logs/app.log)
RUN mkdir -p logs

# Expose port 8000 (FastAPI default port)
# This is documentation - doesn't actually publish the port
EXPOSE 8000

# Health check - Docker will periodically check if container is healthy
# Every 30 seconds, try to access /health endpoint
# If it fails 3 times in a row, container is marked unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command to run when container starts
# --host 0.0.0.0: Listen on all network interfaces (required for Docker)
# --port 8000: Application port
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
