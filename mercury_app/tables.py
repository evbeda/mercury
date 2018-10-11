import django_tables2 as tables
from mercury_app.models import Order
from django.utils.html import format_html
from fontawesome.fields import IconField
from django.utils.safestring import mark_safe



class OrderTable(tables.Table):
    eb_order_id = tables.Column(verbose_name='Order ID')
    merch_status = tables.Column(verbose_name='Order Status')
    actions = tables.Column(
        verbose_name='Actions',
        orderable=False,
        empty_values=(),
        attrs={"th": {"style": "text-align: justify"}},
    )

    def render_actions(self, value, record):
        return format_html('<ul class="fa-ul fa-2x row"><a href="/view_order/{}/"><li><i class="fa fa-eye"></i></li></a> &nbsp &nbsp &nbsp <a href=""><li> <i class="fa fa-trash"></i> </li></ul></a>'.format(record.id))

    class Meta:
        model = Order
        template_name = 'django_tables2/bootstrap4.html'
        fields = ('name', 'eb_order_id', 'merch_status',)
