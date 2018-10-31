from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from mercury_app.views import (
    Home,
    SelectEvents,
    ListItemMerchandising,
    Summary,
    FilteredOrderListView,
    ScanQRView,
    DeleteEvents,
    TransactionListView,
    ActivateLanguageView,
    Webhook,
)


urlpatterns = [
    url(r'language/activate/(?P<language_code>[a-z]+)/', ActivateLanguageView.as_view(), name='activate_language'),
    url(r'event/(?P<event_id>\d+)/summary/$', Summary.as_view(template_name='summary.html'), name='summary'),
    url(r'event/(?P<event_id>\d+)/scanqr/$', ScanQRView.as_view(template_name='scanqr.html'), name='scanqr'),
    url(r'event/(?P<event_id>\d+)/delete/$', DeleteEvents.as_view(template_name='delete.html'), name='delete'),
    url(r'^webhook-order/',csrf_exempt(Webhook.as_view()),name='neworder_webhook'),
    url(r'^webhook-checkin/',csrf_exempt(Webhook.as_view()),name='checkin_webhook'),
    url(r'view_order/(?P<order_id>\d+)/transactions/$', TransactionListView.as_view(), name='transactions'),
    url(r'view_order/(?P<order_id>\d+)\/(?P<attendee_id>[\d\-]+|)\/?$', ListItemMerchandising.as_view(template_name='list_item_mercha.html'), name='item_mercha'),
    url(r'event/(?P<event_id>\d+)/orders/$', FilteredOrderListView.as_view(), name='orders'),
    url(r'^select_events/', SelectEvents.as_view(template_name='select_events.html'), name='select_events'),
    url(r'^(?P<message>[a-zA-Z]+)?', Home.as_view(template_name='index.html'), name='index'),
]
