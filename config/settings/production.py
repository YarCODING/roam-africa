from .base import *

DEBUG = False

ALLOWED_HOSTS = [host.strip() for host in os.environ.get('ALLOWED_HOSTS', '').split(',') if host.strip()]

BASE_URL = os.environ.get('BASE_URL')

SECRET_KEY = os.environ.get('SECRET_KEY')

ADMINS = [
    ('Yaroslav', '20011aric@gmail.com'),
]