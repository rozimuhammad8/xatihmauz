from django.contrib import admin

from .models import Xat


@admin.register(Xat)
class XatAdmin(admin.ModelAdmin):
    list_display = ("fio", "template", "created_by", "created_at")
    list_filter = ("template", "created_by")
    search_fields = ("fio", "mfy_nomi", "street", "murojaat_raqami", "ariza_id")
