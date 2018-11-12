from django.views.generic.base import TemplateView, View
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404, render
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseServerError,
)
from django.contrib import messages
from django_tables2 import SingleTableMixin, SingleTableView
import json
import re
from django.utils import timezone
from datetime import datetime
from mercury_app.models import (
    Event,
    Order,
    Merchandise,
    Transaction,
    Attendee,
    UserOrganization,
    Organization,
)
from badges_app.models import (Printer)
from django.utils import translation
from django.utils.translation import ugettext as _
from mercury_app.tables import OrderTable, TransactionTable, EventTable
from mercury_app.filters import OrderFilter
from mercury_app.filterview_fix import MyFilterView
from mercury_app.utils import (
    get_auth_token,
    redis_conn,
    get_events_mercha_and_badges,
    create_event_complete,
    get_api_organization,
    get_summary_orders,
    get_api_events_id,
    get_db_order_by_id,
    get_percentage_handed,
    get_api_order_barcode,
    get_events_for_organizations,
    get_db_event_by_id,
    get_db_events_by_organization,
    get_db_or_create_organization_by_id,
    get_db_items_left,
    get_db_attendee_from_barcode,
    create_userorganization_assoc,
    create_event_orders_from_api,
    create_event_from_api,
    update_attendee_checked_from_api,
    create_order_webhook_from_view,
    get_data,
    get_summary_types_handed,
    create_transaction,
    delete_events,
    EventAccessMixin,
    OrderAccessMixin,
    send_email_alert,
    get_merchas_for_email,
)
import dateutil.parser
from django.core.cache import cache
import pickle

class Webhook(View):

    def get(self, request, *args, **kwargs):
        return HttpResponseForbidden()

    def post(self, request, *args, **kwargs):
        context = {}
        try:
            json_info = json.loads(request.body)
            get_data.delay(
                json_info,
                request.build_absolute_uri('/')[:-1],
            )
            context['success'] = True
        except Exception:
            context['success'] = False
            return HttpResponseServerError()

        return render(
            request,
            'webhook.html',
            context=context,
            status=200,
        )


@method_decorator(login_required, name='dispatch')
class TransactionListView(SingleTableView, LoginRequiredMixin, EventAccessMixin):
    table_class = TransactionTable
    model = Transaction
    template_name = 'transaction.html'

    def get_queryset(self):
        return Transaction.objects.filter(merchandise__order__id=self.kwargs['order_id'])

    def get_context_data(self, **kwargs):
        context = super(SingleTableView, self).get_context_data(**kwargs)
        table = self.get_table(**self.get_table_kwargs())
        context[self.get_context_table_name(table)] = table
        table.paginate(page=self.request.GET.get('page', 1), per_page=10)
        order = Order.objects.get(id=self.kwargs['order_id'])
        context['order_name'] = '{} {}'.format(
            order.first_name, order.last_name)
        context['order_number'] = order.eb_order_id
        context['event_id'] = order.event.eb_event_id
        context['transaction_count'] = self.get_queryset().count()
        return context


@method_decorator(login_required, name='dispatch')
class ScanQRView(TemplateView, LoginRequiredMixin, OrderAccessMixin):
    template_name = 'scanqr.html'

    def get_context_data(self, **kwargs):
        context = super(ScanQRView, self).get_context_data(**kwargs)
        context['errormsg'] = self.request.session.get('qrerror')
        self.request.session['qrerror'] = None
        context['event_id'] = self.kwargs['event_id']
        context['organization_id'] = get_object_or_404(
            Event, eb_event_id=self.kwargs['event_id']).organization.eb_organization_id
        return context

    def post(self, request, *args, **kwargs):
        data = self.request.POST
        qrcode = data['code']
        org_id = data['org']
        event_id = data['event']
        token = get_auth_token(self.request.user)
        try:
            order = get_api_order_barcode(token, org_id, qrcode)
            eb_order_id = order.get('id')
            order_id = Order.objects.get(eb_order_id=eb_order_id).id
            attendee_id = get_db_attendee_from_barcode(
                qrcode, event_id).eb_attendee_id
            return redirect(reverse(
                'item_mercha',
                kwargs={
                    'order_id': order_id,
                    'attendee_id': attendee_id,
                },
            ))
        except TypeError:
            self.request.session[
                'qrerror'] = 'There was an error processing your QR Code (QR not valid).'

        except Exception as e:
            self.request.session['qrerror'] = 'There was an error processing your QR Code ({}).'.format(
                e)
        return redirect(reverse(
            'scanqr',
            kwargs={'event_id': event_id},
        ))


@method_decorator(login_required, name='dispatch')
class FilteredOrderListView(SingleTableMixin, MyFilterView, EventAccessMixin):
    table_class = OrderTable
    model = Attendee
    template_name = 'orderfilter.html'
    filterset_class = OrderFilter

    def get_queryset(self):
        return Attendee.objects.filter(
            order__event__eb_event_id=self.kwargs['event_id'],
            order__has_merchandise=True,
        ).order_by(
            'first_name',
            'last_name',
            'barcode',
        ).distinct('first_name', 'last_name')

    def get_table_kwargs(self):
        return {'template_name': 'custom_table_with_header.html'}

    def get_context_data(self, **kwargs):
        context = super(SingleTableMixin, self).get_context_data(**kwargs)
        table = self.get_table(**self.get_table_kwargs())
        context[self.get_context_table_name(table)] = table
        table.paginate(page=self.request.GET.get('page', 1), per_page=10)
        event = self.get_event()
        context['event_eb_event_id'] = event.eb_event_id
        context['event_name'] = event.name
        context['order_count'] = self.get_queryset().count()
        return context


@method_decorator(login_required, name='dispatch')
class ListItemMerchandising(TemplateView, LoginRequiredMixin, OrderAccessMixin):
    template_name = 'list_item_mercha.html'

    def get_context_data(self, **kwargs):
        context = super(ListItemMerchandising, self).get_context_data(**kwargs)
        order = get_db_order_by_id(self.kwargs['order_id'])
        merchandising_query_obj = self.get_merchandise()
        attendee_id = self.kwargs.get('attendee_id')
        if attendee_id is not (None or ''):
            try:
                attendee = Attendee.objects.get(eb_attendee_id=attendee_id)
                checked_in = attendee.checked_in
                if not checked_in:
                    checked_in = update_attendee_checked_from_api(
                        user=self.request.user,
                        eb_attendee_id=attendee_id
                    )
                if not checked_in:
                    messages.info(
                        self.request,
                        'This attendee has not checked in.',
                    )
            except Exception as e:
                messages.info(
                    self.request,
                    e,
                )
        context['merchandising'] = get_db_items_left(merchandising_query_obj)
        context['order'] = order
        return context

    def post(self, request, *args, **kwargs):
        data = self.request.POST
        keys = list(data)[:-2]
        merchases = []
        date = datetime.now(tz=timezone.utc)
        for item in keys:
            for qty in range(int(data[item])):
                mercha = Merchandise.objects.get(
                    eb_merchandising_id=item,
                )
                transaction = create_transaction(
                    self.request.user,
                    mercha,
                    data['comment'],
                    'unique',
                    'HA',
                    date,
                )
                merchases.append(mercha)
        merchandises, order_id, email = get_merchas_for_email(
            merchases, transaction.date)
        date = transaction.date.strftime("%Y-%m-%d %H:%M:%S")
        operation = transaction.operation_type

        send_email_alert.delay(json.dumps(merchandises),
                               email,
                               date,
                               operation,
                               order_id)
        event_id = Order.objects.get(
            id=self.kwargs['order_id']).event.eb_event_id
        return redirect(reverse(
            'orders',
            kwargs={'event_id': event_id},
        ))


@method_decorator(login_required, name='dispatch')
class Summary(TemplateView, LoginRequiredMixin, EventAccessMixin):

    template_name = 'summary.html'

    def get_context_data(self, **kwargs):
        context = super(Summary, self).get_context_data(**kwargs)
        event = self.get_event()
        order_ids = Order.objects.filter(
            has_merchandise=True,
            event=event,
        ).values_list('id', flat=True)
        context['data_handed_over_dont'] = get_percentage_handed(
            order_ids)
        context['data_tipes_handed'] = get_summary_types_handed(order_ids)
        context['data_orders'] = get_summary_orders(event)
        context['event'] = event
        return context


@method_decorator(login_required, name='dispatch')
class Home(SingleTableView, LoginRequiredMixin, ):
    template_name = 'index.html'
    table_class = EventTable
    model = Event

    def get_queryset(self):
        return get_db_events_by_organization(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(SingleTableView, self).get_context_data(**kwargs)
        create_order_webhook_from_view(self.request.user)
        table = self.get_table(**self.get_table_kwargs())
        table.paginate(page=self.request.GET.get('page', 1), per_page=10)
        context[self.get_context_table_name(table)] = table
        context['message'] = self.request.session.get('message')
        self.request.session['message'] = None
        context['event_count'] = self.get_queryset().count()
        return context


@method_decorator(login_required, name='dispatch')
class SelectEvents(TemplateView, LoginRequiredMixin):
    template_name = 'select_events.html'

    def get_context_data(self, **kwargs):
        context = super(SelectEvents, self).get_context_data(**kwargs)
        token = get_auth_token(self.request.user)
        organizations = get_api_organization(token)
        events, pagination = get_events_for_organizations(
            organizations,
            self.request.user,
            self.request.GET.get('page'),
        )
        for event in events:
            event['start']['local'] = (dateutil.parser.parse(
                event['start']['local'])).strftime('%b. %e, %Y - %-I:%M %p')
            event_db = Event.objects.filter(eb_event_id=event['id']).first()
            if event_db:
                event['badges_tool'] = event_db.badges_tool
                event['merchandise_tool'] = event_db.merchandise_tool
        context['events'] = events
        if pagination:
            context['has_next'] = pagination.get('has_more_items')
            context['has_previous'] = True if pagination.get(
                'page_number') > 1 else False
            context['number'] = pagination.get('page_number')
            context['num_pages'] = pagination.get('page_count')
            context['next_page_number'] = pagination.get('page_number') + 1
            context['previous_page_number'] = pagination.get('page_number') - 1
        return context

    def post(self, request, *args, **kwargs):
        token = get_auth_token(self.request.user)
        events = get_events_mercha_and_badges(self.request.POST.items())
        for key, value in events.items():
            try:
                create_event_complete(self.request.user,
                                                token,
                                                key,
                                                self.request.POST.get(
                                                    'org_id_{}'.format(key)),
                                                self.request.POST.get(
                                                    'org_name_{}'.format(key)),
                                                value['badges'],
                                                value['merchandise'],
                                                )
                message = 'The event has been successfully added.'
            except Exception:
                message = 'There was an error while adding the event.'
            self.request.session['message'] = message
        return redirect(reverse('index'))


@method_decorator(login_required, name='dispatch')
class DeleteEvents(TemplateView, LoginRequiredMixin, EventAccessMixin):
    template_name = 'delete.html'

    def get_context_data(self, **kwargs):
        context = super(DeleteEvents, self).get_context_data(**kwargs)
        event = get_db_event_by_id(self.kwargs['event_id'])
        context['event'] = event
        return context

    def post(self, request, *args, **kwargs):
        event_id = self.kwargs['event_id']
        delete_events(event_id)
        if isinstance(get_db_event_by_id(event_id), Event) is False:
            message = 'The event has been successfully removed'
            self.request.session['message'] = message
        else:
            message_error = 'An error has occured while the event was being deleted'
            self.request.session['message'] = message_error
        return redirect(reverse('index'))


class ActivateLanguageView(View):
    language_code = ''
    redirect_to = ''

    def get(self, request, *args, **kwargs):
        self.redirect_to = request.META.get('HTTP_REFERER')
        self.language_code = kwargs.get('language_code')
        translation.activate(self.language_code)
        request.session[translation.LANGUAGE_SESSION_KEY] = self.language_code
        return redirect(self.redirect_to)