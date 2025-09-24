# Zela Website - Docker Deployment on Azure

## Overview

This Django application is deployed to Azure App Service using Docker containers. The deployment uses Azure Container Registry (ACR) for image storage and GitHub Actions for CI/CD.

## Architecture

- **Platform**: Azure App Service for Containers (Linux)
- **Container Registry**: Azure Container Registry
- **Runtime**: Python 3.11 (in Docker)
- **Web Server**: Gunicorn
- **Database**: PostgreSQL (Azure Database for PostgreSQL)
- **Static Files**: WhiteNoise (built into container)
- **CSS Framework**: Tailwind CSS (compiled during Docker build)

## Prerequisites

1. **Azure Resources**:
   - Azure Container Registry (ACR)
   - Azure App Service configured for containers
   - Azure Database for PostgreSQL

2. **GitHub Secrets Required**:
   ```
   REGISTRY_LOGIN_SERVER        # e.g., acrzelaprod.azurecr.io
   REGISTRY_USERNAME            # ACR username
   REGISTRY_PASSWORD            # ACR password
   AZUREAPPSERVICE_CLIENTID_*   # Service principal client ID
   AZUREAPPSERVICE_TENANTID_*   # Service principal tenant ID
   AZUREAPPSERVICE_SUBSCRIPTIONID_* # Azure subscription ID
   ```

## Deployment Process

### Automatic Deployment (GitHub Actions)

1. Push code to `main` branch
2. GitHub Actions workflow triggers:
   - Builds Docker image with multi-stage build
   - Pushes image to Azure Container Registry
   - Deploys new image to Azure App Service
3. App Service automatically restarts with new container

### Manual Deployment

```bash
# 1. Build Docker image locally
docker build -t zela-web .

# 2. Tag for ACR
docker tag zela-web {REGISTRY_LOGIN_SERVER}/zela-web:latest

# 3. Login to ACR
docker login {REGISTRY_LOGIN_SERVER} -u {USERNAME} -p {PASSWORD}

# 4. Push to ACR
docker push {REGISTRY_LOGIN_SERVER}/zela-web:latest

# 5. Update App Service (via Azure Portal or CLI)
az webapp config container set \
  --name app-zela-prod \
  --resource-group rg-zela-prod \
  --docker-custom-image-name {REGISTRY_LOGIN_SERVER}/zela-web:latest
```

## Local Development with Docker

### Quick Start

```bash
# Build and run with docker-compose
docker-compose up --build

# Access at http://localhost:8000
```

### Testing Production Build

```bash
# Build production image
docker build -t zela-web:prod .

# Run production container
docker run -p 8000:8000 \
  -e SECRET_KEY='your-secret-key' \
  -e DATABASE_URL='your-database-url' \
  -e DEBUG=False \
  zela-web:prod
```

## Azure Configuration

### App Service Environment Variables

Set these in Azure Portal → App Service → Configuration → Application settings:

```bash
# Django Settings
SECRET_KEY=your-secret-key
DEBUG=False
DJANGO_SETTINGS_MODULE=Zela.settings.production

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Email (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@zela.com

# Allowed Hosts
ALLOWED_HOSTS=app-zela-prod.azurewebsites.net

# Security
SECURE_SSL_REDIRECT=True
```

### Container Configuration

In Azure Portal → App Service → Deployment Center:

1. **Source**: Azure Container Registry
2. **Registry**: Your ACR instance
3. **Image**: zela-web
4. **Tag**: latest
5. **Continuous Deployment**: ON (webhook to ACR)

## Database Management

### Run Migrations

```bash
# SSH into App Service
az webapp ssh --name app-zela-prod --resource-group rg-zela-prod

# Inside container
python manage.py migrate
python manage.py createsuperuser  # Create admin user
```

### Backup Database

```bash
# Use Azure Portal or CLI to create backup
az postgres db-backup create \
  --resource-group rg-zela-prod \
  --server-name your-postgres-server \
  --database-name your-database
```

## Monitoring

### View Logs

```bash
# Stream application logs
az webapp log tail \
  --name app-zela-prod \
  --resource-group rg-zela-prod

# Download logs
az webapp log download \
  --name app-zela-prod \
  --resource-group rg-zela-prod \
  --log-file logs.zip
```

### Container Logs

In Azure Portal:
- App Service → Monitoring → Log stream
- App Service → Diagnose and solve problems

### Health Check

The container includes a health check endpoint:
- URL: `http://app-zela-prod.azurewebsites.net/`
- Interval: 30 seconds
- Timeout: 10 seconds

## Troubleshooting

### Common Issues

#### Container Won't Start
- Check environment variables in App Service Configuration
- Verify DATABASE_URL is correct
- Check container logs for startup errors

#### Static Files Not Loading
- Ensure `collectstatic` runs during Docker build
- Verify WhiteNoise is configured in settings
- Check STATIC_URL and STATIC_ROOT settings

#### Database Connection Failed
- Verify DATABASE_URL format
- Check firewall rules on Azure PostgreSQL
- Ensure SSL mode is configured correctly

#### Image Pull Failed
- Verify ACR credentials in App Service
- Check image exists in ACR
- Ensure App Service has access to ACR

### Rollback Procedure

```bash
# List available images in ACR
az acr repository show-tags \
  --name acrzelaprod \
  --repository zela-web \
  --output table

# Deploy previous version
az webapp config container set \
  --name app-zela-prod \
  --resource-group rg-zela-prod \
  --docker-custom-image-name {REGISTRY_LOGIN_SERVER}/zela-web:{PREVIOUS_TAG}
```

## Security Best Practices

1. **Container Security**:
   - Run as non-root user (django user in Dockerfile)
   - Use minimal base image (python:3.11-slim)
   - Regularly update base images

2. **Registry Security**:
   - Use managed identity when possible
   - Rotate ACR passwords regularly
   - Enable vulnerability scanning

3. **Application Security**:
   - Never commit secrets
   - Use Azure Key Vault for sensitive data
   - Enable HTTPS only
   - Keep dependencies updated

## Maintenance

### Update Dependencies

```bash
# Update Python packages
cd Zela
pip-compile --upgrade pyproject.toml -o requirements.txt

# Update Node packages (for Tailwind)
cd theme/static_src
npm update

# Rebuild and deploy container
```

### Scale Application

```bash
# Scale up (vertical)
az appservice plan update \
  --name your-plan \
  --resource-group rg-zela-prod \
  --sku P2V3

# Scale out (horizontal)
az webapp update \
  --name app-zela-prod \
  --resource-group rg-zela-prod \
  --minimum-elastic-instance-count 2
```

## Version History

- **v2.0** - Migrated to Docker-based deployment
- **v1.2** - Previous code-based deployment (deprecated)

## Support

For deployment issues:
1. Check container logs in Azure Portal
2. Verify all environment variables are set
3. Review GitHub Actions workflow logs
4. Contact DevOps team if issues persist