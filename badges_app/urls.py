from django.conf.urls import url
from badges_app.views import PrinterView, PrinterQueues, JobState

urlpatterns = [
	url(r'^printer/(?P<printer_id>\d+)/key/(?P<key>.*)/queue/$', PrinterQueues.as_view()),
	url(r'^printer/(?P<printer_id>\d+)/key/(?P<key>.*)/job/(?P<job_id>\d+)/$', JobState.as_view()),
    url(r'^printer/(?P<printer_id>\d+)/key/(?P<key>.*)/$', PrinterView.as_view()),
]
