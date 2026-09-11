# -*- coding: utf-8 -*-
"""
Har bir kategoriya uchun rad etish sabablari.
Har bir yozuv: (kod, qisqa_nom (checkbox uchun), to'liq_matn (docx ga yoziladigan)).
Bu matnlar avval shablonlar/*_rad.docx fayllarni yaratishda ishlatilgan matnlar bilan bir xil.
"""

REESTR = (
    "Sizning Ijtimoiy reestrda ro'yxatda emasligingiz va (yoki) oilangizning o'rtacha daromadi belgilangan "
    "me'yordan (har bir oila a'zosi uchun minimal iste'mol xarajatlarining 2 baravaridan) oshganligi aniqlangan. "
    "462-sonli qarorga muvofiq, yordam faqat Ijtimoiy reestrga kiritilgan yoki belgilangan me'yordan oshmagan "
    "daromadga ega oilalarga ko'rsatilishi belgilangan. Shu sababli, ushbu turdagi yordamni tayinlash imkoni "
    "bo'lmagan."
)

FUND_LIMIT = (
    "462-sonli qarorning 2-bandiga muvofiq, \"Saxovat va ko'mak\" jamg'armasi mablag'lari mahallalar kesimida "
    "aholi soni, kambag'al oilalar soni va nogironligi bo'lgan shaxslar soniga mutanosib ravishda hamda tuman "
    "toifasiga qarab belgilangan tuzatish koeffitsiyenti (0,88–1,1) asosida har oyning 5-sanasiga qadar "
    "taqsimlanadi. Mahallangiz uchun joriy oyga taqsimlangan mablag' miqdori to'liq sarflanganligi sababli, "
    "ushbu bosqichda yordam ko'rsatish imkoni bo'lmagan. Qayta murojaat qilishingiz mumkin."
)

MAHALLA_YETTILIGI = (
    "462-sonli qarorga muvofiq, yordam ko'rsatish to'g'risidagi yakuniy qaror \"mahalla yettiligi\" tomonidan "
    "ko'rib chiqiladi va qabul qilinadi. Arizangiz ko'rib chiqilgach, \"mahalla yettiligi\" tomonidan yordam "
    "berishni rad etish to'g'risida qaror qabul qilingan."
)


def _double_funding(noun):
    return (
        f"Sizga (yoki oila a'zoingizga) {noun} maqsadida mo'ljallangan yordam \"Ayollar daftari\", \"Yoshlar "
        "daftari\" yoki \"Saxovat va ko'mak\" jamg'armalaridan biri hisobidan allaqachon ko'rsatilgani "
        "aniqlangan. 462-sonli qaror bilan tasdiqlangan Nizomga muvofiq, bir xil turdagi ijtimoiy yordam ushbu "
        "uch jamg'arma mablag'laridan faqat bittasi hisobidan ko'rsatilishi belgilangan. Shu sababli, ushbu "
        "turdagi yordamni tayinlash imkoni bo'lmagan."
    )


BOSHQA_KOD = "boshqa"

RAD_SABABLARI = {
    "oziq_ovqat": [
        ("reestr", "Ijtimoiy reestrda emas / daromad chegarasidan oshgan", REESTR),
        ("ikki_karra", "Xuddi shu maqsadda boshqa jamg'armadan yordam olingan", _double_funding("oziq-ovqat")),
        ("limit", "Mahalla uchun ajratilgan mablag' (limit) tugagan", FUND_LIMIT),
        ("yettilik", "\"Mahalla yettiligi\" rad etish qarorini qabul qilgan", MAHALLA_YETTILIGI),
        (BOSHQA_KOD, "Boshqa sabab (qo'lda kiritiladi)", None),
    ],
    "kiyim_kechak": [
        ("reestr", "Ijtimoiy reestrda emas / daromad chegarasidan oshgan", REESTR),
        ("ikki_karra", "Xuddi shu maqsadda boshqa jamg'armadan yordam olingan", _double_funding("kiyim-kechak")),
        ("limit", "Mahalla uchun ajratilgan mablag' (limit) tugagan", FUND_LIMIT),
        ("yettilik", "\"Mahalla yettiligi\" rad etish qarorini qabul qilgan", MAHALLA_YETTILIGI),
        (BOSHQA_KOD, "Boshqa sabab (qo'lda kiritiladi)", None),
    ],
    "kommunal_tolovlar": [
        ("reestr", "Ijtimoiy reestrda emas / daromad chegarasidan oshgan", REESTR),
        ("ikki_karra", "Xuddi shu maqsadda boshqa jamg'armadan yordam olingan", _double_funding("kommunal to'lovlar")),
        ("limit", "Mahalla uchun ajratilgan mablag' (limit) tugagan", FUND_LIMIT),
        ("yettilik", "\"Mahalla yettiligi\" rad etish qarorini qabul qilgan", MAHALLA_YETTILIGI),
        (BOSHQA_KOD, "Boshqa sabab (qo'lda kiritiladi)", None),
    ],
    "favqulodda": [
        ("reestr", "Ijtimoiy reestrda emas / daromad chegarasidan oshgan", REESTR),
        ("ikki_karra", "Xuddi shu maqsadda boshqa jamg'armadan yordam olingan", _double_funding("favqulodda (shoshilinch) yordam")),
        ("limit", "Mahalla uchun ajratilgan mablag' (limit) tugagan", FUND_LIMIT),
        ("yettilik", "\"Mahalla yettiligi\" rad etish qarorini qabul qilgan", MAHALLA_YETTILIGI),
        (BOSHQA_KOD, "Boshqa sabab (qo'lda kiritiladi)", None),
    ],
    "uy_joy": [
        ("egalik", "Nomida uy-joy egalik huquqi mavjud emas",
         "Sizning nomingizda ushbu qaror talablariga javob beradigan uy-joy egalik huquqi mavjud emasligi "
         "aniqlangan. Mazkur qaror bilan tasdiqlangan tartibga muvofiq, yordam faqat ariza beruvchining o'z "
         "nomiga rasmiylashtirilgan uy-joyi bo'lgan taqdirdagina ko'rsatilishi belgilangan. Shu sababli, "
         "axborot tizimi tomonidan ariza shakllantirish imkoniyati cheklangan va ushbu turdagi yordamni "
         "rasmiylashtirish imkoni bo'lmagan."),
        ("kadastr", "Uy-joy kadastr va soliq organlarida ro'yxatda emas",
         "Ta'mirlanishi rejalashtirilgan uy-joy kadastr organlarida hisobga olinmagan hamda soliq organlari "
         "axborot tizimiga soliq to'lovchi sifatida kiritilmaganligi aniqlangan. Mazkur qaror talablariga "
         "ko'ra, yordam faqat kadastr organlarida hisobga olingan hamda soliq organlari axborot tizimiga "
         "soliq to'lovchi sifatida kiritilgan uy-joylarga ko'rsatilishi belgilangan. Shu sababli, ushbu "
         "turdagi yordamni rasmiylashtirish imkoni bo'lmagan."),
        ("reestr", "Ijtimoiy himoyaga muhtoj toifaga kirmaydi", REESTR.replace(
            "462-sonli qarorga muvofiq", "Mazkur qarorga muvofiq")),
        ("yettilik", "Mahalla yettiligi tekshiruvidan o'tmagan",
         "Mahalla yettiligi tomonidan o'tkazilgan o'rganish natijasiga ko'ra, uy-joyingiz ta'mirtalab holatda "
         "deb topilmagan va (yoki) ta'mirlanishi zarur bo'lgan qismlar aniq belgilanmagan. Mazkur tartibga "
         "muvofiq, yordam ko'rsatish to'g'risida qaror \"mahalla yettiligi\"ning kollegial xulosasiga asosan "
         "qabul qilinadi. Shu sababli, ushbu turdagi yordamni tayinlash imkoni bo'lmagan."),
        ("mablagh", "Jamg'arma mablag'lari yetarli emas", FUND_LIMIT.replace(
            "462-sonli qarorning 2-bandiga muvofiq", "Mazkur qarorga muvofiq")),
        (BOSHQA_KOD, "Boshqa sabab (qo'lda kiritiladi)", None),
    ],
}

KATEGORIYALAR = [
    ("oziq_ovqat", "Oziq-ovqat"),
    ("kiyim_kechak", "Kiyim-kechak"),
    ("kommunal_tolovlar", "Kommunal to'lovlar"),
    ("uy_joy", "Uy-joy ta'mirlash"),
    ("favqulodda", "Favqulodda (shoshilinch) yordam"),
]

HOLATLAR = [
    ("tayinlangan", "Tayinlangan (ijobiy)"),
    ("rad", "Rad etilgan"),
]

TASHKILOTLAR = [
    ("Prezident ishonch telefoni", "O'zbekiston Respublikasi Prezidenti ishonch telefoni"),
    ("Milliy agentlik", "O'zbekiston Respublikasi Prezidenti huzuridagi Ijtimoiy himoya milliy agentligi"),
    ("Viloyat hokimligi", "Andijon viloyat hokimligi"),
    ("Tuman hokimligi", "Andijon tuman hokimligi"),
    ("Boshqa", "Boshqa tashkilot"),
]

TEMPLATE_FAYLLAR = {
    ("oziq_ovqat", "tayinlangan"): "oziq_ovqat_tayinlangan.docx",
    ("oziq_ovqat", "rad"): "oziq_ovqat_rad.docx",
    ("kiyim_kechak", "tayinlangan"): "kiyim_kechak_tayinlangan.docx",
    ("kiyim_kechak", "rad"): "kiyim_kechak_rad.docx",
    ("kommunal_tolovlar", "tayinlangan"): "kommunal_tolovlar_tayinlangan.docx",
    ("kommunal_tolovlar", "rad"): "kommunal_tolovlar_rad.docx",
    ("uy_joy", "tayinlangan"): "uy_joy_tamirlash_tayinlangan.docx",
    ("uy_joy", "rad"): "uy_joy_rad.docx",
    ("favqulodda", "tayinlangan"): "favqulodda_yordam_tayinlangan.docx",
    ("favqulodda", "rad"): "favqulodda_yordam_rad.docx",
}


def sabablar_royxati(kategoriya):
    return RAD_SABABLARI.get(kategoriya, [])


def sabab_matni_kod_orqali(kategoriya, kod):
    for k, nom, matn in sabablar_royxati(kategoriya):
        if k == kod:
            return nom, matn
    return None, None
