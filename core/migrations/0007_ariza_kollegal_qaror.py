# -*- coding: utf-8 -*-
"""Tayinlangan arizalar uchun kollegal (mahalla yettiligi) qaror raqami.

Shablonlarda "(Kollegal qaror raqami-{kollegal_qaror})" bo'lib chiqadi.
Mavjud yozuvlarda bo'sh qoladi — eski xatlar qayta yuklab olinganda
qavs ichi bo'sh ko'rinadi, shuning uchun ularni tahrirlab to'ldiring.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_xizmat_hujjati"),
    ]

    operations = [
        migrations.AddField(
            model_name="ariza",
            name="kollegal_qaror",
            field=models.CharField(
                blank=True, default="",
                help_text="Mahalla yettiligi qarorining raqami — xatda "
                          "\"(Kollegal qaror raqami-...)\" bo'lib chiqadi",
                max_length=100, verbose_name="Kollegal qaror raqami",
            ),
        ),
    ]
