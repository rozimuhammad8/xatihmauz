# -*- coding: utf-8 -*-
"""Shablons/reeystr/*.docx — boshlang'ich shablonlarni yasaydi.

Bu fayl xat yaratmaydi, faqat SHABLON yasaydi: haqiqiy qiymatlar o'rniga
{fio}, {ariza_sanasi} kabi placeholder'lar yoziladi. Yasalgan .docx'ni keyin
Wordda xohlagancha tahrirlash mumkin — jumlani o'zgartirish, yangi abzats
qo'shish, qonun bandini yangilash. Ilova ishlaganda aynan shu fayl o'qiladi
(qarang: xat/docx_templates.py).

Ishga tushirish:
    python manage.py reestr_shablon

Sahifa o'lchami, shrift va abzats formatlari docx_generator.py dagi bir xil
yordamchilardan olinadi, huquqiy matnlar esa o'sha moduldagi konstantalardan
— ya'ni matn bitta joyda saqlanadi, bu yerda faqat qayta ishlatiladi.
"""
from . import docx_generator as dg
from .docx_generator import (
    add_murojaat_line,
    add_recipient_block,
    add_signature_block,
    body_paragraph,
    new_document,
)

# ------------------------------------------------------------
# PLACEHOLDER'LAR
# Shablonda shu belgilar turadi, ilova ularni haqiqiy qiymatga almashtiradi.
# ------------------------------------------------------------
P_MFY = "{mfy}"
P_KUCHA = "{kucha}"
P_FIO = "{fio}"
P_MUROJAAT_MANBASI = "{murojaat_manbasi}"
P_MUROJAAT_SANASI = "{murojaat_sanasi}"
P_MUROJAAT_RAQAMI = "{murojaat_raqami}"
P_ARIZA_MAQSADI = "{ariza_maqsadi}"
P_ARIZA_SANASI = "{ariza_sanasi}"
P_ARIZA_ID = "{ariza_id}"
P_QAYTA = "{qayta}"
P_TASDIQ_DAVRI = "{tasdiq_davri}"
P_TOLOV_DAVRI = "{tolov_davri}"
P_HISOB_RAQAMI = "{hisob_raqami}"
P_TOLOV_SUMMASI = "{tolov_summasi}"
P_TAYINLASH_QOSHIMCHA = "{tayinlash_qoshimcha}"
P_QOSHIMCHA_MALUMOT = "{qoshimcha_malumot}"

# Dinamik ro'yxatlar — ichida qalin qismlar bo'ladi, shuning uchun oddiy matn
# bilan emas, formatlangan segmentlar bilan almashtiriladi.
P_AVTO_ROYXATI = "{avto_royxati}"
P_UY_SONI = "{uy_soni}"
P_UY_ROYXATI = "{uy_royxati}"
P_RASMIY_MATNI = "{rasmiy_matni}"

# Shartli abzatslar. Abzats shu belgi bilan BOSHLANSA, sharti bajarilmagan
# taqdirda butun abzats hujjatdan o'chiriladi; bajarilsa belgi olib
# tashlanadi va abzats qoladi.
SHART_AVTO = "{?avtoRad}"
SHART_UY = "{?uyRad}"
SHART_RASMIY = "{?rasmiyRad}"
SHART_NORASMIY = "{?norasmiyRad}"
SHART_UYDA_EMAS = "{?uydaEmasRad}"
SHART_TOLOV = "{?tolov}"
SHART_TAYINLASH_QOSHIMCHA = "{?tayinlashQoshimcha}"
SHART_QOSHIMCHA_MALUMOT = "{?qoshimchaMalumot}"


def _sarlavha(doc):
    """Barcha xatlarda bir xil: qabul qiluvchi bloki + murojaat qatori."""
    add_recipient_block(doc, P_MFY, P_KUCHA, P_FIO)
    add_murojaat_line(
        doc,
        {"murojaatfrom": P_MUROJAAT_MANBASI, "murojaatRaqami": P_MUROJAAT_RAQAMI},
        sana_matni=P_MUROJAAT_SANASI,
    )


def qur_rad(doc):
    _sarlavha(doc)

    body_paragraph(doc, [(dg.INTRO_PARAGRAPH, {})])
    body_paragraph(doc, [
        ("Sizga ", {}),
        (P_MFY, {'bold': True}),
        (
            " MFY mahallada kompleks xizmat ko'rsatuvchi xodim, O‘zbekiston Respublikasi "
            "Prezidenti huzuridagi Ijtimoiy himoya milliy Agentligi Andijon viloyati boshqarmasi "
            "Andijon tumani “Inson” ijtimoiy xizmatlar markazi faoliyati, hamda xizmat "
            "turlarini yaqindan tanishtirildi.",
            {},
        ),
    ])
    body_paragraph(doc, dg.NIZOM_FAMILY_REGISTRY_PARAGRAPH)
    body_paragraph(doc, [
        ("Nizom talabalariga asosan sizning ", {}),
        (P_ARIZA_MAQSADI, {'bold': True}),
        (" uchun berilgan ", {}),
        (P_ARIZA_SANASI, {'bold': True}),
        (" kungi arizangiz va unga ilova qilingan ma’lumotlari «Ijtimoiy himoya yagona reyestri» axborot tizimiga ", {}),
        (f"{P_ARIZA_ID}-ID", {'bold': True}),
        (" raqam bilan kiritilgan va dastur tomonidan ", {}),
        (P_QAYTA, {}),
        ("o'rganilganda quydagilar sababli rad etildi:", {}),
    ])

    body_paragraph(doc, [
        (SHART_AVTO, {}),
        ("Sizning oilangiz foydalanuvida bo'lgan ", {}),
        (P_AVTO_ROYXATI, {}),
        (" mavjudligi sababli.", {}),
        dg.asos_segment("(Asos: VM 35-son qarori 4-bob v-band.)"),
    ])
    body_paragraph(doc, [
        (SHART_UY, {}),
        ("Sizning oilangiz nomiga rasmiylashtirilgan ", {}),
        (P_UY_SONI, {}),
        (" ta ko'chmas mulk (", {}),
        (P_UY_ROYXATI, {}),
        (") mavjudligi sababli.", {}),
        dg.asos_segment("(Asos: VM 35-son qarori 4-bob b-band.)"),
    ])
    body_paragraph(doc, [
        (SHART_RASMIY, {}),
        (P_RASMIY_MATNI, {}),
        dg.asos_segment("(Asos: VM 35-son qarori 4-bob a-band.)"),
    ])
    body_paragraph(doc, [
        (SHART_NORASMIY, {}),
        ("O'rganish natijasida ", {}),
        ("“mahalla yettiligi”", {'bold': True}),
        (
            " tomonidan o'tkazilgan so'rovnoma xulosasida norasmiy daromad manbaiyga ega "
            "ekanligngiz “Ijtimoiy himoya yagona reyestri” axborot tizimiga kiritilganda "
            "minimal iste'mol xarajatlaridan yuqori daromadingiz mavjudligi sababli.",
            {},
        ),
        dg.asos_segment("(Asos: VM 35-son qarori 4-bob a-band.)"),
    ])
    body_paragraph(doc, [
        (SHART_UYDA_EMAS, {}),
        (
            "Ijtimoiy xodim tomonidan yashash sharoitini o'rganish maqsadida amalga oshirilgan "
            "tashrif davomida sizni yashash manzilida mavjud bo'lmaganligi sababli ijtimoiy "
            "holatini o'rganish imkoni bo'lmadi. Natijada murojaat bo'yicha zarur o'rganish "
            "yakunlanmaganligi sababli ijobiy qaror qabul qilishning imkoni bo'lmagani.",
            {},
        ),
    ])

    body_paragraph(doc, [(dg.APPEAL_PARAGRAPH, {})])
    add_signature_block(doc, _imzo_placeholderlari())


def qur_tasdiqlandi(doc):
    _sarlavha(doc)

    body_paragraph(doc, [(dg.INTRO_PARAGRAPH, {})])
    body_paragraph(doc, dg.NIZOM_INTRO_SEGMENTS + [
        (" bilan tasdiqlangan Nizomning 33-bandiga muvofiq quyidagilar ma’lum qilinadi.", {}),
    ])
    body_paragraph(doc, dg.AGAR_PARAGRAPH_SEGMENTS)
    body_paragraph(doc, [
        (P_FIO, {'bold': True}),
        (" sizning ", {}),
        (P_ARIZA_SANASI, {'bold': True}),
        (" kunidan ", {}),
        (P_ARIZA_MAQSADI, {'bold': True}),
        (" tayinlash bo'yicha yuborgan arizangiz «Ijtimoiy himoya yagona reestri» axborot tizimiga ", {}),
        (f"{P_ARIZA_ID}-ID", {'bold': True}),
        (" raqam bilan kiritilgan va ", {}),
        (P_TASDIQ_DAVRI, {'bold': True}),
        (" oyidan ", {}),
        (P_ARIZA_MAQSADI, {'bold': True}),
        (" tayinlangan hamda Kambag'al oila toifasiga kiritilgan.", {}),
    ])
    body_paragraph(doc, [
        (SHART_TOLOV, {}),
        ("Sizga ", {}),
        (P_TOLOV_DAVRI, {}),
        (" uchun ", {}),
        (P_HISOB_RAQAMI, {}),
        (" hisob raqamiga ", {}),
        (P_TOLOV_SUMMASI, {}),
        (" so'm to'lab berilganligini ma’lum qilamiz.", {}),
    ])
    body_paragraph(doc, dg.BANK_PARAGRAPH_SEGMENTS)
    body_paragraph(doc, [(dg.APPEAL_PARAGRAPH, {})])
    add_signature_block(doc, _imzo_placeholderlari())


def qur_tayinlandi(doc):
    _sarlavha(doc)

    body_paragraph(doc, [(dg.INTRO_PARAGRAPH, {})])
    body_paragraph(doc, dg.NIZOM_INTRO_SEGMENTS + [
        (" bilan tasdiqlangan Nizomning 33-bandiga muvofiq quyidagilar ma’lum qilinadi.", {}),
    ])
    body_paragraph(doc, dg.AGAR_PARAGRAPH_SEGMENTS)
    body_paragraph(doc, [
        (P_FIO, {'bold': True}),
        (" sizning ", {}),
        (P_ARIZA_SANASI, {'bold': True}),
        (" kuni yuborgan ", {}),
        (P_ARIZA_MAQSADI, {'bold': True}),
        (" tayinlash bo'yicha yuborgan arizangiz «Ijtimoiy himoya yagona reestri» axborot tizimiga ", {}),
        (f"{P_ARIZA_ID}-ID", {'bold': True}),
        (" raqam bilan kiritilgan va ", {}),
        (P_ARIZA_MAQSADI, {'bold': True}),
        (" tayinlangan hamda Kambag'al oila toifasiga kiritilgan.", {}),
    ])
    body_paragraph(doc, [(SHART_TAYINLASH_QOSHIMCHA, {}), (P_TAYINLASH_QOSHIMCHA, {})])
    body_paragraph(doc, dg.BANK_PARAGRAPH_SEGMENTS)
    body_paragraph(doc, [(dg.APPEAL_PARAGRAPH, {})])
    add_signature_block(doc, _imzo_placeholderlari())


def qur_muddat(doc):
    _sarlavha(doc)

    body_paragraph(doc, [
        (
            "O‘zbekiston Respublikasi Prezidenti huzuridagi Ijtimoiy himoya milliy agentligi "
            "Andijon viloyati Andijon tuman “Inson” ijtimoiy xizmatlar markazi ",
            {},
        ),
        (P_MUROJAAT_RAQAMI, {'bold': True}),
        (
            "-raqamli murojaatingiz yuzasidan Andijon tuman “Inson” ijtimoiy xizmatlar "
            "markazi quyidagilar ma’lum qilinadi.",
            {},
        ),
    ])
    body_paragraph(doc, [(
        "Mazkur murojaatingiz bo‘yicha qo‘shimcha o‘rganish talab etilayotganligi "
        "sababli, O‘zbekiston Respublikasi “Jismoniy va yuridik shaxslarning murojaatlari "
        "to‘g‘risida”gi O‘RQ-445-son Qonunning 28-moddasiga muvofiq murojaatni "
        "ko‘rib chiqish muddati uzaytirilganligini bildiramiz.",
        {},
    )])
    body_paragraph(doc, [(SHART_QOSHIMCHA_MALUMOT, {}), (P_QOSHIMCHA_MALUMOT, {})])
    add_signature_block(doc, _imzo_placeholderlari())


def qur_ariza_kiritilgan(doc):
    _sarlavha(doc)

    body_paragraph(doc, dg.NIZOM_FAMILY_REGISTRY_PARAGRAPH)
    body_paragraph(doc, dg.ARIZA_KIRITILGAN_NIZOM_CLAUSE)
    body_paragraph(doc, [
        ("Yuqoridagi qaror talablariga asosan, Sizning ", {}),
        (f"{P_ARIZA_SANASI} kuni", {'bold': True}),
        (" ", {}),
        (f"{P_ARIZA_MAQSADI} olish uchun topshirgan arizangiz belgilangan tartibda ", {}),
        ("“Ijtimoiy himoya yagona reyestri” ", {'bold': True}),
        ("AT dasturida ", {}),
        (f"ID-{P_ARIZA_ID}", {'bold': True}),
        (" bilan ro‘yxatga olinganligini ma’lum qilamiz.", {}),
    ])
    body_paragraph(doc, [(dg.SHIKOYAT_APPEAL_PARAGRAPH, {})])
    # Namunada imzo bloki yo'q (ataylab) — docx_generator.build_ariza_kiritilgan
    # bilan bir xil.


def _imzo_placeholderlari():
    return {
        "tashkilotNomi": "{tashkilot_nomi}",
        "tashkilotRahbar": "{rahbar}",
        "ijrochi": "{ijrochi}",
    }


# Shablon kodi -> (fayl nomi, quruvchi funksiya)
SHABLONLAR = {
    "rad": ("rad.docx", qur_rad),
    "tasdiqlandi": ("tasdiqlandi.docx", qur_tasdiqlandi),
    "tayinlandi": ("tayinlandi.docx", qur_tayinlandi),
    "muddat": ("muddat.docx", qur_muddat),
    "arizaKiritilgan": ("ariza_kiritilgan.docx", qur_ariza_kiritilgan),
}


def shablon_yasash(kod, yol):
    """Bitta shablonni yasab, `yol` ga saqlaydi."""
    _fayl, quruvchi = SHABLONLAR[kod]
    doc = new_document()
    quruvchi(doc)
    doc.save(str(yol))
    return yol
