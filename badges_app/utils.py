from django.http import HttpResponse
from badges_app.models import Printer
from rest_framework.renderers import JSONRenderer
from badges_app.serializers import PrinterSerializer
import json
import uuid


class JSONResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


def mock_jobs(status="pending"):
    return JSONResponse({'status': status})


def mock_queues():
    return JSONResponse([{'job_id': 1,
                          'content': '<p>impresion</p>',
                          'order': 1}])


def configure_printer(key):
    try:
        printer = Printer.objects.get(key=key, secret_key=None)
        printer.secret_key = uuid.uuid4()
        printer.save()
        response = {'secret_key': printer.secret_key.hex}
        return HttpResponse(json.dumps(response), content_type="application/json")
    except Exception:
        message = {"Error": "Public key incorrect, or Printer already configured"}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")


def job_get_status(key):
    try:
        Printer.objects.get(key=key)
        return mock_jobs()
    except Exception:
        message = {"Error": "Printer id and public key does not match"}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")


def job_set_status(key, secret_key, status):
    try:
        Printer.objects.get(key=key,
                            secret_key=secret_key)
        return mock_jobs(status)
    except Exception:
        message = {"Error": "Printer id and public key does not match"}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")


def printer_json(key):
    try:
        printer = Printer.objects.get(key=key)
        serializer = PrinterSerializer(printer, many=False)
        return JSONResponse(serializer.data)
    except Exception:
        message = {"Error": "Public key does not match or Printer does not exist"}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")


def update_printer_name(key, secret_key, name):
    try:
        printer = Printer.objects.get(key=key,
                                      secret_key=secret_key)
        printer.name = name
        printer.save()
        serializer = PrinterSerializer(printer, many=False)
        return JSONResponse(serializer.data)
    except Exception:
        message = {"Error": "Public and Private key does not match"}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")
