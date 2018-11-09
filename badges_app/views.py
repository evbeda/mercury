import json
import os
import redis
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
import pickle
from django.core.urlresolvers import reverse
from django.shortcuts import (
    redirect,
)
from rest_framework.views import APIView, View
from django_tables2 import (
    SingleTableMixin,
    SingleTableView,
)
from mercury_app.filterview_fix import MyFilterView
from mercury_app.utils import (
    EventAccessMixin,
    get_db_attendee_from_eb_id,
)
from badges_app.utils import (
    printer_json,
    configure_printer,
    update_printer_name,
    printer_queue,
    confirm_job,
)
from mercury_app.models import (
    Attendee,
    UserOrganization,
)
from badges_app.models import Printer
from badges_app.tables import PrintingTable
from badges_app.filters import AttendeeFilter


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
        return printer_queue(key)


class ConfigurePrinter(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get(self, request, format=None, **kwargs):
        key = self.kwargs['key']
        return configure_printer(key)


class JobState(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, format=None, **kwargs):
        secret_key = request.POST.get('secret_key')
        job_id = self.kwargs['job_id']
        return confirm_job(self.kwargs['key'], secret_key, job_id)


@method_decorator(login_required, name='dispatch')
class FilteredPrintingList(SingleTableMixin, MyFilterView, EventAccessMixin):
    table_class = PrintingTable
    model = Attendee
    template_name = 'printer_attendee_list.html'
    filterset_class = AttendeeFilter

    def get_queryset(self):
        return Attendee.objects.filter(
            order__event__eb_event_id=self.kwargs['event_id']).order_by(
            'checked_in_time',
        )

    def get_context_data(self, **kwargs):
        context = super(SingleTableMixin, self).get_context_data(**kwargs)
        table = self.get_table(**self.get_table_kwargs())
        context[self.get_context_table_name(table)] = table
        table.paginate(page=self.request.GET.get('page', 1), per_page=10)
        event = self.get_event()
        context['event_eb_event_id'] = event.eb_event_id
        context['event_name'] = event.name
        context['order_count'] = self.get_queryset().count()
        return context


def redis_conn():
    url_p = urlparse.urlparse(os.environ.get('REDIS_URL'))
    return redis.Redis(host=url_p.hostname, port=url_p.port, db=1)


class RedisPrinterOrder(SingleTableView, View):

    def get(self, request, *args, **kwargs):
        try:
            attendee = get_db_attendee_from_eb_id(
                self.kwargs['attendee_id'],
                self.kwargs['event_id'],
            )

            org_id = UserOrganization.objects.filter(
                user=self.request.user.id,
            ).values_list(
                'organization',
                flat=True,
            ).first()
            printer_id = Printer.objects.filter(
                organization=org_id,
            ).values_list(
                'id',
                flat=True,
            ).first()
            rc = redis_conn()
            job_key = "job_{}".format(rc.incr("job_id"))
            job_data = {'job_key': job_key,
                        'first_name': attendee.first_name,
                        'last_name': attendee.last_name}
            rc.set(job_key, pickle.dumps(job_data))
            printer_key = "printer_{}".format(printer_id)
            rc.rpush(printer_key, job_key)
            messages.info(
                self.request,
                'The order was printed correctly.',
            )
        except Exception as e:
                messages.info(
                    self.request,
                    e,
                )
        return redirect(reverse(
            'printing_list',
            kwargs={'event_id': self.kwargs['event_id']},
        ))
