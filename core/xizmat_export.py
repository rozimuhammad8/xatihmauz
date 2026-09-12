# -*- coding: utf-8 -*-
"""Xizmat hujjatlarini Shablons/xizmat/*.docx asosida yaratadi.

Arizalar eksporti bilan bir xil mantiq: shablon ochiladi, {belgi}lar
qiymatga almashtiriladi. Matnni o'zgartirish uchun .docx ni Wordda ochish
kifoya — bu yerdagi kodga tegish shart emas.
"""
import io

from django.conf import settings
from docx import Document

from .docx_export import ShablonTopilmadi, format_sana
from .docx_utils import replace_in_doc
from .models import XizmatHujjati
from .text_utils import ijrochi_qisqa_ism

SHABLON_FAYLLAR = {
    XizmatHujjati.TUR_BILDIRGI: "bildirgi.docx",
    XizmatHujjati.TUR_OGOHLANTIRISH: "ogohlantirish.docx",
    XizmatHujjati.TUR_TALABNOMA: "talabnoma.docx",
}


def shablon_yolini_topish(turi):
    fayl_nomi = SHABLON_FAYLLAR.get(turi)
    if not fayl_nomi:
        raise ShablonTopilmadi(f"\"{turi}\" turi uchun shablon belgilanmagan.")
    yol = settings.XIZMAT_SHABLONLAR_DIR / fayl_nomi
    if not yol.exists():
        raise ShablonTopilmadi(
            f"Shablon fayli topilmadi: Shablons/xizmat/{fayl_nomi}. "
            "Uni tiklash uchun: python manage.py xizmat_shablon"
        )
    return yol, fayl_nomi


def _almashtirishlar(hujjat):
    profil = getattr(hujjat.created_by, "profil", None)
    tashkilot = profil.tashkilot if profil else None
    return {
        "{mahalla}": hujjat.mahalla,
        "{xodim}": hujjat.xodim_fio,
        "{ish_boshlagan_sana}": format_sana(hujjat.ish_boshlagan_sana),
        "{buzilish_sanasi}": hujjat.buzilish_sanasi,
        "{ish_vaqti}": hujjat.ish_vaqti,
        "{yigilish_sanasi}": hujjat.yigilish_sanasi,
        "{rahbar_lavozimi}": hujjat.rahbar_lavozimi,
        "{rahbar_fio}": hujjat.rahbar_fio,
        "{qabul_qiluvchi}": hujjat.qabul_qiluvchi,
        "{fuqaro}": hujjat.fuqaro_fio,
        "{tugilgan_sana}": format_sana(hujjat.fuqaro_tugilgan_sana),
        "{yordam_turi}": hujjat.yordam_turi,
        "{tashkilot_nomi}": tashkilot.nomi if tashkilot else "Markaz",
        "{rahbar}": tashkilot.rahbar if tashkilot else "",
        "{ijrochi}": ijrochi_qisqa_ism(hujjat.created_by),
    }


def xizmat_docx_yaratish(hujjat):
    """Hujjat obyekti asosida to'ldirilgan .docx ni (BytesIO, fayl nomi) qaytaradi."""
    shablon_yoli, fayl_nomi = shablon_yolini_topish(hujjat.turi)
    doc = Document(str(shablon_yoli))
    replace_in_doc(doc, _almashtirishlar(hujjat))

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer, fayl_nomi
