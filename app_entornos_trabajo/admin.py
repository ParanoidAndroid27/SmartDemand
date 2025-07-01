# filepath: c:\SmartDemand\app_entornos_trabajo\admin.py
from django.contrib import admin
from .models import EntornoTrabajo

@admin.register(EntornoTrabajo)
class EntornoTrabajoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'administrador', 'fecha_creacion', 'fecha_actualizacion')
    list_filter = ('fecha_creacion', 'fecha_actualizacion', 'administrador')
    search_fields = ('nombre', 'administrador__username', 'colaboradores__username')
    filter_horizontal = ('colaboradores',) # Hace más amigable la selección de muchos a muchos
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

    fieldsets = (
        (None, {
            'fields': ('nombre', 'administrador')
        }),
        ('Colaboradores', {
            'fields': ('colaboradores',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',) # Para que esta sección aparezca colapsada por defecto
        }),
    )

# Otra forma de registrar, más simple si no necesitas mucha personalización:
# admin.site.register(EntornoTrabajo)