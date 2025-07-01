from django.db import models
from app_cargar_productos.models import Producto
from app_entornos_trabajo.models import EntornoTrabajo

class AlertaStock(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='alertas')
    entorno_trabajo = models.ForeignKey(EntornoTrabajo, on_delete=models.CASCADE)
    umbral_minimo = models.PositiveIntegerField(
        default=10, 
        help_text="Cantidad mínima para que se muestre una alerta de stock."
    )
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Alerta para {self.producto.nombre} en {self.entorno_trabajo.nombre}"

    class Meta:
        verbose_name = "Alerta de Stock"
        verbose_name_plural = "Alertas de Stock"
        # Asegura que solo haya una configuración de alerta por producto en cada entorno
        unique_together = ('producto', 'entorno_trabajo')
