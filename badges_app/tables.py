import django_tables2 as tables
from mercury_app.models import Attendee
from django.utils.html import format_html
from django_tables2.utils import Accessor
from django.utils.translation import ugettext_lazy as _
from mercury_app.strings import (
    string_order,
    event_delete,
    event_with_badge,
    event_with_merch,
)
from badges_app.strings import string_printer
from badges_app.utils import get_html_combo_box


class PrintingTable(tables.Table):
    actions = tables.Column(
        verbose_name=_('Actions'),
        orderable=False,
        empty_values=(),
    )
    first_name = tables.Column(
        verbose_name=_('Full Name'),
        empty_values=(),
    )
    order_eb_order_id = tables.Column(
        verbose_name=('Order ID'),
        accessor=Accessor('order.eb_order_id'),
        orderable=False,
    )

    def render_first_name(self, value, record):
        return '{} {}'.format(record.first_name, record.last_name)

    def render_actions(self, value, record):
        return format_html(
            string_printer.format(
                record.order.event.eb_event_id,
                record.eb_attendee_id,
                get_html_combo_box(record.order.event.id),
            )
        )

    class Meta:
        model = Attendee
        template_name = 'django_tables2/bootstrap4.html'
        exclude = (
            'id',
            'order',
            'last_name',
            'eb_attendee_id',
            'barcode',
            'barcode_url',
            'checked_in',
        )
        sequence = (
            'first_name',
            'checked_in_time',
            'order_eb_order_id',
            'actions',
        )
        show_header = True
