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
    path('xat/', include('xat.urls')),
]
