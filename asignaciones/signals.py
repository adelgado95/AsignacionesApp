from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.timezone import now
from .models import Asignation, Person

@receiver(post_save, sender=Asignation)
def update_days_from_last_asignation(sender, instance, **kwargs):
    """ Update the person's days_from_last_asignation field after asignation is saved. """
    person = instance.person
    today = now().date()
    last_asignation = Asignation.objects.filter(person=person).order_by('-asignation_date').first()

    if last_asignation and last_asignation.asignation_date:
        person.days_from_last_asignation = (today - last_asignation.asignation_date).days
    else:
        person.days_from_last_asignation = 999  # Default value when no asignation exists

    person.save()

@receiver(post_delete, sender=Asignation)
def update_days_from_last_asignation(sender, instance, **kwargs):
    """ Update the person's days_from_last_asignation field after asignation is saved. """
    person = instance.person
    today = now().date()
    last_asignation = Asignation.objects.filter(person=person).order_by('-asignation_date').first()

    if last_asignation and last_asignation.asignation_date:
        person.days_from_last_asignation = (today - last_asignation.asignation_date).days
    else:
        person.days_from_last_asignation = 999  # Default value when no asignation exists

    person.save()


@receiver([post_save, post_delete], sender=Asignation)
def update_days_from_last_helper(sender, instance, **kwargs):
    person = instance.helper  # Replace `helper` with the related name to Person, if different
    #Excluding assingation without helper
    if person:
        today = now().date()
        last_asignation = Asignation.objects.filter(person=person).order_by('-asignation_date').first()

        if last_asignation and last_asignation.asignation_date:
            person.days_from_last_asignation = (today - last_asignation.asignation_date).days
        else:
            person.days_from_last_asignation = 999  # Default value when no asignation exists

        person.save()


# --- "Último cambio": cualquier alta/edición/baja de lo que muestra la app actualiza el archivo de timestamp ---
from django.db import transaction  # noqa: E402

from programa_privilegios.models import ProgramaPrivilegio  # noqa: E402
from vymc.models import ParteVyMC, SemanaVyMC  # noqa: E402

from .changestamp import touch  # noqa: E402


def _bump(sender, **kwargs):
    transaction.on_commit(touch)  # tras confirmar el guardado, para que la app ya vea los datos nuevos


for _model in (ProgramaPrivilegio, SemanaVyMC, ParteVyMC, Asignation, Person):
    for _signal in (post_save, post_delete):
        _signal.connect(_bump, sender=_model, weak=False, dispatch_uid=f'changestamp-{_signal.__class__.__name__}-{_model.__name__}')
