# -*- coding: utf-8 -*-
"""`xsobraqam` maydoni to'g'ri nom bilan qayta nomlanadi: `hisob_raqami`.

Maydon nomi imlo xatosi bilan yozilgan edi ("xsobraqam"), bazadagi qiymatlar
esa to'g'ri. RenameField ustunni nomini almashtiradi — ma'lumot yo'qolmaydi.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("reestr", "0003_xat_indekslar"),
    ]

    operations = [
        migrations.RenameField(
            model_name="xat",
            old_name="xsobraqam",
            new_name="hisob_raqami",
        ),
    ]
