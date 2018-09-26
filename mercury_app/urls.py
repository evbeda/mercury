from django.conf.urls import url
from mercury_app.views import Home, SelectEvents

urlpatterns = [
    url(r'^select_events/', SelectEvents.as_view(template_name='select_events.html'), name='select_events'),
    url(r'^(?P<message>[a-zA-Z]+)?', Home.as_view(template_name='index.html'), name='index'),
]
