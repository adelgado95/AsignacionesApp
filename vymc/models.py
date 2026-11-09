from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from asignaciones.models import Person

# Solo siervos ministeriales y ancianos (varones) pueden tener asignación directa.
ELEGIBLE = {'gender': 'M', 'visible': True, 'rol__in': ['siervo_ministerial', 'anciano']}

MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
         'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

def fmt_tiempo(segundos):
    """Segundos como m:ss, o '-' si no hay dato."""
    return '-' if segundos is None else f'{segundos // 60}:{segundos % 60:02d}'


CANCION = [MinValueValidator(1), MaxValueValidator(200)]


def _persona(related='+'):
    return models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name=related, limit_choices_to=ELEGIBLE)


class SemanaVyMC(models.Model):
    fecha_inicio = models.DateField(
        unique=True, help_text='Lunes de la semana. El domingo se calcula solo.')
    lectura_semanal = models.CharField(
        max_length=100, help_text='Ej. JEREMÍAS 51, 52')
    presidente = _persona()
    consejero = _persona()
    cancion_inicial = models.PositiveSmallIntegerField(null=True, blank=True, validators=CANCION)
    cancion_intermedia = models.PositiveSmallIntegerField(null=True, blank=True, validators=CANCION)
    cancion_final = models.PositiveSmallIntegerField(null=True, blank=True, validators=CANCION)
    conductor_estudio = _persona()
    tiempo_estudio = models.PositiveIntegerField(
        null=True, blank=True, help_text='Duración real del estudio bíblico, en segundos')

    class Meta:
        ordering = ['-fecha_inicio']
        verbose_name = 'Semana de VyMC'
        verbose_name_plural = 'Semanas de VyMC'

    def __str__(self):
        return self.semana

    @property
    def fecha_fin(self):
        return self.fecha_inicio + timedelta(days=6)

    @property
    def semana(self):
        """'Semana 9 – 15 de noviembre' (o con los dos meses si cruza de mes)."""
        a, b = self.fecha_inicio, self.fecha_fin
        if a.month == b.month:
            return f'Semana {a.day} – {b.day} de {MESES[b.month - 1]}'
        return f'Semana {a.day} de {MESES[a.month - 1]} – {b.day} de {MESES[b.month - 1]}'

    @property
    def tiempo_estudio_display(self):
        return fmt_tiempo(self.tiempo_estudio)

    def clean(self):
        if self.fecha_inicio and self.fecha_inicio.weekday() != 0:
            raise ValidationError({'fecha_inicio': 'La fecha de inicio debe ser un lunes.'})


class ParteVyMC(models.Model):
    TESOROS, MAESTROS, VIDA = 'tesoros', 'maestros', 'vida'
    SECCIONES = [
        (TESOROS, 'Tesoros de la Biblia'),
        (MAESTROS, 'Seamos mejores maestros'),
        (VIDA, 'Nuestra vida cristiana'),
    ]

    semana = models.ForeignKey(SemanaVyMC, on_delete=models.CASCADE, related_name='partes')
    seccion = models.CharField(max_length=10, choices=SECCIONES)
    numero = models.PositiveSmallIntegerField(help_text='Número de la parte en el programa')
    titulo = models.CharField(
        max_length=255, blank=True,
        help_text='Obligatorio salvo en partes de Asignaciones (ahí se usa el tipo de asignación si queda vacío)')
    minutos = models.PositiveSmallIntegerField(null=True, blank=True)
    asignada = models.BooleanField(
        default=False,
        help_text='Los participantes vienen de la app Asignaciones (mismo número de parte y semana)')
    persona = _persona()
    tiempo = models.PositiveIntegerField(
        null=True, blank=True, help_text='Duración real de la parte, en segundos')

    class Meta:
        ordering = ['numero']
        unique_together = [('semana', 'numero')]
        verbose_name = 'Parte'
        verbose_name_plural = 'Partes'

    def __str__(self):
        return f'{self.numero}. {self.titulo or "(de Asignaciones)"}'

    @property
    def tiempo_display(self):
        return fmt_tiempo(self.tiempo)

    def clean(self):
        if self.asignada and self.persona_id:
            raise ValidationError({'persona': 'Una parte de Asignaciones no lleva persona aquí.'})
        if not self.asignada and not self.titulo:
            raise ValidationError({'titulo': 'El título es obligatorio.'})
