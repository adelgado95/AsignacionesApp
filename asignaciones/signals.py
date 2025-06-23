from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.timezone import now
from .models import Asignation, Person

@receiver(post_save, sender=Asignation)
def update_days_from_last_asignation(sender, instance, **kwargs):
    """ Update the person's days_from_last_asignation field after asignation is saved. """
    person = instance.person
    last_asignation = person.asignation_set.order_by('-asignation_date').first()  # Get latest asignation
    
    if last_asignation and last_asignation.asignation_date:
        person.days_from_last_asignation = (now().date() - last_asignation.asignation_date).days
    else:
        person.days_from_last_asignation = 365  # Default value if no asignation exists

    person.save()

@receiver(post_delete, sender=Asignation)
def update_days_from_last_asignation(sender, instance, **kwargs):
    """ Update the person's days_from_last_asignation field after asignation is saved. """
    person = instance.person
    last_asignation = person.asignation_set.order_by('-asignation_date').first()  # Get latest asignation
    
    if last_asignation and last_asignation.asignation_date:
        person.days_from_last_asignation = (now().date() - last_asignation.asignation_date).days
    else:
        person.days_from_last_asignation = 365  # Default value if no asignation exists

    person.save()




@receiver([post_save, post_delete], sender=Asignation)
def update_days_from_last_helper(sender, instance, **kwargs):
    person = instance.helper  # Replace `helper` with the related name to Person, if different
    #Excluding assingation without helper
    if person:
        today = now().date()

        last_assignation = person.assisted_asignations.order_by('-asignation_date').first()

        if last_assignation and last_assignation.asignation_date:
            person.days_from_last_helper = (today - last_assignation.asignation_date).days
        else:
            person.days_from_last_helper = 999

        person.save()
