from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.root_redirect, name='root'),
    path('login/', core_views.KirishView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('ariza/', include('core.urls')),
    path('reestr/', include('reestr.urls')),
]

# Xodim uchun tushunarli o'zbekcha xato sahifalari (config/xatolar.py).
# Faqat DEBUG=False bo'lganda ishlaydi — ishlab chiqishda Django'ning
# batafsil xato sahifasi foydaliroq. 404 uchun maxsus sahifa yo'q — Django'ning
# o'z sukut 404 sahifasi ishlatiladi.
handler400 = "config.xatolar.xato_400"
handler403 = "config.xatolar.xato_403"
handler500 = "config.xatolar.xato_500"
