from rest_framework import serializers, viewsets
from django.utils.timezone import now
from asignaciones.models import Person, Asignation, AsignationType

# Serializers
class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = [
            'id',
            'name',
        ]


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

