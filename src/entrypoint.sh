#!/bin/bash
#python manage.py test
rm -r /app/static
python manage.py collectstatic
python manage.py makemigrations
python manage.py migrate
#python manage.py runserver_plus 0.0.0.0:443 --cert /temp/cert
#python manage.py runsslserver 0.0.0.0:443 --certificate ./cert/cert.pem --key ./cert/privekey.pem
python manage.py runsslserver 0.0.0.0:443 --certificate cert.pem --key privkey.pem
exec "$@"
