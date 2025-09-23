# Zela Website - Azure Deployment Guide

## Overview

This Django application is deployed to Azure App Service using GitHub Actions for CI/CD. The deployment process includes building the application, installing dependencies, compiling Tailwind CSS, and deploying to Azure.

## Prerequisites

- Azure subscription with an App Service (Linux, Python 3.11)
- GitHub repository with Actions enabled
- Azure Service Principal for authentication

## Architecture

- **Platform**: Azure App Service (Linux)
- **Runtime**: Python 3.11
- **Web Server**: Gunicorn
- **Database**: PostgreSQL (Azure Database for PostgreSQL)
- **Static Files**: WhiteNoise
- **CSS Framework**: Tailwind CSS

## Deployment Process

### 1. GitHub Actions Workflow

The deployment is triggered automatically when code is pushed to the `main` branch. The workflow:

1. Sets up Python 3.11 environment
2. Creates virtual environment and installs dependencies
3. Builds Tailwind CSS assets
4. Collects static files
5. Creates deployment package
6. Deploys to Azure App Service

### 2. Azure App Service Configuration

#### Required Environment Variables

Set these in Azure Portal → App Service → Configuration → Application settings:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
DJANGO_SETTINGS_MODULE=Zela.settings.production

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Email Configuration (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@zela.com

# Allowed Hosts
ALLOWED_HOSTS=app-zela-prod.azurewebsites.net,.azurewebsites.net

# Security (for HTTPS)
SECURE_SSL_REDIRECT=True
```

#### Startup Command

In Azure Portal → App Service → Configuration → General settings → Startup Command:

```bash
cd /tmp/8ddfae* && . antenv/bin/activate && cd Zela && gunicorn --bind 0.0.0.0:8000 Zela.wsgi:application
```

Or use the custom startup script:

```bash
/home/site/wwwroot/Zela/startup-prod.sh
```

### 3. Database Setup

#### Create Azure Database for PostgreSQL

1. Create a PostgreSQL server in Azure
2. Configure firewall rules to allow Azure services
3. Create a database for the application
4. Note the connection string

#### Run Migrations

SSH into the App Service and run:

```bash
cd /home/site/wwwroot/Zela
python manage.py migrate
python manage.py createsuperuser  # Create admin user
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Application Not Starting

**Error**: `/opt/startup/startup.sh: 26: source: not found`

**Solution**: Azure uses `/bin/sh` not bash. Use the `startup-prod.sh` script which is sh-compatible.

#### 2. Module Import Errors

**Error**: `ModuleNotFoundError: No module named 'Zela'`

**Solution**: Ensure PYTHONPATH is set correctly:
```bash
export PYTHONPATH=/home/site/wwwroot/Zela:$PYTHONPATH
```

#### 3. Static Files Not Loading

**Solution**: 
1. Verify WhiteNoise is installed and configured
2. Run `python manage.py collectstatic --noinput`
3. Check STATIC_ROOT and STATIC_URL settings

#### 4. Database Connection Failed

**Solution**:
1. Verify DATABASE_URL format
2. Check firewall rules on Azure PostgreSQL
3. Ensure SSL mode is configured if required

### Viewing Logs

#### Application Logs
```bash
# Via Azure CLI
az webapp log tail --name app-zela-prod --resource-group your-rg

# Via Azure Portal
App Service → Monitoring → Log stream
```

#### SSH Access
```bash
# Via Azure Portal
App Service → Development Tools → SSH

# Via Azure CLI
az webapp ssh --name app-zela-prod --resource-group your-rg
```

## Local Development

### Setup

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   cd Zela
   pip install -r requirements.txt
   ```
4. Install and build Tailwind CSS:
   ```bash
   cd theme/static_src
   npm install
   npm run build
   ```
5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```
6. Run migrations:
   ```bash
   python manage.py migrate
   ```
7. Run development server:
   ```bash
   python manage.py runserver
   ```

### Testing Production Build Locally

```bash
# Use production settings
export DJANGO_SETTINGS_MODULE=Zela.settings.production
python manage.py collectstatic --noinput
gunicorn --bind 0.0.0.0:8000 Zela.wsgi:application
```

## Deployment Checklist

Before deploying to production:

- [ ] Update SECRET_KEY in Azure App Settings
- [ ] Configure DATABASE_URL for production database
- [ ] Set DEBUG=False
- [ ] Configure email settings if needed
- [ ] Update ALLOWED_HOSTS
- [ ] Test database migrations
- [ ] Verify static files are collected
- [ ] Check SSL/HTTPS configuration
- [ ] Set up monitoring and alerts
- [ ] Configure backup strategy
- [ ] Review security settings

## Monitoring

### Health Checks

The application exposes health endpoints:
- `/` - Main application
- `/admin/` - Django admin interface

### Performance Metrics

Monitor in Azure Portal:
- Response time
- Request rate  
- Error rate
- CPU/Memory usage

## Security Best Practices

1. **Never commit secrets to repository**
   - Use environment variables
   - Use Azure Key Vault for sensitive data

2. **Keep dependencies updated**
   ```bash
   pip list --outdated
   npm audit
   ```

3. **Use HTTPS only**
   - Enforce SSL redirect
   - Use secure cookies

4. **Regular backups**
   - Database backups
   - Application configuration export

## Support

For issues or questions:
1. Check the [troubleshooting section](#troubleshooting)
2. Review Azure App Service logs
3. Contact the development team

## Version History

- **v1.0** - Initial deployment configuration
- **v1.1** - Added sh-compatible startup script for Azure
- **v1.2** - Improved error handling and logging