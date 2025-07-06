"""
Development settings for Zela project.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Development-specific apps
INSTALLED_APPS += [
    'django_browser_reload',
]

# Development-specific middleware
MIDDLEWARE += [
    'django_browser_reload.middleware.BrowserReloadMiddleware',
]

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Django Debug Toolbar (optional - uncomment if you want to use it)
# INTERNAL_IPS = [
#     "127.0.0.1",
# ]

# Email backend for development (prints emails to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable SSL redirects in development
SECURE_SSL_REDIRECT = False

# Static files - disable compression in development
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage' 