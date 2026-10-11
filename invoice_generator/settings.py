import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Where user data (database, logos, PDFs, generated keys) is stored.
DATA_DIR = BASE_DIR / "data"
(DATA_DIR / "db").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "media").mkdir(parents=True, exist_ok=True)

env = environ.Env()
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

# SECRET_KEY: use the environment/.env value if set. Otherwise generate a random
# per-install key once and keep it in the data folder, so there is never a public
# default key in use.
SECRET_KEY = env("SECRET_KEY", default="")
if not SECRET_KEY:
    from django.core.management.utils import get_random_secret_key

    _secret_file = DATA_DIR / "secret_key.txt"
    if _secret_file.exists():
        SECRET_KEY = _secret_file.read_text(encoding="utf-8").strip()
    if not SECRET_KEY:
        SECRET_KEY = get_random_secret_key()
        _secret_file.write_text(SECRET_KEY, encoding="utf-8")
        try:
            os.chmod(_secret_file, 0o600)  # best-effort; no-op on some Windows setups
        except OSError:
            pass

# Off unless you turn it on. Debug pages show settings and stack traces.
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Origins allowed to submit forms: the ALLOWED_HOSTS on port 8000.
_hosts = [h for h in ALLOWED_HOSTS if h != "*"]
CSRF_TRUSTED_ORIGINS = [f"http://{h}:8000" for h in _hosts]


# Application definition

INSTALLED_APPS = [
    "adminita",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "invoices",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "secure_uploads.middleware.SecureUploadMiddleware",
    "secure_uploads.middleware.ContentSecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "invoice_generator.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "invoice_generator.wsgi.application"

# Database - SQLite in data/db folder
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db" / "db.sqlite3",
    }
}

AUTH_USER_MODEL = "accounts.User"

SITE_ID = 1

# Version
INVOICEG_VERSION = "0.1.2"

# Authentication settings
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "invoices:dashboard"
LOGOUT_REDIRECT_URL = "login"

# First login, created on first run by `manage.py create_default_user`. Leave the
# password empty and a random one is generated and saved to data/first_login.txt.
DEFAULT_USER_EMAIL = env("DJANGO_SUPERUSER_EMAIL", default="admin@example.com")
DEFAULT_USER_PASSWORD = env("DJANGO_SUPERUSER_PASSWORD", default="")

# Email: SMTP when EMAIL_HOST is set, otherwise messages print to the console (so
# password-reset emails are not delivered; use `changepassword` instead, see README).
_email_host = env("EMAIL_HOST", default="")
if _email_host:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = _email_host
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
    EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
    DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Let WhiteNoise find static files in the source folders, so the app is styled even
# if collectstatic has not been run (for example with `manage.py runserver`).
WHITENOISE_USE_FINDERS = True

# Media files (company logo, generated PDFs). Served only to logged-in users, see
# invoice_generator/urls.py.
MEDIA_URL = "/media/"
MEDIA_ROOT = DATA_DIR / "media"
# Create invoices directory structure
INVOICES_ROOT = MEDIA_ROOT / "invoices"


STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Static files are compressed but NOT given hashed names, so WhiteNoise's default
# (short) cache time is kept on purpose: a long cache would leave browsers showing
# stale CSS after an update.


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-gb"
TIME_ZONE = os.environ.get("TZ", "Europe/London")
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging
# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "handlers": {
#         "file": {
#             "level": "ERROR",
#             "class": "logging.FileHandler",
#             "filename": BASE_DIR / "logs" / "django.log",
#         },
#     },
#     "loggers": {
#         "django": {
#             "handlers": ["file"],
#             "level": "ERROR",
#             "propagate": True,
#         },
#     },
# }

# Upload security (see secure_uploads/). The only upload is the company logo.
SECURE_UPLOAD_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
SECURE_UPLOAD_MAX_IMAGE_DIMENSIONS = (4096, 4096)
SECURE_UPLOAD_MIN_IMAGE_DIMENSIONS = (10, 10)
SECURE_UPLOAD_ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".gif"]
SECURE_UPLOAD_ALLOWED_IMAGE_MIME_TYPES = [
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
]
SECURE_UPLOAD_SANITISE_FILENAMES = True  # Replace filenames with random ones
