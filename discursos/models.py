from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class DiscursoPublico(models.Model):
    nombre = models.CharField('Nombre', max_length=150, help_text='Nombre del orador')
    congregacion = models.CharField('Congregación', max_length=150)
    fecha = models.DateField('Fecha')
    contacto = models.CharField('Contacto', max_length=100, blank=True, help_text='Teléfono u otro dato de contacto')
    cancion = models.PositiveSmallIntegerField(
        'Canción número', null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(200)])

    class Meta:
        ordering = ['fecha', 'nombre']
        verbose_name = 'Discurso público'
        verbose_name_plural = 'Discursos públicos'

    def __str__(self):
        return f'{self.fecha} – {self.nombre} ({self.congregacion})'
