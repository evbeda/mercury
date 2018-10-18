import django_tables2 as tables
from mercury_app.models import Order, Transaction
from django.utils.html import format_html
from fontawesome.fields import IconField
from django.utils.safestring import mark_safe



class OrderTable(tables.Table):
    state_image = tables.Column(
        verbose_name='',
        orderable=False,
        empty_values=(),
        attrs={'td': {'width': '10px', 'padding-right': '5px', 'class': 'dot-padding'}},
    )
    eb_order_id = tables.Column(verbose_name='Order ID')
    actions = tables.Column(
        verbose_name='Actions',
        orderable=False,
        empty_values=(),
    )

    def render_state_image(self, value, record):
        status = record.merch_status
        if status == 'CO':
            return format_html('<span class="dot-co"></span>')
        elif status == 'PA':
            return format_html('<span class="dot-pa"></span>')
        else:
            return format_html('<span class="dot-pe"></span>')

    def render_actions(self, value, record):
        return format_html('<div class="row text-center"><div class="col-12 text-center"><a id="hip_not_underline" href="/view_order/{}/"><i class="material-icons md-18 icon-gray">info</i></a></div></div>'.format(record.id))

    class Meta:
        model = Order
        template_name = 'custom_table_with_header.html'
        fields = ('name', 'eb_order_id',)
        sequence = ('state_image', 'name', 'eb_order_id', 'actions',)
        show_header = False


class TransactionTable(tables.Table):
    date = tables.Column(verbose_name='Date')
    from_who = tables.Column(verbose_name='Responsible')
    notes = tables.Column(verbose_name='Comment')
    operation_type = tables.Column(verbose_name='Operation Type')
    merchandise = tables.Column(verbose_name='Item')

    def render_merchandise(self, value, record):
        return '{} - {}'.format(record.merchandise.name, record.merchandise.item_type)

    class Meta:
        model = Transaction
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields = ('date', 'from_who', 'notes', 'operation_type','merchandise')
        sequence = ('operation_type','merchandise', 'date', 'from_who', 'notes',)

