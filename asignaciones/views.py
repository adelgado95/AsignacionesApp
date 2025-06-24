import csv
import os
import json
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from .models import Asignation
from .forms import AsignationForm, save_default_date_to_file, load_default_date_from_file
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
import tempfile

from datetime import datetime, date, timedelta
from django.utils.timezone import now
from .models import Person, Asignation


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


CONFIG_PATH = os.path.join(settings.BASE_DIR, 'config.json')

def get_default_month_year():
    try:
        with open(CONFIG_PATH, 'r') as f:
            data = json.load(f)
            return int(data.get('default_month', datetime.today().month)), int(data.get('default_year', datetime.today().year))
    except (FileNotFoundError, json.JSONDecodeError):
        return datetime.today().month, datetime.today().year

def set_default_month_year(month, year):
    with open(CONFIG_PATH, 'w') as f:
        json.dump({'default_month': month, 'default_year': year}, f)


def get_default_month_year():
    try:
        with open(CONFIG_PATH, 'r') as f:
            data = json.load(f)
            return int(data.get('default_month', datetime.today().month)), int(data.get('default_year', datetime.today().year))
    except (FileNotFoundError, json.JSONDecodeError):
        return datetime.today().month, datetime.today().year

def set_default_month_year(month, year):
    with open(CONFIG_PATH, 'w') as f:
        json.dump({'default_month': int(month), 'default_year': int(year)}, f)

def asignation_list_by_month(request):
    # Si se hizo POST para guardar mes por defecto
    if request.method == 'POST' and request.POST.get('set_default_month'):
        set_default_month_year(request.POST['month'], request.POST['year'])
        return redirect('asignation_list_by_month')

    if request.method == 'POST' and request.POST.get('set_default_date'):
        print(request.POST)
        save_default_date_to_file(request.POST.get('asignation_date', ''))
        return redirect('asignation_list_by_month')

    month = request.GET.get('month')
    year = request.GET.get('year')
    if not month or not year:
        month, year = get_default_month_year()
    month = int(month)
    year = int(year)

    asignations = Asignation.objects.filter(
        asignation_date__year=year,
        asignation_date__month=month
    ).order_by('asignation_date', 'room', 'asignation_number')

    # Solo en GET o cuando no es un POST de guardado, carga la fecha por defecto
    if request.method == 'POST' and not request.POST.get('set_default_month') and not request.POST.get('set_default_date'):
        form = AsignationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('asignation_list_by_month')
    else:
        # Aquí se carga la fecha por defecto
        initial = {}
        default_date = load_default_date_from_file()
        if default_date:
            initial['asignation_date'] = default_date
        form = AsignationForm(initial=initial)

    context = {
        'asignations': asignations,
        'form': form,
        'selected_month': month,
        'selected_year': year,
        'month_range': range(1, 13),
        'year_range': range(2020, 2031),
        'default_date': default_date,
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
    ).order_by('asignation_date','asignation_number','room')

    html_string = render_to_string('asignation_pdf_template.html', {
        'asignations': asignations,
        'month': month,
        'year': year,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=asignaciones_{month}_{year}.pdf'
    css = CSS(string='@page { size: letter portrait; }')

    with tempfile.NamedTemporaryFile(delete=True) as output:
        HTML(string=html_string).write_pdf(output.name, stylesheets=[css])
        output.seek(0)
        response.write(output.read())

    return response

def asignation_matrix_by_month(request):
    today = now().date()
    # Primer día del mes hace 2 meses atrás
    first_day = (today.replace(day=1) - timedelta(days=62)).replace(day=1)
    # Último día de este mes
    last_day = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Generar lista de semanas (lunes a domingo)
    weeks = []
    current = first_day
    while current <= last_day:
        week_start = current - timedelta(days=current.weekday())
        week_end = week_start + timedelta(days=6)
        if week_start > last_day:
            break
        weeks.append((week_start, min(week_end, last_day)))
        current = week_end + timedelta(days=1)

    persons = Person.objects.filter(visible=True).order_by('name')
    asignations = Asignation.objects.filter(asignation_date__gte=first_day, asignation_date__lte=last_day)

    # Diccionario: {person_id: {week_index: asignation}}
    matrix = {}
    for person in persons:
        matrix[person.id] = {}
        for i, (start, end) in enumerate(weeks):
            asigna = asignations.filter(person=person, asignation_date__gte=start, asignation_date__lte=end).first()
            matrix[person.id][i] = asigna

    context = {
        'persons': persons,
        'weeks': weeks,
        'matrix': matrix,
    }
    return render(request, 'asignation_matrix_by_month.html', context)

from collections import OrderedDict

def asignation_matrix_by_day(request):
    today = now().date()
    first_day = (today.replace(day=1) - timedelta(days=62)).replace(day=1)
    last_day = today

    persons = Person.objects.filter(visible=True).order_by('name')
    asignations = Asignation.objects.filter(asignation_date__gte=first_day, asignation_date__lte=last_day)

    # Fechas únicas ordenadas
    dates = sorted(set(a.asignation_date for a in asignations))

    # Matriz: {persona.id: {fecha: asignacion}}
    matrix = {}
    for person in persons:
        matrix[person.id] = {}
        for date_ in dates:
            asigna = asignations.filter(person=person, asignation_date=date_).first()
            matrix[person.id][date_] = asigna

    context = {
        'persons': persons,
        'dates': dates,
        'matrix': matrix,
    }
    return render(request, 'asignation_matrix_by_day.html', context)
