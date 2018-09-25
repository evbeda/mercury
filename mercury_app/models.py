from django.conf import settings
from django.db import models


class Organization(models.Model):
    eb_organization_id = models.IntegerField()
    name = models.CharField(max_length=128)


class UserOrganization(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
    )


class Event(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=1024)
    eb_event_id = models.IntegerField(default=0)
    url = models.CharField(max_length=128)
    date_tz = models.CharField(max_length=64)
    start_date_utc = models.DateTimeField()
    end_date_utc = models.DateTimeField()
    created = models.DateTimeField()
    changed = models.DateTimeField()
    status = models.CharField(max_length=16)


class Order(models.Model):

    MERCH_STATUS = (
        ('CO', 'Completed'),
        ('PA', 'Partial'),
        ('PE', 'Pending'),
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE
    )
    eb_order_id = models.IntegerField()
    changed = models.DateTimeField()
    created = models.DateTimeField()
    name = models.CharField(max_length=256)
    status = models.CharField(max_length=32)
    email = models.EmailField(max_length=256)
    merch_status = models.CharField(
        max_length=2,
        choices=MERCH_STATUS,
        default='PE',
    )


class Merchandise(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=256)
    item_type = models.CharField(max_length=128)
    currency = models.CharField(max_length=16)
    value = models.IntegerField()
    delivered = models.BooleanField(default=False)
