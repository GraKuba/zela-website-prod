# Zela Deployment Guide

This guide covers the dual-environment deployment setup for Zela: **Render (Staging)** → **Azure (Production)**.

## 🏗️ Architecture Overview

```
Feature Branch → Staging Branch → Main Branch
       ↓              ↓              ↓
   Development    Render Staging   Azure Production
```

## 🚀 Deployment Environments

### Staging Environment (Render)

- **Branch**: `staging`
- **URL**: `https://zela-staging.onrender.com`
- **Auto-deploy**: ✅ Automatic on push to `staging`
- **Purpose**: Testing, QA, client review

### Production Environment (Azure)

- **Branch**: `main`
- **URL**: `https://zela.com`
- **Deploy**: Manual approval required
- **Purpose**: Live production site

## 📋 Deployment Process

### 1. Development to Staging

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Merge to staging
git checkout staging
git merge feature/new-feature
git push origin staging
```

**What happens automatically:**

- GitHub Actions runs tests
- Render deploys to staging
- Staging URL becomes available for QA

### 2. Staging to Production

```bash
# After QA approval on staging
git checkout main
git merge staging
git push origin main
```

**What happens:**

- GitHub Actions runs comprehensive tests
- Manual approval required (GitHub Environment Protection)
- Azure deployment begins
- Health checks verify deployment
- Production goes live

## 🔧 Environment Configuration

### Staging Environment Variables (Render)

```bash
# Core settings
DJANGO_SETTINGS_MODULE=Zela.settings.staging
DEBUG=False
SECRET_KEY=your-staging-secret-key

# Database
DATABASE_URL=postgresql://user:pass@host:port/db_name

# Security
ALLOWED_HOSTS=zela-staging.onrender.com,*.onrender.com
CSRF_TRUSTED_ORIGINS=https://zela-staging.onrender.com

# Email (optional for staging)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Optional: Redis for caching
REDIS_URL=redis://red-xxx:6379

# Optional: S3 for media files
USE_S3_MEDIA=False
```

### Production Environment Variables (Azure)

```bash
# Core settings
DJANGO_SETTINGS_MODULE=Zela.settings.production
DEBUG=False
SECRET_KEY=your-production-secret-key

# Database
DATABASE_URL=postgresql://user:pass@host:port/db_name

# Security
ALLOWED_HOSTS=zela.com,www.zela.com
CSRF_TRUSTED_ORIGINS=https://zela.com,https://www.zela.com
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@zela.com

# Optional: Redis for caching
REDIS_URL=redis://your-azure-redis:6379

# Optional: Azure Storage for media files
USE_S3_MEDIA=True
AWS_ACCESS_KEY_ID=your-azure-storage-key
AWS_SECRET_ACCESS_KEY=your-azure-storage-secret
AWS_STORAGE_BUCKET_NAME=zela-media
```

## 🧪 Testing Strategy

### Automated Tests (Both Environments)

```bash
# Run locally
cd Zela
python manage.py test

# Tests run automatically in CI/CD:
# - Django unit tests
# - Security checks
# - Deployment readiness checks
# - Database migration validation
```

### Manual QA Checklist (Staging)

- [ ] All pages load correctly
- [ ] Authentication flows work
- [ ] Booking process functions
- [ ] Dashboard features operational
- [ ] Mobile responsiveness
- [ ] Email notifications (if applicable)
- [ ] Payment processing (test mode)

## 🔄 Rollback Procedures

### Quick Rollback (Git-based)

```bash
# Find the last good commit
git log --oneline

# Revert the problematic commit
git revert <bad-commit-hash>
git push origin main

# This triggers automatic redeployment
```

### Azure-specific Rollback

1. **Deployment Slots**: Switch back to previous slot
2. **Container Registry**: Deploy previous image version
3. **Database**: Restore from backup if needed

### Emergency Procedures

1. **Immediate**: Use Azure portal to stop the app
2. **Quick fix**: Deploy hotfix branch directly
3. **Full rollback**: Restore previous version and database

## 📊 Monitoring & Health Checks

### Health Check Endpoints

- **Staging**: `https://zela-staging.onrender.com/health/`
- **Production**: `https://zela.com/health/`

### Monitoring Tools

- **Azure Application Insights** (Production)
- **Render Logs** (Staging)
- **GitHub Actions** (CI/CD status)

## 🔐 Security Considerations

### Secrets Management

- **GitHub Secrets**: Store Azure credentials, API keys
- **Environment Variables**: Never commit to repository
- **Render Environment**: Configure in dashboard
- **Azure Key Vault**: For production secrets

### Required GitHub Secrets

```bash
# For Azure deployment
AZURE_CREDENTIALS={"clientId":"...","clientSecret":"..."}
AZURE_REGISTRY_LOGIN_SERVER=your-registry.azurecr.io
AZURE_REGISTRY_USERNAME=your-username
AZURE_REGISTRY_PASSWORD=your-password
```

## 🚨 Troubleshooting

### Common Issues

**Staging deployment fails:**

```bash
# Check Render logs
# Verify environment variables
# Ensure DATABASE_URL is correct
```

**Production deployment fails:**

```bash
# Check GitHub Actions logs
# Verify Azure credentials
# Check resource quotas
```

**Database migration issues:**

```bash
# Run migration check first
python manage.py migrate --check

# Apply migrations manually if needed
python manage.py migrate --fake-initial
```

### Support Contacts

- **Development Team**: dev@zela.com
- **DevOps**: ops@zela.com
- **Emergency**: +1-xxx-xxx-xxxx

## 📚 Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Render Documentation](https://render.com/docs)
- [Azure Web Apps Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
