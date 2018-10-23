from django.conf.urls import url
from mercury_app.views import (
    Home,
    SelectEvents,
    ListItemMerchandising,
    accept_webhook,
    checkin_webhook,
    Summary,
    FilteredOrderListView,
    ScanQRView,
    DeleteEvents,
    TransactionListView,
)


urlpatterns = [
    url(r'event/(?P<event_id>\d+)/summary/$', Summary.as_view(template_name='summary.html'), name='summary'),
    url(r'event/(?P<event_id>\d+)/scanqr/$', ScanQRView.as_view(template_name='scanqr.html'), name='scanqr'),
    url(r'event/(?P<event_id>\d+)/delete/$', DeleteEvents.as_view(template_name='delete.html'), name='delete'),
    url(r'^webhook-point/',accept_webhook,name='accept_webhook'),
    url(r'^webhook-checkin/',checkin_webhook,name='checkin_webhook'),
    url(r'view_order/(?P<order_id>\d+)/$', ListItemMerchandising.as_view(template_name='list_item_mercha.html'), name='item_mercha'),
    url(r'view_order/(?P<order_id>\d+)/transactions/$', TransactionListView.as_view(), name='transactions'),
    url(r'event/(?P<event_id>\d+)/orders/$', FilteredOrderListView.as_view(), name='orders'),
    url(r'^select_events/', SelectEvents.as_view(template_name='select_events.html'), name='select_events'),
    url(r'^(?P<message>[a-zA-Z]+)?', Home.as_view(template_name='index.html'), name='index'),
]
