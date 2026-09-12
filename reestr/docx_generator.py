# ============================================================
# XAT MATNI VA FORMATLASH YORDAMCHILARI
# ------------------------------------------------------------
# Xat butun holda bu yerda QURILMAYDI — u Shablons/reeystr/*.docx
# fayllaridan o'qiladi (qarang: docx_templates.py). Bu modulda faqat:
#   * matn/son formatlash (split_date, format_money, car_segments, ...)
#   * shablonlarni yasaydigan buyruq uchun quruvchi bloklar
#     (new_document, add_paragraph, add_recipient_block, ...) — ular
#     shablon_qurish.py da ishlatiladi ("python manage.py reestr_shablon")
#   * huquqiy matn konstantalari (INTRO_PARAGRAPH, NIZOM_*, APPEAL_PARAGRAPH)
#     — letter_text.py (brauzer ko'rinishi) ham aynan shu matnlarni
#     qayta ishlatadi, shu sababli .docx va sayt hech qachon farq qilmaydi.
# ============================================================

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


def add_recipient_block(doc, tuman, mfy, street, fio):
    """`tuman` — xatni tayyorlagan xodimning tuman (XodimProfil.tuman)
    qiymati. Qiymatning o'zi allaqachon "Andijon tuman" kabi to'liq so'z
    birikmasi (xodim shunday kiritadi) — shuning uchun bu yerda qo'shimcha
    " tuman"/" tumani" so'zi QO'SHILMAYDI, avval "Andijon tumani" deb
    qattiq yozib qo'yilgan edi."""
    add_paragraph(
        doc,
        [
            (tuman or '', {'bold': True}),
            (", ", {'bold': True}),
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


# "{tuman}" — bu yerda ham LITERAL placeholder matni sifatida saqlanadi
# (haqiqiy qiymat emas): shablon_qurish.py buni .docx shabloniga o'sha
# ko'rinishda ko'chiradi, keyin render_letter() umumiy almashtirish
# mexanizmi orqali xodimning tuman qiymati bilan to'ldiradi (qarang:
# docx_templates._oddiy_almashtirishlar). Brauzer ko'rinishi (letter_text.py)
# esa buni o'zi .replace("{tuman}", ...) qiladi, chunki u .docx orqali
# o'tmaydi. "Andijon viloyati" statik qoladi — bu ilova hozircha faqat
# Andijon viloyati doirasidagi tumanlarga xizmat qiladi.
INTRO_PARAGRAPH = (
    "O‘zbekiston Respublikasi Prezidenti huzuridagi Ijtimoiy himoya milliy Agentligi "
    "Andijon viloyati boshqarmasi {tuman} “Inson” ijtimoiy xizmatlar markazi "
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


# "arizaKiritilmagan" shabloni (Ariza kiritilmagan xati) TEMPLATE_CHOICES'da
# yo'q — hech qachon ishlatilmagan, shuning uchun kod-asosidagi quruvchisi ham
# olib tashlangan. Matni tarixiy sabablarga ko'ra letter_text.py da qolgan
# (ariza_kiritilmagan_paragraphs), lekin PARAGRAPH_BUILDERS orqali chaqirilmaydi.

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


# ARIZA_KIRITILGAN_NIZOM_CLAUSE letter_text.py (brauzer ko'rinishi) va
# shablon_qurish.py (shablon quruvchisi) tomonidan ham ishlatiladi —
# kod-asosidagi build_ariza_kiritilgan() funksiyasi (endi yo'q) shu
# konstantani ishlatgan edi, u olib tashlansa ham konstanta qoladi.


def safe_filename(letter):
    """Yuklab olingan fayl nomi — xat yozilgan fuqaroning F.I.O si
    (shablon turi qo'shilmaydi, faqat ism-familiya)."""
    fio = (letter.get('fio') or 'xat').strip()
    base = re.sub(r'[\\/:*?"<>|]+', '', fio)
    base = re.sub(r'\s+', '_', base).strip('_')
    return f"{base or 'xat'}.docx"
