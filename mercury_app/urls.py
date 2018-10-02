from django.conf.urls import url
from mercury_app.views import Home, SelectEvents, OrderList, ListItemMerchandising, accept_webhook


urlpatterns = [
	url(r'^webhook-point/',accept_webhook,name='accept_webhook'),
	url(r'view_order/(?P<order_id>\d+)/$', ListItemMerchandising.as_view(template_name='list_item_mercha.html'), name='item_mercha'),
    url(r'event/(?P<event_id>\d+)/orders/$', OrderList.as_view(template_name='orders.html'), name='orders'),
    url(r'^select_events/', SelectEvents.as_view(template_name='select_events.html'), name='select_events'),
    url(r'^(?P<message>[a-zA-Z]+)?', Home.as_view(template_name='index.html'), name='index'),
]
