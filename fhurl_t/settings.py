DEBUG = True

DATABASE_ENGINE = 'django.db.backends.sqlite3'
DATABASE_NAME = '/tmp/fhurl.db'
DATABASES = {
    'default': {
        'ENGINE': DATABASE_ENGINE,
        'NAME': DATABASE_NAME,
    },
}
ROOT_URLCONF = 'fhurl_t.urls'

INSTALLED_APPS = ['fhurl_t']

SECRET_KEY = 'fhurlrocks'
TEST_RUNNER = 'django.test.simple.DjangoTestSuiteRunner'

