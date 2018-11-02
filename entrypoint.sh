#!/bin/bash
#python manage.py test
rm -r /app/static
python manage.py collectstatic
python manage.py makemigrations
python manage.py migrate
gunicorn --bind 0.0.0.0:8000 mercury_site.wsgi
exec "$@"
