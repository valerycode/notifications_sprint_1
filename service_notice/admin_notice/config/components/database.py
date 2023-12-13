import os


DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DJANGO_ADMIN_NOTICE_DB_ENGINE'),
        'NAME': os.environ.get('PG_ADMIN_NOTICE_DB_NAME'),
        'USER': os.environ.get('PG_ADMIN_NOTICE_USER'),
        'PASSWORD': os.environ.get('PG_ADMIN_NOTICE_PASSWORD'),
        'HOST': os.environ.get('PG_ADMIN_NOTICE_DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('PG_ADMIN_NOTICE_DB_PORT', 5436),
    }
}
