import django_tables2 as tables
from mercury_app.models import Order, Transaction, Attendee, Event
from django.utils.html import format_html
from fontawesome.fields import IconField
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class EventTable(tables.Table):
    name = tables.Column(verbose_name=_('Event name'), localize=True)
    pretty_date = tables.Column(
        verbose_name=_('Start Date'),
        localize=True,
        empty_values=(),
    )
    actions = tables.Column(
        verbose_name=_('Actions'),
        localize=True,
        orderable=False,
        empty_values=(),
    )

    def render_actions(self, value, record):
        if record.is_processing == True:
            return format_html('<div class="row"><div class="col">Processing...</div><div class="col"><a href="/"><i class="material-icons md-18 icon-black">refresh</i></a></div>')
        else:
            return format_html('<div class="row"><div class="col"><div><a href="/event/{}/summary/"><i class="eds-vector-image eds-icon--small" data-spec="icon" aria-hidden="true"><svg id="eds-icon--magnifying-glass_svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path id="eds-icon--magnifying-glass_base" fill-rule="evenodd" clip-rule="evenodd" d="M17 14.9l-.7.7-1.2-1.2c1.2-1.3 1.9-3 1.9-4.9C17 5.4 13.6 2 9.5 2S2 5.4 2 9.5 5.4 17 9.5 17c1.9 0 3.6-.7 4.9-1.9l1.2 1.2-.7.7 5 5 2.1-2.1-5-5zM3 9.5C3 5.9 5.9 3 9.5 3S16 5.9 16 9.5 13.1 16 9.5 16 3 13.1 3 9.5zM16.3 17l.7-.7 3.6 3.6-.7.7-3.6-3.6z"/></svg></i></a></div></div><div class="col"><div><a href="/event/{}/delete/"><i class="eds-vector-image eds-icon--small" data-spec="icon" aria-hidden="true"><svg id="eds-icon--trash_svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path id="eds-icon--trash_base" fill-rule="evenodd" clip-rule="evenodd" d="M5 6h1v15H5V6zm13 0h1v15h-1V6zM5 21h14v1H5v-1z"/><path id="eds-icon--trash_top" fill-rule="evenodd" clip-rule="evenodd" d="M15 4V2H9v2H4v1h16V4h-5zm-1 0h-4V3h4v1z"/><g id="eds-icon--trash_lines" fill-rule="evenodd" clip-rule="evenodd"><path d="M9 8h1v11H9zm5 0h1v11h-1z"/></g></svg></i></a></div></div></div>'.format(record.eb_event_id, record.eb_event_id))

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
        verbose_name=_('Actions'),
        orderable=False,
        empty_values=(),
    )
    full_name = tables.Column(
        verbose_name=_('Full Name'),
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
        # return format_html('<div class="row text-center"><div class="col-12 text-center"><a id="hip_not_underline" href="/view_order/{}/{}/"><i class="material-icons md-18 icon-gray">info</i></a></div></div>'.format(record.order.id, record.eb_attendee_id))
        return format_html('<div class="row text-center"><div class="col-12 text-center"><div class=""><a id="hip_not_underline" href="/view_order/{}/{}/"><i class="eds-vector-image eds-icon--small" data-spec="icon" aria-hidden="true"><svg id="eds-icon--eye_svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path id="eds-icon--eye_base" fill-rule="evenodd" clip-rule="evenodd" fill="#231F20" d="M11.9 6.5C6.4 6.5 2 12.7 2 12.7s4.4 6.2 9.9 6.2 9.9-6.2 9.9-6.2-4.4-6.2-9.9-6.2zm0 11.3c-3.9 0-7.4-3.6-8.6-5.1 1.2-1.5 4.7-5.1 8.6-5.1 3.9 0 7.4 3.6 8.6 5.1-1.2 1.5-4.7 5.1-8.6 5.1"/><path id="eds-icon--eye_circle" fill-rule="evenodd" clip-rule="evenodd" fill="#231F20" d="M11.9 9.1c-1.9 0-3.5 1.6-3.5 3.6s1.5 3.6 3.5 3.6 3.5-1.6 3.5-3.6-1.6-3.6-3.5-3.6zm0 6.1c-1.4 0-2.5-1.1-2.5-2.6 0-1.4 1.1-2.6 2.5-2.6s2.5 1.1 2.5 2.6-1.1 2.6-2.5 2.6z"/></svg></i></a></div></div></div>'.format(record.order.id, record.eb_attendee_id))


    class Meta:
        model = Attendee
        template_name = 'custom_table_with_header.html'
        fields = ('order.eb_order_id',)
        sequence = ('state_image', 'full_name', 'order.eb_order_id', 'actions',)
        show_header = False


class TransactionTable(tables.Table):
    date = tables.Column(verbose_name=_('Date'))
    from_who = tables.Column(verbose_name=_('Team member'))
    notes = tables.Column(verbose_name=_('Comment'))
    operation_type = tables.Column(verbose_name=_('Operation Type'))
    merchandise = tables.Column(verbose_name=_('Item'))

    def render_merchandise(self, value, record):
        return '{} - {}'.format(record.merchandise.name, record.merchandise.item_type)

    class Meta:
        model = Transaction
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields = ('date', 'from_who', 'notes', 'operation_type','merchandise')
        sequence = ('operation_type','merchandise', 'date', 'from_who', 'notes',)
