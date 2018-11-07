import factory
from badges_app.models import Printer
from mercury_app.test_factories import OrganizationFactory


class PrinterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Printer
    name = factory.LazyAttribute(lambda o: 'name_{}'.format(o.key))
    organization = factory.SubFactory(OrganizationFactory)
    key = "b1f9d07d-4184-4727-9633-f048e288d8e0"
    secret_key = "ec5402e6-5b5e-40f1-925a-ae595b413cfc"
