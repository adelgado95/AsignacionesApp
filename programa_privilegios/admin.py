import datetime as dt

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils import timezone

from .models import ProgramaPrivilegio
from .pdf import MESES, DemasiadasFilas, render_pdf, week_range_label, week_start

FILTER_PARAMS = ('mes', 'anio', 'semana')
RELATED = ('presidente', 'oracion_inicio', 'oracion_final', 'lector', 'entrada', 'auditorio',
           'microfono1', 'microfono2', 'plataforma', 'audio')


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_params(source):
    """meses (list of 1-12, repeat `mes=` to pick several), anio, semana (ISO date of a Monday).

    Works on a QueryDict; invalid values are ignored (meses empty / anio, semana None).
    """
    meses = sorted({m for m in (_int(v) for v in source.getlist('mes')) if m and 1 <= m <= 12})
    try:
        semana = dt.date.fromisoformat(source.get('semana') or '')
    except ValueError:
        semana = None
    return {'meses': meses, 'anio': _int(source.get('anio')), 'semana': semana}


def filter_programas(params):
    """Programs matching month / year / week, ascending by date (Thursday and Saturday together)."""
    qs = ProgramaPrivilegio.objects.all()
    if params['anio']:
        qs = qs.filter(fecha__year=params['anio'])
    if params['meses']:
        qs = qs.filter(fecha__month__in=params['meses'])
    if params['semana']:
        qs = qs.filter(fecha__range=(params['semana'], params['semana'] + dt.timedelta(days=6)))
    return qs.order_by('fecha')


def meses_texto(meses):
    """[11, 12] -> 'Noviembre y diciembre'; [10, 11, 12] -> 'Octubre, noviembre y diciembre'."""
    nombres = [MESES[m - 1] for m in meses]
    texto = nombres[0] if len(nombres) == 1 else ', '.join(nombres[:-1]) + ' y ' + nombres[-1]
    return texto.capitalize()


def periodo_label(params):
    if params['semana']:
        return f"Semana {week_range_label(params['semana'])} de {(params['semana'] + dt.timedelta(days=6)).year}"
    if params['meses'] and params['anio']:
        return f"{meses_texto(params['meses'])} {params['anio']}"
    if params['anio']:
        return f"Año {params['anio']}"
    if params['meses']:
        return f"{meses_texto(params['meses'])} (todos los años)"
    return 'Todos los programas'


@admin.register(ProgramaPrivilegio)
class ProgramaPrivilegioAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'dia', 'presidente', 'oracion_inicio', 'oracion_final',
                    'entrada', 'auditorio', 'microfono1', 'microfono2', 'plataforma', 'audio', 'lector')
    ordering = ('-fecha',)
    list_select_related = True
    list_per_page = 200   # the toolbar filters are not pagination-aware, so keep everything on one page
    change_list_template = 'admin/programa_privilegios/programaprivilegio/change_list.html'
    # Each privilege next to its "asistió" checkbox.
    fields = ('fecha', *[(f, f'{f}_asistio') for f in RELATED])

    @admin.display(description='Día')
    def dia(self, obj):
        return obj.get_dia()

    # --- Mes / Año / Semana toolbar ------------------------------------------------------------
    def changelist_view(self, request, extra_context=None):
        # The toolbar's GET parameters are not model fields: take them out before Django validates the query string.
        params = parse_params(request.GET)
        if any(p in request.GET for p in FILTER_PARAMS):
            query = request.GET.copy()
            for p in FILTER_PARAMS:
                query.pop(p, None)
            request.GET = query
        request._privilegios_params = params

        base = filter_programas({**params, 'semana': None})
        years = sorted({f.year for f in ProgramaPrivilegio.objects.dates('fecha', 'year')} | {timezone.localdate().year})
        weeks = sorted({week_start(f) for f in base.values_list('fecha', flat=True)})
        raw = {'anio': '' if params['anio'] is None else str(params['anio']),
               'semana': params['semana'].isoformat() if params['semana'] else ''}
        extra = {
            'toolbar': {
                'meses': [(i + 1, nombre.capitalize(), (i + 1) in params['meses']) for i, nombre in enumerate(MESES)],
                'meses_label': meses_texto(params['meses']) if params['meses'] else 'Todos',
                'anios': years,
                'semanas': [(w.isoformat(), week_range_label(w)) for w in weeks],
                'valores': raw,
                'export_url': reverse(f'admin:{self.opts.app_label}_{self.opts.model_name}_export_pdf'),
                'clear_url': reverse(f'admin:{self.opts.app_label}_{self.opts.model_name}_changelist'),
                'periodo': periodo_label(params),
            }
        }
        extra.update(extra_context or {})
        return super().changelist_view(request, extra)

    def get_queryset(self, request):
        params = getattr(request, '_privilegios_params', None)
        return filter_programas(params) if params else super().get_queryset(request)

    # --- PDF export ----------------------------------------------------------------------------
    def get_urls(self):
        name = f'{self.opts.app_label}_{self.opts.model_name}_export_pdf'
        return [path('export-pdf/', self.admin_site.admin_view(self.export_pdf), name=name)] + super().get_urls()

    def export_pdf(self, request):
        if not self.has_view_permission(request):
            raise PermissionDenied
        params = parse_params(request.GET)
        programas = list(filter_programas(params).select_related(*RELATED))
        back = redirect(reverse(f'admin:{self.opts.app_label}_{self.opts.model_name}_changelist'))
        if not programas:
            messages.warning(request, 'No hay programas con ese filtro: no se generó el PDF.')
            return back
        try:
            pdf = render_pdf(programas, periodo_label(params))
        except DemasiadasFilas:
            messages.error(request, f'{len(programas)} programas no caben en una sola hoja carta. Filtra por mes o por semana.')
            return back
        first, last = programas[0].fecha, programas[-1].fecha
        filename = f'privilegios-{first:%Y%m%d}-{last:%Y%m%d}.pdf'
        return HttpResponse(pdf, content_type='application/pdf',
                            headers={'Content-Disposition': f'inline; filename="{filename}"'})
