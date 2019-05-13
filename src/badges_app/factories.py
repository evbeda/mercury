import factory
from badges_app.models import Printer
from mercury_app.test_factories import EventFactory
import uuid


class PrinterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Printer
    name = factory.LazyAttribute(lambda o: 'name_{}'.format(o.key))
    event = factory.SubFactory(EventFactory)
    key = uuid.uuid4()
    secret_key = uuid.uuid4()
