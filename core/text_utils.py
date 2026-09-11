# -*- coding: utf-8 -*-
"""Foydalanuvchi kiritgan matn va sonlarni saqlashdan oldin bir xil, to'g'ri
ko'rinishga keltirish uchun umumiy yordamchi funksiyalar (core va xat ilovalari
uchun umumiy)."""
import re

_SOZ_BOSHI_RE = re.compile(r"(^|[.\s])([a-zʻʼ])")
_BIRINCHI_HARF_RE = re.compile(r"[a-zʻʼ]")


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
    return _SOZ_BOSHI_RE.sub(lambda m: m.group(1) + m.group(2).upper(), text)


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
