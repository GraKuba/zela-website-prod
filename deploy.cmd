@echo off
:: Azure App Service deployment script for Django

echo Deployment started...

:: 1. Install Python dependencies
echo Installing Python dependencies...
cd Zela
python -m pip install --upgrade pip
pip install -r requirements.txt

:: 2. Run Django migrations
echo Running database migrations...
python manage.py migrate --noinput

:: 3. Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput

echo Deployment completed successfully!