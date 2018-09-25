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
    date_tz = models.CharField(max_length=64)
    start_date_utc = models.DateTimeField()
    end_date_utc = models.DateTimeField()
    created = models.DateTimeField()
    changed = models.DateTimeField()
    status = models.CharField(max_length=16)


class Order(models.Model):
    event_id = models.ForeignKey(
        'Event',
        on_delete=models.CASCADE
    )
    id_order = models.IntegerField()
    changed = models.DateTimeField()
    created = models.DateTimeField()
    name = models.CharField(max_length=256)
    status = models.CharField(max_length=32)
    email = models.EmailField(max_length=256)


class Merchandise(models.Model):
    order_id = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=256)
    item_type = models.CharField(max_length=128)
    currency = models.CharField(max_length=16)
    value = models.IntegerField()
