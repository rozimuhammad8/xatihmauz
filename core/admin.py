from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from .models import Ariza, Tashkilot, XodimProfil


@admin.register(Ariza)
class ArizaAdmin(admin.ModelAdmin):
    list_display = ("fio", "kategoriya", "holat", "tuman", "created_by", "created_at")
    list_filter = ("kategoriya", "holat", "tuman", "created_by")
    search_fields = ("fio", "mfy", "kucha", "murojaat_raqami", "ariza_raqami")


@admin.register(Tashkilot)
class TashkilotAdmin(admin.ModelAdmin):
    list_display = ("nomi", "rahbar")
    search_fields = ("nomi", "rahbar")


class XodimProfilInline(admin.StackedInline):
    model = XodimProfil
    can_delete = False
    verbose_name_plural = "Xodim profili (tuman)"


class UserAdmin(DefaultUserAdmin):
    inlines = (XodimProfilInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
