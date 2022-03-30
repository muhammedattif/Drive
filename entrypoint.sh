#!/bin/sh
python manage.py migrate 
python manage.py collectstatic   
celery -A cloud worker -l info -D
python manage.py runserver 0.0.0.0:8080

exec "$@"
