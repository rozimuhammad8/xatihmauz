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
    ROL_SAXOVAT = "saxovat"
    ROL_XAT = "xat"
    ROL_CHOICES = [
        (ROL_SAXOVAT, "Saxovat va ko'mak (arizalar)"),
        (ROL_XAT, "Xat tizimi"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profil"
    )
    tuman = models.CharField("Tuman", max_length=100, blank=True, default="")
    rol = models.CharField("Rol", max_length=16, choices=ROL_CHOICES, default=ROL_SAXOVAT)
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

    def __str__(self):
        return f"{self.fio} - {self.get_kategoriya_display()} ({self.get_holat_display()})"

    def rad_sabablari_royxati(self):
        """Tanlangan rad sabablarining (nom, matn) ro'yxatini qaytaradi."""
        from .reasons import sabab_matni_kod_orqali, BOSHQA_KOD

        natija = []
        for kod in self.rad_sabab_kodlari:
            if kod == BOSHQA_KOD:
                if self.boshqa_sabab_matni.strip():
                    natija.append(("Boshqa sabab", self.boshqa_sabab_matni.strip()))
                continue
            nom, matn = sabab_matni_kod_orqali(self.kategoriya, kod)
            if matn:
                natija.append((nom, matn))
        return natija
