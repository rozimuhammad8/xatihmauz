# -*- coding: utf-8 -*-
"""Dashboard filtrlari uchun indekslar (muallif+sana, shablon turi, murojaat sanasi)."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reestr", "0002_alter_xat_template"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="xat",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Xat",
                "verbose_name_plural": "Xatlar",
            },
        ),
        migrations.AddIndex(
            model_name="xat",
            index=models.Index(
                fields=["created_by", "-created_at"], name="xat_muallif_sana_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="xat",
            index=models.Index(fields=["template"], name="xat_shablon_idx"),
        ),
        migrations.AddIndex(
            model_name="xat",
            index=models.Index(fields=["murojaat_vaqti"], name="xat_murojaat_sana_idx"),
        ),
    ]
