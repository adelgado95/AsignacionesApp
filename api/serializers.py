from rest_framework import serializers, viewsets
from django.utils.timezone import now
from asignaciones.models import Person, Asignation, AsignationType, PERMISO_CHOICES
from vymc.models import SemanaVyMC
from programa_privilegios.models import ProgramaPrivilegio, PRIVILEGE_PERMISSION, puede_marcar_asistencia

# Serializers
class PersonSerializer(serializers.ModelSerializer):
    permisos = serializers.MultipleChoiceField(choices=PERMISO_CHOICES, required=False)

    class Meta:
        model = Person
        fields = [
            'id',
            'name',
            'rol',
            'permisos',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['permisos'] = sorted(data['permisos'])
        return data

    def to_internal_value(self, data):
        result = super().to_internal_value(data)
        if 'permisos' in result:
            result['permisos'] = sorted(result['permisos'])
        return result


class AsignationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsignationType
        fields = [
            'id',
            'type_name',
        ]


class AsignationListByMonthSerializer(serializers.ModelSerializer):
    person = PersonSerializer(read_only=True)
    helper = PersonSerializer(read_only=True)
    asignation_type = AsignationTypeSerializer(read_only=True)
    asignation_date = serializers.DateField(format="%Y-%m-%d")
    asignation_number_display = serializers.SerializerMethodField()
    room_display = serializers.SerializerMethodField()
    attended_display = serializers.SerializerMethodField()

    class Meta:
        model = Asignation
        fields = [
            'id',
            'person',
            'helper',
            'asignation_type',
            'asignation_date',
            'asignation_number',
            'asignation_number_display',
            'room',
            'room_display',
            'attended',
            'attended_display',
            'notes',
            'tiempo',
        ]

    def get_asignation_number_display(self, obj):
        return obj.get_asignation_number_display()

    def get_room_display(self, obj):
        return obj.get_room_display()

    def get_attended_display(self, obj):
        return obj.get_attended_display()

# ViewSets
class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class AsignationTypeViewSet(viewsets.ModelViewSet):
    queryset = AsignationType.objects.all()
    serializer_class = AsignationTypeSerializer


class AsignationViewSet(viewsets.ModelViewSet):
    queryset = Asignation.objects.all()
    serializer_class = AsignationListByMonthSerializer



class ProgramaPrivilegioSerializer(serializers.ModelSerializer):
    """Solo lectura: cada privilegio sale como {id, name} o null."""
    dia = serializers.CharField(source='get_dia', read_only=True)
    fecha = serializers.DateField(format="%Y-%m-%d")
    oracion_inicio = PersonSerializer(read_only=True)
    oracion_final = PersonSerializer(read_only=True)
    entrada = PersonSerializer(read_only=True)
    auditorio = PersonSerializer(read_only=True)
    microfono1 = PersonSerializer(read_only=True)
    microfono2 = PersonSerializer(read_only=True)
    plataforma = PersonSerializer(read_only=True)
    audio = PersonSerializer(read_only=True)
    presidente = PersonSerializer(read_only=True)
    lector = PersonSerializer(read_only=True)
    # {privilegio: null|true|false}: pendiente / asistió / no asistió. Se escribe con
    # POST /api/programa-privilegios/{id}/asistio/ (solo ancianos y siervos ministeriales: `puede_marcar`).
    asistio = serializers.SerializerMethodField()
    puede_marcar = serializers.SerializerMethodField()

    class Meta:
        model = ProgramaPrivilegio
        fields = ['id', 'fecha', 'dia', *PRIVILEGE_PERMISSION, 'asistio', 'puede_marcar']

    def get_asistio(self, obj):
        return {f: getattr(obj, f'{f}_asistio') for f in PRIVILEGE_PERMISSION}

    def get_puede_marcar(self, obj):
        request = self.context.get('request')
        return bool(request and puede_marcar_asistencia(request.user))


def _nombre(person):
    return person.name if person else None


class SemanaVyMCSerializer(serializers.ModelSerializer):
    """Programa completo de una semana de VyMC (solo lectura).

    Une tres fuentes: la propia semana (presidente, canciones, títulos),
    Asignaciones (participantes de las partes `asignada`) y Programa Privilegios
    (oraciones y lector del jueves, y acomodadores de todos los días de la semana).
    """
    semana = serializers.CharField(read_only=True)
    fecha_inicio = serializers.DateField(format="%Y-%m-%d")
    fecha_fin = serializers.DateField(format="%Y-%m-%d")
    presidente = serializers.SerializerMethodField()
    consejero = serializers.SerializerMethodField()
    oracion_inicial = serializers.SerializerMethodField()
    oracion_final = serializers.SerializerMethodField()
    partes = serializers.SerializerMethodField()
    estudio_biblico = serializers.SerializerMethodField()
    acomodadores = serializers.SerializerMethodField()

    class Meta:
        model = SemanaVyMC
        fields = [
            'id', 'semana', 'fecha_inicio', 'fecha_fin', 'lectura_semanal',
            'presidente', 'consejero',
            'cancion_inicial', 'cancion_intermedia', 'cancion_final',
            'oracion_inicial', 'oracion_final',
            'partes', 'estudio_biblico', 'acomodadores',
        ]

    # --- fuentes cacheadas por instancia ---
    def _privilegios(self, obj):
        cache = self.context.setdefault('_priv', {})
        if obj.pk not in cache:
            cache[obj.pk] = list(
                ProgramaPrivilegio.objects
                .select_related(*PRIVILEGE_PERMISSION)
                .filter(fecha__range=(obj.fecha_inicio, obj.fecha_fin))
                .order_by('fecha'))
        return cache[obj.pk]

    def _jueves(self, obj):
        # La reunión de VyMC es el jueves de la semana.
        return next((p for p in self._privilegios(obj) if p.fecha.weekday() == 3), None)

    def get_presidente(self, obj):
        return _nombre(obj.presidente)

    def get_consejero(self, obj):
        return _nombre(obj.consejero)

    def get_oracion_inicial(self, obj):
        j = self._jueves(obj)
        return _nombre(j.oracion_inicio) if j else None

    def get_oracion_final(self, obj):
        j = self._jueves(obj)
        return _nombre(j.oracion_final) if j else None

    def get_partes(self, obj):
        asign = {}
        for a in (Asignation.objects
                  .select_related('person', 'helper', 'asignation_type')
                  .filter(asignation_date__range=(obj.fecha_inicio, obj.fecha_fin))):
            asign.setdefault(a.asignation_number, []).append(a)

        def pareja(a):
            return f'{a.person.name} / {a.helper.name}' if a.helper else a.person.name

        out = []
        for p in obj.partes.select_related('persona'):
            principal = auxiliar = None
            titulo = p.titulo
            if p.asignada:
                items = asign.get(p.numero, [])
                sala1 = next((a for a in items if a.room == 1), None)
                sala2 = next((a for a in items if a.room == 2), None)
                principal = pareja(sala1) if sala1 else None
                auxiliar = pareja(sala2) if sala2 else None
                if not titulo and items:
                    titulo = items[0].asignation_type.type_name.strip().capitalize()
            else:
                principal = _nombre(p.persona)
            out.append({
                'numero': p.numero, 'seccion': p.seccion, 'titulo': titulo, 'minutos': p.minutos,
                'tiempo': p.tiempo,
                'principal': principal, 'auxiliar': auxiliar,
            })
        return out

    def get_estudio_biblico(self, obj):
        j = self._jueves(obj)
        ultimo = max((p.numero for p in obj.partes.all()), default=0)
        return {
            'numero': ultimo + 1,
            'titulo': 'Estudio Bíblico de la Congregación',
            'minutos': 30,
            'conductor': _nombre(obj.conductor_estudio),
            'tiempo': obj.tiempo_estudio,
            'lector': _nombre(j.lector) if j else None,
        }

    def get_acomodadores(self, obj):
        return [
            {'fecha': p.fecha.strftime('%Y-%m-%d'), 'dia': p.get_dia(),
             **{campo: _nombre(getattr(p, campo)) for campo in PRIVILEGE_PERMISSION}}
            for p in self._privilegios(obj)
            if p.fecha.weekday() != 5  # los del sábado no se muestran en VyMC
        ]
