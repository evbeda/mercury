from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django_tables2 import SingleTableMixin
import json
from mercury_app.models import (
    Organization,
    UserOrganization,
    Event,
    Order,
    Merchandise,
    UserWebhook,
    Transaction,
)
from mercury_app.tables import OrderTable
from mercury_app.filters import OrderFilter
from mercury_app.filterview_fix import MyFilterView
from mercury_app.utils import (
    get_auth_token,
    get_api_organization,
    get_api_events_org,
    get_summary_orders,
    get_api_events_id,
    get_percentage_handed,
    get_api_orders_of_event,
    get_api_order_barcode,
    get_events_for_organizations,
    get_db_event_by_id,
    get_db_order_by_id,
    get_db_merchandising_by_order_id,
    get_db_orders_by_event,
    get_db_events_by_organization,
    get_db_or_create_organization_by_id,
    get_db_items_left,
    create_userorganization_assoc,
    create_event_orders_from_api,
    create_event_from_api,
    create_order_webhook_from_view,
    get_data,
    get_summary_types_handed,
    get_db_transaction_by_merchandise,
    create_transaction,
    delete_events,
    EventAccessMixin,
    OrderAccessMixin,
)
import time
import dateutil.parser

@csrf_exempt
def accept_webhook(request):
    get_data.delay(json.loads(request.body),
                   request.build_absolute_uri('/')[:-1])
    return HttpResponse('OK', 200)


@method_decorator(login_required, name='dispatch')
class ScanQRView(TemplateView, LoginRequiredMixin, OrderAccessMixin):
    template_name = 'scanqr.html'

    def get_context_data(self, **kwargs):
        context = super(ScanQRView, self).get_context_data(**kwargs)
        context['event_id'] = self.kwargs['event_id']
        context['organization_id'] = Event.objects.get(
            eb_event_id=self.kwargs['event_id']
        ).organization.eb_organization_id
        return context

    def post(self, request, *args, **kwargs):
        data = self.request.POST
        qrcode = data['code']
        org_id = data['org']
        event_id = data['event']
        token = get_auth_token(self.request.user)
        order = get_api_order_barcode(token, org_id, qrcode)
        try:
            eb_order_id = order.get('id')
            order_id = Order.objects.get(eb_order_id=eb_order_id).id
            return redirect(reverse(
                'item_mercha',
                kwargs={'order_id': order_id},
            ))
        except Exception as e:
            return redirect(reverse(
                'summary',
                kwargs={'event_id': event_id},
            ))


@method_decorator(login_required, name='dispatch')
class FilteredOrderListView(SingleTableMixin, MyFilterView, EventAccessMixin):
    table_class = OrderTable
    model = Order
    template_name = 'orderfilter.html'
    filterset_class = OrderFilter

    def get_queryset(self):
        return Order.objects.filter(event__eb_event_id=self.kwargs['event_id'])

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
        context['merchandising'] = get_db_items_left(merchandising_query_obj)
        context['order'] = order
        return context

    def post(self, request, *args, **kwargs):
        data = self.request.POST
        keys = list(data)[:-2]
        for item in keys:
            for qty in range(int(data[item])):
                create_transaction(
                    self.request.user,
                    Merchandise.objects.get(
                        eb_merchandising_id=item,
                    ),
                    data['comment'],
                    'unique',
                    'HA',
                )
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
            event=event).values_list('id', flat=True)
        if len(order_ids) == 0:
            token = get_auth_token(self.request.user)
            orders = get_api_orders_of_event(token, event.eb_event_id)
            create_event_orders_from_api(event, orders)
            order_ids = Order.objects.filter(
                event=event).values_list('id', flat=True)
        context['data_handed_over_dont'] = get_percentage_handed(
            order_ids)
        context['data_tipes_handed'] = get_summary_types_handed(order_ids)
        context['data_orders'] = get_summary_orders(event)
        context['event'] = event
        return context


@method_decorator(login_required, name='dispatch')
class Home(TemplateView, LoginRequiredMixin):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        create_order_webhook_from_view(self.request.user)
        events = {'events': get_db_events_by_organization(self.request.user)}
        message = self.request.GET.get('message')
        page = self.request.GET.get('page')
        paginator = Paginator(tuple(events['events']), 10)
        try:
            pagination = paginator.page(page)
        except PageNotAnInteger:
            pagination = paginator.page(1)
        except EmptyPage:
            pagination = paginator.page(paginator.num_pages)
        context['pagination'] = pagination
        context['message'] = message
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
            event['start']['local'] = (dateutil.parser.parse(event['start']['local'])).strftime('%b. %e, %Y - %I %p')
        context['events'] = events
        if pagination:
            context['has_next'] = pagination.get('has_more_items')
            context['has_previous'] = True if pagination.get('page_number') > 1 else False
            context['number'] = pagination.get('page_number')
            context['num_pages'] = pagination.get('page_count')
            context['next_page_number'] = pagination.get('page_number') + 1
            context['previous_page_number'] = pagination.get('page_number') - 1
        return context

    def post(self, request, *args, **kwargs):
        token = get_auth_token(self.request.user)
        events = {'events': []}
        events['events'] = get_api_events_id(
            token,
            request.POST.get('id_event'),
        )
        org_id = self.request.POST.get('organization_id')
        org_name = self.request.POST.get('organization_name')
        org = get_db_or_create_organization_by_id(org_id, org_name)
        create_userorganization_assoc(org[0], self.request.user)
        if isinstance(create_event_from_api(org[0], events['events']), Event):
            message = 'The event was successfully added!'
        else:
            message = 'An error has occured while adding the event'

        return redirect(reverse('index', kwargs={'message': message}))


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
            message_error = 'The event has been successfully removed'
        else:
            message_error = 'An error has occured while the event was being deleted'
        return redirect(reverse('index', kwargs={'message': message_error}))
