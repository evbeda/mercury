import django_tables2 as tables
from mercury_app.models import Order, Transaction, Attendee, Event
from django.utils.html import format_html
from fontawesome.fields import IconField
from django.utils.safestring import mark_safe


class EventTable(tables.Table):
    name = tables.Column(verbose_name='Event name')
    pretty_date = tables.Column(
        verbose_name='Start Date',
        empty_values=(),
    )
    actions = tables.Column(
        verbose_name='Actions',
        orderable=False,
        empty_values=(),
    )

    def render_actions(self, value, record):
        if record.is_processing == True:
            return format_html('<div class="row"><div class="col">Processing...</div><div class="col"><a href="/"><i class="material-icons md-18 icon-black">refresh</i></a></div>')
        else:
            return format_html('<div class="row"><div class="col"><a href="/event/{}/summary/"><i class="material-icons md-18 icon-black">search</i></a></div><div class="col"><a href="/event/{}/delete/"><i class="material-icons md-18 icon-gray">delete_outline</i></a></div>'.format(record.eb_event_id, record.eb_event_id))

    def render_pretty_date(self, value, record):
        return record.date_start_date_utc

    class Meta:
        model = Event
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields = ('name', 'actions')
        sequence = ('name', 'pretty_date', 'actions',)
        show_header = True


class OrderTable(tables.Table):
    state_image = tables.Column(
        verbose_name='',
        orderable=False,
        empty_values=(),
        attrs={'td': {'width': '10px', 'padding-right': '5px', 'class': 'dot-padding'}},
    )
    actions = tables.Column(
        verbose_name='Actions',
        orderable=False,
        empty_values=(),
    )
    full_name = tables.Column(
        verbose_name='Full Name',
        empty_values=(),
    )

    def render_state_image(self, value, record):
        status = record.order.merch_status
        if status == 'CO':
            return format_html('<span class="dot-co"></span>')
        elif status == 'PA':
            return format_html('<span class="dot-pa"></span>')
        else:
            return format_html('<span class="dot-pe"></span>')

    def render_full_name(self, value, record):
        return '{} {}'.format(record.first_name, record.last_name)

    def render_actions(self, value, record):
        return format_html('<div class="row text-center"><div class="col-12 text-center"><a id="hip_not_underline" href="/view_order/{}/{}/"><i class="material-icons md-18 icon-gray">info</i></a></div></div>'.format(record.order.id, record.eb_attendee_id))

    class Meta:
        model = Attendee
        template_name = 'custom_table_with_header.html'
        fields = ('order.eb_order_id',)
        sequence = ('state_image', 'full_name', 'order.eb_order_id', 'actions',)
        show_header = False


class TransactionTable(tables.Table):
    date = tables.Column(verbose_name='Date')
    from_who = tables.Column(verbose_name='Team member')
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
