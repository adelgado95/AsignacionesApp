# Create your models here.

from django.db import models
from django.utils.timezone import now

class Person(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    name = models.CharField(max_length=255)
    days_from_last_asignation = models.IntegerField(default=365)
    visible = models.BooleanField(default=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')


    def __str__(self):
        return self.name
    
    @property
    def last_asignation(self):
        return self.asignation_set.order_by('-asignation_date').first()

    @property
    def last_asignation_date(self):
        last_asignation = self.asignation_set.order_by('-asignation_date').first()  # Get latest asignation
        if last_asignation and last_asignation.asignation_date:
            return (now().date() - last_asignation.asignation_date).days  # Calculate difference in days
        return 999

    @property
    def last_helper_date(self):
        last_helper_asignation = self.assisted_asignations.order_by('-asignation_date').first()
        if last_helper_asignation and last_helper_asignation.asignation_date:
            return (now().date() - last_helper_asignation.asignation_date).days
        return 999  
    
    @property
    def last_asignation_type(self):
        if self.last_asignation and self.last_asignation.asignation_type:
            return self.last_asignation.asignation_type.type_name
        return None

    @property
    def last_asignation_room(self):
        if self.last_asignation:
            return dict(Asignation.ROOM_CHOICES).get(self.last_asignation.room)
        return None

    @property
    def last_asignation_number(self):
        if self.last_asignation:
            return self.last_asignation.asignation_number
        return None


class AsignationType(models.Model):
    type_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.type_name
    
    

class Asignation(models.Model):
    ROOM_CHOICES = [
        (1, 'Sala 1'),
        (2, 'Sala 2'),
    ]
    ASIG_CHOICES = [
        (3, '3'),
        (4, '4'),
        (5, '5'),
        (6, '6'),
        (7, '7'),
    ]
    ATTENDED_CHOICES = [
        ('pendiente', 'PENDIENTE'),
        ('Asistio', 'ASISTIO'),
        ('no asistio', 'NO ASISTIO')
    ]

    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    helper = models.ForeignKey(
        Person, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="assisted_asignations"  # Changed related_name to avoid clashes
    )
    asignation_type = models.ForeignKey(AsignationType, on_delete=models.CASCADE)
    asignation_number = models.IntegerField(choices=ASIG_CHOICES, default=1)
    asignation_date = models.DateField(default=now, blank=True, null=True)  # Automatically assigns the date
    room = models.IntegerField(choices=ROOM_CHOICES, default=1)
    attended = models.CharField(choices=ATTENDED_CHOICES, max_length=50, null=True, default='pendiente')  # Change to allow NULL and default to None
    notes = models.TextField(blank=True, null=True)  # <- Campo de notas agregado



    def __str__(self):
        return f"{self.person} - {self.asignation_type} ({self.asignation_date}) Sala - {self.room}"
    