from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.utils.html import format_html
from .models import Person, AsignationType, Asignation
from .forms import AsignationForm

class AsignationAdmin(admin.ModelAdmin):
    list_display = ('person', 'asignation_type', 'asignation_date', 'helper')
    list_filter = ('asignation_date', 'asignation_type')
    search_fields = ('person__name', 'asignation_type__type_name', 'helper__name')  # Added required search_fields
#    autocomplete_fields = ('person', 'helper', 'asignation_type')  # Now this won't cause errors

    def asignation_view(self, request):
        """Custom admin view to list and add asignations by date."""
        date_filter = request.GET.get('date')
        asignations = Asignation.objects.filter(asignation_date=date_filter) if date_filter else Asignation.objects.all()

        if request.method == 'POST':
            form = AsignationForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect(request.path)  # Refresh after saving
        else:
            form = AsignationForm()

        return render(request, 'admin/asignation_list.html', {'asignations': asignations, 'form': form})

    def get_urls(self):
        """Registers the custom admin view."""
        urls = super().get_urls()
        custom_urls = [
            path('asignations/', self.admin_site.admin_view(self.asignation_view), name='asignation-list'),
        ]
        return custom_urls + urls

    def asignation_link(self, obj):
        return format_html('<a href="{}">Manage Asignations</a>', '/admin/asignations/')
    asignation_link.short_description = "Manage Asignations"

admin.site.register(Person)
admin.site.register(AsignationType)
admin.site.register(Asignation, AsignationAdmin)


