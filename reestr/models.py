from django.conf import settings
from django.db import models

from core.text_utils import ijrochi_qisqa_ism

TEMPLATE_CHOICES = [
    ("rad", "Rad etish"),
    ("tasdiqlandi", "Tasdiqlash"),
    ("tayinlandi", "Tayinlash"),
    ("muddat", "Muddat so'rash"),
    ("arizaKiritilgan", "Ariza kiritilgan"),
]

# arizaMaqsadi/arizaVaqti/arizaID bu shablonda ishlatilmaydi (docx_generator.py bilan mos)
TEMPLATES_WITHOUT_ARIZA_INFO = ("muddat",)


class Xat(models.Model):
    template = models.CharField(max_length=32, choices=TEMPLATE_CHOICES)

    # Asosiy ma'lumotlar (barcha shablonlarda umumiy)
    # Xatni tayyorlagan xodimning tumani — saqlashda XodimProfil.tuman'dan
    # avtomatik to'ldiriladi (qarang: views._apply_payload). Ariza (core)
    # tizimidagi Ariza.tuman bilan bir xil yondashuv: xodim qo'lda kiritmaydi,
    # forma ham bunday maydonni ko'rsatmaydi.
    tuman = models.CharField("Tuman", max_length=100, blank=True, default="")
    fio = models.CharField("F.I.O", max_length=255)
    mfy_nomi = models.CharField("MFY nomi", max_length=255)
    street = models.CharField("Ko'cha nomi", max_length=255)
    murojaatfrom = models.CharField("Qayerdan murojaat", max_length=500)
    murojaat_raqami = models.CharField("Murojaat raqami", max_length=100)
    murojaat_vaqti = models.DateField("Murojaat sanasi")

    # rad / tasdiqlandi / tayinlandi / arizaKiritilgan uchun
    ariza_maqsadi = models.CharField("Ariza maqsadi", max_length=255, blank=True, default="")
    ariza_vaqti = models.DateField("Ariza sanasi", null=True, blank=True)
    ariza_id = models.CharField("Ariza raqami (ID)", max_length=100, blank=True, default="")
    is_qayta = models.BooleanField("Qayta o'rganildimi", default=False)

    # rad
    rad_sabablari = models.JSONField("Rad sabablari", default=dict, blank=True)

    # tasdiqlandi
    tasdiq_sanasi = models.CharField("Tasdiqlash sanasi", max_length=100, blank=True, default="")
    tolov_sanasi = models.CharField("To'lov sanasi", max_length=100, blank=True, default="")
    tolov_sum = models.CharField("To'lov summasi", max_length=100, blank=True, default="")
    hisob_raqami = models.CharField("Hisob raqami", max_length=100, blank=True, default="")

    # tayinlandi
    tayinlash_qoshimcha = models.CharField("Qo'shimcha ma'lumot", max_length=1000, blank=True, default="")

    # muddat
    qoshimcha_malumot = models.CharField("Qo'shimcha ma'lumot", max_length=1000, blank=True, default="")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="xatlar"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Xat"
        verbose_name_plural = "Xatlar"
        indexes = [
            # Dashboard: "o'z xatlarim, eng yangisi birinchi" + shablon turi va
            # murojaat sanasi bo'yicha filtr.
            models.Index(fields=["created_by", "-created_at"], name="xat_muallif_sana_idx"),
            models.Index(fields=["template"], name="xat_shablon_idx"),
            models.Index(fields=["murojaat_vaqti"], name="xat_murojaat_sana_idx"),
        ]

    def __str__(self):
        return f"{self.fio} - {self.get_template_display()}"

    def to_letter_dict(self):
        """docx_generator.py va letter_text.py kutayotgan aynan o'sha kalitlar bilan
        (Flask ilovasidagi `letter` dict shakli bilan bir xil) lug'at qaytaradi —
        shu orqali eski tizim bilan bir xil hujjat yaratiladi."""
        profil = getattr(self.created_by, "profil", None)
        tashkilot = profil.tashkilot if profil else None
        return {
            "id": self.id,
            "template": self.template,
            "tuman": self.tuman,
            "fio": self.fio,
            "mfyNomi": self.mfy_nomi,
            "street": self.street,
            "murojaatfrom": self.murojaatfrom,
            "murojaatRaqami": self.murojaat_raqami,
            "murojaatVaqti": self.murojaat_vaqti.isoformat() if self.murojaat_vaqti else "",
            "arizaMaqsadi": self.ariza_maqsadi,
            "arizaVaqti": self.ariza_vaqti.isoformat() if self.ariza_vaqti else "",
            "arizaID": self.ariza_id,
            "isQayta": self.is_qayta,
            "radSabablari": self.rad_sabablari or {},
            "tasdiqMalumotlari": {
                "is": self.template == "tasdiqlandi",
                "tasdiqSanasi": self.tasdiq_sanasi,
                "tolovSanasi": self.tolov_sanasi,
                "tolovSum": self.tolov_sum,
                "hisobRaqami": self.hisob_raqami,
            },
            "tayinlashQoshimcha": self.tayinlash_qoshimcha,
            "qoshimchaMalumot": self.qoshimcha_malumot,
            "tashkilotNomi": tashkilot.nomi if tashkilot else "Tashkilot",
            "tashkilotRahbar": tashkilot.rahbar if tashkilot else "",
            "ijrochi": ijrochi_qisqa_ism(self.created_by),
        }
