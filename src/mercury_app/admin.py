from django.contrib import admin

from .models import (
    Organization,
    UserOrganization,
    Event,
    Order,
)

admin.site.register(Organization)
admin.site.register(UserOrganization)
admin.site.register(Event)
admin.site.register(Order)
