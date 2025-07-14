#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit  # Exit on error

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies for Tailwind
if [ -f "theme/static_src/package.json" ]; then
    cd theme/static_src
    npm install
    cd ../..
fi

# Build Tailwind CSS
python manage.py tailwind build

# Collect static files
python manage.py collectstatic --noinput

# Run database migrations
python manage.py migrate

# Create superuser for deployment
python manage.py create_superuser 