# Multi-stage build for optimized production image
# Stage 1: Build Tailwind CSS
FROM node:18-alpine AS tailwind-builder

WORKDIR /app

# Copy Tailwind configuration and source files
COPY Zela/theme/static_src/package*.json ./theme/static_src/
COPY Zela/theme/static_src/ ./theme/static_src/

# Install dependencies and build Tailwind CSS
WORKDIR /app/theme/static_src
RUN npm ci && npm run build

# Stage 2: Python application
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=Zela.settings.production \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r django && useradd -r -g django django

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY Zela/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY Zela/ .

# Copy built Tailwind CSS from previous stage (Tailwind outputs to ../static/css/dist/)
COPY --from=tailwind-builder /app/theme/static/css/dist ./theme/static/css/dist

# Create directories for static files and media
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R django:django /app

# Switch to non-root user
USER django

# Collect static files
RUN python manage.py collectstatic --noinput

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--threads", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "Zela.wsgi:application"]