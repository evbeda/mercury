from django.db import models


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
