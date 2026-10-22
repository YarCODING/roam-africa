from .base import *

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
BASE_URL = "http://localhost:8000"

SECRET_KEY = 'django-insecure-8i_d2i&2$pj6-tffzw&q^1rg_+(v-!9qu90_9o22oxo67j!d)x'

TURNSTILE_SITEKEY = '1x00000000000000000000AA'  # 1x00000000000000000000AA - success, 2x00000000000000000000AB - fail
TURNSTILE_SECRET = '1x0000000000000000000000000000000AA'   # 1x0000000000000000000000000000000AA - success, 2x0000000000000000000000000000000AA - fail

INSTALLED_APPS += ['django_browser_reload']
MIDDLEWARE += ['django_browser_reload.middleware.BrowserReloadMiddleware']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

REDIS_URL = "redis://localhost:6379/0"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": "127.0.0.1",
            "port": 1025,
            "use_tls": False,
        },
    },
}

DEFAULT_FROM_EMAIL = "Roam Africa <noreply@roamafrica.com>"

UNFOLD["SITE_DROPDOWN"] = [
    {
        "icon": "lan",
        "title": "Broker admin (RabbitMQ)",
        "link": "http://localhost:15672/#/",
        "attrs": {"target": "_blank",},
    },
    {
        "icon": "analytics",
        "title": "Worker admin (Flower)",
        "link": "http://127.0.0.1:5555/",
        "attrs": {"target": "_blank",},
    },
]