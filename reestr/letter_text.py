# -*- coding: utf-8 -*-
"""
Xatni brauzerda ko'rish (preview) uchun HTML abzatslar generatori.
docx_generator.py dagi AYNAN o'sha matn yasovchi funksiyalar va konstantalar
qayta ishlatiladi (car_segments, uy_segments, income_text, NIZOM/APPEAL/INTRO
paragraflari, split_date va h.k.) — shu orqali .docx va sahifadagi ko'rinish
har doim bir xil matnni ko'rsatishi kafolatlanadi.
"""
from django.utils.html import escape

from . import docx_generator as dg


def _seg_html(segments):
    parts = []
    for seg in segments:
        text, kwargs = seg if isinstance(seg, tuple) else (seg, {})
        html = escape(text)
        if kwargs.get("bold"):
            html = f"<b>{html}</b>"
        if kwargs.get("italic"):
            html = f"<i>{html}</i>"
        parts.append(html)
    return "".join(parts)


def _p(segments):
    return _seg_html(segments)


def rad_paragraphs(data):
    rad = data.get("radSabablari") or {}
    tuman = data.get("tuman") or ""
    paras = [
        _p([(dg.INTRO_PARAGRAPH.replace("{tuman}", tuman), {})]),
        _p([
            ("Sizga ", {}), (data.get("mfyNomi", ""), {"bold": True}),
            (" MFY mahallada kompleks xizmat ko'rsatuvchi xodim, O‘zbekiston Respublikasi "
             "Prezidenti huzuridagi Ijtimoiy himoya milliy Agentligi Andijon viloyati boshqarmasi "
             f"{tuman} “Inson” ijtimoiy xizmatlar markazi faoliyati, hamda xizmat "
             "turlarini yaqindan tanishtirildi.", {}),
        ]),
        _p(dg.NIZOM_FAMILY_REGISTRY_PARAGRAPH),
    ]

    ariza_year, ariza_day, ariza_month = dg.split_date(data.get("arizaVaqti"))
    qayta = "qayta " if data.get("isQayta") else ""
    paras.append(_p([
        ("Nizom talabalariga asosan sizning ", {}),
        (data.get("arizaMaqsadi", ""), {"bold": True}),
        (" uchun berilgan ", {}),
        (f"{ariza_year}-yil {ariza_day}-{ariza_month}", {"bold": True}),
        (" kungi arizangiz va unga ilova qilingan ma’lumotlari «Ijtimoiy himoya yagona reyestri» axborot tizimiga ", {}),
        (f"{data.get('arizaID', '')}-ID", {"bold": True}),
        (" raqam bilan kiritilgan va dastur tomonidan ", {}),
        (qayta, {}),
        ("o'rganilganda quydagilar sababli rad etildi:", {}),
    ]))

    if rad.get("avtoRad"):
        paras.append(_p(
            [("Sizning oilangiz foydalanuvida bo'lgan ", {})] + dg.car_segments(rad["avtoRad"]) +
            [(" mavjudligi sababli", {})] + dg.rad_xulosa_segments(data) +
            [dg.asos_segment("(Asos: VM 35-son qarori 4-bob v-band.)")]
        ))
    if rad.get("uyRad"):
        paras.append(_p(
            [(f"Sizning oilangiz nomiga rasmiylashtirilgan {len(rad['uyRad'])} ta ko'chmas mulk (", {})] +
            dg.uy_segments(rad["uyRad"]) + [(") mavjudligi sababli", {})] +
            dg.rad_xulosa_segments(data) +
            [dg.asos_segment("(Asos: VM 35-son qarori 4-bob b-band.)")]
        ))
    if rad.get("rasmiyRad"):
        paras.append(_p([
            (dg.income_text(rad["rasmiyRad"]), {}),
            (" sababli", {}),
        ] + dg.rad_xulosa_segments(data) + [
            dg.asos_segment("(Asos: VM 35-son qarori 4-bob a-band.)"),
        ]))
    if rad.get("norasmiyRad"):
        paras.append(_p([
            ("O'rganish natijasida ", {}), ("“mahalla yettiligi”", {"bold": True}),
            (" tomonidan o'tkazilgan so'rovnoma xulosasida norasmiy daromad manbaiyga ega "
             "ekanligngiz “Ijtimoiy himoya yagona reyestri” axborot tizimiga kiritilganda "
             "minimal iste'mol xarajatlaridan yuqori daromadingiz mavjudligi sababli", {}),
        ] + dg.rad_xulosa_segments(data) + [
            dg.asos_segment("(Asos: VM 35-son qarori 4-bob a-band.)"),
        ]))
    if rad.get("uydaEmasRad"):
        paras.append(_p([(
            "Ijtimoiy xodim tomonidan yashash sharoitini o'rganish maqsadida amalga oshirilgan "
            "tashrif davomida sizni yashash manzilida mavjud bo'lmaganligi sababli ijtimoiy "
            "holatini o'rganish imkoni bo'lmadi. Natijada murojaat bo'yicha zarur o'rganish "
            "yakunlanmaganligi sababli", {})] + dg.rad_xulosa_segments(data)))

    paras.append(_p([(dg.APPEAL_PARAGRAPH, {})]))
    return paras


def tasdiqlandi_paragraphs(data):
    tasdiq = data.get("tasdiqMalumotlari") or {}
    paras = [
        _p([(dg.INTRO_PARAGRAPH.replace("{tuman}", data.get("tuman") or ""), {})]),
        _p(dg.NIZOM_INTRO_SEGMENTS + [(" bilan tasdiqlangan Nizomning 33-bandiga muvofiq quyidagilar ma’lum qilinadi.", {})]),
        _p(dg.AGAR_PARAGRAPH_SEGMENTS),
    ]
    ariza_year, ariza_day, ariza_month = dg.split_date(data.get("arizaVaqti"))
    tasdiq_year, tasdiq_month = dg.parse_year_month(tasdiq.get("tasdiqSanasi"))
    tolov_year, tolov_month = dg.parse_year_month(tasdiq.get("tolovSanasi"))
    davr_oy = f"{tasdiq_year}-yil {tasdiq_month}" if tasdiq_month else f"{ariza_year}-yil {ariza_month}"

    paras.append(_p([
        (data.get("fio", ""), {"bold": True}), (" sizning ", {}),
        (f"{ariza_year}-yil {ariza_day}-{ariza_month}", {"bold": True}), (" kunidan ", {}),
        (data.get("arizaMaqsadi", ""), {"bold": True}),
        (" tayinlash bo'yicha yuborgan arizangiz «Ijtimoiy himoya yagona reestri» axborot tizimiga ", {}),
        (f"{data.get('arizaID', '')}-ID", {"bold": True}), (" raqam bilan kiritilgan va ", {}),
        (f"{davr_oy}", {"bold": True}), (" oyidan ", {}),
        (data.get("arizaMaqsadi", ""), {"bold": True}),
        (" tayinlangan hamda Kambag'al oila toifasiga kiritilgan.", {}),
    ]))

    if tasdiq.get("tolovSum") or tasdiq.get("hisobRaqami"):
        davr_tolov = f"{tolov_year}-yil {tolov_month} oyi" if tolov_month else (f"{davr_oy} oyi" if davr_oy else "tegishli davr")
        paras.append(_p([
            ("Sizga ", {}), (davr_tolov, {}), (" uchun ", {}),
            (tasdiq.get("hisobRaqami", ""), {}), (" hisob raqamiga ", {}),
            (f"{dg.format_money(tasdiq.get('tolovSum'))}", {}), (" so'm to'lab berilganligini ma’lum qilamiz.", {}),
        ]))

    paras.append(_p(dg.BANK_PARAGRAPH_SEGMENTS))
    paras.append(_p([(dg.APPEAL_PARAGRAPH, {})]))
    return paras


def tayinlandi_paragraphs(data):
    paras = [
        _p([(dg.INTRO_PARAGRAPH.replace("{tuman}", data.get("tuman") or ""), {})]),
        _p(dg.NIZOM_INTRO_SEGMENTS + [(" bilan tasdiqlangan Nizomning 33-bandiga muvofiq quyidagilar ma’lum qilinadi.", {})]),
        _p(dg.AGAR_PARAGRAPH_SEGMENTS),
    ]
    ariza_year, ariza_day, ariza_month = dg.split_date(data.get("arizaVaqti"))
    paras.append(_p([
        (data.get("fio", ""), {"bold": True}), (" sizning ", {}),
        (f"{ariza_year}-yil {ariza_day}-{ariza_month}", {"bold": True}), (" kuni yuborgan ", {}),
        (data.get("arizaMaqsadi", ""), {"bold": True}),
        (" tayinlash bo'yicha yuborgan arizangiz «Ijtimoiy himoya yagona reestri» axborot tizimiga ", {}),
        (f"{data.get('arizaID', '')}-ID", {"bold": True}), (" raqam bilan kiritilgan va ", {}),
        (data.get("arizaMaqsadi", ""), {"bold": True}),
        (" tayinlangan hamda Kambag'al oila toifasiga kiritilgan.", {}),
    ]))
    if data.get("tayinlashQoshimcha"):
        paras.append(_p([(data.get("tayinlashQoshimcha"), {})]))
    paras.append(_p(dg.BANK_PARAGRAPH_SEGMENTS))
    paras.append(_p([(dg.APPEAL_PARAGRAPH, {})]))
    return paras


def muddat_paragraphs(data):
    tuman = data.get("tuman") or ""
    paras = [
        _p([
            ("O‘zbekiston Respublikasi Prezidenti huzuridagi Ijtimoiy himoya milliy agentligi "
             f"Andijon viloyati {tuman} “Inson” ijtimoiy xizmatlar markazi ", {}),
            (data.get("murojaatRaqami", ""), {"bold": True}),
            (f"-raqamli murojaatingiz yuzasidan {tuman} “Inson” ijtimoiy xizmatlar "
             "markazi quyidagilar ma’lum qilinadi.", {}),
        ]),
        _p([(
            "Mazkur murojaatingiz bo‘yicha qo‘shimcha o‘rganish talab etilayotganligi "
            "sababli, O‘zbekiston Respublikasi “Jismoniy va yuridik shaxslarning murojaatlari "
            "to‘g‘risida”gi O‘RQ-445-son Qonunning 28-moddasiga muvofiq murojaatni "
            "ko‘rib chiqish muddati uzaytirilganligini bildiramiz.", {})]),
    ]
    if data.get("qoshimchaMalumot"):
        paras.append(_p([(data.get("qoshimchaMalumot"), {})]))
    return paras


def ariza_kiritilgan_paragraphs(data):
    paras = [
        _p(dg.NIZOM_FAMILY_REGISTRY_PARAGRAPH),
        _p(dg.ARIZA_KIRITILGAN_NIZOM_CLAUSE),
    ]
    ariza_year, ariza_day, ariza_month = dg.split_date(data.get("arizaVaqti"))
    paras.append(_p([
        ("Yuqoridagi qaror talablariga asosan, Sizning ", {}),
        (f"{ariza_year}-yil {ariza_day}-{ariza_month} kuni", {"bold": True}), (" ", {}),
        (f"{data.get('arizaMaqsadi', '')} olish uchun topshirgan arizangiz belgilangan tartibda ", {}),
        ("“Ijtimoiy himoya yagona reyestri” ", {"bold": True}), ("AT dasturida ", {}),
        (f"ID-{data.get('arizaID', '')}", {"bold": True}), (" bilan ro‘yxatga olinganligini ma’lum qilamiz.", {}),
    ]))
    paras.append(_p([(dg.SHIKOYAT_APPEAL_PARAGRAPH, {})]))
    return paras


def ariza_kiritilmagan_paragraphs(data):
    paras = [
        _p([(dg.ARIZA_KIRITILMAGAN_INTRO, {})]),
        _p([(dg.ARIZA_KIRITILMAGAN_FORM_INTRO, {})]),
        _p([(dg.ARIZA_KIRITILMAGAN_FORM_1, {})]),
        _p([(dg.ARIZA_KIRITILMAGAN_FORM_2, {})]),
        _p([(dg.ARIZA_KIRITILMAGAN_MONTHLY_LIMIT, {})]),
        _p([(dg.ARIZA_KIRITILMAGAN_CONCLUSION, {})]),
        _p([(dg.SHIKOYAT_APPEAL_PARAGRAPH, {})]),
    ]
    if data.get("qoshimchaMalumot"):
        paras.append(_p([(data.get("qoshimchaMalumot"), {})]))
    return paras


PARAGRAPH_BUILDERS = {
    "rad": rad_paragraphs,
    "tasdiqlandi": tasdiqlandi_paragraphs,
    "tayinlandi": tayinlandi_paragraphs,
    "muddat": muddat_paragraphs,
    "arizaKiritilgan": ariza_kiritilgan_paragraphs,
    "arizaKiritilmagan": ariza_kiritilmagan_paragraphs,
}

# Namunada faqat "arizaKiritilgan" imzo blokisiz (ataylab) — docx_generator.py bilan bir xil.
TEMPLATES_WITH_SIGNATURE = {"rad", "tasdiqlandi", "tayinlandi", "muddat", "arizaKiritilmagan"}


def build_preview(data):
    """(pochta_html, murojaat_html, [abzats_html...], has_signature) qaytaradi."""
    tuman = data.get("tuman") or ""
    mfy = data.get("mfyNomi") or ""
    street = data.get("street") or ""
    fio = data.get("fio") or ""
    pochta_html = _p([
        (tuman, {"bold": True}), (", ", {"bold": True}), (mfy, {"bold": True}), (" MFY, ", {"bold": True}),
        (street, {"bold": True}), (" ko'chasida yashovchi fuqaro ", {"bold": True}),
        (fio, {"bold": True}), ("ga", {"bold": True}),
    ])

    year, day, month = dg.split_date(data.get("murojaatVaqti"))
    murojaat_html = _p([
        ("Sizning ", {"italic": True}), (data.get("murojaatfrom", ""), {"italic": True}),
        (" orqali yo'llagan ", {"italic": True}), (f"{year}-yil {day}-{month}", {"italic": True}),
        ("dagi ", {"italic": True}), (data.get("murojaatRaqami", ""), {"italic": True}),
        (" raqamli murojaatingiz bo'yicha", {"italic": True}),
    ])

    template = data.get("template", "rad")
    builder = PARAGRAPH_BUILDERS.get(template, rad_paragraphs)
    paragraphs = builder(data)
    has_signature = template in TEMPLATES_WITH_SIGNATURE
    return pochta_html, murojaat_html, paragraphs, has_signature
