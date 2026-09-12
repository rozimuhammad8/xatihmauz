# -*- coding: utf-8 -*-
"""Talabnoma uchun tashkilotlar va ular ko'rsatadigan yordam turlari.

ASOS: O'zbekiston Respublikasi Vazirlar Mahkamasining 2023-yil 7-oktabrdagi
539-son qarori — "Inson" ijtimoiy xizmatlar markazi va ijtimoiy xodimlar
ko'rsatadigan ijtimoiy xizmatlar va yordamlar ro'yxati (1-ilova). Qarorning
7-bandiga ko'ra ijtimoiy xodimlar guruhi tuzgan reja davlat boshqaruv
organlari, mahalliy ijro etuvchi hokimiyat organlari, xo'jalik birlashmalari,
fuqarolarning o'zini-o'zi boshqarish organlari va boshqa tashkilotlar
tomonidan o'z vakolatlari doirasida BAJARILISHI MAJBURIY.

╔══════════════════════════════════════════════════════════════════════════╗
║ DIQQAT — bu ro'yxat tayyor javob emas, TAVSIYA.                          ║
║ U qarorning 1-ilovasidagi yo'nalishlar va tumandagi amaldagi idoralar    ║
║ nomlari asosida tuzilgan. Hujjat yuborishdan oldin tashkilot nomi va     ║
║ yordam ta'rifini o'z tumaningizdagi rasmiy nomlanish bilan solishtiring. ║
║ Forma erkin matnni ham qabul qiladi — ro'yxatda yo'q variantni shunchaki ║
║ yozib ketish mumkin.                                                     ║
║                                                                          ║
║ Ro'yxatni o'zgartirish uchun faqat shu faylni tahrirlang.                ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

# Har bir yozuv:
#   kod       — ichki belgi (o'zgartirilmaydi)
#   nomi      — hujjatga "...boshlig'iga" so'zidan oldin yoziladigan matn
#   izoh      — tanlash ro'yxatida kulrang izoh sifatida ko'rinadi
#   yordamlar — shu tashkilotdan so'ralishi mumkin bo'lgan yordam turlari
TASHKILOTLAR = [
    {
        "kod": "bandlik",
        "nomi": "{tuman} kambag'allikni qisqartirish va bandlik bo'limi",
        "izoh": "Bandlik, kasb-hunar, tadbirkorlik",
        "yordamlar": [
            "Mahalla xokim yordamchisiga daromad manbai va bandlikni ta'minlash uchun yo'naltirish",
            "Doimiy ish bilan ta'minlash uchun bo'sh ish o'rinlariga yo'naltirish",
            "Kasb-hunarga o'qitish kurslariga jalb qilish",
            "Haq to'lanadigan jamoat ishlariga jalb qilish",
            "Oilaviy tadbirkorlikni yo'lga qo'yish uchun subsidiya ajratish",
            "O'zini o'zi band qilgan shaxs sifatida ro'yxatga olish",
        ],
    },
    {
        "kod": "tibbiyot",
        "nomi": "{tuman} tibbiyot birlashmasi",
        "izoh": "Tibbiy ko'rik, davolanish, dori-darmon",
        "yordamlar": [
            "Chuqurlashtirilgan tibbiy ko'rikdan o'tkazish",
            "Statsionar davolanishga yo'llanma berish",
            "Imtiyozli dori-darmon bilan ta'minlash",
            "Surunkali kasallikni dispanser hisobiga olish",
            "Nogironlikni belgilash uchun TIETMga (VTEK) yo'naltirish",
            "Uyda tibbiy patronaj xizmatini tashkil etish",
        ],
    },
    {
        "kod": "xalq_talimi",
        "nomi": "{tuman} xalq ta'limi bo'limi",
        "izoh": "Maktab, o'quv qurollari",
        "yordamlar": [
            "Bolani umumta'lim maktabiga joylashtirish",
            "O'quv qurollari va maktab formasi bilan ta'minlash",
            "Maktabdan tashqari to'garaklarga jalb qilish",
            "Uyda o'qitishni tashkil etish",
        ],
    },
    {
        "kod": "maktabgacha",
        "nomi": "{tuman} maktabgacha va maktab ta'limi bo'limi",
        "izoh": "Bog'cha, maktabgacha ta'lim",
        "yordamlar": [
            "Bolani maktabgacha ta'lim muassasasiga navbatsiz joylashtirish",
            "Maktabgacha ta'lim to'lovidan ozod qilish yoki imtiyoz berish",
        ],
    },
    {
        "kod": "hokimlik",
        "nomi": "{tuman} hokimligi",
        "izoh": "Uy-joy, kommunal, moddiy yordam",
        "yordamlar": [
            "Uy-joy sharoitini yaxshilash bo'yicha ko'mak ko'rsatish",
            "Uy-joyni ta'mirlash uchun qurilish materiallari ajratish",
            "Ichimlik suvi, elektr yoki tabiiy gaz tarmog'iga ulash",
            "Bir martalik moddiy yordam ajratish",
            "Tomorqa yer uchastkasi ajratish masalasini ko'rib chiqish",
        ],
    },
    {
        "kod": "mahalla",
        "nomi": "Fuqarolarning o'zini o'zi boshqarish organi (mahalla) raisi",
        "izoh": "Mahalla darajasidagi ko'mak",
        "yordamlar": [
            "Mahalla xokim yordamchisiga daromad manbai va bandlikni ta'minlash uchun yo'naltirish",
            "Oilaning ijtimoiy-maishiy sharoitini o'rganish",
            "Homiylar hisobidan yordam tashkil etish",
            "Mahalla yettiligi muhokamasiga kiritish",
        ],
    },
    {
        "kod": "pensiya",
        "nomi": "{tuman} pensiya jamg'armasi bo'limi",
        "izoh": "Pensiya va nafaqa",
        "yordamlar": [
            "Pensiya tayinlash uchun hujjatlarni rasmiylashtirish",
            "Nogironlik bo'yicha nafaqa tayinlash",
            "Boquvchisini yo'qotganlik bo'yicha nafaqa tayinlash",
            "Pensiya miqdorini qayta hisoblash",
        ],
    },
    {
        "kod": "iib",
        "nomi": "{tuman} ichki ishlar bo'limi",
        "izoh": "Hujjat, ro'yxat, profilaktika",
        "yordamlar": [
            "Biometrik pasport rasmiylashtirishda ko'mak berish",
            "Doimiy yashash joyi bo'yicha ro'yxatga olish",
            "Oilaviy nizolar bo'yicha profilaktik ishlarni tashkil etish",
        ],
    },
    {
        "kod": "davlat_xizmatlari",
        "nomi": "{tuman} davlat xizmatlari markazi",
        "izoh": "Hujjatlarni rasmiylashtirish",
        "yordamlar": [
            "Zarur hujjatlarni navbatsiz rasmiylashtirish",
            "Yo'qolgan hujjatlarni tiklash",
            "Ijtimoiy reestrga kiritish uchun ariza qabul qilish",
        ],
    },
    {
        "kod": "kadastr",
        "nomi": "{tuman} kadastr bo'limi",
        "izoh": "Mulk hujjatlari",
        "yordamlar": [
            "Uy-joyni kadastr hisobiga olish",
            "Mulk huquqini rasmiylashtirishda ko'mak berish",
        ],
    },
    {
        "kod": "xotin_qizlar",
        "nomi": "{tuman} xotin-qizlar qo'mitasi",
        "izoh": "Ayollar bilan ishlash",
        "yordamlar": [
            "\"Ayollar daftari\" ro'yxatiga kiritish",
            "Kasb-hunar o'rgatish kurslariga jalb qilish",
            "Oilada nizoli vaziyatni bartaraf etishda ko'mak berish",
        ],
    },
    {
        "kod": "yoshlar",
        "nomi": "{tuman} yoshlar ishlari agentligi bo'limi",
        "izoh": "Yoshlar bilan ishlash",
        "yordamlar": [
            "\"Yoshlar daftari\" ro'yxatiga kiritish",
            "Yoshlarni ish bilan ta'minlash dasturiga jalb qilish",
            "Tadbirkorlik loyihasi uchun imtiyozli kredit rasmiylashtirish",
        ],
    },
    {
        "kod": "protez",
        "nomi": "Andijon viloyat protez-ortopediya markazi",
        "izoh": "Reabilitatsiya vositalari",
        "yordamlar": [
            "Nogironlik aravachasi bilan ta'minlash",
            "Protez-ortopediya buyumlari bilan ta'minlash",
            "Eshitish yoki ko'rish apparati bilan ta'minlash",
            "Reabilitatsiya kursiga yo'llanma berish",
        ],
    },
]


# Ba'zi yozuvlar "{tuman}" placeholderi bilan ("{tuman} hokimligi" kabi) —
# bu XodimProfil.tuman qiymati bilan almashtiriladi (masalan "Andijon tuman"),
# shu orqali boshqa tumandagi xodimga o'z tumanidagi idora nomi taklif
# qilinadi. Placeholder bo'lmagan yozuvlar (mahalla, viloyat darajasidagi
# protez-ortopediya markazi) o'zgarishsiz qoladi.
def _nomi_toldirilgan(tashkilot, tuman):
    return tashkilot["nomi"].replace("{tuman}", tuman or "Andijon tuman")


def tashkilot_nomlari(tuman=""):
    """(nomi, izoh) juftliklari — <datalist> uchun. `tuman` — so'rov
    yuborayotgan xodimning XodimProfil.tuman qiymati."""
    return [(_nomi_toldirilgan(t, tuman), t["izoh"]) for t in TASHKILOTLAR]


def yordamlar_xaritasi(tuman=""):
    """{tashkilot nomi: [yordam turlari]} — tanlangan tashkilotga qarab
    yordam ro'yxatini filtrlash uchun (JSON sifatida sahifaga beriladi)."""
    return {_nomi_toldirilgan(t, tuman): t["yordamlar"] for t in TASHKILOTLAR}


def barcha_yordamlar():
    """Takrorlarsiz umumiy ro'yxat — tashkilot hali tanlanmagan bo'lsa
    yoki erkin matn yozilgan bo'lsa ko'rsatiladi."""
    korilgan, natija = set(), []
    for tashkilot in TASHKILOTLAR:
        for yordam in tashkilot["yordamlar"]:
            if yordam not in korilgan:
                korilgan.add(yordam)
                natija.append(yordam)
    return natija
