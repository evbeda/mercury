from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from social_django.models import UserSocialAuth
from eventbrite import Eventbrite
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from mercury_app.models import (
    Organization,
    UserOrganization,
    Event,
    Order,
    Merchandise)


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
        return {'pagination': pagination}


@method_decorator(login_required, name='dispatch')
class SelectEvents(TemplateView, LoginRequiredMixin):
    template_name = 'select_events.html'

    def get_context_data(self, **kwargs):
        context = super(SelectEvents, self).get_context_data(**kwargs)
        eventbrite = Eventbrite(get_auth_token(self.request.user))
        organizations = eventbrite.get(
            '/users/me/organizations')['organizations']
        events = {'events': []}
        for organization in organizations:
            events['events'].extend(
                eventbrite.get(
                    '/organizations/{}/events/'.format(
                        organization['id']))['events']
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

        eventbrite = Eventbrite(get_auth_token(self.request.user))
        evento = {'evento': []}
        evento['evento'] = eventbrite.get(
            '/events/{}'.format(self.request.POST.get('id_event')))
        try:
            org = Organization.objects.create(
                eb_organization_id=self.request.POST.get('organization_id'),
                name=self.request.POST.get('organization_name')
            )
            UserOrganization.objects.create(
                organization=org,
                user=self.request.user,
            )
        except Exception as e:
            print(e)
        event = Event()
        org_id = evento['evento']['organization_id']
        organizacion = Organization.objects.get(eb_organization_id=org_id)
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


def get_auth_token(user):
    try:
        token = user.social_auth.get(
            provider='eventbrite'
        ).access_token
    except UserSocialAuth.DoesNotExist:
        print ('UserSocialAuth does not exists!')
    return token
