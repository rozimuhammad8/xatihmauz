# -*- coding: utf-8 -*-
"""sr-new.ihma.uz to'lovlari endi bank hisob raqami emas, plastik karta
(PAN) orqali amalga oshiriladi - maydon shunga mos nomlandi. RenameField
ishlatiladi (AddField+RemoveField emas), shuning uchun mavjud yozuvlardagi
qiymatlar saqlanib qoladi."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reestr', '0007_alter_xat_template'),
    ]

    operations = [
        migrations.RenameField(
            model_name='xat',
            old_name='hisob_raqami',
            new_name='karta_raqami',
        ),
        migrations.AlterField(
            model_name='xat',
            name='karta_raqami',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Karta raqami'),
        ),
    ]
