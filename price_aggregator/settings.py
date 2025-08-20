# price_aggregator/settings.py
import os
from pathlib import Path

# from cryptography.fernet import Fernet

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# 你应该替换成你自己的密钥
SECRET_KEY = 'django-insecure-your-own-secret-key-here-for-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition
INSTALLED_APPS = [
    'daphne',  # 强制启动，<-- 将这一行添加到最顶部
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 核心应用
    'core',
    # Channels
    'channels',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'price_aggregator.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [BASE_DIR / 'templates'], # 添加全局模板目录
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

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 【修改】告诉Django在项目根目录的'templates'文件夹中寻找模板
        'DIRS': [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')],
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

WSGI_APPLICATION = 'price_aggregator.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
# --- 已更新为 MySQL 配置 ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'crypto_spread_db',         # 你的数据库名称
        'USER': 'root',         # 你的数据库用户名
        'PASSWORD': 'Xu308689', # 你的数据库密码
        'HOST': '127.0.0.1',            # 数据库主机，本地通常是 127.0.0.1
        'PORT': '3306',                 # 数据库端口，MySQL 默认是 3306
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Channels 配置 ---
ASGI_APPLICATION = 'price_aggregator.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        # 使用 Redis 作为通道层后端
        # 'BACKEND': 'channels.layers.InMemoryChannelLayer',
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)], # Redis 服务器地址
        },
    },
}


# --- 日志配置 (已更新) ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG', # <-- 更新为 DEBUG 以捕获更多信息
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'debug.log',
             'formatter': 'verbose',
        },
        'console': { # 添加控制台 handler
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'core': { # 为我们的core app配置logger
            'handlers': ['console', 'file'],
            'level': 'DEBUG', # <-- 更新为 DEBUG
            'propagate': False,
        },
    },
}


# --- 自定义项目配置 ---
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

TRACKED_PAIRS = [
    'btcusdt', 'ethusdt', 'solusdt',
    'ethbtc', 'solbtc', 'soleth'
]
BROADCAST_INTERVAL = 0.8


# 关键：确保你的 settings.py 中有一个强大的、随机生成的SECRET_KEY
# 并且额外生成一个专门用于数据加密的密钥
# FERNET_KEY = Fernet.generate_key()
FERNET_KEY = 'LSTlyLgxLiLX6UXHooqS-dq6WOL4inOuAY0ea5eBPZw='
