from django.conf import settings
from django.db import models


class Organization(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    org_id = models.IntegerField()
    name = models.CharField(max_length=128)


class Event(models.Model):
    organization_id = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=1024)
    event_id = models.IntegerField()
    url = models.CharField(max_length=128)
    start_date_tz = models.CharField(max_length=64)
    start_date_utc = models.DateTimeField()
    end_date_tz = models.CharField(max_length=64)
    end_date_utc = models.DateTimeField()
    created = models.DateTimeField()
    changed = models.DateTimeField()
    status = models.CharField(max_length=16)


class Order(models.Model):
    event = models.ForeignKey(
        'Event',
        on_delete=models.CASCADE
    )
    id_order = models.IntegerField()
    changed = models.DateTimeField()
    created = models.DateTimeField()
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=200)
    email = models.EmailField(max_length=300)
    merchandise_name = models.CharField(max_length=200)
    currency = models.CharField(max_length=200)
    value = models.IntegerField()
