# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-09-28 17:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mercury_app', '0005_merchandise_delivery_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='merchandise',
            name='eb_merchandising_id',
            field=models.CharField(default=0, max_length=8),
        ),
    ]
