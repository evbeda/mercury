from mercury_site.celery import app
from social_django.models import UserSocialAuth
from eventbrite import Eventbrite
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
import pytz
from django.template import loader
from django.core.mail import send_mail, EmailMessage
from datetime import (
    timedelta,
)
from django.db.models import Sum, Count
from faker import Faker
from random import (
    randint,
    uniform,
)
import json
import os
import re
from .models import (
    Order,
    Event,
    Merchandise,
    Organization,
    UserOrganization,
    UserWebhook,
    Transaction,
    MERCH_STATUS,
    Attendee,
)
from mercury_app.pdf_utils import pdf_merchandise
from django.contrib.auth import get_user_model
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
    result = []
    page = 1
    continuation = True
    while (continuation):
        url = '/events/{}/orders/?page={}'.format(event_id, page)
        call = eventbrite.get(url, expand=('merchandise',))
        result.extend(call.get('orders'))
        page += 1
        continuation = has_continuation(call)
    return result

def get_api_events_org(token, organization, page_number=None):
    """
    Get events of one organization from the user of the token from the api
    """
    eventbrite = Eventbrite(token)
    if page_number == None:
        page_number = 1
    api_query = eventbrite.get(
        '/organizations/{}/events/?page={}'.format(organization['id'], page_number))
    return api_query.get('events'), api_query.get('pagination')


def get_api_events_id(token, event_id):
    """
    Get events from the user of the token from the api
    """
    eventbrite = Eventbrite(token)
    return eventbrite.get('/events/{}'.format(event_id))


def get_api_order(token, order_id):
    eventbrite = Eventbrite(token)
    url = '/orders/{}'.format(order_id)
    return eventbrite.get(url, expand=('merchandise',))


def get_api_order_barcode(token, org_id, barcode):
    eventbrite = Eventbrite(token)
    url = '/organizations/{}/orders/search?barcodes={}'.format(org_id, barcode)
    return eventbrite.get(url).get('orders')[0]


def get_api_order_attendees(token, order_id):
    eventbrite = Eventbrite(token)
    result = []
    page = 1
    continuation = True
    while (continuation):
        url = '/orders/{}/attendees/?page={}'.format(order_id, page)
        call = eventbrite.get(url, expand=('merchandise',))
        result.extend(call.get('attendees'))
        page += 1
        continuation = has_continuation(call)
    return result


def get_api_attendee_checked(token, attendee_id, event_id):
    eventbrite = Eventbrite(token)
    url = '/events/{}/attendees/{}/'.format(event_id, attendee_id)
    return eventbrite.get(url)


def has_continuation(request):
    return request.get('pagination').get('has_more_items')


def get_db_event_by_id(event_id):
    try:
        return Event.objects.get(eb_event_id=event_id)
    except Exception as e:
        return None


def get_db_order_by_id(order_id):
    try:
        return Order.objects.get(id=order_id)
    except Exception as e:
        return None


@app.task(ignore_result=True)
def create_event_orders_from_api(userid, eventid, orders=None):
    created_orders = []
    event = Event.objects.get(id=eventid)
    token = get_auth_token(get_user_model().objects.get(id=userid))
    if orders is None:
        orders = get_api_orders_of_event(token, event.eb_event_id)
    try:
        for order in orders:
            if (order is not None and len(order.get('merchandise')) > 0):
                order_transactions = create_order_atomic.delay(userid, eventid, order)
                created_orders.append(order_transactions)
    except Exception:
        created_orders.append(None)
        if len(created_orders) < len(orders):
            remaining_orders = orders[len(created_orders):]
            more_orders = create_event_orders_from_api.delay(userid, eventid, remaining_orders)
            created_orders.extend(more_orders)
    cache.delete(event.eb_event_id)
    return created_orders


@app.task(ignore_result=True)
def create_order_atomic(userid, eventid, order):
    with transaction.atomic():
        event = Event.objects.get(id=eventid)
        order_creation, _ = Order.objects.get_or_create(
            event=event,
            eb_order_id=order['id'],
            created=order['created'],
            changed=order['changed'],
            first_name=order['first_name'],
            last_name=order['last_name'],
            status=order['status'],
            email=order['email'],
        )
        create_attendee_from_order(userid, order_creation)
        for item in order['merchandise']:
            create_merchandise_from_order(item, order_creation)
        return order_creation


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


def create_attendee_from_order(userid, order):
    token = get_auth_token(get_user_model().objects.get(id=userid))
    attendees = get_api_order_attendees(token, order.eb_order_id)
    created_attendees = []
    for attendee in attendees:
        first_name = attendee.get('profile').get('first_name')
        last_name = attendee.get('profile').get('last_name')
        eb_attendee_id = attendee.get('id')
        barcode = attendee.get('barcodes')[0].get('barcode')
        barcode_url = attendee.get('barcodes')[0].get('qr_code_url')
        checked_in = attendee.get('checked_in')
        att = Attendee.objects.create(
            order=order,
            first_name=first_name,
            last_name=last_name,
            eb_attendee_id=eb_attendee_id,
            barcode=barcode,
            barcode_url=barcode_url,
            checked_in=checked_in,
        )
        created_attendees.append(att)
    return created_attendees


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


def get_events_for_organizations(organizations, user, page_number):
    for organization in organizations:
        event, pagination = get_api_events_org(
            get_auth_token(user), organization, page_number)
        if event:
            for e in event:
                e['org_name'] = organization['name']
        else:
            event = None
    return event, pagination


def create_order_webhook_from_view(user):
    if not UserWebhook.objects.filter(user=user).exists():
        token = get_auth_token(user)
        webhook_id = create_webhook(token)
        if webhook_id is not None:
            UserWebhook.objects.create(
                user=user,
                webhook_id=webhook_id,
            )


def update_attendee_checked_from_api(user, barcode):
    attendee = Attendee.objects.get(barcode=barcode)
    result = get_api_attendee_checked(
        get_auth_token(user),
        attendee.eb_attendee_id,
        attendee.order.event.eb_event_id,
    )
    Attendee.objects.filter(barcode=barcode).update(
        checked_in=result.get('checked_in')
    )
    return result.get('checked_in')


def create_webhook(token):
    data = {
        'endpoint_url': URL_ENDPOINT,
        'actions': WH_ACTIONS,
    }
    response = Eventbrite(token).post('/webhooks/', data)
    return (response.get('id', None))


def delete_webhook(token, webhook_id):
    webhook = UserWebhook.objects.get(webhook_id=webhook_id)
    webhook.delete()
    Eventbrite(token).delete('/webhooks/' + webhook_id + '/')
    return HttpResponseRedirect('/')


def get_email_pdf_context(order_id):
    order = Order.objects.filter(id=order_id)[0]
    context = {'event_name': order.event.name,
               'event_id': order.event.id}
    return context


@app.task(ignore_result=True)
def send_email_with_pdf(order_id, email):
    try:
        pdf = pdf_merchandise(order_id)
        context = get_email_pdf_context(order_id)
        template_html = "emails_pdf.html"
        html = loader.get_template(template_html)
        html_content = html.render(context)
        msg = EmailMessage("Your mechandise for {}".format(context['event_name']),
                           html_content,
                           os.environ.get('EMAIL_HOST_USER'),
                           [email])
        msg.attach('merchandise.pdf', pdf, 'application/pdf')
        msg.content_subtype = "html"
        msg.send()
        return True
    except Exception:
        return False


@app.task(ignore_result=True)
def get_data(body, domain):
    config_data = body
    user_id = config_data['config']['user_id']
    if webhook_available_to_process(user_id):
        social_user = get_social_user(user_id)
        access_token = social_user.access_token
        order_id = re.search(REGEX_ORDER, config_data['api_url'])[5]
        order = get_api_order(
            token=access_token,
            order_id=order_id
        )
        event = Event.objects.get(eb_event_id=order['event_id'])
        if webhook_order_available(social_user.user, order):
            orders = create_event_orders_from_api(social_user.user.id, event.id, [order])
            email = send_email_with_pdf.delay(orders[0][0].id,
                                              orders[0][0].email)

            return {'status': True, 'email': email}

    else:

        return {'status': False, 'email': False}


def webhook_order_available(user, order):
    events = get_db_events_by_organization(user=user)
    if len(events) > 0:
        return True


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


def get_mock_api_event(amount, event_id=0):
    ### UP TO 50 EVENTS ###
    mocked_events_array = []
    fake = Faker()
    for number in range(amount):
        created = fake.date_time_between(
            start_date='-5d', end_date='-1d', tzinfo=pytz.timezone('US/Eastern'))
        if event_id == 0:
            eb_id = str(randint(50000000000, 60000000000))
        else:
            eb_id = event_id
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


def get_json_donut(percentage, quantity, name, id_int):
    data_json = {'quantity': quantity, 'percentage': percentage,
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
            data_json.append({"name": total_mercha[i].get("name"),
                              "handed": handed_mercha[i].get("name_count"),
                              "total": total_mercha[i].get("name_count"),
                              "handed_percentage": handed_percentaje,
                              "not_handed_percentage": dont_handed_percentaje,
                              "pending": total_mercha[i].get("name_count") - handed_mercha[i].get("name_count")})
    else:
        for i in range(len(total_mercha)):
            data_json.append({"name": total_mercha[i].get("name"),
                              "handed": 0,
                              "total": total_mercha[i].get("name_count"),
                              "handed_percentage": 0,
                              "not_handed_percentage": 100,
                              "pending": 0})
    return data_json


def get_percentage_handed(order_ids):
    total_sold = Merchandise.objects.filter(
        order_id__in=order_ids).aggregate(Sum('quantity'))['quantity__sum']
    total_delivered = Transaction.objects.filter(
        merchandise__order__id__in=order_ids, operation_type='HA').count()
    if total_sold is not None:
        if total_sold != 0:
            handed_percentaje = round(
                ((total_delivered *
                  100) / total_sold), 1)
        else:
            handed_percentaje = 0
        return [handed_percentaje, total_sold, total_delivered]


def get_summary_orders(event):
    orders_pending = Order.objects.filter(
        merch_status='PE', event=event).aggregate(quantity=Count('id'))
    orders_delivered = Order.objects.filter(
        merch_status='CO', event=event).aggregate(quantity=Count('id'))
    orders_partially = Order.objects.filter(
        merch_status='PA', event=event).aggregate(quantity=Count('id'))
    total = orders_pending['quantity'] + \
        orders_delivered['quantity'] + orders_partially['quantity']
    if total != 0:
        pending_percentage = (orders_pending['quantity'] * 100) / total
        delivered_percentage = (orders_delivered['quantity'] * 100) / total
        partially_percentage = (orders_partially['quantity'] * 100) / total
    else:
        pending_percentage = 0
        delivered_percentage = 0
        partially_percentage = 0
    data_json = [
        get_json_donut(round(pending_percentage),
                       orders_pending['quantity'], 'Pending', 1),
        get_json_donut(round(delivered_percentage),
                       orders_delivered['quantity'], 'Delivered', 2),
        get_json_donut(round(partially_percentage),
                       orders_partially['quantity'], 'Partial', 3),
    ]
    return data_json


def create_transaction(user, merchandise, note, device, operation, date):
    try:
        tx = Transaction.objects.create(
            merchandise=merchandise,
            from_who=user,
            notes=note,
            device_name=device,
            operation_type=operation,
            date=date,
        )
        update_db_merch_status(tx.merchandise.order)
        return tx
    except Exception:
        return None


def get_db_items_left(merchandising_query_obj):
    merchandising_query = list(merchandising_query_obj.values())
    for index in range(len(merchandising_query)):
        all_transactions = Transaction.objects.filter(
            merchandise=merchandising_query_obj[index]
        )
        transaction_count = 0
        for transaction in all_transactions:
            if transaction.operation_type == 'HA':
                transaction_count -= 1
            elif transaction.operation_type == 'RE':
                transaction_count += 1
            else:
                pass
        items_left = merchandising_query[index].get(
            'quantity') + transaction_count
        merchandising_query[index]['items_left'] = items_left
    return merchandising_query


def get_db_transaction_by_merchandise(merchandise):
    try:
        transaction_query = Transaction.objects.filter(
            merchandise=merchandise,
        )
        return transaction_query
    except Exception:
        return None


def update_db_merch_status(order):
    total_mercha = Merchandise.objects.filter(
        order=order).aggregate(Sum('quantity'))
    handed_mercha = Transaction.objects.filter(
        merchandise__in=Merchandise.objects.filter(
            order=order).values('id').order_by('id'),
        operation_type='HA').count()
    if total_mercha['quantity__sum'] == handed_mercha:
        Order.objects.filter(id=order.id).update(
            merch_status=MERCH_STATUS[0][0]
        )
        return MERCH_STATUS[0][0]
    elif handed_mercha == 0:
        Order.objects.filter(id=order.id).update(
            merch_status=MERCH_STATUS[2][0]
        )
        return MERCH_STATUS[2][0]
    else:
        Order.objects.filter(id=order.id).update(
            merch_status=MERCH_STATUS[1][0]
        )
        return MERCH_STATUS[1][0]


def delete_events(event_id):
    Event.objects.filter(eb_event_id=event_id).delete()

class EventAccessMixin():
    def get_event(self):
        event = get_object_or_404(
            Event,
            eb_event_id=self.kwargs['event_id'],
        )
        org_id = UserOrganization.objects.filter(
            user=self.request.user).values_list('organization', flat=True)
        if event.organization.id not in org_id:
            raise PermissionDenied("You don't have access to this event")
        return event


class OrderAccessMixin():
    def get_merchandise(self):
        order_id = int(self.kwargs['order_id'])
        order = get_object_or_404(Order, id=order_id)
        org_id = UserOrganization.objects.filter(
            user=self.request.user).values_list('organization', flat=True)
        orders_ids = Order.objects.filter(
            event__organization__in=org_id).values_list('id', flat=True)
        if int(order_id) not in orders_ids:
            raise PermissionDenied("You don't have access to this event")
        return Merchandise.objects.filter(
            order=order_id,
        )


@app.task(ignore_result=True)
def send_email_alert(transactions, email, date, operation, order_id):
    transactions = json.loads(transactions)
    if len(transactions):
        template_html = "email.html"
        text_content = "Merchandise delivery"
        html = loader.get_template(template_html)
        context = {'transactions': transactions,
                   'date': date,
                   'operation': operation,
                   'order_id': order_id}
        html_content = html.render(context)
        send_mail(
            "Merchandise delivery",
            text_content,
            os.environ.get('EMAIL_HOST_USER'),
            [email],
            html_message=html_content,
            fail_silently=False,
        )
        return context


def get_merchas_for_email(merchases, date):
    merchandises = []
    merchases_ids = []
    for mercha in merchases:
        if mercha.id not in merchases_ids:
            merchandises.append([mercha.name,
                                 mercha.item_type,
                                 mercha.quantity_handed(date),
                                 ])
            merchases_ids.append(mercha.id)
    return merchandises, mercha.order.id, mercha.order.email
