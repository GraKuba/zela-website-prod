#!/bin/bash

# Azure App Service startup script for Django
echo "Starting Django application..."

# Set the working directory
export WORKDIR="/home/site/wwwroot"

# Check if we're in the right directory structure
if [ -d "$WORKDIR/Zela" ]; then
    echo "Found Zela directory in $WORKDIR"
    cd "$WORKDIR/Zela"
elif [ -f "$WORKDIR/manage.py" ]; then
    echo "Already in Django project root"
    cd "$WORKDIR"
else
    echo "ERROR: Cannot find Django project structure"
    ls -la "$WORKDIR"
    exit 1
fi

# Show current directory for debugging
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

# Add current directory to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput || echo "Migration failed, continuing..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Collectstatic failed, continuing..."

# Start Gunicorn from the Django project directory
echo "Starting Gunicorn server from $(pwd)..."
gunicorn --bind=0.0.0.0:8000 \
         --timeout 600 \
         --workers=2 \
         --access-logfile '-' \
         --error-logfile '-' \
         --chdir "$(pwd)" \
         Zela.wsgi:application