# -*- coding: utf-8 -*-
"""Foydalanuvchi kiritgan matn va sonlarni saqlashdan oldin bir xil, to'g'ri
ko'rinishga keltirish uchun umumiy yordamchi funksiyalar (core va xat ilovalari
uchun umumiy)."""
import re

_SOZ_BOSHI_RE = re.compile(r"(^|[.\s])([a-zʻʼ])")
_BIRINCHI_HARF_RE = re.compile(r"[a-zʻʼ]")

# F.I.O oxiridagi otasining ismi qo'shimchalari rasmiy hujjatlarda KICHIK
# harf bilan yoziladi: "Yusupova Yorqinoy Xakimjon qizi", "Aliyev Vali
# Valijon o'g'li". Bularsiz title-case ularni "Qizi"/"O'g'li" qilib
# yuborardi.
_QOSHIMCHALAR = {"qiz", "qizi", "ogli", "oglii", "ugli", "ugly"}
_APOSTROFLAR = str.maketrans({"ʻ": "", "ʼ": "", "‘": "", "’": "", "`": "", "'": ""})


def _qoshimchami(soz):
    return soz.lower().translate(_APOSTROFLAR) in _QOSHIMCHALAR


def _qoshimchalarni_kichiklashtirish(text):
    sozlar = text.split(" ")
    # Faqat OXIRIDAGI qo'shimchalar kichiklashtiriladi — ism o'rtasidagi
    # tasodifiy so'z tegmasin.
    for i in range(len(sozlar) - 1, -1, -1):
        if not sozlar[i]:
            continue
        if _qoshimchami(sozlar[i]):
            sozlar[i] = sozlar[i].lower()
        else:
            break
    return " ".join(sozlar)


def _bosh_va_oxiridagi_boshliqlarni_tozalash(text):
    return " ".join(text.split()) if text else ""


def smart_title_case(text):
    """Har bir so'zning birinchi harfini katta, qolganini kichik qiladi.
    Apostrofdan keyingi harfni katta qilmaydi (masalan "guz'ar" -> "Guz'ar",
    "KATTA guZ'Ar" -> "Katta Guz'ar"), ortiqcha probellarni yig'ishtiradi."""
    text = _bosh_va_oxiridagi_boshliqlarni_tozalash(text)
    if not text:
        return ""
    text = text.lower()
    text = _SOZ_BOSHI_RE.sub(lambda m: m.group(1) + m.group(2).upper(), text)
    return _qoshimchalarni_kichiklashtirish(text)


def smart_sentence_case(text):
    """Faqat matndagi birinchi harfni katta, qolganini kichik qiladi (tashkilot
    nomlari kabi bir martalik nomlar uchun)."""
    text = _bosh_va_oxiridagi_boshliqlarni_tozalash(text)
    if not text:
        return ""
    text = text.lower()
    m = _BIRINCHI_HARF_RE.search(text)
    if not m:
        return text
    i = m.start()
    return text[:i] + text[i].upper() + text[i + 1:]


def _parse_number(value):
    """'2 220000', '2220000.00', '2,220,000', '2.220.000,00' kabi turli
    formatdagi sonlarni ishonchli tarzda floatga aylantiradi."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(" ", "").replace("\xa0", "")
    if not text:
        return None
    last_sep = max(text.rfind(","), text.rfind("."))
    if last_sep == -1:
        cleaned = text
    else:
        frac_part = text[last_sep + 1:]
        int_part = text[:last_sep]
        if frac_part.isdigit() and 1 <= len(frac_part) <= 2:
            cleaned = re.sub(r"[.,]", "", int_part) + "." + frac_part
        else:
            cleaned = re.sub(r"[.,]", "", text)
    try:
        return float(cleaned)
    except ValueError:
        return None


def ijrochi_qisqa_ism(user):
    """F.I.O dan 'I.Familya' ko'rinishini hosil qiladi (masalan 'D.Atamirzayev'),
    imzo blokidagi "Ijrochi:" qatori uchun. Familya bo'lmasa, foydalanuvchi
    nomi (username) qaytariladi."""
    if not user:
        return ""
    ism = (user.first_name or "").strip()
    familya = (user.last_name or "").strip()
    if ism and familya:
        return f"{ism[0].upper()}.{familya}"
    if familya:
        return familya
    return user.get_username()


def smart_money(value):
    """Turli formatda kiritilgan summani bitta ko'rinishga keltiradi:
    '2 220000' yoki '2220000.00' -> '2 220 000' (butun so'm, minglik probel
    bilan ajratilgan). Sonni tushuna olmasa, kiritilgan matnni o'zgarishsiz
    qaytaradi."""
    if not value:
        return ""
    amount = _parse_number(value)
    if amount is None:
        return str(value).strip()
    text = f"{amount:,.0f}"
    return text.replace(",", " ")


# ------------------------------------------------------------------
# KIRITISHNI O'ZI TO'G'RILASH
# Xodim shoshib, turli formatda yozishi mumkin. Formani xato bilan qaytarish
# o'rniga, tushunarli bo'lgan hamma narsa avtomatik to'g'ri ko'rinishga
# keltiriladi. Faqat umuman tushunib bo'lmaydigan qiymat xato beradi.
# ------------------------------------------------------------------
import datetime as _datetime

# Sana formatlari: 2026-07-16, 16.07.2026, 16/07/2026, 16-07-2026, 2026/07/16
_SANA_NAMUNALARI = (
    ("%Y-%m-%d", None),
    ("%Y/%m/%d", None),
    ("%Y.%m.%d", None),
    ("%d.%m.%Y", None),
    ("%d/%m/%Y", None),
    ("%d-%m-%Y", None),
    ("%d.%m.%y", None),
)


def sanani_oqish(value):
    """Turli formatdagi sanani `datetime.date` ga aylantiradi.

    '2026-07-16', '16.07.2026', '16/07/2026', '16-07-2026', '2026/07/16'
    hammasi bir xil natija beradi. Tushunib bo'lmasa None qaytaradi.
    """
    if value in (None, ""):
        return None
    if isinstance(value, _datetime.datetime):
        return value.date()
    if isinstance(value, _datetime.date):
        return value

    matn = " ".join(str(value).split())
    if not matn:
        return None

    for namuna, _ in _SANA_NAMUNALARI:
        try:
            return _datetime.datetime.strptime(matn, namuna).date()
        except ValueError:
            continue
    return None


# Kirilcha -> lotincha. Shablonlardan ko'chirilgan murojaat matni ko'pincha
# kirilchada keladi; brauzerdagi JS uni o'giradi, lekin server ham
# ishonmasligi kerak — bazaga har doim lotincha tushsin.
_KIRIL_XARITA = {
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Ё': 'Yo',
    'Ж': 'J', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
    'Ф': 'F', 'Х': 'X', 'Ц': 'S', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sh', 'Ъ': "'",
    'Ы': 'I', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    'Ў': "O'", 'Қ': 'Q', 'Ғ': "G'", 'Ҳ': 'H',
}
_KIRIL_XARITA.update({k.lower(): v.lower() for k, v in _KIRIL_XARITA.items()})
_KIRIL_XARITA.update({'ў': "o'", 'қ': 'q', 'ғ': "g'", 'ҳ': 'h'})


# "е" harfi so'z boshida yoki unlidan keyin "ye", aks holda "e" bo'ladi
# ("Елена" -> "Yelena", lekin "Сергей" -> "Sergey"). Qoida brauzerdagi
# krilToLotin() bilan bir xil — ikkalasi bir xil natija berishi shart.
_KIRIL_UNLILAR = "aeiouAEIOUаеёиоуыэюяАЕЁИОУЫЭЮЯ"
_KIRIL_HARFLAR = "a-zA-Zа-яА-ЯёЁўЎқҚғҒҳҲ'ʻʼ"


def kirilni_lotinga(text):
    """Kirilcha harflarni lotinchaga o'giradi. Matnda kirilcha bo'lmasa
    hech narsa o'zgarmaydi."""
    if not text:
        return text
    matn = str(text)
    if not any(ch in _KIRIL_XARITA or ch in "еЕ" for ch in matn):
        return matn

    natija = []
    for i, ch in enumerate(matn):
        if ch in ("е", "Е"):
            oldingi = matn[i - 1] if i else ""
            soz_boshi = not oldingi or not re.match(f"[{_KIRIL_HARFLAR}]", oldingi)
            ye = soz_boshi or oldingi in _KIRIL_UNLILAR
            if ch == "Е":
                natija.append("Ye" if ye else "E")
            else:
                natija.append("ye" if ye else "e")
        else:
            natija.append(_KIRIL_XARITA.get(ch, ch))
    return "".join(natija)


def tozalangan_matn(value):
    """Har qanday matnli maydon uchun eng kam normalizatsiya:
    kirilchani lotinga o'giradi, ortiqcha probel va ko'rinmas belgilarni
    yig'ishtiradi."""
    if not value:
        return ""
    matn = kirilni_lotinga(str(value))
    matn = matn.replace("\xa0", " ").replace("\u200b", "")
    return " ".join(matn.split())


def raqamli_matn(value):
    """Hisob raqami, murojaat raqami kabi maydonlar: probel va ko'rinmas
    belgilar olib tashlanadi, qolgani tegilmaydi."""
    if not value:
        return ""
    return "".join(str(value).split())
