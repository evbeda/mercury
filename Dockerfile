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

ENV POSTGRES_USER postgres
ENV POSTGRES_PASSWORD postgres
ENV POSTGRES_DB postgres
ENV REDIS_URL redis://redis:6379
ENV DATABASE_URL postgres://postgres:postgres@db:5432/postgres
# This is the public URL that's used for webhooks
# If you are developing locally ngrok generated url goes here
ENV URL_LOCAL https://MY_SERVER_NAME
ENV SOCIAL_AUTH_EVENTBRITE_KEY APP_KEY
ENV SOCIAL_AUTH_EVENTBRITE_SECRET OAUTH_TOKEN
ENV EMAIL_HOST MY_SMTP_SERVER_HOST
ENV EMAIL_PORT MY_SMTP_SERVER_PORT
ENV EMAIL_HOST_USER MY_EMAIL_USER
ENV EMAIL_HOST_PASSWORD MY_EMAIL_PASSWORD

# Create app directory
RUN mkdir /app
WORKDIR /app

# Add requirements.txt to the image
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy
COPY ./src /app

EXPOSE 8000