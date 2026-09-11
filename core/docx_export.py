# -*- coding: utf-8 -*-
"""DOCX eksport: shablonlar/*.docx fayllarni to'ldirib, tayyor hujjat qaytaradi.

Run (bir necha <w:r> ga bo'lingan) chegaralaridan qat'iy nazar matn almashtirish
mantig'i uyjoy.py dasturidan olingan.
"""
import copy
import io
from django.conf import settings
from docx import Document
from docx.oxml.ns import qn

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


def _replace_once(paragraph, old, new, start=0):
    """`old`ning `start`dan boshlab birinchi uchrashini `new`ga almashtiradi.

    Qaytadan almashtirilgan matn ichidan qidirmaslik uchun (masalan
    new="S.MutalibovA" bo'lsa-yu old="S.Mutalibov" bo'lsa, new o'zi old'ni
    ichiga oladi va har safar qayta topilib cheksiz o'sib ketishi mumkin edi)
    keyingi qidiruv shu almashtirilgan matndan KEYINGI joydan boshlanadi.
    Yana uchrashi topilsa uning boshlanish indeksini, topilmasa None qaytaradi.
    """
    runs = paragraph.runs
    full_text = "".join(r.text for r in runs)
    idx = full_text.find(old, start)
    if idx == -1:
        return None
    end = idx + len(old)
    pos = 0
    start_run = start_off = None
    end_run = end_off = None
    for i, r in enumerate(runs):
        rlen = len(r.text)
        if start_run is None and pos <= idx < pos + rlen:
            start_run, start_off = i, idx - pos
        if pos < end <= pos + rlen:
            end_run, end_off = i, end - pos
            break
        pos += rlen
    if start_run is None or end_run is None:
        return None
    before = runs[start_run].text[:start_off]
    after = runs[end_run].text[end_off:]
    if start_run == end_run:
        runs[start_run].text = before + new + after
    else:
        runs[start_run].text = before + new
        runs[end_run].text = after
        for i in range(start_run + 1, end_run):
            runs[i].text = ""
    return idx + len(new)


def replace_in_paragraph(paragraph, replacements):
    for old, new in replacements.items():
        if not old:
            continue
        pos = 0
        while True:
            pos = _replace_once(paragraph, old, new, pos)
            if pos is None:
                break


def replace_in_doc(doc, replacements):
    for paragraph in doc.paragraphs:
        replace_in_paragraph(paragraph, replacements)

    def process_table(table):
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    replace_in_paragraph(paragraph, replacements)
                for nested in cell.tables:
                    process_table(nested)

    for table in doc.tables:
        process_table(table)

    for section in doc.sections:
        for part in (section.header, section.footer):
            for paragraph in part.paragraphs:
                replace_in_paragraph(paragraph, replacements)
            for table in part.tables:
                process_table(table)


def _sabablar_paragraflarini_qoyish(doc, matnlar):
    """{Appda belgilangan sabablar} placeholderi joylashgan abzatsni topib,
    har bir sabab uchun ALOHIDA abzats bilan almashtiradi (formatni saqlagan holda)."""
    target_i = None
    for i, p in enumerate(doc.paragraphs):
        if PLACEHOLDER in p.text:
            target_i = i
            break
    if target_i is None:
        return

    paras = doc.paragraphs
    template_p = paras[target_i]._p
    orig_runs = template_p.findall(qn('w:r'))
    rPr_src = orig_runs[0].find(qn('w:rPr')) if orig_runs else None
    pPr_src = template_p.find(qn('w:pPr'))

    new_elements = []
    for text in matnlar:
        p_elem = copy.deepcopy(template_p)
        for r in p_elem.findall(qn('w:r')):
            p_elem.remove(r)
        for pe in p_elem.findall(qn('w:proofErr')):
            p_elem.remove(pe)
        r_elem = p_elem.makeelement(qn('w:r'), {})
        if rPr_src is not None:
            r_elem.append(copy.deepcopy(rPr_src))
        t_elem = r_elem.makeelement(qn('w:t'), {})
        t_elem.set(qn('xml:space'), 'preserve')
        t_elem.text = text
        r_elem.append(t_elem)
        p_elem.append(r_elem)
        new_elements.append(p_elem)

    anchor = template_p
    for elem in new_elements:
        anchor.addnext(elem)
        anchor = elem
    template_p.getparent().remove(template_p)


def ariza_docx_yaratish(ariza):
    """Ariza obyekti asosida to'ldirilgan docx faylni BytesIO sifatida qaytaradi."""
    fayl_nomi = TEMPLATE_FAYLLAR[(ariza.kategoriya, ariza.holat)]
    shablon_yoli = settings.SHABLONLAR_DIR / fayl_nomi

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
        replace_in_doc(doc, replacements)
    else:
        replace_in_doc(doc, replacements)
        sabablar = ariza.rad_sabablari_royxati()
        matnlar = [f"{i + 1}) {t}" for i, (_, t) in enumerate(sabablar)] or ["Sabab ko'rsatilmagan."]
        _sabablar_paragraflarini_qoyish(doc, matnlar)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer, fayl_nomi
