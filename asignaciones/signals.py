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
