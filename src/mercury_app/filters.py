from django_filters import FilterSet, CharFilter, ChoiceFilter
from mercury_app.models import Attendee, MERCH_STATUS
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _


class OrderFilter(FilterSet):

    full_name = CharFilter(label=_('Name'), method='search_by_full_name')
    eb_order_id = CharFilter(label=_('Order ID'), field_name='order__eb_order_id', lookup_expr='icontains')
    merch_status = ChoiceFilter(field_name='order__merch_status',choices=MERCH_STATUS, empty_label='All Orders')

    def search_by_full_name(self, qs, name, value):
        for term in value.split():
            qs = qs.filter(Q(first_name__icontains=term) | Q(last_name__icontains=term))
        return qs

    class Meta:
        model = Attendee
        fields = ['full_name', 'eb_order_id', 'merch_status']
        exclude = {
            'event',
            'changed',
            'created',
            'status',
            'email',
        }
