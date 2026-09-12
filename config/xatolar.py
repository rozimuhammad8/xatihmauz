# -*- coding: utf-8 -*-
"""Xato sahifalari.

DEBUG=False bo'lganda Django sukut bo'yicha inglizcha, bo'sh sahifalarni
ko'rsatadi. Xodim uchun bu tushunarsiz — shuning uchun har bir holat
o'zbekcha, nima bo'lganini aytadigan sahifa bilan almashtiriladi.

404 uchun maxsus sahifa yo'q — Django'ning o'z sukut 404 sahifasi ishlatiladi.
"""
from django.shortcuts import render

MATNLAR = {
    400: ("So'rov noto'g'ri", "Yuborilgan ma'lumot tushunarsiz bo'ldi. Sahifani yangilab, qaytadan urinib ko'ring."),
    403: ("Ruxsat yo'q", "Sizda bu bo'limga kirish huquqi yo'q. Boshqa rol bilan kirgan bo'lishingiz mumkin."),
    500: ("Serverda xatolik", "Kutilmagan xatolik yuz berdi. Xatolik qayd etildi — administratorga xabar bering."),
}


def _javob(request, kod, exception=None):
    sarlavha, izoh = MATNLAR[kod]
    return render(
        request, "xato.html",
        {"kod": kod, "sarlavha": sarlavha, "izoh": izoh},
        status=kod,
    )


def xato_400(request, exception=None):
    return _javob(request, 400, exception)


def xato_403(request, exception=None):
    return _javob(request, 403, exception)


def xato_500(request):
    return _javob(request, 500)
