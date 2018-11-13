from django.conf.urls import url
from badges_app.views import (
    FilteredPrintingList,
    RedisPrinterOrder,
    CreatePrinter,
    ListPrinter,
    DeletePrinter,
    ResetPrinter,
    SetAutoPrinter,
    CustomLabel,
)

urlpatterns = [
    url(r'event/(?P<event_id>\d+)/printing_list/$', FilteredPrintingList.as_view(), name='printing_list'),
    url(r'event/(?P<event_id>\d+)/attendee/(?P<attendee_id>[\d\-]+|)\/print/$', RedisPrinterOrder.as_view(), name='printer_order'),
    url(r'event/(?P<event_id>\d+)/configuration/printer/list/$', ListPrinter.as_view(), name='printer_list'),
    url(r'event/(?P<event_id>\d+)/configuration/printer/create/$', CreatePrinter.as_view(), name='create_printer'),
    url(r'event/(?P<event_id>\d+)/configuration/printer/(?P<printer_id>\d+)/delete/$', DeletePrinter.as_view(), name='delete_printer'),
    url(r'event/(?P<event_id>\d+)/configuration/printer/(?P<printer_id>\d+)/reset/$', ResetPrinter.as_view(), name='reset_printer'),
    url(r'event/(?P<event_id>\d+)/configuration/auto_print/$', SetAutoPrinter.as_view(), name='auto_print'),
    url(r'event/(?P<event_id>\d+)/label/$', CustomLabel.as_view(), name='custom_label'),
]
