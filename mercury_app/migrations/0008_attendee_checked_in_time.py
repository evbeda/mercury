# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-11-01 00:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mercury_app', '0007_auto_20181031_1218'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendee',
            name='checked_in_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
