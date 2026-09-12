from django.urls import path

from . import views

app_name = "reestr"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("create/", views.xat_create_page, name="create_page"),
    path("create/save/", views.xat_create, name="create"),
    path("<int:pk>/edit/", views.xat_edit_page, name="edit_page"),
    path("<int:pk>/edit/save/", views.xat_edit, name="edit"),
    path("<int:pk>/delete/", views.xat_delete, name="delete"),
    path("<int:pk>/export/", views.xat_export, name="export"),
    path("<int:pk>/preview/", views.xat_preview, name="preview"),
]
