from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date
from django.utils.timezone import datetime
from asignaciones.models import Person, Asignation, AsignationType

class Command(BaseCommand):
    help = 'Import asignations for LECTURA DE LA BIBLIA without helper.'

    def handle(self, *args, **kwargs):
        # Aseguramos que el tipo de asignación exista
        lectura_type, created = AsignationType.objects.get_or_create(type_name="LECTURA DE LA BIBLIA")
        if created:
            self.stdout.write(self.style.SUCCESS("AsignationType 'LECTURA DE LA BIBLIA' creado"))
        else:
            self.stdout.write("AsignationType 'LECTURA DE LA BIBLIA' ya existe")

        # Lista de asignaciones: (fecha, nombre)
        asignaciones_data = [
            ("15/1/2025", "Oscar Telleria"),
            ("29/1/2025", "Jairo Ramos"),
            ("5/2/2025", "Mariano Hernandez"),
            ("12/2/2025", "Denis Somarriba"),
            ("19/2/2025", "Jonathan Centeno"),
            ("26/2/2025", "Joshua Gutiérrez"),
            ("5/3/2025", "Clifford Martinez"),
            ("12/3/2025", "Jose Lopez"),
            ("19/3/2025", "Eliezer Osorio"),
            ("26/3/2025", "Josué Osorio"),
            ("2/4/2025", "Michael Maltez"),
            ("9/4/2025", "Franklin Mendez"),
        ]

        for fecha_str, nombre in asignaciones_data:
            # Convertir fecha dd/mm/yyyy a objeto datetime.date
            fecha = datetime.strptime(fecha_str, "%d/%m/%Y").date()

            try:
                person = Person.objects.get(name=nombre.strip())
            except Person.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Persona no encontrada: {nombre}"))
                continue

            asignacion = Asignation.objects.create(
                person=person,
                asignation_type=lectura_type,
                asignation_number=3,  # Puedes ajustar según necesidad
                asignation_date=fecha,
                room=1,
                attended=None,
            )
            self.stdout.write(self.style.SUCCESS(f'Asignación creada para {nombre} en fecha {fecha}'))
