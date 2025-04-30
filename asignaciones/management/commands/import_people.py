from django.core.management.base import BaseCommand
from asignaciones.models import Person

class Command(BaseCommand):
    help = 'Import a list of names as Persons with default gender M'

    def handle(self, *args, **kwargs):
        names = [
            "Arnulfo Delgado", "Alvaro Mayorga", "Carlos Delgado", "Cristian Rivas", "Denis Somarriba",
            "Dodani Blanco", "Flavio Sirias", "Guillermo Martínez", "Franklin Mendez", "Jean Carlos Bonilla",
            "Jairo Ramos", "Jose Lopez", "José Luis Centeno", "Juan Carlos Bonilla", "Juan Carlos Morales",
            "Marlon Gomez", "Mariano Hernandez", "Miguel Maltez", "Roberto López", "Bruno Altamirano",
            "Eliezer Osorio", "Ethan Machado", "Jonathan Centeno", "Joshua Gutiérrez", "Josué Osorio",
            "Kelsy Somarriba", "Mario Machado", "Oscar Telleria", "Michael Maltez", "Thiao Cadena",
            "Clifford Martinez", "Alfonso Delgado", "Carlos Saenz"
        ]

        for name in names:
            person, created = Person.objects.get_or_create(name=name.strip())
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created person: {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Person already exists: {name}'))
