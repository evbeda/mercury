from django.db import models
import uuid


class Printer(models.Model):

    name = models.CharField(max_length=128)
    event = models.ForeignKey(
        'mercury_app.Event',
        on_delete=models.CASCADE,
    )
    key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    secret_key = models.UUIDField(editable=True, unique=True, null=True)
    auto = models.BooleanField(default=False)


class CustomLabel(models.Model):

    event = models.ForeignKey(
        'mercury_app.Event',
        on_delete=models.CASCADE,
    )
    string = models.CharField(max_length=255)
