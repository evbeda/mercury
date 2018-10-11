import django_tables2 as tables
from mercury_app.models import Order
from django.utils.html import format_html


class OrderTable(tables.Table):
    eb_order_id = tables.Column(verbose_name='Order ID')
    merch_status = tables.Column(verbose_name='Order Status')
    actions = tables.Column(
        verbose_name='Actions',
        orderable=False,
        empty_values=()
    )

    def render_actions(self, value, record):
        return format_html('<a href="/view_order/{}/" class="btn btn-outline-success">View</a>'.format(record.id))

    class Meta:
        model = Order
        template_name = 'django_tables2/bootstrap4.html'
        fields = ('name', 'eb_order_id', 'merch_status',)
