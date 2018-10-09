from datetime import (
    datetime,
    timedelta,
)
import string
import pytz
import factory
from factory import fuzzy
from django.contrib.auth import get_user_model
from .models import (
    Organization,
    UserOrganization,
    Event,
    Order,
    Merchandise,
    Transaction,
    UserWebhook,
)
import random


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: 'username_{}'.format(n))
    password = 'password'


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    eb_organization_id = factory.fuzzy.FuzzyInteger(10000000000, 20000000000)
    name = factory.LazyAttribute(
        lambda o: 'name_{}'.format(o.eb_organization_id))


class UserOrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserOrganization

    user = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    organization = factory.SubFactory(OrganizationFactory)
    eb_event_id = factory.fuzzy.FuzzyInteger(50000000000, 60000000000)
    name = factory.LazyAttribute(lambda o: 'event_{}'.format(o.eb_event_id))
    description = factory.fuzzy.FuzzyText(
        length=800,
        chars=string.ascii_letters,
        prefix='description_',
    )
    url = factory.LazyAttribute(
        lambda o: 'https://www.eventbrite.com/e/{}'.format(o.eb_event_id))
    date_tz = 'America/Argentina/Mendoza'
    start_date_utc = factory.fuzzy.FuzzyDateTime(
        datetime.now(tz=pytz.utc),
        datetime.now(tz=pytz.utc) + timedelta(days=45),
    )
    end_date_utc = factory.LazyAttribute(
        lambda o: o.start_date_utc + timedelta(hours=3))

    created = factory.fuzzy.FuzzyDateTime(
        datetime.now(tz=pytz.utc) - timedelta(days=10),
        datetime.now(tz=pytz.utc) - timedelta(days=1),
    )
    changed = factory.LazyAttribute(
        lambda o: o.created + timedelta(seconds=25))
    status = 'live'


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    event = factory.SubFactory(EventFactory)
    eb_order_id = factory.fuzzy.FuzzyInteger(80000000000, 90000000000)
    created = factory.LazyAttribute(
        lambda o: o.event.created + timedelta(hours=1))
    changed = factory.LazyAttribute(
        lambda o: o.created + timedelta(hours=3))
    name = factory.LazyAttribute(lambda o: 'buyer_{}'.format(o.eb_order_id))
    email = factory.LazyAttribute(
        lambda o: 'buyer_{}@email.com'.format(o.eb_order_id))
    status = 'placed'


class MerchandiseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Merchandise

    order = factory.SubFactory(OrderFactory)
    eb_merchandising_id = factory.Sequence(lambda n: n)
    name = factory.LazyAttribute(
        lambda o: 'Item {}'.format(o.eb_merchandising_id))
    item_type = factory.fuzzy.FuzzyChoice(['Red', 'Blue', 'Green', ])
    currency = 'USD'
    quantity = factory.fuzzy.FuzzyInteger(1, 100)
    value = factory.fuzzy.FuzzyFloat(25, 75)


class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transaction

    merchandise = factory.SubFactory(MerchandiseFactory)
    date = factory.fuzzy.FuzzyDateTime(
        datetime.now(tz=pytz.utc),
        datetime.now(tz=pytz.utc) + timedelta(days=45),
    )
    notes = factory.fuzzy.FuzzyText(
        length=256,
        chars=string.ascii_letters,
    )
    device_name = factory.fuzzy.FuzzyText(
        length=128,
        chars=string.ascii_letters,
    )
    operation_type = random.choice(['HA', 'RE'])
    from_who = factory.SubFactory(UserFactory)


class UserWebhookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserWebhook

    webhook_id = str(factory.fuzzy.FuzzyInteger(1, 10000))
    user = factory.SubFactory(UserFactory)
