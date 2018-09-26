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
from django.utils import timezone


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

    def test_home(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


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
