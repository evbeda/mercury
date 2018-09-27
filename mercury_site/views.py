from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from mercury_app.utils import (
    get_auth_token,
)

@method_decorator(login_required, name='dispatch')
class Home(TemplateView, LoginRequiredMixin):

    """ This is the index view. Here we display all the banners that the user
    has created """

    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        eventbrite = get_auth_token(self.request.user)
        page = self.request.GET.get('page')
        events = eventbrite.get('/users/me/events/?page={}'.format(page))
        return events
