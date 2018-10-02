import json
import requests
import re
from mercury_site.celery import app
from social_django.models import UserSocialAuth
from django.contrib.auth import get_user_model
from eventbrite import Eventbrite
import re
from .models import (
    Order,
    Event,
    Merchandise,
    Organization,
    UserOrganization,
    UserWebhook,
)
from django.conf import settings
from django.http import HttpResponseRedirect


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


def get_api_orders_of_event(token, event_id):
    """
    Get organization from the user of the token from the api
    """
    eventbrite = Eventbrite(token)
    url = "/events/{}/orders/".format(event_id)
    return eventbrite.get(url, expand=('merchandise',))['orders']


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


def get_db_event_by_id(event_id):
    try:
        return Event.objects.get(eb_event_id=event_id)
    except Exception as e:
        print(e)
        return None


def create_event_orders_from_api(event, orders):
    for order in orders:
        if order.get('merchandise'):
            try:
                order_creation = Order.objects.get_or_create(
                    event=event,
                    eb_order_id=order['id'],
                    created=order['created'],
                    changed=order['changed'],
                    name=order['name'],
                    status=order['status'],
                    email=order['email'],
                )
                for item in order['merchandise']:
                    create_merchandise_from_order(item, order_creation[0])
            except Exception as e:
                print(e)


def create_merchandise_from_order(item, order):
    try:
        Merchandise.objects.create(
            order=order,
            eb_merchandising_id=item['id'],
            name=re.sub(r'(.*?)\s?\(.*?\)', r'\1', item['name']),
            quantity=item['quantity'],
            item_type=re.findall(
                '\(([^)]+)',
                item['name'])[0] if re.findall(
                '\(([^)]+)',
                item['name']) else '',
            value=item['costs']['gross']['major_value'],
        )
    except Exception as e:
        print(e)


def get_db_merchandising_by_order_id(order_id):
    try:
        merchandising_query = Merchandise.objects.get(
            order=order_id,
        )
    except Exception as e:
        print(e)
    return merchandising_query


def get_db_orders_by_event(event):
    try:
        order_query = Order.objects.filter(
            event=event
        ).all()
    except Exception as e:
        print(e)
    return order_query


def get_db_organizations_by_user(user):
    try:
        organizations_query = UserOrganization.objects.filter(
            user=user
        )
    except Exception as e:
        print(e)
    return organizations_query


def get_db_events_by_organization(user):
    organizations_query = get_db_organizations_by_user(user)
    try:
        events = Event.objects.filter(
            organization__in=[ user_organization.organization for user_organization in organizations_query ],
        )
    except Exception as e:
        print(e)
    return events


def get_db_or_create_organization_by_id(ebid, ebname):
    try:
        organization = Organization.objects.get_or_create(
            eb_organization_id=ebid,
            name=ebname,
        )
    except Exception as e:
        print(e)
    return organization


def create_userorganization_assoc(organization, user):
    try:
        UserOrganization.objects.get_or_create(
            organization=organization,
            user=user,
        )
    except Exception as e:
        print(e)


def create_event_from_api(organization, event):
    try:
        Event.objects.create(
            organization=organization,
            name=event['name']['text'],
            description=event['description']['text'],
            eb_event_id=event['id'],
            url=event['url'],
            date_tz=event['start']['timezone'],
            start_date_utc=event['start']['utc'],
            end_date_utc=event['end']['utc'],
            created=event['created'],
            changed=event['changed'],
            status=event['status'],
        )
        message = 'The event {} was added successfully!'.format(
            event['name']['text']
        )
        return message
    except Exception as e:
        return e


def get_events_for_organizations(organizations, user):
    for organization in organizations:
        event = get_api_events_org(get_auth_token(user), organization)
        for e in event:
            e['org_name'] = organization['name']
    return event


def create_webhook_from_view(user):
    if not UserWebhook.objects.filter(user=user).exists():
        token = get_auth_token(user)
        webhook_id = create_webhook(token)
        UserWebhook.objects.create(
            user=user,
            webhook_id=webhook_id,
        )


def create_webhook(token):
    url = settings.URL_LOCAL
    data = {
        "endpoint_url": url + "/webhook-point/",
        "actions": "order.placed",
    }
    response = Eventbrite(token).post('/webhooks/', data)
    return (response[u'id'])


def delete_webhook(token, webhook_id):
    webhook = UserWebhook.objects.get(webhook_id=webhook_id)
    webhook.delete()
    Eventbrite(token).delete('/webhooks/' + webhook_id + "/")
    return HttpResponseRedirect('/')


@app.task(ignore_result=True)
def get_data(body, domain):
    print('Here! get_data')
    config_data = body
    user_id = config_data['config']['user_id']

    if webhook_available_to_process(user_id):
        social_user = get_social_user(user_id)
        access_token = social_user.access_token
        order_id = re.search(
            r'(http[s]?:\/\/)?([^\/\s]+\/)([^\/\s]+\/)([^\/\s]+\/)(\d+)(.*)',
            config_data['api_url'])[5]
        order = get_order(
            token=access_token,
            order_id=order_id
        )
        event = Event.objects.get(eb_event_id=order['event_id'])
        if webhook_order_available(social_user.user, order):
            create_event_orders_from_api(event, [order])

            return {'status': True}
    else:
        return {'status': False}


def webhook_order_available(user, order):
    events = get_db_events_by_organization(user=user)
    if len(events) > 0:
        return True


def get_order(token, order_id):
    eventbrite = Eventbrite(token)
    url = "/orders/{}".format(order_id)
    return eventbrite.get(url, expand=('merchandise',))


def webhook_available_to_process(user_id):
    if UserSocialAuth.objects.exists():
        if social_user_exists(user_id):
            return True


def social_user_exists(user_id):
    social_user = UserSocialAuth.objects.filter(
        uid=user_id
    )
    if len(social_user) == 0:
        return False
    else:
        return True


def get_social_user_id(user_id):
    social_user = get_social_user(user_id)
    return social_user.user_id


def get_social_user(user_id):
    social_user = UserSocialAuth.objects.filter(
        uid=user_id
    )
    return social_user[0]
