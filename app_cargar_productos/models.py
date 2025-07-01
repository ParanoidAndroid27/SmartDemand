# app_cargar_productos/models.py

from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=255)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.TextField(blank=True)
    stock = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    destacado = models.BooleanField(default=False, help_text="Marcar para que aparezca en la página principal")
    entorno = models.ForeignKey(
        'app_entornos_trabajo.EntornoTrabajo',  # Usar cadena para la relación
        on_delete=models.CASCADE, # O SET_NULL si prefieres no borrar productos al borrar entorno
        related_name='productos',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-fecha_registro']

    def __str__(self):
        return self.nombre
