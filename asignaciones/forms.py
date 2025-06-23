from django import forms
from django.conf import settings
from .models import Asignation, Person
from django.utils.timezone import now
import os

DEFAULT_DATE_FILE =os.path.join(settings.BASE_DIR, 'default_date.txt')

def save_default_date_to_file(date_str):
    with open(DEFAULT_DATE_FILE, 'w') as f:
        f.write(date_str)

def load_default_date_from_file():
    if os.path.exists(DEFAULT_DATE_FILE):
        with open(DEFAULT_DATE_FILE, 'r') as f:
            return f.read().strip()
    return None


class AsignationForm(forms.ModelForm):
    asignation_date = forms.CharField(
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'type': 'text',
            },
        ),
        required=False
    )
    class Meta:
        model = Asignation
        fields = ['person', 'asignation_type', 'asignation_date', 'helper', 'asignation_number','room', 'attended', 'notes']
        widgets = {
            'person': forms.Select(attrs={'class': 'form-control select2'}),
            'asignation_type': forms.Select(attrs={'class': 'form-control select2'}),
            'asignation_number': forms.Select(attrs={'class': 'form-control select2'}),
            'room':forms.Select(attrs={'class': 'form-control select2'}),
            'helper': forms.Select(attrs={'class': 'form-control select2'}),
            'attended': forms.Select(attrs={'class': 'form-control select2'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),  # <- Widget para notas
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si la instancia no tiene fecha y no viene en initial, cargar la fecha por defecto del archivo
        if not self.instance.pk or not self.instance.asignation_date:
            default_date = load_default_date_from_file()
            if default_date and 'asignation_date' not in self.initial:
                self.initial['asignation_date'] = default_date

        # Si la instancia tiene fecha, usarla
        if self.instance and self.instance.asignation_date:
            self.initial['asignation_date'] = self.instance.asignation_date.strftime('%Y-%m-%d')

        # Customize person field display
        self.fields['person'].queryset = Person.objects.all().order_by('-days_from_last_asignation', 'name')
        self.fields['helper'].queryset = Person.objects.all().order_by('-days_from_last_helper')

        # Customize the display label
        self.fields['person'].label_from_instance = lambda obj: f"""
            {obj.name} 
            Num {obj.last_asignation_number} 
            {obj.last_asignation_type} 
            {obj.last_asignation_room}  
            ({obj.days_from_last_asignation} dias) 
            Gen: {obj.gender    }
        """
        self.fields['helper'].label_from_instance = lambda obj: f"{obj.name} ({obj.last_helper_date} dias)"
        self.fields['asignation_type'].widget.attrs['onchange'] = "filterFormFields();"
        print(self.instance.__dict__)
        print(self.instance.asignation_type_id)

        self.fields['asignation_type'].widget.attrs['data-current-asignation-type'] = str(self.instance.asignation_type_id) if self.instance.asignation_type_id else ''


    def save(self, commit=True):
        print("Saving AsignationForm...")
        print("Cleaned data:", self.cleaned_data)

        instance = super().save(commit=False)

        print("Instance before save:", instance.__dict__)
        if self.instance.pk is None:
            instance.attended = None

        if commit:
            instance.save()
            self.save_m2m()  # Si tienes relaciones ManyToMany

        print("Instance after save:", instance.__dict__)

        return instance
