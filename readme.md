# Media Directory

All media files saved in /media in the base directory (Don't serve it with Nginx)


# Steps


## 1- Install the requirements

```bash
pip install -r requirements.txt
```

## 2- Apply migrations

```bash
python manage.py migrate
```

## 3- Create Super User

```bash
python manage.py createsuperuser
```

## 4- Update Settings Configurations

Configure Redis server, port, and DB Settings

## 5- Start Celery Worker

Run this command in the project's main directory
```
celery -A cloud worker -l info
```