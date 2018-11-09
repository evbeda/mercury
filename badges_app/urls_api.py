from django.conf.urls import url
from badges_app.views import (
    PrinterView,
    PrinterQueues,
    JobState,
    ConfigurePrinter,
)

urlpatterns = [
    url(r'^printer/(?P<key>.*)/configure/$', ConfigurePrinter.as_view()),
    url(r'^printer/(?P<key>.*)/queue/$', PrinterQueues.as_view()),
    url(r'^printer/(?P<key>.*)/job/(?P<job_id>.*)/$', JobState.as_view()),
    url(r'^printer/(?P<key>.*)/$', PrinterView.as_view()),
]
