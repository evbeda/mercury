# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-11-08 13:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('badges_app', '0003_auto_20181106_1141'),
    ]

    operations = [
        migrations.AlterField(
            model_name='printer',
            name='secret_key',
            field=models.UUIDField(unique=True),
        ),
    ]