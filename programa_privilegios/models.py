from django.core.exceptions import ValidationError
from django.db import models
from django.utils.deconstruct import deconstructible

from asignaciones.models import Person

THURSDAY, SATURDAY = 3, 5
MEETING_WEEKDAYS = (THURSDAY, SATURDAY)

# Cada privilegio -> permiso que debe tener la persona (ver Person.permisos).
PRIVILEGE_PERMISSION = {
    'oracion_inicio': 'oracion',
    'oracion_final': 'oracion',
    'entrada': 'entrada_y_auditorio',
    'auditorio': 'entrada_y_auditorio',
    'microfono1': 'acomodador',
    'microfono2': 'acomodador',
    'plataforma': 'acomodador',
    'audio': 'audio',
    'presidente': 'presidente',
    # Jueves lee el estudio de la congregación (Lectura Libro); sábado, La Atalaya.
    'lector': ('lectura_libro', 'lectura_atalaya'),
}
# Solo estos roles pueden presidir; el resto de privilegios admite cualquier rol.
PRESIDENT_ROLES = ('siervo_ministerial', 'anciano')


def required_permissions(field, fecha=None):
    """Permisos que sirven para `field` (basta uno). El lector depende del día."""
    permiso = PRIVILEGE_PERMISSION[field]
    perms = {permiso} if isinstance(permiso, str) else set(permiso)
    if field == 'lector' and fecha is not None:
        perms = {'lectura_libro'} if fecha.weekday() == THURSDAY else {'lectura_atalaya'}
    return perms


def eligible_ids(field, fecha=None):
    """IDs de las personas que pueden ocupar el privilegio `field`.

    Hombres visibles con el permiso correspondiente; para presidente, además
    siervo ministerial o anciano. Se filtra en Python porque SQLite no soporta
    `contains` sobre JSONField.
    """
    perms = required_permissions(field, fecha)
    qs = Person.objects.filter(gender='M', visible=True)
    if field == 'presidente':
        qs = qs.filter(rol__in=PRESIDENT_ROLES)
    return [p.pk for p in qs if perms & set(p.permisos or [])]


@deconstructible
class EligibleFor:
    """limit_choices_to serializable para las migraciones."""

    def __init__(self, field):
        self.field = field

    def __call__(self):
        return {'pk__in': eligible_ids(self.field)}

    def __eq__(self, other):
        return isinstance(other, EligibleFor) and other.field == self.field


def _privilege(field, related):
    return models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name=related,
        limit_choices_to=EligibleFor(field),
    )


class ProgramaPrivilegio(models.Model):
    fecha = models.DateField(unique=True, help_text='Solo jueves o sábado')
    oracion_inicio = _privilege('oracion_inicio', '+')
    oracion_final = _privilege('oracion_final', '+')
    entrada = _privilege('entrada', '+')
    auditorio = _privilege('auditorio', '+')
    microfono1 = _privilege('microfono1', '+')
    microfono2 = _privilege('microfono2', '+')
    plataforma = _privilege('plataforma', '+')
    audio = _privilege('audio', '+')
    presidente = _privilege('presidente', '+')
    lector = _privilege('lector', '+')

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Programa de privilegios'
        verbose_name_plural = 'Programas de privilegios'

    def __str__(self):
        return f"Privilegios {self.fecha:%d/%m/%Y} ({self.get_dia()})"

    def get_dia(self):
        return {THURSDAY: 'Jueves', SATURDAY: 'Sábado'}.get(self.fecha.weekday(), '')

    def clean(self):
        errors = {}
        if self.fecha and self.fecha.weekday() not in MEETING_WEEKDAYS:
            errors['fecha'] = 'La fecha debe ser jueves o sábado.'
        for field in PRIVILEGE_PERMISSION:
            person_id = getattr(self, f'{field}_id')
            if person_id and person_id not in eligible_ids(field, self.fecha):
                errors[field] = 'Esta persona no cumple los requisitos para este privilegio.'
        if errors:
            raise ValidationError(errors)
