import json
from datetime import date

from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.decorators import xat_talab

from .docx_generator import build_letter_document, format_money, safe_filename, to_title_case
from .letter_text import build_preview
from .models import TEMPLATE_CHOICES, TEMPLATES_WITHOUT_ARIZA_INFO, Xat

XAT_FROM = [
    ("Prezidentga ishonch telefoni", "O‘zbekiston Respublikasi Prezidentiga ishonch telefoni"),
    ("Prezidentga veb-sayt", "O‘zbekiston Respublikasi Prezidentiga veb-sayt"),
    ("Prezidentga Xalq qabulxonasi", "O‘zbekiston Respublikasi Prezidentiga Xalq qabulxonasi"),
    ("Prokuraturaga murojaat.gov.uz", "O‘zbekiston Respublikasi Andijon tuman prokuraturasiga murojaat.gov.uz"),
    ("Prokuraturaga yozma", "O‘zbekiston Respublikasi Andijon tuman prokuraturasiga yozma murojaat"),
    ("Adliya Vazirligi murojaat.gov.uz", "O‘zbekiston Respublikasi Adliya vazirligiga murojaat.gov.uz yozma murojaat"),
    ("Adliya Vazirligi yozma", "O‘zbekiston Respublikasi Adliya vazirligiga yozma murojaat"),
    ("Davlat xavfsizlik murojaat.gov.uz", "O‘zbekiston Respublikasi Davlat xavfsizlik xizmatiga murojaat.gov.uz yozma murojaat"),
    ("Davlat xavfsizlik yozma", "O‘zbekiston Respublikasi Davlat xavfsizlik xizmatiga yozma murojaat"),
    ("Tuman hokimi shaxsiy qabuli", "Andijon viloyati, Andijon tumani hokimining shaxsiy qabul"),
    ("Tuman hokimi sayyor qabuli", "O‘zbekiston Respublikasi Andijon viloyati, Andijon tuman hokimining sayyor qabuli"),
    ("Agentlik Direktori Sayyor Qabuli", "O‘zbekiston Respublikasi Prezident huzuridagi Ijtimoiy himoya milliy Agentligi Andijon viloyat boshqarmasi Andijon tuman \"Inson\" Ijtimoiy xizmatlar markazi Direktorining sayyor qabuli"),
    ("Agentlik Ishonch telefoni", "O‘zbekiston Respublikasi Prezident huzuridagi Ijtimoiy himoya milliy Agentligi Andijon viloyat boshqarmasi Andijon tuman \"Inson\" Ijtimoiy xizmatlar markazi ishonch telefoni"),
]


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _validate_payload(payload):
    errors = []
    template = payload.get("template", "rad")

    for key, msg in [
        ("fio", "F.I.O kiriting!"),
        ("mfyNomi", "MFY nomini kiriting!"),
        ("street", "Ko'cha nomini kiriting!"),
        ("murojaatfrom", "Murojaat manbasini tanlang!"),
        ("murojaatVaqti", "Murojaat sanasini tanlang!"),
        ("murojaatRaqami", "Murojaat raqamini kiriting!"),
    ]:
        if not payload.get(key):
            errors.append(msg)

    if template not in TEMPLATES_WITHOUT_ARIZA_INFO:
        if not payload.get("arizaVaqti"):
            errors.append("Ariza sanasini tanlang!")
        if not payload.get("arizaID"):
            errors.append("Ariza raqamini (ID) kiriting!")
        if not payload.get("arizaMaqsadi"):
            errors.append("Ariza maqsadini tanlang!")

    if template == "rad":
        rad = payload.get("radSabablari") or {}
        has_reason = (
            rad.get("uydaEmasRad")
            or rad.get("norasmiyRad")
            or (rad.get("uyRad") and len(rad["uyRad"]) > 0)
            or (rad.get("avtoRad") and len(rad["avtoRad"]) > 0)
            or (rad.get("rasmiyRad") and len(rad["rasmiyRad"]) > 0)
        )
        if not has_reason:
            errors.append("Kamida bitta rad etish sababini tanlang!")

    if template == "tasdiqlandi":
        tasdiq = payload.get("tasdiqMalumotlari") or {}
        for key, msg in [
            ("tasdiqSanasi", "Tasdiqlash sanasini kiriting!"),
            ("tolovSanasi", "To'lov sanasini kiriting!"),
            ("xsobraqam", "Hisob raqamini kiriting!"),
            ("tolovSum", "To'lov summasini kiriting!"),
        ]:
            if not tasdiq.get(key):
                errors.append(msg)

    return errors


def _clean_name(value):
    """Ortiqcha probellarni yig'ishtirib, so'zlarning bosh harflarini to'g'ri
    ko'rinishga keltiradi (fio/mfy_nomi/street/uyManzil/avtoModel kabi erkin
    matnli maydonlar uchun)."""
    value = " ".join((value or "").split())
    return to_title_case(value)


def _normalize_rad_sabablari(rad):
    """uyManzil/avtoModel kabi erkin matnli maydonlarni bir xil, to'g'ri
    ko'rinishga keltiradi (docx_generator bu qiymatlarni o'zgarishsiz ishlatadi,
    shuning uchun saqlashdan oldin shu yerda tozalanadi)."""
    if not rad:
        return rad
    for item in rad.get("uyRad") or []:
        if item.get("uyManzil"):
            item["uyManzil"] = _clean_name(item["uyManzil"])
    for item in rad.get("avtoRad") or []:
        if item.get("avtoModel"):
            item["avtoModel"] = _clean_name(item["avtoModel"])
    return rad


def _apply_payload(xat, payload):
    template = payload.get("template", "rad")
    tasdiq = payload.get("tasdiqMalumotlari") or {}

    xat.template = template
    xat.fio = _clean_name(payload.get("fio", ""))
    xat.mfy_nomi = _clean_name(payload.get("mfyNomi", ""))
    xat.street = _clean_name(payload.get("street", ""))
    xat.murojaatfrom = payload.get("murojaatfrom", "")
    xat.murojaat_raqami = (payload.get("murojaatRaqami") or "").strip()
    xat.murojaat_vaqti = _parse_date(payload.get("murojaatVaqti"))
    xat.ariza_maqsadi = payload.get("arizaMaqsadi", "")
    xat.ariza_vaqti = _parse_date(payload.get("arizaVaqti"))
    xat.ariza_id = (payload.get("arizaID") or "").strip()
    xat.is_qayta = bool(payload.get("isQayta"))

    xat.rad_sabablari = _normalize_rad_sabablari(payload.get("radSabablari") or {}) if template == "rad" else {}
    xat.tasdiq_sanasi = tasdiq.get("tasdiqSanasi", "") if template == "tasdiqlandi" else ""
    xat.tolov_sanasi = tasdiq.get("tolovSanasi", "") if template == "tasdiqlandi" else ""
    xat.tolov_sum = format_money(tasdiq.get("tolovSum", "")) if template == "tasdiqlandi" else ""
    xat.xsobraqam = tasdiq.get("xsobraqam", "") if template == "tasdiqlandi" else ""
    xat.tayinlash_qoshimcha = payload.get("tayinlashQoshimcha", "") if template == "tayinlandi" else ""
    xat.qoshimcha_malumot = payload.get("qoshimchaMalumot", "") if template == "muddat" else ""


def _form_context(request):
    return {
        "template_choices": TEMPLATE_CHOICES,
        "xat_from": XAT_FROM,
    }


@xat_talab
def dashboard(request):
    base_qs = Xat.objects.select_related("created_by").all()
    if not request.user.is_superuser:
        base_qs = base_qs.filter(created_by=request.user)
    xatlar = base_qs

    search = request.GET.get("q", "").strip()
    if search:
        from django.db.models import Q
        xatlar = xatlar.filter(
            Q(fio__icontains=search)
            | Q(mfy_nomi__icontains=search)
            | Q(street__icontains=search)
            | Q(murojaat_raqami__icontains=search)
        )

    template_filter = request.GET.get("template", "")
    if template_filter:
        xatlar = xatlar.filter(template=template_filter)

    from_date = _parse_date(request.GET.get("from", ""))
    if from_date:
        xatlar = xatlar.filter(murojaat_vaqti__gte=from_date)
    to_date = _parse_date(request.GET.get("to", ""))
    if to_date:
        xatlar = xatlar.filter(murojaat_vaqti__lte=to_date)

    paginator = Paginator(xatlar, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    template_stats = [
        {"kod": kod, "nom": nom, "soni": base_qs.filter(template=kod).count()}
        for kod, nom in TEMPLATE_CHOICES
    ]

    ctx = {
        "page_obj": page_obj,
        "template_choices": TEMPLATE_CHOICES,
        "search": search,
        "template_filter": template_filter,
        "from_date": request.GET.get("from", ""),
        "to_date": request.GET.get("to", ""),
        "jami": base_qs.count(),
        "template_stats": template_stats,
    }
    return render(request, "xat/dashboard.html", ctx)


@xat_talab
def xat_create_page(request):
    ctx = _form_context(request)
    ctx["is_edit"] = False
    ctx["xat_id"] = None
    ctx["xat_json"] = "null"
    return render(request, "xat/create.html", ctx)


@xat_talab
@require_POST
def xat_create(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"success": False, "error": "Noto'g'ri so'rov formati"}, status=400)

    errors = _validate_payload(payload)
    if errors:
        return JsonResponse({"success": False, "errors": errors}, status=400)

    xat = Xat(created_by=request.user)
    _apply_payload(xat, payload)
    xat.save()

    return JsonResponse({"success": True, "id": xat.id, "redirect": reverse("xat:dashboard")})


def _xat_uchun_ruxsat(request, xat):
    return request.user.is_superuser or xat.created_by_id == request.user.id


@xat_talab
def xat_edit_page(request, pk):
    xat = get_object_or_404(Xat, pk=pk)
    if not _xat_uchun_ruxsat(request, xat):
        return HttpResponseForbidden("Sizga bu xatni ko'rishga ruxsat yo'q.")
    ctx = _form_context(request)
    ctx["is_edit"] = True
    ctx["xat_id"] = xat.id
    ctx["xat_json"] = json.dumps(xat.to_letter_dict(), ensure_ascii=False)
    return render(request, "xat/create.html", ctx)


@xat_talab
@require_POST
def xat_edit(request, pk):
    xat = get_object_or_404(Xat, pk=pk)
    if not _xat_uchun_ruxsat(request, xat):
        return HttpResponseForbidden("Sizga bu xatni tahrirlashga ruxsat yo'q.")

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"success": False, "error": "Noto'g'ri so'rov formati"}, status=400)

    errors = _validate_payload(payload)
    if errors:
        return JsonResponse({"success": False, "errors": errors}, status=400)

    _apply_payload(xat, payload)
    xat.save()

    return JsonResponse({"success": True, "id": xat.id, "redirect": reverse("xat:dashboard")})


@xat_talab
@require_POST
def xat_delete(request, pk):
    xat = get_object_or_404(Xat, pk=pk)
    if not _xat_uchun_ruxsat(request, xat):
        return HttpResponseForbidden("Sizga bu xatni o'chirishga ruxsat yo'q.")
    xat.delete()
    return JsonResponse({"success": True})


@xat_talab
def xat_export(request, pk):
    xat = get_object_or_404(Xat, pk=pk)
    if not _xat_uchun_ruxsat(request, xat):
        return HttpResponseForbidden("Sizga bu xatni yuklab olishga ruxsat yo'q.")
    letter = xat.to_letter_dict()
    buffer = build_letter_document(letter)
    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response["Content-Disposition"] = f'attachment; filename="{safe_filename(letter)}"'
    return response


@xat_talab
def xat_preview(request, pk):
    xat = get_object_or_404(Xat, pk=pk)
    if not _xat_uchun_ruxsat(request, xat):
        return HttpResponseForbidden("Sizga bu xatni ko'rishga ruxsat yo'q.")
    letter = xat.to_letter_dict()
    pochta_html, murojaat_html, paragraphs, has_signature = build_preview(letter)
    ctx = {
        "xat": xat,
        "pochta_html": pochta_html,
        "murojaat_html": murojaat_html,
        "paragraphs": paragraphs,
        "has_signature": has_signature,
        "tashkilot_nomi": letter.get("tashkilotNomi", ""),
        "tashkilot_rahbar": letter.get("tashkilotRahbar", ""),
        "ijrochi": letter.get("ijrochi", ""),
    }
    return render(request, "xat/preview.html", ctx)
