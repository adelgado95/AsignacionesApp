"""Printable PDF (one US Letter sheet) of the privilegios program, built with WeasyPrint."""
import datetime as dt

from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML

MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
         'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
MESES_CORTO = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

# Column order of the sheet: (field on ProgramaPrivilegio, header)
COLUMNAS = [
    ('presidente', 'Presidente'),
    ('oracion_inicio', 'Oración inicial'),
    ('oracion_final', 'Oración final'),
    ('lector', 'Lector'),
    ('entrada', 'Entrada'),
    ('auditorio', 'Auditorio'),
    ('microfono1', 'Micrófono 1'),
    ('microfono2', 'Micrófono 2'),
    ('plataforma', 'Plataforma'),
    ('audio', 'Audio'),
]
FONT_SIZES_PT = (11, 10, 9, 8, 7)   # tried in order until everything fits on a single sheet


class DemasiadasFilas(Exception):
    """The results do not fit on one Letter sheet even with the smallest font."""


def week_start(fecha: dt.date) -> dt.date:
    return fecha - dt.timedelta(days=fecha.weekday())


def week_range_label(monday: dt.date) -> str:
    """'9 – 15 de noviembre' or '30 nov – 6 dic' when the week crosses a month."""
    end = monday + dt.timedelta(days=6)
    if monday.month == end.month:
        return f'{monday.day} – {end.day} de {MESES[end.month - 1]}'
    return f'{monday.day} {MESES_CORTO[monday.month - 1]} – {end.day} {MESES_CORTO[end.month - 1]}'


def render_pdf(programas, periodo: str) -> bytes:
    """`programas`: ProgramaPrivilegio rows (Thursday and Saturday) -> PDF bytes, ascending by date."""
    programas = sorted(programas, key=lambda p: p.fecha)
    filas, semana_anterior = [], None
    for p in programas:
        lunes = week_start(p.fecha)
        filas.append({
            'dia': p.get_dia(),
            'fecha': p.fecha.strftime('%d/%m/%Y'),
            'nuevo_bloque': semana_anterior is not None and lunes != semana_anterior,
            'celdas': [getattr(p, campo) for campo, _ in COLUMNAS],
        })
        semana_anterior = lunes

    ctx = {
        'congregacion': getattr(settings, 'CONGREGACION', ''),
        'periodo': periodo,
        'columnas': [titulo for _, titulo in COLUMNAS],
        'filas': filas,
        'generado': dt.date.today().strftime('%d/%m/%Y'),
    }
    for size in FONT_SIZES_PT:
        html = render_to_string('programa_privilegios/privilegios_pdf.html', {**ctx, 'font_pt': size, 'th_pt': size - 2})
        document = HTML(string=html).render()
        if len(document.pages) == 1:
            return document.write_pdf()
    raise DemasiadasFilas(f'{len(filas)} filas no caben en una hoja carta')
