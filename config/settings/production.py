from .base import *
import dj_database_url

DEBUG = False

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
RATELIMIT_USE_X_FORWARDED_FOR = True
ALLAUTH_TRUSTED_CLIENT_IP_HEADER = "HTTP_X_FORWARDED_FOR"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True 

SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

TURNSTILE_SITEKEY = env('TURNSTILE_SITEKEY')
TURNSTILE_SECRET = env('TURNSTILE_SECRET')


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# MAILERS = {
#     'default': {
#         'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
#         'OPTIONS': {
#             'host': 'smtp.gmail.com',
#             'port': 587,
#             'use_tls': True,
#             'username': env('EMAIL_USER'),
#             'password': env('EMAIL_PASSWORD'),
#             'timeout': 10,
#         },
#     },
# }

DEFAULT_FROM_EMAIL = f"Roam Africa <{env('EMAIL_USER')}>"


BASE_URL = env('BASE_URL')

SECRET_KEY = env('SECRET_KEY')

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

ADMINS = [
    ('Yaroslav', '20011aric@gmail.com'),
]

CELERY_BROKER_URL = env('CLOUDAMQP_URL')
CELERY_RESULT_BACKEND = env('REDIS_URL')

REDIS_URL = env("REDIS_URL")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

DATABASES = {
    'default': dj_database_url.config(
        default=env('DATABASE_URL'),
        conn_max_age=600
    )
}

UNFOLD["SITE_DROPDOWN"] = [
    {
        "icon": "lan",
        "title": "Broker admin (RabbitMQ)",
        "link": env('RABBITMQ_ADMIN_URL'),
        "attrs": {
            "target": "_blank",
        },
    },
    {
        "icon": "analytics",
        "title": "Worker admin (Flower)",
        "link": env("CELERY_FLOWER_URL"),
        "attrs": {
            "target": "_blank",
        },
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'ERROR',
    },
}