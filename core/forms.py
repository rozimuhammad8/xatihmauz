from django import forms

from .models import Ariza
from .text_utils import smart_money, smart_title_case


class ArizaForm(forms.ModelForm):
    sana = forms.DateField(
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
            "boshqa_sabab_matni",
        ]

    def clean(self):
        cleaned = super().clean()
        holat = cleaned.get("holat")
        if holat == "tayinlangan" and not cleaned.get("ajratilgan_summa"):
            self.add_error("ajratilgan_summa", "Tayinlangan holat uchun summa kiritilishi shart.")

        for maydon in ("mfy", "kucha", "fio"):
            if cleaned.get(maydon):
                cleaned[maydon] = smart_title_case(cleaned[maydon])
        if cleaned.get("ajratilgan_summa"):
            cleaned["ajratilgan_summa"] = smart_money(cleaned["ajratilgan_summa"])

        return cleaned
