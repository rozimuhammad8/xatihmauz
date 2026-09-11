from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def _foydalanuvchi_roli(user):
    profil = getattr(user, "profil", None)
    return profil.rol if profil else "saxovat"


class RolTalabMixin:
    """Class-based view uchun: faqat kerakli_rol (yoki superuser) kira oladi."""

    kerakli_rol = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_superuser:
            if _foydalanuvchi_roli(request.user) != self.kerakli_rol:
                messages.error(request, "Sizga bu bo'limga kirish huquqi yo'q.")
                return redirect("root")
        return super().dispatch(request, *args, **kwargs)


def rol_talab(kerakli_rol):
    """Function-based view uchun: login + rol tekshiruvini birga qiladi."""

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_superuser and _foydalanuvchi_roli(request.user) != kerakli_rol:
                messages.error(request, "Sizga bu bo'limga kirish huquqi yo'q.")
                return redirect("root")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


saxovat_talab = rol_talab("saxovat")
xat_talab = rol_talab("xat")
