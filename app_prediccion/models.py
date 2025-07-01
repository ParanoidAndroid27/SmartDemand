from django.db import models
from django.contrib.auth.models import User

class ExportacionReporte(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to='reportes_exportados/')
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.archivo.name}"
