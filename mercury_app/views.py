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
    get_api_events_id,
    get_api_orders_of_event,
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
    get_summary_handed_over_dont_json,
    get_summary_types_handed,
    get_db_transaction_by_merchandise,
    create_transaction,
    EventAccessMixin,
    OrderAccessMixin,
)


@csrf_exempt
def accept_webhook(request):
    get_data.delay(json.loads(request.body),
                   request.build_absolute_uri('/')[:-1])
    return HttpResponse('OK', 200)


@method_decorator(login_required, name='dispatch')
class FilteredOrderListView(SingleTableMixin, MyFilterView, EventAccessMixin):
    table_class = OrderTable
    model = Order
    template_name = 'orderfilter.html'
    filterset_class = OrderFilter

    def get_queryset(self):
        return Order.objects.filter(event__eb_event_id=self.kwargs['event_id'])

    def get_table_kwargs(self):
        return {'template_name': 'django_tables2/bootstrap4.html'}

    def get_context_data(self, **kwargs):
        context = super(SingleTableMixin, self).get_context_data(**kwargs)
        table = self.get_table(**self.get_table_kwargs())
        context[self.get_context_table_name(table)] = table
        event = self.get_event()
        context['event_name'] = event.name
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
        keys = list(data)[:-1]
        for item in keys:
            for qty in range(int(data[item])):
                create_transaction(
                    self.request.user,
                    Merchandise.objects.get(
                        eb_merchandising_id=item,
                    ),
                    '',
                    'unique',
                    'HA',
                )
        return redirect(reverse('index'))





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
        context['data_handed_over_dont'] = get_summary_handed_over_dont_json(
            order_ids)
        context['data_tipes_handed'] = get_summary_types_handed(order_ids)
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
        events = {'events': get_events_for_organizations(
            organizations,
            self.request.user,
        )}
        paginator = Paginator(tuple(events['events']), 10)
        page = self.request.GET.get('page')
        try:
            pagination = paginator.page(page)
        except PageNotAnInteger:
            pagination = paginator.page(1)
        except EmptyPage:
            pagination = paginator.page(paginator.num_pages)
        context['pagination'] = pagination
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
class TransactionView(TemplateView, LoginRequiredMixin):
    template_name = 'transaction.html'

    def get_context_data(self, **kwargs):
        context = super(TransactionView, self).get_context_data(**kwargs)
        item = self.kwargs['item_id']
        context['transaction'] = (item)
        return context

    def post(self, request, *args, **kwargs):
        token = get_auth_token(self.request.user)
        name = self.kwargs['name']
