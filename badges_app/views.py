import os
import redis
import json
import uuid
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import (
    redirect,
)
from django.views.generic.base import TemplateView
from rest_framework.views import APIView, View
from django.views.generic import TemplateView
from django_tables2 import (
    SingleTableMixin,
    SingleTableView,
)
from mercury_app.filterview_fix import MyFilterView
from mercury_app.utils import (
    EventAccessMixin,
    get_db_attendee_from_eb_id,
    get_canned_questions_list,
)
from badges_app.utils import (
    printer_json,
    configure_printer,
    update_printer_name,
    printer_queue,
    confirm_job,
    set_custom_label,
)
from mercury_app.models import (
    Attendee,
    Event,
)
from badges_app.models import (
    Printer,
    CustomLabel,
)
from badges_app.tables import PrintingTable
from badges_app.filters import AttendeeFilter
from django.views.generic.list import ListView
from django.shortcuts import render
from badges_app.utils import set_redis_job


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
class FilteredPrintingList(SingleTableMixin, MyFilterView, EventAccessMixin, LoginRequiredMixin):
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


@method_decorator(login_required, name='dispatch')
class RedisPrinterOrder(SingleTableView, View, LoginRequiredMixin, EventAccessMixin):

    def get(self, request, *args, **kwargs):
        attendee = get_db_attendee_from_eb_id(
            self.kwargs['attendee_id'],
            self.kwargs['event_id'],
        )
        result = set_redis_job(self.request.GET.get('printer_id'),
                               attendee,)
        if result:
            messages.info(
                self.request,
                'The order was printed correctly.',
            )
        else:
            messages.info(
                self.request,
                'The order was not printed correctly.',
            )
        return redirect(reverse(
            'printing_list',
            kwargs={'event_id': self.kwargs['event_id']},
        ))


@method_decorator(login_required, name='dispatch')
class CreatePrinter(View, LoginRequiredMixin, EventAccessMixin):
    def get(self, request, *args, **kwargs):
        context = {}
        context['event_id'] = self.kwargs['event_id']
        return render(
            request,
            'create_printer.html',
            context=context,
            status=200,
        )

    def post(self, request, *args, **kwargs):
        context = {}
        event_id = self.kwargs['event_id']
        name = self.request.POST.get('name')
        try:
            event = Event.objects.get(eb_event_id=event_id)
            Printer.objects.create(name=name,
                                   event=event)
            context['messages'] = True
            message = 'The printer was added'
            self.request.session['message'] = message
            return render(
                request,
                'printer_list.html',
                context=context,
                status=200,
            )
        except Exception:
            return redirect(reverse('printer_list', kwargs={
                'event_id': event_id}))


@method_decorator(login_required, name='dispatch')
class ListPrinter(ListView, LoginRequiredMixin, EventAccessMixin):
    model = Printer
    template_name = "printer_list.html"

    def get_context_data(self, **kwargs):
        context = super(ListPrinter, self).get_context_data(**kwargs)
        event_id = self.kwargs['event_id']
        event = Event.objects.get(eb_event_id=event_id)
        context['printers'] = Printer.objects.filter(
            event_id=event.id,
        ).order_by('id')
        context['event_id'] = event.eb_event_id
        context['print_auto'] = event.badges_tool_auto
        context['message'] = self.request.session.get('message')
        self.request.session['message'] = None
        return context


@method_decorator(login_required, name='dispatch')
class DeletePrinter(TemplateView, LoginRequiredMixin, EventAccessMixin):
    template_name = 'printer_delete.html'

    def get_context_data(self, **kwargs):
        context = super(DeletePrinter, self).get_context_data(**kwargs)
        context['event'] = self.get_event()
        context['printer'] = Printer.objects.get(id=self.kwargs['printer_id'])
        return context

    def post(self, request, *args, **kwargs):
        printer_id = self.kwargs['printer_id']
        Printer.objects.filter(id=printer_id).delete()
        try:
            printer = Printer.objects.get(id=printer_id)
        except Exception:
            printer = None
        if isinstance(printer, Printer) is False:
            message = 'The Printer has been successfully removed'
            self.request.session['message'] = message
        else:
            message_error = 'An error has occured while the printer was being deleted'
            self.request.session['message'] = message_error
        return redirect(reverse('printer_list', kwargs={
                                'event_id': self.kwargs['event_id']}))


@method_decorator(login_required, name='dispatch')
class ResetPrinter(TemplateView, LoginRequiredMixin, EventAccessMixin):
    template_name = 'printer_delete.html'

    def get(self, request, *args, **kwargs):
        context = super(ResetPrinter, self).get_context_data(**kwargs)
        context['event'] = self.get_event()
        printer = Printer.objects.get(id=self.kwargs['printer_id'])
        printer.secret_key = None
        printer.key = uuid.uuid4()
        printer.save()
        message = 'The Key was changed and the secret key was removed'
        self.request.session['message'] = message
        return redirect(reverse('printer_list', kwargs={
                                'event_id': self.kwargs['event_id']}))


@method_decorator(login_required, name='dispatch')
class SetAutoPrinter(View, LoginRequiredMixin, EventAccessMixin):

    def post(self, request, *args, **kwargs):
        event = self.get_event()
        tool = True if (self.request.POST.get('print_auto')) else False
        event.badges_tool_auto = tool
        event.save()
        Printer.objects.filter(event_id=event.id).update(auto=False)
        printer = Printer.objects.get(id=self.request.POST.get('printer_id'))
        printer.auto = tool
        printer.save()
        message = 'Auto print configured'
        self.request.session['message'] = message
        return redirect(reverse('printer_list', kwargs={
                                'event_id': self.kwargs['event_id']}))


@method_decorator(login_required, name='dispatch')
class CustomLabel(TemplateView, LoginRequiredMixin, EventAccessMixin):
    template_name = 'custom_label.html'

    def get_context_data(self, **kwargs):
        context = super(CustomLabel, self).get_context_data(**kwargs)
        q_list = get_canned_questions_list(
            self.request.user,
            self.kwargs['event_id'],
        )
        context['questions'] = q_list
        return context

    def post(self, request, *args, **kwargs):
        data = self.request.POST
        lines = list(data)[:-1]
        event = Event.objects.get(
            eb_event_id=self.kwargs['event_id'],
        )
        set_custom_label(
            event,
            data[lines[0]],
            data[lines[1]],
            data[lines[2]],
            data[lines[3]],
        )
        messages.info(
            self.request,
            'The label has been updated.',
        )
        return redirect(reverse(
            'printer_list',
            kwargs={'event_id': self.kwargs['event_id']},
        ))
