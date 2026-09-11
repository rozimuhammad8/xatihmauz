from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("create/", views.ariza_create, name="ariza_create"),
    path("<int:pk>/", views.ariza_detail, name="ariza_detail"),
    path("<int:pk>/edit/", views.ariza_edit, name="ariza_edit"),
    path("<int:pk>/delete/", views.ariza_delete, name="ariza_delete"),
    path("<int:pk>/export/", views.ariza_export, name="ariza_export"),
]
