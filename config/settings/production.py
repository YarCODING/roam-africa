from .base import *

DEBUG = False

ALLOWED_HOSTS = [host.strip() for host in os.environ.get('ALLOWED_HOSTS', '').split(',') if host.strip()]

SECRET_KEY = os.environ.get('SECRET_KEY')