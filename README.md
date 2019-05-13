# Gemini: Mercury on docker

## CI

Travis
[![Build Status](https://travis-ci.org/evbeda/mercury.svg?branch=master)](https://travis-ci.org/evbeda/mercury)

Coverage
[![Coverage Status](https://coveralls.io/repos/github/evbeda/mercury/badge.svg?branch=master)](https://coveralls.io/github/evbeda/mercury?branch=master)

## Versions

App | Version
--- | ---
Celery | 4.2.1
Django | 1.11
Nginx  | 1.15.5
Python | 3.6.6
Redis  | 4.0.11

## What is included

- Celery as a way of running async tasks
- Django as the main Python application
- Nginx as a web server
- PostgreSQL as a Django database
- Redis as a queue for Redis

## Docker Compose containers

- db (Django PostgreSQL database)
- django (Django application)
- redis (Redis result backend for Celery)
- web-nginx (Web server)
- worker (Celery worker)

# Setup & Run

## Setup

 - Change the envirorment variables in the `Dockerfile` as you see fit
 - Generate SSL certificates for nginx ([Self Signed](https://www.digitalocean.com/community/tutorials/how-to-create-a-self-signed-ssl-certificate-for-nginx-in-ubuntu-16-04) or [Let's encrypt](https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-16-04))
 - Place the certificate files in the root folder (`./cert.crt` and `./cert.key`)
 - (Optional) Use [ngrok](https://ngrok.com/) to debug webhooks locally

## Build

    docker-compose build

## Start containers

    docker-compose up

Run in the background

    docker-compose up -d

## Shell into container

    docker-compose exec [container] bash -l

## Run tests

    docker-compose run django python manage.py test

## See logs

    docker-compose logs [container]

## Run from local machine

    # Install requirements
    python3 -m venv env
    source env/bin/activate
    pip install -r requirements.txt

    # Set the envirorment variables described in Dockerfile
    # Temporary:
    export VARIABLE=VALUE
    # Static:
    echo 'export VARIABLE=VALUE' >> ~/.bashrc

    # Move to 'src' folder
    cd src

    # Run worker
    celery -A mercury_app worker

    # Start application on another console
    python manage.py runserver
