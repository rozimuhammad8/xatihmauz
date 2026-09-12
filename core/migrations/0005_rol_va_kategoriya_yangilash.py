# -*- coding: utf-8 -*-
"""Rol kodlarini va ariza kategoriyalarini yangilaydi.

1. XodimProfil.rol: "saxovat" -> "bosh_ijtimoiy", "xat" -> "reestr".
   Mavjud xodimlar o'z bo'limida qolishi uchun qiymatlar ko'chiriladi
   (reverse funksiyasi ham bor — migratsiyani orqaga qaytarish mumkin).

2. Ariza.kategoriya: "favqulodda" olib tashlandi, "davolanish" va
   "jarrohlik" qo'shildi.

   DIQQAT: eski "favqulodda" arizalari O'CHIRILMAYDI — foydalanuvchi
   ma'lumoti yo'qotilmasligi uchun bazada saqlanib qoladi. Ular ro'yxatda
   ko'rinadi, lekin .docx eksport qilinganda tushunarli xabar beriladi
   (core/docx_export.py -> ShablonTopilmadi), chunki favqulodda_yordam_*.docx
   shablonlari olib tashlangan. Bunday arizalarni kerak bo'lsa qo'lda
   boshqa kategoriyaga o'tkazing yoki o'chiring.
"""
from django.db import migrations, models

ROL_KOCHIRISH = {
    "saxovat": "bosh_ijtimoiy",
    "xat": "reestr",
}


def rollarni_yangilash(apps, schema_editor):
    XodimProfil = apps.get_model("core", "XodimProfil")
    for eski, yangi in ROL_KOCHIRISH.items():
        XodimProfil.objects.filter(rol=eski).update(rol=yangi)


def rollarni_qaytarish(apps, schema_editor):
    XodimProfil = apps.get_model("core", "XodimProfil")
    for eski, yangi in ROL_KOCHIRISH.items():
        XodimProfil.objects.filter(rol=yangi).update(rol=eski)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_tashkilot_xodimprofil_tashkilot"),
    ]

    operations = [
        # Avval maydonni kengaytiramiz ("bosh_ijtimoiy" 13 belgi — eski
        # max_length=16 ga sig'sa ham, kelajakdagi rollar uchun joy qoldiriladi),
        # keyingina qiymatlarni ko'chiramiz.
        migrations.AlterField(
            model_name="xodimprofil",
            name="rol",
            field=models.CharField(
                choices=[
                    ("bosh_ijtimoiy", "Bosh ijtimoiy (arizalar)"),
                    ("reestr", "Reestr tizimi"),
                ],
                default="bosh_ijtimoiy",
                max_length=24,
                verbose_name="Rol",
            ),
        ),
        migrations.RunPython(rollarni_yangilash, rollarni_qaytarish),
        migrations.AlterField(
            model_name="ariza",
            name="kategoriya",
            field=models.CharField(
                choices=[
                    ("oziq_ovqat", "Oziq-ovqat"),
                    ("kiyim_kechak", "Kiyim-kechak"),
                    ("kommunal_tolovlar", "Kommunal to'lovlar"),
                    ("uy_joy", "Uy-joy ta'mirlash"),
                    ("davolanish", "Davolanish xarajatlari"),
                    ("jarrohlik", "Jarrohlik amaliyoti xarajatlari"),
                ],
                max_length=32,
            ),
        ),
        migrations.AlterModelOptions(
            name="ariza",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Ariza",
                "verbose_name_plural": "Arizalar",
            },
        ),
        migrations.AddIndex(
            model_name="ariza",
            index=models.Index(
                fields=["created_by", "-created_at"], name="ariza_muallif_sana_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="ariza",
            index=models.Index(fields=["kategoriya", "holat"], name="ariza_kat_holat_idx"),
        ),
    ]
