# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-13 08:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0008_auto_20160513_1454'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invitioncode',
            name='code',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='邀请码'),
        ),
    ]
