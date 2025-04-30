from rest_framework import serializers, viewsets
from django.utils.timezone import now
from .models import Person, Asignation, AsignationType

# Serializers
class PersonSerializer(serializers.ModelSerializer):
    last_asignation_date = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = ['id', 'name', 'days_from_last_asignation', 'visible', 'last_asignation_date']

    def get_last_asignation_date(self, obj):
        return obj.last_asignation_date


class AsignationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsignationType
        fields = ['id', 'type_name']


class AsignationSerializer(serializers.ModelSerializer):
    person = PersonSerializer()  # Nest full Person data
    helper = PersonSerializer()  # Nest full Helper data (if exists)
    asignation_type = AsignationTypeSerializer(read_only=True)  # Nest full AsignationType data


    class Meta:
        model = Asignation
        fields = ['id', 'person', 'helper', 'asignation_type', 'asignation_date']

# ViewSets
class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class AsignationTypeViewSet(viewsets.ModelViewSet):
    queryset = AsignationType.objects.all()
    serializer_class = AsignationTypeSerializer


class AsignationViewSet(viewsets.ModelViewSet):
    queryset = Asignation.objects.all()
    serializer_class = AsignationSerializer

