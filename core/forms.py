from django import forms

from .models import Ariza, XizmatHujjati
from .text_utils import (
    raqamli_matn,
    sanani_oqish,
    smart_money,
    smart_sentence_case,
    smart_title_case,
    tozalangan_matn,
)


class EgiluvchanSanaField(forms.DateField):
    """Sanani turli formatda qabul qiladi: 2026-07-16, 16.07.2026, 16/07/2026...

    Django'ning oddiy DateField'i faqat ro'yxatdagi formatlarni tushunadi va
    boshqasiga "To'g'ri sana kiriting" deb xato beradi. Bu versiya avval
    sanani_oqish() bilan tushunishga harakat qiladi — xodim qanday yozsa ham
    ishlaydi.
    """

    def to_python(self, value):
        if value in self.empty_values:
            return None
        sana = sanani_oqish(value)
        if sana is not None:
            return sana
        return super().to_python(value)


class NormalizatsiyaAralashmasi:
    """Saqlashdan oldin barcha matnli maydonlarni bir xil ko'rinishga
    keltiradi: kirilcha -> lotincha, ortiqcha probellar olib tashlanadi.

    Maxsus qoidalar sinf ichida e'lon qilinadi:
      SARLAVHA_MAYDONLARI — har so'z bosh harf bilan (ism, manzil)
      JUMLA_MAYDONLARI    — faqat birinchi harf katta (tashkilot nomi)
      RAQAM_MAYDONLARI    — probelsiz (hisob raqami)
      PUL_MAYDONLARI      — "1 500 000" ko'rinishida
    """

    SARLAVHA_MAYDONLARI = ()
    JUMLA_MAYDONLARI = ()
    RAQAM_MAYDONLARI = ()
    PUL_MAYDONLARI = ()

    def clean(self):
        tozalangan = super().clean()
        for nom, qiymat in list(tozalangan.items()):
            if isinstance(qiymat, str):
                tozalangan[nom] = tozalangan_matn(qiymat)

        for nom in self.SARLAVHA_MAYDONLARI:
            if tozalangan.get(nom):
                tozalangan[nom] = smart_title_case(tozalangan[nom])
        for nom in self.JUMLA_MAYDONLARI:
            if tozalangan.get(nom):
                tozalangan[nom] = smart_sentence_case(tozalangan[nom])
        for nom in self.RAQAM_MAYDONLARI:
            if tozalangan.get(nom):
                tozalangan[nom] = raqamli_matn(tozalangan[nom])
        for nom in self.PUL_MAYDONLARI:
            if tozalangan.get(nom):
                tozalangan[nom] = smart_money(tozalangan[nom])
        return tozalangan


class ArizaForm(NormalizatsiyaAralashmasi, forms.ModelForm):
    SARLAVHA_MAYDONLARI = ("mfy", "kucha", "fio")
    PUL_MAYDONLARI = ("ajratilgan_summa",)
    RAQAM_MAYDONLARI = ("kollegal_qaror",)

    sana = EgiluvchanSanaField(
        label="Murojaat sanasi",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = Ariza
        fields = [
            "kategoriya",
            "holat",
            "mfy",
            "kucha",
            "fio",
            "tashkilot",
            "sana",
            "murojaat_raqami",
            "ariza_raqami",
            "ajratilgan_summa",
            "kollegal_qaror",
            "boshqa_sabab_matni",
        ]

    def clean(self):
        cleaned = super().clean()   # normalizatsiya shu yerda bajariladi
        if cleaned.get("holat") == "tayinlangan":
            if not cleaned.get("ajratilgan_summa"):
                self.add_error("ajratilgan_summa", "Tayinlangan holat uchun summa kiritilishi shart.")
            if not cleaned.get("kollegal_qaror"):
                self.add_error("kollegal_qaror",
                               "Tayinlangan holat uchun kollegal qaror raqami shart.")
        return cleaned


class XizmatHujjatiForm(NormalizatsiyaAralashmasi, forms.ModelForm):
    SARLAVHA_MAYDONLARI = ("mahalla", "xodim_fio", "fuqaro_fio")
    JUMLA_MAYDONLARI = ("qabul_qiluvchi",)

    """Uchala hujjat turi uchun bitta forma — kerakli maydonlar tanlangan
    turga qarab clean() da tekshiriladi (interfeysda ham shu turga tegishli
    bo'lim ko'rsatiladi)."""

    ish_boshlagan_sana = EgiluvchanSanaField(
        label="Lavozimga kirgan sana", required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    fuqaro_tugilgan_sana = EgiluvchanSanaField(
        label="Fuqaro tug'ilgan sana", required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = XizmatHujjati
        fields = [
            "turi", "mahalla", "xodim_fio",
            "ish_boshlagan_sana", "buzilish_sanasi", "ish_vaqti",
            "yigilish_sanasi", "rahbar_lavozimi", "rahbar_fio",
            "qabul_qiluvchi", "fuqaro_fio", "fuqaro_tugilgan_sana", "yordam_turi",
        ]

    # Tur -> o'sha tur uchun MAJBURIY maydonlar
    MAJBURIY = {
        XizmatHujjati.TUR_BILDIRGI: ["ish_boshlagan_sana", "buzilish_sanasi", "ish_vaqti"],
        XizmatHujjati.TUR_OGOHLANTIRISH: ["yigilish_sanasi", "rahbar_lavozimi", "rahbar_fio"],
        XizmatHujjati.TUR_TALABNOMA: [
            "qabul_qiluvchi", "fuqaro_fio", "fuqaro_tugilgan_sana", "yordam_turi"
        ],
    }

    def clean(self):
        cleaned = super().clean()
        turi = cleaned.get("turi")

        for maydon in self.MAJBURIY.get(turi, []):
            if not cleaned.get(maydon):
                self.add_error(maydon, "Bu maydon ushbu hujjat turi uchun majburiy.")

        # Boshqa turlarga tegishli maydonlar tozalanadi — bazada chalkash
        # ma'lumot qolmasligi uchun (ariza tizimidagi bilan bir xil yondashuv).
        for boshqa_tur, maydonlar in self.MAJBURIY.items():
            if boshqa_tur == turi:
                continue
            for maydon in maydonlar:
                if maydon in cleaned and maydon not in self.MAJBURIY.get(turi, []):
                    cleaned[maydon] = None if maydon.endswith("_sana") else ""

        return cleaned
