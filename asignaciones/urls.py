from django.urls import path, include
from .views import asignation_list, asignation_list_by_month, asignation_edit, asignation_pdf_by_month
from .serializers import PersonViewSet, AsignationTypeViewSet, AsignationViewSet
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'persons', PersonViewSet)
router.register(r'asignation-types', AsignationTypeViewSet)
router.register(r'asignations', AsignationViewSet)

urlpatterns = router.urls


urlpatterns = [
    path('dynamic/', asignation_list, name='asignation_list'),
#    path('api/', include(router.urls)),
    path('monthly/', asignation_list_by_month, name='asignation_list_by_month'),
    path('asignations/edit/<int:asignation_id>/', asignation_edit, name='asignation_edit'),
    path('asignations/pdf/', asignation_pdf_by_month, name='asignation_pdf_by_month'),
    path('asignation-matrix/', views.asignation_matrix_by_day, name='asignation_matrix_by_day'),
]