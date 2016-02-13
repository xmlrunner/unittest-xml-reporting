
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = 'not-a-secret'
DEBUG = True
ALLOWED_HOSTS = []
INSTALLED_APPS = ['app', 'app2']
MIDDLEWARE_CLASSES = []
ROOT_URLCONF = 'example.urls'
TEMPLATES = []
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'

# The settings we care about for xmlrunner.
# They are commented out because we will use settings.configure() in tests.

# TEST_RUNNER = 'xmlrunner.extra.djangotestrunner.XMLTestRunner'
# TEST_OUTPUT_FILE_NAME = 'results.xml'
# TEST_OUTPUT_VERBOSE = 2
