from django.http import HttpResponse
from badges_app.models import Printer
from rest_framework.renderers import JSONRenderer
from badges_app.serializers import PrinterSerializer
import json


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


def job_get_status(printer_id, key):
    try:
        Printer.objects.get(id=printer_id, key=key)
        return mock_jobs()
    except Exception:
        message = {"Error": "Printer id and public key does not match"}
        return HttpResponse(json.dumps(message))


def job_set_status(printer_id, key, secret_key, status):
    try:
        Printer.objects.get(id=printer_id,
                            key=key,
                            secret_key=secret_key)
        return mock_jobs(status)
    except Exception:
        message = {"Error": "Printer id and public key does not match"}
        return HttpResponse(json.dumps(message))


def printer_json(printer_id, key):
    try:
        printer = Printer.objects.get(id=printer_id, key=key)
        serializer = PrinterSerializer(printer, many=False)
        return JSONResponse(serializer.data)
    except Exception:
        message = {"Error": "Public key does not match or Printer does not exist"}
        return HttpResponse(json.dumps(message))


def update_printer_name(printer_id, key, secret_key, name):
    try:
        printer = Printer.objects.get(id=printer_id,
                                      key=key,
                                      secret_key=secret_key)
        printer.name = name
        printer.save()
        serializer = PrinterSerializer(printer, many=False)
        return JSONResponse(serializer.data)
    except Exception:
        message = {"Error": "Public and Private key does not match"}
        return HttpResponse(json.dumps(message))
