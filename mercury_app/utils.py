from social_django.models import UserSocialAuth
from eventbrite import Eventbrite


def get_auth_token(user):
    try:
        token = user.social_auth.get(
            provider='eventbrite'
        ).access_token
    except UserSocialAuth.DoesNotExist:
        print ('UserSocialAuth does not exists!')
    return token


def get_api_organization(token):

    """
    Get organization from the user of the token from the api
    """
    eventbrite = Eventbrite(token)
    return eventbrite.get('/users/me/organizations').get('organizations')


def get_api_events_org(token, organization):
    """
    Get events of one organization from the user of the token from the api
    """
    eventbrite = Eventbrite(token)
    return eventbrite.get('/organizations/{}/events/'.format(organization['id'])).get('events')


def get_api_events_id(token, request):
    """
    Get events from the user of the token from the api
    """
    eventbrite = Eventbrite(token)
    return eventbrite.get('/events/{}'.format(request.POST.get('id_event')))
