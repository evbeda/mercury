from django.http import HttpResponse
from badges_app.models import Printer
from rest_framework.renderers import JSONRenderer
from badges_app.serializers import PrinterSerializer
import json
import uuid
from mercury_app.utils import redis_conn
import pickle


class JSONResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


def printer_queue(key):
    try:
        printer = Printer.objects.get(key=key)
        rc = redis_conn()
        printer_key = 'printer_{}'.format(printer.id)
        response = rc.lrange(printer_key, 0, -1)
        jobs = []
        for job_key in response:
            result = pickle.loads(rc.get(job_key))
            jobs.append({'job_key' : result['job_key'],
                    'content' : get_zpl(result['first_name'], result['last_name'])})
        if jobs:
            return HttpResponse(json.dumps(jobs),
                                content_type="application/json")
        else:
            message = {"Error": "the queue is empty"}
            return HttpResponse(json.dumps(message),
                                content_type="application/json")

    except Exception:
        message = {"Error": "Printer id and public key does not match"}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")


def get_zpl(name, last_name):
        result = '^XA\
^FO20,10^GB700,1,3^FS\
^CFA,30\
^AV,25,25^FO20,30^FD{}^FS\
^AV,25,25^FO20,130^FD{}^FS\
^FO20,330^GB700,1,3^FS\
^XZ'.format(name, last_name)
        return result


def confirm_job(key, secret_key, job_key):
    if secret_key and key:
        try:
            printer = Printer.objects.filter(key=key, secret_key=secret_key)
            if printer:
                printer_key = 'printer_{}'.format(printer[0].id)
                rc = redis_conn()
                if rc.lrem(name=printer_key, value=job_key, num=0) and rc.delete(job_key):
                    message = {"job_key": job_key,
                               "delete": "ok"}
                else:
                    message = {"error": "job_key does not exist or printer does not exist"}
                return HttpResponse(json.dumps(message),
                                    content_type="application/json")
        except Exception:
            message = {"error": "job_key does not exist or printer does not exist"}
            return HttpResponse(json.dumps(message),
                        content_type="application/json")
    message = {"Error": "Undefined key or secret key"}
    return HttpResponse(json.dumps(message),
                        content_type="application/json")

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
