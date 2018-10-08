from mercury_site.celery import app
from social_django.models import UserSocialAuth
from eventbrite import Eventbrite
import pytz
from datetime import (
    timedelta,
)
from django.db.models import Sum
from faker import Faker
from random import (
    randint,
    uniform,
)
import re
from .models import (
    Order,
    Event,
    Merchandise,
    Organization,
    UserOrganization,
    UserWebhook,
    Transaction,
)
from django.http import HttpResponseRedirect
from mercury_app.app_settings import (
    URL_ENDPOINT,
    WH_ACTIONS,
    REGEX_ORDER,
)


def get_auth_token(user):
    try:
        token = user.social_auth.get(
            provider='eventbrite'
        ).access_token
    except UserSocialAuth.DoesNotExist:
        return ''
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
    url = '/events/{}/orders/'.format(event_id)
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
        return None


def create_event_orders_from_api(event, orders):
    created_orders = []
    try:
        for order in orders:
            if order.get('merchandise'):
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
                created_orders.append(order_creation)
    except Exception:
        created_orders.append(None)
        if len(created_orders) < len(orders):
            remaining_orders = orders[len(created_orders):]
            more_orders = create_event_orders_from_api(event, remaining_orders)
            created_orders.extend(more_orders)
    return created_orders


def create_merchandise_from_order(item, order):
    try:
        merchandise = Merchandise.objects.create(
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
        return merchandise
    except Exception:
        return None


def get_db_merchandising_by_order_id(order_id):
    try:
        merchandising_query = Merchandise.objects.filter(
            order=order_id,
        )
        return merchandising_query
    except Exception:
        return None


def get_db_orders_by_event(event):
    try:
        order_query = Order.objects.filter(
            event=event
        ).all()
        return order_query
    except Exception:
        return None


def get_db_organizations_by_user(user):
    try:
        organizations_query = UserOrganization.objects.filter(
            user=user
        )
        return organizations_query
    except Exception:
        return None


def get_db_events_by_organization(user):
    organizations_query = get_db_organizations_by_user(user)
    try:
        events = Event.objects.filter(
            organization__in=[
                user_organization.organization for user_organization in organizations_query],
        )
        return events
    except Exception:
        return None


def get_db_or_create_organization_by_id(ebid, ebname):
    try:
        organization = Organization.objects.get_or_create(
            eb_organization_id=ebid,
            name=ebname,
        )
        return organization
    except Exception:
        return None


def create_userorganization_assoc(organization, user):
    try:
        user_org = UserOrganization.objects.get_or_create(
            organization=organization,
            user=user,
        )
        return user_org
    except Exception:
        return None


def create_event_from_api(organization, event):
    try:
        event = Event.objects.create(
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
        return event
    except Exception as e:
        return None


def get_events_for_organizations(organizations, user):
    for organization in organizations:
        event = get_api_events_org(get_auth_token(user), organization)
        for e in event:
            e['org_name'] = organization['name']
    return event


def create_order_webhook_from_view(user):
    if not UserWebhook.objects.filter(user=user).exists():
        token = get_auth_token(user)
        webhook_id = create_webhook(token)
        UserWebhook.objects.create(
            user=user,
            webhook_id=webhook_id,
        )


def create_webhook(token):
    data = {
        'endpoint_url': URL_ENDPOINT,
        'actions': WH_ACTIONS,
    }
    response = Eventbrite(token).post('/webhooks/', data)
    return (response['id'])


def delete_webhook(token, webhook_id):
    webhook = UserWebhook.objects.get(webhook_id=webhook_id)
    webhook.delete()
    Eventbrite(token).delete('/webhooks/' + webhook_id + '/')
    return HttpResponseRedirect('/')


@app.task(ignore_result=True)
def get_data(body, domain):
    config_data = body
    user_id = config_data['config']['user_id']
    if webhook_available_to_process(user_id):
        social_user = get_social_user(user_id)
        access_token = social_user.access_token
        order_id = re.search(REGEX_ORDER, config_data['api_url'])[5]
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
    url = '/orders/{}'.format(order_id)
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


def get_mock_api_event(amount):
    ### UP TO 50 EVENTS ###
    mocked_events_array = []
    fake = Faker()
    for number in range(amount):
        created = fake.date_time_between(
            start_date='-5d', end_date='-1d', tzinfo=pytz.timezone('US/Eastern'))
        eb_id = str(randint(50000000000, 60000000000))
        mocked_events_array.append(
            {
                'name': {'text': fake.text(100), 'html': None},
                'description': {'text': fake.text(1000), 'html': None},
                'id': eb_id,
                'url': 'https://www.eventbrite.com/e/test-event-tickets-{}'.format(eb_id),
                'start': {
                    'timezone': 'America/Los_Angeles',
                    'local': '2018-10-28T22:00:00',
                    'utc': fake.date_time_between(start_date='+15d', end_date='+30d', tzinfo=pytz.timezone('US/Eastern')).strftime('%Y-%m-%dT%H:%M:%SZ')
                },
                'end': {
                    'timezone': 'America/Los_Angeles',
                    'local': '2018-10-29T22:00:00',
                    'utc': fake.date_time_between(start_date='+31d', end_date='+32d', tzinfo=pytz.timezone('US/Eastern')).strftime('%Y-%m-%dT%H:%M:%SZ')
                },
                'organization_id': '272770247903',
                'created': created.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'changed': (created + timedelta(seconds=30)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'capacity': 200,
                'capacity_is_custom': False,
                'status': 'draft',
                'currency': 'USD',
                'listed': False,
                'shareable': True,
                'invite_only': False,
                'online_event': False,
                'show_remaining': False,
                'tx_time_limit': 480,
                'hide_start_date': False,
                'hide_end_date': False,
                'locale': 'en_US',
                'is_locked': False,
                'privacy_setting': 'unlocked',
                'is_series': False,
                'is_series_parent': False,
                'is_reserved_seating': False,
                'show_pick_a_seat': False,
                'show_seatmap_thumbnail': False,
                'show_colors_in_seatmap_thumbnail': False,
                'source': 'create_2.0',
                'is_free': False,
                'version': '3.0.0',
                'logo_id': None,
                'organizer_id': '17867896837',
                'venue_id': None,
                'category_id': None,
                'subcategory_id': None,
                'format_id': None,
                'resource_uri': 'https://www.eventbriteapi.com/v3/events/{}/'.format(eb_id),
                'is_externally_ticketed': False,
                'logo': None
            }

        )
    mock_api_event = {
        'pagination': {
            'object_count': int(amount),
            'page_number': 1,
            'page_size': 50,
            'page_count': 1,
            'has_more_items': False
        },
        'events': mocked_events_array}
    return mock_api_event


def get_mock_api_orders(amount, w_merchandise, event_id):
    mocked_orders_array = []
    fake = Faker()
    for item in range(amount):
        base_price = round(uniform(10.0, 150.0), 2)
        eb_fee = round(base_price * 0.07, 2)
        pay_fee = round((base_price + eb_fee) * 0.07, 2)
        total_cost = base_price + eb_fee + pay_fee
        first_name = fake.first_name()
        last_name = fake.last_name()
        merchandises = [
            {
                'costs': {
                    'eventbrite_fee': {
                        'display': '$0.00',
                        'currency': 'USD',
                        'value': 0,
                        'major_value': '0.00'
                    },
                    'gross': {
                        'display': '$10.00',
                        'currency': 'USD',
                        'value': 1000,
                        'major_value': '10.00'
                    },
                    'payment_fee': {
                        'display': '$0.30',
                        'currency': 'USD',
                        'value': 30,
                        'major_value': '0.30'
                    },
                    'tax': {
                        'display': '$0.00',
                        'currency': 'USD',
                        'value': 0,
                        'major_value': '0.00'
                    }
                },
                'id': '1',
                'quantity': '2',
                'name': 'Cup (Red)',
                'status': 'placed'
            },
            {
                'costs': {
                    'eventbrite_fee': {
                        'display': '$0.00',
                        'currency': 'USD',
                        'value': 0,
                        'major_value': '0.00'
                    },
                    'gross': {
                        'display': '$80.00',
                        'currency': 'USD',
                        'value': 8000,
                        'major_value': '80.00'
                    },
                    'payment_fee': {
                        'display': '$2.40',
                        'currency': 'USD',
                        'value': 240,
                        'major_value': '2.40'
                    },
                    'tax': {
                        'display': '$0.00',
                        'currency': 'USD',
                        'value': 0,
                        'major_value': '0.00'
                    }
                },
                'id': '2',
                'quantity': '4',
                'name': 'T-Shirt (Blue)',
                'status': 'placed'
            }
        ] if w_merchandise > 0 else []

        mocked_orders_array.append(
            {
                'costs': {
                    'base_price': {
                        'display': '${}'.format(base_price),
                        'currency': 'USD',
                        'value': float(str(base_price).replace(',', '')),
                        'major_value': base_price
                    },
                    'eventbrite_fee': {
                        'display': '${}'.format(eb_fee),
                        'currency': 'USD',
                        'value': float(str(eb_fee).replace(',', '')),
                        'major_value': eb_fee
                    },
                    'gross': {
                        'display': '${}'.format(total_cost),
                        'currency': 'USD',
                        'value': float(str(total_cost).replace(',', '')),
                        'major_value': total_cost
                    },
                    'payment_fee': {
                        'display': '${}'.format(pay_fee),
                        'currency': 'USD',
                        'value': float(str(pay_fee).replace(',', '')),
                        'major_value': pay_fee
                    },
                    'tax': {
                        'display': '$0.00',
                        'currency': 'USD',
                        'value': 0,
                        'major_value': '0.00'
                    }
                },
                'resource_uri': 'https://www.evbdevapi.com/v3/orders/11/',
                'id': str(randint(1, 10000000)),
                'changed': '2018-09-24T17:20:39Z',
                'created': '2018-09-24T17:20:23Z',
                'name': first_name + last_name,
                'first_name': first_name,
                'last_name': last_name,
                'email': fake.free_email(),
                'status': 'placed',
                'time_remaining': None,
                'event_id': event_id,
                'merchandise': merchandises
            })
        w_merchandise -= 1
    return mocked_orders_array

def get_json_donut(percentage, name, id_int):
    data_json = {'quantity': percentage, 'percentage': percentage,
                 'name': name, 'id': id_int}
    return data_json


def get_summary_types_handed(order_ids):
    total_mercha = Merchandise.objects.filter(order_id__in=order_ids).values(
        'name').annotate(name_count=Sum('quantity')).order_by('name')
    types = Merchandise.objects.filter(
        order_id__in=order_ids).values_list('name', flat=True).distinct().order_by('name')
    types_id = []
    for ty_pe in types:
        types_id.append(Transaction.objects.filter(
            merchandise__order__id__in=order_ids,
            operation_type='HA',
            merchandise__name=ty_pe).count())
    handed_mercha = []
    for item in range(len(types)):
        handed_mercha.append(
            {'name': types[item], 'name_count': types_id[item]})
    data_json = []
    if len(handed_mercha) != 0:
        for i in range(len(handed_mercha)):
            if total_mercha[i]['name_count'] != 0:
                handed_percentaje = round(
                    ((handed_mercha[i]['name_count'] *
                      100) / total_mercha[i]['name_count']), 1)
            else:
                handed_percentaje = 0
            dont_handed_percentaje = 100 - handed_percentaje
            data_json.append([get_json_donut(
                handed_percentaje,
                '{} handed'.format(total_mercha[i]['name']),
                1),
                get_json_donut(
                dont_handed_percentaje,
                '{} don\'t handed'.format(total_mercha[i]['name']),
                2)])
    else:
        for i in range(len(total_mercha)):
            data_json.append([get_json_donut(
                0,
                '{} handed'.format(total_mercha[i]['name']),
                1),
                get_json_donut(
                100,
                '{} don\'t handed'.format(total_mercha[i]['name']),
                2)])
    return data_json


def get_summary_handed_over_dont_json(order_ids):
    total_sold = Merchandise.objects.filter(
        order_id__in=order_ids).aggregate(Sum('quantity'))['quantity__sum']
    total_delivered = Transaction.objects.filter(
        merchandise__order__id__in=order_ids, operation_type='HA').count()
    if total_sold != 0:
        handed_percentaje = round(
            ((total_delivered *
              100) / total_sold), 1)
    else:
        handed_percentaje = 0
    dont_handed_percentaje = 100 - handed_percentaje
    data_json = ([get_json_donut(
        handed_percentaje,
        'Orders Handed',
        1),
        get_json_donut(
        dont_handed_percentaje,
        'Orders don\'t handed',
        2)])
    return data_json

def create_transaction(merchandise):
    try:
        Transaction.objects.create(
            merchandise=merchandise,
            date=timezone.now(),
            from_who=self.request.user['text'],
            #notes=
            #device_name=merchandise['delivered'],
            #operation_typt=,
        )
        message = 'The transaction {} was added successfully!'.format(
            merchandise['name']['text']
        )
        return message
    except Exception as e:
        return e


def get_transaction_by_merchandise(eb_merchandising_id):
    try:
        transaction_query = Transaction.objects.filter(
            merchandise=eb_merchandising_id,
        )
    except Exception as e:
        print(e)
    return transaction_query
