# -*- coding: utf-8 -*-
"""Reestr tizimi xatlarini Shablons/reeystr/*.docx asosida yaratadi.

Ilgari xat butunlay kodda qurilardi (docx_generator.py) — jumlani o'zgartirish
uchun Python faylini tahrirlash kerak edi. Endi "Bosh ijtimoiy" arizalaridagi
kabi tayyor .docx shablon o'qiladi va ichidagi placeholder'lar to'ldiriladi,
ya'ni matnni Wordda ochib tahrirlash kifoya.

Shablonda uch xil belgi ishlatiladi:

  {fio}, {ariza_sanasi} ...   — oddiy matn bilan almashtiriladi
  {avto_royxati} ...          — formatlangan (ichida qalin qismi bor) ro'yxat
  {?avtoRad} ...              — abzats boshidagi SHART: sharti bajarilmasa
                                butun abzats hujjatdan o'chiriladi

Shablon fayli topilmasa, eski kod generatoriga qaytadi — ya'ni papka
tasodifan o'chib ketsa ham tizim ishlashda davom etadi.
"""
import io

from django.conf import settings
from docx import Document

from core.docx_utils import (
    delete_paragraph,
    iter_all_paragraphs,
    replace_in_doc,
    replace_in_paragraph,
    replace_with_segments,
)

from . import docx_generator as dg
from .shablon_qurish import SHABLONLAR


def shablon_yoli(template):
    """Shablon kodiga mos .docx yo'li (mavjud bo'lmasa ham yo'lni qaytaradi)."""
    kirish = SHABLONLAR.get(template)
    if not kirish:
        return None
    return settings.REESTR_SHABLONLAR_DIR / kirish[0]


# ------------------------------------------------------------
# QIYMATLARNI TAYYORLASH
# ------------------------------------------------------------
def _sana(value):
    """'2026-07-16' -> '2026-yil 16-iyul'."""
    year, day, month = dg.split_date(value)
    if not year:
        return ""
    return f"{year}-yil {day}-{month}"


def _davrlar(data):
    """Tasdiqlash xatidagi "... oyidan" va "... uchun" davrlari.

    Mantiq docx_generator.build_tasdiqlandi dagi bilan bir xil: tasdiq/to'lov
    sanasi bo'sh bo'lsa, ariza sanasidagi oyga qaytiladi.
    """
    tasdiq = data.get("tasdiqMalumotlari") or {}
    ariza_year, _ariza_day, ariza_month = dg.split_date(data.get("arizaVaqti"))
    tasdiq_year, tasdiq_month = dg.parse_year_month(tasdiq.get("tasdiqSanasi"))
    tolov_year, tolov_month = dg.parse_year_month(tasdiq.get("tolovSanasi"))

    davr_oy = f"{tasdiq_year}-yil {tasdiq_month}" if tasdiq_month else f"{ariza_year}-yil {ariza_month}"
    if tolov_month:
        davr_tolov = f"{tolov_year}-yil {tolov_month} oyi"
    elif davr_oy:
        davr_tolov = f"{davr_oy} oyi"
    else:
        davr_tolov = "tegishli davr"
    return davr_oy, davr_tolov


def _oddiy_almashtirishlar(data):
    tasdiq = data.get("tasdiqMalumotlari") or {}
    davr_oy, davr_tolov = _davrlar(data)
    return {
        "{mfy}": data.get("mfyNomi") or "",
        "{kucha}": data.get("street") or "",
        "{fio}": data.get("fio") or "",
        "{murojaat_manbasi}": data.get("murojaatfrom") or "",
        "{murojaat_sanasi}": _sana(data.get("murojaatVaqti")),
        "{murojaat_raqami}": data.get("murojaatRaqami") or "",
        "{ariza_maqsadi}": data.get("arizaMaqsadi") or "",
        "{ariza_sanasi}": _sana(data.get("arizaVaqti")),
        "{ariza_id}": data.get("arizaID") or "",
        "{qayta}": "qayta " if data.get("isQayta") else "",
        "{tasdiq_davri}": davr_oy,
        "{tolov_davri}": davr_tolov,
        "{hisob_raqami}": tasdiq.get("hisobRaqami") or "",
        "{tolov_summasi}": dg.format_money(tasdiq.get("tolovSum")),
        "{tayinlash_qoshimcha}": data.get("tayinlashQoshimcha") or "",
        "{qoshimcha_malumot}": data.get("qoshimchaMalumot") or "",
        "{tashkilot_nomi}": data.get("tashkilotNomi") or "Tashkilot",
        "{rahbar}": data.get("tashkilotRahbar") or "",
        "{ijrochi}": data.get("ijrochi") or "",
    }


def _shartlar(data):
    """Har bir {?belgi} uchun: abzats hujjatda qolsinmi?"""
    rad = data.get("radSabablari") or {}
    tasdiq = data.get("tasdiqMalumotlari") or {}
    return {
        "{?avtoRad}": bool(rad.get("avtoRad")),
        "{?uyRad}": bool(rad.get("uyRad")),
        "{?rasmiyRad}": bool(rad.get("rasmiyRad")),
        "{?norasmiyRad}": bool(rad.get("norasmiyRad")),
        "{?uydaEmasRad}": bool(rad.get("uydaEmasRad")),
        "{?tolov}": bool(tasdiq.get("tolovSum") or tasdiq.get("hisobRaqami")),
        "{?tayinlashQoshimcha}": bool(data.get("tayinlashQoshimcha")),
        "{?qoshimchaMalumot}": bool(data.get("qoshimchaMalumot")),
    }


def _segment_almashtirishlari(data):
    """Ichida qalin qismi bo'lgan dinamik ro'yxatlar."""
    rad = data.get("radSabablari") or {}
    natija = {}
    if rad.get("avtoRad"):
        natija["{avto_royxati}"] = dg.car_segments(rad["avtoRad"])
    if rad.get("uyRad"):
        natija["{uy_royxati}"] = dg.uy_segments(rad["uyRad"])
    return natija


# ------------------------------------------------------------
# SHABLONNI TO'LDIRISH
# ------------------------------------------------------------
def _shartli_abzatslarni_ishlash(doc, shartlar):
    """Shart bajarilmagan abzatslarni o'chiradi, bajarilganidan belgini olib
    tashlaydi."""
    for paragraph in list(iter_all_paragraphs(doc)):
        matn = paragraph.text.lstrip()
        for belgi, qolsin in shartlar.items():
            if not matn.startswith(belgi):
                continue
            if qolsin:
                replace_in_paragraph(paragraph, {belgi: ""})
            else:
                delete_paragraph(paragraph)
            break


def _segmentlarni_qoyish(doc, segmentlar):
    for paragraph in list(iter_all_paragraphs(doc)):
        for belgi, segments in segmentlar.items():
            if belgi in paragraph.text:
                replace_with_segments(paragraph, belgi, segments)


def render_letter(data):
    """Xat yozuvi (letter dict) uchun to'ldirilgan .docx — BytesIO qaytaradi."""
    yol = shablon_yoli(data.get("template"))
    if yol is None or not yol.exists():
        # Shablon yo'q (masalan "arizaKiritilmagan" — unga alohida .docx
        # yasalmagan) yoki papka o'chirilgan: eski kod generatori ishlaydi.
        return dg.build_letter_document(data)

    doc = Document(str(yol))

    _shartli_abzatslarni_ishlash(doc, _shartlar(data))
    _segmentlarni_qoyish(doc, _segment_almashtirishlari(data))

    rad = data.get("radSabablari") or {}
    oddiy = _oddiy_almashtirishlar(data)
    oddiy["{uy_soni}"] = str(len(rad.get("uyRad") or []))
    oddiy["{rasmiy_matni}"] = dg.income_text(rad.get("rasmiyRad") or [])
    replace_in_doc(doc, oddiy)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
