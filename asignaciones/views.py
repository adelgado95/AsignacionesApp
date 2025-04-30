from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from .models import Asignation
from .forms import AsignationForm
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
import tempfile

from datetime import datetime


def asignation_list(request):
    date_filter = request.GET.get('date')
    asignations = Asignation.objects.filter(asignation_date=date_filter).order_by('asignation_date', 'room','asignation_number')\
        if date_filter else Asignation.objects.all().order_by('asignation_date', 'room','asignation_number')

    if request.method == 'POST':
        form = AsignationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('asignation_list')  # Refresh page after saving
    else:
        form = AsignationForm()

    return render(request, 'asignation_list.html', {'asignations': asignations, 'form': form})

def asignation_list_by_month(request):
    # Get month and year from GET parameters, default to current date
    month = request.GET.get('month')
    year = request.GET.get('year')

    today = datetime.today()
    month = int(month) if month else today.month
    year = int(year) if year else today.year

    # Filter asignations by selected month and year
    asignations = Asignation.objects.filter(
        asignation_date__year=year,
        asignation_date__month=month
    ).order_by('asignation_date', 'room','asignation_number')

    # Handle form submission
    if request.method == 'POST':
        form = AsignationForm(request.POST)
        print("Pringint request {}".format(request.POST))
        if form.is_valid():
            form.save()
            return redirect('asignation_list_by_month')  # Redirect to the same view after saving
        else:
            print("Form is not valid")
            print(form.errors)
    else:
        form = AsignationForm()

    # Define the range for dropdowns
    context = {
        'asignations': asignations,
        'form': form,
        'selected_month': month,
        'selected_year': year,
        'month_range': range(1, 13),
        'year_range': range(2020, 2031),  # Adjust year range as needed
    }

    return render(request, 'asignation_list_by_month.html', context)


def asignation_edit(request, asignation_id):
    asignation = get_object_or_404(Asignation, id=asignation_id)

    if request.method == 'POST':
        form = AsignationForm(request.POST, instance=asignation)
        if form.is_valid():
            form.save()
            return redirect('asignation_list_by_month')
    else:
        form = AsignationForm(instance=asignation)

    context = {
        'form': form,
        'edit_mode': True,
        'asignation': asignation,
    }
    return render(request, 'asignation_edit.html', context)

def asignation_pdf_by_month(request):
    month = request.GET.get('month')
    year = request.GET.get('year')

    today = datetime.today()
    month = int(month) if month else today.month
    year = int(year) if year else today.year

    asignations = Asignation.objects.filter(
        asignation_date__year=year,
        asignation_date__month=month
    ).order_by('asignation_date', 'room','asignation_number')

    html_string = render_to_string('asignation_pdf_template.html', {
        'asignations': asignations,
        'month': month,
        'year': year,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=asignaciones_{month}_{year}.pdf'
    css = CSS(string='@page { size: A4 landscape; }')

    with tempfile.NamedTemporaryFile(delete=True) as output:
        HTML(string=html_string).write_pdf(output.name, stylesheets=[css])
        output.seek(0)
        response.write(output.read())

    return response