from rest_framework import viewsets, mixins
from rest_framework.exceptions import ValidationError
from asignaciones.models import Person, AsignationType, Asignation
from .serializers import PersonSerializer, AsignationTypeSerializer, AsignationListByMonthSerializer

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