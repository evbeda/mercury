from django.http import HttpResponse
from badges_app.models import Printer
from rest_framework.renderers import JSONRenderer
from badges_app.serializers import PrinterSerializer
import json
import uuid
import pickle
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse
import os
import redis
from mercury_app.models import Attendee


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
            jobs.append({'job_key': result['job_key'],
                         'content': get_zpl(result['attendee_id'])})
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


def get_zpl(attendee_id):
    attendee = Attendee.objects.get(id=attendee_id)
    result = '^XA\
^FX\
^CFA,30\
^FO50,100^FD{0}^FS\
^FO50,140^FD100{1}^FS\
^CFA,15\
^FO50,200^GB700,1,3^FS\
^FS^FS^FS^FS\
^FO^FO^FO^FO^FS\
^FO250,200\
^BQN,2,10\
^FD ,{0} , {1} , {2} , {3}\
^XZ'.format(attendee.first_name,
            attendee.last_name,
            attendee.order.email,
            attendee.order.event.organization.name,
            )
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
                    message = {
                        "error": "job_key does not exist or printer does not exist"}
                return HttpResponse(json.dumps(message),
                                    content_type="application/json")
        except Exception:
            message = {
                "error": "job_key does not exist or printer does not exist"}
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


def get_html_combo_box(event_id):
    printers = Printer.objects.filter(event_id=event_id)
    html = "<select class='form-control' name='printer_id'>"
    for printer in printers:
        html += "<option value={}>{}</option>".format(printer.id, printer.name)
    html += "</select>"
    return html


def redis_conn():
    url_p = urlparse.urlparse(os.environ.get('REDIS_URL'))
    return redis.Redis(host=url_p.hostname, port=url_p.port, db=1)


def set_redis_job(printer_id, attendee):
    try:
        rc = redis_conn()
        job_key = "job_{}".format(rc.incr("job_id"))
        job_data = {'job_key': job_key,
                    'attendee_id': attendee.id}
        rc.set(job_key, pickle.dumps(job_data))
        printer_key = "printer_{}".format(printer_id)
        rc.rpush(printer_key, job_key)
        return True
    except Exception:
        return False
