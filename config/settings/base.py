import environ, os
from pathlib import Path
from django.templatetags.static import static
from django.urls import reverse_lazy

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

PROJECT_TITLE = "Roam Africa"

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


INSTALLED_APPS = [
    # admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.import_export",
    "unfold.contrib.simple_history",
    "unfold.contrib.hijack",

    # django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # apps
    'core',
    'users',
    'tours',
    'bookings',
    'bot',

    # 3rd party
    'allauth',
    'allauth.account',
    'django_countries',
    'import_export',
    'simple_history',
    'hijack',
    'hijack.contrib.admin',
    'djmoney',
    'djmoney.contrib.exchange',

    'django_cleanup.apps.CleanupConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'hijack.middleware.HijackUserMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'tours.context_processors.countries_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_USER_MODEL = 'users.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'uk'

TIME_ZONE = 'Europe/Kyiv'

USE_I18N = True

USE_TZ = True

DATE_INPUT_FORMATS = [
    "%d.%m.%Y",
    "%Y-%m-%d",
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = '/media/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/'

AUTH_USER_MODEL = 'users.CustomUser'
ACCOUNT_LOGIN_METHODS = {'email', 'username'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']


STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')


def get_navigation(request):
    navigation = [
        {
            "title": "Головна",
            "separator": False,
            "items": [
                {
                    "title": "Дашборд",
                    "icon": "dashboard",
                    "link": reverse_lazy("admin:index"),
                },
            ],
        },
        {
            "title": "Управління турами",
            "separator": True,
            "items": [
                {
                    "title": "Країни",
                    "icon": "public",
                    "link": reverse_lazy("admin:tours_country_changelist"),
                },
                {
                    "title": "Тури",
                    "icon": "explore",
                    "link": reverse_lazy("admin:tours_tour_changelist"),
                },
                {
                    "title": "Дати заїздів",
                    "icon": "calendar_month",
                    "link": reverse_lazy("admin:tours_tourdate_changelist"),
                },
                {
                    "title": "Відгуки",
                    "icon": "rate_review",
                    "link": reverse_lazy("admin:tours_tourreview_changelist"),
                },
            ],
        },
        {
            "title": "Продажі та бронювання",
            "separator": True,
            "items": [
                {
                    "title": "Бронювання",
                    "icon": "book_2",
                    "link": reverse_lazy("admin:bookings_booking_changelist"),
                },
            ],
        },
    ]

    is_superuser = request.user.is_superuser
    is_top_manager = request.user.groups.filter(name="Вищі менеджери").exists()
    
    if is_superuser or is_top_manager:
        navigation.append({
            "title": "Адміністрування",
            "separator": True,
            "items": [
                {
                    "title": "Користувачі", 
                    "icon": "people", 
                    "link": reverse_lazy("admin:users_customuser_changelist")
                },
                {
                    "title": "Групи прав", 
                    "icon": "security", 
                    "link": reverse_lazy("admin:auth_group_changelist")
                },
                {
                    "title": "Журнал", 
                    "icon": "history", 
                    "link": reverse_lazy("admin:admin_logentry_changelist")
                },
            ],
        })
        
    return navigation


UNFOLD = {
    "SITE_TITLE": "Roam Africa Admin",
    "SITE_HEADER": "Roam Africa",
    "SITE_URL": "/",
    
    "SITE_ICON": {
        "light": lambda request: static("images/logo.png"),
        "dark": lambda request: static("images/logo.png"),
    },

    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": lambda request: static("images/favicon.png"),
        },
    ],
    
    "COLORS": {
        "primary": {
            "50": "250 246 240",   # #FAF6F0
            "100": "242 234 224",  # #F2EAE0
            "200": "229 216 200",  # #E5D8C8
            "300": "224 159 62",   # #E09F3E (Accent)
            "400": "158 71 42",    # #9E472A (Primary)
            "500": "158 71 42",    # #9E472A
            "600": "120 54 32",
            "700": "90 40 24",
            "800": "45 64 48",     # #2D4030 (Secondary)
            "900": "42 36 33",     # #2A2421
            "950": "28 25 23",     # #1C1917
        },
    },
    
    "STYLES": [
        lambda request: static("css/unfold_custom.css"),
    ],
    
    "DASHBOARD_CALLBACK": "tours.dashboard.dashboard_callback",

    "LOGIN": {
        "image": lambda request: static("images/login_image.jpg"),
    },


    "SIDEBAR": {
        "show_search": False,
        "show_all_applications": False,
        "navigation": get_navigation,
    },
}


def custom_hijack_check(hijacker, hijacked):
    if hijacked.is_superuser:
        return False
    return hijacker.groups.filter(name="Вищі менеджери").exists()


HIJACK_PERMISSION_CHECK = "config.settings.base.custom_hijack_check"


AUTO_CONVERT_MONEY = True
EXCHANGE_BACKEND = 'djmoney.contrib.exchange.backends.OpenExchangeRatesBackend'
OPEN_EXCHANGE_RATES_APP_ID = 'affa1ca0af1648bf89d99825f8affd4e'
DEFAULT_CURRENCY = 'EUR'
CURRENCIES = ['EUR', 'USD', 'UAH']