import json

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from .decorators import RolTalabMixin, saxovat_talab
from .docx_export import ariza_docx_yaratish
from .forms import ArizaForm
from .models import Ariza
from .reasons import (
    BOSHQA_KOD,
    HOLATLAR,
    KATEGORIYALAR,
    RAD_SABABLARI,
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
    rol = profil.rol if profil else "saxovat"
    if rol == "xat":
        return redirect("xat:dashboard")
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
        "rad_sabab_kodlari": ariza.rad_sabab_kodlari,
        "boshqa_sabab_matni": ariza.boshqa_sabab_matni,
        "created_by": ariza.created_by.username,
        "can_edit": True,
    }


class DashboardView(RolTalabMixin, LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"
    kerakli_rol = "saxovat"

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
        return ctx


def _rad_sabab_kodlarini_olish(request, kategoriya):
    tanlangan = request.POST.getlist("rad_sabablari")
    ruxsat_etilgan = {k for (k, _nom, _matn) in sabablar_royxati(kategoriya)}
    return [k for k in tanlangan if k in ruxsat_etilgan]


@saxovat_talab
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


@saxovat_talab
def ariza_detail(request, pk):
    ariza = get_object_or_404(Ariza, pk=pk)
    if not _ariza_uchun_ruxsat(request, ariza):
        return HttpResponseForbidden("Sizga bu arizani ko'rishga ruxsat yo'q.")
    return JsonResponse(_ariza_dict(ariza))


@saxovat_talab
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


@saxovat_talab
@require_POST
def ariza_delete(request, pk):
    ariza = get_object_or_404(Ariza, pk=pk)
    if not _ariza_uchun_ruxsat(request, ariza):
        return HttpResponseForbidden("Sizga bu arizani o'chirishga ruxsat yo'q.")
    ariza.delete()
    messages.success(request, "Ariza o'chirildi.")
    return redirect("core:dashboard")


@saxovat_talab
def ariza_export(request, pk):
    ariza = get_object_or_404(Ariza, pk=pk)
    if not _ariza_uchun_ruxsat(request, ariza):
        return HttpResponseForbidden("Sizga bu arizani yuklab olishga ruxsat yo'q.")
    buffer, andoza_nomi = ariza_docx_yaratish(ariza)
    fayl_nomi = f"{ariza.fio}_{ariza.get_kategoriya_display()}_{ariza.get_holat_display()}.docx".replace(" ", "_")
    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response["Content-Disposition"] = f'attachment; filename="{fayl_nomi}"'
    return response
