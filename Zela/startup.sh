#!/bin/bash

# Azure App Service startup script for Django
echo "Starting Django application..."

# Navigate to the app directory
cd /home/site/wwwroot/Zela || cd /home/site/wwwroot

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files (if not already done during build)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn server..."
gunicorn --bind=0.0.0.0:8000 \
         --timeout 600 \
         --workers=2 \
         --access-logfile '-' \
         --error-logfile '-' \
         Zela.wsgi:application