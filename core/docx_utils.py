# -*- coding: utf-8 -*-
"""Word (.docx) shablonlari bilan ishlashning umumiy quroli.

Ikkala tizim ham shu moduldan foydalanadi:
  * core  — Shablons/Ariza/*.docx ("Bosh ijtimoiy" arizalari)
  * xat   — Shablons/reeystr/*.docx ("Reestr tizimi" xatlari)

Asosiy muammo: Word bitta jumlani bir necha <w:r> (run) ga bo'lib tashlaydi
(imlo tekshiruvi, til belgisi va h.k. sababli), shuning uchun oddiy
`paragraph.text.replace(...)` ishlamaydi — matn run chegaralaridan o'tib
almashtirilishi kerak. Shu mantiq uyjoy.py dasturidan olingan va bu yerda
bitta joyda saqlanadi.
"""
import copy

from docx.oxml.ns import qn


class ShablonTopilmadi(Exception):
    """Kerakli .docx shablon fayli topilmadi yoki belgilanmagan.

    Ikkala tizim ham (core/docx_export.py, core/xizmat_export.py,
    reestr/docx_templates.py) shu istisnoni ko'taradi — view'lar buni
    ushlab, foydalanuvchiga 500-xatolik o'rniga tushunarli xabar ko'rsatadi.
    """


# ------------------------------------------------------------
# MATN ALMASHTIRISH (run chegaralaridan o'tib)
# ------------------------------------------------------------
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


def iter_all_paragraphs(doc):
    """Hujjatdagi BARCHA abzatslar: asosiy matn, jadvallar (ichma-ich ham),
    kolontitullar. Shablonning qaysi qismida placeholder turganidan qat'i
    nazar topilishi uchun."""

    def from_table(table):
        for row in table.rows:
            for cell in row.cells:
                yield from cell.paragraphs
                for nested in cell.tables:
                    yield from from_table(nested)

    yield from doc.paragraphs
    for table in doc.tables:
        yield from from_table(table)
    for section in doc.sections:
        for part in (section.header, section.footer):
            yield from part.paragraphs
            for table in part.tables:
                yield from from_table(table)


def replace_in_doc(doc, replacements):
    for paragraph in iter_all_paragraphs(doc):
        replace_in_paragraph(paragraph, replacements)


# ------------------------------------------------------------
# ABZATS DARAJASIDAGI AMALLAR
# ------------------------------------------------------------
def find_paragraph(doc, marker):
    """Matnida `marker` bo'lgan birinchi abzatsni qaytaradi (topilmasa None)."""
    for p in iter_all_paragraphs(doc):
        if marker in p.text:
            return p
    return None


def delete_paragraph(paragraph):
    element = paragraph._p
    parent = element.getparent()
    if parent is not None:
        parent.remove(element)


def _blank_clone(paragraph):
    """Abzatsning run'larsiz nusxasi — abzats formatlari (tekislash, chekinish,
    intervallar) saqlanadi, ichidagi matn esa tozalanadi."""
    clone = copy.deepcopy(paragraph._p)
    for r in clone.findall(qn("w:r")):
        clone.remove(r)
    # Word'ning imlo/grammatika belgilari nusxada ortiqcha bo'sh joy hosil
    # qilmasligi uchun olib tashlanadi.
    for tag in ("w:proofErr", "w:bookmarkStart", "w:bookmarkEnd"):
        for el in clone.findall(qn(tag)):
            clone.remove(el)
    return clone


def _source_rpr(paragraph):
    """Abzatsdagi birinchi run'ning formatlash bloki (<w:rPr>) — yangi
    run'lar aynan shu shrift/o'lcham/rangni meros qilib oladi."""
    runs = paragraph._p.findall(qn("w:r"))
    return runs[0].find(qn("w:rPr")) if runs else None


def _make_run(p_elem, rpr_src, text, bold=None, italic=None):
    """Yangi <w:r> elementi yasaydi (hujjatga qo'shmaydi).

    Format `rpr_src` dan meros olinadi; bold/italic faqat None BO'LMAGANDA
    ustidan yoziladi, ya'ni shablonning shrifti/o'lchami/rangi saqlanadi.
    """
    r_elem = p_elem.makeelement(qn("w:r"), {})
    if rpr_src is not None:
        rpr = copy.deepcopy(rpr_src)
    else:
        rpr = r_elem.makeelement(qn("w:rPr"), {})
    if bold is not None:
        for tag in ("w:b", "w:bCs"):
            for el in rpr.findall(qn(tag)):
                rpr.remove(el)
        if bold:
            for tag in ("w:b", "w:bCs"):
                rpr.append(rpr.makeelement(qn(tag), {}))
    if italic is not None:
        for tag in ("w:i", "w:iCs"):
            for el in rpr.findall(qn(tag)):
                rpr.remove(el)
        if italic:
            for tag in ("w:i", "w:iCs"):
                rpr.append(rpr.makeelement(qn(tag), {}))
    if len(rpr):
        r_elem.append(rpr)
    t_elem = r_elem.makeelement(qn("w:t"), {})
    t_elem.set(qn("xml:space"), "preserve")
    t_elem.text = text
    r_elem.append(t_elem)
    return r_elem


def _normalize_segments(item):
    """Bandni segmentlar ro'yxatiga keltiradi.

    Qabul qilinadigan ko'rinishlar:
      "oddiy matn"
      [("matn", {}), ("qalin", {"bold": True})]
    """
    if isinstance(item, str):
        return [(item, {})]
    segments = []
    for seg in item:
        text, kwargs = seg if isinstance(seg, tuple) else (seg, {})
        segments.append((text, kwargs or {}))
    return segments


def expand_paragraph(paragraph, items):
    """Marker abzatsini har bir band uchun ALOHIDA abzats bilan almashtiradi.

    `items` — matnlar yoki segment ro'yxatlari. Har bir yangi abzats marker
    abzatsining formatini (shrift, o'lcham, tekislash, qizil chiziq) meros
    qiladi, shuning uchun shablonni Wordda qanday bezasangiz, natija ham
    shunday chiqadi. Bandlar bo'sh bo'lsa, marker abzatsining o'zi ham
    o'chiriladi.
    """
    rpr_src = _source_rpr(paragraph)
    anchor = paragraph._p
    for item in items:
        p_elem = _blank_clone(paragraph)
        for text, kwargs in _normalize_segments(item):
            p_elem.append(_make_run(p_elem, rpr_src, text,
                                    bold=kwargs.get("bold"), italic=kwargs.get("italic")))
        anchor.addnext(p_elem)
        anchor = p_elem
    delete_paragraph(paragraph)


def set_paragraph_segments(paragraph, segments):
    """Abzats ichidagi barcha run'larni yangi segmentlar bilan almashtiradi
    (abzats formati o'zgarmaydi)."""
    rpr_src = _source_rpr(paragraph)
    p_elem = paragraph._p
    for r in p_elem.findall(qn("w:r")):
        p_elem.remove(r)
    for text, kwargs in _normalize_segments(segments):
        p_elem.append(_make_run(p_elem, rpr_src, text,
                                bold=kwargs.get("bold"), italic=kwargs.get("italic")))


def _consolidate(paragraph, needle, start=0):
    """`needle` bir necha run'ga bo'linib ketgan bo'lsa, uni BITTA run ichiga
    yig'adi va (run indeksi, run ichidagi siljish) juftligini qaytaradi."""
    runs = paragraph.runs
    full_text = "".join(r.text for r in runs)
    idx = full_text.find(needle, start)
    if idx == -1:
        return None
    end = idx + len(needle)
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
        runs[start_run].text = before + needle + after
    else:
        runs[start_run].text = before + needle
        runs[end_run].text = after
        for i in range(start_run + 1, end_run):
            runs[i].text = ""
    return start_run, len(before)


def replace_with_segments(paragraph, placeholder, segments):
    """`placeholder` matnini FORMATLANGAN segmentlar bilan almashtiradi.

    expand_paragraph() butun abzatsni almashtirsa, bu funksiya abzats ichidagi
    bitta so'zni almashtiradi va atrofidagi qo'lda yozilgan matnni tegmay
    qoldiradi. Shu sababli shablonda jumlani ("Sizning oilangiz foydalanuvida
    bo'lgan {avto_royxati} mavjudligi sababli.") Wordda erkin tahrirlash
    mumkin, lekin ro'yxat ichidagi avtomobil rusumi/raqami baribir qalin
    chiqadi. Almashtirilgan bo'lsa True qaytaradi.
    """
    topilgan = _consolidate(paragraph, placeholder)
    if topilgan is None:
        return False
    run_idx, off = topilgan
    run = paragraph.runs[run_idx]
    matn = run.text
    before = matn[:off]
    after = matn[off + len(placeholder):]

    r_elem = run._r
    rpr_src = r_elem.find(qn("w:rPr"))
    p_elem = paragraph._p
    run.text = before

    anchor = r_elem
    for text, kwargs in _normalize_segments(segments):
        yangi = _make_run(p_elem, rpr_src, text,
                          bold=kwargs.get("bold"), italic=kwargs.get("italic"))
        anchor.addnext(yangi)
        anchor = yangi
    if after:
        anchor.addnext(_make_run(p_elem, rpr_src, after))
    return True
