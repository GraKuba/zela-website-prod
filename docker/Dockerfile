# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=Zela.settings.production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for Tailwind
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY Zela/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY Zela/ .

# Install Node.js dependencies and build Tailwind
RUN if [ -f "theme/static_src/package.json" ]; then \
        cd theme/static_src && \
        npm install && \
        cd ../..; \
    fi

# Build Tailwind CSS
RUN python manage.py tailwind build

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "Zela.wsgi:application"] 