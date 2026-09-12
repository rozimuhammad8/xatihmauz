# ============================================================
# WORD (.docx) XAT GENERATORI
# ------------------------------------------------------------
# "exmple/" papkasidagi rasmiy shablonlar (AVTO_NORASMIY,
# Tasdiqlandi SHABLON, Tayinlandi SHABLON, Muddat so'rash SHABLON,
# RASMIY/NORASMIY DAROMAD, Uyda Bolmagan va h.k.) asosida, har bir
# xat yozuvi (letter) uchun bir xil dizayn/formatda to'ldirilgan
# rasmiy Word hujjati yaratadi.
# ============================================================

import io
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.shared import Emu, Pt

# ------------------------------------------------------------
# NAMUNADAN OLINGAN O'LCHAMLAR (exmple/AVTO_NORASMIY.docx)
# ------------------------------------------------------------
PAGE_WIDTH = Emu(7560310)
PAGE_HEIGHT = Emu(10692130)
MARGIN_TOP = Emu(540385)
MARGIN_BOTTOM = Emu(720090)
MARGIN_LEFT = Emu(720090)
MARGIN_RIGHT = Emu(719455)

RECIPIENT_LEFT_INDENT = Emu(3240405)
MUROJAAT_RIGHT_INDENT = Emu(2879090)
BODY_FIRST_LINE_INDENT = Emu(450215)
SIGNATURE_TAB_POSITION = Emu(5943600)  # ~6.5 sm dan keyin, imzo joyiga mos

FONT_NAME = 'Times New Roman'

MONTHS = [
    "yanvar", "fevral", "mart", "aprel", "may", "iyun",
    "iyul", "avgust", "sentyabr", "oktyabr", "noyabr", "dekabr",
]


# ------------------------------------------------------------
# YORDAMCHI FUNKSIYALAR
# ------------------------------------------------------------
def split_date(value):
    """'YYYY-MM-DD' ni (yil, kun, oy nomi) ga ajratadi.

    Kun oldidagi nol olib tashlanadi: "2026-06-03" -> ("2026", "3", "iyun").
    Ilgari "03-iyun" deb yozilar, "Bosh ijtimoiy" arizalari esa (format_sana
    d.day butun sonini ishlatgani uchun) "3-iyun" deb yozar edi — bitta markaz
    ikki xil sana formatida rasmiy xat chiqarardi.
    """
    if not value:
        return '', '', ''
    parts = value.split('-')
    year = parts[0] if len(parts) > 0 else ''
    day = parts[2] if len(parts) > 2 else ''
    if day.isdigit():
        day = str(int(day))
    month = ''
    if len(parts) > 1 and parts[1].isdigit():
        idx = int(parts[1]) - 1
        if 0 <= idx < len(MONTHS):
            month = MONTHS[idx]
    return year, day, month


def parse_year_month(value):
    """'YYYY, OyNomi' (masalan '2026, Mart') formatidagi erkin matnni (yil, oy) ga ajratadi.
    tasdiqSanasi/tolovSanasi maydonlari index.html da sana emas, shu formatdagi matn sifatida
    kiritiladi (split_date() bilan aralashtirib bo'lmaydi)."""
    if not value:
        return '', ''
    parts = value.split(',')
    year = parts[0].strip() if len(parts) > 0 else ''
    month = parts[1].strip() if len(parts) > 1 else ''
    if not month and year:
        # vergulsiz "2026 mart" kabi kiritilgan bo'lsa ham urinib ko'ramiz
        bits = year.split()
        if len(bits) >= 2:
            year, month = bits[0], ' '.join(bits[1:])
    # oy nomlari dastur bo'ylab har doim kichik harf bilan yoziladi (masalan "16-iyul")
    return year, month.lower()


def to_title_case(text):
    """Har bir so'zning bosh harfini katta qiladi.

    "qizi"/"o'g'li" kabi F.I.O qo'shimchalari kichik qoladi — mantiq
    core.text_utils da, ikkala tizimda bir xil bo'lishi uchun.
    """
    if not text:
        return ''
    from core.text_utils import smart_title_case
    return smart_title_case(text)


def to_sentence_case(text):
    """Faqat matndagi birinchi harfni katta qiladi, qolganini kichik (tashkilot nomlari uchun).
    Qo'shtirnoq kabi harf bo'lmagan belgilar bilan boshlansa ham, birinchi harfni topib katta qiladi."""
    if not text:
        return ''
    text = text.lower()
    m = re.search(r'[a-zʻʼ]', text)
    if not m:
        return text
    i = m.start()
    return text[:i] + text[i].upper() + text[i + 1:]


def format_car_number(number):
    if not number:
        return ''
    m = re.match(r'^(\d+)([A-Za-z])(\d+)([A-Za-z]+)$', number)
    if not m:
        return number
    return f"{m.group(1)} {m.group(2)} {m.group(3)} {m.group(4)}"


def _parse_number(value):
    """Foydalanuvchi kiritishi mumkin bo'lgan '687 810.00', '687,810.00', '476720,00',
    '1.450.543,00' kabi turli formatdagi sonlarni ishonchli tarzda floatga aylantiradi.
    Oxirgi vergul/nuqtadan keyin 1-2 ta raqam kelsa, o'sha kasr ajratgichi deb topiladi
    (masalan '476720,00' -> 476720.00), aks holda barcha vergul/nuqtalar minglik
    ajratgichi sifatida olib tashlanadi (masalan '1,234,567' -> 1234567)."""
    if value is None or value == '':
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(' ', '').replace('\xa0', '')
    if not text:
        return 0.0
    last_sep = max(text.rfind(','), text.rfind('.'))
    if last_sep == -1:
        cleaned = text
    else:
        frac_part = text[last_sep + 1:]
        int_part = text[:last_sep]
        if frac_part.isdigit() and 1 <= len(frac_part) <= 2:
            cleaned = re.sub(r'[.,]', '', int_part) + '.' + frac_part
        else:
            cleaned = re.sub(r'[.,]', '', text)
    try:
        return float(cleaned)
    except (TypeError, ValueError):
        return 0.0


def format_amount(value):
    amount = _parse_number(value)
    text = f"{amount:,.0f}"
    return text.replace(',', ' ')


def format_money(value):
    """Pul summasi uchun: 2 xonali kasr va probel bilan ajratilgan minglik ("687 810.00")."""
    amount = _parse_number(value)
    text = f"{amount:,.2f}"
    return text.replace(',', ' ')


def car_segments(items):
    """Avtomobil(lar) haqidagi matnni (matn, format) segmentlar ro'yxati sifatida qaytaradi."""
    if not items:
        return []
    segs = []
    if len(items) == 1:
        it = items[0]
        segs += [
            (f"{it.get('avtoYil', '')}-yilda ishlab chiqarilgan davlat raqami ", {}),
            (format_car_number(it.get('avtoRaqam', '')), {'bold': True}),
            (" bo'lgan ", {}),
            (f"“{it.get('avtoModel', '')}”", {'bold': True}),
            (" rusumli avtomashina", {}),
        ]
    else:
        for i, it in enumerate(items):
            prefix = '' if i == 0 else ' va '
            segs += [
                (f"{prefix}{it.get('avtoYil', '')}-yilda ishlab chiqarilgan davlat raqami ", {}),
                (format_car_number(it.get('avtoRaqam', '')), {'bold': True}),
                (" bo'lgan ", {}),
                (f"“{it.get('avtoModel', '')}”", {'bold': True}),
                (" rusumli", {}),
            ]
        segs.append((" avtomashinalar", {}))
    return segs


def uy_segments(items):
    if not items:
        return []
    segs = []
    if len(items) == 1:
        it = items[0]
        segs.append((
            f"manzili {it.get('uyManzil', '')} kadastr raqami {it.get('uyKadastr', '')} bo'lgan",
            {},
        ))
    else:
        for i, it in enumerate(items):
            prefix = 'M' if i == 0 else ' va m'
            segs.append((
                f"{prefix}anzili {it.get('uyManzil', '')} kadastr raqami {it.get('uyKadastr', '')} bo'lgan",
                {},
            ))
        segs.append((" xonadonlar", {}))
    return segs


def income_text(items):
    if not items:
        return ''
    owners, orgs, incomes = [], [], []
    for it in items:
        owner = to_title_case(it.get('egasi', ''))
        if owner and owner not in owners:
            owners.append(owner)
        org = to_sentence_case(it.get('tashkilot', ''))
        if org and org not in orgs:
            orgs.append(org)
    for it in items:
        parts = (it.get('davri') or '').split(',')
        month = to_title_case(parts[0].strip()) if len(parts) > 0 else ''
        year = parts[1].strip() if len(parts) > 1 else ''
        amount = format_amount(it.get('miqdori'))
        incomes.append(f"{year}-yil {month} oyi uchun {amount} so'm")
    # Jumla ATAYLAB nuqtasiz tugaydi: ortidan rad_xulosa_segments() ning
    # " sababli sizga ... tayinlash rad etildi." qismi ulanadi.
    return (
        ' va '.join(orgs) + ' tomonidan ' + ' va '.join(owners) + "ga " +
        ', '.join(incomes) +
        " oylik daromad hisoblangan va bu minimal iste'mol xarajatlaridan yuqori ekanligi"
    )


def rad_xulosa_segments(data):
    """Har bir rad sababining oxiriga qo'shiladigan umumiy xulosa.

    Sabab jumlasi "... sababli" bilan tugaydi, bu funksiya esa
    "sizga <dastur nomi> tayinlash rad etildi." qismini qo'shadi — natijada
    har bir band nima uchun va nima rad etilganini o'zi to'liq aytadi.
    """
    return [
        (" sizga ", {}),
        (data.get('arizaMaqsadi', ''), {'bold': True}),
        (" tayinlash rad etildi.", {}),
    ]


def asos_segment(text):
    """'(Asos: ...)' matnini oldingi jumla bilan bitta qatorda, qalin qilib qo'shadi."""
    return (' ' + text, {'bold': True})


# ------------------------------------------------------------
# HUJJAT QURISH BLOKLARI
# ------------------------------------------------------------
def new_document():
    doc = Document()
    normal = doc.styles['Normal']
    normal.font.name = FONT_NAME
    normal.font.size = Pt(14)

    section = doc.sections[0]
    section.page_width = PAGE_WIDTH
    section.page_height = PAGE_HEIGHT
    section.top_margin = MARGIN_TOP
    section.bottom_margin = MARGIN_BOTTOM
    section.left_margin = MARGIN_LEFT
    section.right_margin = MARGIN_RIGHT
    return doc


def add_run(paragraph, text, bold=False, italic=False, size=14, color=None):
    run = paragraph.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    run.font.name = FONT_NAME
    if color:
        run.font.color.rgb = color
    return run


def add_paragraph(doc, segments, align=None, first_line_indent=None,
                   left_indent=None, right_indent=None, space_after=0,
                   line_spacing=1.0):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    if align is not None:
        p.alignment = align
    if first_line_indent is not None:
        pf.first_line_indent = first_line_indent
    if left_indent is not None:
        pf.left_indent = left_indent
    if right_indent is not None:
        pf.right_indent = right_indent
    pf.space_before = Pt(0)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line_spacing
    for seg in segments:
        text, kwargs = seg if isinstance(seg, tuple) else (seg, {})
        add_run(p, text, **kwargs)
    return p


def body_paragraph(doc, segments):
    """Asosiy matn: 14pt, ikki tomonga tekislangan, qizil chiziq bilan boshlanadi, bo'shliqsiz."""
    return add_paragraph(
        doc, segments,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        first_line_indent=BODY_FIRST_LINE_INDENT,
        space_after=2,
    )


def add_recipient_block(doc, mfy, street, fio):
    add_paragraph(
        doc,
        [
            ("Andijon tumani, ", {'bold': True}),
            (mfy or '', {'bold': True}),
            (" MFY, ", {'bold': True}),
            (street or '', {'bold': True}),
            (" ko'chasida yashovchi fuqaro ", {'bold': True}),
            (fio or '', {'bold': True}),
            ("ga", {'bold': True}),
        ],
        left_indent=RECIPIENT_LEFT_INDENT,
    )


def add_murojaat_line(doc, data, sana_matni=None):
    """`sana_matni` berilmasa, sana data['murojaatVaqti'] dan hosil qilinadi.
    Shablon yasashda (shablon_qurish.py) u yerga "{murojaat_sanasi}"
    placeholderi uzatiladi."""
    if sana_matni is None:
        year, day, month = split_date(data.get('murojaatVaqti'))
        sana_matni = f"{year}-yil {day}-{month}"
    add_paragraph(
        doc,
        [
            ("Sizning ", {'italic': True, 'size': 12}),
            (data.get('murojaatfrom', ''), {'italic': True, 'size': 12}),
            (" orqali yo'llagan ", {'italic': True, 'size': 12}),
            (sana_matni, {'italic': True, 'size': 12}),
            ("dagi ", {'italic': True, 'size': 12}),
            (data.get('murojaatRaqami', ''), {'italic': True, 'size': 12}),
            (" raqamli murojaatingiz bo'yicha", {'italic': True, 'size': 12}),
        ],
        right_indent=MUROJAAT_RIGHT_INDENT,
        space_after=4,
    )
    # namunadagi bo'sh ajratuvchi qator
    add_paragraph(doc, [], align=WD_ALIGN_PARAGRAPH.JUSTIFY)


def add_signature_block(doc, data):
    tashkilot_nomi = data.get('tashkilotNomi') or 'Tashkilot'
    tashkilot_rahbar = data.get('tashkilotRahbar') or ''
    ijrochi = data.get('ijrochi') or ''

    add_paragraph(doc, [], space_after=4)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.tab_stops.add_tab_stop(SIGNATURE_TAB_POSITION, WD_TAB_ALIGNMENT.RIGHT)
    add_run(p, f"{tashkilot_nomi} direktori:", bold=True)
    p.add_run('\t')
    add_run(p, tashkilot_rahbar, bold=True)
    add_paragraph(doc, [], space_after=4)
    add_paragraph(doc, [(f"Ijrochi: {ijrochi}", {'bold': True, 'italic': True, 'size': 9})])


INTRO_PARAGRAPH = (
    "O‘zbekiston Respublikasi Prezidenti huzuridagi Ijtimoiy himoya milliy Agentligi "
    "Andijon viloyati boshqarmasi Andijon tumani “Inson” ijtimoiy xizmatlar markazi "
    "tomonidan murojaatingiz o‘rganib chiqildi."
)

APPEAL_PARAGRAPH = (
    "Murojaatingiz yuzasidan qabul qilingan qarordan norozi bo'lsangiz O‘zbekiston "
    "Respublikasining “Jismoniy va yuridik shaxslarning murojaatlari to‘g‘risida”gi "
    "Qonuniga ko‘ra yuqori turuvchi tashkilotga shikoyat qilishingiz mumkinligi haqida "
    "ogohlantirib o‘taman."
)

# "Murojaatni ko'rib chiqish jarayonida sizga ..." abzasining umumiy boshlanishi.
# Rasmiy shablonlarda ushbu katta iqtibosning FAQAT "35-son" qismi qalin bo'ladi.
NIZOM_CITATION_LEAD = (
    "O‘zbekiston Respublikasi Vazirlar Mahkamasining 2026-yil 29-yanvardagi "
    "“Ijtimoiy reestrga kiritilgan oilalarni qo‘llab-quvvatlash tizimini "
    "takomillashtirishning qo‘shimcha chora-tadbirlari to‘g‘risida”gi "
)

NIZOM_INTRO_SEGMENTS = [
    ("Murojaatni ko'rib chiqish jarayonida sizga ", {}),
    (NIZOM_CITATION_LEAD, {}),
    ("35-son", {'bold': True}),
    (" qarori", {}),
]

# Shared by "rad" and "arizaKiritilgan" — both cite the same Nizom clause
# explaining that the benefit/assistance is only assigned to families
# already entered into the Ijtimoiy reestr.
NIZOM_FAMILY_REGISTRY_PARAGRAPH = NIZOM_INTRO_SEGMENTS + [
    ("ga asosan, ", {}),
    ("bolalar nafaqasi va moddiy yordamlar faqat Ijtimoiy reestrga kiritilgan oilalarga tayinlanishi", {'bold': True}),
    (" tushuntirildi.", {}),
]

AGAR_PARAGRAPH_SEGMENTS = [
    (
        "Agar, oila a’zolariga to‘g‘ri keladigan o‘rtacha oylik daromad minimal "
        "iste’mol xarajatlaridan yuqori bo‘lsa, ortiqcha ko‘chmas mulk yoki daromad "
        "keltiruvchi noturar ob’ektlar mavjud bo‘lsa, belgilangan muddatdan yangi transport "
        "vositalari yoki bir nechta texnika vositalari bor bo‘lsa, shuningdek bank omonatlari "
        "yoki qimmatli qog‘ozlari belgilangan miqdordan ortiq bo‘lsa yoxud qonunchilikda "
        "nazarda tutilgan boshqa holatlar ",
        {},
    ),
    (
        "(jumladan, chet elga ko‘chib ketish, jinoyat uchun jazo o‘tash, internat "
        "muassasalariga joylashish, murojaat talablariga rioya qilmaslik yoki ariza "
        "beruvchining vafoti)",
        {'italic': True},
    ),
    (
        " mavjud bo‘lganda kam ta’minlangan oilalarga bolalar nafaqasi yoki moddiy "
        "yordam tayinlash rad etilishi yoki to’xtatilishi belgilangan.",
        {},
    ),
]

BANK_PARAGRAPH_SEGMENTS = [
    (
        "Bolalar nafaqasi yoki moddiy yordam to‘lovi Xalq bankining filiallari tomonidan "
        "belgilangan tartibda to‘lov oyining 4-sanasidan 27-sanasiga qadar amalga oshiriladi.",
        {'bold': True},
    ),
]


# ------------------------------------------------------------
# 1) RAD ETISH XATI
# ------------------------------------------------------------
def build_rad(doc, data):
    rad = data.get('radSabablari') or {}

    add_recipient_block(doc, data.get('mfyNomi'), data.get('street'), data.get('fio'))
    add_murojaat_line(doc, data)

    body_paragraph(doc, [(INTRO_PARAGRAPH, {})])
    body_paragraph(doc, [
        ("Sizga ", {}),
        (data.get('mfyNomi', ''), {'bold': True}),
        (
            " MFY mahallada kompleks xizmat ko'rsatuvchi xodim, O‘zbekiston Respublikasi "
            "Prezidenti huzuridagi Ijtimoiy himoya milliy Agentligi Andijon viloyati boshqarmasi "
            "Andijon tumani “Inson” ijtimoiy xizmatlar markazi faoliyati, hamda xizmat "
            "turlarini yaqindan tanishtirildi.",
            {},
        ),
    ])
    body_paragraph(doc, NIZOM_FAMILY_REGISTRY_PARAGRAPH)

    ariza_year, ariza_day, ariza_month = split_date(data.get('arizaVaqti'))
    qayta = 'qayta ' if data.get('isQayta') else ''
    body_paragraph(doc, [
        ("Nizom talabalariga asosan sizning ", {}),
        (data.get('arizaMaqsadi', ''), {'bold': True}),
        (" uchun berilgan ", {}),
        (f"{ariza_year}-yil {ariza_day}-{ariza_month}", {'bold': True}),
        (" kungi arizangiz va unga ilova qilingan ma’lumotlari «Ijtimoiy himoya yagona reyestri» axborot tizimiga ", {}),
        (f"{data.get('arizaID', '')}-ID", {'bold': True}),
        (" raqam bilan kiritilgan va dastur tomonidan ", {}),
        (qayta, {}),
        ("o'rganilganda quydagilar sababli rad etildi:", {}),
    ])

    if rad.get('avtoRad'):
        body_paragraph(doc, [("Sizning oilangiz foydalanuvida bo'lgan ", {})] +
                       car_segments(rad['avtoRad']) + [(" mavjudligi sababli", {})] +
                       rad_xulosa_segments(data) +
                       [asos_segment("(Asos: VM 35-son qarori 4-bob v-band.)")])

    if rad.get('uyRad'):
        body_paragraph(
            doc,
            [(f"Sizning oilangiz nomiga rasmiylashtirilgan {len(rad['uyRad'])} ta ko'chmas mulk (", {})] +
            uy_segments(rad['uyRad']) + [(") mavjudligi sababli", {})] +
            rad_xulosa_segments(data) +
            [asos_segment("(Asos: VM 35-son qarori 4-bob b-band.)")],
        )

    if rad.get('rasmiyRad'):
        body_paragraph(doc, [
            (income_text(rad['rasmiyRad']), {}),
            (" sababli", {}),
        ] + rad_xulosa_segments(data) + [
            asos_segment("(Asos: VM 35-son qarori 4-bob a-band.)"),
        ])

    if rad.get('norasmiyRad'):
        body_paragraph(doc, [
            ("O'rganish natijasida ", {}),
            ("“mahalla yettiligi”", {'bold': True}),
            (
                " tomonidan o'tkazilgan so'rovnoma xulosasida norasmiy daromad manbaiyga ega "
                "ekanligngiz “Ijtimoiy himoya yagona reyestri” axborot tizimiga kiritilganda "
                "minimal iste'mol xarajatlaridan yuqori daromadingiz mavjudligi sababli",
                {},
            ),
        ] + rad_xulosa_segments(data) + [
            asos_segment("(Asos: VM 35-son qarori 4-bob a-band.)"),
        ])

    if rad.get('uydaEmasRad'):
        body_paragraph(doc, [(
            "Ijtimoiy xodim tomonidan yashash sharoitini o'rganish maqsadida amalga oshirilgan "
            "tashrif davomida sizni yashash manzilida mavjud bo'lmaganligi sababli ijtimoiy "
            "holatini o'rganish imkoni bo'lmadi. Natijada murojaat bo'yicha zarur o'rganish "
            "yakunlanmaganligi sababli",
            {},
        )] + rad_xulosa_segments(data))

    body_paragraph(doc, [(APPEAL_PARAGRAPH, {})])
    add_signature_block(doc, data)


# ------------------------------------------------------------
# 2) TASDIQLASH XATI (template == 'tasdiqlandi')
# ------------------------------------------------------------
def build_tasdiqlandi(doc, data):
    tasdiq = data.get('tasdiqMalumotlari') or {}

    add_recipient_block(doc, data.get('mfyNomi'), data.get('street'), data.get('fio'))
    add_murojaat_line(doc, data)

    body_paragraph(doc, [(INTRO_PARAGRAPH, {})])
    body_paragraph(doc, NIZOM_INTRO_SEGMENTS + [
        (" bilan tasdiqlangan Nizomning 33-bandiga muvofiq quyidagilar ma’lum qilinadi.", {}),
    ])
    body_paragraph(doc, AGAR_PARAGRAPH_SEGMENTS)

    ariza_year, ariza_day, ariza_month = split_date(data.get('arizaVaqti'))
    tasdiq_year, tasdiq_month = parse_year_month(tasdiq.get('tasdiqSanasi'))
    tolov_year, tolov_month = parse_year_month(tasdiq.get('tolovSanasi'))
    davr_oy = f"{tasdiq_year}-yil {tasdiq_month}" if tasdiq_month else f"{ariza_year}-yil {ariza_month}"

    body_paragraph(doc, [
        (data.get('fio', ''), {'bold': True}),
        (" sizning ", {}),
        (f"{ariza_year}-yil {ariza_day}-{ariza_month}", {'bold': True}),
        (" kunidan ", {}),
        (data.get('arizaMaqsadi', ''), {'bold': True}),
        (" tayinlash bo'yicha yuborgan arizangiz «Ijtimoiy himoya yagona reestri» axborot tizimiga ", {}),
        (f"{data.get('arizaID', '')}-ID", {'bold': True}),
        (" raqam bilan kiritilgan va ", {}),
        (f"{davr_oy}", {'bold': True}),
        (" oyidan ", {}),
        (data.get('arizaMaqsadi', ''), {'bold': True}),
        (" tayinlangan hamda Kambag'al oila toifasiga kiritilgan.", {}),
    ])

    if tasdiq.get('tolovSum') or tasdiq.get('hisobRaqami'):
        davr_tolov = f"{tolov_year}-yil {tolov_month} oyi" if tolov_month else (f"{davr_oy} oyi" if davr_oy else "tegishli davr")
        body_paragraph(doc, [
            ("Sizga ", {}),
            (davr_tolov, {}),
            (" uchun ", {}),
            (tasdiq.get('hisobRaqami', ''), {}),
            (" hisob raqamiga ", {}),
            (f"{format_money(tasdiq.get('tolovSum'))}", {}),
            (" so'm to'lab berilganligini ma’lum qilamiz.", {}),
        ])

    body_paragraph(doc, BANK_PARAGRAPH_SEGMENTS)
    body_paragraph(doc, [(APPEAL_PARAGRAPH, {})])
    add_signature_block(doc, data)


# ------------------------------------------------------------
# 3) TAYINLASH XATI (template == 'tayinlandi')
# ------------------------------------------------------------
def build_tayinlandi(doc, data):
    add_recipient_block(doc, data.get('mfyNomi'), data.get('street'), data.get('fio'))
    add_murojaat_line(doc, data)

    body_paragraph(doc, [(INTRO_PARAGRAPH, {})])
    body_paragraph(doc, NIZOM_INTRO_SEGMENTS + [
        (" bilan tasdiqlangan Nizomning 33-bandiga muvofiq quyidagilar ma’lum qilinadi.", {}),
    ])
    body_paragraph(doc, AGAR_PARAGRAPH_SEGMENTS)

    ariza_year, ariza_day, ariza_month = split_date(data.get('arizaVaqti'))
    body_paragraph(doc, [
        (data.get('fio', ''), {'bold': True}),
        (" sizning ", {}),
        (f"{ariza_year}-yil {ariza_day}-{ariza_month}", {'bold': True}),
        (" kuni yuborgan ", {}),
        (data.get('arizaMaqsadi', ''), {'bold': True}),
        (" tayinlash bo'yicha yuborgan arizangiz «Ijtimoiy himoya yagona reestri» axborot tizimiga ", {}),
        (f"{data.get('arizaID', '')}-ID", {'bold': True}),
        (" raqam bilan kiritilgan va ", {}),
        (data.get('arizaMaqsadi', ''), {'bold': True}),
        (" tayinlangan hamda Kambag'al oila toifasiga kiritilgan.", {}),
    ])

    if data.get('tayinlashQoshimcha'):
        body_paragraph(doc, [(data.get('tayinlashQoshimcha'), {})])

    body_paragraph(doc, BANK_PARAGRAPH_SEGMENTS)
    body_paragraph(doc, [(APPEAL_PARAGRAPH, {})])
    add_signature_block(doc, data)


# ------------------------------------------------------------
# 4) MUDDAT SO'RASH XATI (template == 'muddat')
# ------------------------------------------------------------
def build_muddat(doc, data):
    add_recipient_block(doc, data.get('mfyNomi'), data.get('street'), data.get('fio'))
    add_murojaat_line(doc, data)

    body_paragraph(doc, [
        (
            "O‘zbekiston Respublikasi Prezidenti huzuridagi Ijtimoiy himoya milliy agentligi "
            "Andijon viloyati Andijon tuman “Inson” ijtimoiy xizmatlar markazi ",
            {},
        ),
        (data.get('murojaatRaqami', ''), {'bold': True}),
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

    if data.get('qoshimchaMalumot'):
        body_paragraph(doc, [(data.get('qoshimchaMalumot'), {})])

    add_signature_block(doc, data)


# ------------------------------------------------------------
# 5) ARIZA KIRITILMAGAN XATI (template == 'arizaKiritilmagan')
# Butunlay statik matn (exmple/"Ariza kiritlmaganga namuna.docx" asosida) —
# faqat qabul qiluvchi va murojaat bloklari ma'lumotga bog'liq, xat matnining
# o'zida "ariza"ga oid hech narsa yo'q (chunki ariza umuman kiritilmagan).
# ------------------------------------------------------------
ARIZA_KIRITILMAGAN_INTRO = (
    "Murojaatingiz, Andijon tumani “Inson” ijtimoiy xizmatlar markazi xodimlari "
    "tomonidan o‘rganildi. O‘rganish davomida, Sizga O‘zbekiston Respublikasi "
    "Vazirlar Mahkamasining 2026 yil 29 yanvardagi “Ijtimoiy reestrni yuritish tartibi "
    "to‘g‘risida”gi 35-son qarori bilan tasdiqlangan Nizomning 1-ilova 2-bobida "
    "Oilani Reyestrga kiritish to‘g‘risidagi murojaatni ko‘rib chiqish tartibi "
    "belgilanganligi tushuntirildi."
)

ARIZA_KIRITILMAGAN_FORM_INTRO = (
    "Ushbu nizomning 5-bandiga asosan Ariza beruvchi oilasini Reyestrga kiritish "
    "uchun vakolatli organga quyidagi shakllarda murojaat qiladi:"
)

ARIZA_KIRITILMAGAN_FORM_1 = (
    "davlat xizmatlari markazi yoki vakolatli organga borgan holda yoki yashash "
    "manzili bo‘yicha mahallaga biriktirilgan ijtimoiy xodim orqali;"
)

ARIZA_KIRITILMAGAN_FORM_2 = (
    "“YAMIH” AT, Yagona interaktiv davlat xizmatlari portali (keyingi o‘rinlarda "
    "— YIDXP) yoki “Ijtimoiy karta” mobil ilovasi orqali mustaqil ravishda."
)

ARIZA_KIRITILMAGAN_MONTHLY_LIMIT = (
    "Har bir oila tomonidan Reyestrga kiritish uchun ariza topshirish bir oyda bir "
    "marta amalga oshirishligi belgilangan."
)

ARIZA_KIRITILMAGAN_CONCLUSION = (
    "Yuqoridagilardan kelib chiqqan holda Siz kam ta’minlangan oilalarga bolalar "
    "nafaqasi yoki moddiy yordam tayinlashni so‘rab murojaat qilmaganligingizni "
    "ma’lum qiladi."
)

# APPEAL_PARAGRAPH bilan bir xil ma'noda, lekin so'zma-so'z farqli variant —
# "arizaKiritilmagan" va "arizaKiritilgan" namunalarida aynan shu ibora
# ishlatilgan, shu sabab ikkalasida ham qayta ishlatiladi.
SHIKOYAT_APPEAL_PARAGRAPH = (
    "Murojaatingiz yuzasidan qabul qilingan qarordan qoniqish hosil qilmagan "
    "taqdiringizda O‘zbekiston Respublikasining “Jismoniy va yuridik shaxslarning "
    "murojaatlari to‘g‘risida”gi Qonuniga ko‘ra yuqori turuvchi tashkilotga shikoyat "
    "qilishingiz mumkinligi haqida ogohlantirib o‘taman."
)


def build_ariza_kiritilmagan(doc, data):
    add_recipient_block(doc, data.get('mfyNomi'), data.get('street'), data.get('fio'))
    add_murojaat_line(doc, data)

    body_paragraph(doc, [(ARIZA_KIRITILMAGAN_INTRO, {})])
    body_paragraph(doc, [(ARIZA_KIRITILMAGAN_FORM_INTRO, {})])
    body_paragraph(doc, [(ARIZA_KIRITILMAGAN_FORM_1, {})])
    body_paragraph(doc, [(ARIZA_KIRITILMAGAN_FORM_2, {})])
    body_paragraph(doc, [(ARIZA_KIRITILMAGAN_MONTHLY_LIMIT, {})])
    body_paragraph(doc, [(ARIZA_KIRITILMAGAN_CONCLUSION, {})])
    body_paragraph(doc, [(SHIKOYAT_APPEAL_PARAGRAPH, {})])

    add_signature_block(doc, data)


# ------------------------------------------------------------
# 6) ARIZA KIRITILGAN XATI (template == 'arizaKiritilgan')
# "Ariza kiritilmagan"ning aksi — ariza haqiqatan ham "Ijtimoiy himoya
# yagona reyestri"ga qabul qilib ro'yxatga olinganini tasdiqlaydi
# (exmple/"Ariza Kiritilgan.docx" asosida). Namunada boshqa shablonlardan
# farqli o'laroq imzo bloki yo'q — ataylab shunday qoldirilgan.
# ------------------------------------------------------------
ARIZA_KIRITILGAN_NIZOM_CLAUSE = [
    ("Shuningdek, mazkur qarorning ", {}),
    ("2-bob 7-bandi", {'bold': True}),
    ("ga ko‘ra, ", {}),
    (
        "ariza beruvchi davlat xizmatidan foydalanishdan uning har qanday bosqichida "
        "bosh tortish huquqiga ega",
        {'italic': True},
    ),
    (". ", {}),
    ("Bundan tashqari, ", {}),
    ("11-band", {'bold': True}),
    ("ga muvofiq, ", {}),
    (
        "kam ta’minlangan oilalarga bolalar nafaqasi tayinlash uchun kelib tushgan "
        "ariza uch ish kuni ichida o‘rganilib, ariza beruvchining xonadoniga borilgan "
        "holda, u yoki muomalaga layoqatli oila a’zosi ishtirokida Nizomning "
        "3-ilovasiga muvofiq savolnoma axborot modulida elektron shaklda to‘ldirilishi "
        "belgilangan",
        {'italic': True},
    ),
    (".", {}),
]


def build_ariza_kiritilgan(doc, data):
    add_recipient_block(doc, data.get('mfyNomi'), data.get('street'), data.get('fio'))
    add_murojaat_line(doc, data)

    body_paragraph(doc, NIZOM_FAMILY_REGISTRY_PARAGRAPH)
    body_paragraph(doc, ARIZA_KIRITILGAN_NIZOM_CLAUSE)

    ariza_year, ariza_day, ariza_month = split_date(data.get('arizaVaqti'))
    body_paragraph(doc, [
        ("Yuqoridagi qaror talablariga asosan, Sizning ", {}),
        (f"{ariza_year}-yil {ariza_day}-{ariza_month} kuni", {'bold': True}),
        (" ", {}),
        (f"{data.get('arizaMaqsadi', '')} olish uchun topshirgan arizangiz belgilangan tartibda ", {}),
        ("“Ijtimoiy himoya yagona reyestri” ", {'bold': True}),
        ("AT dasturida ", {}),
        (f"ID-{data.get('arizaID', '')}", {'bold': True}),
        (" bilan ro‘yxatga olinganligini ma’lum qilamiz.", {}),
    ])

    body_paragraph(doc, [(SHIKOYAT_APPEAL_PARAGRAPH, {})])
    # Namunada imzo bloki yo'q (ataylab) — add_signature_block() bu yerda
    # chaqirilmaydi.


TEMPLATE_BUILDERS = {
    'rad': build_rad,
    'tasdiqlandi': build_tasdiqlandi,
    'tayinlandi': build_tayinlandi,
    'muddat': build_muddat,
    'arizaKiritilmagan': build_ariza_kiritilmagan,
    'arizaKiritilgan': build_ariza_kiritilgan,
}


def build_letter_document(letter):
    """Berilgan xat yozuvi (letter dict) uchun to'ldirilgan .docx yaratadi va BytesIO qaytaradi."""
    doc = new_document()
    builder = TEMPLATE_BUILDERS.get(letter.get('template'), build_rad)
    builder(doc, letter)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def safe_filename(letter):
    fio = (letter.get('fio') or 'xat').strip()
    template = letter.get('template') or 'xat'
    base = f"{fio}_{template}"
    base = re.sub(r'[\\/:*?"<>|]+', '', base)
    base = re.sub(r'\s+', '_', base).strip('_')
    return f"{base or 'xat'}.docx"
