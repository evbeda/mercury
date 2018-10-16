from django_filters import FilterSet, CharFilter, ChoiceFilter
from mercury_app.models import Order, MERCH_STATUS


class OrderFilter(FilterSet):

    name = CharFilter(lookup_expr='icontains', label='Name')
    eb_order_id = CharFilter(lookup_expr='icontains', label='Order ID')
    merch_status = ChoiceFilter(choices=MERCH_STATUS, empty_label='All Orders')

    class Meta:
        model = Order
        exclude = {
            'event',
            'changed',
            'created',
            'status',
            'email',
        }
