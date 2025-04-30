from django.core.management.base import BaseCommand
from asignaciones.models import Person

class Command(BaseCommand):
    help = 'Import a list of male and female names into the Person model.'

    def handle(self, *args, **kwargs):
        male_names = [
            "Arnulfo Delgado", "Alvaro Mayorga", "Carlos Delgado", "Cristian Rivas", "Denis Somarriba",
            "Dodani Blanco", "Flavio Sirias", "Guillermo Martínez", "Franklin Mendez", "Jean Carlos Bonilla",
            "Jairo Ramos", "Jose Lopez", "José Luis Centeno", "Juan Carlos Bonilla", "Juan Carlos Morales",
            "Marlon Gomez", "Mariano Hernandez", "Miguel Maltez", "Roberto López", "Bruno Altamirano",
            "Eliezer Osorio", "Ethan Machado", "Jonathan Centeno", "Joshua Gutiérrez", "Josué Osorio",
            "Kelsy Somarriba", "Mario Machado", "Oscar Telleria", "Michael Maltez", "Thiao Cadena",
            "Clifford Martinez", "Alfonso Delgado", "Carlos Saenz"
        ]

        female_names = [
            "Alexa Martínez", "Alba Rosa Centeno", "Ana Beatriz Gomez", "Andrea Cárcamo", "Blanca Lopez",
            "Carian Saenz", "Carmen Escoto", "Concepción Delgado", "Cristina Centeno", "Darlang Centeno",
            "Dolores Bonilla", "Eleana Gómez", "Elida Maltez", "Francisca Saenz", "Irene Espinoza",
            "Irene Terán", "Jazmin Reyes", "Judith Cadena", "Karla Vanegas", "Ligia Gutierrez",
            "Livia Martinez", "Maria Elena Pineda", "Maria Lopez", "Martha Centeno", "Martha Flores",
            "Matilde Somarriba", "Mayra Quintana", "Meyling Centeno", "Muriel Leiva", "Reina Blanco",
            "Petrona Caceres", "Rosa Sirias", "Rosa E. Martinez", "Rosa Lozano", "Sandra Zuniga",
            "Sandra Sandoval", "Sara Osejo", "Sarai Anton", "Yesenia Gómez", "Daniela Saenz",
            "Cristina Mayorga", "Michelle Blanco"
        ]

        self.import_names(male_names, gender='M')
        self.import_names(female_names, gender='F')

    def import_names(self, names, gender):
        for name in names:
            name = name.strip()
            person, created = Person.objects.get_or_create(name=name, defaults={'gender': gender})
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created {gender} person: {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Person already exists: {name}'))
