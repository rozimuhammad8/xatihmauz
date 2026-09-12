from django.conf import settings
from django.db import models

from .reasons import KATEGORIYALAR, HOLATLAR


class Tashkilot(models.Model):
    """Xat/ariza imzo blokida ko'rsatiladigan tashkilot: nomi ("... direktori:"
    qatorida) va rahbari (F.I.O). Xodimlar shu tashkilotlardan biriga
    biriktiriladi (XodimProfil.tashkilot)."""

    nomi = models.CharField("Tashkilot nomi", max_length=255)
    rahbar = models.CharField("Rahbar F.I.O", max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "Tashkilot"
        verbose_name_plural = "Tashkilotlar"

    def __str__(self):
        return self.nomi


class XodimProfil(models.Model):
    # Rol kodlari ("bosh_ijtimoiy"/"reestr") ilgari "saxovat"/"xat" deb
    # nomlangan edi — 0005 migratsiyasi eski yozuvlarni yangi kodlarga
    # ko'chiradi, shuning uchun kodda faqat shu ikki qiymat ishlatiladi.
    ROL_BOSH_IJTIMOIY = "bosh_ijtimoiy"
    ROL_REESTR = "reestr"
    ROL_CHOICES = [
        (ROL_BOSH_IJTIMOIY, "Bosh ijtimoiy (arizalar)"),
        (ROL_REESTR, "Reestr tizimi"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profil"
    )
    tuman = models.CharField("Tuman", max_length=100, blank=True, default="")
    rol = models.CharField("Rol", max_length=24, choices=ROL_CHOICES, default=ROL_BOSH_IJTIMOIY)
    tashkilot = models.ForeignKey(
        Tashkilot, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="xodimlar", verbose_name="Tashkilot",
    )

    def __str__(self):
        return f"{self.user.username} ({self.tuman or 'tuman kiritilmagan'})"


class Ariza(models.Model):
    kategoriya = models.CharField(max_length=32, choices=KATEGORIYALAR)
    holat = models.CharField(max_length=16, choices=HOLATLAR)

    tuman = models.CharField("Tuman", max_length=100, default="", blank=True)
    mfy = models.CharField("MFY", max_length=255)
    kucha = models.CharField("Ko'cha", max_length=255)
    fio = models.CharField("F.I.O", max_length=255)
    tashkilot = models.CharField("Murojaat tashkiloti", max_length=255)
    sana = models.DateField("Murojaat sanasi")
    murojaat_raqami = models.CharField("Murojaat raqami", max_length=100)
    ariza_raqami = models.CharField("Ariza raqami", max_length=100)

    # Faqat holat = tayinlangan bo'lganda ishlatiladi
    ajratilgan_summa = models.CharField(
        "Ajratilgan summa (so'm)", max_length=100, blank=True, default=""
    )
    kollegal_qaror = models.CharField(
        "Kollegal qaror raqami", max_length=100, blank=True, default="",
        help_text="Mahalla yettiligi qarorining raqami — xatda "
                  "\"(Kollegal qaror raqami-...)\" bo'lib chiqadi",
    )

    # Faqat holat = rad bo'lganda ishlatiladi
    rad_sabab_kodlari = models.JSONField("Rad sabablari (kodlar)", default=list, blank=True)
    boshqa_sabab_matni = models.TextField("Boshqa sabab matni", blank=True, default="")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="arizalar"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Ariza"
        verbose_name_plural = "Arizalar"
        indexes = [
            # Dashboard har doim "o'z arizalarim, eng yangisi birinchi" deb
            # so'raydi; admin ro'yxati kategoriya/holat bo'yicha filtrlaydi.
            models.Index(fields=["created_by", "-created_at"], name="ariza_muallif_sana_idx"),
            models.Index(fields=["kategoriya", "holat"], name="ariza_kat_holat_idx"),
        ]

    def __str__(self):
        return f"{self.fio} - {self.get_kategoriya_display()} ({self.get_holat_display()})"

    def rad_sabablari_royxati(self):
        """Tanlangan rad sabablarining (nom, matn) ro'yxatini qaytaradi."""
        from .reasons import sabab_matni_kod_orqali, BOSHQA_KOD

        natija = []
        for kod in self.rad_sabab_kodlari or []:
            if kod == BOSHQA_KOD:
                if self.boshqa_sabab_matni.strip():
                    natija.append(("Boshqa sabab", self.boshqa_sabab_matni.strip()))
                continue
            nom, matn = sabab_matni_kod_orqali(self.kategoriya, kod)
            if matn:
                natija.append((nom, matn))
        return natija


class XizmatHujjati(models.Model):
    """Xizmat (ichki) hujjatlari — arizalardan farqli o'laroq fuqaroga emas,
    xodim yoki boshqa tashkilotga yoziladi:

      bildirgi      — viloyat boshqarmasiga xodim intizomi yuzasidan xabar
      ogohlantirish — xodimga zoom yig'ilishiga kelmagani uchun ogohlantirish
      talabnoma     — boshqa tashkilotdan fuqaroga yordam berishni so'rash

    Matn Shablons/xizmat/*.docx dan olinadi, bu yerda faqat o'zgaruvchi
    maydonlar saqlanadi (qarang: core/xizmat_export.py).
    """

    TUR_BILDIRGI = "bildirgi"
    TUR_OGOHLANTIRISH = "ogohlantirish"
    TUR_TALABNOMA = "talabnoma"
    TUR_CHOICES = [
        (TUR_BILDIRGI, "Bildirgi (intizom yuzasidan)"),
        (TUR_OGOHLANTIRISH, "Ogohlantirish xati (zoom yig'ilishi)"),
        (TUR_TALABNOMA, "Talabnoma (boshqa tashkilotga)"),
    ]

    turi = models.CharField("Hujjat turi", max_length=20, choices=TUR_CHOICES)

    # Uchala turda ham bor
    mahalla = models.CharField("Mahalla / MFY nomi", max_length=255)
    xodim_fio = models.CharField("Ijtimoiy xodim F.I.O", max_length=255)

    # bildirgi
    ish_boshlagan_sana = models.DateField(
        "Lavozimga kirgan sana", null=True, blank=True
    )
    buzilish_sanasi = models.CharField(
        "Qoidabuzarlik sanasi", max_length=100, blank=True, default="",
        help_text="Masalan: 2026-yilning 19-20-avgust",
    )
    ish_vaqti = models.CharField(
        "Ish boshlanish vaqti", max_length=20, blank=True, default="09:00"
    )

    # ogohlantirish
    yigilish_sanasi = models.CharField(
        "Yig'ilish sanasi", max_length=100, blank=True, default="",
        help_text="Masalan: 30-iyun",
    )
    rahbar_lavozimi = models.CharField(
        "Yig'ilishni o'tkazgan rahbar lavozimi", max_length=255, blank=True, default=""
    )
    rahbar_fio = models.CharField(
        "Yig'ilishni o'tkazgan rahbar F.I.O", max_length=255, blank=True, default=""
    )

    # talabnoma
    qabul_qiluvchi = models.CharField(
        "Qaysi tashkilotga", max_length=500, blank=True, default="",
        help_text="\"...boshlig'iga\" so'zisiz. Masalan: Andijon tuman kambag'allikni "
                  "qisqartirish va bandlik bo'limi",
    )
    fuqaro_fio = models.CharField("Fuqaro F.I.O", max_length=255, blank=True, default="")
    fuqaro_tugilgan_sana = models.DateField(
        "Fuqaro tug'ilgan sana", null=True, blank=True
    )
    yordam_turi = models.CharField(
        "So'ralayotgan yordam turi", max_length=500, blank=True, default=""
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="xizmat_hujjatlari"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Xizmat hujjati"
        verbose_name_plural = "Xizmat hujjatlari"
        indexes = [
            models.Index(fields=["created_by", "-created_at"], name="xizmat_muallif_sana_idx"),
            models.Index(fields=["turi"], name="xizmat_turi_idx"),
        ]

    def __str__(self):
        return f"{self.get_turi_display()} — {self.xodim_fio}"
