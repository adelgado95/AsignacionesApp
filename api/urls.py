from rest_framework.routers import DefaultRouter
from .views import PersonViewSet, AsignationTypeViewSet, AsignationViewSet, AsignationByMonthViewSet, AsignationEditViewSet

router = DefaultRouter()
router.register(r'persons', PersonViewSet)
router.register(r'asignation-types', AsignationTypeViewSet)
router.register(r'asignations', AsignationViewSet)
router.register(r'asignations-by-month', AsignationByMonthViewSet, basename='asignations-by-month')
router.register(r'asignations-edit', AsignationEditViewSet, basename='asignations-edit')

urlpatterns = router.urls
