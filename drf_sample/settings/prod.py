from drf_sample.settings.base import *

# Override base settings for production environment
DEBUG = False
ALLOWED_HOSTS = ["*"]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'drf_sample_db',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

try:
    from drf_sample.settings.local import *
except FileNotFoundError:
    raise Exception("Create local.py to provide local settings configurations")
