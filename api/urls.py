from rest_framework.routers import DefaultRouter
from .views import PersonViewSet, AsignationTypeViewSet, AsignationViewSet, AsignationByMonthViewSet

router = DefaultRouter()
router.register(r'persons', PersonViewSet)
router.register(r'asignation-types', AsignationTypeViewSet)
router.register(r'asignations', AsignationViewSet)
router.register(r'asignations-by-month', AsignationByMonthViewSet, basename='asignations-by-month')

urlpatterns = router.urls
