from django.db import models
from django.utils.timezone import now

class Person(models.Model):
    name = models.CharField(max_length=255)
    days_from_last_asignation = models.IntegerField(default=365)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    @property
    def last_asignation_date(self):
        last_asignation = self.asignation_set.order_by('-asignation_date').first()
        if last_asignation and last_asignation.asignation_date:
            return (now().date() - last_asignation.asignation_date).days

    def can_have_asignation_type(self, asignation_type):
        """Check if the person has permission to be assigned the given AsignationType."""
        return PersonPermission.objects.filter(person=self, asignation_type=asignation_type).exists()


class AsignationType(models.Model):
    type_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.type_name


class PersonPermission(models.Model):
    """Defines which asignation types a person can have."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    asignation_type = models.ForeignKey(AsignationType, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('person', 'asignation_type')

    def __str__(self):
        return f"{self.person} can have {self.asignation_type}"


class Asignation(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    asignation_type = models.ForeignKey(AsignationType, on_delete=models.CASCADE)
    asignation_date = models.DateField(default=now, blank=True, null=True)

    def __str__(self):
        return f"{self.person} - {self.asignation_type} ({self.asignation_date})"
