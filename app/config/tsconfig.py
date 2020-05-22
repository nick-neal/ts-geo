import os

### APP CONFIG ###

APP_NAME = "ts-geo"
APP_VERSION = "ALPHA 20.9.0"
if 'APP_ENV' in os.environ:
    APP_ENV = os.environ['APP_ENV']
else:
    APP_ENV = "DEV" # DEV, TEST, PROD
APP_HOST = '0.0.0.0'
APP_PORT = 4080
APP_DEBUG = True
