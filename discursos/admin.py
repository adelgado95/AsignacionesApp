from django.contrib import admin

from .models import DiscursoPublico


@admin.register(DiscursoPublico)
class DiscursoPublicoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'nombre', 'congregacion', 'contacto', 'cancion')
    list_filter = ('fecha', 'congregacion')
    search_fields = ('nombre', 'congregacion', 'contacto')
    date_hierarchy = 'fecha'
