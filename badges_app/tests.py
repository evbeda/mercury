from django.test import TestCase
from badges_app.factories import PrinterFactory
from badges_app.models import Printer
from mercury_app.test_factories import AttendeeFactory, OrderFactory, EventFactory, OrganizationFactory
from badges_app.utils import (configure_printer,
                              update_printer_name,
                              printer_queue,
                              confirm_job,
                              printer_json)
from mercury_app.tests import TestBase
from mercury_app.models import Event
import fakeredis
from mercury_app.test_factories import (OrganizationFactory,
                                        UserOrganizationFactory,
                                        EventFactory)
from unittest.mock import (
    patch,
)
import pickle


class TestApi(TestCase):

    def setUp(self):
        self.printer = PrinterFactory(id=1, name="Printer HP")

    def test_get_name(self):
        result = self.client.get(
            '/api/printer/{}/'.format(self.printer.key))
        expected = b'{"id":1,"name":"Printer HP"}'
        self.assertEqual(expected, result.content)

    def test_set_name(self):
        self.client.post('/api/printer/{}/'.format(self.printer.key),
                         data={'name': 'Zebra', 'secret_key': self.printer.secret_key})
        result = Printer.objects.get(id=self.printer.id)
        expected = 'Zebra'
        self.assertEqual(expected, result.name)

    def test_printer_json(self):
        result = printer_json(self.printer.key,)
        expected = b'{"id":1,"name":"Printer HP"}'
        self.assertEqual(expected, result.content)

    def test_printer_json_not(self):
        result = printer_json(12312312)
        expected = b'{"Error": "Public key does not match or Printer does not exist"}'
        self.assertEqual(expected, result.content)

    def test_update_printer_name(self):
        result = update_printer_name(self.printer.key,
                                     self.printer.secret_key,
                                     "new_name")
        expected = b'{"id":1,"name":"new_name"}'
        self.assertEqual(expected, result.content)

    def test_update_printer_name_not(self):
        result = update_printer_name(self.printer.key,
                                     123123,
                                     "new_name")
        expected = b'{"Error": "Public and Private key does not match"}'
        self.assertEqual(expected, result.content)

    def test_configure_printer(self):
        self.printer.secret_key = None
        self.printer.save()
        self.assertFalse(self.printer.secret_key)
        configure_printer(self.printer.key)
        printer = Printer.objects.get(id=self.printer.id)
        self.assertTrue(printer.secret_key)

    def test_configure_printer_error(self):
        self.assertTrue(self.printer.secret_key)
        result = configure_printer(self.printer.key)
        expected = b'{"Error": "Public key incorrect, or Printer already configured"}'
        self.assertTrue(expected, result.content)

    @patch('badges_app.utils.redis_conn', return_value=fakeredis.FakeRedis())
    def test_printer_queue(self, mock_redis):
        rc = fakeredis.FakeStrictRedis()
        organization = OrganizationFactory(name='Org1')
        event = EventFactory(name="Event",organization=organization)
        order = OrderFactory(event = event, email='hola@gmail.com')
        attendee = AttendeeFactory(
            first_name='Test',
            last_name='Mock',
            order=order,
        )
        job_key = "job_{}".format(1)
        job_data = {'job_key': job_key,
                    'attendee_id': attendee.id,}
        rc.set(job_key, pickle.dumps(job_data))
        printer_key = 'printer_{}'.format(self.printer.id)
        rc.rpush(printer_key, job_key)
        result = printer_queue(self.printer.key)
        expected = b'[{"job_key": "job_1", "content": "^XA^FX^CFA,30^FO50,100^FDTest^FS^FO50,140^FD100Mock^FS^CFA,15^FO50,200^GB700,1,3^FS^FS^FS^FS^FS^FO^FO^FO^FO^FS^FO250,200^BQN,2,10^FD ,Test , Mock , hola@gmail.com , Org1^XZ"}]'
        self.assertEqual(result.content, expected)

    @patch('badges_app.utils.redis_conn', return_value=fakeredis.FakeStrictRedis())
    def test_printer_queue_not_items(self, mock_redis):
        rc = fakeredis.FakeStrictRedis()
        rc.flushdb()
        result = printer_queue(self.printer.key)
        expected = b'{"Error": "the queue is empty"}'
        self.assertEqual(result.content, expected)

    @patch('badges_app.utils.redis_conn', return_value=fakeredis.FakeRedis())
    def test_confirm_jobs(self, mock_redis):
        rc = fakeredis.FakeStrictRedis()
        job_key = "job_{}".format(1)
        job_data = {'job_key': job_key,
                    'first_name': "Test",
                    'last_name': "Mock"}
        rc.set(job_key, pickle.dumps(job_data))
        printer_key = 'printer_{}'.format(self.printer.id)
        rc.rpush(printer_key, job_key)
        result = confirm_job(
            self.printer.key, self.printer.secret_key, job_key)
        expected = b'{"job_key": "job_1", "delete": "ok"}'
        self.assertEqual(result.content, expected)


class TestFactoryPrinter(TestCase):

    def test_create_printer(self):
        printer = PrinterFactory()
        self.assertIsInstance(printer, Printer)

    def test_create_printer_with_name(self):
        printer = PrinterFactory(name="Printer HP")
        self.assertIsInstance(printer, Printer)


class TestPrinterView(TestBase):

    def test_list_printer_view(self):
        org = OrganizationFactory()
        UserOrganizationFactory(user=self.user, organization=org)
        event = EventFactory(organization=org, name="Evento")
        response = self.client.get('/event/{}/configuration/printer/list/'.format(event.eb_event_id))
        self.assertContains(response, event.eb_event_id)

    def test_list_printer_view_one_printer(self):
        org = OrganizationFactory()
        UserOrganizationFactory(user=self.user, organization=org)
        event = EventFactory(organization=org, name="Evento")
        printer = PrinterFactory(name="Printer HP", event=event)
        response = self.client.get('/event/{}/configuration/printer/list/'.format(event.eb_event_id))
        self.assertContains(response, printer.name)

    def test_delete_printer(self):
        org = OrganizationFactory()
        UserOrganizationFactory(user=self.user, organization=org)
        event = EventFactory(organization=org, name="Evento")
        printer = PrinterFactory(name="Printer HP", event=event)
        self.assertEqual(len(Printer.objects.all()), 1)
        self.client.post('/event/{}/configuration/printer/{}/delete/'.format(event.eb_event_id, printer.id))
        self.assertEqual(len(Printer.objects.all()), 0)

    def test_reset_printer(self):
        org = OrganizationFactory()
        UserOrganizationFactory(user=self.user, organization=org)
        event = EventFactory(organization=org, name="Evento")
        printer = PrinterFactory(name="Printer HP", event=event)
        first_key = printer.key
        response = self.client.get('/event/{}/configuration/printer/{}/reset/'.format(event.eb_event_id, printer.id))
        printer = Printer.objects.get(id=printer.id)
        self.assertEqual(printer.secret_key, None)
        self.assertNotEqual(printer.key, first_key)
