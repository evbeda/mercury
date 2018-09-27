# mercury  

Travis  
[![Build Status](https://travis-ci.org/evbeda/mercury.svg?branch=master)](https://travis-ci.org/evbeda/mercury)  

Coverage  
[![Coverage Status](https://coveralls.io/repos/github/evbeda/mercury/badge.svg?branch=master)](https://coveralls.io/github/evbeda/mercury?branch=master)  

Getting Started  
We assume that you have already created and activated a virtual environment  

clone  
`git clone https://github.com/evbeda/mercury.git`

install requeriments  

`(env) $ pip install -r requeriments.txt`

set environment  

`(env) $ export DATABASE=postgres://user:password@localhost:5432/db`  
`(env) $ export SOCIAL_AUTH_EVENTBRITE_SECRET=secret`  
`(env) $ export SOCIAL_AUTH_EVENTBRITE_KEY=key`  

run local server  

`(env) $ python manage.py runserver`  

login with Eventbrite in your localhost  

http://localhost:8000/  







