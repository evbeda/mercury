release: python manage.py migrate
web: gunicorn mercury_site.wsgi --log-file -
worker: celery -A mercury_app worker --beat
