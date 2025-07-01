from django.db import models
from django.contrib.auth.models import User
import uuid

def ruta_foto(instance, filename):
    return f'perfiles/{instance.user.username}/{filename}'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    foto_perfil = models.ImageField(upload_to=ruta_foto, null=True, blank=True)

    def __str__(self):
        return self.user.username


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
