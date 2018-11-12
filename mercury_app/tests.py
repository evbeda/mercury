from django.test import TestCase
from social_django.models import UserSocialAuth
from factory import fuzzy
from django.contrib.auth import get_user_model
import fakeredis
from .models import (
    Event,
    Organization,
    UserOrganization,
    Order,
    Merchandise,
    UserWebhook,
    Transaction,
    Attendee,
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
    AttendeeFactory,
)
from .pdf_utils import pdf_merchandise
from django.template import loader
from .utils import (
    get_auth_token,
    get_events_mercha_and_badges,
    get_email_pdf_context,
    get_merchas_for_email,
    create_event_complete,
    get_api_organization,
    get_summary_orders,
    get_api_events_org,
    get_api_events_id,
    get_percentage_handed,
    get_api_orders_of_event,
    get_api_order_barcode,
    get_api_order_attendees,
    get_api_attendee_checked,
    create_webhook,
    delete_webhook,
    get_events_for_organizations,
    get_db_event_by_id,
    get_db_order_by_id,
    get_db_merchandising_by_order_id,
    get_db_orders_by_event,
    get_db_events_by_organization,
    get_db_organizations_by_user,
    get_db_or_create_organization_by_id,
    get_db_transaction_by_merchandise,
    get_db_items_left,
    get_db_attendee_from_barcode,
    update_db_merch_status,
    create_userorganization_assoc,
    create_event_orders_from_api,
    create_event_from_api,
    create_merchandise_from_order,
    create_attendee_from_order,
    create_transaction,
    create_order_atomic,
    update_attendee_checked_from_api,
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
    create_order_webhook_from_view,
    delete_events,
    send_email_alert,
)
from mercury_app.views import Home, Summary
from django.utils import timezone
from django.urls import resolve
from datetime import datetime
from unittest.mock import (
    patch,
    MagicMock,
)
from mercury_app.mock_api import MOCK_API_ATTENDEE
import json
from unittest import skip


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


class TestMerchandise(TestCase):
    def test_quantity_handed(self):
        merchandise = MerchandiseFactory()
        date = datetime.now(tz=timezone.utc)
        TransactionFactory(
            merchandise=merchandise, operation_type='HA', date=date)
        result = merchandise.quantity_handed(date)
        self.assertEqual(result, 1)

    def test_quantity_handed_two(self):
        merchandise = MerchandiseFactory()
        date = datetime.now(tz=timezone.utc)
        TransactionFactory(merchandise=merchandise,
                           operation_type='HA',
                           date=date)
        TransactionFactory(merchandise=merchandise,
                           operation_type='HA',
                           date=date)
        result = merchandise.quantity_handed(date)
        self.assertEqual(result, 2)

    def test_quantity_handed_three(self):
        merchandise = MerchandiseFactory()
        date = datetime.now(tz=timezone.utc)
        TransactionFactory(merchandise=merchandise,
                           operation_type='HA',
                           date=date)
        TransactionFactory(merchandise=merchandise,
                           operation_type='HA',
                           date=date)
        TransactionFactory(merchandise=merchandise,
                           operation_type='HA',
                           date=date)
        result = merchandise.quantity_handed(date)
        self.assertEqual(result, 3)


class TestBase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(
            username='mercury_user',
            password='the_best_password_of_ever',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        self.user.set_password('the_best_password_of_ever_2')
        self.user.save()
        self.social_auth_user_id_fuzzy = fuzzy.FuzzyInteger(50000000000, 60000000000)
        self.auth = UserSocialAuth.objects.create(
            user=self.user,
            provider='eventbrite',
            uid=self.social_auth_user_id_fuzzy,
            extra_data={'access_token': 'AAAAAAAAAABBBBBBBBB'},
        )
        self.social_auth_user_id = UserSocialAuth.objects.get(user=self.user).uid
        login = self.client.login(
            username='mercury_user',
            password='the_best_password_of_ever_2'
        )
        return login


@patch('badges_app.views.redis_conn', return_value=fakeredis.FakeStrictRedis())
class TestRedisPrinterOrder(TestBase):
    def test_redis_connect_ok(self, mock_redis):
        att = AttendeeFactory()
        response = self.client.get(
            '/event/{}/attendee/{}/print/'.format(
                att.order.event.eb_event_id,
                att.eb_attendee_id
            )
        )
        self.assertEqual(response.status_code, 302)


@patch('mercury_app.views.create_order_webhook_from_view', return_value='')
class TestActivateLanguageView(TestBase):

    def setUp(self):
        super(TestActivateLanguageView, self).setUp()

    def test_status_code(self, mock_create_order_webhook_from_view):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

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
        self.assertNotContains(response, 'search')
        self.assertContains(response, 'Add')


    @skip('Could not find a way to properly mock')
    @patch('mercury_app.models.Event.is_processing', return_value=True)
    def test_home_processing_entry(self, mock_create_order_webhook_from_view, mock_is_processing):
        org = OrganizationFactory()
        UserOrganizationFactory(user=self.user, organization=org)
        EventFactory(organization=org)
        response = self.client.get('/')
        self.assertContains(response, 'Processing')
        self.assertNotContains(response, 'search')
        self.assertContains(response, 'Add')

    @patch('mercury_app.models.Event.is_processing', return_value=False)
    def test_home_one_entry(self, mock_create_order_webhook_from_view, mock_is_processing):
        org = OrganizationFactory()
        UserOrganizationFactory(user=self.user, organization=org)
        EventFactory(organization=org)
        response = self.client.get('/')
        self.assertContains(response, 'Add')

    @patch('mercury_app.models.Event.is_processing', return_value=False)
    def test_home_two_entry(self, mock_create_order_webhook_from_view, mock_is_processing):
        org = OrganizationFactory()
        UserOrganizationFactory(user=self.user, organization=org)
        EventFactory(name='Hello', organization=org)
        EventFactory(name='Goodbye', organization=org)
        response = self.client.get('/')
        self.assertContains(response, 'Hello')
        self.assertContains(response, 'Goodbye')
        self.assertContains(response, 'Add')


class HomeViewTestWithoutUser(TestCase):

    def setUp(self):
        pass

    def test_home(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)


class SelectEventsLoggedTest(TestBase):

    @patch('mercury_app.views.get_api_organization')
    @patch('mercury_app.views.get_events_for_organizations')
    def test_template_is_rendered_successfully_with_one_event_only(self, mock_get_events_for_organizations, mock_get_api_organization):
        mock_get_api_organization.return_value = MOCK_ORGANIZATION_API.get(
            'organizations')
        fake_events = get_mock_api_event(1)
        mock_get_events_for_organizations.return_value = fake_events[
            'events'], fake_events['pagination']
        response = self.client.get('/select_events/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add')

    @patch('mercury_app.views.get_api_organization')
    @patch('mercury_app.views.get_events_for_organizations')
    def test_template_is_rendered_successfully_with_five_events(self, mock_get_events_for_organizations, mock_get_api_organization):
        mock_get_api_organization.return_value = MOCK_ORGANIZATION_API.get(
            'organizations')
        fake_events = get_mock_api_event(1)
        mock_get_events_for_organizations.return_value = fake_events[
            'events'], fake_events['pagination']
        response = self.client.get('/select_events/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add')

    @patch('mercury_app.views.cache')
    @patch('mercury_app.views.create_event_orders_from_api')
    @patch('mercury_app.utils.get_api_events_id', return_value=get_mock_api_event(1, 1000).get('events')[0])
    def test_add_event(self, mock_get_api_events_id, mock_create_event_orders_from_api, mock_cache):
        with self.settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}):
            response = self.client.post(
                '/select_events/', data={'org_id_51960795137': '279503785013', 'org_name_51960795137': 'Mercury Mercury', "badges_51960795137" : 'on', "merchandise_51960795137" : 'on'})
        event = Event.objects.get(
            eb_event_id=1000
        )
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

    @patch('mercury_app.utils.has_continuation', return_value=False)
    def test_get_api_orders_of_event(self, mock_has_continuation, mock_api_call):
        get_api_orders_of_event('TEST', '1234')
        mock_api_call.assert_called_once()
        self.assertEquals(
            mock_api_call.call_args_list[0][0][0],
            '/events/1234/orders/?page=1',
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
            '/organizations/5678/events/?page=1',
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

    def test_get_api_order_barcode(self, mock_api_call):
        get_api_order_barcode('TEST', '111', '1115555')
        mock_api_call.assert_called_once()
        self.assertEquals(
            mock_api_call.call_args_list[0][0][0],
            '/organizations/111/orders/search?barcodes=1115555',
        )

    @patch('mercury_app.utils.has_continuation', return_value=False)
    def test_get_api_order_attendees(self, mock_continuation, mock_api_call):
        get_api_order_attendees('TEST', '222')
        mock_api_call.assert_called_once()
        self.assertEquals(
            mock_api_call.call_args_list[0][0][0],
            '/orders/222/attendees/?page=1',
        )

    def test_get_api_attendee_checked(self, mock_api_call):
        get_api_attendee_checked('TEST', '2342', '34532')
        mock_api_call.assert_called_once()
        self.assertEquals(
            mock_api_call.call_args_list[0][0][0],
            '/events/34532/attendees/2342/',
        )

    @patch('mercury_app.utils.Eventbrite.post', return_value={'id': '1'})
    def test_create_webhook(self, mock_api_post_call, mock_api_get_call):
        result = create_webhook('TEST')
        mock_api_post_call.assert_called()
        self.assertEquals(
            mock_api_post_call.call_args_list[0][0][0],
            '/webhooks/',
        )
        self.assertEquals(result, ('1', '1'))

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


class UtilsTest(TestBase):

    def test_get_merchas_for_email(self):
        order = OrderFactory(id=20, email="algun@email.com")
        merchandises = [MerchandiseFactory(
            name="Gorra", item_type="Roja", order=order)]
        date = datetime.now(tz=timezone.utc)
        result = get_merchas_for_email(merchandises, date)
        expected = ([["Gorra", "Roja", 0]], 20, "algun@email.com")
        self.assertEqual(expected, result)

    def test_get_merchas_for_email_two(self):
        order = OrderFactory(id=20, email="algun@email.com")
        merchandises = [MerchandiseFactory(
            name="Gorra", item_type="Azul", order=order)]
        date = datetime.now(tz=timezone.utc)
        TransactionFactory(merchandise=merchandises[0],
                           operation_type='HA',
                           date=date)
        result = get_merchas_for_email(merchandises, date)
        expected = ([["Gorra", "Azul", 1]], 20, "algun@email.com")
        self.assertEqual(expected, result)

    @patch('django.template.loader.get_template', return_value=loader.get_template('404.html'))
    @patch('mercury_app.utils.send_mail', return_value=0)
    def test_send_email_alert(self, mock_send_email, mock_template):
        expected = {'transactions': [["gorra", "red"]],
                    'date': '2018-10-23 13:49:30',
                    'operation': 'HA',
                    'order_id': 1}
        param = [['gorra',
                  'red',
                  ]]
        result = send_email_alert(json.dumps(param),
                                  'navarro_lautaro@hotmail.com',
                                  '2018-10-23 13:49:30',
                                  'HA',
                                  1)
        self.assertEqual(expected, result)

    def test_get_db_event_by_id(self):
        event = EventFactory(eb_event_id=1234)
        result = get_db_event_by_id(1234)
        self.assertEqual(result, event)

    def test_get_db_order_by_id(self):
        order = OrderFactory(id=4)
        result = get_db_order_by_id(4)
        self.assertEqual(result, order)

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

    def test_get_db_attendee_from_barcode(self):
        event = EventFactory()
        att = AttendeeFactory(order__event=event)
        result = get_db_attendee_from_barcode(att.barcode, event.eb_event_id)
        self.assertEqual(int(result.eb_attendee_id), att.eb_attendee_id)

    def test_get_db_attendee_from_barcode_no_result(self):
        result = get_db_attendee_from_barcode('322', '111')
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

    @patch('mercury_app.utils.get_api_attendee_checked')
    def test_update_attendee_checked_from_api(self, mock_get_api_attendee_checked):
        mock_get_api_attendee_checked.return_value = {'barcodes': [{'status': 'used'}]}
        att = AttendeeFactory()
        update_attendee_checked_from_api(self.user, att.barcode)
        att_search = Attendee.objects.get(barcode=att.barcode)
        self.assertEqual(att_search.checked_in, True)

    @patch('mercury_app.utils.get_api_attendee_checked')
    def test_update_attendee_checked_from_api(self, mock_get_api_attendee_checked):
        mock_get_api_attendee_checked.return_value = {'barcodes': [{'status': 'used'}]}
        att = AttendeeFactory()
        update_attendee_checked_from_api(self.user, eb_attendee_id=att.eb_attendee_id)
        att_search = Attendee.objects.get(eb_attendee_id=att.eb_attendee_id)
        self.assertEqual(att_search.checked_in, True)

    @patch('mercury_app.utils.get_api_events_org')
    @patch('mercury_app.utils.get_auth_token')
    def test_get_events_for_organizations(self, mock_get_auth_token, mock_get_api_events_org):
        fake_events = get_mock_api_event(2)
        mock_get_api_events_org.return_value = fake_events['events'], fake_events['pagination']
        org = OrganizationFactory(eb_organization_id=272770247903).__dict__
        result = get_events_for_organizations([org], 'patched', 1)
        self.assertEqual(len(result), len(fake_events['events']))
        self.assertEqual(result[0][0]['org_name'], org['name'])

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
        self.assertTrue(isinstance(result[0], Event))

    def test_create_event_from_api_failed(self):
        org = OrganizationFactory(eb_organization_id=272770247903)
        result = create_event_from_api(org, None)
        self.assertEqual(result, None)

    @patch('mercury_app.utils.cache')
    @patch('mercury_app.utils.create_order_atomic.delay')
    @patch('mercury_app.utils.get_api_orders_of_event')
    def test_create_event_orders_from_api(self, mock_get_api_orders_of_event, mock_create_order_atomic, mock_cache):
        event = EventFactory()
        mock_create_order_atomic.return_value = OrderFactory()
        mock_get_api_orders_of_event.return_value = get_mock_api_orders(3, 3, event.eb_event_id)
        userid = self.user.id
        result = create_event_orders_from_api(userid, event.id)
        self.assertEqual(len(result), 3)
        self.assertTrue(isinstance(result[0], Order))

    @patch('mercury_app.utils.get_api_events_id')
    @patch('mercury_app.utils.create_event_from_api')
    def test_create_event_complete(self,
                                   mock_create_event_from_api,
                                   mock_get_api_events_id):
        mock_get_api_events_id.return_value.return_value = get_mock_api_event(1, 1000).get('events')[0]
        mock_create_event_from_api.return_value =  (Event(eb_event_id=1231241), True)
        with self.settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}):
            result = create_event_complete(self.user,
                              1242341,
                              1231241,
                              1231231,
                              "Organization name",
                              True,
                              False)
        expected = 'The event was successfully added!'
        self.assertEqual(result, expected)

    @patch('mercury_app.utils.cache')
    @patch('mercury_app.utils.get_api_events_id')
    @patch('mercury_app.utils.create_event_from_api')
    def test_create_event_complete_two(self,
                                   mock_create_event_from_api,
                                   mock_get_api_events_id,
                                   mock_cache):
        mock_get_api_events_id.return_value.return_value = get_mock_api_event(1, 1000).get('events')[0]
        mock_create_event_from_api.return_value =  (None, False)
        result = create_event_complete(self.user,
                          1242341,
                          1231241,
                          1231231,
                          "Organization name",
                          True,
                          False)
        expected = 'An error has occured while adding the event'
        self.assertEqual(result, expected)

    def test_get_events_mercha_and_badges(self):
        data = {'org_id_51960795137': ['279503785013'],
                'org_name_51960795137': ['Mercury Mercury'],
                'badges_51960795137': ['on'],
                'merchandise_51960795137':['on']}.items()
        result = get_events_mercha_and_badges(data)
        expected = {'51960795137': {'merchandise': True, 'badges': True}}
        self.assertEqual(result, expected)

    def test_get_events_mercha_and_badges_two(self):
        data = {'org_id_51960795137': ['279503785013'],
                'org_name_51960795137': ['Mercury Mercury'],
                'merchandise_51960795137':['on']}.items()
        result = get_events_mercha_and_badges(data)
        expected = {'51960795137': {'merchandise': True, 'badges': False}}
        self.assertEqual(result, expected)

    def test_get_events_mercha_and_badges_three(self):
        data = {'org_id_51960795137': ['279503785013'],
                'org_name_51960795137': ['Mercury Mercury']}.items()
        result = get_events_mercha_and_badges(data)
        expected = {}
        self.assertEqual(result, expected)

    def test_get_events_mercha_and_badges_four(self):
        data = {'org_id_51960795137': ['279503785013'],
                'org_name_51960795137': ['Mercury Mercury'],
                'badges_51960795137': ['on'],
                'merchandise_51960795137':['on'],
                'org_id_51960795134': ['279503785013'],
                'org_name_51960795134': ['Mercury Mercury'],
                'merchandise_51960795134':['on']}.items()
        result = get_events_mercha_and_badges(data)
        expected = {'51960795137': {'merchandise': True, 'badges': True},
                    '51960795134': {'merchandise': True, 'badges': False}}
        self.assertEqual(result, expected)


    @patch('mercury_app.utils.get_api_order_attendees', return_value=MOCK_API_ATTENDEE['attendees'])
    def test_create_attendee_from_order(self, mock_get_api_order_attendees):
        order = OrderFactory(eb_order_id=846464739)
        result = create_attendee_from_order(self.user.id, order)
        self.assertEquals(result[0].first_name, 'Jane')

    @patch('mercury_app.utils.cache')
    @patch('mercury_app.utils.create_order_atomic.delay')
    @patch('mercury_app.utils.get_api_orders_of_event')
    def test_create_event_orders_from_api_empty_order(self, mock_get_api_orders_of_event, mock_create_order_atomic, mock_cache):
        event = EventFactory()
        orders = get_mock_api_orders(1, 1, event.eb_event_id)
        orders.append(None)
        orders.extend(get_mock_api_orders(1, 1, event.eb_event_id))
        mock_create_order_atomic.return_value = OrderFactory()
        mock_get_api_orders_of_event.return_value = orders
        result = create_event_orders_from_api(self.user.id, event.id, orders)
        self.assertEqual(len(result), 2)
        self.assertTrue(isinstance(result[1], Order))

    @patch('mercury_app.utils.create_merchandise_from_order')
    @patch('mercury_app.utils.create_attendee_from_order')
    def test_create_order_atomic_success_w_merchandise(self, mock_create_attendee_from_order, mock_create_merchandise_from_order):
        event = EventFactory(eb_event_id=444)
        order = get_mock_api_orders(1, 1, 444)
        result = create_order_atomic(self.user.id, event.id, order[0], True)
        self.assertTrue(isinstance(result, Order))

    @patch('mercury_app.utils.create_merchandise_from_order')
    @patch('mercury_app.utils.create_attendee_from_order')
    def test_create_order_atomic_success_wo_merchandise(self, mock_create_attendee_from_order, mock_create_merchandise_from_order):
        event = EventFactory(eb_event_id=444)
        order = get_mock_api_orders(1, 0, 444)
        result = create_order_atomic(self.user.id, event.id, order[0], False)
        self.assertTrue(isinstance(result, Order))

    @patch('mercury_app.utils.create_merchandise_from_order')
    @patch('mercury_app.utils.create_attendee_from_order', side_effect=Exception())
    def test_create_order_atomic_fail(self, mock_create_attendee_from_order, mock_create_merchandise_from_order):
        event = EventFactory(eb_event_id=444)
        order = get_mock_api_orders(1, 1, 444)
        with self.assertRaises(Exception):
            result = create_order_atomic(self.user.id, event.id, order[0])
            self.assertFail()
        orders = Order.objects.filter(event__eb_event_id=444)
        self.assertEqual(len(orders), 0)

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
        date = datetime.now(tz=timezone.utc)
        tx = create_transaction(
            UserFactory(), MerchandiseFactory(), 'TEST NOTE', 'iPhone', 'HA', date)
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
        MerchandiseFactory(quantity=2, order__id=99)
        merchandising_query_obj = get_db_merchandising_by_order_id(99)
        TransactionFactory(
            merchandise=merchandising_query_obj[0],
            operation_type='HA',
        )
        items_left = get_db_items_left(merchandising_query_obj)
        result = items_left[0].get('items_left')
        self.assertEqual(result, 1)

    def test_get_db_items_left_refund(self):
        MerchandiseFactory(quantity=2, order__id=99)
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

    def test_update_db_merch_status_pending(self):
        order = OrderFactory()
        MerchandiseFactory(order=order, quantity=1)
        result = update_db_merch_status(order)
        self.assertEqual(result, 'PE')

    def test_update_db_merch_status_partial(self):
        order = OrderFactory()
        merchandise = MerchandiseFactory(order=order, quantity=2)
        TransactionFactory(merchandise=merchandise, operation_type='HA')
        update_db_merch_status(order)
        result = Order.objects.get(id=order.id).merch_status
        self.assertEqual(result, 'PA')

    def test_update_db_merch_status_delivered(self):
        order = OrderFactory()
        merchandise = MerchandiseFactory(order=order, quantity=1)
        TransactionFactory(merchandise=merchandise, operation_type='HA')
        update_db_merch_status(order)
        result = Order.objects.get(id=order.id).merch_status
        self.assertEqual(result, 'CO')

    def test_pdf_merchandise(self):
        order = OrderFactory()
        MerchandiseFactory(order=order)
        pdf = pdf_merchandise(order.id)
        self.assertEqual(type(pdf), bytes)


class UtilsWebhook(TestBase):

    def test_get_auth_token(self):
        result = get_auth_token(
            get_user_model().objects.get(username='mercury_user'))
        self.assertEqual(result, 'AAAAAAAAAABBBBBBBBB')

    def test_get_auth_token_does_not_exist(self):
        result = get_auth_token(UserFactory())
        self.assertEqual(result, '')

    def test_webhook_available_to_process(self):
        user_id = self.social_auth_user_id
        self.assertTrue(webhook_available_to_process(user_id))

    def test_webhook_not_available_to_process(self):
        user_id = 324234234
        with self.assertRaises(Exception) as context:
            webhook_available_to_process(user_id)
        self.assertTrue('USER ID: {} WAS NOT FOUND.'.format(user_id) in str(context.exception))

    def test_social_user_exists(self):
        user_id = self.social_auth_user_id
        self.assertTrue(social_user_exists(user_id))

    def test_social_user_not_exists(self):
        user_id = '5630245671'
        self.assertFalse(social_user_exists(user_id))

    def test_get_social_user_id(self):
        result = get_social_user_id(self.social_auth_user_id)
        self.assertEqual(result, self.user.id)

    def test_get_social_user(self):
        result = get_social_user(self.social_auth_user_id)
        self.assertEqual(result.user_id, self.user.id)

    def test_webhook_order_available(self):
        user = UserFactory()
        org = OrganizationFactory()
        UserOrganizationFactory(user=user, organization=org)
        EventFactory(organization=org)
        order = OrderFactory()
        result = webhook_order_available(user, order)
        self.assertEqual(result, True)

    def test_webhook_order_available_none(self):
        user = UserFactory()
        org = OrganizationFactory()
        UserOrganizationFactory(user=user, organization=org)
        order = OrderFactory()
        result = webhook_order_available(user, order)
        self.assertEqual(result, None)

    @patch('mercury_app.utils.create_event_orders_from_api')
    @patch('mercury_app.utils.get_api_order')
    def test_get_data_success(self, mock_get_api_order, mock_create_event_orders_from_api):
        social_auth_uid = UserSocialAuth.objects.get(user=self.user).uid
        request = MagicMock(
            body=json.dumps({
                "api_url": "https://www.eventbriteapi.com/v3/orders/834225363/",
                "config": {
                    "action": "order.placed",
                    "user_id": social_auth_uid,
                    "endpoint_url": "https://ebmercury.herokuapp.com/webhook-point/",
                    "webhook_id": 799325,
                }
            })
        )
        org = OrganizationFactory()
        UserOrganizationFactory(
            user=self.user,
            organization=org,
        )
        event = EventFactory(organization=org)
        mock_get_api_order.return_value = get_mock_api_orders(1, 1, event.eb_event_id)[0]
        result = get_data(
            json.loads(request.body),
            request.build_absolute_uri('/')[:-1],
        )
        self.assertTrue(result['status'])

    @patch('mercury_app.utils.get_api_attendee_checked')
    def test_get_data_success_checkin_one(self, mock_get_api_attendee_checked):
        social_auth_uid = UserSocialAuth.objects.get(user=self.user).uid
        org = OrganizationFactory()
        UserOrganizationFactory(
            user=self.user,
            organization=org,
        )
        event = EventFactory(organization=org)
        att = AttendeeFactory(order__event=event)
        # ('barcodes')[0].get('status'
        mock_get_api_attendee_checked.return_value = {
            'barcodes': [
                {
                    'status': 'used',
                    'changed': '2018-10-31T13:13:43Z'
                },
            ]
        }
        request = MagicMock(
            body=json.dumps({
                "api_url": "https://www.eventbriteapi.com/v3/events/{}/attendees/{}/".format(
                    event.eb_event_id,
                    att.eb_attendee_id,
                ),
                "config": {
                    "action": "barcode.checked_in",
                    "user_id": social_auth_uid,
                    "endpoint_url": "https://ebmercury.herokuapp.com/webhook-point/",
                    "webhook_id": 799325,
                }
            })
        )
        result = get_data(
            json.loads(request.body),
            request.build_absolute_uri('/')[:-1],
        )
        self.assertTrue(result['status'])


    @patch('mercury_app.utils.get_api_order_attendees')
    def test_get_data_success_checkin_more_than_one(self, mock_get_api_order_attendees):
        social_auth_uid = UserSocialAuth.objects.get(user=self.user).uid
        org = OrganizationFactory()
        UserOrganizationFactory(
            user=self.user,
            organization=org,
        )
        event = EventFactory(organization=org)
        order = OrderFactory(event=event)
        att = AttendeeFactory(order=order)
        att2 = AttendeeFactory(
            first_name=att.first_name,
            last_name=att.last_name,
            order=order,
            eb_attendee_id='{}-1'.format(
                att.eb_attendee_id),
        )
        att3 = AttendeeFactory(
            first_name=att.first_name,
            last_name=att.last_name,
            order=order,
            eb_attendee_id='{}-2'.format(
                att.eb_attendee_id),
        )
        mock_get_api_order_attendees.return_value = [
            {
                'barcodes': [
                    {
                        'status': 'used',
                        'changed': '2018-10-31T13:13:43Z',
                        'barcode': '{}'.format(att.barcode),
                    },
                ]
            },
            {
                'barcodes': [
                    {
                        'status': 'unused',
                        'changed': '2018-10-31T13:13:43Z',
                        'barcode': '{}'.format(att2.barcode),
                    },
                ]
            },
            {
                'barcodes': [
                    {
                        'status': 'used',
                        'changed': '2018-10-31T13:13:43Z',
                        'barcode': '{}'.format(att3.barcode),
                    },
                ]
            },

        ]
        request = MagicMock(
            body=json.dumps({
                "api_url": "https://www.eventbriteapi.com/v3/events/{}/attendees/{}/".format(
                    event.eb_event_id,
                    att.eb_attendee_id,
                ),
                "config": {
                    "action": "barcode.checked_in",
                    "user_id": social_auth_uid,
                    "endpoint_url": "https://ebmercury.herokuapp.com/webhook-point/",
                    "webhook_id": 799325,
                }
            })
        )
        result = get_data(
            json.loads(request.body),
            request.build_absolute_uri('/')[:-1],
        )
        result2 = Attendee.objects.filter(checked_in=True).count()
        self.assertTrue(result['status'])
        self.assertEqual(result2, 2)

    def test_get_email_pdf_context(self):
        event = EventFactory(name="Event", id=1)
        order = OrderFactory(event=event)
        result = get_email_pdf_context(order.id)
        expected = {
            'event_name': "Event",
            'event_id': 1,
        }
        self.assertEqual(result, expected)

    @patch('mercury_app.utils.get_api_order', return_value=get_mock_api_orders(1, 1, 1)[0])
    def test_get_data_failure(self, mock_get_api_order):
        social_auth_uid = UserSocialAuth.objects.get(user=self.user).uid
        request = MagicMock(
            body=json.dumps({
                "api_url": "https://www.eventbriteapi.com/v3/orders/834225363/",
                "config": {
                    "action": "order.placed",
                    "user_id": social_auth_uid,
                    "endpoint_url": "https://ebmercury.herokuapp.com/webhook-point/",
                    "webhook_id": 799325,
                }
            })
        )
        result = get_data(json.loads(request.body),
                          request.build_absolute_uri('/')[:-1])
        self.assertFalse(result['status'])

    @patch('mercury_app.utils.create_webhook', return_value=(1231241, 2342342))
    def test_create_order_webhook_from_view(self, mock_create_webhook):
        user = UserFactory()
        result = UserWebhook.objects.all().count()
        self.assertEqual(result, 0)
        result2 = create_order_webhook_from_view(user)
        self.assertTrue(result2['created'])
        self.assertFalse(result2['existed'])

    @patch('mercury_app.utils.create_webhook', return_value=(None, None))
    def test_create_order_webhook_from_view_fail_from_api(self, mock_create_webhook):
        user = UserFactory()
        result = UserWebhook.objects.all().count()
        self.assertEqual(result, 0)
        result2 = create_order_webhook_from_view(user)
        self.assertFalse(result2['created'])
        self.assertFalse(result2['existed'])

    @patch('mercury_app.utils.create_webhook', return_value=(None, None))
    def test_create_order_webhook_from_view_fail_wh_existed(self, mock_create_webhook):
        user = UserFactory()
        UserWebhookFactory(user=user)
        result = UserWebhook.objects.all().count()
        self.assertEqual(result, 1)
        result2 = create_order_webhook_from_view(user)
        self.assertFalse(result2['created'])
        self.assertTrue(result2['existed'])

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
            first_name='First',
            last_name='Last',
            event=event,
            eb_order_id=2323,
            changed=timezone.now(),
            created=timezone.now(),
            status='pending',
            email='hola@hola',
            merch_status='PE',
            has_merchandise=True,
        )
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
        self.organization = OrganizationFactory()
        UserOrganizationFactory(organization=self.organization, user=self.user)

    def test_get_context_data(self):
        event = EventFactory(organization=self.organization)
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
        result = get_json_donut(1, 1, 'nombre', 2)
        self.assertEqual(expected, result)

    def test_get_summary_orders_one(self):
        expected = [{'quantity': 0, 'percentage': 0,
                     'name': 'Pending', 'id': 1},
                    {'quantity': 0, 'percentage': 0,
                     'name': 'Delivered', 'id': 2},
                    {'quantity': 0, 'percentage': 0,
                     'name': 'Partial', 'id': 3}]
        event = EventFactory()
        result = get_summary_orders(event)
        self.assertEqual(expected, result)

    def test_get_summary_orders_two(self):
        expected = [{'quantity': 1, 'percentage': 100,
                     'name': 'Pending', 'id': 1},
                    {'quantity': 0, 'percentage': 0,
                     'name': 'Delivered', 'id': 2},
                    {'quantity': 0, 'percentage': 0,
                     'name': 'Partial', 'id': 3}]
        event = EventFactory()
        order = OrderFactory(event=event)
        result = get_summary_orders(event)
        self.assertEqual(expected, result)

    def test_get_summary_orders_three(self):
        expected = [{'quantity': 0, 'percentage': 0,
                     'name': 'Pending', 'id': 1},
                    {'quantity': 1, 'percentage': 100,
                     'name': 'Delivered', 'id': 2},
                    {'quantity': 0, 'percentage': 0,
                     'name': 'Partial', 'id': 3}]
        event = EventFactory()
        OrderFactory(event=event, merch_status='CO')
        result = get_summary_orders(event)
        self.assertEqual(expected, result)

    def test_get_summary_orders_pa(self):
        expected = [{'quantity': 0, 'percentage': 0,
                     'name': 'Pending', 'id': 1},
                    {'quantity': 0, 'percentage': 0,
                     'name': 'Delivered', 'id': 2},
                    {'quantity': 1, 'percentage': 100,
                     'name': 'Partial', 'id': 3}]
        event = EventFactory()
        OrderFactory(event=event, merch_status='PA')
        result = get_summary_orders(event)
        self.assertEqual(expected, result)

    def test_get_summary_orders_five(self):
        expected = [{'quantity': 0, 'percentage': 0,
                     'name': 'Pending', 'id': 1},
                    {'quantity': 1, 'percentage': 50,
                     'name': 'Delivered', 'id': 2},
                    {'quantity': 1, 'percentage': 50,
                     'name': 'Partial', 'id': 3}]
        event = EventFactory()
        OrderFactory(event=event, merch_status='PA')
        OrderFactory(event=event, merch_status='CO')
        result = get_summary_orders(event)
        self.assertEqual(expected, result)

    def test_get_summary_handed_over_dont_json_one(self):
        expected = [0.0, 3, 0]
        mercha = MerchandiseFactory(quantity=3)
        result = get_percentage_handed([mercha.order.id])
        self.assertEqual(expected, result)

    def test_get_summary_handed_over_dont_json_two(self):
        expected = [100.0, 1, 1]
        mercha = MerchandiseFactory(quantity=1)
        TransactionFactory(
            merchandise=mercha,
            operation_type='HA',
        )
        result = get_percentage_handed([mercha.order.id])
        self.assertEqual(expected, result)

    def test_get_summary_handed_over_dont_json_three(self):
        expected = [66.7, 3, 2]
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
        result = get_percentage_handed([self.order.id])
        self.assertEqual(expected, result)

    def test_get_summary_handed_over_dont_json_four(self):
        expected = [33.3, 3, 1]
        mercha = MerchandiseFactory(name='Gorra',
                                    quantity=3,
                                    order=self.order)
        TransactionFactory(
            merchandise=mercha,
            operation_type='HA',
        )
        result = get_percentage_handed([self.order.id])
        self.assertEqual(expected, result)

    def test_get_summary_types_handed_one(self):
        expected = [{'handed': 1,
                     'handed_percentage': 100.0,
                     'name': 'Gorra',
                     'not_handed_percentage': 0.0,
                     'pending': 0,
                     'total': 1}]
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
        expected = [{'handed': 1,
                     'handed_percentage': 100.0,
                     'name': 'Gorra',
                     'not_handed_percentage': 0.0,
                     'pending': 0,
                     'total': 1},
                    {'handed': 1,
                     'handed_percentage': 100.0,
                     'name': 'Remera',
                     'not_handed_percentage': 0.0,
                     'pending': 0,
                     'total': 1}]

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
        expected = [{'handed': 0,
                     'handed_percentage': 0.0,
                     'name': 'Gorra',
                     'not_handed_percentage': 100.0,
                     'pending': 1,
                     'total': 1},
                    {'handed': 0,
                     'handed_percentage': 0.0,
                     'name': 'Remera',
                     'not_handed_percentage': 100.0,
                     'pending': 1,
                     'total': 1}]
        MerchandiseFactory(name='Gorra',
                           quantity=1,
                           order=self.order)
        MerchandiseFactory(name='Remera',
                           quantity=1,
                           order=self.order)
        result = get_summary_types_handed([self.order.id])
        self.assertEqual(expected, result)

    def test_get_summary_types_handed_four(self):
        expected = [{'handed': 0,
                     'handed_percentage': 0.0,
                     'name': 'Gorra',
                     'not_handed_percentage': 100.0,
                     'pending': 1,
                     'total': 1},
                    {'handed': 1,
                     'handed_percentage': 100.0,
                     'name': 'Remera',
                     'not_handed_percentage': 0.0,
                     'pending': 0,
                     'total': 1}]
        new_order = OrderFactory()
        MerchandiseFactory(
            name='Gorra',
            quantity=1,
            order=new_order,
        )
        mercha = MerchandiseFactory(
            name='Remera',
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

    def test_merchandise_403(self):
        user = UserFactory()
        org = OrganizationFactory()
        UserOrganizationFactory(user=user, organization=org)
        EventFactory(organization=org, eb_event_id=50781817783)
        response = self.client.get('/event/50781817783/summary/')
        self.assertEqual(403, response.status_code)

    def test_merchandise_404(self):
        response = self.client.get('/event/50781817783/summary/')
        self.assertEqual(404, response.status_code)

@patch('mercury_app.views.update_attendee_checked_from_api', return_value=True)
@patch('mercury_app.views.send_email_alert', return_value=0)
class ListItemMerchandisingTest(TestBase):

    def setUp(self):
        super(ListItemMerchandisingTest, self).setUp()
        self.org = OrganizationFactory()
        UserOrganizationFactory(user=self.user, organization=self.org)
        self.event = EventFactory(organization=self.org)

    def test_merchandise_one_entry_not_checked(self, mock_send_email, mock_attendee_checked):
        mock_attendee_checked.return_value = False
        order = OrderFactory(event=self.event)
        att = AttendeeFactory(order=order, checked_in=False)
        MerchandiseFactory(name='Camiseta', order=order)
        url = '/view_order/{}/{}/'.format(order.id, att.eb_attendee_id)
        response = self.client.get('/view_order/{}/{}/'.format(order.id, att.eb_attendee_id))
        self.assertContains(response, 'This attendee has not checked in.')

    def test_merchandise_one_entry(self, mock_send_email, mock_attendee_checked):
        order = OrderFactory(event=self.event)
        MerchandiseFactory(name='Camiseta', order=order)
        response = self.client.get('/view_order/{}/'.format(order.id))
        self.assertContains(response, 'Camiseta')

    def test_merchandise_status_code(self, mock_send_email, mock_attendee_checked):
        order = OrderFactory(event=self.event)
        MerchandiseFactory(name='Camiseta', order=order)
        response = self.client.get('/view_order/{}/'.format(order.id))
        self.assertEqual(response.status_code, 200)

    def test_merchandise_delivered(self, mock_send_email, mock_attendee_checked):
        order = OrderFactory(event=self.event)
        merchandise = MerchandiseFactory(
            name='Gorra',
            quantity=1,
            order=order,
        )
        TransactionFactory(
            merchandise=merchandise,
            operation_type='HA'
        )
        response = self.client.get('/view_order/{}/'.format(order.id))
        self.assertContains(response, 'Yes')

    def test_merchandise_403(self, mock_send_email, mock_attendee_checked):
        user = UserFactory()
        org = OrganizationFactory()
        UserOrganizationFactory(user=user, organization=org)
        event = EventFactory(organization=org)
        order = OrderFactory()
        response = self.client.get('/view_order/{}/'.format(order.id))
        self.assertEqual(403, response.status_code)

    def test_merchandise_404(self, mock_send_email, mock_attendee_checked):
        response = self.client.get('/view_order/243284293427342398423/')
        self.assertEqual(404, response.status_code)

    def test_merchandise_partial_delivery(self, mock_send_email, mock_attendee_checked):
        order = OrderFactory(event=self.event)
        merchandise = MerchandiseFactory(
            name='Gorra',
            quantity=2,
            order=order,
        )
        TransactionFactory(
            merchandise=merchandise,
            operation_type='HA'
        )
        response = self.client.get('/view_order/{}/'.format(order.id))
        self.assertContains(response, 'Partially')

    def test_merchandise_delivered_two(self, mock_send_email, mock_attendee_checked):
        order = OrderFactory(event=self.event)
        merchandise = MerchandiseFactory(
            name='Gorra',
            quantity=2,
            order=order,
        )
        TransactionFactory(
            merchandise=merchandise,
            operation_type='HA'
        )
        TransactionFactory(
            merchandise=merchandise,
            operation_type='HA'
        )
        response = self.client.get('/view_order/{}/'.format(order.id))
        self.assertContains(response, 'Yes')

    def test_merchandise_post_form(self, mock_send_email, mock_attendee_checked):
        order = OrderFactory(event=self.event, id=7)
        merchandise = MerchandiseFactory(
            eb_merchandising_id=123,
            name='Gorra',
            quantity=1,
            order=order,
        )
        response = self.client.post(
            '/view_order/{}/'.format(order.id),
            {'123': '1', 'comment': 'test', 'csrftoken': 'TEST'},
        )
        self.assertEqual(response.status_code, 302)
        transaction_count = Transaction.objects.filter(
            merchandise=merchandise
        ).count()
        self.assertEqual(transaction_count, 1)


@patch('mercury_app.views.create_order_webhook_from_view', return_value='')
class OrderListTest(TestBase):

    def setUp(self):
        super(OrderListTest, self).setUp()
        self.org = OrganizationFactory()
        UserOrganizationFactory(user=self.user, organization=self.org)
        self.event = EventFactory(organization=self.org)

    def test_order_status_code(self, mock_webhook):
        OrderFactory(event=self.event, id=9)
        response = self.client.get('/view_order/9/')
        self.assertEqual(response.status_code, 200)

    def test_create_order(self, mock_webhook):
        org = OrganizationFactory()
        UserOrganizationFactory(user=self.user, organization=org)
        event = EventFactory(organization=org)
        AttendeeFactory(
            order__event=event,
            first_name='Jaime',
            last_name='Bond',
        )
        response = self.client.get('/event/{}/orders/'.format(
            event.eb_event_id)
        )
        self.assertContains(response, 'Jaime Bond')

    def test_filter_name(self, mock_webhook):
        org = OrganizationFactory()
        UserOrganizationFactory(user=self.user, organization=org)
        event = EventFactory(organization=org, eb_event_id=50782024402)
        AttendeeFactory(
            order__event=event,
            first_name='Charles',
            last_name='Brown',
        )
        AttendeeFactory(
            order__event=event,
            first_name='Carlos',
            last_name='Brown',
        )
        response = self.client.get('/event/50782024402/orders/?full_name={}\
            &eb_order_id=&merch_status='.format('Charles'))
        self.assertContains(response, 'Charles Brown')
        response2 = self.client.get('/event/50782024402/orders/?full_name={}\
            &eb_order_id=&merch_status='.format('Brown'))
        self.assertContains(response2, 'Charles Brown')
        self.assertContains(response2, 'Carlos Brown')
        response3 = self.client.get('/event/50782024402/orders/?full_name={}\
            &eb_order_id=&merch_status='.format('John'))
        self.assertNotContains(response3, 'Charles Brown')
        self.assertNotContains(response3, 'Carlos Brown')

    def test_filter_eb_order_id(self, mock_webhook):
        org = OrganizationFactory()
        UserOrganizationFactory(user=self.user, organization=org)
        event = EventFactory(organization=org, eb_event_id=50782024402)
        order1 = OrderFactory(
            event=event,
        )
        AttendeeFactory(
            order=order1,
            first_name=order1.first_name,
            last_name=order1.last_name,
        )
        order2 = OrderFactory(
            event=event,
        )
        response = self.client.get('/event/50782024402/orders/?full_name=&eb_order_id={}\
            &merch_status='.format(order1.eb_order_id))
        self.assertContains(response, '{} {}'.format(
            order1.first_name,
            order1.last_name
        ))
        response2 = self.client.get('/event/50782024402/orders/?full_name=&eb_order_id={}\
            &merch_status='.format('3454234234242423424'))
        self.assertNotContains(response2, '{} {}'.format(
            order1.first_name,
            order1.last_name
        ))
        self.assertNotContains(response2, '{} {}'.format(
            order2.first_name,
            order2.last_name
        ))

    def test_filter_order_status(self, mock_webhook):
        org = OrganizationFactory()
        UserOrganizationFactory(user=self.user, organization=org)
        event = EventFactory(organization=org, eb_event_id=50782024402)
        order1 = OrderFactory(event=event)
        order2 = OrderFactory(event=event)
        order3 = OrderFactory(event=event)
        AttendeeFactory(
            order=order1,
            first_name='Charles',
            last_name='Brown',
        )
        AttendeeFactory(
            order=order2,
            first_name='Carlos',
            last_name='Brown',
        )
        AttendeeFactory(
            order=order3,
            first_name='Charlie',
            last_name='Brown',
        )
        merch1 = MerchandiseFactory(order=order1, quantity=1)
        merch2 = MerchandiseFactory(order=order2, quantity=2)
        MerchandiseFactory(order=order3, quantity=2)
        TransactionFactory(merchandise=merch1, operation_type='HA')
        update_db_merch_status(order1)
        TransactionFactory(merchandise=merch2, operation_type='HA')
        update_db_merch_status(order2)
        response = self.client.get('/event/50782024402/orders/?full_name=&eb_order_id=\
            &merch_status={}'.format('CO'))
        self.assertContains(response, 'Charles Brown')
        self.assertNotContains(response, 'Carlos Brown')
        self.assertNotContains(response, 'Charlie Brown')
        response2 = self.client.get('/event/50782024402/orders/?full_name=&eb_order_id=\
            &merch_status={}'.format('PA'))
        self.assertNotContains(response2, 'Charles Brown')
        self.assertContains(response2, 'Carlos Brown')
        self.assertNotContains(response2, 'Charlie Brown')
        response3 = self.client.get('/event/50782024402/orders/?full_name=&eb_order_id=\
            &merch_status={}'.format('PE'))
        self.assertNotContains(response3, 'Charles Brown')
        self.assertNotContains(response3, 'Carlos Brown')
        self.assertContains(response3, 'Charlie Brown')


class ScanQRViewTest(TestBase):

    def setUp(self):
        super(ScanQRViewTest, self).setUp()
        self.org = OrganizationFactory()
        UserOrganizationFactory(user=self.user, organization=self.org)
        self.event = EventFactory(organization=self.org)

    def test_camera_screen(self):
        response = self.client.get(
            '/event/{}/scanqr/'.format(self.event.eb_event_id))
        self.assertContains(response, 'canvas')

    @patch('mercury_app.views.get_db_attendee_from_barcode')
    @patch('mercury_app.views.update_attendee_checked_from_api')
    @patch('mercury_app.views.get_api_order_barcode')
    def test_scan_post_success(
        self,
        mock_get_api_order_barcode,
        mock_update_attendee_checked_from_api,
        mock_get_db_attendee_from_barcode,
    ):
        order = OrderFactory(event=self.event)
        MerchandiseFactory(name='shirt', order=order)
        mock_get_api_order_barcode.return_value = {'id': order.eb_order_id}
        mock_get_db_attendee_from_barcode.return_value = AttendeeFactory(order=order)
        response = self.client.post(
            '/event/{}/scanqr/'.format(self.event.eb_event_id),
            {
                'code': '55555',
                'org': self.org.eb_organization_id,
                'event': self.event.eb_event_id,
            },
            follow=True
        )
        self.assertContains(response, 'shirt')

    @patch('mercury_app.views.get_api_order_barcode')
    def test_scan_post_failure(self, mock_get_api_order_barcode):
        order = OrderFactory(event=self.event, eb_order_id='1234')
        MerchandiseFactory(name='shirt', order=order)
        mock_get_api_order_barcode.return_value = {'id': '12344'}
        response = self.client.post(
            '/event/{}/scanqr/'.format(self.event.eb_event_id),
            {
                'code': '55555',
                'org': '22222',
                'event': '1111',
            },
            follow=True
        )
        self.assertEqual(response.status_code, 404)


class DeleteEventsTest(TestBase):

    def setUp(self):
        super(DeleteEventsTest, self).setUp()
        self.event = EventFactory()

    def test_delete_one_event(self):
        response = self.client.get(
            '/event/{}/delete/'.format(self.event.eb_event_id))
        self.assertIsNotNone(response.context['event'])

    def test_delate_event(self):
        self.client.post(
            '/event/{}/delete/'.format(self.event.eb_event_id))
        delete_events(self.event.eb_event_id)
        self.assertEqual(Event.objects.filter(
            eb_event_id=self.event.eb_event_id).count(), 0)


class TransactionViewTest(TestBase):

    def setUp(self):
        super(TransactionViewTest, self).setUp()
        self.org = OrganizationFactory()
        UserOrganizationFactory(user=self.user, organization=self.org)
        self.event = EventFactory(organization=self.org)

    def test_transaction_status_code(self):
        OrderFactory(event=self.event, id=55)
        response = self.client.get('/view_order/55/transactions/')
        self.assertEqual(response.status_code, 200)

    def test_one_transaction_in_view(self):
        order = OrderFactory(event=self.event, id=56)
        TransactionFactory(merchandise__name='Cap',
                           merchandise__order=order, operation_type='HA')
        response = self.client.get('/view_order/56/transactions/')
        self.assertContains(response, 'Cap')

    def test_two_transactions_in_view(self):
        order = OrderFactory(event=self.event, id=56)
        TransactionFactory(merchandise__name='Cap',
                           merchandise__order=order, operation_type='HA')
        TransactionFactory(merchandise__name='Water',
                           merchandise__order=order, operation_type='HA')
        response = self.client.get('/view_order/56/transactions/')
        self.assertContains(response, 'Cap')
        self.assertContains(response, 'Water')
        self.assertContains(response, 'Fulfillment')
        self.assertNotContains(response, 'Return')

    def test_two_transactions_in_view(self):
        order = OrderFactory(event=self.event, id=56)
        TransactionFactory(merchandise__name='Cap',
                           merchandise__order=order, operation_type='HA')
        TransactionFactory(merchandise__name='Water',
                           merchandise__order=order, operation_type='HA')
        TransactionFactory(merchandise__name='Water',
                           merchandise__order=order, operation_type='RE')
        response = self.client.get('/view_order/56/transactions/')
        self.assertContains(response, 'Cap')
        self.assertContains(response, 'Water')
        self.assertContains(response, 'Return')
