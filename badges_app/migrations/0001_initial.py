# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-11-06 12:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('mercury_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Printer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mercury_app.Organization')),
            ],
        ),
    ]
