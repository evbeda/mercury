# Use base python image with python 3.6.6
FROM python:3.6.6

# Install postgres client to check status of db cotainers
# This peace of script taken from Django's official repository
# It is deprecated in favor of the python repository
# https://hub.docker.com/_/django/
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
RUN mkdir /app
WORKDIR /app

# Add requirements.txt to the image
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy
COPY ./src /app

# Used in wait-for-postgres.sh to connect to PostgreSQL
# Needs to be updated, repeats in docker-compose
ENV POSTGRES_USER postgres
ENV POSTGRES_PASSWORD postgres
ENV POSTGRES_DB postgres
ENV REDIS_URL redis://redis:6379
ENV DATABASE_URL postgres://postgres:postgres@db:5432/postgres
ENV URL_LOCAL xxxx.domain
ENV SOCIAL_AUTH_EVENTBRITE_KEY xxxx
ENV SOCIAL_AUTH_EVENTBRITE_SECRET xxxx
ENV EMAIL_HOST xxxx
ENV EMAIL_PORT 587
ENV EMAIL_HOST_USER xxxx
ENV EMAIL_HOST_PASSWORD xxxx
