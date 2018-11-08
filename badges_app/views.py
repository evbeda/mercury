from django.http import HttpResponse
from rest_framework.views import APIView
from .utils import (printer_json,
                    update_printer_name,
                    job_get_status,
                    job_set_status,
                    configure_printer,
                    mock_queues)
from badges_app.models import Printer
import json


class PrinterView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get(self, request, format=None, **kwargs):
        key = self.kwargs['key']
        return printer_json(key)

    def post(self, request, format=None, **kwargs):
        key = self.kwargs['key']
        secret_key = request.POST.get('secret_key')
        name = request.POST.get('name')
        if secret_key and name:
            return update_printer_name(key, secret_key, name)
        message = {"Error": "Undefined name or secret key"}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")


class PrinterQueues(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get(self, request, format=None, **kwargs):
        key = self.kwargs['key']
        try:
            Printer.objects.get(key=key)
            return mock_queues()
        except Exception:
            message = {"Error": "Printer id and public key does not match"}
            return HttpResponse(json.dumps(message),
                                content_type="application/json")


class ConfigurePrinter(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get(self, request, format=None, **kwargs):
        key = self.kwargs['key']
        return configure_printer(key)


class JobState(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get(self, request, format=None, **kwargs):
        key = self.kwargs['key']
        self.kwargs['job_id']
        return job_get_status(key)

    def post(self, request, format=None, **kwargs):
        secret_key = request.POST.get('secret_key')
        status = request.POST.get('status')
        if secret_key and status:
            self.kwargs['job_id']
            return job_set_status(self.kwargs['key'],
                                  secret_key,
                                  status)
        else:
            message = {"Error": "Undefined status or secret key"}
            return HttpResponse(json.dumps(message),
                                content_type="application/json")
