#!/bin/sh

# Azure App Service startup script for Django - sh compatible
echo "Starting Django application on Azure..."
echo "================================"

# Function to find and navigate to Django project
find_django_project() {
    # Check if we're running from Oryx extracted directory
    if [ -d "/tmp/8ddfae"* ]; then
        echo "Found Oryx extracted directory"
        cd /tmp/8ddfae* || exit 1
        
        # Activate virtual environment using . instead of source
        if [ -f "antenv/bin/activate" ]; then
            echo "Activating virtual environment..."
            . antenv/bin/activate
        fi
        
        # Navigate to Django project
        if [ -d "Zela" ]; then
            cd Zela || exit 1
        fi
    # Check standard Azure deployment path
    elif [ -d "/home/site/wwwroot" ]; then
        cd /home/site/wwwroot || exit 1
        
        # Check if we need to extract the output
        if [ -f "output.tar.gz" ]; then
            echo "Extracting compressed output..."
            tar -xzf output.tar.gz
        fi
        
        # Look for virtual environment
        if [ -f "venv/bin/activate" ]; then
            echo "Activating virtual environment..."
            . venv/bin/activate
        elif [ -f "antenv/bin/activate" ]; then
            echo "Activating virtual environment..."
            . antenv/bin/activate
        fi
        
        # Navigate to Django project directory
        if [ -d "Zela" ]; then
            cd Zela || exit 1
        elif [ -f "manage.py" ]; then
            echo "Already in Django project root"
        else
            echo "ERROR: Cannot find Django project"
            ls -la
            exit 1
        fi
    else
        echo "ERROR: Cannot find deployment directory"
        exit 1
    fi
}

# Main execution
echo "Locating Django project..."
find_django_project

echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

# Verify we can find manage.py
if [ ! -f "manage.py" ]; then
    echo "ERROR: manage.py not found in $(pwd)"
    echo "Looking for manage.py in parent directories..."
    find .. -name "manage.py" -type f 2>/dev/null | head -5
    exit 1
fi

# Set environment variables
export PYTHONPATH="${PWD}:${PYTHONPATH}"
export DJANGO_SETTINGS_MODULE="Zela.settings.production"

# Show Python and pip versions for debugging
echo "Python version:"
python --version
echo "Pip packages location:"
pip show django | grep Location || echo "Django not found in pip"

# Run migrations (allow failure but log it)
echo "Running database migrations..."
python manage.py migrate --noinput 2>&1 || echo "WARNING: Migration failed, continuing..."

# Collect static files (allow failure but log it)
echo "Collecting static files..."
python manage.py collectstatic --noinput 2>&1 || echo "WARNING: Collectstatic failed, continuing..."

# Start Gunicorn with explicit module path
echo "Starting Gunicorn server..."
echo "Using WSGI application: Zela.wsgi:application"

# Use exec to replace the shell process with gunicorn
exec gunicorn \
    --bind=0.0.0.0:8000 \
    --timeout=600 \
    --workers=2 \
    --threads=4 \
    --worker-class=sync \
    --access-logfile='-' \
    --error-logfile='-' \
    --log-level=info \
    --capture-output \
    --enable-stdio-inheritance \
    Zela.wsgi:application