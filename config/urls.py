from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path

from core import views as core_views

from .xatolar import xato_404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.root_redirect, name='root'),
    path('login/', core_views.KirishView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('ariza/', include('core.urls')),
    path('reestr/', include('reestr.urls')),
]

# Xodim uchun tushunarli o'zbekcha xato sahifalari (config/xatolar.py).
# 400/403/500 uchun handler* ishlatiladi — bular faqat DEBUG=False bo'lganda
# chaqiriladi (DEBUG=True bo'lsa Django'ning o'z batafsil sahifasi ko'proq
# foyda beradi, shuning uchun ular qasddan tegilmagan).
#
# 404 boshqacha: Django DEBUG=True bo'lsa handler404'ni UMUMAN chaqirmaydi
# (bu handler'lar ichida yagona bunday cheklovga ega bo'lgani). Shu sababli
# custom 404 ikki YO'LDAN ta'minlanadi (config/middleware.py da tushuntirilgan):
#   1) view ichida ko'tarilgan Http404 — Maxsus404Middleware ushlaydi
#   2) hech qanday manzil mos kelmagan holat — pastdagi "hammasini tut"
#      yo'nalishi orqali, DEBUG holatidan qat'i nazar.
# Shu ikkalasi ham handler404'dan MUSTAQIL ishlaydi, shuning uchun bu yerda
# handler404 belgilanmagan.
handler400 = "config.xatolar.xato_400"
handler403 = "config.xatolar.xato_403"
handler500 = "config.xatolar.xato_500"

urlpatterns += [
    re_path(r'^.*$', xato_404),
]
