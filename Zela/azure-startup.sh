#!/bin/bash

# Azure App Service startup script with extraction handling
echo "Azure Django App Startup Script"
echo "================================"

# Check if we need to extract the compressed output
if [ -f "/home/site/wwwroot/output.tar.gz" ]; then
    echo "Found compressed output, extracting..."
    cd /home/site/wwwroot/
    tar -xzf output.tar.gz
    echo "Extraction complete"
    
    # Remove the tar file to save space (optional)
    # rm -f output.tar.gz
fi

# Navigate to the Django project directory
if [ -d "/home/site/wwwroot/Zela" ]; then
    echo "Navigating to /home/site/wwwroot/Zela"
    cd /home/site/wwwroot/Zela
elif [ -d "/home/site/wwwroot" ] && [ -f "/home/site/wwwroot/manage.py" ]; then
    echo "Django project found at /home/site/wwwroot"
    cd /home/site/wwwroot
else
    echo "ERROR: Cannot find Django project"
    echo "Current directory contents:"
    ls -la /home/site/wwwroot/
    exit 1
fi

echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

# Set Python path
export PYTHONPATH="/home/site/wwwroot/Zela:${PYTHONPATH}"

# Run migrations (optional - can be commented out if handled elsewhere)
echo "Running database migrations..."
python manage.py migrate --noinput || echo "Migration failed, continuing..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Collectstatic failed, continuing..."

# Start Gunicorn
echo "Starting Gunicorn server..."
exec gunicorn --bind=0.0.0.0:8000 \
              --timeout 600 \
              --workers 2 \
              --threads 4 \
              --worker-class sync \
              --access-logfile '-' \
              --error-logfile '-' \
              --log-level info \
              Zela.wsgi:application