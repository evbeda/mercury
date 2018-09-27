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
