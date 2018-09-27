from django.test import TestCase
from social_django.models import UserSocialAuth
from django.contrib.auth import get_user_model
from .models import (
    Event,
    Organization,
    UserOrganization,
    Order,
    Merchandise,
)
from mercury_app.views import Home
from django.utils import timezone
from django.urls import resolve
from unittest.mock import patch
import json


MOCK_ORGANIZATION_API = {
    "organizations": [{
        "_type": "organization",
        "name": "Mercury Team",
        "vertical": "default",
        "locale": None,
        "image_id": None,
        "id": "272770247903",
    }],
    "pagination": {
        "continuation": "b2Zmc2V0LTE=",
        "has_more_items": False,
    },
}
MOCK_EVENT_API = {
    "pagination": {
        "object_count": 1,
        "page_number": 1,
        "page_size": 50,
        "page_count": 1,
        "has_more_items": False
    },
    "events": [{
        "name": {"text": "Test event", "html": "Test event"},
        "description": {"text": None, "html": None},
        "id": "50452133690",
        "url": "https://www.eventbrite.com/e/test-event-tickets-50452133690",
        "start": {
            "timezone": "America/Los_Angeles",
            "local": "2018-10-29T19:00:00",
            "utc": "2018-10-30T02:00:00Z"
        },
        "end": {
            "timezone": "America/Los_Angeles",
            "local": "2018-10-29T22:00:00",
            "utc": "2018-10-30T05:00:00Z"
        },
        "organization_id": "272770247903",
        "created": "2018-09-19T17:16:39Z",
        "changed": "2018-09-24T15:06:49Z",
        "capacity": 200,
        "capacity_is_custom": False,
        "status": "draft",
        "currency": "USD",
        "listed": False,
        "shareable": True,
        "invite_only": False,
        "online_event": False,
        "show_remaining": False,
        "tx_time_limit": 480,
        "hide_start_date": False,
        "hide_end_date": False,
        "locale": "en_US",
        "is_locked": False,
        "privacy_setting": "unlocked",
        "is_series": False,
        "is_series_parent": False,
        "is_reserved_seating": False,
        "show_pick_a_seat": False,
        "show_seatmap_thumbnail": False,
        "show_colors_in_seatmap_thumbnail": False,
        "source": "create_2.0",
        "is_free": False,
        "version": "3.0.0",
        "logo_id": None,
        "organizer_id": "17867896837",
        "venue_id": None,
        "category_id": None,
        "subcategory_id": None,
        "format_id": None,
        "resource_uri": "https://www.eventbriteapi.com/v3/events/50452133690/",
        "is_externally_ticketed": False,
        "logo": None
    }]}


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
        self.auth = UserSocialAuth.objects.create(
            user=self.user, provider='eventbrite', uid="563480245671"
        )
        login = self.client.login(
            username='mercury_user',
            password='the_best_password_of_ever_2'
        )
        return login


class HomeViewTest(TestBase):

    def setUp(self):
        super(HomeViewTest, self).setUp()

    def test_home_status_code(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_charset(self):
        response = self.client.get('/')
        self.assertEqual(response.charset, "utf-8")

    def test_home_status_code_two(self):
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)

    def test_home_resolve_home_class_view(self):
        found = resolve('/')
        self.assertEquals(found.func.view_class, Home)

    def test_home_resolve_home_not_args(self):
        found = resolve('/')
        self.assertEquals(found.args, ())

    def test_home_resolve_home_kwargs_empty(self):
        found = resolve('/')
        self.assertEquals(found.kwargs, {'message': None})

    def test_home_resolve_home_kwargs_message_full(self):
        found = resolve('/Welcome')
        self.assertEquals(found.kwargs, {'message': "Welcome"})

    def test_home_url_name(self):
        found = resolve('/')
        self.assertEqual(found.url_name, 'index')

    def test_home_none_entry(self):
        response = self.client.get('/')
        self.assertNotContains(response, "class='btn btn-success'>View</a>")
        self.assertContains(response, 'Add')

    def test_home_one_entry(self):
        org = Organization.objects.create(
            eb_organization_id=1, name='test_organization')
        Event.objects.create(organization=org,
                             name="Evento",
                             description="description",
                             eb_event_id=1,
                             date_tz="America/Argentina/Mendoza",
                             start_date_utc="2018-10-22T22:00:09Z",
                             end_date_utc="2018-10-22T22:00:09Z",
                             created="2017-11-23 23:33:57-03",
                             changed="2017-11-23 23:33:57-03",
                             status="completed",
                             )
        response = self.client.get('/')
        self.assertContains(response, 'Evento')
        self.assertContains(response, 'View')
        self.assertContains(response, 'Add')

    def test_home_two_entry(self):
        org = Organization.objects.create(
            eb_organization_id=1, name='test_organization')
        Event.objects.create(organization=org,
                             name="Evento",
                             description="description",
                             eb_event_id=1,
                             date_tz="America/Argentina/Mendoza",
                             start_date_utc="2018-10-22T22:00:09Z",
                             end_date_utc="2018-10-22T22:00:09Z",
                             created="2017-11-23 23:33:57-03",
                             changed="2017-11-23 23:33:57-03",
                             status="completed",
                             )
        Event.objects.create(organization=org,
                             name="ev",
                             description="description nueva",
                             eb_event_id=2,
                             date_tz="America/Argentina/Cordoba",
                             start_date_utc="2017-10-22T22:00:09Z",
                             end_date_utc="2017-10-22T22:00:09Z",
                             created="2016-11-23 23:33:57-03",
                             changed="2016-11-23 23:33:57-03",
                             status="completed",
                             )
        response = self.client.get('/')
        self.assertContains(response, 'Evento')
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

    def setUp(self):
        super(SelectEventsLoggedTest, self).setUp()

    @patch('mercury_app.views.get_api_organization', return_value=MOCK_ORGANIZATION_API.get('organizations'))
    @patch('mercury_app.views.get_api_events_org', return_value=MOCK_EVENT_API.get('events'))
    def test_screen_with_one_event(self, mock_get_api_events_org, mock_get_api_organization):
        response = self.client.get('/select_events/')
        self.assertEqual(response.status_code, 200)

    @patch('mercury_app.views.get_api_events_id', return_value=MOCK_EVENT_API.get('events')[0])
    def test_add_event(self, mock_get_api_events_id):
        response = self.client.post('/select_events/', {'organization_id': '1234', 'organization_name': 'TestOrg'})
        event = Event.objects.get(eb_event_id=MOCK_EVENT_API.get('events')[0].get('id'))
        self.assertTrue(isinstance(event, Event))
        self.assertEqual(response.status_code, 302)

class SelectEventsRedirectTest(TestCase):

    def test_redirect(self):
        response = self.client.get('/select_events/')
        self.assertEqual(response.status_code, 302)


class OrganizationModelTest(TestCase):

    def create_organization(
        self, name="Organization",
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
        name="event1",
        description="this is an event",
        eb_event_id="123", date_tz=timezone.now(),
        start_date_utc=timezone.now(), end_date_utc=timezone.now(),
        created=timezone.now(), changed=timezone.now(), status="created"
    ):
        organization = Organization.objects.create(
            eb_organization_id=23223,
            name="Eventbrite")
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
        self, name="order", eb_order_id=2323, changed=timezone.now(),
        created=timezone.now(), status="pending", email="hola@hola",
        merch_status="PE"
    ):
        organization = Organization.objects.create(
            eb_organization_id=23223, name="Eventbrite"
        )
        event = Event.objects.create(
            name="event", organization=organization, description="event1",
            eb_event_id="456", date_tz=timezone.now(),
            start_date_utc=timezone.now(), end_date_utc=timezone.now(),
            created=timezone.now(), changed=timezone.now(), status="pending")
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
        self, name="Remeras", item_type="talle l", currency="USD",
        value="508730", delivered=True
    ):
        organization = Organization.objects.create(
            eb_organization_id=23223,
            name="Eventbrite")
        event = Event.objects.create(
            name="event", organization=organization,
            description="event1", eb_event_id="456",
            date_tz=timezone.now(), start_date_utc=timezone.now(),
            end_date_utc=timezone.now(), created=timezone.now(),
            changed=timezone.now(), status="pending"
        )
        order = Order.objects.create(
            name="order", event=event,
            eb_order_id=2323, changed=timezone.now(),
            created=timezone.now(), status="pending",
            email="hola@hola", merch_status="PE")
        return Merchandise.objects.create(
            order=order, name=name, item_type=item_type,
            currency=currency, value=value, delivered=delivered)

    def test_merchandise_creation(self):
        merchandise = self.create_merchandise()
        self.assertTrue(isinstance(merchandise, Merchandise))
        self.assertEqual(merchandise.__string__(), merchandise.name)


class UserOrganizationModelTest(TestBase):

    def create_user_organization(self):
        organization = Organization.objects.create(
            eb_organization_id=23223, name="Eventbrite"
        )
        return UserOrganization.objects.create(
            user=self.user, organization=organization
        )

    def test_user_organization_creation(self):
        user_organization = self.create_user_organization()
        self.assertTrue(isinstance(user_organization, UserOrganization))
