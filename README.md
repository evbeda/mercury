# Gemini: Mercury on docker


## Versions

App | Version
--- | ---
Python | 3.6.6
Django | 1.11
Celery | 4.2.1

## What is included

- PostgreSQL as a Django database
- Redis for celery

## Docker Compose containers

- db (Django PostgreSQL database)
- redis (Redis result backend for Celery)
- web (Django application)
- worker (Celery worker)

# Setup & Run

## Run inside docker

    # build docker containers
    docker-compose build

    # option 1: run 1 instance of web
    docker-compose up

You can also run manage.py commands using docker environment, for example tests.

    docker-compose run web python ./manage.py test

See docker's logs

    docker-compose logs --tail 5

## Run from local machine

    # Install requirements
    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt

    # Move to 'src' folder
    cd src

    # Run worker
    celery -A mercury_app worker --beat

    # Start application on another console
    python manage.py runserver
