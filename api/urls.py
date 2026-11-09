from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import PersonViewSet, AsignationTypeViewSet, AsignationViewSet, AsignationByMonthViewSet, AsignationEditViewSet, ProgramaPrivilegioViewSet, SemanaVyMCViewSet, MisPartesView

router = DefaultRouter()
router.register(r'persons', PersonViewSet)
router.register(r'asignation-types', AsignationTypeViewSet)
router.register(r'asignations', AsignationViewSet)
router.register(r'asignations-by-month', AsignationByMonthViewSet, basename='asignations-by-month')
router.register(r'programa-privilegios', ProgramaPrivilegioViewSet, basename='programa-privilegios')
router.register(r'vymc', SemanaVyMCViewSet, basename='vymc')
router.register(r'asignations-edit', AsignationEditViewSet, basename='asignations-edit')

urlpatterns = [
    # Login with a Django username/password -> {access, refresh}
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('mis-partes/', MisPartesView.as_view(), name='mis-partes'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] + router.urls
