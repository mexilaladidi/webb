# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-19 12:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0013_auto_20160518_1252'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitioncode',
            name='giftmoney',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='invitioncode',
            name='bindusername',
            field=models.CharField(blank=True, max_length=20, verbose_name='用户名'),
        ),
    ]
