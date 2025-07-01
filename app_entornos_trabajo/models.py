# Create your models here.
from django.db import models
from django.conf import settings

class EntornoTrabajo(models.Model):
    nombre = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Nombre opcional para identificar el entorno de trabajo."
    )
    administrador = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='entorno_administrado',
        help_text="Usuario que administra este entorno de trabajo."
    )
    colaboradores = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='entornos_donde_colabora',
        blank=True,
        help_text="Usuarios que colaboran en este entorno de trabajo."
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora en que se creó el entorno."
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de la última actualización del entorno."
    )

    def __str__(self):
        if self.nombre:
            return f"Entorno '{self.nombre}' (Admin: {self.administrador.username})"
        return f"Entorno de {self.administrador.username}"

    class Meta:
        verbose_name = "Entorno de Trabajo"
        verbose_name_plural = "Entornos de Trabajo"
        ordering = ['-fecha_creacion']
