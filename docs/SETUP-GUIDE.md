# Zela Deployment Setup Guide

This guide will help you set up the complete staging → production pipeline for Zela.

## 🚀 Quick Start

### 1. Create Environment Files

```bash
# Copy example files
cp env-staging.example .env.staging
cp env-production.example .env.production

# Edit with your actual values
nano .env.staging
nano .env.production
```

### 2. Set Up GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

**Required Secrets:**

```bash
# Azure Credentials (JSON format)
AZURE_CREDENTIALS={"clientId":"xxx","clientSecret":"xxx","subscriptionId":"xxx","tenantId":"xxx"}

# Azure Container Registry (if using Docker)
AZURE_REGISTRY_LOGIN_SERVER=yourregistry.azurecr.io
AZURE_REGISTRY_USERNAME=yourregistry
AZURE_REGISTRY_PASSWORD=xxx
```

### 3. Configure Render (Staging)

1. Connect your GitHub repository
2. Set branch to `staging`
3. Set build command: `./build-staging.sh`
4. Set start command: `gunicorn --bind 0.0.0.0:$PORT Zela.wsgi:application`
5. Add environment variables from `.env.staging`

### 4. Configure Azure (Production)

1. Create Azure Web App
2. Set up deployment from GitHub (main branch)
3. Configure environment variables from `.env.production`
4. Set up Azure Database for PostgreSQL

## 📋 Detailed Setup Instructions

### Render Staging Setup

1. **Create Render Account**: Sign up at [render.com](https://render.com)

2. **Create Web Service**:

   - Connect GitHub repository
   - Branch: `staging`
   - Root Directory: `Zela`
   - Build Command: `./build-staging.sh`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT Zela.wsgi:application`

3. **Add Environment Variables**:

   ```bash
   DJANGO_SETTINGS_MODULE=Zela.settings.staging
   SECRET_KEY=your-staging-secret-key
   DEBUG=False
   # ... (copy from env-staging.example)
   ```

4. **Create PostgreSQL Database**:
   - Create new PostgreSQL service in Render
   - Copy DATABASE_URL to your environment variables

### Azure Production Setup

1. **Create Azure Resources**:

   ```bash
   # Create resource group
   az group create --name zela-production --location eastus

   # Create App Service Plan
   az appservice plan create --name zela-plan --resource-group zela-production --sku B1 --is-linux

   # Create Web App
   az webapp create --resource-group zela-production --plan zela-plan --name zela-production --runtime "PYTHON|3.11"

   # Create PostgreSQL Database
   az postgres server create --resource-group zela-production --name zela-db --admin-user zelaadmin --admin-password YourSecurePassword123
   ```

2. **Configure Deployment**:

   - Set up GitHub Actions deployment (already configured)
   - Add environment variables to Azure Web App
   - Configure custom domain and SSL

3. **Set Environment Variables**:
   ```bash
   az webapp config appsettings set --resource-group zela-production --name zela-production --settings @production-settings.json
   ```

### GitHub Actions Setup

1. **Environment Protection**:

   - Go to Settings → Environments
   - Create "production" environment
   - Add protection rules (require reviewers)

2. **Branch Protection**:
   - Protect `main` branch
   - Require PR reviews
   - Require status checks

## 🔄 Workflow

### Development Process

```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Make changes and test locally
python manage.py runserver

# 3. Commit and push to staging
git checkout staging
git merge feature/new-feature
git push origin staging
# → Automatic deployment to Render staging

# 4. QA testing on staging
# Visit https://zela-staging.onrender.com

# 5. After QA approval, deploy to production
git checkout main
git merge staging
git push origin main
# → Manual approval required → Azure deployment
```

### Emergency Procedures

**Quick Rollback:**

```bash
# Revert last commit
git revert HEAD
git push origin main

# Or rollback to specific commit
git reset --hard <good-commit-hash>
git push --force origin main
```

## 🧪 Testing Setup

### Local Testing

```bash
cd Zela
python manage.py test
python manage.py check --deploy
```

### CI/CD Testing

- Tests run automatically on every push
- Staging: Basic functionality tests
- Production: Comprehensive security and deployment checks

## 📊 Monitoring

### Health Checks

Add to your Django URLs:

```python
# Zela/website/urls.py
path('health/', lambda request: JsonResponse({'status': 'ok'}), name='health'),
```

### Logging

- **Render**: Built-in logging dashboard
- **Azure**: Application Insights integration
- **Local**: Django logging to console

## 🔐 Security Checklist

- [ ] Environment variables configured (no secrets in code)
- [ ] HTTPS enabled on both environments
- [ ] Database credentials secured
- [ ] GitHub secrets configured
- [ ] CSRF protection enabled
- [ ] HSTS headers configured
- [ ] Secure cookies enabled

## 🚨 Troubleshooting

### Common Issues

**Build fails on Render:**

```bash
# Check build logs
# Verify environment variables
# Ensure requirements.txt is up to date
```

**Azure deployment fails:**

```bash
# Check GitHub Actions logs
# Verify Azure credentials
# Check resource quotas
```

**Database connection issues:**

```bash
# Verify DATABASE_URL format
# Check firewall rules
# Test connection locally
```

### Getting Help

1. **Check logs first**: Render dashboard, Azure portal, GitHub Actions
2. **Verify configuration**: Environment variables, secrets
3. **Test locally**: Ensure code works in development
4. **Contact support**: Include error messages and logs

## 📚 Next Steps

After successful setup:

1. Set up monitoring and alerting
2. Configure backup strategies
3. Implement load testing
4. Set up CDN for static files
5. Configure error tracking (Sentry)

## 🎯 Success Criteria

Your setup is complete when:

- [ ] Staging deploys automatically on `staging` branch push
- [ ] Tests run successfully in CI/CD
- [ ] Production requires manual approval
- [ ] Health checks pass on both environments
- [ ] Rollback procedures work
- [ ] Monitoring is functional
