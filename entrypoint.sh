#!/bin/bash
#python manage.py test
rm -r /app/static
python manage.py collectstatic
python manage.py makemigrations
python manage.py migrate
gunicorn mercury_site.wsgi --bind=0.0.0.0:8000 --log-file -
exec "$@"
