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
)
from .utils import (
    get_auth_token,
    get_api_organization,
    get_api_events_org,
    get_api_events_id
)


@method_decorator(login_required, name='dispatch')
class Home(TemplateView, LoginRequiredMixin):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        organizations_query = UserOrganization.objects.filter(
            user=self.request.user
        )
        events = {'events': Event.objects.filter(
            organization__in=[ user_organization.organization for user_organization in organizations_query ],
        )}
        paginator = Paginator(tuple(events['events']), 10)
        page = self.request.GET.get('page')
        try:
            pagination = paginator.page(page)
        except PageNotAnInteger:
            pagination = paginator.page(1)
        except EmptyPage:
            pagination = paginator.page(paginator.num_pages)
        message = self.request.GET.get('message')
        return {'pagination': pagination, 'message': message}


@method_decorator(login_required, name='dispatch')
class SelectEvents(TemplateView, LoginRequiredMixin):
    template_name = 'select_events.html'

    def get_context_data(self, **kwargs):
        context = super(SelectEvents, self).get_context_data(**kwargs)
        token = get_auth_token(self.request.user)
        organizations = get_api_organization(token)
        events = {'events': []}
        for organization in organizations:
            event = get_api_events_org(token, organization)
            for e in event:
                e['org_name'] = organization['name']
            events['events'].extend(
                event
            )
        paginator = Paginator(tuple(events['events']), 10)
        page = self.request.GET.get('page')
        try:
            pagination = paginator.page(page)
        except PageNotAnInteger:
            pagination = paginator.page(1)
        except EmptyPage:
            pagination = paginator.page(paginator.num_pages)
        return {'pagination': pagination}

    def post(self, request, *args, **kwargs):
        token = get_auth_token(self.request.user)
        event = get_api_events_id(token, request)
        evento = {'evento': []}
        evento['evento'] = get_api_events_id(token, request)
        org_id = self.request.POST.get('organization_id')
        try:
            organizacion = Organization.objects.get(eb_organization_id=org_id)
        except Organization.DoesNotExist:
            organizacion = Organization.objects.create(
                eb_organization_id=org_id,
                name=self.request.POST.get('organization_name')
            )
            UserOrganization.objects.create(
                organization=organizacion,
                user=self.request.user,
            )
        event = Event()
        event.organization = organizacion
        event.name = evento['evento']['name']['text']
        event.description = evento['evento']['description']['text']
        event.eb_event_id = evento['evento']['id']
        event.url = evento['evento']['url']
        event.date_tz = evento['evento']['start']['timezone']
        event.start_date_utc = evento['evento']['start']['utc']
        event.end_date_utc = evento['evento']['end']['utc']
        event.created = evento['evento']['created']
        event.changed = evento['evento']['changed']
        event.status = evento['evento']['status']
        try:
            event.save()
            message = 'Se agrego el evento {}'.format(
                evento['evento']['name']['text'])
        except Exception:
            message = 'El evento ya existe'
        return redirect(reverse('index', kwargs={'message': message}))
