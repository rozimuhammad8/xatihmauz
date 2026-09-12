# -*- coding: utf-8 -*-
"""DEBUG rejimidan qat'i nazar ishlaydigan 404 sahifasi.

Django'ning standart qoidasi: `settings.DEBUG = True` bo'lsa, `handler404`
(config/urls.py dagi) UMUMAN chaqirilmaydi — Django har doim o'zining
texnik (manzillar ro'yxati, SQL so'rovi ko'rsatilgan) sahifasini ko'rsatadi.
Buni handler404 orqali o'chirib bo'lmaydi.

Yechim — Django'ning ichki oqimidan foydalanish (django/core/handlers/base.py,
BaseHandler._get_response): view ichida Http404 ko'tarilsa (masalan
get_object_or_404), Django DEBUG tekshiruvidan OLDIN barcha middleware'larning
`process_exception` metodini chaqiradi. Shu middleware o'sha bosqichda ishga
tushib, javobni DEBUG holatiga qaramay qaytarib yuboradi.

Bu FAQAT view ICHIDA ko'tarilgan Http404'ni qamrab oladi. "Bunday manzil
umuman yo'q" holati (hech qanday URL naqshi mos kelmasa) BOSHQACHA ishlaydi —
u Django ichida middleware'ga yetib kelishdan oldin javobga aylantiriladi.
Shu sababli config/urls.py oxiriga alohida "hammasini tut" yo'nalishi
qo'shilgan — ikkalasi birga barcha 404 holatlarini qamrab oladi.
"""
from django.http import Http404

from .xatolar import xato_404


class Maxsus404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            return xato_404(request, exception)
        return None
