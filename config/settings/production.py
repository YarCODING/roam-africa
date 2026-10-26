from .base import *
import dj_database_url
import ssl

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
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True 

SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

TURNSTILE_SITEKEY = env('TURNSTILE_SITEKEY')
TURNSTILE_SECRET = env('TURNSTILE_SECRET')


# MAILERS = {
#     'default': {
#         'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
#         'OPTIONS': {
#             'host': 'smtp-relay.brevo.com',
#             'port': 587,
#             'use_tls': True,
#             'username': env('BREVO_USER'),
#             'password': env('BREVO_PASSWORD'),
#             'timeout': 10,
#         },
#     },
# }
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp-relay.brevo.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('BREVO_USER')
EMAIL_HOST_PASSWORD = env('BREVO_PASSWORD')
EMAIL_TIMEOUT = 30

DEFAULT_FROM_EMAIL = f"Roam Africa <{env('EMAIL_USER')}>"


BASE_URL = env('BASE_URL')

SECRET_KEY = env('SECRET_KEY')

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "access_key": env("AWS_ACCESS_KEY_ID"),
            "secret_key": env("AWS_SECRET_ACCESS_KEY"),
            "bucket_name": "media",
            "endpoint_url": env("AWS_S3_ENDPOINT_URL"),
            "region_name": "eu-west-3",
            "default_acl": "public-read",
            "querystring_auth": False,
            "custom_domain": "iqythdlpjdmijfzefhun.storage.supabase.co/storage/v1/object/public/media",
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

MEDIA_URL = f"https://iqythdlpjdmijfzefhun.storage.supabase.co/storage/v1/object/public/media/"


ADMINS = [
    ('Yaroslav', '20011aric@gmail.com'),
]

REDIS_URL = env("REDIS_URL")

CELERY_BROKER_URL = env('CLOUDAMQP_URL')
CELERY_RESULT_BACKEND = REDIS_URL

REDIS_SSL_OPTIONS = {
    "ssl_cert_reqs": ssl.CERT_NONE,
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "ssl_cert_reqs": ssl.CERT_NONE,
        }
    }
}

CELERY_REDIS_BACKEND_USE_SSL = {
    'ssl_cert_reqs': ssl.CERT_NONE
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