# -*- coding: utf-8 -*-
"""Xizmat hujjatlari shablonlarini yasaydi (Shablons/xizmat/*.docx).

Manba — "yangi shablonlar/" papkasidagi haqiqiy namunalar. Ular nusxalanadi
va ichidagi aniq qiymatlar ({mahalla}, {xodim} kabi) placeholder'larga
almashtiriladi. Namunaning o'z formati (sahifa o'lchami, shrift, qalin
qismlar, tabulyatsiya) to'liq saqlanadi — biz faqat matnni almashtiramiz.

    python manage.py xizmat_shablon
    python manage.py xizmat_shablon --force

Almashtirish soni tekshiriladi: namuna matni kutilganidan farq qilsa,
buyruq jim qolmasdan xato beradi.
"""
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from docx import Document

from core.docx_utils import iter_all_paragraphs, replace_in_doc

# Har bir shablon uchun: (manba fayl, natija fayl, [(eski matn, placeholder, nechta)])
# "nechta" — namunada necha marta uchrashi kerakligi. Mos kelmasa xato.
KOCHIRISHLAR = {
    "bildirgi": (
        "bildirgi.docx",
        "bildirgi.docx",
        [
            ("Yusupova Yorqinoy Xakimjon qiz", "{xodim}", 4),
            ("Mart", "{mahalla}", 3),
            ("2024-yil 3-oktabr", "{ish_boshlagan_sana}", 1),
            ("2026-yilning 19-20-avgust", "{buzilish_sanasi}", 2),
            ("09:00", "{ish_vaqti}", 1),
            ("Markaz Direktori:", "{tashkilot_nomi} direktori:", 1),
            ("S.Mutalibov", "{rahbar}", 1),
        ],
    ),
    "ogohlantirish": (
        "ogoxlantirish_zoom.docx",
        "ogohlantirish.docx",
        [
            ("Sidiqov Xasanboy", "{xodim}", 1),
            ("Tolmazor", "{mahalla}", 1),
            ("30-iyun", "{yigilish_sanasi}", 1),
            ("direktor o‘rinbosari Abdullayev Sirojiddin Sadullayevich",
             "{rahbar_lavozimi} {rahbar_fio}", 1),
            ("Markaz direktori", "{tashkilot_nomi} direktori", 1),
            ("S.Mutalibov", "{rahbar}", 1),
        ],
    ),
    "talabnoma": (
        "talabnoma.docx",
        "talabnoma.docx",
        [
            ("Andijon tuman kambagallikni kiskartirish va bandlik bo‘limi",
             "{qabul_qiluvchi}", 1),
            ("MADAZIMOV ABDUMUXTOR MADAMINOVICH", "{xodim}", 1),
            ("IMINOVA DILNOZA MAMATKOMILOVNA", "{fuqaro}", 1),
            ("2010-yil 3-iyun", "{tugilgan_sana}", 1),
            ("Sanoat", "{mahalla}", 1),
            ("Mahalla xokim yordamchisiga даромад манбаи ва бандликни таъминлаш "
             "учун йўналтириш", "{yordam_turi}", 1),
            ("Markazi direktori:", "{tashkilot_nomi} direktori:", 1),
            ("S.Mutalibov", "{rahbar}", 1),
        ],
    ),
}


def _toliq_matn(yol):
    doc = Document(str(yol))
    return "\n".join(p.text for p in iter_all_paragraphs(doc))


class Command(BaseCommand):
    help = "Xizmat hujjatlari uchun .docx shablonlarni namunalardan yasaydi"

    def add_arguments(self, parser):
        parser.add_argument("shablonlar", nargs="*",
                            help=f"Qaysi shablon: {', '.join(KOCHIRISHLAR)}")
        parser.add_argument("--force", action="store_true",
                            help="Mavjud fayllarni qayta yozish (qo'lda tahrirlar yo'qoladi!)")

    def handle(self, *args, **options):
        manba_papka = settings.XIZMAT_NAMUNA_DIR
        if not manba_papka.exists():
            raise CommandError(
                f"Namunalar papkasi topilmadi: {manba_papka}\n"
                "Shablonlar allaqachon yasalgan bo'lsa, bu buyruq kerak emas."
            )
        papka = settings.XIZMAT_SHABLONLAR_DIR
        papka.mkdir(parents=True, exist_ok=True)

        tanlangan = options["shablonlar"] or list(KOCHIRISHLAR)
        notogri = [k for k in tanlangan if k not in KOCHIRISHLAR]
        if notogri:
            raise CommandError(f"Noma'lum shablon: {', '.join(notogri)}")

        for kod in tanlangan:
            manba_nomi, natija_nomi, almashtirishlar = KOCHIRISHLAR[kod]
            natija = papka / natija_nomi
            if natija.exists() and not options["force"]:
                self.stdout.write(f"  o'tkazib yuborildi (mavjud): {natija_nomi}")
                continue

            manba = manba_papka / manba_nomi
            if not manba.exists():
                raise CommandError(f"Namuna topilmadi: {manba}")

            matn = _toliq_matn(manba)
            for eski, _yangi, kutilgan in almashtirishlar:
                topildi = matn.count(eski)
                if topildi != kutilgan:
                    raise CommandError(
                        f"{manba_nomi}: \"{eski[:45]}...\" {topildi} marta topildi, "
                        f"{kutilgan} kutilgan edi. Namuna o'zgarganmi? "
                        "KOCHIRISHLAR ro'yxatini yangilang."
                    )

            shutil.copyfile(manba, natija)
            doc = Document(str(natija))
            replace_in_doc(doc, {eski: yangi for eski, yangi, _n in almashtirishlar})
            doc.save(str(natija))

            yangi_matn = _toliq_matn(natija)
            qolgan = [eski for eski, _y, _n in almashtirishlar if eski in yangi_matn]
            if qolgan:
                raise CommandError(f"{natija_nomi}: almashtirilmay qoldi: {qolgan}")

            self.stdout.write(self.style.SUCCESS(f"  yasaldi: {natija_nomi}"))

        self.stdout.write(f"\nPapka: {papka}")
