from django import forms
from .models import Asignation, Person
from django.utils.timezone import now


class AsignationForm(forms.ModelForm):
    class Meta:
        model = Asignation
        fields = ['person', 'asignation_type', 'asignation_date', 'helper', 'asignation_number','room', 'attended', 'notes']
        widgets = {
            'person': forms.Select(attrs={'class': 'form-control select2'}),
            'asignation_type': forms.Select(attrs={'class': 'form-control select2'}),
            'asignation_number': forms.Select(attrs={'class': 'form-control select2'}),
            'room':forms.Select(attrs={'class': 'form-control select2'}),
            'asignation_date': forms.DateInput(attrs={'class': 'form-control vDateField', 'type': 'date'}),
            'helper': forms.Select(attrs={'class': 'form-control select2'}),
            'attended': forms.Select(attrs={'class': 'form-control select2'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),  # <- Widget para notas


        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and not self.instance.asignation_date:
            self.instance.asignation_date = now()

        if self.instance and self.instance.asignation_date:
            self.initial['asignation_date'] = self.instance.asignation_date.strftime('%Y-%m-%d')

        # Customize person field display
        self.fields['person'].queryset = Person.objects.all().order_by('-days_from_last_asignation')
        self.fields['helper'].queryset = Person.objects.all().order_by('-days_from_last_asignation')

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