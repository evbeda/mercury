from django.test import TestCase
from social_django.models import UserSocialAuth
from django.contrib.auth import get_user_model
from .models import (
    Event,
    Organization,
    UserOrganization,
    Order,
    Merchandise,
    UserWebhook,
    Transaction,
)
from .test_factories import (
    UserFactory,
    OrganizationFactory,
    UserOrganizationFactory,
    EventFactory,
    OrderFactory,
    MerchandiseFactory,
    TransactionFactory,
    UserWebhookFactory,
)
from .utils import (
    get_auth_token,
    get_api_organization,
    get_api_events_org,
    get_api_events_id,
    get_api_orders_of_event,
    create_webhook,
    delete_webhook,
    get_events_for_organizations,
    get_db_event_by_id,
    get_db_merchandising_by_order_id,
    get_db_orders_by_event,
    get_db_events_by_organization,
    get_db_organizations_by_user,
    get_db_or_create_organization_by_id,
    get_db_transaction_by_merchandise,
    get_db_items_left,
    create_userorganization_assoc,
    create_event_orders_from_api,
    create_event_from_api,
    create_merchandise_from_order,
    create_transaction,
    get_mock_api_event,
    get_mock_api_orders,
    get_data,
    webhook_order_available,
    get_api_order,
    webhook_available_to_process,
    social_user_exists,
    get_social_user_id,
    get_social_user,
    get_json_donut,
    get_summary_types_handed,
    get_summary_handed_over_dont_json,
    create_order_webhook_from_view,
)
from mercury_app.views import Home, Summary
from django.utils import timezone
from django.urls import resolve
from datetime import datetime
from unittest.mock import (
    patch,
    MagicMock,
)
from unittest import skip
import json

MOCK_ORGANIZATION_API = {
    'organizations': [{
        '_type': 'organization',
        'name': 'Mercury Team',
        'vertical': 'default',
        'locale': None,
        'image_id': None,
        'id': '272770247903',
    }],
    'pagination': {
        'continuation': 'b2Zmc2V0LTE=',
        'has_more_items': False,
    },
}
MOCK_EVENT_API = {
    'pagination': {
        'object_count': 1,
        'page_number': 1,
        'page_size': 50,
        'page_count': 1,
        'has_more_items': False
    },
    'events': [{
        'name': {'text': 'Test event', 'html': 'Test event'},
        'description': {'text': None, 'html': None},
        'id': '50452133690',
        'url': 'https://www.eventbrite.com/e/test-event-tickets-50452133690',
        'start': {
            'timezone': 'America/Los_Angeles',
            'local': '2018-10-29T19:00:00',
            'utc': '2018-10-30T02:00:00Z'
        },
        'end': {
            'timezone': 'America/Los_Angeles',
            'local': '2018-10-29T22:00:00',
            'utc': '2018-10-30T05:00:00Z'
        },
        'organization_id': '272770247903',
        'created': '2018-09-19T17:16:39Z',
        'changed': '2018-09-24T15:06:49Z',
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
        'resource_uri': 'https://www.eventbriteapi.com/v3/events/50452133690/',
        'is_externally_ticketed': False,
        'logo': None
    }]}


class TestBase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(
            id=1,
            username='mercury_user',
            password='the_best_password_of_ever',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        self.user.set_password('the_best_password_of_ever_2')
        self.user.save()
        self.auth = UserSocialAuth.objects.create(
            user=self.user,
            provider='eventbrite',
            uid='563480245671',
            extra_data={'access_token': 'AAAAAAAAAABBBBBBBBB'},
        )
        login = self.client.login(
            username='mercury_user',
            password='the_best_password_of_ever_2'
        )
        return login


@patch('mercury_app.views.create_order_webhook_from_view', return_value='')
class HomeViewTest(TestBase):

    def setUp(self):
        super(HomeViewTest, self).setUp()

    def test_home_status_code(self, mock_create_order_webhook_from_view):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_charset(self, mock_create_order_webhook_from_view):
        response = self.client.get('/')
        self.assertEqual(response.charset, 'utf-8')

    def test_home_status_code_two(self, mock_create_order_webhook_from_view):
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)

    def test_home_resolve_home_class_view(self, mock_create_order_webhook_from_view):
        found = resolve('/')
        self.assertEquals(found.func.view_class, Home)

    def test_home_resolve_home_not_args(self, mock_create_order_webhook_from_view):
        found = resolve('/')
        self.assertEquals(found.args, ())

    def test_home_resolve_home_kwargs_empty(self, mock_create_order_webhook_from_view):
        found = resolve('/')
        self.assertEquals(found.kwargs, {'message': None})

    def test_home_resolve_home_kwargs_message_full(self, mock_create_order_webhook_from_view):
        found = resolve('/Welcome')
        self.assertEquals(found.kwargs, {'message': 'Welcome'})

    def test_home_url_name(self, mock_create_order_webhook_from_view):
        found = resolve('/')
        self.assertEqual(found.url_name, 'index')

    def test_home_none_entry(self, mock_create_order_webhook_from_view):
        response = self.client.get('/')
        self.assertNotContains(response, 'class="btn btn-success">View</a>')
        self.assertContains(response, 'Add')

    def test_home_one_entry(self, mock_create_order_webhook_from_view):
        org = Organization.objects.create(
            eb_organization_id=1, name='test_organization')
        Event.objects.create(organization=org,
                             name='Evento',
                             description='description',
                             eb_event_id=1,
                             date_tz='America/Argentina/Mendoza',
                             start_date_utc='2018-10-22T22:00:09Z',
                             end_date_utc='2018-10-22T22:00:09Z',
                             created='2017-11-23 23:33:57-03',
                             changed='2017-11-23 23:33:57-03',
                             status='completed',
                             )
        response = self.client.get('/')
        self.assertContains(response, 'View')
        self.assertContains(response, 'Add')

    def test_home_two_entry(self, mock_create_order_webhook_from_view):
        org = Organization.objects.create(
            eb_organization_id=1, name='test_organization')
        Event.objects.create(organization=org,
                             name='Evento',
                             description='description',
                             eb_event_id=1,
                             date_tz='America/Argentina/Mendoza',
                             start_date_utc='2018-10-22T22:00:09Z',
                             end_date_utc='2018-10-22T22:00:09Z',
                             created='2017-11-23 23:33:57-03',
                             changed='2017-11-23 23:33:57-03',
                             status='completed',
                             )
        Event.objects.create(organization=org,
                             name='ev',
                             description='description nueva',
                             eb_event_id=2,
                             date_tz='America/Argentina/Cordoba',
                             start_date_utc='2017-10-22T22:00:09Z',
                             end_date_utc='2017-10-22T22:00:09Z',
                             created='2016-11-23 23:33:57-03',
                             changed='2016-11-23 23:33:57-03',
                             status='completed',
                             )
        response = self.client.get('/')
        self.assertContains(response, 'ev')
        self.assertContains(response, 'View')
        self.assertContains(response, 'Add')


class HomeViewTestWithouUser(TestCase):

    def setUp(self):
        pass

    def test_home(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)


class SelectEventsLoggedTest(TestBase):

    @skip('Broken by refactor')
    @patch('mercury_app.utils.get_api_organization', return_value=MOCK_ORGANIZATION_API.get('organizations'))
    @patch('mercury_app.utils.get_api_events_org', return_value=MOCK_EVENT_API.get('events'))
    def test_template_is_rendered_successfully_with_one_event_only(self, mock_get_api_events_org, mock_get_api_organization):
        response = self.client.get('/select_events/')
        self.assertEqual(response.status_code, 200)

    @skip('Broken by refactor')
    @patch('mercury_app.utils.get_api_events_id', return_value=MOCK_EVENT_API.get('events')[0])
    def test_add_event(self, mock_get_api_events_id):
        response = self.client.post(
            '/select_events/', {'organization_id': '1234', 'organization_name': 'TestOrg'})
        event = Event.objects.get(
            eb_event_id=MOCK_EVENT_API.get('events')[0].get('id'))
        self.assertTrue(event)
        self.assertEqual(response.status_code, 302)


@patch('mercury_app.utils.Eventbrite.get')
class APICallsTest(TestCase):

    def test_get_api_organization(self, mock_api_call):
        get_api_organization('TEST')
        mock_api_call.assert_called_once()
        self.assertEquals(
            mock_api_call.call_args_list[0][0][0],
            '/users/me/organizations',
        )

    def test_get_api_orders_of_event(self, mock_api_call):
        get_api_orders_of_event('TEST', '1234')
        mock_api_call.assert_called_once()
        self.assertEquals(
            mock_api_call.call_args_list[0][0][0],
            '/events/1234/orders/',
        )
        self.assertEquals(
            mock_api_call.call_args_list[0][1]['expand'][0],
            'merchandise'
        )

    def test_get_api_events_org(self, mock_api_call):
        get_api_events_org('TEST', {'id': '5678'})
        mock_api_call.assert_called_once()
        self.assertEquals(
            mock_api_call.call_args_list[0][0][0],
            '/organizations/5678/events/',
        )

    def test_get_api_events_id(self, mock_api_call):
        get_api_events_id('TEST', '11')
        mock_api_call.assert_called_once()
        self.assertEquals(
            mock_api_call.call_args_list[0][0][0],
            '/events/11',
        )

    def test_get_api_order(self, mock_api_call):
        get_api_order('TEST', '222')
        mock_api_call.assert_called_once()
        self.assertEquals(
            mock_api_call.call_args_list[0][0][0],
            '/orders/222',
        )
        self.assertEquals(
            mock_api_call.call_args_list[0][1]['expand'][0],
            'merchandise'
        )

    @patch('mercury_app.utils.Eventbrite.post', return_value={'id': '1'})
    def test_create_webhook(self, mock_api_post_call, mock_api_get_call):
        result = create_webhook('TEST')
        mock_api_post_call.assert_called_once()
        self.assertEquals(
            mock_api_post_call.call_args_list[0][0][0],
            '/webhooks/',
        )
        self.assertEquals(result, '1')

    @patch('mercury_app.utils.Eventbrite.delete', return_value={'id': '1'})
    def test_delete_webhook(self, mock_api_delete_call, mock_api_get_call):
        UserWebhookFactory(webhook_id='7100')
        delete_webhook('TEST', '7100')
        mock_api_delete_call.assert_called_once()
        self.assertEquals(
            mock_api_delete_call.call_args_list[0][0][0],
            '/webhooks/7100/',
        )
        result = UserWebhook.objects.filter(webhook_id='7100')
        self.assertEquals(result.count(), 0)


class UtilsTest(TestCase):

    def test_get_db_event_by_id(self):
        event = EventFactory(eb_event_id=1234)
        result = get_db_event_by_id(1234)
        self.assertEqual(result, event)

    def test_get_db_event_by_id_no_result(self):
        result = get_db_event_by_id(1234)
        self.assertEqual(result, None)

    def test_get_db_merchandising_by_order_id(self):
        merchandising = MerchandiseFactory(
            order__id=15
        )
        result = get_db_merchandising_by_order_id(15)[0]
        self.assertEqual(result, merchandising)

    def test_get_db_merchandising_by_order_id_no_result(self):
        result = get_db_merchandising_by_order_id('de')
        self.assertEqual(result, None)

    def test_get_db_orders_by_event(self):
        event = EventFactory()
        OrderFactory.create_batch(10, event=event)
        result = len(get_db_orders_by_event(event))
        self.assertEqual(result, 10)

    def test_get_db_orders_by_event_no_result(self):
        fake_event = OrganizationFactory()
        result = get_db_orders_by_event(fake_event)
        self.assertEqual(result, None)

    def test_get_db_organizations_by_user(self):
        user = UserFactory()
        UserOrganizationFactory.create_batch(2, user=user)
        result = len(get_db_organizations_by_user(user))
        self.assertEqual(result, 2)

    def test_get_db_organizations_by_user_no_result(self):
        fake_user = EventFactory()
        result = get_db_organizations_by_user(fake_user)
        self.assertEqual(result, None)

    def test_get_db_events_by_organization(self):
        organization = OrganizationFactory()
        user = UserFactory()
        UserOrganizationFactory(user=user, organization=organization)
        EventFactory.create_batch(5, organization=organization)
        result = len(get_db_events_by_organization(user))
        self.assertEqual(result, 5)

    def test_get_db_events_by_organization_no_result(self):
        fake_user = EventFactory()
        result = get_db_events_by_organization(fake_user)
        self.assertEqual(result, None)

    def test_get_db_or_create_organization_by_id_create_case(self):
        org_name = 'TestOrganization'
        org_id = '23235534532'
        mock = OrganizationFactory.build(
            name=org_name, eb_organization_id=org_id)
        result = get_db_or_create_organization_by_id(org_id, org_name)
        self.assertEqual(result[0].eb_organization_id, mock.eb_organization_id)
        self.assertEqual(result[0].name, mock.name)
        self.assertTrue(result[1])

    def test_get_db_or_create_organization_by_id_get_case(self):
        org_name = 'TestOrganization'
        org_id = '23235534532'
        OrganizationFactory(name=org_name, eb_organization_id=org_id)
        mock = OrganizationFactory.build(
            name=org_name, eb_organization_id=org_id)
        result = get_db_or_create_organization_by_id(org_id, org_name)
        self.assertEqual(result[0].eb_organization_id, mock.eb_organization_id)
        self.assertEqual(result[0].name, mock.name)
        self.assertFalse(result[1])

    def test_get_db_or_create_organization_by_id_no_result(self):
        result = get_db_or_create_organization_by_id(None, None)
        self.assertEqual(result, None)

    def test_create_userorganization_assoc_create_case(self):
        org = OrganizationFactory()
        user = UserFactory()
        mock = UserOrganizationFactory.build(organization=org, user=user)
        result = create_userorganization_assoc(org, user)
        self.assertEqual(result[0].organization, mock.organization)
        self.assertEqual(result[0].user, mock.user)
        self.assertTrue(result[1])

    def test_create_userorganization_assoc_get_case(self):
        org = OrganizationFactory()
        user = UserFactory()
        UserOrganizationFactory(organization=org, user=user)
        mock = UserOrganizationFactory.build(organization=org, user=user)
        result = create_userorganization_assoc(org, user)
        self.assertEqual(result[0].organization, mock.organization)
        self.assertEqual(result[0].user, mock.user)
        self.assertFalse(result[1])

    def test_create_userorganization_assoc_get_case_no_result(self):
        result = create_userorganization_assoc(None, None)
        self.assertEqual(result, None)

    @patch('mercury_app.utils.get_api_events_org')
    @patch('mercury_app.utils.get_auth_token')
    def test_get_events_for_organizations(self, mock_get_auth_token, mock_get_api_events_org):
        fake_events = get_mock_api_event(5)
        mock_get_api_events_org.return_value = fake_events['events']
        org = OrganizationFactory(eb_organization_id=272770247903).__dict__
        result = get_events_for_organizations([org], 'patched')
        self.assertEqual(len(result), len(fake_events['events']))
        self.assertEqual(result[0]['org_name'], org['name'])

    def test_get_mock_api_event(self):
        events = get_mock_api_event(2)['events']
        creation_date = datetime.strptime(
            events[0]['created'],
            '%Y-%m-%dT%H:%M:%SZ',
        )
        self.assertEqual(len(events), 2)
        self.assertTrue(events[0]['name'])
        self.assertTrue(int(events[0]['id']) > 4999999999)
        self.assertTrue(creation_date < datetime.now())

    def test_get_mock_api_orders(self):
        orders = get_mock_api_orders(2, 1, 5532332)
        self.assertEqual(len(orders), 2)
        self.assertTrue(orders[0]['merchandise'])
        self.assertFalse(orders[1]['merchandise'])

    def test_create_event_from_api(self):
        org = OrganizationFactory(eb_organization_id=272770247903)
        result = create_event_from_api(org, get_mock_api_event(1)['events'][0])
        self.assertTrue(isinstance(result, Event))

    def test_create_event_from_api_failed(self):
        org = OrganizationFactory(eb_organization_id=272770247903)
        result = create_event_from_api(org, None)
        self.assertEqual(result, None)

    def test_create_event_orders_from_api(self):
        event = EventFactory()
        orders = get_mock_api_orders(5, 2, event.eb_event_id)
        result = create_event_orders_from_api(event, orders)
        self.assertEqual(len(result), 2)
        self.assertTrue(isinstance(result[0][0], Order))

    def test_create_event_orders_from_api_empty_order(self):
        event = EventFactory()
        orders = get_mock_api_orders(1, 1, event.eb_event_id)
        orders.append(None)
        orders.extend(get_mock_api_orders(1, 1, event.eb_event_id))
        result = create_event_orders_from_api(event, orders)
        self.assertEqual(len(result), 3)
        self.assertTrue(isinstance(result[2][0], Order))
        self.assertEqual(result[1], None)

    def test_create_merchandise_from_order(self):
        result = []
        event = EventFactory()
        order = OrderFactory(event=event)
        api_order = get_mock_api_orders(1, 1, event.eb_event_id)[0]
        for item in api_order['merchandise']:
            result.append(create_merchandise_from_order(item, order))
        self.assertEqual(len(result), 2)
        self.assertTrue(isinstance(result[0], Merchandise))

    def test_create_merchandise_from_order_failed(self):
        result = []
        event = EventFactory()
        order = None
        api_order = get_mock_api_orders(1, 1, event.eb_event_id)[0]
        for item in api_order['merchandise']:
            result.append(create_merchandise_from_order(item, order))
        self.assertEqual(result[0], None)

    def test_create_transaction(self):
        tx = create_transaction(UserFactory(), MerchandiseFactory(), 'TEST NOTE', 'iPhone', 'HA')
        self.assertTrue(isinstance(tx, Transaction))
        self.assertEqual(tx.notes, 'TEST NOTE')

    def test_get_db_transaction_by_merchandise(self):
        merchandise = MerchandiseFactory()
        tx = TransactionFactory(merchandise=merchandise)
        result = get_db_transaction_by_merchandise(merchandise)
        self.assertEqual(result[0], tx)

    def test_get_db_transaction_by_merchandise_failed(self):
        result = get_db_transaction_by_merchandise(UserFactory())
        self.assertEqual(result, None)

    def test_get_db_items_left_hand(self):
        merchandise = MerchandiseFactory(quantity=2, order__id=99)
        merchandising_query_obj = get_db_merchandising_by_order_id(99)
        TransactionFactory(
            merchandise=merchandising_query_obj[0],
            operation_type='HA',
        )
        items_left = get_db_items_left(merchandising_query_obj)
        result = items_left[0].get('items_left')
        self.assertEqual(result, 1)

    def test_get_db_items_left_refund(self):
        merchandise = MerchandiseFactory(quantity=2, order__id=99)
        merchandising_query_obj = get_db_merchandising_by_order_id(99)
        TransactionFactory(
            merchandise=merchandising_query_obj[0],
            operation_type='HA',
        )
        TransactionFactory(
            merchandise=merchandising_query_obj[0],
            operation_type='RE',
        )
        items_left = get_db_items_left(merchandising_query_obj)
        result = items_left[0].get('items_left')
        self.assertEqual(result, 2)

class UtilsWebhook(TestBase):

    def test_get_auth_token(self):
        result = get_auth_token(
            get_user_model().objects.get(username='mercury_user'))
        self.assertEqual(result, 'AAAAAAAAAABBBBBBBBB')

    def test_get_auth_token_does_not_exist(self):
        result = get_auth_token(UserFactory())
        self.assertEqual(result, '')

    def test_webhook_available_to_process(self):
        user_id = '563480245671'
        self.assertTrue(webhook_available_to_process(user_id))

    def test_webhook_not_available_to_process(self):
        user_id = '5630245671'
        self.assertFalse(webhook_available_to_process(user_id))

    def test_social_user_exists(self):
        user_id = '563480245671'
        self.assertTrue(social_user_exists(user_id))

    def test_social_user_not_exists(self):
        user_id = '5630245671'
        self.assertFalse(social_user_exists(user_id))

    def test_get_social_user_id(self):
        result = get_social_user_id(563480245671)
        self.assertEqual(result, 1)

    def test_get_social_user(self):
        result = get_social_user(563480245671)
        self.assertEqual(result.user_id, 1)


    @patch('mercury_app.utils.get_api_order', return_value=get_mock_api_orders(1, 1, '1')[0])
    def test_get_data(self, mock_get_api_order):
        request = MagicMock(
            body='{"config": {"action": "order.placed", "user_id": 563480245671, "endpoint_url": "https://ebmercury.herokuapp.com/webhook-point/", "webhook_id": 799325}, "api_url": "https://www.eventbriteapi.com/v3/orders/834225363/"}'
        )
        org = OrganizationFactory(eb_organization_id=1)
        UserOrganizationFactory(
            user=get_user_model().objects.get(username='mercury_user'),
            organization=org
        )
        EventFactory(eb_event_id=1, organization=org)
        result = get_data(json.loads(request.body),
                          request.build_absolute_uri('/')[:-1])
        self.assertTrue(result['status'])

    @patch('mercury_app.utils.get_api_order', return_value=get_mock_api_orders(1, 1, 1)[0])
    def test_get_data(self, mock_get_api_order):
        request = MagicMock(
            body='{"config": {"action": "order.placed", "user_id": 45671, "endpoint_url": "https://ebmercury.herokuapp.com/webhook-point/", "webhook_id": 799325}, "api_url": "https://www.eventbriteapi.com/v3/orders/834225363/"}'
        )
        result = get_data(json.loads(request.body),
                          request.build_absolute_uri('/')[:-1])
        self.assertFalse(result['status'])

    @patch('mercury_app.utils.create_webhook', return_value=1231241)
    def test_create_order_webhook_from_view(self, mock_create_webhook):
        user = UserFactory()
        result = UserWebhook.objects.all().count()
        self.assertEqual(result, 0)
        create_order_webhook_from_view(user)
        result = UserWebhook.objects.all().count()
        self.assertEqual(result, 1)


class SelectEventsNotLoggedRedirectTest(TestCase):

    def test_redirect_not_logged_in(self):
        response = self.client.get('/select_events/')
        self.assertEqual(response.status_code, 302)


class EventOrdersNotLoggedRedirectTest(TestCase):

    def test_redirect_not_logged_in(self):
        response = self.client.get('/events/32423/orders')
        self.assertEqual(response.status_code, 302)


class OrganizationModelTest(TestCase):

    def create_organization(
        self, name='Organization',
        eb_organization_id=23223
    ):
        return Organization.objects.create(
            name=name,
            eb_organization_id=eb_organization_id
        )

    def test_organization_creation(self):
        organization = self.create_organization()
        self.assertTrue(isinstance(organization, Organization))
        self.assertEqual(organization.__string__(), organization.name)


class EventModelTest(TestCase):

    def create_event(
        self,
        name='event1',
        description='this is an event',
        eb_event_id='123', date_tz=timezone.now(),
        start_date_utc=timezone.now(), end_date_utc=timezone.now(),
        created=timezone.now(), changed=timezone.now(), status='created'
    ):
        organization = Organization.objects.create(
            eb_organization_id=23223,
            name='Eventbrite')
        return Event.objects.create(
            name=name, organization=organization,
            description=description, eb_event_id=eb_event_id,
            date_tz=date_tz, start_date_utc=start_date_utc,
            end_date_utc=end_date_utc, created=created,
            changed=changed, status=status
        )

    def test_event_creation(self):
        event = self.create_event()
        self.assertTrue(isinstance(event, Event))
        self.assertEqual(event.__string__(), event.name)


class OrderModelTest(TestCase):

    def create_order(
        self, name='order', eb_order_id=2323, changed=timezone.now(),
        created=timezone.now(), status='pending', email='hola@hola',
        merch_status='PE'
    ):
        organization = Organization.objects.create(
            eb_organization_id=23223, name='Eventbrite'
        )
        event = Event.objects.create(
            name='event', organization=organization, description='event1',
            eb_event_id='456', date_tz=timezone.now(),
            start_date_utc=timezone.now(), end_date_utc=timezone.now(),
            created=timezone.now(), changed=timezone.now(), status='pending')
        return Order.objects.create(
            eb_order_id=eb_order_id, event=event, changed=changed,
            created=created, name=name, status=status, email=email,
            merch_status=merch_status
        )

    def test_order_creation(self):
        order = self.create_order()
        self.assertTrue(isinstance(order, Order))
        self.assertEqual(order.__string__(), order.name)


class MerchandiseModelTest(TestCase):

    def create_merchandise(
        self, name='Remeras', item_type='talle l', currency='USD',
        value='508730',
    ):
        organization = Organization.objects.create(
            eb_organization_id=23223,
            name='Eventbrite')
        event = Event.objects.create(
            name='event', organization=organization,
            description='event1', eb_event_id='456',
            date_tz=timezone.now(), start_date_utc=timezone.now(),
            end_date_utc=timezone.now(), created=timezone.now(),
            changed=timezone.now(), status='pending'
        )
        order = Order.objects.create(
            name='order', event=event,
            eb_order_id=2323, changed=timezone.now(),
            created=timezone.now(), status='pending',
            email='hola@hola', merch_status='PE')
        return Merchandise.objects.create(
            order=order, name=name, item_type=item_type,
            currency=currency, value=value)

    def test_merchandise_creation(self):
        merchandise = self.create_merchandise()
        self.assertTrue(isinstance(merchandise, Merchandise))
        self.assertEqual(merchandise.__string__(), merchandise.name)


class UserOrganizationModelTest(TestBase):

    def create_user_organization(self):
        organization = Organization.objects.create(
            eb_organization_id=23223, name='Eventbrite'
        )
        return UserOrganization.objects.create(
            user=self.user, organization=organization
        )

    def test_user_organization_creation(self):
        user_organization = self.create_user_organization()
        self.assertTrue(isinstance(user_organization, UserOrganization))


class SummaryTest(TestBase):

    def setUp(self):
        super(SummaryTest, self).setUp()
        self.order = OrderFactory()
        self.maxDiff = None

    def test_get_context_data(self):
        event = EventFactory()
        order = OrderFactory(event=event)
        mercha = MerchandiseFactory(order=order)
        response = self.client.get(
            '/event/{}/summary/'.format(event.eb_event_id))
        self.assertIsNotNone(response.context['data_handed_over_dont'])
        self.assertIsNotNone(response.context['event'])
        self.assertIsNotNone(response.context['data_tipes_handed'])

    def test_get_json_donut(self):
        expected = {'quantity': 1, 'percentage': 1,
                    'name': 'nombre', 'id': 2}
        result = get_json_donut(1, 'nombre', 2)
        self.assertEqual(expected, result)

    def test_get_summary_handed_over_dont_json_one(self):
        expected = ([{'quantity': 0, 'percentage': 0,
                      'name': 'Orders Handed', 'id': 1},
                     {'quantity': 100, 'percentage': 100,
                      'name': 'Orders don\'t handed', 'id': 2}])
        mercha = MerchandiseFactory()
        result = get_summary_handed_over_dont_json([mercha.order.id])
        self.assertEqual(expected, result)

    def test_get_summary_handed_over_dont_json_two(self):
        expected = ([{'quantity': 100, 'percentage': 100,
                      'name': 'Orders Handed', 'id': 1},
                     {'quantity': 0, 'percentage': 0,
                      'name': 'Orders don\'t handed', 'id': 2}])
        mercha = MerchandiseFactory(quantity=1)
        TransactionFactory(
            merchandise=mercha,
            operation_type='HA',
        )
        result = get_summary_handed_over_dont_json([mercha.order.id])
        self.assertEqual(expected, result)

    def test_get_summary_handed_over_dont_json_three(self):
        expected = ([{'quantity': 66.7, 'percentage': 66.7,
                      'name': 'Orders Handed', 'id': 1},
                     {'quantity': 33.3, 'percentage': 33.3,
                      'name': 'Orders don\'t handed', 'id': 2}])
        mercha = MerchandiseFactory(name='Gorra',
                                    quantity=3,
                                    order=self.order)
        TransactionFactory(
            merchandise=mercha,
            operation_type='HA',
        )
        TransactionFactory(
            merchandise=mercha,
            operation_type='HA',
        )
        result = get_summary_handed_over_dont_json([self.order.id])
        self.assertEqual(expected, result)

    def test_get_summary_handed_over_dont_json_four(self):
        expected = ([{'quantity': 33.3, 'percentage': 33.3,
                      'name': 'Orders Handed', 'id': 1},
                     {'quantity': 66.7, 'percentage': 66.7,
                      'name': 'Orders don\'t handed', 'id': 2}])
        mercha = MerchandiseFactory(name='Gorra',
                                    quantity=3,
                                    order=self.order)
        TransactionFactory(
            merchandise=mercha,
            operation_type='HA',
        )
        result = get_summary_handed_over_dont_json([self.order.id])
        self.assertEqual(expected, result)

    def test_get_summary_types_handed_one(self):
        expected = ([[{'quantity': 100.0, 'percentage': 100.0,
                       'name': 'Gorra handed', 'id': 1},
                      {'quantity': 0.0, 'percentage': 0.0,
                       'name': 'Gorra don\'t handed', 'id': 2}]])
        mercha = MerchandiseFactory(name='Gorra',
                                    quantity=1,
                                    order=self.order)
        TransactionFactory(
            merchandise=mercha,
            operation_type='HA',
        )
        result = get_summary_types_handed([self.order.id])
        self.assertEqual(expected, result)

    def test_get_summary_types_handed_two(self):
        expected = ([[{'quantity': 100.0, 'percentage': 100.0,
                       'name': 'Gorra handed', 'id': 1},
                      {'quantity': 0.0, 'percentage': 0.0,
                       'name': 'Gorra don\'t handed', 'id': 2}],
                     [{'quantity': 100.0, 'percentage': 100.0,
                       'name': 'Remera handed', 'id': 1},
                      {'quantity': 0.0, 'percentage': 0.0,
                       'name': 'Remera don\'t handed', 'id': 2}]
                     ])
        mercha_one = MerchandiseFactory(name='Gorra',
                                        quantity=1,
                                        order=self.order)
        mercha_two = MerchandiseFactory(name='Remera',
                                        quantity=1,
                                        order=self.order)
        TransactionFactory(
            merchandise=mercha_one,
            operation_type='HA',
        )
        TransactionFactory(
            merchandise=mercha_two,
            operation_type='HA',
        )
        result = get_summary_types_handed([self.order.id])
        self.assertEqual(expected, result)

    def test_get_summary_types_handed_three(self):
        expected = ([[{'quantity': 0.0, 'percentage': 0.0,
                       'name': 'Gorra handed', 'id': 1},
                      {'quantity': 100.0, 'percentage': 100.0,
                       'name': 'Gorra don\'t handed', 'id': 2}],
                     [{'quantity': 0.0, 'percentage': 0.0,
                       'name': 'Remera handed', 'id': 1},
                      {'quantity': 100.0, 'percentage': 100.0,
                       'name': 'Remera don\'t handed', 'id': 2}]
                     ])
        MerchandiseFactory(name='Gorra',
                           quantity=1,
                           order=self.order)
        MerchandiseFactory(name='Remera',
                           quantity=1,
                           order=self.order)
        result = get_summary_types_handed([self.order.id])
        self.assertEqual(expected, result)

    def test_get_summary_types_handed_four(self):
        expected = ([
            [
                {
                    'quantity': 0.0,
                    'percentage': 0.0,
                    'name': 'Gorra2 handed',
                    'id': 1,
                },
                {
                    'quantity': 100.0,
                    'percentage': 100.0,
                    'name': 'Gorra2 don\'t handed',
                    'id': 2,
                },
            ],
            [
                {
                    'quantity': 100.0,
                    'percentage': 100.0,
                    'name': 'Remera2 handed',
                    'id': 1,
                },
                {
                    'quantity': 0.0,
                    'percentage': 0.0,
                    'name': 'Remera2 don\'t handed',
                    'id': 2,
                },
            ],
        ])
        new_order = OrderFactory()
        MerchandiseFactory(
            name='Gorra2',
            quantity=1,
            order=new_order,
        )
        mercha = MerchandiseFactory(
            name='Remera2',
            quantity=1,
            order=new_order,
        )
        TransactionFactory(
            merchandise=mercha,
            operation_type='HA',
        )
        result = get_summary_types_handed([new_order.id])
        self.assertEqual(expected, result)

    def test_summary_resolve_home_class_view(self):
        found = resolve('/event/50781817784/summary/')
        self.assertEquals(found.func.view_class, Summary)


class ListItemMerchandisingTest(TestBase):

    def setUp(self):
        super(ListItemMerchandisingTest, self).setUp()

    def test_merchandise_one_entry(self):
        MerchandiseFactory(name='Camiseta', order__id=5)
        response = self.client.get('/view_order/5/')
        self.assertContains(response, 'Camiseta')

    def test_merchandise_status_code(self):
        MerchandiseFactory(name='Camiseta', order__id=4)
        response = self.client.get('/view_order/4/')
        self.assertEqual(response.status_code, 200)

    def test_merchandise_delivered(self):
        merchandise = MerchandiseFactory(
            name='Gorra',
            quantity=1,
            order__id=5
        )
        TransactionFactory(
            merchandise=merchandise,
            operation_type='HA'
        )
        response = self.client.get('/view_order/5/')
        self.assertContains(response, 'Yes')

    def test_merchandise_partial_delivery(self):
        merchandise = MerchandiseFactory(
            name='Gorra',
            quantity=2,
            order__id=5
        )
        TransactionFactory(
            merchandise=merchandise,
            operation_type='HA'
        )
        response = self.client.get('/view_order/5/')
        self.assertContains(response, 'Partially')

    def test_merchandise_delivered_two(self):
        merchandise = MerchandiseFactory(
            name='Gorra',
            quantity=2,
            order__id=5
        )
        TransactionFactory(
            merchandise=merchandise,
            operation_type='HA'
        )
        TransactionFactory(
            merchandise=merchandise,
            operation_type='HA'
        )
        response = self.client.get('/view_order/5/')
        # import ipdb; ipdb.set_trace()
        self.assertContains(response, 'Yes')

    def test_merchandise_post_form(self):
        merchandise = MerchandiseFactory(
            eb_merchandising_id=123,
            name='Gorra',
            quantity=1,
            order__id=7
        )

        response = self.client.post(
            '/view_order/7/', {'123': '1', 'csrftoken': 'TEST'})
        self.assertEqual(response.status_code, 302)
        transaction_count = Transaction.objects.filter(
            merchandise=merchandise
        ).count()
        self.assertEqual(transaction_count, 1)


@patch('mercury_app.views.create_order_webhook_from_view', return_value='')
class OrderListTest(TestBase):

    def test_order_status_code(self, mock_webhook):
        OrderFactory()
        response = self.client.get('/view_order/9/')
        self.assertEqual(response.status_code, 200)

    def test_create_order(self, mock_webhook):
        event = EventFactory()
        OrderFactory(name='Jaime Bond', event=event)
        response = self.client.get('/event/{}/orders/'.format(
            event.eb_event_id)
        )
        self.assertContains(response, 'Jaime Bond')
