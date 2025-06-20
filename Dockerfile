# Build stage
FROM python:3.13-alpine as builder

WORKDIR /app

# Install system dependencies for building
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    g++ \
    libffi-dev \
    openssl-dev

# Install uv for faster dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.13-alpine

WORKDIR /app

# Install only runtime system dependencies
RUN apk add --no-cache \
    curl \
    tzdata

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create non-root user (Alpine syntax)
RUN addgroup -g 1000 appuser && adduser -D -u 1000 -G appuser appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application
CMD ["python", "app.py"]