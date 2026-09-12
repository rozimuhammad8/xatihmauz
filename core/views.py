import json
import logging
import re

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from .decorators import RolTalabMixin, bosh_ijtimoiy_talab
from .docx_export import ShablonTopilmadi, ariza_docx_yaratish
from .xizmat_export import xizmat_docx_yaratish
from .forms import ArizaForm, XizmatHujjatiForm
from .models import Ariza, XizmatHujjati, XodimProfil
from .talabnoma import barcha_yordamlar, tashkilot_nomlari, yordamlar_xaritasi

logger = logging.getLogger(__name__)
from .reasons import (
    HOLATLAR,
    KATEGORIYALAR,
    TASHKILOTLAR,
    sabablar_royxati,
)


class KirishView(auth_views.LoginView):
    template_name = "core/login.html"
    redirect_authenticated_user = True


@login_required
def root_redirect(request):
    """Login qilgandan keyin foydalanuvchining roliga qarab tegishli dashboardga yo'naltiradi."""
    profil = getattr(request.user, "profil", None)
    rol = profil.rol if profil else XodimProfil.ROL_BOSH_IJTIMOIY
    if rol == XodimProfil.ROL_REESTR:
        return redirect("reestr:dashboard")
    return redirect("core:dashboard")


def _sabablar_json():
    natija = {}
    for kod, _nom in KATEGORIYALAR:
        natija[kod] = [
            {"kod": k, "nom": nom} for (k, nom, _matn) in sabablar_royxati(kod)
        ]
    return natija


def _ariza_dict(ariza):
    return {
        "id": ariza.id,
        "kategoriya": ariza.kategoriya,
        "holat": ariza.holat,
        "tuman": ariza.tuman,
        "mfy": ariza.mfy,
        "kucha": ariza.kucha,
        "fio": ariza.fio,
        "tashkilot": ariza.tashkilot,
        "sana": ariza.sana.isoformat() if ariza.sana else "",
        "murojaat_raqami": ariza.murojaat_raqami,
        "ariza_raqami": ariza.ariza_raqami,
        "ajratilgan_summa": ariza.ajratilgan_summa,
        "kollegal_qaror": ariza.kollegal_qaror,
        "rad_sabab_kodlari": ariza.rad_sabab_kodlari,
        "boshqa_sabab_matni": ariza.boshqa_sabab_matni,
        "created_by": ariza.created_by.username,
        "can_edit": True,
    }


class DashboardView(RolTalabMixin, LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"
    kerakli_rol = XodimProfil.ROL_BOSH_IJTIMOIY

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        arizalar = Ariza.objects.select_related("created_by").all()
        if not self.request.user.is_superuser:
            arizalar = arizalar.filter(created_by=self.request.user)
        ctx["arizalar"] = arizalar
        ctx["arizalar_json"] = json.dumps(
            [_ariza_dict(a) for a in arizalar], ensure_ascii=False
        )
        ctx["kategoriyalar"] = KATEGORIYALAR
        ctx["holatlar"] = HOLATLAR
        ctx["tashkilotlar"] = TASHKILOTLAR
        ctx["sabablar_json"] = json.dumps(_sabablar_json(), ensure_ascii=False)
        ctx["form"] = ArizaForm()
        ctx["tayinlangan_soni"] = sum(1 for a in arizalar if a.holat == "tayinlangan")
        ctx["rad_soni"] = sum(1 for a in arizalar if a.holat == "rad")
        profil = getattr(self.request.user, "profil", None)
        ctx["xodim_tuman"] = profil.tuman if profil else ""

        hujjatlar = XizmatHujjati.objects.select_related("created_by").all()
        if not self.request.user.is_superuser:
            hujjatlar = hujjatlar.filter(created_by=self.request.user)
        ctx["xizmat_hujjatlari"] = hujjatlar
        ctx["xizmat_json"] = json.dumps(
            [_xizmat_dict(h) for h in hujjatlar], ensure_ascii=False
        )
        ctx["xizmat_turlari"] = XizmatHujjati.TUR_CHOICES
        ctx["xizmat_form"] = XizmatHujjatiForm()

        # Talabnoma uchun VM 539-son qarori asosidagi tavsiyalar (core/talabnoma.py).
        # Maydonlar erkin matnni ham qabul qiladi — bu faqat taklif ro'yxati.
        ctx["talabnoma_tashkilotlari"] = tashkilot_nomlari(ctx["xodim_tuman"])
        ctx["talabnoma_yordamlari"] = barcha_yordamlar()
        ctx["talabnoma_xaritasi_json"] = json.dumps(
            yordamlar_xaritasi(ctx["xodim_tuman"]), ensure_ascii=False
        )
        return ctx


def _rad_sabab_kodlarini_olish(request, kategoriya):
    tanlangan = request.POST.getlist("rad_sabablari")
    ruxsat_etilgan = {k for (k, _nom, _matn) in sabablar_royxati(kategoriya)}
    return [k for k in tanlangan if k in ruxsat_etilgan]


@bosh_ijtimoiy_talab
@require_POST
def ariza_create(request):
    form = ArizaForm(request.POST)
    if form.is_valid():
        ariza = form.save(commit=False)
        ariza.created_by = request.user
        profil = getattr(request.user, "profil", None)
        ariza.tuman = profil.tuman if profil else ""
        if ariza.holat == "rad":
            ariza.rad_sabab_kodlari = _rad_sabab_kodlarini_olish(request, ariza.kategoriya)
            ariza.ajratilgan_summa = ""
            ariza.kollegal_qaror = ""
        else:
            ariza.rad_sabab_kodlari = []
            ariza.boshqa_sabab_matni = ""
        ariza.save()
        messages.success(request, "Ariza muvaffaqiyatli qo'shildi.")
    else:
        messages.error(request, "Formada xatolik bor: " + "; ".join(
            f"{f}: {', '.join(e)}" for f, e in form.errors.items()
        ))
    return redirect("core:dashboard")


def _ariza_uchun_ruxsat(request, ariza):
    return request.user.is_superuser or ariza.created_by_id == request.user.id


@bosh_ijtimoiy_talab
def ariza_detail(request, pk):
    ariza = get_object_or_404(Ariza, pk=pk)
    if not _ariza_uchun_ruxsat(request, ariza):
        return HttpResponseForbidden("Sizga bu arizani ko'rishga ruxsat yo'q.")
    return JsonResponse(_ariza_dict(ariza))


@bosh_ijtimoiy_talab
@require_POST
def ariza_edit(request, pk):
    ariza = get_object_or_404(Ariza, pk=pk)
    if not _ariza_uchun_ruxsat(request, ariza):
        return HttpResponseForbidden("Sizga bu arizani tahrirlashga ruxsat yo'q.")

    form = ArizaForm(request.POST, instance=ariza)
    if form.is_valid():
        ariza = form.save(commit=False)
        if ariza.holat == "rad":
            ariza.rad_sabab_kodlari = _rad_sabab_kodlarini_olish(request, ariza.kategoriya)
            ariza.ajratilgan_summa = ""
            ariza.kollegal_qaror = ""
        else:
            ariza.rad_sabab_kodlari = []
            ariza.boshqa_sabab_matni = ""
        ariza.save()
        messages.success(request, "Ariza muvaffaqiyatli tahrirlandi.")
    else:
        messages.error(request, "Formada xatolik bor: " + "; ".join(
            f"{f}: {', '.join(e)}" for f, e in form.errors.items()
        ))
    return redirect("core:dashboard")


@bosh_ijtimoiy_talab
@require_POST
def ariza_delete(request, pk):
    ariza = get_object_or_404(Ariza, pk=pk)
    if not _ariza_uchun_ruxsat(request, ariza):
        return HttpResponseForbidden("Sizga bu arizani o'chirishga ruxsat yo'q.")
    ariza.delete()
    messages.success(request, "Ariza o'chirildi.")
    return redirect("core:dashboard")


def _docx_javobi(buffer, fayl_nomi):
    """Tayyor .docx ni yuklab olinadigan javobga o'raydi. Fayl nomidagi
    Windows ruxsat bermaydigan belgilar olib tashlanadi."""
    xavfsiz_nom = re.sub(r'[\/:*?"<>|]+', "", fayl_nomi).replace(" ", "_").strip("_")
    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response["Content-Disposition"] = f'attachment; filename="{xavfsiz_nom or "hujjat.docx"}"'
    return response


@bosh_ijtimoiy_talab
def ariza_export(request, pk):
    ariza = get_object_or_404(Ariza, pk=pk)
    if not _ariza_uchun_ruxsat(request, ariza):
        return HttpResponseForbidden("Sizga bu arizani yuklab olishga ruxsat yo'q.")
    try:
        buffer, _andoza_nomi = ariza_docx_yaratish(ariza)
    except ShablonTopilmadi as xato:
        messages.error(request, str(xato))
        return redirect("core:dashboard")
    except Exception:
        logger.exception("Ariza eksportida xatolik (ariza id=%s)", ariza.pk)
        messages.error(
            request,
            "Hujjatni yaratib bo'lmadi. Shablon fayli buzilgan bo'lishi mumkin — "
            "administratorga xabar bering.",
        )
        return redirect("core:dashboard")

    nom = f"{ariza.fio}_{ariza.get_kategoriya_display()}_{ariza.get_holat_display()}.docx"
    return _docx_javobi(buffer, nom)


# ============================================================
# XIZMAT HUJJATLARI (bildirgi / ogohlantirish / talabnoma)
# Arizalardan alohida: fuqaroga emas, xodim yoki boshqa tashkilotga
# yoziladi. Ruxsat qoidalari arizalarnikiga to'liq mos.
# ============================================================
def _xizmat_dict(hujjat):
    return {
        "id": hujjat.id,
        # Manzil shu yerda hosil qilinadi — shablondagi JS uni qattiq
        # yozib qo'ymasligi uchun (URL tuzilishi o'zgarsa ham ishlayveradi).
        "edit_url": reverse("core:xizmat_edit", args=[hujjat.id]),
        "turi": hujjat.turi,
        "mahalla": hujjat.mahalla,
        "xodim_fio": hujjat.xodim_fio,
        "ish_boshlagan_sana": hujjat.ish_boshlagan_sana.isoformat() if hujjat.ish_boshlagan_sana else "",
        "buzilish_sanasi": hujjat.buzilish_sanasi,
        "ish_vaqti": hujjat.ish_vaqti,
        "yigilish_sanasi": hujjat.yigilish_sanasi,
        "rahbar_lavozimi": hujjat.rahbar_lavozimi,
        "rahbar_fio": hujjat.rahbar_fio,
        "qabul_qiluvchi": hujjat.qabul_qiluvchi,
        "fuqaro_fio": hujjat.fuqaro_fio,
        "fuqaro_tugilgan_sana": hujjat.fuqaro_tugilgan_sana.isoformat() if hujjat.fuqaro_tugilgan_sana else "",
        "yordam_turi": hujjat.yordam_turi,
    }


def _xizmat_uchun_ruxsat(request, hujjat):
    return request.user.is_superuser or hujjat.created_by_id == request.user.id


@bosh_ijtimoiy_talab
@require_POST
def xizmat_create(request):
    form = XizmatHujjatiForm(request.POST)
    if form.is_valid():
        hujjat = form.save(commit=False)
        hujjat.created_by = request.user
        hujjat.save()
        messages.success(request, "Xizmat hujjati qo'shildi.")
    else:
        messages.error(request, "Formada xatolik bor: " + "; ".join(
            f"{form.fields[f].label if f in form.fields else f}: {', '.join(e)}"
            for f, e in form.errors.items()
        ))
    return redirect("core:dashboard")


@bosh_ijtimoiy_talab
def xizmat_detail(request, pk):
    hujjat = get_object_or_404(XizmatHujjati, pk=pk)
    if not _xizmat_uchun_ruxsat(request, hujjat):
        return HttpResponseForbidden("Sizga bu hujjatni ko'rishga ruxsat yo'q.")
    return JsonResponse(_xizmat_dict(hujjat))


@bosh_ijtimoiy_talab
@require_POST
def xizmat_edit(request, pk):
    hujjat = get_object_or_404(XizmatHujjati, pk=pk)
    if not _xizmat_uchun_ruxsat(request, hujjat):
        return HttpResponseForbidden("Sizga bu hujjatni tahrirlashga ruxsat yo'q.")
    form = XizmatHujjatiForm(request.POST, instance=hujjat)
    if form.is_valid():
        form.save()
        messages.success(request, "Xizmat hujjati tahrirlandi.")
    else:
        messages.error(request, "Formada xatolik bor: " + "; ".join(
            f"{form.fields[f].label if f in form.fields else f}: {', '.join(e)}"
            for f, e in form.errors.items()
        ))
    return redirect("core:dashboard")


@bosh_ijtimoiy_talab
@require_POST
def xizmat_delete(request, pk):
    hujjat = get_object_or_404(XizmatHujjati, pk=pk)
    if not _xizmat_uchun_ruxsat(request, hujjat):
        return HttpResponseForbidden("Sizga bu hujjatni o'chirishga ruxsat yo'q.")
    hujjat.delete()
    messages.success(request, "Xizmat hujjati o'chirildi.")
    return redirect("core:dashboard")


@bosh_ijtimoiy_talab
def xizmat_export(request, pk):
    hujjat = get_object_or_404(XizmatHujjati, pk=pk)
    if not _xizmat_uchun_ruxsat(request, hujjat):
        return HttpResponseForbidden("Sizga bu hujjatni yuklab olishga ruxsat yo'q.")
    try:
        buffer, _shablon = xizmat_docx_yaratish(hujjat)
    except ShablonTopilmadi as xato:
        messages.error(request, str(xato))
        return redirect("core:dashboard")
    except Exception:
        logger.exception("Xizmat hujjati eksportida xatolik (id=%s)", hujjat.pk)
        messages.error(
            request,
            "Hujjatni yaratib bo'lmadi. Shablon fayli buzilgan bo'lishi mumkin — "
            "administratorga xabar bering.",
        )
        return redirect("core:dashboard")

    return _docx_javobi(buffer, f"{hujjat.get_turi_display()}_{hujjat.xodim_fio}.docx")
