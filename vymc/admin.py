from django.contrib import admin, messages

from .models import ParteVyMC, SemanaVyMC

# Estructura habitual del programa: (numero, seccion, titulo, minutos, asignada)
PARTES_BASE = [
    (1, 'tesoros', '', 10, False),
    (2, 'tesoros', 'Busquemos perlas escondidas.', 10, False),
    (3, 'tesoros', 'Lectura de la Biblia', 4, True),
    (4, 'maestros', '', 3, True),
    (5, 'maestros', '', 4, True),
    (6, 'maestros', '', 5, True),
    (7, 'vida', '', 15, False),
]


class ParteInline(admin.TabularInline):
    model = ParteVyMC
    extra = 0
    fields = ('numero', 'seccion', 'titulo', 'minutos', 'asignada', 'persona', 'tiempo')


@admin.register(SemanaVyMC)
class SemanaVyMCAdmin(admin.ModelAdmin):
    list_display = ('semana', 'lectura_semanal', 'presidente', 'consejero')
    date_hierarchy = 'fecha_inicio'
    inlines = [ParteInline]
    fieldsets = (
        (None, {'fields': ('fecha_inicio', 'lectura_semanal', 'presidente', 'consejero')}),
        ('Canciones', {'fields': ('cancion_inicial', 'cancion_intermedia', 'cancion_final')}),
        ('Estudio bíblico de la congregación', {'fields': ('conductor_estudio', 'tiempo_estudio')}),
    )

    def get_inline_instances(self, request, obj=None):
        # Las partes se editan después de crear la semana, ya con la estructura base.
        return super().get_inline_instances(request, obj) if obj else []

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        semana = form.instance
        if not change and not semana.partes.exists():
            ParteVyMC.objects.bulk_create([
                ParteVyMC(semana=semana, numero=n, seccion=s, titulo=t, minutos=m, asignada=a)
                for n, s, t, m, a in PARTES_BASE
            ])
            messages.info(request, 'Se crearon las partes base. Completa títulos y participantes abajo.')
