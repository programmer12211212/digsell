import os
from pathlib import Path
import environ
from datetime import timedelta

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Read .env file if it exists
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY', default='django-insecure-default-key-replace-in-prod')

# Explicitly cast DEBUG and ALLOWED_HOSTS from environment
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])

# Dev-safe defaults: allow localhost when DEBUG, but require explicit configuration in prod
if DEBUG:
    if not ALLOWED_HOSTS:
        ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
else:
    if SECRET_KEY.startswith('django-insecure-') or len(SECRET_KEY) < 50:
        raise RuntimeError('In production, set a strong SECRET_KEY in the environment.')
    if not ALLOWED_HOSTS:
        raise RuntimeError('In production, set ALLOWED_HOSTS in the environment.')
    if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['*']:
        raise RuntimeError('In production, set a secure ALLOWED_HOSTS in the environment.')
    
# Application definition
INSTALLED_APPS = [
    'daphne',
    # Admin UI (Must be before django.contrib.admin)
    'jazzmin',
    # removed incorrect 'django-extensions' entry (use 'django_extensions' below)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',

    # Realtime
    'channels',

    # Security apps
    'axes',

    # Allauth and social auth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # Third party apps
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_htmx',
    'django_celery_results',
    'django_celery_beat',
    'django_extensions',

    # Internal apps
    'apps.users.apps.UsersConfig',
    'apps.marketplace',
    'apps.orders',
    'apps.ai_system',
    'apps.analytics',
    'apps.notifications',
    'apps.freelance.apps.FreelanceConfig',
    'apps.payments',
    'apps.subscriptions',
    'apps.support',
    'apps.security',
    'apps.blog',
    'apps.chat',
    'apps.core',
    'apps.videos',
    'apps.marketing',
    'apps.adminpanel',
    'apps.telegram_services.apps.TelegramServicesConfig',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'apps.security.middleware.BruteForceProtectionMiddleware',
    'apps.security.middleware.BlockedIPMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.notifications.context_processors.notifications_ctx',
                'apps.marketing.context_processors.advertisements_ctx',
                'apps.core.context_processors.branding_ctx',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database
DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 9},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Security settings
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'
# Redirect to HTTPS in production by default when DEBUG is False
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=(not DEBUG))
# During local development ensure we do not redirect to HTTPS even if env is set.
if DEBUG:
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0

# HSTS: enabled in production by default
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=(0 if DEBUG else 31536000))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=not DEBUG)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=not DEBUG)

# When behind a proxy (e.g. gunicorn + nginx) set this header in your proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookie secure flags will be set later based on DEBUG and SECURE_SSL_REDIRECT
# (this prevents setting secure-only cookies during local development over HTTP).
# SESSION_COOKIE_SECURE and CSRF_COOKIE_SECURE are configured below.

CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])
# In development, add common localhost origins so runserver POSTs don't fail CSRF.
if DEBUG and not CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = [
        'http://127.0.0.1',
        'http://localhost',
    ]

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_CREDENTIALS = True

# Configure secure cookie flags depending on environment
if DEBUG:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=SECURE_SSL_REDIRECT)
    CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=SECURE_SSL_REDIRECT)
DATA_UPLOAD_MAX_MEMORY_SIZE = env.int('DATA_UPLOAD_MAX_MEMORY_SIZE', default=10485760)
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Sessiya xavfsizligi
SESSION_COOKIE_AGE = 3600 * 8  # 8 soat
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# Parol xavfsizligi
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]

# AI API Keys
GROQ_API_KEY = env('GROQ_API_KEY', default='')

# Internationalization
LANGUAGE_CODE = 'uz-uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Use WhiteNoise storage for static files in production
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Jazzmin Settings
JAZZMIN_SETTINGS = {
    "site_title": "Digsell.uz Admin",
    "site_header": "Digsell.uz",
    "site_brand": "Digsell.uz",
    "site_logo": None,
    "welcome_sign": "Digsell.uz boshqaruv paneliga xush kelibsiz",
    "copyright": "Digsell.uz Ltd",
    "search_model": ["users.User", "marketplace.Product"],
    "user_avatar": None,

    # Top Menu
    "topmenu_links": [
        {"name": "Bosh sahifa",  "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Telegram Dashboard", "url": "/admin/telegram-services/dashboard/", "permissions": ["telegram_services.view_telegramorder"]},
        {"model": "support.SupportTicket"},
        {"model": "users.User"},
    ],

    # User Menu
    "usermenu_links": [
        {"name": "Yordam", "url": "https://t.me/Digsell_Help", "new_window": True},
        {"model": "users.User"}
    ],

    # Sidebar
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": [
        "telegram_services", "marketplace", "orders", "payments", "users", "freelance", "ai_system", "support", "blog"
    ],
    
    "icons": {
        "users.User": "fas fa-users",
        "marketplace.Product": "fas fa-shopping-cart",
        "marketplace.Category": "fas fa-tags",
        "orders.Order": "fas fa-file-invoice-dollar",
        "payments.Transaction": "fas fa-wallet",
        "payments.Coupon": "fas fa-ticket-alt",
        "ai_system.AIInteraction": "fas fa-robot",
        "support.SupportTicket": "fas fa-headset",
        "blog.BlogPost": "fas fa-newspaper",
        "telegram_services.telegramorder": "fas fa-shopping-basket",
        "telegram_services.telegramprovider": "fas fa-key",
        "telegram_services.telegramproduct": "fas fa-box",
        "telegram_services.telegramproductcategory": "fas fa-folder",
        "telegram_services.telegrampaymentcard": "fas fa-credit-card",
        "telegram_services.telegrampayment": "fas fa-receipt",
        "telegram_services.telegramgift": "fas fa-gift",
        "telegram_services.telegramproviderlog": "fas fa-file-alt",
        "telegram_services.telegramorderlog": "fas fa-history",
        "telegram_services.telegramnotification": "fas fa-bell",
        "telegram_services.telegramsettings": "fas fa-cogs",
    },
    
    "custom_links": {
        "telegram_services": [
            {
                "name": "Dashboard",
                "url": "/admin/telegram-services/dashboard/",
                "icon": "fas fa-chart-line",
                "permissions": ["telegram_services.view_telegramorder"]
            }
        ]
    },
    
    "show_ui_builder": False,
    "default_theme_mode": "dark",
    "custom_css": "css/admin_custom.css",
    "custom_js": "js/admin_effects.js",
    "use_google_fonts_cdn": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-danger",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-danger",
    "sidebar_nav_small_text": True,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_hover_elevate": True,
    "sidebar_accent": "accent-danger",
    "theme": "darkly",
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
}

# Django Axes (brute-force protection)
AXES_ENABLED = env.bool('AXES_ENABLED', default=True)
AXES_FAILURE_LIMIT = env.int('AXES_FAILURE_LIMIT', default=5)
AXES_COOLOFF_TIME = timedelta(minutes=env.int('AXES_COOLOFF_TIME_MINUTES', default=30))
# Note: older AXES settings like AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP,
# AXES_ONLY_USER_FAILURES and AXES_USE_USER_AGENT are deprecated in newer
# django-axes versions and are intentionally omitted here.

# Allauth / Authentication Settings
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
ACCOUNT_LOGIN_METHODS = {'email', 'username'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
    }
}

LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'users:login'
ACCOUNT_LOGOUT_REDIRECT_URL = 'users:login'
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = True

# Celery (background tasks)
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default=CELERY_BROKER_URL)

# X-Accel / sendfile support: when True, views will set X-Accel-Redirect for nginx
USE_X_ACCEL_REDIRECT = env.bool('USE_X_ACCEL_REDIRECT', default=False)
X_ACCEL_INTERNAL_LOCATION = env('X_ACCEL_INTERNAL_LOCATION', default='/internal_media/')

# Rate limit defaults
RATELIMIT_ENABLE = env.bool('RATELIMIT_ENABLE', default=True)

# Redis / Cache / Channels
REDIS_URL = env('REDIS_URL', default=CELERY_BROKER_URL)

if DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'digsell-admin',
        }
    }
    CHANNEL_LAYERS = {
        'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
        }
    }
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {'hosts': [REDIS_URL]},
        },
    }
