import environ
env = environ.Env()
# reading .env file
environ.Env.read_env()

CELERY_BROKER_URL = f'redis://{env("REDIS_HOST")}:6379'
CELERY_IMPORTS = ("file.tasks", "drive.tasks")