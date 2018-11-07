from django.db import models
from mercury_app.models import Organization
import uuid
# Create your models here.


class Printer(models.Model):

    name = models.CharField(max_length=128)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
    )
    key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    secret_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
