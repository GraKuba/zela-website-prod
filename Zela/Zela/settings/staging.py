"""
Staging settings for Zela project.
Used for Render deployment and testing environment.
"""

import dj_database_url
from .base import *

# Debug mode - can be enabled for staging troubleshooting
DEBUG = config('DEBUG', default=False, cast=bool)

# Allowed hosts for Render and custom staging domain
ALLOWED_HOSTS = [
    '*.onrender.com',
    'staging.zela.com',
    'zela-staging.onrender.com',
] + config('ALLOWED_HOSTS', default='').split(',')

# Remove empty strings from ALLOWED_HOSTS
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS if host.strip()]

# Database configuration using DATABASE_URL (Render PostgreSQL)
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default=''),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Email configuration for staging (can use console or real SMTP for testing)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='staging@zela.com')

# Security settings - less strict than production for easier testing
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_HSTS_SECONDS = 3600  # 1 hour (less than production)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = False  # Don't preload staging domains
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
X_FRAME_OPTIONS = 'DENY'

# CSRF trusted origins for staging
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://staging.zela.com',
    'https://zela-staging.onrender.com',
] + [origin.strip() for origin in config('CSRF_TRUSTED_ORIGINS', default='').split(',') if origin.strip()]

# Staging-specific apps (optional - for testing tools)
STAGING_APPS = config('STAGING_APPS', default='').split(',')
if STAGING_APPS and STAGING_APPS[0]:  # Check if not empty
    INSTALLED_APPS += [app.strip() for app in STAGING_APPS if app.strip()]

# Logging configuration for staging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': config('LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'Zela': {  # Your app-specific logging
            'handlers': ['console'],
            'level': config('APP_LOG_LEVEL', default='DEBUG'),
            'propagate': False,
        },
    },
}

# Cache configuration for staging (optional - Redis if available)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'zela_staging',
        'TIMEOUT': 300,
    }
} if config('REDIS_URL', default='') else {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'zela-staging-cache',
    }
}

# Media files configuration for staging
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# Optional: Use cloud storage for staging media files
if config('USE_S3_MEDIA', default=False, cast=bool):
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default='zela-staging-media')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
