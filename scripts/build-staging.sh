#!/usr/bin/env bash
# Build script for Render staging deployment

set -o errexit  # Exit on error

echo "🚀 Starting Zela staging build process..."

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

# Build Tailwind CSS
echo "🎨 Building Tailwind CSS..."
python manage.py tailwind build

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "🗃️  Running database migrations..."
python manage.py migrate

# Create default users for staging
echo "👤 Creating default users..."
python manage.py create_default_users

# Run basic health checks
echo "🔍 Running deployment health checks..."
python manage.py check --deploy

# Optional: Run tests in staging build
if [ "$RUN_TESTS_ON_BUILD" = "true" ]; then
    echo "🧪 Running tests..."
    python manage.py test --keepdb --verbosity=1
fi

echo "✅ Staging build completed successfully!"
