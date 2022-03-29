#!/bin/sh
python manage.py runserver 0.0.0.0:8080
python manage.py migrate
python manage.py collectstatic   

exec "$@"
