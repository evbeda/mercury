from django.test import TestCase
from badges_app.factories import PrinterFactory
from badges_app.models import Printer
from badges_app.utils import (mock_jobs,
                              mock_queues,
                              job_get_status,
                              job_set_status,
                              update_printer_name,
                              printer_json)
# Create your tests here.


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

    def test_get_job_status(self):
        result = self.client.get(
            '/api/printer/{}/job/1231/'.format(self.printer.key))
        expected = b'{"status":"pending"}'
        self.assertEqual(expected, result.content)

    def test_set_job_status(self):
        result = self.client.post('/api/printer/{}/job/1231/'.format(self.printer.key),
                                  data={'status': 'Done', 'secret_key': self.printer.secret_key})
        expected = b'{"status":"Done"}'
        self.assertEqual(expected, result.content)

    def test_get_queue_jobs(self):
        result = self.client.get(
            '/api/printer/{}/queue/'.format(self.printer.key))
        expected = b'[{"job_id":1,"content":"<p>impresion</p>","order":1}]'
        self.assertEqual(expected, result.content)

    def test_mock_jobs(self):
        result = mock_jobs("pending")
        expected = b'{"status":"pending"}'
        self.assertEqual(expected, result.content)

    def test_mock_queue(self):
        result = mock_queues()
        expected = b'[{"job_id":1,"content":"<p>impresion</p>","order":1}]'
        self.assertEqual(expected, result.content)

    def test_job_get_status_ok(self):
        result = job_get_status(self.printer.key)
        expected = b'{"status":"pending"}'
        self.assertEqual(expected, result.content)

    def test_job_get_status_not(self):
        result = job_get_status('12312313')
        expected = b'{"Error": "Printer id and public key does not match"}'
        self.assertEqual(expected, result.content)

    def test_job_set_status(self):
        result = job_set_status(self.printer.key,
                                self.printer.secret_key,
                                "pending")
        expected = b'{"status":"pending"}'
        self.assertEqual(expected, result.content)

    def test_job_set_status_not(self):
        result = job_set_status(self.printer.key,
                                123123,
                                "pending")
        expected = b'{"Error": "Printer id and public key does not match"}'
        self.assertEqual(expected, result.content)

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


class TestFactoryPrinter(TestCase):

    def test_create_printer(self):
        printer = PrinterFactory()
        self.assertIsInstance(printer, Printer)

    def test_create_printer_with_name(self):
        printer = PrinterFactory(name="Printer HP")
        self.assertIsInstance(printer, Printer)
