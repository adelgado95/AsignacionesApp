from django.contrib import admin

from .models import ProgramaPrivilegio


@admin.register(ProgramaPrivilegio)
class ProgramaPrivilegioAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'dia', 'presidente', 'oracion_inicio', 'oracion_final',
                    'entrada', 'auditorio', 'microfono1', 'microfono2', 'plataforma', 'audio', 'lector')
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)
    list_select_related = True

    @admin.display(description='Día')
    def dia(self, obj):
        return obj.get_dia()
