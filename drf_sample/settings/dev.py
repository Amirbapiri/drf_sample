from drf_sample.settings.base import *

# Override base settings for development environment
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'drf_dev_db',
        'HOST': '127.0.0.1',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'PORT': '5432',
    }
}

INSTALLED_APPS = INSTALLED_APPS + ["django_extensions"]

try:
    from drf_sample.settings.local import *
except FileNotFoundError:
    raise Exception("Create local.py to provide local settings configurations")
