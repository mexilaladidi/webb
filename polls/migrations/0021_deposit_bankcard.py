# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-02 10:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0020_auto_20160602_1855'),
    ]

    operations = [
        migrations.AddField(
            model_name='deposit',
            name='bankcard',
            field=models.CharField(default='', max_length=128, verbose_name='银行卡信息'),
            preserve_default=False,
        ),
    ]
