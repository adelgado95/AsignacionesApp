from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from asignaciones.models import Person, AsignationType, Asignation
from programa_privilegios.models import ProgramaPrivilegio
import calendar
from datetime import date, timedelta
from django.db.models import Q
from django.utils import timezone
from rest_framework.views import APIView
from vymc.models import SemanaVyMC, ParteVyMC
from programa_privilegios.models import ProgramaPrivilegio
from .serializers import SemanaVyMCSerializer, ProgramaPrivilegioSerializer, PersonSerializer, AsignationTypeSerializer, AsignationListByMonthSerializer

class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer

class AsignationTypeViewSet(viewsets.ModelViewSet):
    queryset = AsignationType.objects.all()
    serializer_class = AsignationTypeSerializer

class AsignationViewSet(viewsets.ModelViewSet):
    queryset = Asignation.objects.all()
    serializer_class = AsignationListByMonthSerializer

class AsignationByMonthViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Asignation.objects.all()
    serializer_class = AsignationListByMonthSerializer

    def get_queryset(self):
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if not month or not year:
            raise ValidationError({'detail': 'Both "month" and "year" query parameters are required.'})
        qs = self.queryset.filter(asignation_date__month=month, asignation_date__year=year)
        return qs

class AsignationEditViewSet(mixins.UpdateModelMixin,
                            mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
    queryset = Asignation.objects.all()
    serializer_class = AsignationListByMonthSerializer


class ProgramaPrivilegioViewSet(viewsets.ReadOnlyModelViewSet):
    """Programa de privilegios (solo lectura). Filtra con ?month=&year= (opcionales)."""
    serializer_class = ProgramaPrivilegioSerializer

    def get_queryset(self):
        qs = ProgramaPrivilegio.objects.select_related(
            'oracion_inicio', 'oracion_final', 'entrada', 'auditorio',
            'microfono1', 'microfono2', 'plataforma', 'audio', 'presidente', 'lector',
        ).order_by('fecha')
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month:
            qs = qs.filter(fecha__month=month)
        if year:
            qs = qs.filter(fecha__year=year)
        return qs


class SemanaVyMCViewSet(viewsets.ReadOnlyModelViewSet):
    """Programa de VyMC (solo lectura). ?month=&year= devuelve las semanas que tocan ese mes."""
    serializer_class = SemanaVyMCSerializer

    def get_queryset(self):
        qs = SemanaVyMC.objects.select_related('presidente', 'consejero', 'conductor_estudio').order_by('fecha_inicio')
        try:
            month = int(self.request.query_params.get('month', ''))
            year = int(self.request.query_params.get('year', ''))
        except ValueError:
            return qs
        first = date(year, month, 1)
        nxt = date(year + (month == 12), month % 12 + 1, 1)
        # Una semana (lunes-domingo) toca el mes si empieza hasta 6 días antes del día 1 y antes del mes siguiente.
        return qs.filter(fecha_inicio__gte=first - timedelta(days=6), fecha_inicio__lt=nxt)

    @action(detail=True, methods=['post'])
    def tiempo(self, request, pk=None):
        """Guarda la duración real (segundos) de una parte: {numero, tiempo}.

        `numero` es el de la parte en el programa; el del estudio bíblico
        (la última parte) se guarda en la semana. `tiempo: null` borra el dato.
        """
        semana = self.get_object()
        try:
            numero = int(request.data.get('numero'))
            raw = request.data.get('tiempo')
            tiempo = None if raw is None else int(raw)
        except (TypeError, ValueError):
            return Response({'detail': '"numero" y "tiempo" deben ser enteros.'}, status=status.HTTP_400_BAD_REQUEST)
        if tiempo is not None and tiempo < 0:
            return Response({'detail': '"tiempo" no puede ser negativo.'}, status=status.HTTP_400_BAD_REQUEST)

        partes = list(semana.partes.all())
        parte = next((p for p in partes if p.numero == numero), None)
        if parte is not None:
            parte.tiempo = tiempo
            parte.save(update_fields=['tiempo'])
        elif numero == max((p.numero for p in partes), default=0) + 1:
            semana.tiempo_estudio = tiempo
            semana.save(update_fields=['tiempo_estudio'])
        else:
            return Response({'detail': f'La semana no tiene la parte {numero}.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'numero': numero, 'tiempo': tiempo})


# --- Mis partes: lo que le toca al usuario logueado en los próximos 3 meses ---

PRIVILEGIO_LABELS = {
    'presidente': 'Presidente',
    'oracion_inicio': 'Oración inicial',
    'oracion_final': 'Oración final',
    'lector': 'Lector',
    'entrada': 'Entrada',
    'auditorio': 'Auditorio',
    'microfono1': 'Micrófono 1',
    'microfono2': 'Micrófono 2',
    'plataforma': 'Plataforma',
    'audio': 'Audio',
}
DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']


def add_months(d, n):
    m = d.month - 1 + n
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


class MisPartesView(APIView):
    """GET /api/mis-partes/ — privilegios, partes de VyMC y asignaciones del usuario
    (vía su Person vinculada) desde hoy hasta dentro de 3 meses, agrupados por día."""

    def get(self, request):
        person = getattr(request.user, 'person', None)  # None si el usuario no está vinculado
        hoy = timezone.localdate()
        hasta = add_months(hoy, 3)
        out = {
            'person': {'id': person.pk, 'name': person.name} if person else None,
            'desde': hoy.isoformat(), 'hasta': hasta.isoformat(), 'dias': [],
        }
        if person is None:
            return Response(out)

        dias = {}

        def add(fecha, tipo, texto):
            items = dias.setdefault(fecha, [])
            if not any(i['texto'] == texto for i in items):  # p. ej. presidente en Privilegios y en VyMC
                items.append({'tipo': tipo, 'texto': texto})

        # 1) Programa de privilegios
        campos = list(PRIVILEGIO_LABELS)
        filtro = Q()
        for c in campos:
            filtro |= Q(**{c: person})
        for p in ProgramaPrivilegio.objects.filter(fecha__range=(hoy, hasta)).filter(filtro):
            for c in campos:
                if getattr(p, f'{c}_id') == person.pk:
                    add(p.fecha, 'privilegio', PRIVILEGIO_LABELS[c])

        # 2) Partes de VyMC (la reunión es el jueves de la semana)
        for sem in SemanaVyMC.objects.filter(
                fecha_inicio__gte=hoy - timedelta(days=6), fecha_inicio__lte=hasta).prefetch_related('partes'):
            reunion = sem.fecha_inicio + timedelta(days=3)
            if not (hoy <= reunion <= hasta):
                continue
            if sem.presidente_id == person.pk:
                add(reunion, 'vymc', 'Presidente')
            if sem.consejero_id == person.pk:
                add(reunion, 'vymc', 'Consejero de la sala auxiliar')
            for pt in sem.partes.all():
                if pt.persona_id == person.pk:
                    add(reunion, 'vymc', f'{pt.numero}. {pt.titulo}' if pt.titulo else f'Parte {pt.numero}')
            if sem.conductor_estudio_id == person.pk:
                add(reunion, 'vymc', 'Estudio bíblico (conductor)')

        # 3) Asignaciones (como participante o ayudante)
        asignaciones = (Asignation.objects.select_related('person', 'helper', 'asignation_type')
                        .filter(asignation_date__range=(hoy, hasta))
                        .filter(Q(person=person) | Q(helper=person)))
        for a in asignaciones:
            titulo = a.asignation_type.type_name.strip().capitalize()  # corto: el detalle está en VyMC
            sala = ' (sala auxiliar)' if a.room == 2 else ''
            if a.person_id == person.pk:
                con = f' con {a.helper.name}' if a.helper else ''
                add(a.asignation_date, 'asignacion', f'{a.asignation_number}. {titulo}{sala}{con}')
            else:
                add(a.asignation_date, 'asignacion', f'Ayudante de {a.person.name}: {a.asignation_number}. {titulo}{sala}')

        out['dias'] = [
            {'fecha': f.isoformat(), 'dia': DIAS[f.weekday()], 'partes': dias[f]} for f in sorted(dias)
        ]
        return Response(out)
