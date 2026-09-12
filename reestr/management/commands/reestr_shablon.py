# -*- coding: utf-8 -*-
"""Shablons/reeystr/ papkasidagi .docx shablonlarni yasab beradi.

    python manage.py reestr_shablon            # yo'qlarini yasaydi
    python manage.py reestr_shablon --force    # borini ham qayta yozadi
    python manage.py reestr_shablon rad        # faqat bittasini

DIQQAT: --force qo'lda kiritilgan tahrirlarni yo'qotadi. Sukut bo'yicha
mavjud fayllarga tegilmaydi.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from reestr.shablon_qurish import SHABLONLAR, shablon_yasash


class Command(BaseCommand):
    help = "Reestr tizimi uchun boshlang'ich .docx shablonlarni yasaydi"

    def add_arguments(self, parser):
        parser.add_argument(
            "shablonlar", nargs="*",
            help=f"Qaysi shablon(lar): {', '.join(SHABLONLAR)}. Bo'sh qoldirilsa — hammasi.",
        )
        parser.add_argument(
            "--force", action="store_true",
            help="Mavjud fayllarni ham qayta yozish (qo'lda kiritilgan tahrirlar yo'qoladi!)",
        )

    def handle(self, *args, **options):
        papka = settings.REESTR_SHABLONLAR_DIR
        papka.mkdir(parents=True, exist_ok=True)

        tanlangan = options["shablonlar"] or list(SHABLONLAR)
        notogri = [k for k in tanlangan if k not in SHABLONLAR]
        if notogri:
            raise CommandError(
                f"Noma'lum shablon: {', '.join(notogri)}. "
                f"Mavjudlari: {', '.join(SHABLONLAR)}"
            )

        for kod in tanlangan:
            fayl_nomi = SHABLONLAR[kod][0]
            yol = papka / fayl_nomi
            if yol.exists() and not options["force"]:
                self.stdout.write(f"  o'tkazib yuborildi (mavjud): {fayl_nomi}")
                continue
            shablon_yasash(kod, yol)
            self.stdout.write(self.style.SUCCESS(f"  yasaldi: {fayl_nomi}"))

        self.stdout.write(f"\nPapka: {papka}")
        self.stdout.write("Shablonlarni Wordda ochib erkin tahrirlashingiz mumkin.")
