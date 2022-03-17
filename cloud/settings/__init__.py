import environ
env = environ.Env()
# reading .env file
environ.Env.read_env()

CELERY_BROKER_URL = f'redis://{env("REDIS_HOST")}:{int(env("REDIS_PORT"))}'
CELERY_IMPORTS = ("file.tasks", )