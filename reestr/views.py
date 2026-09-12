import json
import logging

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.decorators import reestr_talab
from core.text_utils import raqamli_matn, sanani_oqish, tozalangan_matn

from .docx_generator import format_money, safe_filename, to_title_case
from .docx_templates import render_letter
from .letter_text import build_preview
from .models import TEMPLATE_CHOICES, TEMPLATES_WITHOUT_ARIZA_INFO, Xat

logger = logging.getLogger(__name__)

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
    """Sanani turli formatda qabul qiladi (2026-07-16, 16.07.2026, ...).
    Tushunib bo'lmasa None."""
    return sanani_oqish(value)


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

    # murojaat_vaqti bazada NOT NULL. Sana turli formatda kelishi mumkin
    # (_parse_date ularni o'zi tushunadi); umuman tushunib bo'lmasa, saqlashda
    # IntegrityError bilan 500-xatolik chiqmasligi uchun shu yerda ushlanadi.
    if payload.get("murojaatVaqti") and _parse_date(payload["murojaatVaqti"]) is None:
        errors.append("Murojaat sanasini tushunib bo'lmadi (masalan: 16.07.2026)!")

    if template not in TEMPLATES_WITHOUT_ARIZA_INFO:
        if not payload.get("arizaVaqti"):
            errors.append("Ariza sanasini tanlang!")
        elif _parse_date(payload["arizaVaqti"]) is None:
            errors.append("Ariza sanasini tushunib bo'lmadi (masalan: 03.06.2026)!")
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
            ("hisobRaqami", "Hisob raqamini kiriting!"),
            ("tolovSum", "To'lov summasini kiriting!"),
        ]:
            if not tasdiq.get(key):
                errors.append(msg)

    return errors


def _clean_name(value):
    """Erkin matnli maydonlarni (fio/mfy_nomi/street/uyManzil/avtoModel)
    bir xil ko'rinishga keltiradi: kirilcha -> lotincha, ortiqcha probellar
    olib tashlanadi, so'z boshlari katta harf.

    Kirilchani brauzerdagi JS ham o'giradi, lekin server unga ishonmaydi —
    so'rov to'g'ridan-to'g'ri (kengaytma yoki skript orqali) kelishi mumkin.
    """
    return to_title_case(tozalangan_matn(value))


def _normalize_rad_sabablari(rad):
    """uyManzil/avtoModel kabi erkin matnli maydonlarni bir xil, to'g'ri
    ko'rinishga keltiradi (docx_generator bu qiymatlarni o'zgarishsiz ishlatadi,
    shuning uchun saqlashdan oldin shu yerda tozalanadi)."""
    if not rad:
        return rad
    for item in rad.get("uyRad") or []:
        item["uyManzil"] = _clean_name(item.get("uyManzil"))
        item["uyKadastr"] = raqamli_matn(item.get("uyKadastr"))
    for item in rad.get("avtoRad") or []:
        item["avtoModel"] = _clean_name(item.get("avtoModel"))
        item["avtoRaqam"] = raqamli_matn(item.get("avtoRaqam")).upper()
        item["avtoYil"] = raqamli_matn(item.get("avtoYil"))
    for item in rad.get("rasmiyRad") or []:
        item["egasi"] = _clean_name(item.get("egasi"))
        item["tashkilot"] = tozalangan_matn(item.get("tashkilot"))
        item["davri"] = tozalangan_matn(item.get("davri"))
    return rad


def _apply_payload(xat, payload):
    template = payload.get("template", "rad")
    tasdiq = payload.get("tasdiqMalumotlari") or {}

    xat.template = template
    xat.fio = _clean_name(payload.get("fio", ""))
    xat.mfy_nomi = _clean_name(payload.get("mfyNomi", ""))
    xat.street = _clean_name(payload.get("street", ""))
    xat.murojaatfrom = tozalangan_matn(payload.get("murojaatfrom", ""))
    xat.murojaat_raqami = tozalangan_matn(payload.get("murojaatRaqami"))
    xat.murojaat_vaqti = _parse_date(payload.get("murojaatVaqti"))
    xat.ariza_maqsadi = tozalangan_matn(payload.get("arizaMaqsadi", "")).lower()
    xat.ariza_vaqti = _parse_date(payload.get("arizaVaqti"))
    xat.ariza_id = raqamli_matn(payload.get("arizaID"))
    xat.is_qayta = bool(payload.get("isQayta"))

    xat.rad_sabablari = _normalize_rad_sabablari(payload.get("radSabablari") or {}) if template == "rad" else {}
    xat.tasdiq_sanasi = tozalangan_matn(tasdiq.get("tasdiqSanasi")) if template == "tasdiqlandi" else ""
    xat.tolov_sanasi = tozalangan_matn(tasdiq.get("tolovSanasi")) if template == "tasdiqlandi" else ""
    xat.tolov_sum = format_money(tasdiq.get("tolovSum", "")) if template == "tasdiqlandi" else ""
    xat.hisob_raqami = raqamli_matn(tasdiq.get("hisobRaqami")) if template == "tasdiqlandi" else ""
    xat.tayinlash_qoshimcha = tozalangan_matn(payload.get("tayinlashQoshimcha")) if template == "tayinlandi" else ""
    xat.qoshimcha_malumot = tozalangan_matn(payload.get("qoshimchaMalumot")) if template == "muddat" else ""


def _form_context(request):
    return {
        "template_choices": TEMPLATE_CHOICES,
        "xat_from": XAT_FROM,
    }


@reestr_talab
def dashboard(request):
    base_qs = Xat.objects.select_related("created_by").all()
    if not request.user.is_superuser:
        base_qs = base_qs.filter(created_by=request.user)
    xatlar = base_qs

    search = request.GET.get("q", "").strip()
    if search:
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

    # Bitta GROUP BY so'rovi — ilgari har bir shablon turi uchun alohida
    # COUNT so'rovi ketardi.
    sanoq = dict(
        base_qs.values_list("template").annotate(soni=Count("id")).values_list("template", "soni")
    )
    template_stats = [
        {"kod": kod, "nom": nom, "soni": sanoq.get(kod, 0)}
        for kod, nom in TEMPLATE_CHOICES
    ]

    ctx = {
        "page_obj": page_obj,
        "template_choices": TEMPLATE_CHOICES,
        "search": search,
        "template_filter": template_filter,
        "from_date": request.GET.get("from", ""),
        "to_date": request.GET.get("to", ""),
        "jami": sum(sanoq.values()),
        "template_stats": template_stats,
    }
    return render(request, "reestr/dashboard.html", ctx)


@reestr_talab
def xat_create_page(request):
    ctx = _form_context(request)
    ctx["is_edit"] = False
    ctx["xat_id"] = None
    ctx["xat_json"] = "null"
    return render(request, "reestr/create.html", ctx)


@reestr_talab
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
    # Ariza (core) tizimidagi Ariza.tuman bilan bir xil: xodim kiritmaydi,
    # o'z profilidagi tuman avtomatik yoziladi (docx hujjatning boshidagi
    # qabul qiluvchi blokida ishlatiladi).
    profil = getattr(request.user, "profil", None)
    xat.tuman = profil.tuman if profil else ""
    xat.save()

    return JsonResponse({"success": True, "id": xat.id, "redirect": reverse("reestr:dashboard")})


def _xat_uchun_ruxsat(request, xat):
    return request.user.is_superuser or xat.created_by_id == request.user.id


@reestr_talab
def xat_edit_page(request, pk):
    xat = get_object_or_404(Xat, pk=pk)
    if not _xat_uchun_ruxsat(request, xat):
        return HttpResponseForbidden("Sizga bu xatni ko'rishga ruxsat yo'q.")
    ctx = _form_context(request)
    ctx["is_edit"] = True
    ctx["xat_id"] = xat.id
    ctx["xat_json"] = json.dumps(xat.to_letter_dict(), ensure_ascii=False)
    return render(request, "reestr/create.html", ctx)


@reestr_talab
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

    # tuman qayta yozilmaydi (Ariza tizimidagi ariza_edit bilan bir xil) —
    # tahrirlovchi boshqa xodim yoki superuser bo'lishi mumkin, letter yaratgan
    # xodimning tumani saqlanib qolishi kerak.
    _apply_payload(xat, payload)
    xat.save()

    return JsonResponse({"success": True, "id": xat.id, "redirect": reverse("reestr:dashboard")})


@reestr_talab
@require_POST
def xat_delete(request, pk):
    xat = get_object_or_404(Xat, pk=pk)
    if not _xat_uchun_ruxsat(request, xat):
        return HttpResponseForbidden("Sizga bu xatni o'chirishga ruxsat yo'q.")
    xat.delete()
    return JsonResponse({"success": True})


@reestr_talab
def xat_export(request, pk):
    xat = get_object_or_404(Xat, pk=pk)
    if not _xat_uchun_ruxsat(request, xat):
        return HttpResponseForbidden("Sizga bu xatni yuklab olishga ruxsat yo'q.")
    letter = xat.to_letter_dict()
    # Shablons/reeystr/*.docx dan o'qiladi; shablon topilmasa docx_generator'ga
    # qaytadi (qarang: docx_templates.render_letter). Shunday bo'lsa ham
    # hujjat yasashda kutilmagan xatolik chiqsa, foydalanuvchi oq sahifa
    # emas, tushunarli xabar ko'rishi kerak.
    try:
        buffer = render_letter(letter)
    except Exception:
        logger.exception("Xat eksportida xatolik (xat id=%s)", xat.pk)
        messages.error(
            request,
            "Hujjatni yaratib bo'lmadi. Shablon fayli buzilgan bo'lishi mumkin — "
            "administratorga xabar bering.",
        )
        return redirect("reestr:dashboard")
    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response["Content-Disposition"] = f'attachment; filename="{safe_filename(letter)}"'
    return response


@reestr_talab
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
    return render(request, "reestr/preview.html", ctx)
