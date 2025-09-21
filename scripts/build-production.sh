#!/usr/bin/env bash
# Build script for Azure production deployment

set -o errexit  # Exit on error

echo "🚀 Starting Zela production build process..."

# Change to Django project directory
cd Zela

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies for Tailwind
if [ -f "theme/static_src/package.json" ]; then
    echo "🎨 Installing Node.js dependencies for Tailwind..."
    cd theme/static_src
    npm install
    cd ../..
else
    echo "⚠️  No package.json found for Tailwind, skipping Node.js dependencies"
fi

# Build Tailwind CSS for production
echo "🎨 Building Tailwind CSS for production..."
python manage.py tailwind build

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations (with extra safety checks)
echo "🗃️  Running database migrations..."
python manage.py migrate --check  # Check migrations first
python manage.py migrate

# Create default users for production (if needed)
echo "👤 Creating default users (if needed)..."
python manage.py create_default_users

# Run comprehensive health checks
echo "🔍 Running production health checks..."
python manage.py check --deploy
python manage.py check --tag security

# Validate production settings
echo "🔒 Validating production configuration..."
python -c "
import os
from django.conf import settings
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Zela.settings.production')
execute_from_command_line(['manage.py', 'check', '--deploy'])

# Check critical production settings
assert not settings.DEBUG, 'DEBUG must be False in production'
assert settings.SECRET_KEY != 'django-insecure-6pc)do(sz^6x7!lfykctp_a$$j&&ts1^lj()yxk@lxgsu_vwx5', 'SECRET_KEY must be changed in production'
assert settings.ALLOWED_HOSTS, 'ALLOWED_HOSTS must be configured'
assert settings.DATABASES['default']['NAME'], 'Database must be configured'

print('✅ Production configuration validated')
"

echo "✅ Production build completed successfully!"
