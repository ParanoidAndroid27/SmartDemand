from django.db import models
from app_cargar_productos.models import Producto
from django.contrib.auth.models import User

class VentaProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha_venta = models.DateField()
    cantidad_vendida = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-fecha_venta']

    def __str__(self):
        return f"{self.producto.nombre} - {self.fecha_venta} ({self.cantidad_vendida})"
