from django.conf.urls import url
from mercury_app.views import Home

urlpatterns = [
    url(r'^$', Home.as_view(template_name='index.html'), name='index'),
]
