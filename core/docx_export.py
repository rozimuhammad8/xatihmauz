# -*- coding: utf-8 -*-
"""DOCX eksport: Shablons/Ariza/*.docx fayllarni to'ldirib, tayyor hujjat qaytaradi.

Run (bir necha <w:r> ga bo'lingan) chegaralaridan qat'iy nazar matn almashtirish
mantig'i core/docx_utils.py da — u "Reestr tizimi" bilan umumiy.
"""
import io

from django.conf import settings
from docx import Document

from .docx_utils import ShablonTopilmadi, expand_paragraph, find_paragraph, replace_in_doc
from .reasons import TEMPLATE_FAYLLAR
from .text_utils import ijrochi_qisqa_ism

PLACEHOLDER = "{Appda belgilangan sabablar}"

OYLAR = {
    1: "yanvar", 2: "fevral", 3: "mart", 4: "aprel",
    5: "may", 6: "iyun", 7: "iyul", 8: "avgust",
    9: "sentyabr", 10: "oktyabr", 11: "noyabr", 12: "dekabr",
}


def format_sana(d):
    if not d:
        return ""
    return f"{d.year}-yil {d.day}-{OYLAR[d.month]}"


def shablon_yolini_topish(kategoriya, holat):
    """(kategoriya, holat) juftligi uchun shablon faylini qaytaradi.

    Ilgari bu yer to'g'ridan-to'g'ri TEMPLATE_FAYLLAR[...] edi: kategoriya
    ro'yxatdan chiqarilgan bo'lsa (masalan "favqulodda") yoki shablon fayli
    o'chib ketgan bo'lsa, foydalanuvchi 500-xatolik ko'rardi. Endi sababi
    tushunarli xabar beriladi.
    """
    fayl_nomi = TEMPLATE_FAYLLAR.get((kategoriya, holat))
    if not fayl_nomi:
        raise ShablonTopilmadi(
            f"\"{kategoriya}\" kategoriyasi va \"{holat}\" holati uchun shablon "
            "belgilanmagan. Bu kategoriya tizimdan olib tashlangan bo'lishi mumkin — "
            "arizani mavjud kategoriyalardan biriga o'zgartiring."
        )
    yol = settings.SHABLONLAR_DIR / fayl_nomi
    if not yol.exists():
        raise ShablonTopilmadi(
            f"Shablon fayli topilmadi: Shablons/Ariza/{fayl_nomi}"
        )
    return yol, fayl_nomi


def ariza_docx_yaratish(ariza):
    """Ariza obyekti asosida to'ldirilgan docx faylni BytesIO sifatida qaytaradi."""
    shablon_yoli, fayl_nomi = shablon_yolini_topish(ariza.kategoriya, ariza.holat)

    doc = Document(str(shablon_yoli))

    profil = getattr(ariza.created_by, "profil", None)
    tashkilot = profil.tashkilot if profil else None
    tashkilot_nomi = tashkilot.nomi if tashkilot else "Tashkilot"
    tashkilot_rahbar = tashkilot.rahbar if tashkilot else ""
    ijrochi = ijrochi_qisqa_ism(ariza.created_by)

    replacements = {
        "{tuman}": ariza.tuman,
        "{mfy}": ariza.mfy,
        "{kucha}": ariza.kucha,
        "{fio}": ariza.fio,
        "{sana}": format_sana(ariza.sana),
        "{murojaat_raqami}": ariza.murojaat_raqami,
        "{ariza_raqami}": ariza.ariza_raqami,
        "{tashkilot}": ariza.tashkilot,
        # Shablonlarda statik yozilgan imzo bloki — endi tashkilot va
        # xodimning o'ziga moslab almashtiriladi.
        "Markazi direktori:": f"{tashkilot_nomi} direktori:",
        "S.Mutalibov": tashkilot_rahbar,
        "Ijrochi: Y.Olimjonov": f"Ijrochi: {ijrochi}",
    }

    if ariza.holat == "tayinlangan":
        replacements["{ajratilgan_summa}"] = ariza.ajratilgan_summa
        replacements["{kollegal_qaror}"] = ariza.kollegal_qaror
        replace_in_doc(doc, replacements)
    else:
        replace_in_doc(doc, replacements)
        sabablar = ariza.rad_sabablari_royxati()
        matnlar = [f"{i + 1}) {t}" for i, (_, t) in enumerate(sabablar)] or ["Sabab ko'rsatilmagan."]
        marker = find_paragraph(doc, PLACEHOLDER)
        if marker is not None:
            expand_paragraph(marker, matnlar)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer, fayl_nomi
