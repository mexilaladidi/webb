# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-16 04:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0009_auto_20160513_1639'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userinfo',
            name='profit',
            field=models.CharField(blank=True, default='', max_length=128, verbose_name='rebate'),
        ),
    ]
