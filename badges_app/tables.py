import django_tables2 as tables
from mercury_app.models import Attendee
from django.utils.html import format_html
from django_tables2.utils import Accessor
from django.utils.translation import ugettext_lazy as _
from mercury_app.strings import (
    string_order,
    string_printer,
    event_delete,
    event_with_badge,
    event_with_merch,
)


class PrintingTable(tables.Table):
    actions = tables.Column(
        verbose_name=_('Actions'),
        orderable=False,
        empty_values=(),
    )
    full_name = tables.Column(
        verbose_name=_('Full Name'),
        empty_values=(),
    )
    order_eb_order_id = tables.Column(
        verbose_name=('Order ID'),
        accessor=Accessor('order.eb_order_id'),
    )

    def render_full_name(self, value, record):
        return '{} {}'.format(record.first_name, record.last_name)

    def render_actions(self, value, record):
        return format_html(
            string_printer.format(
                record.order.event.eb_event_id,
                record.eb_attendee_id,
            )
        )

    class Meta:
        model = Attendee
        template_name = 'django_tables2/bootstrap4.html'
        exclude = (
            'id',
            'order',
            'first_name',
            'last_name',
            'eb_attendee_id',
            'barcode',
            'barcode_url',
            'checked_in_time',
        )
        sequence = (
            'full_name',
            'checked_in',
            'order_eb_order_id',
            'actions',
        )
        show_header = True
