from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import XodimProfil


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def xodim_profilini_yaratish(sender, instance, created, **kwargs):
    if created:
        XodimProfil.objects.get_or_create(user=instance)
