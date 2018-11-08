from django.conf.urls import url
from badges_app.views import (
    FilteredPrintingList,
    RedisPrinterOrder,
)

urlpatterns = [
    url(r'event/(?P<event_id>\d+)/printing_list/$', FilteredPrintingList.as_view(), name='printing_list'),
    url(r'event/(?P<event_id>\d+)/attendee/(?P<attendee_id>\d+)/print/$', RedisPrinterOrder.as_view(), name='printer_order'),
]
