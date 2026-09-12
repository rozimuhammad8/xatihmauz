# -*- coding: utf-8 -*-
"""Xato sahifalari.

DEBUG=False bo'lganda Django sukut bo'yicha inglizcha, bo'sh sahifalarni
ko'rsatadi. Xodim uchun bu tushunarsiz — shuning uchun har bir holat
o'zbekcha, nima bo'lganini aytadigan sahifa bilan almashtiriladi.
"""
from django.http import HttpResponse
from django.shortcuts import render

MATNLAR = {
    400: ("So'rov noto'g'ri", "Yuborilgan ma'lumot tushunarsiz bo'ldi. Sahifani yangilab, qaytadan urinib ko'ring."),
    403: ("Ruxsat yo'q", "Sizda bu bo'limga kirish huquqi yo'q. Boshqa rol bilan kirgan bo'lishingiz mumkin."),
    500: ("Serverda xatolik", "Kutilmagan xatolik yuz berdi. Xatolik qayd etildi — administratorga xabar bering."),
}

# 404 shablon orqali emas, to'g'ridan-to'g'ri HttpResponse bilan qaytariladi
# (foydalanuvchi so'ragan aniq talab) — HTML shu yerda o'zi yozilgan.
XATO_404_HTML = """<!doctype html>
<html lang="uz">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>404 — Sahifa topilmadi</title>
<style>
  :root{
    --bg:#f6f7f9; --card:#fff; --text-1:#111827; --text-2:#6b7280;
    --border:#e5e7eb; --accent:#111827;
  }
  @media (prefers-color-scheme: dark){
    :root{ --bg:#0f1115; --card:#171a21; --text-1:#f3f4f6; --text-2:#9ca3af; --border:#262b36; --accent:#f3f4f6; }
  }
  *{box-sizing:border-box}
  body{
    margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center;
    padding:24px; background:var(--bg); color:var(--text-1);
    font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
  }
  .card{
    width:100%; max-width:460px; background:var(--card); border:1px solid var(--border);
    border-radius:16px; padding:32px; text-align:center;
    box-shadow:0 1px 3px rgba(0,0,0,.06);
  }
  .kod{font-size:52px; font-weight:700; letter-spacing:-.03em; line-height:1; margin:0}
  h1{font-size:18px; margin:14px 0 8px}
  p{color:var(--text-2); font-size:14px; line-height:1.6; margin:0 0 22px}
  a{
    display:inline-block; padding:10px 18px; border-radius:9px; text-decoration:none;
    background:var(--accent); color:var(--card); font-size:14px; font-weight:600;
  }
</style>
</head>
<body>
  <div class="card">
    <p class="kod">404</p>
    <h1>Sahifa topilmadi</h1>
    <p>Adashib qoldingiz yoki buzmoqchisiz... Ortga qayting.</p>
    <a href="/">Bosh sahifaga qaytish</a>
  </div>
</body>
</html>
"""


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


def xato_404(request, exception=None):
    return HttpResponse(XATO_404_HTML, status=404)


def xato_500(request):
    return _javob(request, 500)
