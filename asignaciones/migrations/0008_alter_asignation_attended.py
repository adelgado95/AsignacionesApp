# Generated by Django 5.1.7 on 2025-04-30 03:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asignaciones', '0007_person_gender'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asignation',
            name='attended',
            field=models.CharField(choices=[('pendiente', 'PENDIENTE'), ('Asistio', 'ASISTIO'), ('no asistio', 'NO ASISTIO')], default='pendiente', max_length=50, null=True),
        ),
    ]
