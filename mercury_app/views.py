from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from mercury_app.models import (
    Organization,
    UserOrganization,
    Event,
    Order,
    Merchandise,
)
from .utils import (
    get_auth_token,
    get_api_organization,
    get_api_events_org,
    get_api_events_id,
    get_api_orders_of_event,
    get_events_for_organizations,
    get_db_event_by_id,
    get_db_merchandising_by_order_id,
    get_db_orders_by_event,
    get_db_events_by_organization,
    get_db_or_create_organization_by_id,
    create_userorganization_assoc,
    create_event_orders_from_api,
    create_event_from_api,

)


@method_decorator(login_required, name='dispatch')
class ListItemMerchandising(TemplateView, LoginRequiredMixin):
    template_name = 'list_item_mercha.html'

    def get_context_data(self, **kwargs):
        context = super(ListItemMerchandising, self).get_context_data(**kwargs)
        context['merchandising'] = get_db_merchandising_by_order_id(
            kwargs['order_id']
        )
        return context


@method_decorator(login_required, name='dispatch')
class OrderList(TemplateView, LoginRequiredMixin):
    template_name = 'orders.html'

    def get_context_data(self, **kwargs):
        context = super(OrderList, self).get_context_data(**kwargs)
        event_id = self.kwargs['event_id']
        event = get_db_event_by_id(event_id)
        token = get_auth_token(self.request.user)
        orders = get_api_orders_of_event(token, event_id)
        create_event_orders_from_api(event, orders)
        context['orders'] = get_db_orders_by_event(event)
        return context


@method_decorator(login_required, name='dispatch')
class Home(TemplateView, LoginRequiredMixin):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
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
        events['events'] = get_api_events_id(token, request)
        org_id = self.request.POST.get('organization_id')
        org_name = self.request.POST.get('organization_name')
        org = get_db_or_create_organization_by_id(org_id, org_name)
        create_userorganization_assoc(org[0], self.request.user)
        message = create_event_from_api(org[0], events['events'])
        return redirect(reverse('index', kwargs={'message': message}))
