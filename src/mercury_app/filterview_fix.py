from django.core.exceptions import ImproperlyConfigured
from django_filters.views import FilterView


class MyFilterView(FilterView):

    def get_filterset_kwargs(self, filterset_class):
        """
        Returns the keyword arguments for instanciating the filterset.
        """
        kwargs = {
            'data': self.request.GET,
            'request': self.request,
        }
        try:
            kwargs.update({
                'queryset': self.get_queryset(),
            })
        except ImproperlyConfigured:
            # ignore the error here if the filterset has a model defined
            # to acquire a queryset from
            if filterset_class._meta.model is None:
                msg = ("'%s' does not define a 'model' and the view '%s' does "
                       "not return a valid queryset from 'get_queryset'.  You "
                       "must fix one of them.")
                args = (filterset_class.__name__, self.__class__.__name__)

                raise ImproperlyConfigured(msg % args)
        return kwargs
