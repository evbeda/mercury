from django.conf import settings
from django.db import models
from django.core.cache import cache
from mercury_app.app_settings import WH_TYPE

MERCH_STATUS = (
    ('CO', 'Delivered'),
    ('PA', 'Partially delivered'),
    ('PE', 'Pending delivery'),
)


class Organization(models.Model):
    eb_organization_id = models.CharField(
        max_length=40,
        unique=True,
        default=0,
    )
    name = models.CharField(max_length=128)

    def __string__(self):
        return self.name


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
    description = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
    )
    eb_event_id = models.CharField(
        max_length=40,
        unique=True,
    )
    url = models.CharField(max_length=128)
    date_tz = models.CharField(max_length=64)
    start_date_utc = models.DateTimeField()
    end_date_utc = models.DateTimeField()
    created = models.DateTimeField()
    changed = models.DateTimeField()
    status = models.CharField(max_length=16)
    badges_tool = models.BooleanField(default=False)
    merchandise_tool = models.BooleanField(default=True)

    def __string__(self):
        return self.name

    def date_start_date_utc(self):
        return self.start_date_utc.strftime('%b. %e, %Y - %-I:%M %p')

    @property
    def is_processing(self):
        return cache.get(self.eb_event_id)


class Order(models.Model):

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    eb_order_id = models.BigIntegerField(
        unique=True,
    )
    changed = models.DateTimeField()
    created = models.DateTimeField()
    status = models.CharField(max_length=32)
    email = models.EmailField(max_length=256)
    merch_status = models.CharField(
        max_length=2,
        choices=MERCH_STATUS,
        default='PE',
    )
    has_merchandise = models.BooleanField()

    def __string__(self):
        return '{} {}'.format(self.first_name, self.last_name)

    def date_created(self):
        return self.created.strftime('%b. %e, %Y - %I:%M %p')


class Merchandise(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE
    )
    eb_merchandising_id = models.CharField(max_length=8, unique=True)
    name = models.CharField(max_length=256)
    item_type = models.CharField(max_length=128)
    currency = models.CharField(max_length=3)
    quantity = models.IntegerField(default=0)
    value = models.CharField(max_length=16)

    def quantity_handed(self, date):
        return Transaction.objects.filter(
            merchandise__id=self.id,
            operation_type='HA',
            date=date).count()

    def __string__(self):
        return self.name


class UserWebhook(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    webhook_id = models.CharField(max_length=16, unique=True)
    wh_type = models.CharField(
        max_length=2,
        choices=WH_TYPE,
    )


class Transaction(models.Model):

    OPERATION_TYPES = (
        ('HA', 'Fulfillment'),
        ('RE', 'Return'),
    )
    date = models.DateTimeField(auto_now_add=False)
    from_who = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    notes = models.CharField(max_length=256)
    merchandise = models.ForeignKey(
        Merchandise,
        on_delete=models.CASCADE,
    )
    device_name = models.CharField(max_length=128)
    operation_type = models.CharField(
        max_length=2,
        choices=OPERATION_TYPES,
        default='HA',
    )


class Attendee(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    eb_attendee_id = models.CharField(max_length=16)
    barcode = models.CharField(max_length=30, unique=True)
    barcode_url = models.CharField(max_length=120)
    checked_in = models.BooleanField()
    checked_in_time = models.DateTimeField(
        blank=True,
        null=True,
    )
