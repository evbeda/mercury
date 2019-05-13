from badges_app.models import Printer
from rest_framework import serializers


class PrinterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Printer
        fields = ('id', 'name')
