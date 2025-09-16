from  .settings import *

DATABASES = {
     "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "rcp_test",
        "USER": "postgres",
        "PASSWORD": "admin123",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
