# # from pathlib import Path
# # from datetime import timedelta

# # # BASE DIR
# # BASE_DIR = Path(__file__).resolve().parent.parent

# # # SECURITY WARNING: keep the secret key used in production secret!
# # SECRET_KEY = 'django-insecure-change-this-to-a-strong-secret'

# # # SECURITY WARNING: don’t run with debug turned on in production!
# # DEBUG = True

# # ALLOWED_HOSTS = []


# # # Application definition
# # INSTALLED_APPS = [
# #     # Django default apps
# #     'django.contrib.admin',
# #     'django.contrib.auth',
# #     'django.contrib.contenttypes',
# #     'django.contrib.sessions',
# #     'django.contrib.messages',
# #     'django.contrib.staticfiles',

# #     # Third-party apps
# #     'rest_framework',
# #     'corsheaders',

# #     # Your apps
# #     'UserAuth',
# #     'Account',
# #     'Product',
# # ]

# # MIDDLEWARE = [
# #     'corsheaders.middleware.CorsMiddleware',   # must be at the top for CORS
# #     'django.middleware.security.SecurityMiddleware',
# #     'django.contrib.sessions.middleware.SessionMiddleware',
# #     'django.middleware.common.CommonMiddleware',
# #     'django.middleware.csrf.CsrfViewMiddleware',
# #     'django.contrib.auth.middleware.AuthenticationMiddleware',
# #     'django.contrib.messages.middleware.MessageMiddleware',
# #     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# # ]

# # ROOT_URLCONF = 'store.urls'

# # TEMPLATES = [
# #     {
# #         'BACKEND': 'django.template.backends.django.DjangoTemplates',
# #         'DIRS': [],
# #         'APP_DIRS': True,
# #         'OPTIONS': {
# #             'context_processors': [
# #                 'django.template.context_processors.debug',
# #                 'django.template.context_processors.request',
# #                 'django.contrib.auth.context_processors.auth',
# #                 'django.contrib.messages.context_processors.messages',
# #             ],
# #         },
# #     },
# # ]

# # WSGI_APPLICATION = 'store.wsgi.application'


# # # Database
# # # Using SQLite for dev. Swap with Postgres/MySQL in prod
# # DATABASES = {
# #     'default': {
# #         'ENGINE': 'django.db.backends.sqlite3',
# #         'NAME': BASE_DIR / 'db.sqlite3',
# #     }
# # }


# # # Password validation
# # AUTH_PASSWORD_VALIDATORS = [
# #     {
# #         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
# #     },
# #     {
# #         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
# #         'OPTIONS': {'min_length': 8}  # enforce strong passwords
# #     },
# #     {
# #         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
# #     },
# #     {
# #         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
# #     },
# # ]


# # # Internationalization
# # LANGUAGE_CODE = 'en-us'
# # TIME_ZONE = 'UTC'
# # USE_I18N = True
# # USE_TZ = True


# # # Static files (CSS, JavaScript, Images)
# # STATIC_URL = 'static/'

# # DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# # # ---------------------------
# # # Django REST Framework setup
# # # ---------------------------
# # REST_FRAMEWORK = {
# #     'DEFAULT_AUTHENTICATION_CLASSES': (
# #         'rest_framework_simplejwt.authentication.JWTAuthentication',
# #     ),
# #     'DEFAULT_PERMISSION_CLASSES': (
# #         'rest_framework.permissions.AllowAny',  # during dev
# #     ),
# # }

# # # ---------------------------
# # # Simple JWT setup
# # # ---------------------------
# # SIMPLE_JWT = {
# #     "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
# #     "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
# #     "ROTATE_REFRESH_TOKENS": False,
# #     "BLACKLIST_AFTER_ROTATION": True,
# # }

# # # ---------------------------
# # # CORS setup
# # # ---------------------------
# # CORS_ALLOWED_ORIGINS = [
# #     "http://localhost:3000",   # Your Next.js frontend
# #     "http://127.0.0.1:3000",   # Alternative localhost
# # ]
# # CORS_ALLOW_CREDENTIALS = True
# from pathlib import Path
# from datetime import timedelta
# import os

# # BASE DIR
# BASE_DIR = Path(__file__).resolve().parent.parent

# # SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-change-this-to-a-strong-secret'

# # SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True

# ALLOWED_HOSTS = []


# # Application definition
# INSTALLED_APPS = [
#     # Django default apps
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',

#     # Third-party apps
#     'rest_framework',
#     'corsheaders',
#     'django_filters',  # Add this line

#     # Your apps
#     'UserAuth',
#     'Account',
#     'Product',
# ]

# MIDDLEWARE = [
#     'corsheaders.middleware.CorsMiddleware',   # must be at the top for CORS
#     'django.middleware.security.SecurityMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]

# ROOT_URLCONF = 'store.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'store.wsgi.application'


# # Database
# # Using SQLite for dev. Swap with Postgres/MySQL in prod
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


# # Password validation
# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#         'OPTIONS': {'min_length': 8}  # enforce strong passwords
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]


# # Internationalization
# LANGUAGE_CODE = 'en-us'
# TIME_ZONE = 'UTC'
# USE_I18N = True
# USE_TZ = True


# # Static files (CSS, JavaScript, Images)
# STATIC_URL = 'static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# # Media files (uploaded content)
# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# # ---------------------------
# # Django REST Framework setup
# # ---------------------------
# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'rest_framework_simplejwt.authentication.JWTAuthentication',
#     ),
#     'DEFAULT_PERMISSION_CLASSES': (
#         'rest_framework.permissions.AllowAny',  # during dev
#     ),
#     'DEFAULT_FILTER_BACKENDS': [
#         'django_filters.rest_framework.DjangoFilterBackend',
#         'rest_framework.filters.SearchFilter',
#         'rest_framework.filters.OrderingFilter',
#     ],
# }

# # ---------------------------
# # Simple JWT setup
# # ---------------------------
# SIMPLE_JWT = {
#     "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
#     "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
#     "ROTATE_REFRESH_TOKENS": False,
#     "BLACKLIST_AFTER_ROTATION": True,
# }

# # ---------------------------
# # CORS setup
# # ---------------------------
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",   # Your Next.js frontend
#     "http://127.0.0.1:3000",   # Alternative localhost
# ]
# CORS_ALLOW_CREDENTIALS = True

from pathlib import Path
from datetime import timedelta
import os
import dj_database_url

# BASE DIR
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-change-this-to-a-strong-secret'
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-to-a-strong-secret')

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# ALLOWED_HOSTS = []
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.railway.app',
]


# Application definition
INSTALLED_APPS = [
    # Django default apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'corsheaders',
    'django_filters',  # Add this line

    # Your apps
    'UserAuth',
    'Account',
    'Product',
    'Cart',
    'Order'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # must be at the top for CORS
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'store.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Add this line
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

WSGI_APPLICATION = 'store.wsgi.application'


# Database
# Using SQLite for dev. Swap with Postgres/MySQL in prod
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
        conn_max_age=600
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}  # enforce strong passwords
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# Media files (uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------
# Django REST Framework setup
# ---------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',  # during dev
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# ---------------------------
# Simple JWT setup
# ---------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
}

# ---------------------------
# CORS setup
# ---------------------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",   # Your Next.js frontend
    "http://127.0.0.1:3000",   # Alternative localhost
]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]