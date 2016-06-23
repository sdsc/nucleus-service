"""
Django settings for nucleus project.

Generated by 'django-admin startproject' using Django 1.8.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import ssl

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME_DIR = os.getenv("HOME")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'qy4-11q&&19jaz!dwn7mk6r#zh+=iiprtzxn^@698$t*e(+f%#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = []
#DEBUG_PROPAGATE_EXCEPTIONS = True

# Application definition

# !!!!!!!!!!!!!!!!!!!!!!!!!! ONLY ENABLE IF USING BEHIND SECURE PROXY
# See https://docs.djangoproject.com/en/1.9/ref/settings/#secure-proxy-ssl-header warning
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

CSRF_COOKIE_AGE = 600
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_httpsignature',
    'api',
    'rest_framework_swagger',
    'rest_auth'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'nucleus.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'nucleus/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'nucleus.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'STORAGE_ENGINE': 'InnoDB',
        'OPTIONS': {'read_default_file': '/opt/rocks/etc/.nucleus.my.cnf'}
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'US/Pacific-New'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/html/static'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'api.auth.NucleusAPISignatureAuthentication'
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}

CELERY_TASK_SERIALIZER = 'auth'

CELERY_SECURITY_KEY = '/var/secrets/cometvc/key.pem'
CELERY_SECURITY_CERTIFICATE = '/var/secrets/cometvc/cert.pem'
CELERY_SECURITY_CERT_STORE = '/var/secrets/cometvc/*.pem'

CELERY_ROUTES = (
    {'api.tasks.submit_computeset':
     {'routing_key': 'frontend'}
     },
    {'api.tasks.cancel_computeset':
     {'routing_key': 'frontend'}
     },
    {'api.tasks.poweron_nodeset':
     {'routing_key': 'frontend'}
     },
    {'api.tasks.poweron_nodes':
     {'routing_key': 'frontend'}
     },
    {'api.tasks.poweroff_nodes':
     {'routing_key': 'frontend'}
     },
    {'api.tasks.attach_iso':
     {'routing_key': 'frontend'}
     },
    {'api.tasks.update_computeset':
     {'routing_key': 'update'}
     },
    {'api.tasks.update_clusters':
     {'routing_key': 'update'}
     }
)

CELERY_QUEUES = {
    'frontend': {
        'binding_key': 'frontend',
    },
    'update': {
        'binding_key': 'update',
    },
}

BROKER_USE_SSL = {
  'keyfile': '/var/secrets/cometvc/key.pem',
  'certfile': '/var/secrets/cometvc/cert.pem',
  'ca_certs': '/var/secrets/cometvc/ca.pem',
  'cert_reqs': ssl.CERT_REQUIRED
}

SWAGGER_SETTINGS = {
    "api_version": '1.0',  # API's version
    "api_path": "/nucleus"  # the path to API (it could not be a root level)
}
