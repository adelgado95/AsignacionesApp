from django.contrib import admin

from .models import DiscursoPublico


@admin.register(DiscursoPublico)
class DiscursoPublicoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'titulo', 'nombre', 'congregacion', 'contacto', 'cancion')
    list_filter = ('fecha', 'congregacion')
    search_fields = ('titulo', 'nombre', 'congregacion', 'contacto')
    date_hierarchy = 'fecha'
