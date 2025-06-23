from django.core.management.base import BaseCommand
from django.utils.timezone import now
from asignaciones.models import Person

class Command(BaseCommand):
    help = 'Update days_from_last_helper field for all Person instances using last_helper_date()'

    def handle(self, *args, **options):
        today = now().date()

        people = Person.objects.all()
        updated_count = 0

        for person in people:
            last_helper_assignation = person.assisted_asignations.order_by('-asignation_date').first()

            if last_helper_assignation and last_helper_assignation.asignation_date:
                person.days_from_last_helper = (today - last_helper_assignation.asignation_date).days
            else:
                person.days_from_last_helper = 999  # Default value if no helper date exists

            person.save()
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} Person records.'))

