from django.core.management.base import BaseCommand
from django.utils.timezone import now
from asignaciones.models import Person

class Command(BaseCommand):
    help = 'Update days_from_last_asignation field for all Person instances'

    def handle(self, *args, **options):
        today = now().date()

        people = Person.objects.all()
        updated_count = 0

        for person in people:
            last_asignation = person.asignation_set.order_by('-asignation_date').first()

            if last_asignation and last_asignation.asignation_date:
                person.days_from_last_asignation = (today - last_asignation.asignation_date).days
            else:
                person.days_from_last_asignation = 999  # Default value when no asignation exists

            person.save()
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} Person records.'))
