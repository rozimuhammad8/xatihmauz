"""Django sozlamalari.

Muhitga bog'liq qiymatlar (maxfiy kalit, DEBUG, ruxsat etilgan hostlar, baza)
`.env` faylidan yoki muhit o'zgaruvchilaridan o'qiladi — kodda hech qanday
maxfiy ma'lumot yozilmaydi. Namuna uchun: `.env.example` faylini nusxalab
`.env` deb nomlang.

Ishlab chiqish (development):
    DJANGO_DEBUG=True bo'lsa, sozlamalar yumshoq: har qanday host qabul
    qilinadi, xavfsizlik cheklovlari o'chiriladi, xatolar to'liq ko'rsatiladi.

Ishga tushirish (production):
    DJANGO_DEBUG=False (sukut bo'yicha). Bunda DJANGO_SECRET_KEY va
    DJANGO_ALLOWED_HOSTS majburiy — ularsiz dastur ataylab ishga tushmaydi,
    chunki noto'g'ri sozlangan server maxfiy ma'lumotni oshkor qilishi mumkin.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------
# .env FAYLINI O'QISH
# Tashqi kutubxonasiz, sodda o'quvchi: KALIT=qiymat ko'rinishidagi
# qatorlar. Muhit o'zgaruvchisi allaqachon o'rnatilgan bo'lsa, .env uni
# BOSIB O'TMAYDI (server sozlamasi fayldan ustun turadi).
# ------------------------------------------------------------------
def _env_faylini_yuklash(yol):
    if not yol.exists():
        return
    for qator in yol.read_text(encoding="utf-8").splitlines():
        qator = qator.strip()
        if not qator or qator.startswith("#") or "=" not in qator:
            continue
        kalit, qiymat = qator.split("=", 1)
        kalit, qiymat = kalit.strip(), qiymat.strip()
        if len(qiymat) >= 2 and qiymat[0] == qiymat[-1] and qiymat[0] in "\"'":
            qiymat = qiymat[1:-1]
        os.environ.setdefault(kalit, qiymat)


_env_faylini_yuklash(BASE_DIR / ".env")


def env(kalit, sukut=None):
    qiymat = os.environ.get(kalit)
    return qiymat if qiymat not in (None, "") else sukut


def env_bool(kalit, sukut=False):
    qiymat = env(kalit)
    if qiymat is None:
        return sukut
    return qiymat.strip().lower() in ("1", "true", "yes", "on", "ha")


def env_list(kalit, sukut=()):
    qiymat = env(kalit)
    if not qiymat:
        return list(sukut)
    return [b.strip() for b in qiymat.split(",") if b.strip()]


class SozlamaXatosi(Exception):
    """Production uchun majburiy sozlama berilmagan."""


# ------------------------------------------------------------------
# ASOSIY
# ------------------------------------------------------------------
DEBUG = env_bool("DJANGO_DEBUG", False)

# Ishlab chiqishda tasodifiy kalit yetarli; productionda majburiy.
SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-faqat-ishlab-chiqish-uchun-almashtiring"
    else:
        raise SozlamaXatosi(
            "DJANGO_SECRET_KEY berilmagan. .env faylida uni belgilang:\n"
            "  python -c \"from django.core.management.utils import "
            "get_random_secret_key as k; print(k())\""
        )

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    if DEBUG:
        ALLOWED_HOSTS = ["*"]
    else:
        raise SozlamaXatosi(
            "DJANGO_ALLOWED_HOSTS berilmagan. Masalan:\n"
            "  DJANGO_ALLOWED_HOSTS=ihma.uz,www.ihma.uz,127.0.0.1"
        )

# HTTPS orqali ishlaganda CSRF uchun ishonchli manbalar
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")


# ------------------------------------------------------------------
# ILOVALAR
# ------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'reestr',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise statik fayllarni Django serverisiz uzatadi (o'rnatilgan
    # bo'lsa ishlatiladi; bo'lmasa ro'yxatdan chiqariladi — pastga qarang).
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # DEBUG=True bo'lsa ham custom 404 sahifasini ko'rsatadi — qarang:
    # config/middleware.py.
    'config.middleware.Maxsus404Middleware',
]

try:  # pragma: no cover — muhitga bog'liq
    import whitenoise  # noqa: F401
except ImportError:
    MIDDLEWARE.remove('whitenoise.middleware.WhiteNoiseMiddleware')

ROOT_URLCONF = 'config.urls'

# Mavjud migratsiyalar (va bazadagi ustunlar) BigAutoField bilan yaratilgan.
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ------------------------------------------------------------------
# BAZA
# ------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': env("DJANGO_DB_PATH", BASE_DIR / 'db.sqlite3'),
        'OPTIONS': {
            # Bir vaqtda bir necha xodim yozayotganda "database is locked"
            # xatosi o'rniga 20 soniyagacha kutadi.
            'timeout': 20,
        },
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ------------------------------------------------------------------
# MINTAQA
# ------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True


# ------------------------------------------------------------------
# STATIK FAYLLAR
# ------------------------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'   # `manage.py collectstatic` shu yerga yig'adi

if not DEBUG:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if 'whitenoise.middleware.WhiteNoiseMiddleware' in MIDDLEWARE
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }


# ------------------------------------------------------------------
# SHABLONLAR (.docx)
# Barcha Word shablonlari bitta "Shablons" papkasida, tizimlar bo'yicha
# ajratilgan: Ariza / reeystr / xizmat. Qarang: Shablons/README.md
# ------------------------------------------------------------------
SHABLONLAR_ROOT = Path(env("SHABLONLAR_ROOT", BASE_DIR / 'Shablons'))

SHABLONLAR_DIR = SHABLONLAR_ROOT / 'Ariza'
REESTR_SHABLONLAR_DIR = SHABLONLAR_ROOT / 'reeystr'
XIZMAT_SHABLONLAR_DIR = SHABLONLAR_ROOT / 'xizmat'

# Xizmat shablonlari yasaladigan haqiqiy namunalar (loyihadan tashqarida)
XIZMAT_NAMUNA_DIR = BASE_DIR.parent / 'yangi shablonlar'


# ------------------------------------------------------------------
# AUTENTIFIKATSIYA
# ------------------------------------------------------------------
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

SESSION_COOKIE_AGE = int(env("DJANGO_SESSION_AGE", 60 * 60 * 12))  # 12 soat
SESSION_EXPIRE_AT_BROWSER_CLOSE = False


# ------------------------------------------------------------------
# XAVFSIZLIK (faqat production'da yoqiladi)
# ------------------------------------------------------------------
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"

    # Teskari proksi (nginx) orqasida HTTPS ishlatilsa
    if env_bool("DJANGO_HTTPS", False):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
        SECURE_SSL_REDIRECT = True
        SESSION_COOKIE_SECURE = True
        CSRF_COOKIE_SECURE = True
        SECURE_HSTS_SECONDS = 31536000
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True
        SECURE_HSTS_PRELOAD = True


# ------------------------------------------------------------------
# FAYL YUKLASH CHEKLOVI
# Murojaat .docx fayli brauzerda o'qiladi, lekin formalar orqali katta
# ma'lumot kelishining oldi olinadi.
# ------------------------------------------------------------------
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024      # 5 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# ------------------------------------------------------------------
# LOGLASH
# Xatolar konsolga va (production'da) fayldan tashqari joyga yozilmaydi —
# xodim ko'rgan xatolikni keyin topib bo'ladi.
# ------------------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
LOG_FAYLGA = env_bool("DJANGO_LOG_FAYLGA", not DEBUG)
if LOG_FAYLGA:
    LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "toliq": {
            "format": "{asctime} [{levelname}] {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "konsol": {
            "class": "logging.StreamHandler",
            "formatter": "toliq",
        },
        **({
            "fayl": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(LOG_DIR / "ihma.log"),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
                "formatter": "toliq",
            }
        } if LOG_FAYLGA else {}),
    },
    "root": {
        "handlers": ["konsol"] + (["fayl"] if LOG_FAYLGA else []),
        "level": env("DJANGO_LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django.request": {
            "handlers": ["konsol"] + (["fayl"] if LOG_FAYLGA else []),
            "level": "ERROR",
            "propagate": False,
        },
    },
}
