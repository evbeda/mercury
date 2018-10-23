from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mercury_site.settings')

app = Celery('mercury')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('mercury_app.app_settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# app.conf.update(
#     BROKER_URL=os.environ['REDIS_URL'],
#     CELERY_RESULT_BACKEND=os.environ['REDIS_URL'],
# )
app.conf.update(
    BROKER_URL=os.environ['REDIS_URL'],
    CELERY_RESULT_BACKEND=os.environ['REDIS_URL'],
)


@app.task(bind=True)
def debug_task(self):
    print('Reqiest: {0!r}'.format(self.request))
