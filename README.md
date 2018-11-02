# Gemini: Mercury on docker


## Versions

App | Version
--- | ---
Python | 3.6.6
Django | 1.11
Celery | 4.2.1
Nginx  | 1.15.5

## What is included

- PostgreSQL as a Django database
- Redis for celery
- Nginx as a webserver - only HTTPS enabled

## Docker Compose containers

- db (Django PostgreSQL database)
- redis (Redis result backend for Celery)
- django (Django application)
- worker (Celery worker)
- web-nginx (Webserver)

# Setup & Run

## Run inside docker

    # Envirorment variables
    set the required env variables in the Dockerfile

    # SSL Certificates
    provide the certificate and private key with the following naming: "certificate.key" and "certificate.crt" in .src/cert/

    # Build docker containers
    docker-compose build

    # Run
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
    celery worker -A mercury_app -Q default -n default@%h

    # Start application on another console
    python manage.py runserver
