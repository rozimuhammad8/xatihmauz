# -*- coding: utf-8 -*-
"""Mavjud bazani "xat" ilovasidan "reestr" ilovasiga ko'chiradi.

"xat" ilovasi "reestr" deb qayta nomlanganda Django uchun bu BUTUNLAY YANGI
ilova bo'lib ko'rinadi: u `reestr_xat` jadvalini yaratmoqchi bo'ladi, lekin
bazada `xat_xat` turibdi. Natijada `migrate` "table already exists" xatosi
bilan to'xtaydi.

Bu buyruq uchta yozuvni to'g'rilaydi:
  1. jadval nomi:            xat_xat -> reestr_xat
  2. qo'llanilgan migratsiya: django_migrations.app     'xat' -> 'reestr'
  3. kontent turi:           django_content_type.app_label 'xat' -> 'reestr'

YANGI (bo'sh) bazada bu buyruq KERAK EMAS — oddiy `migrate` yetarli.
Buyruq o'zini tekshiradi: ko'chirish kerak bo'lmasa hech narsa qilmaydi,
shuning uchun ikki marta ishga tushirish xavfsiz.

Tartib:
    python manage.py xat_reestrga_kochir
    python manage.py migrate
"""
from django.core.management.base import BaseCommand
from django.db import connection

ESKI = "xat"
YANGI = "reestr"


def _jadval_bormi(cursor, nomi):
    return nomi in connection.introspection.table_names(cursor)


class Command(BaseCommand):
    help = "Eski 'xat' ilovasidagi bazani 'reestr' nomiga ko'chiradi"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Hech narsani o'zgartirmasdan, nima qilinishini ko'rsatadi",
        )

    def handle(self, *args, **options):
        quruq = options["dry_run"]
        qadamlar = []

        with connection.cursor() as cursor:
            eski_jadval = f"{ESKI}_xat"
            yangi_jadval = f"{YANGI}_xat"

            if _jadval_bormi(cursor, eski_jadval):
                if _jadval_bormi(cursor, yangi_jadval):
                    self.stderr.write(self.style.ERROR(
                        f"Ikkala jadval ham mavjud ({eski_jadval} va {yangi_jadval}). "
                        "Qaysi biri kerakligini qo'lda hal qiling — buyruq to'xtatildi."
                    ))
                    return
                qadamlar.append((
                    f"jadval: {eski_jadval} -> {yangi_jadval}",
                    f'ALTER TABLE "{eski_jadval}" RENAME TO "{yangi_jadval}"',
                    None,
                ))

            cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app = %s", [ESKI])
            if cursor.fetchone()[0]:
                qadamlar.append((
                    "django_migrations.app -> reestr",
                    "UPDATE django_migrations SET app = %s WHERE app = %s",
                    [YANGI, ESKI],
                ))

            cursor.execute(
                "SELECT COUNT(*) FROM django_content_type WHERE app_label = %s", [ESKI]
            )
            if cursor.fetchone()[0]:
                qadamlar.append((
                    "django_content_type.app_label -> reestr",
                    "UPDATE django_content_type SET app_label = %s WHERE app_label = %s",
                    [YANGI, ESKI],
                ))

            if not qadamlar:
                self.stdout.write(self.style.SUCCESS(
                    "Ko'chirish kerak emas — baza allaqachon 'reestr' nomida."
                ))
                return

            for izoh, sql, params in qadamlar:
                if quruq:
                    self.stdout.write(f"  [quruq] {izoh}")
                    continue
                cursor.execute(sql, params) if params else cursor.execute(sql)
                self.stdout.write(self.style.SUCCESS(f"  bajarildi: {izoh}"))

        if quruq:
            self.stdout.write("\nHech narsa o'zgartirilmadi (--dry-run).")
        else:
            self.stdout.write(self.style.SUCCESS(
                "\nKo'chirish tugadi. Endi: python manage.py migrate"
            ))
